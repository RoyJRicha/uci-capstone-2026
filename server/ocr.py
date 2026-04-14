"""Trying Out various OCR methods"""
from receiptparser.config import read_config
from receiptparser.parser import process_receipt

CONFIG = read_config("uploads/germany.yml")  # config file necessary for receiptparser library

def _testReceiptParser(fileName):
    """Test the receipt parser library"""
    receipt = process_receipt(CONFIG, fileName)
    print("Filename:   ", receipt.filename)
    print("Company:    ", receipt.company)
    print("Postal code:", receipt.postal)
    print("Date:       ", receipt.date)
    print("Amount:     ", receipt.sum)

def testReceiptParser():
    """Test 4 different receipts"""
    _testReceiptParser("uploads/receipt1.jpg")
    _testReceiptParser("uploads/receipt2.jpg")
    _testReceiptParser("uploads/receipt3.jpg")
    _testReceiptParser("uploads/receipt4.jpg")
    

"""
This library was originally trainined on German receipts. Format is similar to US receipts,
but language differents seem to cause issues in identifying certain fields of the receipt.
Also, this library lacks the granularity necessary for our project, as it only recovers
the ZIP code, Company, Date of transaction, and Total cost.
In the following test, this library is unable to correctly identify the receipts as belonging
to Alberstsons, and it captures the zip code backwards/upside down as 21926 instead of 92612.
It is unable to capture date and amount in all tests
"""
# testReceiptParser()

from PIL import Image, ImageOps
import numpy as np
import cv2
from matplotlib import pyplot as plt
import easyocr  # now testing easyocr library

reader = easyocr.Reader(['en'], gpu=False)
img = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt1.jpg")))
img2 = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt2.jpg")))
img3 = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt3.jpg")))
img4 = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt4.jpg")))

def testEasyOCR(npImg: np.ndarray, showBoundingBox=False):
    results = reader.readtext(npImg)
    imgAnnotated = npImg.copy() if showBoundingBox else None
    for (bbox, text, confidence) in results:
        print(f"Text: {text}, | Confidence: {confidence}")
        if showBoundingBox:
            topLeft = tuple(map(int, bbox[0]))  # grab corners of bbox
            topRight = tuple(map(int, bbox[1]))
            bottomLeft = tuple(map(int, bbox[2]))
            bottomRight = tuple(map(int, bbox[3]))

            # Draw box
            pts = np.array([topLeft, topRight, bottomLeft, bottomRight], dtype=np.int32)
            cv2.polylines(imgAnnotated, [pts], isClosed=True, color=[0,255,0], thickness=2)

            # draw text bove box
            cv2.putText(imgAnnotated, text, topLeft, cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(255,0,0), thickness=2)
    
    if showBoundingBox:
        plt.figure(figsize=(10, 15))
        plt.imshow(imgAnnotated)
        plt.axis('off')
        plt.title("Receipt OCR - Bounding Boxes")
        plt.show()
    print("End test")

testEasyOCR(img, True)
testEasyOCR(img2, True)
testEasyOCR(img3, True)
testEasyOCR(img4, True)
