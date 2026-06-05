from transformers import pipeline

# Load summarization pipeline (using a small model for speed)
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def generate_medical_summary(report_text, max_length=120, min_length=30):
    """
    Generate a short medical summary from extracted report text.
    """
    summary = summarizer(report_text, max_length=max_length, min_length=min_length, do_sample=False)[0]['summary_text']
    return summary

def explain_prediction(disease, metrics):
    """
    Return a simple explanation for the predicted disease based on metrics.
    """
    explanations = {
        'diabetes': f"High glucose value ({metrics.get('glucose', 'N/A')}) may indicate diabetes risk.",
        'heart': f"Elevated cholesterol ({metrics.get('cholesterol', 'N/A')}) may indicate heart disease risk.",
        'liver': f"Abnormal hemoglobin ({metrics.get('hemoglobin', 'N/A')}) may indicate liver issues."
    }
    return explanations.get(disease, "No specific explanation available.")

def summarize_prediction(model_type, prediction):
    if prediction == 1:
        return f"{model_type} model indicates high risk."
    return f"{model_type} model indicates low risk or normal."
