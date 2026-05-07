import io
import PIL.Image
from fastapi import BackgroundTasks
from pydantic import BaseModel
from pyzbar import pyzbar
import cv2
from typing import Optional, Dict, Any
import os
import requests
import urllib.parse
import base64
from thefuzz import fuzz

CONFIDENCE_THRESHOLD = 0.8 # not sure what this should be set to

class ExtractionResult(BaseModel):
    data: Dict[str, Any]
    confidence: float
    method_used: str

class RetrievalPipeline:
    def __init__(self, image_path, metadata):
        self.image_path = image_path
        self.metadata = metadata
        self.img = PIL.Image.open(image_path)
    
    def pre_process(self):
        # TODO: optimize image for ai/ocr
        pass

    async def run(self) -> ExtractionResult:
        self.pre_process()
        # Step 1: Barcode/UPC Lookup
        result = self.barcode_lookup()
        if result.confidence >= CONFIDENCE_THRESHOLD:
            return result

        # Step 2: AI Vision
        result = await self.ai_vision()
        if result.confidence >= CONFIDENCE_THRESHOLD:
            return result

        # Step 3: Visual Search
        result = self.visual_search()
        if result.confidence >= CONFIDENCE_THRESHOLD:
            return result

        # Step 4: Web Scraping
        result = self.web_scraping()
        if result.confidence >= CONFIDENCE_THRESHOLD:
            return result

        # Step 5: OCR
        result = self.ocr()
        if result.confidence >= CONFIDENCE_THRESHOLD:
            return result

        # Step 6: Human Verification
        return self.human_verification()

    def barcode_lookup(self) -> ExtractionResult:
        try:
            img_cv = cv2.imread(self.image_path)
            if img_cv is None:
                return ExtractionResult(data={}, confidence=0.0, method_used="barcode")
            
            # convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # sepaeate bars from the background
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            detected_barcodes = pyzbar.decode(thresh)
            if not detected_barcodes:
                detected_barcodes = pyzbar.decode(gray) #try raw grayscale 
            if not detected_barcodes:
                return ExtractionResult(data={}, confidence=0.0, method_used="barcode")
            
            primary_barcode = detected_barcodes[0]
            barcode_data = primary_barcode.data.decode("utf-8")
            barcode_type = primary_barcode.type

            return ExtractionResult(
                data={
                    "upc": barcode_data,
                    "barcode_type": barcode_type,
                },
                confidence=1.0,
                method_used="barcode"
            )
        except Exception as e:
            print(f"Error in barcode lookup: {e}")
            return ExtractionResult(data={}, confidence=0.0, method_used="barcode")     

    async def ai_vision(self) -> ExtractionResult:
        # TODO: Integrate logic from main.py
        return ExtractionResult(data={}, confidence=0.0, method_used="ai_vision")

    def visual_search(self) -> ExtractionResult:
        # TODO: Implement Google Lens integration
        return ExtractionResult(data={}, confidence=0.0, method_used="visual_search")

    def retailer_api(self, product_name: str = "", retailer_name: str = "") -> ExtractionResult:
        if not product_name or not retailer_name:
            return ExtractionResult(data={}, confidence=0.0, method_used="retailer_api")
        
        CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
        CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")
        if not CLIENT_ID or not CLIENT_SECRET:
            print("Missing Kroger API credentials in .env!")
            return ExtractionResult(data={}, confidence=0.0, method_used="retailer_api")

        try:
            auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
            b64_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            token_url = "https://api.kroger.com/v1/connect/oauth2/token"
            token_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {b64_auth}"
            }
            token_data = {"grant_type": "client_credentials", "scope": "product.compact"}
            token_res = requests.post(token_url, headers=token_headers, data=token_data)
            if token_res.status_code != 200:
                print("Failed to authenticate with Kroger API")
                return ExtractionResult(data={}, confidence=0.0, method_used="retailer_api")
            
            access_token = token_res.json().get("access_token")

            # Search Kroger API
            encoded_name = urllib.parse.quote(product_name)
            search_url = f"https://api.kroger.com/v1/products?filter.term={encoded_name}&filter.limit=5"
            search_headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            search_res = requests.get(search_url, headers=search_headers)
            
            # Fuzzy String Matching
            if search_res.status_code == 200:
                data = search_res.json()
                items = data.get("data", [])
                best_match = None
                highest_score = 0.0
                for item in items:
                    desc = item.get("description", "")
                    score = fuzz.partial_ratio(product_name.lower(), desc.lower()) / 100.0
                    if score > highest_score:
                        highest_score = score
                        best_match = item
                        
                # Verification Check
                if best_match and highest_score >= CONFIDENCE_THRESHOLD:
                    return ExtractionResult(
                        data={
                            "upc": best_match.get("upc"),
                            "matched_name": best_match.get("description")
                        },
                        confidence=highest_score,
                        method_used="retailer_api"
                    )
            
            # Fall back to human verification if no results passed the threshold
            return ExtractionResult(data={}, confidence=0.0, method_used="retailer_api")
            
        except Exception as e:
            print(f"Error during Kroger API lookup: {e}")
            return ExtractionResult(data={}, confidence=0.0, method_used="retailer_api")

    def ocr(self) -> ExtractionResult:
        # TODO: Implement OCR
        return ExtractionResult(data={}, confidence=0.0, method_used="ocr")

    def human_verification(self) -> ExtractionResult:
        # TODO: Add to a list/queue for human auditors to review and input data manually
        return ExtractionResult(data={}, confidence=0.5, method_used="human_audit")

# background_tasks.add_task(run_pipeline, save_path, metadata)
# need to define what metadata we want to pass in here
# integrate with fastapi endpoint
async def run_pipeline(save_path, metadata):
    pipeline = RetrievalPipeline(save_path, metadata)
    final_data = await pipeline.run()
    
    # save final_data.data to SQL Database
