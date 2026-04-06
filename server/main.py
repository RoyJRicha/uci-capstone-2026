import io
import os
import uuid
from datetime import datetime

import PIL.Image
import firebase_admin
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, db
from google import genai
from google.cloud import storage
from pydantic import BaseModel

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Firebase Realtime Database setup
# ---------------------------------------------------------------------------
_cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(
    _cred,
    {"databaseURL": "https://wayvia-capstone-default-rtdb.firebaseio.com/"},
)

# head to http://localhost:8000/docs to test the API (no Postman needed)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow Expo Go / physical devices on the LAN
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def push_to_firebase(df: pd.DataFrame, image_type: str, extra_meta: dict) -> None:
    """
    Pushes one scan's worth of data to Firebase Realtime Database.

    Structure:
      /receipts/<push-id>  →  { datetime, store_name, store_location, items: [...] }
      /shelves/<push-id>   →  { datetime, location, items: [...] }
    """
    import json, re

    def safe_key(k: str) -> str:
        """Firebase keys cannot contain . # $ [ ] / — replace all with _."""
        return re.sub(r'[.#$\[\]/]', '_', k)

    # Rename columns to Firebase-safe names before serializing
    safe_df = df.rename(columns={col: safe_key(col) for col in df.columns})

    # pandas → JSON string → plain Python list (handles all numpy/NaN edge cases)
    items = json.loads(safe_df.to_json(orient="records", default_handler=str))

    node = {**extra_meta, "items": items}

    # Full round-trip through json.dumps(default=str) — final safety net
    node = json.loads(json.dumps(node, default=str))

    ref_path = "receipts" if image_type == "receipt" else "shelves"
    db.reference(ref_path).push(node)
    print(f"[Firebase] pushed {len(items)} row(s) to /{ref_path}")


def process_with_gemini(save_path: str, image_type: str):
    """
    Runs after the HTTP response is already sent to the client.
    Calls Gemini, parses the CSV result, and pushes to Firebase.
    """
    client = genai.Client()
    img = PIL.Image.open(save_path)

    if image_type == "receipt":
        query = (
            "Analyze this receipt image and systematically extract all purchase data. "
            "Respond with ONLY a raw, perfectly parseable CSV stream (do not use markdown formatting or code blocks). "
            "Use the exact following columns: Store Name, Store Location, Item Description, Item UPC/SKU, Quantity, Item Price (Per Unit). "
            "To minimize output tokens, ONLY include the 'Store Name' and 'Store Location' on the very first row. "
            "For all subsequent items, leave those two fields blank (just output the commas)."
        )
    else:
        query = (
            "Extract product and inventory information from this shelf photo and respond "
            "with ONLY a parsable csv with the following columns: Product Description, brand, "
            "general category, shelf visibility (full (1), partial(0), none(-1)), "
            "and misplaced boolean (is it on the wrong shelf based on other items in photo). "
            "IMPORTANT: if any field value contains a comma, wrap it in double-quotes."
        )

    print(f"Processing {image_type} image...")
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=[query, img],
    )

    # Strip any potential markdown blocks Gemini occasionally throws in
    clean_csv = response.text.replace("```csv", "").replace("```", "").strip()
    df = pd.read_csv(io.StringIO(clean_csv), on_bad_lines='skip')

    today = str(datetime.now())

    if image_type == "receipt":
        # Store name/location only appear on row 0 — forward-fill then drop cols from items
        df["Store Name"] = df["Store Name"].ffill()
        df["Store Location"] = df["Store Location"].ffill()
        store_name = df["Store Name"].iloc[0] if not df.empty else ""
        store_location = df["Store Location"].iloc[0] if not df.empty else ""
        items_df = df.drop(columns=["Store Name", "Store Location"])
        extra_meta = {
            "datetime": today,
            "store_name": store_name,
            "store_location": store_location,
        }
        print(df)
        push_to_firebase(items_df, image_type, extra_meta)
    else:
        location = input("Input the retail location of photo: ")
        df["datetime"] = today
        df["UPC"] = None
        extra_meta = {"datetime": today, "location": location}
        print(df)
        push_to_firebase(df, image_type, extra_meta)



def upload_image_to_cloud(source_file_path, destination_blob_name):
    storage_client = storage.Client()

    bucket = storage_client.bucket("wayvia_storage_bucket")

    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_path)

    print(f"File {source_file_path} uploaded to {destination_blob_name} in Wayvia Cloud Storage.")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Saves the uploaded image and immediately returns a success response.
    Gemini processing happens in the background after this response is sent.
    """
    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    # Determine image type based on the filename set by the mobile app ('shelf.jpg' or 'receipt.jpg')
    image_type = "receipt" if (file.filename or "").startswith("receipt") else "shelf"
    upload_path = os.path.join(image_type, unique_name)
    # Queue Gemini processing — runs after response is returned to client
    background_tasks.add_task(upload_image_to_cloud, save_path, upload_path)
    background_tasks.add_task(process_with_gemini, save_path, image_type)

    return {
        "status": "ok",
        "saved_as": unique_name,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(bytes(contents)),
    }
