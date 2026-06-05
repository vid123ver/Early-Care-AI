import os
from flask import Blueprint, request, jsonify, g

from routes.auth_routes import token_required
from database.mongo import (
    fetch_latest_report_by_user,
    count_reports_by_user,
)
from routes.dashboard_routes import (
    _score_and_concerns,
    _abnormal_markers,
    _marker_history_summary,
)
from ai.llm_client import ask_general_health

UPLOAD_FOLDER = "uploads"
chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def _get_chat_impl():
    """Import lightweight chat helpers. Kept in a helper so import errors are caught nicely."""
    try:
        from ai.report_chat import process_pdf_and_store, answer_question

        return process_pdf_and_store, answer_question, None
    except Exception as e:  # pragma: no cover - defensive
        return None, None, e


@chat_bp.route("/upload_report", methods=["POST"])
@token_required
def upload_report():
    """Upload a PDF and extract text for later chat about that specific file.

    This is optional now that we also use dashboard metrics, but kept for
    scenarios where the user wants Q&A about a standalone PDF.
    """
    process_pdf_and_store, _, err = _get_chat_impl()
    if err or not process_pdf_and_store:
        return (
            jsonify(
                {
                    "error": "Chat dependencies are not installed/configured on the backend",
                    "details": str(err),
                }
            ),
            500,
        )

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    report_id = file.filename  # For demo, use filename as report_id
    num_tokens = process_pdf_and_store(filepath, report_id)
    return jsonify({"report_id": report_id, "size": num_tokens}), 200


@chat_bp.route("/ask", methods=["POST"])
@token_required
def ask():
    """Unified chat endpoint.

    - For general health questions (no clear "report" intent), use
      ai.report_chat.answer_question with optional uploaded-report context.
    - For questions that mention a lab report / test results, summarise the
      latest stored report using the same metrics as the dashboard.
    """
    data = request.json or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    user_id = str(g.current_user["_id"])
    q_lower = question.lower()

    # If the question clearly mentions a report or lab results, return
    # the structured dashboard-style summary for the latest report.
    report_intent = any(
        k in q_lower
        for k in [
            "report",
            "lab",
            "blood test",
            "test result",
            "test results",
        ]
    )

    if not report_intent:
        # General health / symptom / lifestyle questions:
        # 1) Try external LLM if configured (HF_API_KEY set).
        # 2) Fall back to lightweight topic-based implementation.

        llm_answer = ask_general_health(question)
        if llm_answer:
            return jsonify({"answer": llm_answer}), 200

        _, answer_question, err = _get_chat_impl()
        if err or not answer_question:
            return jsonify(
                {
                    "answer": (
                        "I can give general health education, but the detailed chat "
                        "module is not available right now. Please ask your doctor "
                        "for personalised medical advice."
                    )
                }
            ), 200

        report_id = data.get("report_id")  # may be None
        answer = answer_question(report_id, question)
        return jsonify({"answer": answer}), 200

    # ---- Report-focused answer using dashboard data ----
    latest = fetch_latest_report_by_user(user_id)
    total_reports = count_reports_by_user(user_id)

    if not latest:
        answer_lines = [
            "## Summary",
            "",
            f"You asked: '{question}'.",
            "",
            "- I cannot find any saved lab report for your account yet.",
            "- Once a report is uploaded and visible on your dashboard, I can show a structured summary here (key values, trends, and points to discuss with your doctor).",
            "",
            "---",
            "",
            "### Important Disclaimer",
            "This assistant cannot see or interpret images or PDFs that are not stored in the app's dashboard. It provides general education only and is **not** a medical diagnosis. Always discuss your situation and any test results directly with your doctor.",
        ]
        return jsonify({"answer": "\n".join(answer_lines)}), 200

    metrics = latest.get("metrics") or {}
    health_score, risk_level, concerns = _score_and_concerns(metrics)
    abnormal = _abnormal_markers(metrics)

    created_at = latest.get("created_at")
    created_str = str(created_at) if created_at else "(date not recorded)"

    answer_lines: list[str] = []
    answer_lines.append("## Summary")
    answer_lines.append("")
    answer_lines.append(f"You asked: '{question}'.")
    answer_lines.append("")

    summary_bullets: list[str] = []
    summary_bullets.append(
        f"- Overall risk level: **{risk_level}** (health score {health_score}/100)."
    )
    summary_bullets.append(
        f"- Latest report date: **{created_str}** (reports on file: {total_reports})."
    )

    # Simple emergency-style check, mirroring dashboard alerts.
    critical: list[str] = []
    glucose = metrics.get("glucose")
    if isinstance(glucose, (int, float)) and (glucose >= 300 or glucose <= 50):
        critical.append("Dangerous glucose level (very high or very low) detected.")

    cholesterol = metrics.get("cholesterol")
    if isinstance(cholesterol, (int, float)) and cholesterol >= 300:
        critical.append("Very high cholesterol level detected; high cardiovascular risk.")

    hemoglobin = metrics.get("hemoglobin")
    if isinstance(hemoglobin, (int, float)) and hemoglobin < 8:
        critical.append("Severely low hemoglobin detected; possible significant anemia.")

    if abnormal:
        summary_bullets.append(
            "- Some values are outside the normal range and should be discussed with your doctor."
        )
    elif concerns:
        summary_bullets.append(
            "- There are a few minor concerns; lifestyle changes and follow-up are usually advised."
        )
    else:
        summary_bullets.append(
            "- No major issues detected in the main tracked markers (glucose, cholesterol, hemoglobin)."
        )

    if critical:
        summary_bullets.append(
            "- **Possible emergency findings are present – see details below and contact a doctor urgently.**"
        )

    answer_lines.extend(summary_bullets)

    # --- Key metrics table ---
    answer_lines.append("")
    answer_lines.append("---")
    answer_lines.append("")
    answer_lines.append("## Key Lab Metrics")
    answer_lines.append("")
    answer_lines.append("| Test Name | Result | Status | Reference Range |")
    answer_lines.append("|----------|--------|--------|-----------------|")

    # Helper to find status from abnormal markers list.
    def _marker_status(name: str) -> str:
        for a in abnormal:
            if a.get("marker") == name:
                s = a.get("status") or ""
                return str(s).capitalize()
        return "Normal"

    # Glucose row
    if isinstance(metrics.get("glucose"), (int, float)):
        answer_lines.append(
            f"| Glucose | {metrics['glucose']} | {_marker_status('glucose')} | See lab's reference range |"
        )

    # Cholesterol row
    if isinstance(metrics.get("cholesterol"), (int, float)):
        answer_lines.append(
            f"| Cholesterol | {metrics['cholesterol']} | {_marker_status('cholesterol')} | See lab's reference range |"
        )

    # Hemoglobin row
    if isinstance(metrics.get("hemoglobin"), (int, float)):
        answer_lines.append(
            f"| Hemoglobin | {metrics['hemoglobin']} | {_marker_status('hemoglobin')} | See lab's reference range |"
        )

    if critical:
        answer_lines.append("")
        answer_lines.append("## Critical Warnings")
        answer_lines.append("")
        for c in critical:
            answer_lines.append(f"- **{c}**")
        answer_lines.append("- **Immediate doctor consultation is strongly recommended.**")

    # High-level trend view using the same history summaries as /dashboard/lifestyle.
    glucose_summary = _marker_history_summary(
        user_id, "glucose", high_threshold=126, borderline_threshold=100
    )
    cholesterol_summary = _marker_history_summary(
        user_id, "cholesterol", high_threshold=240, borderline_threshold=200
    )
    hemoglobin_summary = _marker_history_summary(user_id, "hemoglobin")

    def _trend_sentence(summary, label: str) -> str | None:
        if not summary:
            return None
        status = summary.get("trend_status")
        last = summary.get("last")
        risk = summary.get("risk_flag")
        base = f"For {label}, the latest value is {last}. It has been {status} over your reports."
        if risk == "high":
            base += (
                " It is currently in a high range; this usually needs active management with your doctor."
            )
        elif risk == "borderline":
            base += (
                " It is in a borderline range; this is a good time to focus on lifestyle and close follow-up."
            )
        return base

    trend_sentences: list[str] = []
    s = _trend_sentence(glucose_summary, "blood sugar (glucose)")
    if s:
        trend_sentences.append(s)
    s = _trend_sentence(cholesterol_summary, "cholesterol")
    if s:
        trend_sentences.append(s)
    s = _trend_sentence(hemoglobin_summary, "hemoglobin (blood count)")
    if s:
        trend_sentences.append(s)

    if trend_sentences:
        answer_lines.append("")
        answer_lines.append("## Trend Overview")
        answer_lines.append("")
        for t in trend_sentences:
            answer_lines.append(f"- {t}")

    # --- Next steps ---
    answer_lines.append("")
    answer_lines.append("## Next Steps / Doctor Discussion Points")
    answer_lines.append("")

    if abnormal or critical:
        answer_lines.append(
            "- Show this summary and your full report to your doctor and ask what these results mean for you personally."
        )
        answer_lines.append(
            "- Ask whether any further tests, lifestyle changes, or medicine adjustments are needed based on these values and trends."
        )
    else:
        answer_lines.append(
            "- Continue your current healthy habits and regular follow-up as advised by your clinician."
        )
        answer_lines.append(
            "- Ask your doctor how often you should repeat these tests to keep track of your health."
        )

    answer_lines.append(
        "- If you develop new or worrying symptoms (for example, chest pain, severe breathlessness, fainting, or heavy bleeding), seek urgent medical care even if the report looks okay."
    )

    # --- Shared safety disclaimer ---
    answer_lines.append("")
    answer_lines.append("---")
    answer_lines.append("")
    answer_lines.append("### Important Disclaimer")
    answer_lines.append(
        "This structured summary is generated automatically from the data in your dashboard and is **not** a medical diagnosis or treatment plan. "
        "Only a qualified clinician who knows your full history, examines you, and reviews the complete report can make medical decisions for you."
    )

    return jsonify({"answer": "\n".join(answer_lines)}), 200
