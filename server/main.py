import io
import os
import uuid
import asyncio
import PIL.Image
import firebase_admin
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, db
from google import genai
from google.cloud import storage
from pydantic import BaseModel

from pipeline import run_pipeline

load_dotenv()

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


def upload_image_to_cloud(source_file_path, destination_blob_name):
    try:
        # Use the local Firebase service account key for Google Cloud Storage authentication too
        storage_client = storage.Client.from_service_account_json("serviceAccountKey.json")
        bucket = storage_client.bucket("wayvia_storage_bucket")
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        print(f"File {source_file_path} uploaded to {destination_blob_name} in Wayvia Cloud Storage.")
    except Exception as e:
        pass
        # print(f"[WARNING] Skipping Cloud Storage Upload: You do not have IAM permissions configured yet. ({e})")


def _run_pipeline_sync(save_path: str, metadata: dict):
    result = asyncio.run(run_pipeline(save_path, metadata))
    
    if result.method_used != "human_audit":
        today = str(datetime.now())
        df    = pd.DataFrame(result.data.get("items", []))
        
        if metadata["image_type"] == "receipt":
            store_name     = df["Store Name"].iloc[0] if not df.empty else ""
            store_location = df["Store Location"].iloc[0] if not df.empty else ""
            items_df       = df.drop(columns=["Store Name", "Store Location"])
            extra_meta     = {"datetime": today, "store_name": store_name, "store_location": store_location}
            push_to_firebase(items_df, "receipt", extra_meta)
        else:
            df["datetime"] = today
            extra_meta     = {"datetime": today, "store_name": metadata.get("retailer_name", ""), "store_location": metadata.get("store_location", "")}
            push_to_firebase(df, "shelf", extra_meta)


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
    
    store_location = "4255 CAMPUS DR IRVINE CA 92612"; retailer_name="Target"
    metadata = {
        "image_type": image_type,
        "store_location": store_location,
        "retailer_name": retailer_name,
}
    background_tasks.add_task(upload_image_to_cloud, save_path, upload_path)
    background_tasks.add_task(_run_pipeline_sync, save_path, metadata)

    return {
        "status": "ok",
        "saved_as": unique_name,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(bytes(contents)),
    }
