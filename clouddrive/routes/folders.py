from flask import Blueprint, request

from ..auth import login_required, get_current_user_id
from ..models import FolderModel
from ..utils.responses import success, error

folders_bp = Blueprint('folders', __name__, url_prefix='/api')


@folders_bp.route('/folders', methods=['POST'])
@login_required
def create_folder():
    user_id = get_current_user_id()
    data = request.get_json()
    name = data.get('name', '').strip()
    parent_id = data.get('parent_id')
    
    if not name:
        return error('Folder name required', 'VALIDATION_ERROR', 400)
    
    if parent_id:
        folder = FolderModel.get_by_id(parent_id, user_id)
        if not folder:
            return error('Parent folder not found', 'NOT_FOUND', 404)
    
    folder_id = FolderModel.create(user_id, name, parent_id)
    return success({'folder_id': folder_id}, 'Folder created', 201)


@folders_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    user_id = get_current_user_id()
    
    folder = FolderModel.get_by_id(folder_id, user_id)
    if not folder:
        return error('Folder not found', 'NOT_FOUND', 404)
    
    result = FolderModel.delete(folder_id, user_id)
    if not result:
        return error('Folder not empty', 'VALIDATION_ERROR', 400)
    
    return success(message='Folder deleted')
