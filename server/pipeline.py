import os
import time
import cv2
import PIL.Image
from fastapi import BackgroundTasks
from pydantic import BaseModel
from pyzbar import pyzbar
from typing import Optional, Dict, Any
from kroger_api import kroger_api

CONFIDENCE_THRESHOLD = 0.8

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

    # def _create_log_file(self, log_name: str):
    #     with open(log_name, 'w') as log:
    #         log.write(f"Processing image at {self.image_path}\n")
    #     return time.time()

    # def _write_to_log(self, log_name: str, method: str, confidence: float):
    #     with open(log_name, "a") as log:
    #         log.write(f"Method {method} was used, returning a confidence score of {confidence}.")
    #         if co with success {success}\n")

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

    def retailer_api(self, product_name: str, retailer_name: str) -> ExtractionResult:
        data, confidence = kroger_api(product_name, retailer_name)
        return ExtractionResult(data=data, confidence=confidence, method_used="retailer_api")

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
