import os
from flask import Blueprint, request, jsonify, g
import bcrypt
import jwt
from datetime import datetime, timedelta
from database.mongo import insert_user, fetch_user
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
