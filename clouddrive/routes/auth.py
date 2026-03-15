from flask import Blueprint, request, jsonify

from ..models import UserModel
from ..auth import login_required, create_session, clear_session

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    
    existing_user = UserModel.get_by_username(username)
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    from ..utils.storage import get_user_storage_path
    user_id = UserModel.create(username, password)
    get_user_storage_path(user_id)
    
    return jsonify({'message': 'User registered successfully', 'user_id': user_id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = UserModel.get_by_username(username)
    
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if not UserModel.verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    create_session(user['id'], user['username'])
    
    return jsonify({'message': 'Login successful', 'username': user['username']}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    clear_session()
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    from ..auth import get_current_user_id
    
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password required'}), 400
    
    if len(new_password) < 4:
        return jsonify({'error': 'New password must be at least 4 characters'}), 400
    
    user_id = get_current_user_id()
    user = UserModel.get_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not UserModel.verify_password(current_password, user['password_hash']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    UserModel.update_password(user_id, new_password)
    
    return jsonify({'message': 'Password changed successfully'}), 200
