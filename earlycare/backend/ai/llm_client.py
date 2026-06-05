import os
from typing import Optional

import google.generativeai as genai


def _build_prompt(question: str) -> str:
    """Create a careful system-style prompt for general health questions.

    The model is used only for broad education, not diagnosis. We keep the
    wording conservative and always ask the model to include a clear
    "not a diagnosis" reminder.
    """

    base = (
        "You are a cautious medical information assistant. "
        "Answer the question in simple language, in 4-8 short bullet points. "
        "Focus on general information, lifestyle advice, and warning signs. "
        "Do NOT name specific prescription doses, do NOT tell the user exactly "
        "what medicine to start or stop. Always finish with a reminder that this "
        "is not a diagnosis and they must talk to a doctor for personal advice.\n\n"
        f"Question: {question}\n"
        "Answer:"
    )
    return base


def ask_general_health(question: str) -> Optional[str]:
    """Call Google Gemini for general health questions.

    Expects the environment variable GEMINI_API_KEY to be set with your own
    key. There is typically a free tier, but you must check Google's current
    pricing and limits yourself.

    Returns a plain-text answer or None if the call fails or is not
    configured, so the caller can fall back to local heuristics.
    """

    question = (question or "").strip()
    if not question:
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        model_id = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_id)
        prompt = _build_prompt(question)
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        return text or None
    except Exception:
        # On any error, silently fall back so the caller can use
        # rule-based answers instead of breaking the API.
        return None
