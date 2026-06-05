def generate_doctor_report(
    patient_summary,
    predicted_conditions,
    risk_level,
    important_markers,
    doctor_recommendations
):
    """
    Generate a structured doctor-style medical report.
    """
    return {
        "patient_summary": patient_summary,
        "predicted_conditions": predicted_conditions,
        "risk_level": risk_level,
        "important_markers": important_markers,
        "doctor_recommendations": doctor_recommendations
    }

# Example usage:
# report = generate_doctor_report(
#     patient_summary="Patient shows moderate risk for diabetes and high cholesterol.",
#     predicted_conditions=["diabetes", "hypercholesterolemia"],
#     risk_level="Moderate",
#     important_markers=["glucose", "cholesterol"],
#     doctor_recommendations=["Increase physical activity", "Reduce sugar intake", "Follow up in 3 months"]
# )
