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

def order_points(pts):
    """Orders the 4 corner points as: top-left, top-right, bottom-right, bottom-left"""
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # Top-left     (smallest x+y sum)
    rect[2] = pts[np.argmax(s)]   # Bottom-right (largest x+y sum)

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right    (smallest y-x diff)
    rect[3] = pts[np.argmax(diff)]  # Bottom-left  (largest y-x diff)

    return rect


def four_point_transform(image, pts):
    """Applies a perspective transform to get a flat top-down view of the receipt"""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Calculate the width of the output image
    widthA  = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB  = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # Calculate the height of the output image
    heightA  = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB  = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # Define destination points for the flat top-down view
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    # Compute and apply the perspective transform
    M       = cv2.getPerspectiveTransform(rect, dst)
    warped  = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    return warped

def crop_receipt(image):
    """Crops the receipt to aid OCR detection and remove artifacts from image."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    img_h, img_w = image.shape[:2]
    min_area = (img_h * img_w) * 0.10
    kernel = np.ones((20, 20), np.uint8)

    # ── Method 1: Otsu Bright (white receipt on dark background) ────────────
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    result = _find_and_crop(image, closed, min_area)
    if result is not None:
        print("Otsu Bright succeeded")
        return result

    # ── Method 2: Otsu Inverse (dark receipt on bright background) ──────────
    _, thresh_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    closed_inv = cv2.morphologyEx(thresh_inv, cv2.MORPH_CLOSE, kernel)
    result = _find_and_crop(image, closed_inv, min_area)
    if result is not None:
        print("Otsu Inverse succeeded")
        return result

    # ── Fallback: Content Density ────────────────────────────────────────────
    print("Warning: Otsu methods failed — falling back to content density")
    return _convex_hull_fallback(image, gray)


def expand_contour(pts, img_w, img_h, scale_x=1.25, scale_y=1.05):
    """
    Current crop function often cuts into the sides of the receipt, so this
    function takes the corners, width, and height to scale the bounding boc
    """
    # Find the center of the 4 points
    center = pts.mean(axis=0)

    # Create separate scale factors for x (width) and y (height)
    scales = np.array([scale_x, scale_y])

    # Move each corner away from the center by respective scale factors
    expanded = center + scales * (pts - center)

    # Clamp so the expanded points don't go outside the image bounds
    expanded[:, 0] = np.clip(expanded[:, 0], 0, img_w - 1)  # x within width
    expanded[:, 1] = np.clip(expanded[:, 1], 0, img_h - 1)  # y within height

    return expanded.astype("float32")

def _find_and_crop(image, mask, min_area):
    img_h, img_w = image.shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Drop anything too small to be a receipt
    large = sorted(
        [c for c in contours if cv2.contourArea(c) >= min_area],
        key=cv2.contourArea,
        reverse=True
    )
    if not large:
        return None

    # 1. Artifact Filter 
    # If the largest contour is 3x bigger than the next, it's clearly the
    # receipt so drop all others outright. This gets rid of small artifacts.
    if len(large) > 1:
        size_ratio = cv2.contourArea(large[0]) / cv2.contourArea(large[1])
        if size_ratio >= 3.0:
            large = [large[0]]  # Dominant receipt found - discard artifact
            print(f"  → Artifact dropped (size ratio: {size_ratio:.1f}x)")

    # 2. Receipt Score
    # Among remaining candidates, prefer the most rectangle-like shape.
    # Receipts are tall, solid rectangles. Artifacts rarely are.
    def receipt_score(c):
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        # How much of its own bounding box does the contour fill?
        rectangularity = area / (w * h) if (w * h) > 0 else 0
        # Receipts are portrait-ish so penalize very square or very thin shapes
        aspect = max(w, h) / max(min(w, h), 1)
        aspect_score = 1.0 if 1.5 <= aspect <= 8.0 else 0.5
        # Weight by size relative to image
        normalized_area = area / (img_h * img_w)
        return normalized_area * rectangularity * aspect_score

    best = max(large[:5], key=receipt_score)
    score = receipt_score(best)
    print(f"  → Best contour score: {score:.4f} (area: {cv2.contourArea(best) / (img_h * img_w) * 100:.1f}% of image)")

    # 4-Sided Check: try progressively looser epsilon values
    perimeter       = cv2.arcLength(best, True)
    receipt_contour = None

    for epsilon_factor in [0.02, 0.04, 0.06, 0.08, 0.10]:
        approx = cv2.approxPolyDP(best, epsilon_factor * perimeter, True)
        if len(approx) == 4:
            receipt_contour = approx.reshape(4, 2).astype("float32")
            print(f"  → 4-sided contour found (epsilon={epsilon_factor})")
            break

    # Force 4 Corners via minAreaRect if approxPolyDP still failed
    # minAreaRect always returns exactly 4 corners — never falls through
    if receipt_contour is None:
        rect            = cv2.minAreaRect(best)
        receipt_contour = cv2.boxPoints(rect).astype("float32")
        print("  → No 4-sided contour found — forced 4 corners via minAreaRect")

    receipt_contour = expand_contour(receipt_contour, img_w, img_h, scale_x=1.25, scale_y=1.05)  # expand bounding box width by 25%
    return four_point_transform(image, receipt_contour)


def _convex_hull_fallback(image, gray):
    """Wraps the convex hull of all detected content as a last resort."""
    laplacian   = cv2.Laplacian(gray, cv2.CV_64F)
    content_map = np.abs(laplacian).astype(np.uint8)
    _, mask     = cv2.threshold(content_map, 10, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("  → No content found at all — returning full image")
        return image

    all_pts = np.vstack(contours)
    hull    = cv2.convexHull(all_pts)
    x, y, w, h = cv2.boundingRect(hull)
    return image[y:y+h, x:x+w]

def deskew1(image):  # Hough Lines method
    """
    This first deskew method relies on the Hough Line method. It runs Canny edge detection
    to find edges, ideally along the top and bottom of each character in lines of text.
    Every edge then casts a vote (like a classifier) on which lines can pass through them.
    When many edges are along a line, this line will have a high score, and text produces
    a lot of these edges in a line. However, testing has found that deep creases can
    "trick" the Hough Line method by creating their own edges that are off-centered.
    The result is that this method actually further skews the receipt.
    It remains for testing purposes, as it works very well when there are no creases.
    """
    edges = cv2.Canny(image, 50, 150, apertureSize=3)  # edge detection
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180,
                             threshold=80,
                             minLineLength=100,
                             maxLineGap=10)

    if lines is None:
        print("  - No lines found for deskew; returning as-is")
        return image

    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if -30 < angle < 30:  # Only near-horizontal lines (text baselines)
            angles.append(angle)

    if not angles:
        print("  - No horizontal lines detected;  returning as-is")
        return image

    median_angle = np.median(angles)
    print(f"  - Deskew angle: {median_angle:.2f}°")

    if abs(median_angle) < 0.5:
        print("  - Skew negligible;  no rotation needed")
        return image

    (h, w) = image.shape
    center   = (w // 2, h // 2)
    M        = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    deskewed = cv2.warpAffine(image, M, (w, h),
                               flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)
    return deskewed

def deskew2(image):  # Projection Profile method
    """
    This 2nd deskew method follows the Projection Profile method. This method
    rotates the image at many small trial angles and sums pixel values row by row
    since at the best angle, text will produce high variance between dark text rows
    and white space between rows. This method is preferred to the Hough Line method
    because it is unaffected by deep creases in the receipt!
    """
    # Step 1: Narrow search range
    # The perspective transform already corrected large rotations.
    # We only need to fix small residual skew, so searching beyond
    # +/- 6 degrees is almost certainly a crease, not real skew.
    search_range = np.arange(-6, 6.5, 0.25)  # 6 degree range, 0.25 step size
    best_angle   = 0
    best_score   = -1

    for angle in search_range:
        # Step 2: Rotate the image at this trial angle
        (h, w)   = image.shape
        center   = (w // 2, h // 2)
        M        = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated  = cv2.warpAffine(image, M, (w, h),
                                   flags=cv2.INTER_CUBIC,
                                   borderMode=cv2.BORDER_REPLICATE)

        # Step 3: Sum pixel values across each row
        # Dark text pixels = low values, white space = high values
        row_sums = np.sum(rotated, axis=1).astype(np.float32)

        # Step 4: Score = variance of row sums
        # High variance means sharp separation between text rows and white space
        # Low variance means text is smeared across rows = wrong angle
        score = np.var(row_sums)

        if score > best_score:
            best_score = score
            best_angle = angle

    print(f"  → Deskew angle: {best_angle:.2f}°")

    if abs(best_angle) < 0.5:
        print("  → Skew negligible — no rotation needed")
        return image

    # Step 5: Apply the best angle to the original image
    (h, w)   = image.shape
    center   = (w // 2, h // 2)
    M        = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    deskewed = cv2.warpAffine(image, M, (w, h),
                               flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)
    return deskewed

def preprocess(img: np.ndarray):
    img = crop_receipt(img)
    # convert to gray scale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # upscale image
    scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # remove image noise
    denoised = cv2.fastNlMeansDenoising(scaled, h=10)
    # contrast enhanchment, brightening dimmly lit areas without washing out already bright areas
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(denoised)

    
    return deskew2(contrasted)

def testEasyOCR(npImg: np.ndarray, showBoundingBox=False, file="test.txt"):
    npImg = preprocess(npImg)
    results = reader.readtext(npImg)
    imgAnnotated = npImg.copy() if showBoundingBox else None
    with open(file, "w") as f:
        for (bbox, text, confidence) in results:
            print(f"Text: {text}, | Confidence: {confidence}")
            print(text, file=f)

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

def tester(filename: str):
    testEasyOCR(img, True, filename + "1.txt")
    testEasyOCR(img2, True, filename + "2.txt")
    testEasyOCR(img3, True, filename + "3.txt")
    testEasyOCR(img4, True, filename + "4.txt")

if __name__ == "__main__":
    reader = easyocr.Reader(['en'], gpu=False)
    # sometimes image orientation is stored in EXIF metadata, and this is NOT read by default by Image.open()
    # Therefore, all images using Image.open() should also use exif_tranpose in case orientation data is needed
    img = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt1.jpg")))
    img2 = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt2.jpg")))
    img3 = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt3.jpg")))
    img4 = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt4.jpg")))
    img5 = np.array(ImageOps.exif_transpose(Image.open("uploads/receipt5.jpg")))
    tester("results_for_receipt")