from flask import Blueprint, request, jsonify

from ..auth import login_required, get_current_user_id
from ..models import FolderModel

folders_bp = Blueprint('folders', __name__, url_prefix='/api')


@folders_bp.route('/folders', methods=['POST'])
@login_required
def create_folder():
    user_id = get_current_user_id()
    data = request.get_json()
    name = data.get('name', '').strip()
    parent_id = data.get('parent_id')
    
    if not name:
        return jsonify({'error': 'Folder name required'}), 400
    
    if parent_id:
        folder = FolderModel.get_by_id(parent_id, user_id)
        if not folder:
            return jsonify({'error': 'Parent folder not found'}), 404
    
    folder_id = FolderModel.create(user_id, name, parent_id)
    return jsonify({'message': 'Folder created', 'folder_id': folder_id}), 201


@folders_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    user_id = get_current_user_id()
    
    folder = FolderModel.get_by_id(folder_id, user_id)
    if not folder:
        return jsonify({'error': 'Folder not found'}), 404
    
    success = FolderModel.delete(folder_id, user_id)
    if not success:
        return jsonify({'error': 'Folder not empty'}), 400
    
    return jsonify({'message': 'Folder deleted'}), 200
