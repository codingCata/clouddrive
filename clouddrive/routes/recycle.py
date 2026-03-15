from flask import Blueprint, request

from ..auth import login_required, get_current_user_id
from ..models import RecycleBinModel
from ..utils.responses import success, error

recycle_bp = Blueprint('recycle', __name__, url_prefix='/api')


@recycle_bp.route('/recycle-bin', methods=['GET'])
@login_required
def list_recycle_bin():
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    result = RecycleBinModel.get_all(user_id, page, page_size)
    return success({
        'items': [
            {
                'id': item['id'],
                'item_type': item['item_type'],
                'item_id': item['item_id'],
                'name': item['original_name'],
                'size': item['filesize'],
                'deleted_at': item['deleted_at'],
                'expires_at': item['expires_at']
            }
            for item in result['items']
        ],
        'total': result['total'],
        'page': page,
        'page_size': page_size
    })


@recycle_bp.route('/recycle-bin/<int:item_id>/restore', methods=['POST'])
@login_required
def restore_item(item_id):
    user_id = get_current_user_id()
    
    if RecycleBinModel.restore(user_id, item_id):
        return success(message='Item restored successfully')
    return error('Item not found', 'NOT_FOUND', 404)


@recycle_bp.route('/recycle-bin/<int:item_id>', methods=['DELETE'])
@login_required
def permanent_delete_item(item_id):
    user_id = get_current_user_id()
    
    if RecycleBinModel.permanent_delete(user_id, item_id):
        return success(message='Item permanently deleted')
    return error('Item not found', 'NOT_FOUND', 404)


@recycle_bp.route('/recycle-bin/empty', methods=['POST'])
@login_required
def empty_recycle_bin():
    user_id = get_current_user_id()
    RecycleBinModel.empty(user_id)
    return success(message='Recycle bin emptied')


@recycle_bp.route('/recycle-bin/cleanup', methods=['POST'])
def cleanup_expired():
    deleted = RecycleBinModel.cleanup_expired()
    return success(message=f'Cleaned up {deleted} expired items')