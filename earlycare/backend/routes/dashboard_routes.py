from bson.objectid import ObjectId
from flask import Blueprint, jsonify, g, request
from routes.auth_routes import token_required
from database.mongo import (
    count_reports_by_user,
    fetch_latest_report_by_user,
    fetch_report,
    fetch_user_reports_metrics,
)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def _score_and_concerns(metrics):
    """
    Lightweight heuristic scoring from parsed metrics.
    Keeps things explainable and avoids storing PDFs.
    """
    metrics = metrics or {}
    concerns = []
    score = 100

    glucose = metrics.get('glucose')
    if isinstance(glucose, (int, float)):
        if glucose >= 126:
            concerns.append("High glucose")
            score -= 20
        elif glucose >= 100:
            concerns.append("Borderline glucose")
            score -= 10

    cholesterol = metrics.get('cholesterol')
    if isinstance(cholesterol, (int, float)):
        if cholesterol >= 240:
            concerns.append("High cholesterol")
            score -= 20
        elif cholesterol >= 200:
            concerns.append("Borderline cholesterol")
            score -= 10

    hemoglobin = metrics.get('hemoglobin')
    if isinstance(hemoglobin, (int, float)):
        if hemoglobin < 11:
            concerns.append("Low hemoglobin")
            score -= 15
        elif hemoglobin > 18:
            concerns.append("High hemoglobin")
            score -= 10

    score = max(0, min(100, score))
    risk_level = "Low" if score >= 75 else ("Medium" if score >= 50 else "High")
    return score, risk_level, concerns[:5]


def _abnormal_markers(metrics):
    """Return a simple list of abnormal or borderline markers for quick display."""
    metrics = metrics or {}
    out = []

    glucose = metrics.get('glucose')
    if isinstance(glucose, (int, float)):
        if glucose >= 126:
            out.append({
                'marker': 'glucose',
                'value': glucose,
                'status': 'high',
                'message': 'Glucose is in diabetic range; discuss sugar control with your doctor.',
            })
        elif glucose >= 100:
            out.append({
                'marker': 'glucose',
                'value': glucose,
                'status': 'borderline',
                'message': 'Glucose is borderline; focus on diet, exercise, and repeat testing.',
            })

    cholesterol = metrics.get('cholesterol')
    if isinstance(cholesterol, (int, float)):
        if cholesterol >= 240:
            out.append({
                'marker': 'cholesterol',
                'value': cholesterol,
                'status': 'high',
                'message': 'Cholesterol is high; long-term heart protection plan is needed.',
            })
        elif cholesterol >= 200:
            out.append({
                'marker': 'cholesterol',
                'value': cholesterol,
                'status': 'borderline',
                'message': 'Cholesterol is borderline; start heart-healthy lifestyle changes.',
            })

    hemoglobin = metrics.get('hemoglobin')
    if isinstance(hemoglobin, (int, float)):
        if hemoglobin < 11:
            out.append({
                'marker': 'hemoglobin',
                'value': hemoglobin,
                'status': 'low',
                'message': 'Hemoglobin is low; ask your doctor about anemia and iron.',
            })
        elif hemoglobin > 18:
            out.append({
                'marker': 'hemoglobin',
                'value': hemoglobin,
                'status': 'high',
                'message': 'Hemoglobin is higher than usual; discuss this pattern with your clinician.',
            })

    return out


def _marker_history_summary(user_id, marker, high_threshold=None, borderline_threshold=None):
    """Summarize long-term pattern for a single lab marker."""
    pairs = fetch_user_reports_metrics(user_id, marker)
    if not pairs:
        return None

    values = [v for _, v in pairs if isinstance(v, (int, float))]
    if not values:
        return None

    first = values[0]
    last = values[-1]
    avg = sum(values) / len(values)
    trend_delta = last - first

    status = "stable"
    if abs(trend_delta) >= 5:
        status = "increasing" if trend_delta > 0 else "decreasing"

    risk_flag = None
    if isinstance(high_threshold, (int, float)) and last >= high_threshold:
        risk_flag = "high"
    elif isinstance(borderline_threshold, (int, float)) and last >= borderline_threshold:
        risk_flag = "borderline"

    return {
        "marker": marker,
        "first": first,
        "last": last,
        "average": avg,
        "trend_delta": trend_delta,
        "trend_status": status,
        "risk_flag": risk_flag,
        "count": len(values),
    }


@dashboard_bp.route('/overview', methods=['GET'])
@token_required
def dashboard_overview():
    """
    Query params:
    - report_id: optional (defaults to latest report)
    - compare: "true" | "false" (if true, includes simple deltas vs previous report)
    """
    user_id = str(g.current_user['_id'])
    report_id = request.args.get('report_id')
    compare = (request.args.get('compare') or '').lower() in ('1', 'true', 'yes')

    if report_id:
        try:
            oid = ObjectId(report_id)
        except Exception:
            return jsonify({'error': 'Invalid report id'}), 400
        report = fetch_report({'_id': oid, 'user_id': user_id})
        if not report:
            return jsonify({'error': 'Report not found'}), 404
    else:
        report = fetch_latest_report_by_user(user_id)

    total = count_reports_by_user(user_id)

    if not report:
        return jsonify({
            'total_reports': total,
            'latest_prediction': None,
            'risk_level': None,
            'top_health_concerns': [],
            'health_score': 100,
            'current_report': None,
            'comparison': None,
        }), 200

    metrics = report.get('metrics') or {}
    health_score, risk_level, concerns = _score_and_concerns(metrics)
    abnormal = _abnormal_markers(metrics)

    comparison = None
    if compare:
        # Previous report: newest report older than current report's created_at.
        created_at = report.get('created_at')
        prev = None
        if created_at:
            from database.mongo import reports_collection  # local import to avoid expanding public API
            prev = reports_collection.find_one(
                {'user_id': user_id, 'created_at': {'$lt': created_at}},
                sort=[('created_at', -1)]
            )
        if prev:
            prev_metrics = prev.get('metrics') or {}
            deltas = {}
            for key in ('glucose', 'cholesterol', 'hemoglobin'):
                a = metrics.get(key)
                b = prev_metrics.get(key)
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    deltas[key] = a - b
            comparison = {
                'previous_report_id': str(prev.get('_id')),
                'deltas': deltas,
            }

    # Simple one-line summary for the UI health summary card.
    summary_bits = []
    summary_bits.append(f"Risk: {risk_level} (score {health_score}/100)")
    if abnormal:
        names = ", ".join({a['marker'] for a in abnormal})
        summary_bits.append(f"Abnormal values in: {names}.")
    elif concerns:
        summary_bits.append("Minor concerns detected; follow lifestyle advice and track reports.")
    else:
        summary_bits.append("No major issues in the latest report.")

    return jsonify({
        'total_reports': total,
        'latest_prediction': None,
        'risk_level': risk_level,
        'top_health_concerns': concerns,
        'health_score': health_score,
        'abnormal_markers': abnormal,
        'health_summary_text': " ".join(summary_bits),
        'current_report': {
            'id': str(report.get('_id')),
            'created_at': str(report.get('created_at', '')),
            'filename': report.get('filename'),
            'metrics': metrics,
        },
        'comparison': comparison,
    }), 200

@dashboard_bp.route('/health_trends', methods=['GET'])
@token_required
def dashboard_health_trends():
    user_id = str(g.current_user['_id'])

    def _series(marker):
        pairs = fetch_user_reports_metrics(user_id, marker)
        out = []
        for created_at, value in pairs:
            out.append({'x': str(created_at), 'y': value})
        return out

    glucose = _series('glucose')
    cholesterol = _series('cholesterol')
    hemoglobin = _series('hemoglobin')

    # Score series computed from stored metrics on each report
    from database.mongo import reports_collection
    score = []
    for r in reports_collection.find({'user_id': user_id}).sort('created_at', 1):
        s, _, _ = _score_and_concerns(r.get('metrics') or {})
        score.append({'x': str(r.get('created_at')), 'y': s})

    return jsonify({
        'glucose': glucose,
        'cholesterol': cholesterol,
        'hemoglobin': hemoglobin,
        'health_score': score,
    }), 200

@dashboard_bp.route('/alerts', methods=['GET'])
@token_required
def dashboard_alerts():
    user_id = str(g.current_user['_id'])
    latest = fetch_latest_report_by_user(user_id)
    if not latest:
        return jsonify({
            'alerts': [],
            'critical_alerts': [],
            'emergency': False,
            'emergency_message': None,
        }), 200

    metrics = latest.get('metrics') or {}
    _, _, concerns = _score_and_concerns(metrics)

    # Detect clearly critical lab patterns for emergency attention.
    critical = []
    glucose = metrics.get('glucose')
    if isinstance(glucose, (int, float)) and (glucose >= 300 or glucose <= 50):
        critical.append("Dangerous glucose level (very high or very low) detected.")

    cholesterol = metrics.get('cholesterol')
    if isinstance(cholesterol, (int, float)) and cholesterol >= 300:
        critical.append("Very high cholesterol level detected; high cardiovascular risk.")

    hemoglobin = metrics.get('hemoglobin')
    if isinstance(hemoglobin, (int, float)) and hemoglobin < 8:
        critical.append("Severely low hemoglobin detected; possible significant anemia.")

    emergency = bool(critical)
    alerts = (critical + concerns) if critical else concerns

    return jsonify({
        'alerts': alerts,
        'critical_alerts': critical,
        'emergency': emergency,
        'emergency_message': "Immediate doctor consultation required." if emergency else None,
    }), 200


@dashboard_bp.route('/lifestyle', methods=['GET'])
@token_required
def dashboard_lifestyle():
    """Lifestyle & preventive recommendations based on all past and current reports."""
    user_id = str(g.current_user['_id'])

    glucose_summary = _marker_history_summary(user_id, 'glucose', high_threshold=126, borderline_threshold=100)
    cholesterol_summary = _marker_history_summary(user_id, 'cholesterol', high_threshold=240, borderline_threshold=200)
    hemoglobin_summary = _marker_history_summary(user_id, 'hemoglobin')

    sections = []

    # Blood sugar / diabetes prevention
    if glucose_summary:
        recs = [
            "Aim for at least 30–45 minutes of brisk walking or similar activity on most days of the week.",
            "Spread carbohydrates across the day instead of taking 1–2 very heavy meals.",
            "Prefer whole grains (millets, brown rice, multigrain roti) and vegetables over sweets, refined flour, and sugary drinks.",
        ]
        if glucose_summary.get('risk_flag') == 'high':
            recs.append("Your blood sugar has been in a high range in multiple reports – talk to your doctor about diabetes evaluation and long-term sugar control.")
        elif glucose_summary.get('risk_flag') == 'borderline':
            recs.append("Your blood sugar is in a borderline range – focus on weight control, regular exercise, and early lifestyle changes to prevent diabetes.")
        if glucose_summary.get('trend_status') == 'increasing':
            recs.append("Glucose values are trending up over time – try to cut back on added sugar and high-carb snacks, and repeat labs as advised by your clinician.")

        sections.append({
            'title': 'Blood sugar & diabetes prevention',
            'applies': True,
            'recommendations': recs,
            'marker_summary': glucose_summary,
        })

    # Cholesterol / heart prevention
    if cholesterol_summary:
        recs = [
            "Use a heart-friendly diet: more vegetables, fruits, whole grains, and healthy fats (nuts, seeds, mustard/olive oil in small amounts).",
            "Limit deep-fried snacks, fast food, and high-fat meats; avoid repeated frying of oil.",
            "Aim for at least 150 minutes/week of moderate exercise (walking, cycling, etc.) if your doctor says it is safe.",
        ]
        if cholesterol_summary.get('risk_flag') == 'high':
            recs.append("Your cholesterol has been in a high range in multiple reports – discuss long-term heart and cholesterol management with your doctor (including medicines if needed).")
        elif cholesterol_summary.get('risk_flag') == 'borderline':
            recs.append("Cholesterol is borderline – start lifestyle measures now (diet, exercise, weight control) to prevent future heart risk.")
        if cholesterol_summary.get('trend_status') == 'increasing':
            recs.append("Cholesterol values are trending up – review your diet (oil, fried food, high-fat dairy) and repeat labs as advised.")

        sections.append({
            'title': 'Cholesterol & heart protection',
            'applies': True,
            'recommendations': recs,
            'marker_summary': cholesterol_summary,
        })

    # Hemoglobin / anemia
    if hemoglobin_summary:
        recs = [
            "Include iron-rich foods such as green leafy vegetables, dals/beans, and, if non-vegetarian, eggs/lean meat (if culturally acceptable).",
            "Take vitamin C–rich foods (lemon, amla, orange) with iron-rich meals to improve absorption.",
        ]
        # Treat a very low last value as possible anemia.
        last_hb = hemoglobin_summary.get('last')
        if isinstance(last_hb, (int, float)) and last_hb < 11:
            recs.append("Hemoglobin has been low in reports – ask your doctor about anemia workup and whether you need iron or other supplements.")
        if hemoglobin_summary.get('trend_status') == 'decreasing':
            recs.append("Hemoglobin appears to be trending down – repeat labs and discuss with a clinician, especially if you have tiredness, breathlessness, or heavy periods.")

        sections.append({
            'title': 'Hemoglobin & anemia prevention',
            'applies': True,
            'recommendations': recs,
            'marker_summary': hemoglobin_summary,
        })

    # General lifestyle block (always shown)
    general_recs = [
        "Avoid smoking and limit alcohol; both can worsen heart, liver, and overall health.",
        "Aim for 7–8 hours of regular sleep and manage stress with relaxation, breathing exercises, or hobbies.",
        "Keep regular follow-up with your clinician, especially if your reports are abnormal or symptoms change.",
    ]
    sections.append({
        'title': 'General lifestyle & prevention',
        'applies': True,
        'recommendations': general_recs,
        'marker_summary': None,
    })

    return jsonify({
        'sections': sections,
        'markers': {
            'glucose': glucose_summary,
            'cholesterol': cholesterol_summary,
            'hemoglobin': hemoglobin_summary,
        },
        'disclaimer': 'General lifestyle education based on lab trends only – not a diagnosis or treatment plan. Always discuss major lifestyle or medicine changes with your doctor.',
    }), 200
