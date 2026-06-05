from bson.objectid import ObjectId
from flask import Blueprint, jsonify, g, request
from database.mongo import fetch_predictions_by_user, fetch_reports_by_user, fetch_report
from routes.auth_routes import token_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/predictions', methods=['GET'])
@token_required
def get_user_predictions():
    user_id = str(g.current_user['_id'])
    predictions = fetch_predictions_by_user(user_id)
    # Convert ObjectId to string for JSON serialization
    for p in predictions:
        p['_id'] = str(p['_id'])
        p['report_id'] = str(p.get('report_id', ''))
        p['created_at'] = str(p.get('created_at', ''))
    return jsonify({'predictions': predictions}), 200


@user_bp.route('/reports', methods=['GET'])
@token_required
def get_user_reports():
    user_id = str(g.current_user['_id'])
    limit = request.args.get('limit', 50)
    reports = fetch_reports_by_user(user_id, limit=limit)

    for r in reports:
        r['_id'] = str(r['_id'])
        r['created_at'] = str(r.get('created_at', ''))
    return jsonify({'reports': reports}), 200


@user_bp.route('/reports/<report_id>', methods=['GET'])
@token_required
def get_user_report(report_id):
    user_id = str(g.current_user['_id'])
    try:
        oid = ObjectId(report_id)
    except Exception:
        return jsonify({'error': 'Invalid report id'}), 400

    report = fetch_report({'_id': oid, 'user_id': user_id})
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    report['_id'] = str(report['_id'])
    report['created_at'] = str(report.get('created_at', ''))
    return jsonify({'report': report}), 200
