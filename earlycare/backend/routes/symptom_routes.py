from flask import Blueprint, jsonify, request

from routes.auth_routes import token_required

symptom_bp = Blueprint("symptom", __name__, url_prefix="/symptom")


# Simple, explainable symptom→condition mapping.
# Output is normalized into probability-like scores.
CONDITIONS = {
    "Common Cold": {
        "symptoms": {"runny nose", "sneezing", "sore throat", "cough", "congestion"},
        "followups": ["Do you have a fever?", "Are your symptoms mild and improving?"],
    },
    "Flu (Influenza)": {
        "symptoms": {"fever", "chills", "body ache", "fatigue", "dry cough", "headache"},
        "followups": ["Did symptoms start suddenly?", "Any severe muscle aches?"],
    },
    "COVID-19": {
        "symptoms": {"fever", "cough", "loss of smell", "loss of taste", "fatigue", "sore throat"},
        "followups": ["Any loss of smell/taste?", "Any close contact exposure recently?"],
    },
    "Gastritis / Food Poisoning": {
        "symptoms": {"nausea", "vomiting", "diarrhea", "stomach pain", "cramps"},
        "followups": ["Any recent outside/unsafe food?", "Any blood in stool?"],
    },
    "Migraine": {
        "symptoms": {"headache", "nausea", "light sensitivity", "sound sensitivity"},
        "followups": ["Is the headache one-sided and throbbing?", "Any visual aura?"],
    },
    "Allergy (Rhinitis)": {
        "symptoms": {"sneezing", "itchy eyes", "runny nose", "congestion"},
        "followups": ["Do symptoms worsen with dust/pollen/pets?", "Any itchy eyes?"],
    },
}

RED_FLAGS = [
    ("chest pain", "Chest pain can be serious. Consider urgent medical evaluation."),
    ("shortness of breath", "Breathing difficulty can be serious. Consider urgent medical evaluation."),
    ("fainting", "Fainting can be serious. Consider urgent medical evaluation."),
    ("severe bleeding", "Severe bleeding requires urgent medical evaluation."),
]


def _tokenize(text):
    if not text:
        return set()
    # Keep it simple: split by commas/newlines and also by spaces.
    parts = []
    for chunk in str(text).lower().replace("\n", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    tokens = set()
    for p in parts:
        if len(p) <= 2:
            continue
        tokens.add(p)
        # Add some word-level tokens too
        for w in p.split():
            if len(w) > 2:
                tokens.add(w)
    return tokens


def _scores_from_symptoms(symptoms_set):
    scored = []
    for name, cfg in CONDITIONS.items():
        known = cfg["symptoms"]
        overlap = len(symptoms_set & known)
        if overlap <= 0:
            raw = 0.05  # tiny prior
        else:
            # weighted overlap + small prior
            raw = 0.2 + (overlap / max(1, len(known))) * 0.8
        scored.append((name, raw, overlap, len(known)))

    # Normalize to sum=1
    total = sum(x[1] for x in scored) or 1.0
    probs = []
    for name, raw, overlap, denom in scored:
        probs.append({
            "condition": name,
            "probability": round(raw / total, 4),
            "matched_symptoms": overlap,
            "model_coverage": denom,
        })
    probs.sort(key=lambda x: x["probability"], reverse=True)
    return probs


def _next_question(symptoms_set, top_conditions):
    # Pick a symptom that best disambiguates among top conditions:
    # choose the symptom that appears in some-but-not-all conditions and isn't already present.
    candidates = {}
    top_cfgs = [CONDITIONS[c["condition"]] for c in top_conditions if c["condition"] in CONDITIONS]
    for cfg in top_cfgs:
        for s in cfg["symptoms"]:
            if s in symptoms_set:
                continue
            candidates[s] = candidates.get(s, 0) + 1

    if not candidates:
        # fallback to a generic follow-up from the top condition
        top = top_conditions[0]["condition"] if top_conditions else None
        if top and top in CONDITIONS and CONDITIONS[top].get("followups"):
            return {"type": "yes_no", "question": CONDITIONS[top]["followups"][0]}
        return None

    # choose symptom with frequency closest to half of top_cfgs (max information gain heuristic)
    n = max(1, len(top_cfgs))
    best = sorted(candidates.items(), key=lambda kv: (abs((kv[1] / n) - 0.5), -kv[1]))[0][0]
    return {"type": "yes_no", "question": f"Do you also have {best}?"}


@symptom_bp.route("/check", methods=["POST"])
@token_required
def symptom_check():
    data = request.json or {}
    text = data.get("symptoms_text", "")
    answers = data.get("answers") or {}

    symptoms = _tokenize(text)
    # fold in previous yes/no follow-up answers
    for k, v in answers.items():
        if v is True:
            symptoms.add(str(k).lower())

    red_flag_msgs = []
    for rf, msg in RED_FLAGS:
        if rf in symptoms:
            red_flag_msgs.append(msg)

    probs = _scores_from_symptoms(symptoms)
    top = probs[:3]
    next_q = _next_question(symptoms, top)

    return jsonify({
        "input_symptoms": sorted(list(symptoms))[:50],
        "results": probs[:5],
        "suggested_conditions": [r["condition"] for r in top],
        "next_question": next_q,
        "red_flags": red_flag_msgs,
        "emergency": bool(red_flag_msgs),
        "emergency_message": "Immediate doctor consultation required." if red_flag_msgs else None,
    }), 200

