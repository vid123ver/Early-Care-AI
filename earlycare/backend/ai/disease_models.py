import os

import joblib
import pandas as pd

from config import MODEL_FOLDER, MODEL_NAMES

models = {}


def load_models():
    global models
    models = {}
    for name in MODEL_NAMES:
        path = os.path.join(MODEL_FOLDER, f"{name}.joblib")
        if os.path.exists(path):
            models[name.split("_")[0]] = joblib.load(path)
    return models


def predict_payload(data):
    model_type = data["type"]

    report = data["features"]
    symptoms = data["symptoms"]
    history = data["history"]

    full_input = report + symptoms + history

    saved = models[model_type]

    model = saved["model"]
    feature_names = saved["features"]

    if len(full_input) != len(feature_names):
        return {
            "error": f"Expected {len(feature_names)} features, got {len(full_input)}"
        }, 400

    input_df = pd.DataFrame([full_input], columns=feature_names)
    prediction = model.predict(input_df)

    return {
        "prediction": int(prediction[0]),
        "status": "success"
    }, 200


def predict_from_metrics(metrics, disease_type):
    """
    metrics: dict of extracted values from PDF
    disease_type: 'diabetes', 'heart', or 'liver'
    Returns: dict with prediction and probability
    """
    if disease_type not in models:
        return {"error": f"Model for {disease_type} not loaded"}
    model_obj = models[disease_type]
    model = model_obj["model"]
    feature_names = model_obj["features"]
    # Prepare input in correct order, fill missing with 0
    input_row = [metrics.get(f, 0) for f in feature_names]
    input_df = pd.DataFrame([input_row], columns=feature_names)
    pred = model.predict(input_df)[0]
    if hasattr(model, "predict_proba"):
        proba = float(model.predict_proba(input_df)[0][1])
    else:
        proba = None
    return {
        "prediction": int(pred),
        "probability": proba,
        "status": "success"
    }


try:
    load_models()
    print("✅ All models (22-feature versions) loaded successfully!")
except Exception as e:
    print(f"❌ Error loading models: {e}")
