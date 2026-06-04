import os
import easyocr
import numpy as np
import PIL.Image
from PIL import ImageOps
from pydantic import BaseModel
from typing import Dict, Any
from dataclasses import asdict
            
from kroger_api import kroger_api
from visual_search import run_visual_search, DetectedProduct
from parser import parse_receipt
from ocr import preprocess
from ai_vision import run_ai_vision
from human_review import enqueue_for_review

CONFIDENCE_THRESHOLD = 0.8


class ExtractionResult(BaseModel):
    data: Dict[str, Any]
    confidence: float
    method_used: str


class RetrievalPipeline:
    def __init__(self, image_path: str, metadata: dict):
        self.image_path = image_path
        self.metadata   = metadata
        # Respect EXIF orientation so portrait receipts aren't rotated sideways
        self.img        = ImageOps.exif_transpose(PIL.Image.open(image_path))
        # image_type must be "receipt" or "shelf" — callers set this in metadata
        self.image_type: str = metadata.get("image_type", "shelf")

    async def run(self) -> ExtractionResult:
        result = await self.ai_vision()
        if result.confidence >= CONFIDENCE_THRESHOLD:
            return result
        if self.image_type == "shelf":
            result = self.visual_search()
            if result.confidence >= CONFIDENCE_THRESHOLD:
                return result
        else:  # receipt
            result = self.ocr()
            if result.confidence >= CONFIDENCE_THRESHOLD:
                return result
        return self.human_verification(result)

    async def ai_vision(self) -> ExtractionResult:
        """
        Delegates to ai_vision.run_ai_vision(), which owns the Gemini prompt
        and CSV parsing logic.
        """
        try:
            items, confidence = run_ai_vision(self.image_path, self.image_type)
            if not items:
                return ExtractionResult(data={}, confidence=0.0, method_used="ai_vision")
            retailer_name = self.metadata.get("retailer_name", "")
            items = self._enrich_upcs(items, retailer_name)
            return ExtractionResult(
                data={"items": items},
                confidence=confidence,
                method_used="ai_vision",
            )
        except Exception as e:
            print(f"Error in AI vision: {e}")
            return ExtractionResult(data={}, confidence=0.0, method_used="ai_vision")

    def visual_search(self) -> ExtractionResult:
        """
        Calls run_visual_search() from visual_search.py.
        Confidence is the fraction of detected products successfully identified
        by Google Lens.
        """
        try:
            store_location = self.metadata.get("store_location", "")
            products: list[DetectedProduct] = run_visual_search(
                image_path=self.image_path,
                store_location=store_location,
            )
            if not products:
                return ExtractionResult(data={}, confidence=0.0, method_used="visual_search")
            return ExtractionResult(data={}, confidence=0.0, method_used="visual_search")

        except Exception as e:
            print(f"Error in visual search: {e}")
            return ExtractionResult(data={}, confidence=0.0, method_used="visual_search")

    # Step 3 (receipt) — OCR
    def ocr(self) -> ExtractionResult:
        """
        1. Pre-processes the receipt image with ocr.preprocess()
        2. Runs EasyOCR to extract raw text
        3. Feeds the text through parser.parse_receipt() → structured DataFrame
        4. Enriches any row missing a UPC via the Kroger API
        """
        try:
            img_np    = np.array(self.img)
            processed = preprocess(img_np)

            reader   = easyocr.Reader(['en'], gpu=False)
            raw_text = "\n".join(text for (_, text, _) in reader.readtext(processed))

            if not raw_text.strip():
                return ExtractionResult(data={}, confidence=0.0, method_used="ocr")

            df = parse_receipt(raw_text)
            if df is None or df.empty:
                return ExtractionResult(data={}, confidence=0.0, method_used="ocr")

            # Kroger UPC enrichment for rows missing a UPC
            retailer_name = self.metadata.get(
                "retailer_name",
                df["Store Name"].iloc[0] if "Store Name" in df.columns else "",
            )
            retailer_name = self.metadata.get("retailer_name", df["Store Name"].iloc[0] if "Store Name" in df.columns else "")
            items = self._enrich_upcs(df.to_dict(orient="records"), retailer_name)

            # Any non-empty parse is considered high-confidence; UPC coverage is a bonus
            confidence = 0.85 if items else 0.0

            return ExtractionResult(
                data={"items": items},
                confidence=confidence,
                method_used="ocr",
            )
        except Exception as e:
            print(f"Error in OCR step: {e}")
            return ExtractionResult(data={}, confidence=0.0, method_used="ocr")

    # Kroger API method
    def _enrich_upcs(self, items: list[dict], retailer_name: str) -> list[dict]:
        """
        For any item missing a UPC, attempt a Kroger API lookup by product name.
        Works on both receipt items and shelf products — any dict with a name field.
        """
        name_keys = ("Product Description", "Item Description", "product_name", "label")  # receipt, visual_search, ai_vision shelf
        upc_keys  = ("Item UPC/SKU", "upc")

        for item in items:
            # Check if a UPC already exists under any known key
            has_upc = any(
                str(item.get(k, "")).strip() not in ("", "nan", "None")
                for k in upc_keys
            )
            if has_upc:
                continue

            # Find the best available name field
            product_name = next(
                (str(item[k]).strip() for k in name_keys if item.get(k)),
                None
            )
            if not product_name:
                continue

            api_data, api_conf = kroger_api(product_name, retailer_name)
            if api_conf > 0.6 and api_data.get("upc"):
                item["upc"] = api_data["upc"]

        return items

    def human_verification(self, last_result: ExtractionResult) -> ExtractionResult:
        """
        Pushes whatever partial data was extracted so far to the human review
        queue in Firebase (/human_review/<push-id>), then returns a result that
        signals the pipeline completed with a human audit pending.

        Auditors resolve items via the /review endpoints in human_review.py.
        """
        reason = (
            "no_items_parsed" if not last_result.data
            else "low_confidence"
        )
        review_id = enqueue_for_review(
            image_path=self.image_path,
            image_type=self.image_type,
            partial_data=last_result.data,
            reason=reason,
        )
        return ExtractionResult(
            data={**last_result.data, "review_id": review_id},
            confidence=0.5,
            method_used="human_audit",
        )


async def run_pipeline(save_path: str, metadata: dict) -> ExtractionResult:
    """
    Entry point called by the FastAPI background task.

    Expected metadata keys:
      image_type      : "receipt" | "shelf"
      retailer_name   : e.g. "Albertsons"  (Kroger UPC enrichment)
      store_location  : street address      (visual_search Firebase push)
    """
    pipeline   = RetrievalPipeline(save_path, metadata)
    final_data = await pipeline.run()

    # TODO: persist final_data.data to SQL / Firebase
    return final_data

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    receipt_image = "uploads/5f81ad0d06eb4c3e9eec738e82e0e4db.jpg"
    receipt_image2 = "uploads/d368f4c4cc2e44df8902139f2609075d.jpg"
    
    shelf_image = "uploads/7f25e6774015481f98aa395b6e5d15f6.png"
    simple_shelf = "uploads/Screenshot 2026-06-04 at 2.05.05 AM.png"
    metadata = {"image_type": "shelf", "retailer_name": "Target", "store_location": "Fake Store, CA"}
    
    pipeline = RetrievalPipeline(shelf_image, metadata)

    # Test each method individually by calling it directly:
    result = asyncio.run(pipeline.ai_vision())
    # result = pipeline.visual_search()
    # result = pipeline.ocr()
    # result = pipeline.retailer_api("Lucerne Whole Milk", "Albertsons")

    # items = [{'Product Description': 'Raisin Nut Bran', 'brand': 'General Mills', 'general category': 'Cereal', 'shelf visibility': 1, 'misplaced boolean': 0}, 
    #          {'Product Description': "Generic Cereal '4'", 'brand': 'Unspecified', 'general category': 'Cereal', 'shelf visibility': 1, 'misplaced boolean': 0}, 
    #          {'Product Description': 'Oatmeal Crisp (Hearty Raisin)', 'brand': 'General Mills', 'general category': 'Cereal', 'shelf visibility': 1, 'misplaced boolean': 0}]
    # items = pipeline._enrich_upcs(items, "Target")
    # print(items)

    # Or test the full pipeline:
    # result = asyncio.run(pipeline.run())
    print(f"Method : {result.method_used}")
    print(f"Confidence: {result.confidence}")
    print(f"Data: {result.data}")
    