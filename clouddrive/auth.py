from functools import wraps
from flask import session, request
from .models import UserModel
from .utils.responses import error


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return error('Unauthorized', 'UNAUTHORIZED', 401)
        if user_id == 'RATE_LIMITED':
            return error('Too many requests. Please try again later.', 'RATE_LIMITED', 429)
        return f(*args, **kwargs)
    return decorated_function


def create_session(user_id, username):
    session['user_id'] = user_id
    session['username'] = username


def clear_session():
    session.clear()


def get_current_user_id():
    if 'user_id' in session:
        return session.get('user_id')
    
    api_key = request.headers.get('X-API-Key')
    if api_key:
        user = UserModel.get_by_api_key(api_key)
        if user is None:
            return None
        if user == 'RATE_LIMITED':
            return 'RATE_LIMITED'
        return user['id']
    
    return None


def get_current_username():
    if 'username' in session:
        return session.get('username')
    
    api_key = request.headers.get('X-API-Key')
    if api_key:
        user = UserModel.get_by_api_key(api_key)
        if user and user != 'RATE_LIMITED':
            return user['username']
    
    return None
