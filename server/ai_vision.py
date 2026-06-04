"""
ai_vision.py — Gemini-based image extraction, decoupled from main.py and pipeline.py.

Exposes a single public function:
    run_ai_vision(image_path, image_type) -> tuple[list[dict], float]

Returns (items, confidence) where:
  - items is a list of dicts ready to store (same shape as the OCR/parser output)
  - confidence is 0.0 on failure or when Gemini returns nothing usable

Keeping Gemini calls here means main.py and pipeline.py share the same
implementation without either importing the other.
"""

import io
import os
import pandas as pd
import PIL.Image
from google import genai

# ---------------------------------------------------------------------------
# Prompts (identical to what main.py used, centralised here)
# ---------------------------------------------------------------------------
_RECEIPT_PROMPT = (
    "Analyze this receipt image and systematically extract all purchase data. "
    "Respond with ONLY a raw, perfectly parseable CSV stream (do not use markdown "
    "formatting or code blocks). "
    "Use the exact following columns: Store Name, Store Location, Item Description, "
    "Item UPC/SKU, Quantity, Item Price (Per Unit). "
    "On the first row only, include the Store Name and Store Location in columns 1 and 2. "
    "On all subsequent rows, leave columns 1 and 2 empty (just output the leading commas). "
    "Example format:\n"
    "Walmart,123 Main St,Milk,012345678901,1,3.99\n"
    ",, Eggs,012345678902,1,2.49"
)

_SHELF_PROMPT = (
    "Extract product and inventory information from this shelf photo and respond "
    "with ONLY a parsable csv with the following columns: Product Description, brand, "
    "general category, shelf visibility (full (1), partial(0), none(-1)), "
    "and misplaced boolean (is it on the wrong shelf based on other items in photo). "
    "IMPORTANT: if any field value contains a comma, wrap it in double-quotes."
)

_GEMINI_MODEL = "gemini-2.5-flash"


def run_ai_vision(image_path: str, image_type: str) -> tuple[list[dict], float]:
    """
    Sends the image to Gemini and parses the CSV response.

    Args:
        image_path:  Path to the image file on disk.
        image_type:  "receipt" or "shelf".

    Returns:
        (items, confidence)
        items      — list of row dicts (empty list on failure)
        confidence — float in [0, 1]; 0.9 on a clean parse, 0.0 on failure
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ai_vision] GEMINI_API_KEY not set — skipping.")
        return [], 0.0

    try:
        client = genai.Client(api_key=api_key)
        img    = PIL.Image.open(image_path)
        query  = _RECEIPT_PROMPT if image_type == "receipt" else _SHELF_PROMPT
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=[query, img],
        )
        
        RECEIPT_COLUMNS = ["Store Name", "Store Location", "Item Description", "Item UPC/SKU", "Quantity", "Item Price (Per Unit)"]
        clean_csv = response.text.replace("```csv", "").replace("```", "").strip()
        if image_type == "receipt":
            df = pd.read_csv(io.StringIO(clean_csv), names=RECEIPT_COLUMNS, index_col=False, on_bad_lines="skip")
        else:
            df = pd.read_csv(io.StringIO(clean_csv), on_bad_lines="skip")
        print(df)
        if df.empty:
            return [], 0.0

        if image_type == "receipt":
            # Store name/location only appear on the first row — forward-fill then
            # pull them out so items don't each carry redundant store data.
            df["Store Name"]     = df["Store Name"].ffill()
            df["Store Location"] = df["Store Location"].ffill()

        items = df.to_dict(orient="records")
        return items, 0.9

    except Exception as e:
        print(f"[ai_vision] Gemini error: {e}")
        return [], 0.0
