"""
For SHELF images:
  - Uses Gemini Flash to detect and crop individual products from the shelf
  - Uploads each crop to imgbb for a public URL
  - Queries SerpAPI Google Lens per crop to get product name, brand, SKU, price, retailer
  - Returns a structured ExtractionResult containing all identified products

For RECEIPT images:
  - Returns immediately with 0 confidence (not applicable)
"""

import os
import time
import json
import base64
import logging
from io import BytesIO
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests
from PIL import Image

log = logging.getLogger("visual_search")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SERP_API_KEY   = os.environ.get("SERPAPI_API_KEY", "")
IMGBB_API_KEY  = os.environ.get("IMGBB_API_KEY", "")

GEMINI_MODEL    = "gemini-2.5-flash"
MIN_CROP_W      = 60
MIN_CROP_H      = 80
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


#bound-box detection

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
- If the same product appears multiple times do not include each instance.
- Do NOT merge different products into one box.
- Ignore shelf price-tags unless they are part of the package.
- Return ONLY a raw JSON array — no markdown fences, no prose."""


def _detect_with_gemini(img: Image.Image) -> list[dict]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)

    log.info(f"Sending shelf image to Gemini ({GEMINI_MODEL}) for product detection…")
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

    raw = response.text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]

    detections = json.loads(raw.strip())
    log.info(f"Gemini detected {len(detections)} raw bounding boxes.")
    return detections


def _build_products(img: Image.Image, raw_detections: list[dict]) -> list[DetectedProduct]:
    products = []
    for i, det in enumerate(raw_detections):
        bbox = BoundingBox(
            x=max(0, int(det.get("x", 0))),
            y=max(0, int(det.get("y", 0))),
            w=int(det.get("w", 0)),
            h=int(det.get("h", 0)),
        )
        # Clamp to image bounds
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

    log.info(f"{len(products)} products remain after size filtering.")
    return products


def _crop_products(img: Image.Image, products: list[DetectedProduct],
                   out_dir: str, padding: int = 8) -> list[DetectedProduct]:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    W, H = img.width, img.height

    for p in products:
        x1, y1, x2, y2 = p.bbox.to_xyxy()
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(W, x2 + padding)
        y2 = min(H, y2 + padding)

        crop  = img.crop((x1, y1, x2, y2))
        fname = f"product_{p.index:03d}.jpg"
        fpath = os.path.join(out_dir, fname)
        crop.save(fpath, "JPEG", quality=92)
        p.crop_path = fpath

    log.info(f"Saved {len(products)} product crops to: {out_dir}")
    return products


#imgbb upload

def _upload_to_imgbb(path: str) -> Optional[str]:
    if not IMGBB_API_KEY:
        return None
    try:
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": b64},
            timeout=20,
        )
        resp.raise_for_status()
        url = resp.json()["data"]["url"]
        log.debug(f"imgbb upload OK: {url}")
        return url
    except Exception as exc:
        log.warning(f"imgbb upload failed for {path}: {exc}")
        return None


#SerpAPI Google Lens

def _parse_lens_results(product: DetectedProduct, results: dict) -> None:
    """Populate a DetectedProduct in-place from a SerpAPI Google Lens response."""
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
                entry = {
                    "price"     : price.get("value"),
                    "currency"  : price.get("currency"),
                    "extracted" : price.get("extracted_value"),
                    "source"    : m.get("source"),
                    "link"      : m.get("link"),
                }
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
            entry = {
                "price"    : str(price_val),
                "currency" : item.get("currency", "USD"),
                "source"   : item.get("source"),
                "link"     : item.get("link"),
            }
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


def _query_google_lens(product: DetectedProduct) -> DetectedProduct:
    from serpapi import GoogleSearch

    image_url = _upload_to_imgbb(product.crop_path)
    if not image_url:
        product.identification_status = "failed"
        product.error = "imgbb upload failed — set IMGBB_API_KEY"
        return product

    log.info(f"  Google Lens → #{product.index}: {product.label[:55]}")
    try:
        results = GoogleSearch({
            "engine"  : "google_lens",
            "url"     : image_url,
            "api_key" : SERP_API_KEY,
            "no_cache": "true",
        }).get_dict()

        _parse_lens_results(product, results)
        product.identification_status = "success"

    except Exception as exc:
        product.identification_status = "failed"
        product.error = str(exc)
        log.warning(f"  Lens failed for #{product.index}: {exc}")

    return product


def push_shelf_products_to_firebase(
    products: list[DetectedProduct],
    image_path: str,
    store_location: str = "",
) -> None:
    """
    Push identified shelf products to Firebase under /shelves/<push-id>.

    Schema:
      /shelves/<push-id>
        datetime        : str
        image_path      : str
        store_location  : str
        method          : "visual_search"
        products        : [ {product_name, brand, skus, prices, retailers, ...}, ... ]
    """
    import re
    import json
    from datetime import datetime
    from firebase_admin import db

    def safe_key(k: str) -> str:
        return re.sub(r'[.#$\[\]/]', '_', str(k))

    serialised = []
    for p in products:
        d = asdict(p)
        # Trim raw lens matches to top 3 to keep Firebase payload small
        d["raw_lens_visual_matches"] = d["raw_lens_visual_matches"][:3]
        # Sanitise dict keys
        d = {safe_key(k): v for k, v in d.items()}
        serialised.append(d)

    node = {
        "datetime"      : str(datetime.now()),
        "image_path"    : image_path,
        "store_location": store_location,
        "method"        : "visual_search",
        "products"      : serialised,
    }
    node = json.loads(json.dumps(node, default=str))

    db.reference("shelves").push(node)
    log.info(f"[visual_search] Pushed {len(serialised)} product(s) to Firebase /shelves")


#entry point

def run_visual_search(
    image_path: str,
    out_dir: str = "./shelf_output",
    max_products: int = 0,
    serp_delay: float = SERP_RATE_LIMIT,
    store_location: str = "",
) -> list[DetectedProduct]:
    """
    Full shelf visual-search pipeline for one image.

    Steps:
      1. Load image from disk
      2. Gemini Flash → bounding boxes for each distinct product
      3. Crop each product with padding
      4. imgbb upload → SerpAPI Google Lens per crop
      5. Push all results to Firebase /shelves
      6. Return list of DetectedProduct

    Returns an empty list if Gemini or SerpAPI keys are missing.
    """
    global GEMINI_API_KEY, SERP_API_KEY, IMGBB_API_KEY
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    SERP_API_KEY   = os.environ.get("SERPAPI_API_KEY", "")
    IMGBB_API_KEY  = os.environ.get("IMGBB_API_KEY", "")

    if not GEMINI_API_KEY:
        log.warning("[visual_search] GEMINI_API_KEY not set — skipping.")
        return []
    if not SERP_API_KEY:
        log.warning("[visual_search] SERPAPI_API_KEY not set — skipping.")
        return []

    # 1. Load
    img = Image.open(image_path).convert("RGB")
    log.info(f"Shelf image loaded: {img.width}×{img.height}")

    # 2. Detect
    try:
        raw_detections = _detect_with_gemini(img)
    except Exception as exc:
        log.error(f"[visual_search] Gemini detection failed: {exc}")
        return []

    products = _build_products(img, raw_detections)
    if not products:
        log.warning("[visual_search] No products detected after filtering.")
        return []

    if max_products and max_products < len(products):
        log.info(f"Capping to first {max_products} products.")
        products = products[:max_products]

    # 3. Crop
    crops_dir = os.path.join(out_dir, "crops")
    products  = _crop_products(img, products, crops_dir)

    # 4. Google Lens per crop
    log.info(f"Starting Google Lens identification for {len(products)} product(s)…")
    for i, product in enumerate(products):
        products[i] = _query_google_lens(product)
        if i < len(products) - 1:
            time.sleep(serp_delay)

    # 5. Push to Firebase
    # push_shelf_products_to_firebase(products, image_path, store_location)

    return products