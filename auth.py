from functools import wraps
from flask import session, jsonify, request
from models import UserModel


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


def create_session(user_id, username):
    session['user_id'] = user_id
    session['username'] = username


def clear_session():
    session.clear()


def get_current_user_id():
    # First check session
    if 'user_id' in session:
        return session.get('user_id')
    
    # Then check API key header
    api_key = request.headers.get('X-API-Key')
    if api_key:
        user = UserModel.get_by_api_key(api_key)
        if user:
            return user['id']
    
    return None


def get_current_username():
    # First check session
    if 'username' in session:
        return session.get('username')
    
    # Then check API key header
    api_key = request.headers.get('X-API-Key')
    if api_key:
        user = UserModel.get_by_api_key(api_key)
        if user:
            return user['username']
    
    return None
