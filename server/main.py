import io
import os
import uuid
from datetime import date

import PIL.Image
import pandas as pd
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.cloud import storage

load_dotenv()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# head to http://localhost:8000/docs to test the API (no Postman needed)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow Expo Go / physical devices on the LAN
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def process_with_gemini(save_path: str, image_type: str):
    """
    Runs after the HTTP response is already sent to the client.
    Calls Gemini, parses the CSV result, and prints the dataframe.
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
            "UPC (leave empty if barcode is not clearly visible), and misplaced boolean "
            "(is it on the wrong shelf based on other items in photo)"
        )
        
    print(f"Processing {image_type} image...")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=[query, img],
    )
    
    # Strip any potential markdown blocks Gemini occasionally throws in
    clean_csv = response.text.replace("```csv", "").replace("```", "").strip()
    df = pd.read_csv(io.StringIO(clean_csv))
    
    # Only prompt for location if it's a shelf photo, since receipts extract it automatically
    if image_type == "shelf":
        location = input("Input the retail location of photo: ")
        df["location"] = location
        
    df["date"] = date.today()
    print(df)


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

    # Queue Gemini processing — runs after response is returned to client
    background_tasks.add_task(process_with_gemini, save_path, image_type)

    return {
        "status": "ok",
        "saved_as": unique_name,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
    }
