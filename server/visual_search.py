import os
import re
import httpx
from pipeline import ExtractionResult

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "")
OPENFOODFACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"
OFF_PRODUCT_URL = "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

#confidence scores
HIGH_CONFIDENCE = 0.85 #title + UPC
MEDIUM_CONFIDENCE = 0.65 #only title, no UPC
LOW_CONFIDENCE = 0.35 #no product data, but visual links

async def visual_search(image_path):
    """
    Send image_url to api
    parse the visual_matches from response
    for each matched title, query open food facts
    return list of products with confidence scores
    """

    if not SERPAPI_KEY:
        print("Visual Search SERPAPI_API_KEY not set")
        return ExtractionResult(data={}, confidence=0.0, method_used="visual_search")


