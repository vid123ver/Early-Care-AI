from flask import Blueprint, jsonify, request, g

from database.mongo import fetch_reports_by_user
from routes.auth_routes import token_required


diet_bp = Blueprint("diet", __name__, url_prefix="/diet")


# Simple rule-based dietary guidance per condition.
# This is conservative lifestyle education, not a prescription.
DIET_LIBRARY = {
    "Diabetes": {
        "profile": "Low-sugar, high-fiber, balanced plate",
        "eat_more": [
            "Non-starchy vegetables (spinach, broccoli, cucumber, bhindi, lauki)",
            "Whole grains in controlled portions (brown rice, oats, dalia, millets)",
            "Lean proteins (dal, chana, rajma, egg whites, grilled chicken/fish)",
            "Healthy fats in small amounts (nuts, seeds, olive/mustard oil)",
        ],
        "eat_less_or_avoid": [
            "Sugary drinks (regular soda, packaged juices, sweetened tea/coffee)",
            "White rice, maida products (white bread, biscuits, pastries)",
            "Deep-fried snacks and sweets (samosa, kachori, jalebi, gulab jamun)",
            "Large portions of fruits high in sugar (mango, grapes) – keep portions small",
        ],
        "sample_chart": {
            "breakfast": [
                "Oats or dalia with skim milk + 1 small fruit (apple/guava)",
                "2 egg whites + 1 small multigrain roti + salad",
            ],
            "lunch": [
                "1–2 phulka (without ghee) + dal + bowl of sabzi + salad",
                "Small portion brown rice + rajma/chana + salad",
            ],
            "snacks": [
                "Handful of roasted chana / nuts",
                "Buttermilk (unsweetened) or lemon water without sugar",
            ],
            "dinner": [
                "Bowl of vegetable soup + 1–2 phulka + grilled paneer/tofu",
                "Light khichdi (dal + rice) with lots of vegetables",
            ],
        },
        "notes": [
            "Spread carbohydrates across the day instead of 1–2 heavy meals.",
            "Avoid skipping meals to prevent sugar spikes and overeating later.",
            "Combine carbs with protein/fiber (e.g., dal + roti + salad).",
        ],
    },
    "High Cholesterol": {
        "profile": "Low-saturated-fat, heart-friendly diet",
        "eat_more": [
            "Plenty of vegetables and fruits (aim for 4–5 servings/day)",
            "Whole grains (oats, dalia, brown rice, multigrain roti)",
            "Lean protein (fish, skinless chicken, dals, beans)",
            "Healthy fats in moderation (nuts, seeds, olive oil, mustard oil)",
        ],
        "eat_less_or_avoid": [
            "Fried foods and fast food (pakora, fries, burgers)",
            "Red meat and processed meat (sausages, salami)",
            "Full-fat dairy (malai, cream, cheese in excess)",
            "Bakery products rich in trans fat (puff, packaged cookies)",
        ],
        "sample_chart": {
            "breakfast": [
                "Oats with skim milk + nuts + fruit slice",
                "Vegetable upma/poha cooked with minimal oil",
            ],
            "lunch": [
                "2 phulka + dal + 2 vegetable dishes + salad",
                "Brown rice + sambar/rasam + vegetables",
            ],
            "snacks": [
                "Fruit + handful of nuts",
                "Sprout salad with onion, tomato, lemon",
            ],
            "dinner": [
                "Grilled fish/chicken + veggies + small portion of rice/roti",
                "Veg soup + stir-fried vegetables + small roti",
            ],
        },
        "notes": [
            "Limit visible oil to ~3–4 tsp/day (for entire day cooking).",
            "Avoid repeated frying in same oil.",
            "Combine diet changes with regular walking and weight control.",
        ],
    },
    "Liver Disease / Fatty Liver": {
        "profile": "Liver-friendly, moderate-protein, low-alcohol",
        "eat_more": [
            "Fresh fruits and vegetables",
            "Complex carbs (brown rice, millets, dalia) in moderate portions",
            "Lean protein (dal, beans, egg whites, fish)",
        ],
        "eat_less_or_avoid": [
            "Alcohol (best to avoid completely)",
            "Very oily, spicy, deep-fried foods",
            "Sugary desserts and drinks",
        ],
        "sample_chart": {
            "breakfast": [
                "Idli with sambar + fruit",
                "Dalia with vegetables + curd (low-fat)",
            ],
            "lunch": [
                "2 phulka + dal + sabzi + salad",
                "Rice + vegetable curry + curd (low-fat)",
            ],
            "snacks": [
                "Fruit bowl",
                "Roasted chana/nuts (small handful)",
            ],
            "dinner": [
                "Light khichdi with vegetables",
                "Vegetable soup + 1–2 phulka",
            ],
        },
        "notes": [
            "Maintain healthy weight; gradual weight loss helps fatty liver.",
            "Hydrate well; avoid unnecessary supplements/herbal products without doctor advice.",
        ],
    },
}


@diet_bp.route("/recommend", methods=["POST"])
@token_required
def recommend_diet():
    data = request.json or {}
    raw_condition = (data.get("condition") or "").strip()
    # Treat notes / symptoms_text as the user's symptom description.
    symptoms_text = (data.get("symptoms_text") or data.get("notes") or "").strip()

    # Pull all past reports for this user so diet can use real history.
    user = getattr(g, "current_user", None)
    user_id = str(user.get("_id")) if user else None
    reports = fetch_reports_by_user(user_id, limit=50) if user_id else []

    # Derive simple flags from metrics across all reports.
    def _metric_flags(all_reports):
        diabetes_flag = False
        chol_flag = False
        liver_flag = False
        latest_metrics = {}

        for idx, r in enumerate(all_reports):
            metrics = r.get("metrics", {}) or {}
            if idx == 0:
                latest_metrics = metrics
            m_lower = {str(k).lower(): v for k, v in metrics.items()}

            # Very simple heuristics; thresholds are conservative and educational.
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

    diabetes_flag, chol_flag, liver_flag, latest_metrics = _metric_flags(reports)

    # Use both reports and symptoms text to choose best diet focus when user selects Auto.
    normalized = raw_condition.lower()
    auto_requested = not normalized or normalized.startswith("auto")

    # Symptom/notes keyword hints.
    symp = symptoms_text.lower()
    diab_score = 0
    chol_score = 0
    liver_score = 0

    if diabetes_flag:
        diab_score += 2
    if chol_flag:
        chol_score += 2
    if liver_flag:
        liver_score += 2

    if any(w in symp for w in ["diab", "sugar", "high sugar", "hbA1c".lower()]):
        diab_score += 1
    if any(w in symp for w in ["chol", "lipid", "triglyceride", "heart attack", "blockage"]):
        chol_score += 1
    if any(w in symp for w in ["liver", "fatty", "jaundice", "hepatitis"]):
        liver_score += 1

    auto_choice = None
    if auto_requested:
        scores = [("Diabetes", diab_score), ("High Cholesterol", chol_score), ("Liver Disease / Fatty Liver", liver_score)]
        scores.sort(key=lambda x: x[1], reverse=True)
        auto_choice = scores[0][0] if scores and scores[0][1] > 0 else None

    # If user explicitly picked a focus, respect it but still normalize.
    if not auto_requested and normalized:
        if "diab" in normalized:
            chosen_key = "Diabetes"
        elif "chol" in normalized or "lipid" in normalized:
            chosen_key = "High Cholesterol"
        elif "liver" in normalized or "fatty" in normalized:
            chosen_key = "Liver Disease / Fatty Liver"
        else:
            chosen_key = raw_condition
    else:
        chosen_key = auto_choice or "Diabetes"  # sensible default

    payload = DIET_LIBRARY.get(chosen_key)
    if not payload:
        return jsonify({
            "condition_input": raw_condition,
            "condition_resolved": chosen_key,
            "profile": "General heart-healthy, balanced diet",
            "eat_more": [
                "Plenty of vegetables and fruits",
                "Whole grains instead of refined grains",
                "Adequate water intake",
            ],
            "eat_less_or_avoid": [
                "Sugary drinks and desserts",
                "Deep-fried and highly processed foods",
                "Excess alcohol",
            ],
            "sample_chart": {},
            "notes": [
                "Use this only as general education; individual needs vary.",
                "Discuss specific diet changes with your clinician, especially if you have chronic illness.",
            ],
            "labs_used": latest_metrics,
            "history_used": {
                "total_reports": len(reports),
                "flags": {
                    "diabetes_profile": diabetes_flag,
                    "high_cholesterol_profile": chol_flag,
                    "liver_profile": liver_flag,
                },
            },
            "symptoms_used": symptoms_text,
            "disclaimer": "Educational diet guidance only – not a prescription.",
        }), 200

    return jsonify({
        "condition_input": raw_condition,
        "condition_resolved": chosen_key,
        "profile": payload["profile"],
        "eat_more": payload["eat_more"],
        "eat_less_or_avoid": payload["eat_less_or_avoid"],
        "sample_chart": payload["sample_chart"],
        "notes": payload["notes"],
        "labs_used": latest_metrics,
        "history_used": {
            "total_reports": len(reports),
            "flags": {
                "diabetes_profile": diabetes_flag,
                "high_cholesterol_profile": chol_flag,
                "liver_profile": liver_flag,
            },
        },
        "symptoms_used": symptoms_text,
        "disclaimer": "Educational diet guidance only – not a prescription.",
    }), 200
