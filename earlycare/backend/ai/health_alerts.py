def generate_health_alerts(metrics):
    alerts = []
    if metrics.get('glucose', 0) > 200:
        alerts.append('High glucose level detected')
        alerts.append('Possible diabetes risk')
    if metrics.get('cholesterol', 0) > 240:
        alerts.append('High cholesterol level detected')
        alerts.append('Possible heart disease risk')
    if metrics.get('hemoglobin', 20) < 12:
        alerts.append('Low hemoglobin detected')
        alerts.append('Possible anemia risk')
    # Add more rules as needed
    return {'alerts': alerts}
