def calculate_health_score(prediction_result, risk_score, abnormal_markers, lifestyle_recommendations):
    """
    Returns a health score (0-100), category, and advice string.
    """
    # Start with a base score
    score = 100
    # Deduct for high-risk prediction
    if prediction_result.get('prediction', 0) == 1:
        score -= 30
    # Deduct based on risk score
    risk = risk_score.get('risk_score', 0)
    if risk >= 70:
        score -= 30
    elif risk >= 30:
        score -= 15
    # Deduct for each abnormal marker
    score -= 5 * len(abnormal_markers)
    # Bonus for positive lifestyle recommendations
    if lifestyle_recommendations:
        score += 5
    # Clamp score between 0 and 100
    score = max(0, min(100, score))
    # Category
    if score >= 80:
        category = 'Good'
        advice = 'Maintain current lifestyle'
    elif score >= 60:
        category = 'Moderate'
        advice = 'Consider minor improvements'
    else:
        category = 'Needs Attention'
        advice = 'Consult a healthcare professional and improve habits'
    return {
        'health_score': score,
        'category': category,
        'advice': advice
    }
