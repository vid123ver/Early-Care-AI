import pdfplumber


# In-memory store for demo (report_id -> raw text context)
REPORT_CONTEXTS = {}


def _summarise_context(context: str, question: str, max_chars: int = 600) -> str:
    """Very simple heuristic to pull a short snippet from the report related to the question."""
    if not context:
        return ""

    ctx = context.replace("\n", " ")
    sentences = [s.strip() for s in ctx.split(".") if s.strip()]
    if not sentences:
        return ctx[:max_chars]

    q_words = [w.lower() for w in question.split() if len(w) > 3]
    scored = []
    for s in sentences:
        score = sum(1 for w in q_words if w in s.lower())
        scored.append((score, s))

    # Prefer sentences with some keyword overlap; fall back to first few.
    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = [s for score, s in scored[:3] if score > 0] or sentences[:3]
    snippet = ". ".join(chosen)
    return snippet[:max_chars]


def process_pdf_and_store(pdf_path, report_id):
    """Extract raw text from a PDF and keep it in memory for chat about that report."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "".join([page.extract_text() or "" for page in pdf.pages])
    text = (text or "").strip()
    REPORT_CONTEXTS[report_id] = text
    # Return a simple size indicator for the frontend
    return len(text.split()) if text else 0


def answer_question(report_id, question):
    """Answer using report text when available, plus topic-based general guidance."""
    question = (question or "").strip()
    q_lower = question.lower()
    context = REPORT_CONTEXTS.get(report_id) if report_id else None
    snippet = _summarise_context(context or "", question)

    parts = []

    # 1) Show any useful lines from the report itself.
    if snippet:
        parts.append("From your report, here are a few related lines:")
        parts.append(snippet)

    # 2) If the user is asking for a general "analysis" of the report,
    #    explain how doctors usually read lab reports and what to look at.
    analyse_intent = any(
        k in q_lower
        for k in [
            "analyse my report",
            "analyze my report",
            "analyse my lab",
            "analyze my lab",
            "lab report",
            "latest report",
            "interpret my report",
            "explain my report",
        ]
    )

    if analyse_intent:
        snippet_lower = (snippet or "").lower()
        topics = []
        if any(k in snippet_lower for k in ["diabet", "glucose", "hba1c", "sugar"]):
            topics.append("blood sugar / diabetes control")
        if any(k in snippet_lower for k in ["cholesterol", "ldl", "hdl", "triglyceride"]):
            topics.append("cholesterol and heart risk")
        if any(k in snippet_lower for k in ["liver", "sgpt", "sgot", "alt", "ast", "bilirubin"]):
            topics.append("liver health")
        if any(k in snippet_lower for k in ["hemoglobin", "haemoglobin", "hb", "anemia", "anaemia"]):
            topics.append("blood count / anemia")

        text = (
            "When a doctor analyses a lab report, they usually check that it is your "
            "report (name, age, date, fasting or non‑fasting), then look at groups of "
            "tests together instead of a single number. Common groups are blood sugar, "
            "cholesterol and heart risk, kidney function, liver function, blood counts, "
            "thyroid, and vitamins."
        )
        parts.append(text)

        if topics:
            parts.append(
                "In your report text I can see terms that usually belong to: "
                + ", ".join(topics)
                + ". Your doctor will pay special attention to these areas."
            )

        parts.append(
            "A practical way to review your report is: (1) mark clearly high or low "
            "values, (2) see whether the same value has changed compared with your old "
            "reports, (3) note any symptoms you are having now, and then (4) take this "
            "summary to your doctor so you can decide together what it means."
        )

    # 3) Simple topic-based education so the reply is not identical every time.
    if any(k in q_lower for k in ["chia seed", "chia seeds", "chia"]):
        parts.append(
            "Chia seeds are rich in fibre, plant protein, and healthy fats (including omega‑3 ALA). "
            "Regular small portions may help bowel movement, support heart health, and keep you full for longer. "
            "They are usually taken soaked in water, milk, or curd so that they swell and are easier to digest. "
            "Very large dry quantities without enough water can cause bloating or discomfort, and people with swallowing problems or on blood‑thinning medicines should check with their doctor first."
        )
    elif any(k in q_lower for k in ["pumpkin seed", "pumpkin seeds"]):
        parts.append(
            "Pumpkin seeds are rich in healthy fats, plant protein, fibre, magnesium, zinc, and antioxidants. "
            "They may support heart health, blood sugar control, and good cholesterol when used as part of an overall balanced diet. "
            "Keep portions moderate (for example, a small handful) and avoid very salty or sugar‑coated versions, especially if you have high blood pressure or diabetes."
        )
    elif any(k in q_lower for k in ["trans fat", "trans-fat", "transfat"]):
        parts.append(
            "Trans fats (often found in repeatedly fried foods, some bakery items, and certain packaged snacks) can raise bad cholesterol (LDL), lower good cholesterol (HDL), and increase heart and blood vessel risk. "
            "Regular high intake of trans fats is linked to heart attacks, stroke, and inflammation. "
            "Most guidelines advise keeping trans fat intake as close to zero as possible by limiting deep-fried fast food and checking labels for 'partially hydrogenated oils'."
        )
    elif any(k in q_lower for k in ["fever", "temperature", "viral"]):
        parts.append(
            "Fever usually means the body is fighting an infection (often viral or bacterial). "
            "Important things are checking how high the temperature is, how long it has lasted, and whether there are red-flag symptoms like trouble breathing, chest pain, confusion, or rash. "
            "Home care often includes rest, plenty of fluids, and medicines like paracetamol for comfort if your doctor says they are safe for you."
        )
    elif any(k in q_lower for k in ["diabet", "sugar", "glucose", "hba1c"]):
        parts.append(
            "Questions about blood sugar and diabetes usually focus on fasting glucose, HbA1c, and symptoms such as thirst, frequent urination, or weight change. "
            "Lifestyle changes (balanced diet, regular activity, weight control, sleep) are the foundation, and medicines are added by a doctor if needed based on your exact numbers and history."
        )
    elif any(k in q_lower for k in ["cholesterol", "ldl", "hdl", "triglyceride"]):
        parts.append(
            "For cholesterol, doctors look at total cholesterol, LDL, HDL, and triglycerides together with your heart risk factors (age, blood pressure, diabetes, smoking, family history). "
            "Heart-healthy diet, regular exercise, and weight control are key; tablets like statins are decided by your doctor using your full risk profile."
        )
    elif any(k in q_lower for k in ["liver", "sgpt", "sgot", "alt", "ast", "bilirubin"]):
        parts.append(
            "Liver reports (ALT/AST, bilirubin, ultrasound findings) need to be read together with history of alcohol use, medicines, infections (like hepatitis), and metabolic problems. "
            "Avoiding alcohol, unnecessary medicines, and very oily food is usually advised while your doctor looks for the exact cause."
        )
    elif any(k in q_lower for k in ["anemia", "hemoglobin", "hb", "tired", "fatigue"]):
        parts.append(
            "Low hemoglobin (anemia) can cause tiredness, breathlessness, or palpitations and may come from iron lack, vitamin problems, blood loss, or other illnesses. "
            "Your doctor usually combines hemoglobin, red cell indices, iron studies, and your history to decide on tests and treatment such as iron or other supplements."
        )
    else:
        # General catch‑all educational text.
        parts.append(
            "Most lab values are interpreted as a pattern rather than one number alone. "
            "Trends over time and your symptoms are often more important than a single slightly high or low reading."
        )

    # 4) Shared safety disclaimer (kept at the end).
    parts.append(
        "In general, lab reports and symptoms must be interpreted in the full "
        "context of your health history, medicines, and examination. An online "
        "assistant can explain terms and give general education, but it cannot "
        "confirm a diagnosis or choose treatments for you."
    )
    parts.append(
        "Please discuss this question and your report directly with your doctor "
        "for personal medical advice and decisions."
    )

    return "\n\n".join(parts).strip()
