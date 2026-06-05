import os
import re
import pdfplumber

import pytesseract
from PIL import Image
from database.mongo import insert_report

def process_upload(file, upload_folder):
    if "file" not in file:
        return {"error": "No file uploaded"}, 400

    uploaded_file = file["file"]
    if uploaded_file.filename == "":
        return {"error": "No file selected"}, 400

    filepath = os.path.join(upload_folder, uploaded_file.filename)
    uploaded_file.save(filepath)

    raw_text = pytesseract.image_to_string(Image.open(filepath))
    extracted_numbers = re.findall(r"\d+\.\d+|\d+", raw_text)

    return {
        "message": "File processed successfully",
        "extracted_text": raw_text[:500],
        "numbers": extracted_numbers,
    }, 200


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_metrics_from_text(text):
    metrics = {}
    patterns = {
        'glucose': r'(glucose|blood sugar)[^\d]*(\d+\.?\d*)',
        'cholesterol': r'(cholesterol)[^\d]*(\d+\.?\d*)',
        'hemoglobin': r'(hemoglobin)[^\d]*(\d+\.?\d*)',
        # Add more patterns as needed
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                metrics[key] = float(match.group(2)) if '.' in match.group(2) else int(match.group(2))
            except Exception:
                continue
    return metrics


def analyze_pdf_report(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    metrics = extract_metrics_from_text(text)
    if metrics:
        insert_report({'pdf_path': pdf_path, 'metrics': metrics})
    return metrics
