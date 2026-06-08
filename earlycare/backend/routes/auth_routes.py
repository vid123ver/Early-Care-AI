import os
import hashlib
import secrets
from flask import Blueprint, request, jsonify, g
import bcrypt
import jwt
from datetime import datetime, timedelta
from database.mongo import insert_user, fetch_user, update_user
from bson.objectid import ObjectId

SECRET_KEY = os.getenv(
    'JWT_SECRET',
    'change_me_to_a_long_random_secret_key_at_least_32_bytes'
)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Helper: hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Helper: verify password
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Helper: create JWT token
def create_token(user_id):
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Middleware: token required
def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[-1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'message': 'Token is invalid!'}), 401
            try:
                user_object_id = ObjectId(user_id)
            except Exception:
                return jsonify({'message': 'Token is invalid!'}), 401

            user = fetch_user({'_id': user_object_id})
            if not user:
                return jsonify({'message': 'User not found!'}), 401
            g.current_user = user
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# POST /auth/register
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password required'}), 400
    if len(data.get('password', '')) < 6:
        return jsonify({'message': 'Password must be at least 6 characters'}), 400
    if fetch_user({'email': data['email']}):
        return jsonify({'message': 'User already exists'}), 409
    hashed = hash_password(data['password'])
    user = {
        'name': (data.get('name') or '').strip() or None,
        'email': data['email'],
        'password': hashed,
        'created_at': datetime.utcnow()
    }
    insert_user(user)
    return jsonify({'message': 'User registered successfully'}), 201

# POST /auth/login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = fetch_user({'email': data.get('email')})
    if not user or not verify_password(data.get('password', ''), user['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    token = create_token(user['_id'])
    return jsonify({'token': token}), 200

# GET /auth/me
@auth_bp.route('/me', methods=['GET'])
@token_required
def me():
    user = g.current_user
    return jsonify({
        'id': str(user.get('_id')),
        'name': user.get('name'),
        'email': user.get('email'),
        'created_at': user.get('created_at'),
    }), 200


# POST /auth/logout
# JWT is stateless; logout is handled client-side by deleting the token.
@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Logged out'}), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = fetch_user({'email': email})
    if not user:
        return jsonify({'message': 'If the email exists, a reset code has been created.'}), 200

    reset_token = secrets.token_urlsafe(32)
    reset_token_hash = hashlib.sha256(reset_token.encode('utf-8')).hexdigest()
    reset_expires_at = datetime.utcnow() + timedelta(minutes=30)

    update_user(
        {'_id': user['_id']},
        {
            '$set': {
                'password_reset_token_hash': reset_token_hash,
                'password_reset_expires_at': reset_expires_at,
            }
        },
    )

    return jsonify({
        'message': 'Reset code created. Copy it and use it to set a new password.',
        'reset_token': reset_token,
        'expires_in_minutes': 30,
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    reset_token = (data.get('reset_token') or '').strip()
    new_password = data.get('new_password') or ''

    if not email or not reset_token or not new_password:
        return jsonify({'message': 'Email, reset code, and new password are required'}), 400
    if len(new_password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters'}), 400

    user = fetch_user({'email': email})
    if not user:
        return jsonify({'message': 'Invalid reset code or email'}), 400

    stored_hash = user.get('password_reset_token_hash')
    expires_at = user.get('password_reset_expires_at')
    if not stored_hash or not expires_at:
        return jsonify({'message': 'No active reset request found'}), 400

    if datetime.utcnow() > expires_at:
        return jsonify({'message': 'Reset code has expired'}), 400

    reset_token_hash = hashlib.sha256(reset_token.encode('utf-8')).hexdigest()
    if reset_token_hash != stored_hash:
        return jsonify({'message': 'Invalid reset code or email'}), 400

    update_user(
        {'_id': user['_id']},
        {
            '$set': {
                'password': hash_password(new_password),
            },
            '$unset': {
                'password_reset_token_hash': '',
                'password_reset_expires_at': '',
            },
        },
    )

    return jsonify({'message': 'Password updated successfully'}), 200
