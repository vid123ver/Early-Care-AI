from flask import Blueprint, jsonify, request, g

from database.mongo import fetch_reports_by_user
from routes.auth_routes import token_required

treatment_bp = Blueprint("treatment", __name__, url_prefix="/treatment")


# Non-prescription (OTC) guidance only. Keep it conservative.
TREATMENT_LIBRARY = {
    "Common Cold": {
        "otc": [
            {
                "name": "Paracetamol (Acetaminophen)",
                "use_for": ["fever", "sore throat", "body ache"],
                "adult_max_per_day_mg": 3000,
                "notes": [
                    "Avoid combining multiple products that contain acetaminophen.",
                    "Avoid if you have severe liver disease or heavy alcohol use.",
                ],
            },
            {
                "name": "Cetirizine (antihistamine)",
                "use_for": ["runny nose", "sneezing"],
                "adult_dose": "10 mg once daily",
                "notes": ["May cause drowsiness in some people."],
            },
        ],
        "home_remedies": [
            "Warm fluids and rest",
            "Salt-water gargles for sore throat",
            "Steam inhalation / humidifier for congestion",
        ],
    },
    "Flu (Influenza)": {
        "otc": [
            {
                "name": "Paracetamol (Acetaminophen)",
                "use_for": ["fever", "body ache", "headache"],
                "adult_max_per_day_mg": 3000,
                "notes": ["Avoid combining multiple products that contain acetaminophen."],
            },
            {
                "name": "Ibuprofen (NSAID)",
                "use_for": ["fever", "body ache"],
                "adult_max_per_day_mg": 1200,
                "notes": [
                    "Avoid if you have stomach ulcers, kidney disease, or are on blood thinners.",
                    "Take with food.",
                ],
            },
        ],
        "home_remedies": ["Rest", "Oral fluids", "Warm soups", "Monitor fever and hydration"],
    },
    "COVID-19": {
        "otc": [
            {
                "name": "Paracetamol (Acetaminophen)",
                "use_for": ["fever", "body ache"],
                "adult_max_per_day_mg": 3000,
                "notes": ["Avoid combining multiple products that contain acetaminophen."],
            }
        ],
        "home_remedies": [
            "Rest and hydration",
            "Isolate per local guidance if infectious symptoms",
            "Monitor oxygen if available",
        ],
    },
    "Allergy (Rhinitis)": {
        "otc": [
            {
                "name": "Cetirizine (antihistamine)",
                "use_for": ["sneezing", "runny nose", "itchy eyes"],
                "adult_dose": "10 mg once daily",
                "notes": ["May cause drowsiness in some people."],
            },
            {
                "name": "Saline nasal spray",
                "use_for": ["congestion"],
                "notes": ["Safe, non-medicated option."],
            },
        ],
        "home_remedies": [
            "Avoid triggers (dust/pollen/pets if suspected)",
            "Rinse nose with saline",
        ],
    },
    "Gastritis / Food Poisoning": {
        "otc": [
            {
                "name": "Oral Rehydration Solution (ORS)",
                "use_for": ["diarrhea", "vomiting", "dehydration prevention"],
                "notes": ["Small frequent sips if nausea/vomiting."],
            },
            {
                "name": "Bismuth subsalicylate (if available)",
                "use_for": ["diarrhea", "nausea"],
                "notes": [
                    "Avoid if allergic to aspirin, on blood thinners, or with certain viral infections in children.",
                ],
            },
        ],
        "home_remedies": [
            "Clear fluids and ORS",
            "Bland foods when tolerating (rice, toast, bananas)",
            "Avoid alcohol, spicy/fatty foods for 24–48h",
        ],
    },
    "Migraine": {
        "otc": [
            {
                "name": "Ibuprofen (NSAID)",
                "use_for": ["headache pain"],
                "adult_max_per_day_mg": 1200,
                "notes": ["Take early in attack; avoid if ulcers/kidney disease/blood thinners."],
            },
            {
                "name": "Paracetamol (Acetaminophen)",
                "use_for": ["headache pain"],
                "adult_max_per_day_mg": 3000,
                "notes": ["Avoid combining multiple products that contain acetaminophen."],
            },
        ],
        "home_remedies": [
            "Rest in a dark, quiet room",
            "Hydrate",
            "Cold compress on forehead",
        ],
    },
}


DEFAULT_ALERTS = [
    "If symptoms are severe, worsening, or lasting more than 2–3 days, consult a doctor.",
    "Seek urgent care for chest pain, trouble breathing, fainting, severe dehydration, or confusion.",
]


def _consult_alerts(symptoms_text, red_flags):
    symptoms_text = (symptoms_text or "").lower()
    alerts = []
    alerts.extend(red_flags or [])
    if "pregnan" in symptoms_text:
        alerts.append("If pregnant, consult a clinician before taking medicines.")
    if "child" in symptoms_text or "baby" in symptoms_text:
        alerts.append("For children, dosing differs—consult a clinician or pharmacist.")
    return alerts


def _metric_flags(all_reports):
    """Very simple, conservative flags based on all past reports."""
    diabetes_flag = False
    chol_flag = False
    liver_flag = False
    latest_metrics = {}

    for idx, r in enumerate(all_reports):
        metrics = r.get("metrics", {}) or {}
        if idx == 0:
            latest_metrics = metrics
        m_lower = {str(k).lower(): v for k, v in metrics.items()}

        g_val = m_lower.get("glucose") or m_lower.get("fasting_glucose") or m_lower.get("fbs")
        hba1c = m_lower.get("hba1c") or m_lower.get("hb1ac")
        if (isinstance(g_val, (int, float)) and g_val >= 126) or (
            isinstance(hba1c, (int, float)) and hba1c >= 6.5
        ):
            diabetes_flag = True

        chol = m_lower.get("cholesterol") or m_lower.get("total_cholesterol")
        ldl = m_lower.get("ldl")
        if (isinstance(chol, (int, float)) and chol >= 240) or (
            isinstance(ldl, (int, float)) and ldl >= 160
        ):
            chol_flag = True

        alt = m_lower.get("alt") or m_lower.get("sgpt")
        ast = m_lower.get("ast") or m_lower.get("sgot")
        bili = m_lower.get("bilirubin")
        if (
            (isinstance(alt, (int, float)) and alt > 40)
            or (isinstance(ast, (int, float)) and ast > 40)
            or (isinstance(bili, (int, float)) and bili > 1.2)
        ):
            liver_flag = True

    return diabetes_flag, chol_flag, liver_flag, latest_metrics


@treatment_bp.route("/suggest", methods=["POST"])
@token_required
def suggest_treatment():
    data = request.json or {}
    condition = (data.get("condition") or "").strip()
    symptoms_text = data.get("symptoms_text") or ""
    red_flags = data.get("red_flags") or []

    # Pull user's past reports so we can adjust safety messages based on labs.
    user = getattr(g, "current_user", None)
    user_id = str(user.get("_id")) if user else None
    reports = fetch_reports_by_user(user_id, limit=50) if user_id else []
    diabetes_flag, chol_flag, liver_flag, latest_metrics = _metric_flags(reports)

    report_context = {
        "total_reports": len(reports),
        "flags": {
            "diabetes_profile": diabetes_flag,
            "high_cholesterol_profile": chol_flag,
            "liver_profile": liver_flag,
        },
        "latest_metrics": latest_metrics,
    }

    consult_alerts = _consult_alerts(symptoms_text, red_flags) + DEFAULT_ALERTS
    # Add extra caution messages based on report patterns.
    if diabetes_flag:
        consult_alerts.append(
            "Your past reports suggest high blood sugar / HbA1c – discuss diabetes management and medicines with your doctor."
        )
    if chol_flag:
        consult_alerts.append(
            "Your past reports suggest high cholesterol – focus on long-term heart and cholesterol treatment with your doctor, not only symptom relief."
        )
    if liver_flag:
        consult_alerts.append(
            "Your past reports suggest possible liver involvement – avoid or limit medicines that can affect the liver unless your doctor says they are safe (for example, some painkillers and high-dose paracetamol)."
        )

    if not condition:
        return jsonify({"error": "condition is required"}), 400

    payload = TREATMENT_LIBRARY.get(condition)
    if not payload:
        return jsonify({
            "condition": condition,
            "otc": [],
            "home_remedies": [],
            "dosage_awareness": [
                "Use medicines only as directed on the label.",
                "Avoid mixing multiple cold/flu products with overlapping ingredients.",
                "Consult a doctor before taking any new medicine or supplement, especially if you have other health conditions.",
            ],
            "consult_doctor_alerts": consult_alerts,
            "report_context": report_context,
            "disclaimer": "Non-prescription, general information only – not a diagnosis or prescription. Consult a doctor before taking any medication or supplement.",
        }), 200

    dosage_awareness = [
        "Do not exceed label directions.",
        "Avoid mixing multiple OTC products that share the same active ingredient.",
        "Consult a doctor before taking any new medicine or supplement, especially if you have chronic illness (liver/kidney disease, ulcers, blood thinners, pregnancy, etc.).",
    ]

    return jsonify({
        "condition": condition,
        "otc": payload.get("otc", []),
        "home_remedies": payload.get("home_remedies", []),
        "dosage_awareness": dosage_awareness,
        "consult_doctor_alerts": consult_alerts,
        "report_context": report_context,
        "disclaimer": "Non-prescription, general information only – not a diagnosis or prescription. Consult a doctor before taking any medication or supplement.",
    }), 200

