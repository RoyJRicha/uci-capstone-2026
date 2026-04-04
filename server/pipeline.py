import io
import PIL.Image
from fastapi import BackgroundTasks
from pydantic import BaseModel
from pyzbar import pyzbar
import cv2
from typing import Optional, Dict, Any

CONFIDENCE_THRESHOLD = 0.8 #not sure what this should be set to

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
            
            #convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            #gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            #sepaeate bars from the background
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

    def web_scraping(self) -> ExtractionResult:
        # TODO: Scrape retailer inventory APIs/sites
        return ExtractionResult(data={}, confidence=0.0, method_used="web_scraping")

    def ocr(self) -> ExtractionResult:
        # TODO: Implement OCR
        return ExtractionResult(data={}, confidence=0.0, method_used="ocr")

    def human_verification(self) -> ExtractionResult:
        # TODO: Add to a list/queue for human auditors to review and input data manually
        return ExtractionResult(data={}, confidence=0.5, method_used="human_audit")

# Integration into your FastAPI upload endpoint
# background_tasks.add_task(run_pipeline, save_path, metadata)
# need to define what metadata we want to pass in here
async def run_pipeline(save_path, metadata):
    pipeline = RetrievalPipeline(save_path, metadata)
    final_data = await pipeline.run()
    
    # save final_data.data to SQL Database
