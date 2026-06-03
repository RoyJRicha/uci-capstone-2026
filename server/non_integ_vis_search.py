"""
Retail Shelf Product Detection & Identification Pipeline
=========================================================
Pipeline:
  1. Load shelf image (URL or local path)
  2. Use Google Gemini Flash (FREE) to detect & crop individual products
  3. Upload each crop to ImgBB (free) for a public URL
  4. Query SerpAPI Google Lens for each crop → product name, SKU, price, retailer
  5. Output structured results to console + results.json
"""

import os
import sys
import json
import time
import base64
import logging
from io import BytesIO
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests
from PIL import Image
from serpapi import GoogleSearch

#logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("shelf_pipeline")

from dotenv import load_dotenv
load_dotenv()

#setup 
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY", "")
SERP_API_KEY      = os.environ.get("SERPAPI_API_KEY", "")
IMGBB_API_KEY     = os.environ.get("IMGBB_API_KEY", "")

GEMINI_MODEL = "gemini-2.5-flash"

MIN_CROP_W    = 60
MIN_CROP_H    = 80
SERP_RATE_LIMIT = 1.5

@dataclass
class BoundingBox:
    x: int
    y: int
    w: int
    h: int

    def to_xyxy(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    @property
    def area(self):
        return self.w * self.h


@dataclass
class DetectedProduct:
    index: int
    bbox: BoundingBox
    label: str
    confidence: str
    crop_path: Optional[str]      = None
    product_name: Optional[str]   = None
    brand: Optional[str]          = None
    skus: list                    = field(default_factory=list)
    prices: list                  = field(default_factory=list)
    retailers: list               = field(default_factory=list)
    categories: list              = field(default_factory=list)
    related_searches: list        = field(default_factory=list)
    lens_title: Optional[str]     = None
    lens_source: Optional[str]    = None
    lens_thumbnail: Optional[str] = None
    raw_lens_visual_matches: list = field(default_factory=list)
    identification_status: str    = "pending"
    error: Optional[str]          = None


# ─── Shared Detection Prompt ───────────────────────────────────────────────────
DETECTION_PROMPT = """You are a computer-vision assistant specialised in retail shelf analysis.
Identify every distinct product / SKU visible on the shelves in this image.

For EACH product output a JSON object with these exact keys:
  "label"      : brief product description (brand + type when readable)
  "confidence" : "high" | "medium" | "low"
  "x"          : left edge in pixels (integer)
  "y"          : top  edge in pixels (integer)
  "w"          : width  in pixels (integer)
  "h"          : height in pixels (integer)

Rules:
- Coordinates must be inside the image bounds.
- Each box should tightly surround ONE unique product facing.
- If the same product appears multiple times  do not include each instance.
- Do NOT merge different products into one box.
- Ignore shelf price-tags unless they are part of the package.
- Return ONLY a raw JSON array — no markdown fences, no prose."""


#load image
def load_image(source):
    if source.startswith("http://") or source.startswith("https://"):
        log.info(f"Downloading image: {source}")
        resp = requests.get(source, timeout=30)
        resp.raise_for_status()
        raw = resp.content
    else:
        log.info(f"Loading local image: {source}")
        with open(source, "rb") as fh:
            raw = fh.read()

    img = Image.open(BytesIO(raw)).convert("RGB")
    log.info(f"Image size: {img.width}×{img.height}")
    return img, raw


#detect with Gemini Flash
def detect_with_gemini(img):
    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
        )

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)

    log.info(f"Sending image to Gemini ({GEMINI_MODEL}) for product detection …")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"),
            types.Part.from_text(
                text=f"Image dimensions: {img.width}×{img.height} pixels.\n\n"
                     + DETECTION_PROMPT
            ),
        ],
    )
    return _parse_detection_response(response.text)



def _parse_detection_response(raw_text):
    raw_text = raw_text.strip()
    log.debug(f"Vision model raw (first 400 chars):\n{raw_text[:400]}")

    if raw_text.startswith("```"):
        parts = raw_text.split("```")
        raw_text = parts[1] if len(parts) > 1 else raw_text
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    detections = json.loads(raw_text.strip())
    log.info(f"Vision model detected {len(detections)} raw bounding boxes.")
    return detections


def detect_products(img, raw_bytes):
    log.info("Vision backend: Gemini Flash")
    raw = detect_with_gemini(img)

    products = []
    for i, det in enumerate(raw):
        bbox = BoundingBox(
            x=max(0, int(det.get("x", 0))),
            y=max(0, int(det.get("y", 0))),
            w=int(det.get("w", 0)),
            h=int(det.get("h", 0)),
        )
        bbox.w = min(bbox.w, img.width  - bbox.x)
        bbox.h = min(bbox.h, img.height - bbox.y)

        if bbox.w < MIN_CROP_W or bbox.h < MIN_CROP_H:
            continue

        products.append(DetectedProduct(
            index=i,
            bbox=bbox,
            label=det.get("label", "unknown"),
            confidence=det.get("confidence", "low"),
        ))

    log.info(f"  → {len(products)} products after size filtering.")
    return products


#Crop & Save
def crop_products(img, products, out_dir, padding: int = 8):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    W, H = img.width, img.height

    for p in products:
        x1, y1, x2, y2 = p.bbox.to_xyxy()
        x1, y1 = max(0, x1 - padding), max(0, y1 - padding)
        x2, y2 = min(W, x2 + padding), min(H, y2 + padding)

        crop  = img.crop((x1, y1, x2, y2))
        fname = f"product_{p.index:03d}.jpg"
        fpath = os.path.join(out_dir, fname)
        crop.save(fpath, "JPEG", quality=92)
        p.crop_path = fpath

    log.info(f"Saved {len(products)} product crops to: {out_dir}")
    return products


#upload crop to ImgBB 
def upload_to_imgbb(path, api_key):
    try:
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": api_key, "image": b64},
            timeout=20,
        )
        resp.raise_for_status()
        url = resp.json()["data"]["url"]
        log.debug(f"  ImgBB upload OK: {url}")
        return url
    except Exception as exc:
        log.warning(f"  ImgBB upload failed: {exc}")
        return None


#Google Lens via SerpAPI
def query_google_lens(product):
    if not SERP_API_KEY:
        product.identification_status = "failed"
        product.error = "SERP_API_KEY not set"
        return product

    # Resolve public URL
    image_url: Optional[str] = None
    if IMGBB_API_KEY:
        image_url = upload_to_imgbb(product.crop_path, IMGBB_API_KEY)

    if not image_url:
        image_url = f"file://{os.path.abspath(product.crop_path)}"
        log.warning(f"  No public URL for #{product.index} — set IMGBB_API_KEY for best results.")

    log.info(f"  Google Lens → #{product.index}: {product.label[:55]}")
    try:
        results = GoogleSearch({
            "engine":  "google_lens",
            "url":      image_url,
            "api_key":  SERP_API_KEY,
            "no_cache": "true",
        }).get_dict()

        _parse_lens_results(product, results)
        product.identification_status = "success"

    except Exception as exc:
        product.identification_status = "failed"
        product.error = str(exc)
        log.warning(f"  Lens failed for #{product.index}: {exc}")

    return product


def _parse_lens_results(product, results):
    visual_matches = results.get("visual_matches", [])
    product.raw_lens_visual_matches = visual_matches[:10]

    if visual_matches:
        top = visual_matches[0]
        product.lens_title     = top.get("title")
        product.lens_source    = top.get("source")
        product.lens_thumbnail = top.get("thumbnail")

        names = [m.get("title", "") for m in visual_matches if m.get("title")]
        if names:
            product.product_name = max(names, key=len)

        sources = [m.get("source", "") for m in visual_matches if m.get("source")]
        if sources:
            product.brand = sources[0]

        for m in visual_matches:
            price = m.get("price")
            if price:
                entry = {"price": price.get("value"), "currency": price.get("currency"),
                         "extracted": price.get("extracted_value"),
                         "source": m.get("source"), "link": m.get("link")}
                if entry not in product.prices:
                    product.prices.append(entry)

        for m in visual_matches:
            src, lnk = m.get("source"), m.get("link")
            if src and {"name": src, "url": lnk} not in product.retailers:
                product.retailers.append({"name": src, "url": lnk})

    kg = results.get("knowledge_graph", {})
    if not product.product_name:
        product.product_name = kg.get("title")
    if not product.brand:
        product.brand = kg.get("brand")

    for item in results.get("shopping_results", []):
        for key in ("item_id", "sku", "product_id", "docid"):
            val = item.get(key)
            if val and str(val) not in product.skus:
                product.skus.append(str(val))

        price_val = item.get("extracted_price") or item.get("price")
        if price_val:
            entry = {"price": str(price_val), "currency": item.get("currency", "USD"),
                     "source": item.get("source"), "link": item.get("link")}
            if entry not in product.prices:
                product.prices.append(entry)

        src, lnk = item.get("source"), item.get("link")
        if src and {"name": src, "url": lnk} not in product.retailers:
            product.retailers.append({"name": src, "url": lnk})

        title = item.get("title", "")
        if title and (not product.product_name or len(title) > len(product.product_name)):
            product.product_name = title

    for rs in results.get("related_searches", []):
        q = rs.get("query")
        if q and q not in product.related_searches:
            product.related_searches.append(q)

    for cat in results.get("categories", []):
        name = cat.get("name")
        if name and name not in product.categories:
            product.categories.append(name)


#output
def print_results(products):
    print("\n" + "═" * 70)
    print("  SHELF PRODUCT IDENTIFICATION RESULTS")
    print("═" * 70)
    for p in products:
        print(f"\n┌─ Product #{p.index:03d}  [{p.confidence} confidence]")
        print(f"│  Detected label : {p.label}")
        print(f"│  Bounding box   : x={p.bbox.x} y={p.bbox.y} w={p.bbox.w} h={p.bbox.h}")
        print(f"│  Crop saved     : {p.crop_path or 'N/A'}")
        print(f"│  ID status      : {p.identification_status}")

        if p.identification_status == "success":
            print(f"│  Product name   : {p.product_name or '—'}")
            print(f"│  Brand          : {p.brand or '—'}")
            print(f"│  Lens title     : {p.lens_title or '—'}")
            if p.skus:
                print(f"│  SKUs           : {', '.join(p.skus)}")
            for pr in p.prices[:3]:
                print(f"│  Price          : {pr.get('price')} {pr.get('currency','')} "
                      f"@ {pr.get('source','?')}")
            for r in p.retailers[:3]:
                print(f"│  Retailer       : {r['name']}  →  {r.get('url','')}")
            if p.categories:
                print(f"│  Categories     : {', '.join(p.categories[:5])}")
            if p.related_searches:
                print(f"│  Related        : {' | '.join(p.related_searches[:4])}")
        elif p.error:
            print(f"│  Error          : {p.error}")
        print("└" + "─" * 68)

    print(f"\n✓ Processed {len(products)} products total.")


def save_json(products: list[DetectedProduct], out_path: str):
    data = []
    for p in products:
        d = asdict(p)
        d["raw_lens_visual_matches"] = d["raw_lens_visual_matches"][:5]
        data.append(d)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    log.info(f"Results saved to: {out_path}")


def run_pipeline(
    image_source: str,
    out_dir: str            = "./shelf_output",
    max_products: int       = 0,
    serp_delay: float       = SERP_RATE_LIMIT,
    save_json_results: bool = True,
):
    img, raw_bytes = load_image(image_source)
    products = detect_products(img, raw_bytes)

    if not products:
        log.warning("No products detected.")
        return []

    if max_products and max_products < len(products):
        log.info(f"Capping to first {max_products} products.")
        products = products[:max_products]

    products = crop_products(img, products, os.path.join(out_dir, "crops"))

    if SERP_API_KEY:
        log.info(f"Starting Google Lens identification for {len(products)} products …")
        for i, product in enumerate(products):
            products[i] = query_google_lens(product)
            if i < len(products) - 1:
                time.sleep(serp_delay)
    else:
        log.warning("SERP_API_KEY not set — skipping identification.")
        for p in products:
            p.identification_status = "skipped"
            p.error = "SERP_API_KEY not provided"

    print_results(products)
    if save_json_results:
        save_json(products, os.path.join(out_dir, "results.json"))

    return products

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Retail Shelf Product Detection & Identification Pipeline"
    )
    parser.add_argument("image", help="URL or local path of the shelf image")
    parser.add_argument("--out-dir",      default="./shelf_output",
                        help="Output directory (default: ./shelf_output)")
    parser.add_argument("--max-products", type=int, default=0,
                        help="Max products to process (0 = all)")
    parser.add_argument("--serp-delay",   type=float, default=SERP_RATE_LIMIT,
                        help="Seconds between SerpAPI calls (default: 1.5)")
    parser.add_argument("--no-json",      action="store_true",
                        help="Skip saving results.json")
    args = parser.parse_args()

    run_pipeline(
        image_source     = args.image,
        out_dir          = args.out_dir,
        max_products     = args.max_products,
        serp_delay       = args.serp_delay,
        save_json_results= not args.no_json,
    )