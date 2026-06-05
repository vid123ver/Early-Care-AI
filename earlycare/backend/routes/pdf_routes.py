import os
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from database.mongo import insert_report
from routes.auth_routes import token_required

UPLOAD_FOLDER = 'uploads'
pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')

def _get_pdf_impl():
    try:
        from ai.pdf_extractor import extract_text_from_pdf, extract_metrics_from_text
        return extract_text_from_pdf, extract_metrics_from_text, None
    except Exception as e:
        return None, None, e

@pdf_bp.route('/upload', methods=['POST'])
@token_required
def upload_pdf():
    extract_text_from_pdf, extract_metrics_from_text, err = _get_pdf_impl()
    if err:
        return jsonify({'error': 'PDF extractor dependencies are not installed', 'details': str(err)}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    try:
        text = extract_text_from_pdf(filepath)
        metrics = extract_metrics_from_text(text) if extract_metrics_from_text else {}

        # Save only parsed data (not the PDF) to MongoDB, tied to the current user.
        user_id = str(g.current_user['_id'])
        report_doc = {
            'user_id': user_id,
            'filename': file.filename,
            'metrics': metrics,
            'extracted_text_preview': (text[:2000] if text else ""),
            'created_at': datetime.utcnow(),
        }
        inserted = insert_report(report_doc)

        return jsonify({
            'report_id': str(inserted.inserted_id),
            'extracted_text': text,
            'metrics': metrics,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Remove the uploaded PDF after parsing to save disk space.
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
