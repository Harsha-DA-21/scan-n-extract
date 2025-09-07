import cv2
import pytesseract
import re
import os
import pandas as pd
from typing import Dict, Optional

# ✅ Configure Tesseract path (update if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Aadhaar image folder
IMAGE_FOLDER = r"D:\PRACTICE FILES\PYTHON\UDHAR CARD SCANER\udhar images"

# Output Excel file
OUTPUT_FILE = r"D:\PRACTICE FILES\PYTHON\UDHAR CARD SCANER\aadhaar_data.xlsx"

# Regex patterns
DOB_PATTERN = re.compile(r"(?:DOB|D\.O\.B\.|Date of Birth)[:\s]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})", re.IGNORECASE)
GENDER_PATTERN = re.compile(r"\b(Male|Female|Others?)\b", re.IGNORECASE)

def clean_lines(text: str):
    """Split OCR text into cleaned lines."""
    return [l.strip() for l in text.splitlines() if l.strip()]

def parse_aadhaar_text(text: str) -> Dict[str, Optional[str]]:
    """Extract Name, DOB, Gender, Address from OCR text."""
    result = {"name": None, "dob": None, "gender": None, "address": None}
    lines = clean_lines(text)

    # Remove footer/junk
    lines = [l for l in lines if "download date" not in l.lower() and "consent" not in l.lower()]

    # DOB or Year of Birth
    for line in lines:
        if "print date" in line.lower():
            continue  # skip print date
        m = DOB_PATTERN.search(line)
        if m:
            result["dob"] = m.group(1)
            break
        # Handle "Year of Birth: 2000"
        yob = re.search(r"(Year of Birth[:\s]*)(\d{4})", line, re.IGNORECASE)
        if yob:
            result["dob"] = yob.group(2)
            break

    # Gender
    for line in lines:
        g = GENDER_PATTERN.search(line)
        if g:
            result["gender"] = g.group(1).title()
            break
        # Fallback for single letters
        if re.search(r"\bM\b", line):
            result["gender"] = "Male"
            break
        if re.search(r"\bF\b", line):
            result["gender"] = "Female"
            break

    # Name (above DOB line)
    if result["dob"]:
        dob_idx = next((i for i, l in enumerate(lines) if result["dob"] in l), None)
        if dob_idx:
            for j in range(dob_idx - 1, -1, -1):
                cand = lines[j]
                if any(k in cand.lower() for k in ["government", "uidai", "dob", "gender", "vid", "aadhaar", "address"]):
                    continue
                if 2 < len(cand) < 40:
                    result["name"] = cand
                    break

    # Address (after "Address:")
    addr_block, capture = [], False
    for line in lines:
        low = line.lower()
        if "address:" in low:
            capture = True
            after = line.split("Address:", 1)[-1].strip()
            if after:
                addr_block.append(after)
            continue
        if capture:
            if (
                low.startswith("vid")
                or "government" in low
                or "uidai" in low
                or "help@" in low
                or re.fullmatch(r"\d[\d\s]{6,}", line)
            ):
                break
            addr_block.append(line)

    if addr_block:
        # Join, normalize spaces
        address = " ".join(addr_block)
        address = re.sub(r"\s+", " ", address).strip()
        # Remove duplicate consecutive words
        words = address.split()
        clean_words = []
        for w in words:
            if not clean_words or clean_words[-1].lower() != w.lower():
                clean_words.append(w)
        result["address"] = " ".join(clean_words)

    return result

def ocr_image(img_path: str) -> str:
    """Run OCR on an image and return text."""
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, lang="eng")

def process_folder(folder: str):
    records = []
    for fname in os.listdir(folder):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(folder, fname)
            text = ocr_image(path)
            data = parse_aadhaar_text(text)
            data["file"] = fname
            records.append(data)
    return records

if __name__ == "__main__":
    records = process_folder(IMAGE_FOLDER)
    df = pd.DataFrame(records)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Extracted data saved to {OUTPUT_FILE}")












































# import re
# from pathlib import Path
# from typing import Dict, List, Optional

# from PIL import Image, ImageOps
# import pytesseract

# # --- If Tesseract is not on PATH (Windows), set its path here ---
# # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# DOB_PATTERN = re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b")
# GENDER_PATTERN = re.compile(r"\b(MALE|FEMALE|TRANSGENDER)\b", re.IGNORECASE)

# def ocr(path: Path, lang: str = "eng") -> str:
#     """Run OCR on an image path and return raw text."""
#     img = Image.open(path)
#     try:
#         img = ImageOps.exif_transpose(img)  # correct orientation if needed
#     except Exception:
#         pass
#     return pytesseract.image_to_string(img, lang=lang)

# def clean_lines(text: str) -> List[str]:
#     lines = [re.sub(r"[^\x20-\x7E]", "", l) for l in text.splitlines()]
#     lines = [l.strip() for l in lines if l.strip()]
#     return lines

# def parse_from_combined_text(text: str) -> Dict[str, Optional[str]]:
#     result = {"name": None, "dob": None, "gender": None, "address": None}
#     t = text.replace("\r", "")
#     lines = clean_lines(t)

#     # DOB
#     dob_match = DOB_PATTERN.search(t)
#     if dob_match:
#         result["dob"] = dob_match.group(1)

#     # Gender
#     g = GENDER_PATTERN.search(t)
#     if g:
#         result["gender"] = g.group(1).title()

#     # Name (line above DOB)
#     if dob_match:
#         dob_idx = next((i for i, l in enumerate(lines) if dob_match.group(1) in l), None)
#         if dob_idx is not None:
#             for j in range(dob_idx - 1, max(-1, dob_idx - 4), -1):
#                 cand = lines[j]
#                 if any(k in cand.lower() for k in ["government", "uidai", "dob", "issue date", "gender", "vid", "aadhaar"]):
#                     continue
#                 if len(cand) <= 40:
#                     result["name"] = cand
#                     break

#     # Address
#     addr_block, capture = [], False
#     for line in lines:
#         low = line.lower()
#         if "address:" in low:
#             capture = True
#             after = line.split("Address:", 1)[-1].strip()
#             if after:
#                 addr_block.append(after)
#             continue
#         if capture:
#             if (
#                 low.startswith("vid")
#                 or "government" in low
#                 or "uidai" in low
#                 or re.fullmatch(r"\d[\d\s]{6,}", line)
#                 or "help@" in low
#                 or "download date" in low
#             ):
#                 break
#             addr_block.append(line)
#     if addr_block:
#         address = ", ".join(addr_block)
#         address = re.sub(r"\s*,\s*", ", ", address)
#         address = re.sub(r"\s{2,}", " ", address)
#         result["address"] = address

#     return result

# def extract_from_images(front_image: Path, back_image: Path) -> Dict[str, Optional[str]]:
#     raw_front = ocr(front_image, lang="eng")
#     raw_back = ocr(back_image, lang="eng")
#     combined = raw_front + "\n" + raw_back
#     return parse_from_combined_text(combined)

# if __name__ == "__main__":
#     front = Path(r"D:\PRACTICE FILES\PYTHON\UDHAR CARD SCANER\mf.jpg")
#     back  = Path(r"D:\PRACTICE FILES\PYTHON\UDHAR CARD SCANER\mb.jpg")

#     fields = extract_from_images(front, back)

#     print("\nExtracted Info:")
#     print(f"Name   : {fields.get('name')}")
#     print(f"DOB    : {fields.get('dob')}")
#     print(f"Gender : {fields.get('gender')}")
#     print(f"Address: {fields.get('address')}")
