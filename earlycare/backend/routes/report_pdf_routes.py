from bson.objectid import ObjectId
from flask import Blueprint, jsonify, g, send_file, request
from io import BytesIO

from routes.auth_routes import token_required
from database.mongo import fetch_report
from ai.report_pdf import build_health_report_pdf

report_pdf_bp = Blueprint("report_pdf", __name__, url_prefix="/report_pdf")


@report_pdf_bp.route("/<report_id>/download", methods=["GET"])
@token_required
def download_report_pdf(report_id):
  """Generate a structured, colorful PDF report for a given lab report.

  Optional query params:
  - include_diet=true/false (frontend may already have a diet plan)
  - include_treatment=true/false

  Optional JSON body (for future extension, e.g. POST): diet, treatment.
  """
  user_id = str(g.current_user["_id"])
  try:
    oid = ObjectId(report_id)
  except Exception:
    return jsonify({"error": "Invalid report id"}), 400

  report = fetch_report({"_id": oid, "user_id": user_id})
  if not report:
    return jsonify({"error": "Report not found"}), 404

  # Fetch dashboard overview and trends by calling internal helpers via HTTP would be heavy.
  # Instead, we reconstruct minimal pieces here by reusing the same collection helpers.
  from database.mongo import fetch_user_reports_metrics

  metrics = report.get("metrics") or {}
  # Lightweight scoring, same logic as dashboard_routes._score_and_concerns
  score = 100
  concerns = []

  glucose = metrics.get("glucose")
  if isinstance(glucose, (int, float)):
    if glucose >= 126:
      concerns.append("High glucose")
      score -= 20
    elif glucose >= 100:
      concerns.append("Borderline glucose")
      score -= 10

  cholesterol = metrics.get("cholesterol")
  if isinstance(cholesterol, (int, float)):
    if cholesterol >= 240:
      concerns.append("High cholesterol")
      score -= 20
    elif cholesterol >= 200:
      concerns.append("Borderline cholesterol")
      score -= 10

  hemoglobin = metrics.get("hemoglobin")
  if isinstance(hemoglobin, (int, float)):
    if hemoglobin < 11:
      concerns.append("Low hemoglobin")
      score -= 15
    elif hemoglobin > 18:
      concerns.append("High hemoglobin")
      score -= 10

  score = max(0, min(100, score))
  risk_level = "Low" if score >= 75 else ("Medium" if score >= 50 else "High")

  # Simple comparison vs previous value to say if markers are increasing/decreasing
  # (only used for language like "it is increasing").
  from database.mongo import reports_collection

  created_at = report.get("created_at")
  prev = None
  if created_at:
    prev = reports_collection.find_one(
      {"user_id": user_id, "created_at": {"$lt": created_at}},
      sort=[("created_at", -1)],
    )
  deltas = {}
  if prev:
    prev_metrics = prev.get("metrics") or {}
    for key in ("glucose", "cholesterol", "hemoglobin"):
      a = metrics.get(key)
      b = prev_metrics.get(key)
      if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        deltas[key] = a - b

  overview = {
    "risk_level": risk_level,
    "health_score": score,
    "comparison": {"deltas": deltas} if deltas else None,
  }

  # Build minimal trends (date/value) for potential chart-aware language.
  def _series(marker):
    pairs = fetch_user_reports_metrics(user_id, marker)
    return [
      {"x": str(created), "y": value}
      for created, value in pairs
    ]

  trends = {
    "glucose": _series("glucose"),
    "cholesterol": _series("cholesterol"),
    "hemoglobin": _series("hemoglobin"),
  }

  # For now we don&apos;t recompute diet/treatment; the report focuses on lab + generic guidance.
  diet = None
  treatment = None

  pdf_bytes = build_health_report_pdf(
    user=g.current_user,
    report=report,
    overview=overview,
    trends=trends,
    diet=diet,
    treatment=treatment,
  )

  return send_file(
    BytesIO(pdf_bytes),
    mimetype="application/pdf",
    as_attachment=True,
    download_name=f"earlycare_report_{report_id}.pdf",
  )
