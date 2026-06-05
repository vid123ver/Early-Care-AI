import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MODEL_FOLDER = os.path.join(BASE_DIR, "models")
MODEL_NAMES = ["diabetes_model", "heart_model", "liver_model"]
BACKEND_PORT = 5001
