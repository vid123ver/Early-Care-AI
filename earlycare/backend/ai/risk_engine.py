def compute_risk_score(metrics):
    """
    Compute a risk score and level based on medical metrics.
    metrics: dict with keys like 'glucose', 'cholesterol', 'hemoglobin', 'blood_pressure'
    Returns: dict with risk_score, risk_level, important_markers
    """
    score = 0
    important = []
    # Example thresholds (customize as needed)
    if 'glucose' in metrics:
        val = metrics['glucose']
        if val < 100:
            score += 10
        elif val < 126:
            score += 30
            important.append('glucose')
        else:
            score += 50
            important.append('glucose')
    if 'cholesterol' in metrics:
        val = metrics['cholesterol']
        if val < 200:
            score += 10
        elif val < 240:
            score += 25
            important.append('cholesterol')
        else:
            score += 40
            important.append('cholesterol')
    if 'hemoglobin' in metrics:
        val = metrics['hemoglobin']
        if val < 12:
            score += 30
            important.append('hemoglobin')
        elif val > 17:
            score += 20
            important.append('hemoglobin')
        else:
            score += 10
    if 'blood_pressure' in metrics:
        val = metrics['blood_pressure']
        if val < 120:
            score += 10
        elif val < 140:
            score += 25
            important.append('blood_pressure')
        else:
            score += 40
            important.append('blood_pressure')
    # Normalize score to 0-100
    risk_score = min(score, 100)
    if risk_score < 30:
        risk_level = 'Low'
    elif risk_score < 70:
        risk_level = 'Moderate'
    else:
        risk_level = 'High'
    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'important_markers': important
    }
