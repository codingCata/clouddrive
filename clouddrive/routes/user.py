from flask import Blueprint, jsonify

from ..auth import login_required, get_current_user_id, get_current_username
from ..utils.storage import get_user_storage_used

user_bp = Blueprint('user', __name__, url_prefix='/api')


@user_bp.route('/user', methods=['GET'])
@login_required
def get_user():
    user_id = get_current_user_id()
    username = get_current_username()
    storage_used = get_user_storage_used(user_id)
    
    return jsonify({
        'user_id': user_id,
        'username': username,
        'storage_used': storage_used
    }), 200
