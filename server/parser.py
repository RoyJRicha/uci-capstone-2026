import re
import os
import json
import pandas as pd
from google import genai
from google.genai import types


def detect_store(text: str) -> str:
    text_upper = text.upper()
    if "ALBERTSONS" in text_upper:
        return "albertsons"
    elif "CHICK-FIL-A" in text_upper or "CHICK" in text_upper:
        return "chickfila"
    else:
        return "unknown"


def parse_albertsons(text: str) -> str:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    data  = {
        "store_name" : "Albertsons",
        "address"    : None,
        "items"      : []
    }

    # Address — always contains "Campus Dr" and "IRVINE CA"
    for line in lines:
        if re.search(r'\d{4}\s+campus\s+dr', line, re.IGNORECASE):
            data["address"] = line.strip()
            break
        if re.search(r'irvine\s+ca\s+\d{5}', line, re.IGNORECASE):
            data["address"] = line.strip()
            break

    # Items — pattern observed across all 3 receipts:
    # Long item code (8+ digits), item name, regular price, sale price $
    # e.g. "4178900131MARCHN CHICKEN6.994.49 $"
    # e.g. "2113007002LUCERNE WHOLE MILK4.994.99 $"
    item_pattern = re.compile(
        r'(\d{8,})\s*([A-Za-z][A-Za-z0-9\s/]{2,}?)\s+'  # item code + name
        r'(\d+\.\d{2})\s+'                                 # regular price
        r'(\d+\.\d{2})\s*\$'                               # sale/you pay price
    )

    # Stop parsing items once we hit payment/summary section
    stop_keywords = ['TAX', 'BALANCE', 'PAYMENT', 'CHANGE', 'POINTS', 'SAVINGS', 'THANK']

    for line in lines:
        if any(kw in line.upper() for kw in stop_keywords):
            break
        match = item_pattern.search(line)
        if match:
            data["items"].append({
                "item_code"  : match.group(1),
                "item_name"  : match.group(2).strip(),
                "item_count" : None,   # Not listed on Albertsons receipts
                "price"      : float(match.group(4))  # "You Pay" price
            })

    return data



test = os.getenv("GEMINI_API_KEY")
print(f"test: {test}")
# Create client once at module level
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def parse_with_llm(text: str) -> str:
    prompt = f"""
    You are a receipt parser. Extract structured data from the OCR text below and return it as JSON.

    Important notes:
    - The text may contain OCR errors such as misread characters (e.g. "Chick-fe4" means
      "Chick-fil-A", "Maln" means "Main", "Salo Sevingo" means "Sale Savings")
    - Item codes are long numeric sequences, sometimes joined with item names without spaces
      (e.g. "4178900131MARCHN CHICKEN" means item code "4178900131", name "MARCHN CHICKEN")
    - Some receipts show two prices per item — the regular price and the sale/you pay price.
      Always use the final "You Pay" price.
    - Ignore everything after payment details, loyalty points, savings summaries,
      survey URLs, and cashier info — those are footer noise.

    Return exactly this JSON structure:
    {{
        "store_name": "string or null",
        "address": "string or null",
        "items": [
            {{
                "item_code": "string or null",
                "item_name": "string",
                "item_count": "number or null",
                "price": "number"
            }}
        ]
    }}

    Receipt OCR text:
    {text}
    """

    try:
        response = client.models.generate_content(
            model    = "gemini-2.5-flash",
            contents = prompt,
            config   = types.GenerateContentConfig(
                response_mime_type = "application/json"
            )
        )
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Failed to parse Gemini response as JSON")
        return None
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None
    
def strip_footer(text: str) -> str:
    # Everything after these keywords is noise
    cutoff_keywords = ['THANK YOU', 'FOR ALBERTSONS', 'FOR UQUEST',
                       'FORGOT TO SCAN', 'CHICK-FIL-A.COM']
    lines  = text.split('\n')
    result = []
    for line in lines:
        if any(kw in line.upper() for kw in cutoff_keywords):
            break
        result.append(line)
    return '\n'.join(result)

def _parse_receipt(text: str) -> str:
    text  = strip_footer(text)
    store = detect_store(text)

    if store == "albertsons":
        print("Using Albertsons template parser")
        result = parse_albertsons(text)

        # If template missed items, fall back to Gemini
        if not result["items"]:
            print("Template found no items — falling back to Gemini")
            result = parse_with_llm(text)

        return result

    else:
        # Unknown store (e.g. Chick-fil-A) — go straight to Gemini
        print(f"Unknown store ({store}) — using Gemini parser")
        return parse_with_llm(text)

def parse_receipt(text: str) -> pd.DataFrame:
    """returns parsed receipt as a pandas dataframe"""
    return convert_json_to_df(_parse_receipt(text))

def convert_json_to_df(receipt_json: str) -> pd.DataFrame:
    """
    Converts json recieved from parser to pandas data frame for uploading to firebase
    """
    df = pd.json_normalize(
        receipt_json,                   # Pass the list directly
        record_path=['items'],          # Flatten the items array
        meta=['store_name', 'address']  # Pull in store-level fields
    )

    # Rename columns
    df.rename(columns={
        'store_name'  : 'Store Name',
        'address'     : 'Store Location',
        'item_name'   : 'Item Description',
        'item_code'   : 'Item UPC/SKU',
        'item_count'  : 'Quantity',
        'price'       : 'Item Price (Per Unit)'
    }, inplace=True)
    # Reorder columns
    df = df[['Store Name', 'Store Location', 'Item Description', 'Item UPC/SKU', 'Quantity', 'Item Price (Per Unit)']]
    return df


def tester(filename: str):
    with open(filename, "w+") as f:
        with open("results_for_receipt3.txt", "r") as f2:
            x = f2.read()
            json_text = _parse_receipt(x)
            print(convert_json_to_df(json_text))
            json.dump(json_text, f)

if __name__ == "__main__":
    # tester("first_test")
    # tester("second_test.txt")
    tester("third_test.txt")
