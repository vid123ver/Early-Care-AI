def generate_health_insights(prediction_result, risk_score_info, abnormal_markers, medical_explanations):
    """
    Combine prediction, risk, markers, and explanations into a health insights report.
    prediction_result: dict (e.g., {"prediction": 1, "probability": 0.82})
    risk_score_info: dict (e.g., {"risk_score": 72, "risk_level": "Moderate", ...})
    abnormal_markers: list of marker names (e.g., ["cholesterol", "glucose"])
    medical_explanations: dict of explanations per marker
    Returns: dict with overall health, top concerns, recommended tests, lifestyle suggestions
    """
    # Overall health
    overall_health = f"{risk_score_info.get('risk_level', 'Unknown')} risk"
    # Top concerns
    top_concerns = abnormal_markers or []
    # Recommend tests based on markers
    recommended_tests = []
    if 'glucose' in abnormal_markers:
        recommended_tests.append('HbA1c')
    if 'cholesterol' in abnormal_markers:
        recommended_tests.append('lipid profile')
    if 'hemoglobin' in abnormal_markers:
        recommended_tests.append('CBC')
    # Aggregate lifestyle suggestions from explanations
    lifestyle_suggestions = []
    for marker in abnormal_markers:
        recs = medical_explanations.get(marker, {}).get('recommendations', [])
        if isinstance(recs, list):
            lifestyle_suggestions.extend(recs)
    # Deduplicate and simplify
    lifestyle_suggestions = list(set(lifestyle_suggestions))
    return {
        'overall_health': overall_health,
        'top_concerns': top_concerns,
        'recommended_tests': recommended_tests,
        'lifestyle_suggestions': lifestyle_suggestions
    }
