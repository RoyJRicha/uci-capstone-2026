import base64
import os
import requests
import urllib.parse
from thefuzz import fuzz
from pipeline import CONFIDENCE_THRESHOLD


def extract_retailer_upc(self, kroger_upc: str, retailer_name: str = "") -> str:
    if any(name in retailer_name for name in ["Kroger", "Ralphs", "Albertsons"]):
        return kroger_upc
    elif any(name in retailer_name for name in ["Target", "Walmart"]):
        upc = kroger_upc[2:]
        odd_sum = sum(int(upc[i]) for i in range(0, 11, 2))
        even_sum = sum(int(upc[i]) for i in range(1, 11, 2))
        total = odd_sum * 3 + even_sum
        check = (10 - (total % 10)) % 10
        return upc + str(check)
    else:
        return None

def kroger_api(self, product_name: str, retailer_name: str) -> tuple[dict, float]:
    if not product_name or not retailer_name:
        return {}, 0.0
    
    CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
    CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Missing Kroger API credentials in .env!")
        return {}, 0.0

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
            return {}, 0.0
        
        access_token = token_res.json().get("access_token")
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
                    
            if best_match:
                return {"upc": extract_retailer_upc(best_match.get("upc")),
                        "matched_name": best_match.get("description")
                        }, highest_score
        
        return {}, 0.0
        
    except Exception as e:
        print(f"Error during Kroger API lookup: {e}")
        return {}, 0.0