import os

try:
    from dotenv import load_dotenv

    # Load environment variables from .env (if present) before importing routes/db.
    load_dotenv()
except Exception:
    # `python-dotenv` is optional; app can still run with env vars set by the shell.
    pass

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pytesseract
from PIL import Image
import re
import numpy as np
import pandas as pd

from routes.auth_routes import auth_bp
from routes.pdf_routes import pdf_bp
from routes.user_routes import user_bp
from routes.chat_routes import chat_bp
from routes.dashboard_routes import dashboard_bp
from routes.symptom_routes import symptom_bp
from routes.treatment_routes import treatment_bp
from routes.diet_routes import diet_bp
from routes.report_pdf_routes import report_pdf_bp

app = Flask(__name__)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5177")
CORS(
    app,
    supports_credentials=True,
    resources={r"/*": {"origins": FRONTEND_ORIGIN}}
)

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", FRONTEND_ORIGIN)
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
    return response

# Global OPTIONS handler for CORS preflight
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 200
# 1. Configuration for Folder Paths
UPLOAD_FOLDER = 'uploads'
MODEL_FOLDER = 'models'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# NOTE: If you are on Windows, update this path to your Tesseract installation
# Example: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 2. Load the trained ML Models
# Each model now expects 22 features based on our updated train_models.py
models = {}
try:
    model_names = ["diabetes_model", "heart_model", "liver_model"]
    for name in model_names:
        path = os.path.join(MODEL_FOLDER, f'{name}.joblib')
        if os.path.exists(path):
            models[name.split('_')[0]] = joblib.load(path)
    print("✅ All models (22-feature versions) loaded successfully!")
except Exception as e:
    print(f"❌ Error loading models: {e}")

@app.route('/')
def home():
    return "EarlyCare Backend (v2.0) is Running!"

# 3. Route for Combined Prediction (Report + Symptoms + History)
@app.route('/predict', methods=['POST'])
def predict():

    data = request.json
    model_type = data["type"]

    report = data["features"]
    symptoms = data["symptoms"]
    history = data["history"]

    full_input = report + symptoms + history

    saved = models[model_type]

    model = saved["model"]
    feature_names = saved["features"]

    if len(full_input) != len(feature_names):

        return jsonify({
            "error": f"Expected {len(feature_names)} features, got {len(full_input)}"
        }), 400

    input_df = pd.DataFrame([full_input], columns=feature_names)

    prediction = model.predict(input_df)

    return jsonify({
        "prediction": int(prediction[0]),
        "status": "success"
    })
    
# 4. Route for Image Upload and OCR Extraction
@app.route('/upload', methods=['POST'])
def upload_report():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Save the file temporarily
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Perform OCR using Tesseract
        # Methodology: LSTM-based character recognition
        raw_text = pytesseract.image_to_string(Image.open(filepath))
        
        # Use Regex to extract all numbers (integers and decimals)
        extracted_numbers = re.findall(r'\d+\.\d+|\d+', raw_text)
        
        return jsonify({
            "message": "File processed successfully",
            "extracted_text": raw_text[:500], # Return first 500 chars for preview
            "numbers": extracted_numbers
        })

    except Exception as e:
        print(f"OCR Error: {e}")
        return jsonify({"error": str(e)}), 500

# Register the authentication blueprint
app.register_blueprint(auth_bp)

# Register the PDF upload blueprint
app.register_blueprint(pdf_bp)

# Register the user predictions blueprint
app.register_blueprint(user_bp)

# Register the chat routes blueprint
app.register_blueprint(chat_bp)

# Register the dashboard routes blueprint
app.register_blueprint(dashboard_bp)

# Register the symptom checker blueprint
app.register_blueprint(symptom_bp)

# Register treatment suggestions blueprint
app.register_blueprint(treatment_bp)

# Register diet recommendation blueprint
app.register_blueprint(diet_bp)

# Register downloadable PDF report blueprint
app.register_blueprint(report_pdf_bp)

if __name__ == '__main__':
    # Use Render's injected PORT when available, otherwise fall back locally.
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5002)))


