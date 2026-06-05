from transformers import pipeline

# Use a small LLM for demo; swap with a larger model or OpenAI for production
llm = pipeline("text-generation", model="gpt2")

# Example medical knowledge prompt template
def build_prompt(marker, value, status):
    return (
        f"Marker: {marker}\n"
        f"Value: {value} ({status})\n"
        "Explain what this value means for health.\n"
        "List possible diseases if abnormal.\n"
        "List lifestyle risks.\n"
        "Suggest preventive actions.\n"
        "Format as JSON with keys: explanation, possible_conditions, recommendations."
    )

def explain_marker(marker, value, status):
    prompt = build_prompt(marker, value, status)
    response = llm(prompt, max_length=256, do_sample=False)[0]['generated_text']
    # Try to extract JSON from the response (very basic)
    import re, json
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            return {marker: {"status": status, **json.loads(match.group(0))}}
        except Exception:
            pass
    # Fallback: return raw text
    return {marker: {"status": status, "explanation": response}}

def explain_abnormal_metrics(metrics_status):
    """
    metrics_status: dict of {marker: (value, status)}
    Returns: dict of explanations for each abnormal marker
    """
    results = {}
    for marker, (value, status) in metrics_status.items():
        if status != "Normal":
            results.update(explain_marker(marker, value, status))
    return results
