import os
import uuid
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file

from config import STORAGE_DIR
from models import UserModel, FileModel, FolderModel
from auth import login_required, create_session, clear_session, get_current_user_id, get_current_username

api_bp = Blueprint('api', __name__, url_prefix='/api')


def get_user_storage_path(user_id, folder_id=None):
    if folder_id:
        folder = FolderModel.get_by_id(folder_id, user_id)
        if folder:
            user_path = os.path.join(STORAGE_DIR, str(user_id), 'folders', str(folder_id))
        else:
            user_path = os.path.join(STORAGE_DIR, str(user_id))
    else:
        user_path = os.path.join(STORAGE_DIR, str(user_id))
    os.makedirs(user_path, exist_ok=True)
    return user_path


def get_user_storage_used(user_id):
    return FileModel.get_total_size(user_id)


@api_bp.route('/register', methods=['POST'])
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
    
    user_id = UserModel.create(username, password)
    get_user_storage_path(user_id)
    
    return jsonify({'message': 'User registered successfully', 'user_id': user_id}), 201


@api_bp.route('/login', methods=['POST'])
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


@api_bp.route('/logout', methods=['POST'])
def logout():
    clear_session()
    return jsonify({'message': 'Logged out successfully'}), 200


@api_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
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


@api_bp.route('/user', methods=['GET'])
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


@api_bp.route('/files', methods=['GET'])
@login_required
def list_files():
    user_id = get_current_user_id()
    folder_id = request.args.get('folder_id', type=int)
    
    files = FileModel.get_by_user(user_id, folder_id)
    folders = FolderModel.get_by_user(user_id, folder_id)
    
    return jsonify({
        'files': [
            {
                'id': row['id'],
                'filename': row['filename'],
                'filesize': row['filesize'],
                'created_at': row['created_at']
            }
            for row in files
        ],
        'folders': [
            {
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at']
            }
            for row in folders
        ]
    }), 200


@api_bp.route('/search', methods=['GET'])
@login_required
def search():
    user_id = get_current_user_id()
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 1:
        return jsonify({'files': [], 'folders': []}), 200
    
    files = FileModel.search(user_id, query)
    folders = FolderModel.search(user_id, query)
    
    return jsonify({
        'files': [
            {
                'id': row['id'],
                'filename': row['filename'],
                'filesize': row['filesize'],
                'created_at': row['created_at'],
                'folder_id': row['folder_id'] if 'folder_id' in row.keys() else None
            }
            for row in files
        ],
        'folders': [
            {
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at']
            }
            for row in folders
        ]
    }), 200


@api_bp.route('/folders', methods=['POST'])
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


@api_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
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


@api_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    user_id = get_current_user_id()
    folder_id = request.form.get('folder_id', type=int)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    original_filename = str(file.filename) if file.filename else 'unknown'
    ext = os.path.splitext(original_filename)[1] or ''
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    user_path = get_user_storage_path(user_id, folder_id)
    filepath = os.path.join(user_path, unique_filename)
    file.save(filepath)
    
    FileModel.create(user_id, original_filename, filepath, file_size, folder_id)
    
    return jsonify({
        'message': 'File uploaded successfully',
        'filename': original_filename,
        'filesize': file_size
    }), 201


@api_bp.route('/download/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    user_id = get_current_user_id()
    
    file_record = FileModel.get_by_filename(user_id, filename)
    
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    filepath = file_record['filepath']
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=file_record['filename']
    )


PREVIEWABLE_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'svg': 'image/svg+xml',
    'pdf': 'application/pdf',
    'txt': 'text/plain',
    'md': 'text/markdown',
    'json': 'application/json',
    'js': 'text/javascript',
    'ts': 'text/typescript',
    'py': 'text/x-python',
    'html': 'text/html',
    'css': 'text/css',
    'xml': 'application/xml',
    'yaml': 'application/x-yaml',
    'sh': 'text/x-shellscript',
    'yml': 'application/x-yaml',
}

PREVIEWABLE_EXTS = set(PREVIEWABLE_TYPES.keys())
MAX_PREVIEW_SIZE = 10 * 1024 * 1024  # 10MB

@api_bp.route('/preview/<filename>', methods=['GET'])
@login_required
def preview_file(filename):
    user_id = get_current_user_id()
    
    file_record = FileModel.get_by_filename(user_id, filename)
    
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    filepath = file_record['filepath']
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found on disk'}), 404
    
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in PREVIEWABLE_EXTS:
        return jsonify({'error': 'Preview not supported for this file type'}), 400
    
    file_size = os.path.getsize(filepath)
    
    if file_size > MAX_PREVIEW_SIZE:
        return jsonify({'error': 'File too large to preview', 'max_size': MAX_PREVIEW_SIZE}), 400
    
    content_type = PREVIEWABLE_TYPES.get(ext, 'application/octet-stream')
    
    return send_file(
        filepath,
        mimetype=content_type,
        as_attachment=False
    )


@api_bp.route('/delete/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    user_id = get_current_user_id()
    
    filepath = FileModel.delete(user_id, filename)
    
    if not filepath:
        return jsonify({'error': 'File not found'}), 404
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return jsonify({'message': 'File deleted successfully'}), 200


@api_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete():
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    files = data.get('files', [])
    folders = data.get('folders', [])
    
    deleted_files = []
    deleted_folders = []
    failed = []
    
    for filename in files:
        filepath = FileModel.delete(user_id, filename)
        if filepath:
            if os.path.exists(filepath):
                os.remove(filepath)
            deleted_files.append(filename)
        else:
            failed.append({'type': 'file', 'name': filename, 'error': 'Not found'})
    
    for folder_id in folders:
        if FolderModel.delete(folder_id, user_id):
            deleted_folders.append(folder_id)
        else:
            failed.append({'type': 'folder', 'id': folder_id, 'error': 'Not found or not empty'})
    
    return jsonify({
        'message': f'{len(deleted_files)} files and {len(deleted_folders)} folders deleted',
        'deleted_files': deleted_files,
        'deleted_folders': deleted_folders,
        'failed': failed
    }), 200


import zipfile
import io

@api_bp.route('/batch-download', methods=['POST'])
@login_required
def batch_download():
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    files = data.get('files', [])
    
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in files:
            file_record = FileModel.get_by_filename(user_id, filename)
            if file_record and os.path.exists(file_record['filepath']):
                with open(file_record['filepath'], 'rb') as f:
                    zf.writestr(filename, f.read())
    
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='files.zip'
    )


@api_bp.route('/api-key', methods=['GET'])
@login_required
def get_api_key_info():
    user_id = get_current_user_id()
    info = UserModel.get_api_key_info(user_id)
    return jsonify(info), 200


@api_bp.route('/api-key', methods=['POST'])
@login_required
def create_api_key():
    user_id = get_current_user_id()
    info = UserModel.get_api_key_info(user_id)
    
    if info['has_key']:
        return jsonify({'error': 'API key already exists. Delete it first.'}), 400
    
    api_key = UserModel.generate_api_key(user_id)
    return jsonify({
        'api_key': api_key,
        'message': 'Save this API key now. You won\'t be able to see it again.'
    }), 201


@api_bp.route('/api-key', methods=['DELETE'])
@login_required
def delete_api_key():
    user_id = get_current_user_id()
    UserModel.delete_api_key(user_id)
    return jsonify({'message': 'API key deleted successfully'}), 200


@api_bp.route('/ai-docs', methods=['GET'])
def ai_docs():
    """API documentation for AI integration."""
    return jsonify({
        'name': 'CloudDrive API',
        'description': 'Personal cloud storage API for AI integration',
        'authentication': {
            'session': {
                'description': 'Use session cookie from login',
                'example': 'Cookie: session=xxx'
            },
            'api_key': {
                'description': 'Use API key in header',
                'header': 'X-API-Key',
                'example': 'X-API-Key: your-api-key-here'
            }
        },
        'endpoints': {
            'list_files': {
                'method': 'GET',
                'path': '/api/files',
                'params': {
                    'folder_id': 'optional, integer - folder ID to list'
                },
                'description': 'List all files and folders',
                'example': {
                    'request': 'GET /api/files?folder_id=1',
                    'response': {
                        'files': [{'id': 1, 'filename': 'test.txt', 'filesize': 1024, 'created_at': '2024-01-01'}],
                        'folders': [{'id': 1, 'name': 'Documents'}]
                    }
                }
            },
            'get_user': {
                'method': 'GET',
                'path': '/api/user',
                'description': 'Get current user info including storage usage',
                'example': {
                    'request': 'GET /api/user',
                    'response': {'user_id': 1, 'username': 'john', 'storage_used': 1024000}
                }
            },
            'download_file': {
                'method': 'GET',
                'path': '/api/download/<filename>',
                'description': 'Download a file',
                'example': {
                    'request': 'GET /api/download/document.pdf'
                }
            },
            'upload_file': {
                'method': 'POST',
                'path': '/api/upload',
                'description': 'Upload a file',
                'example': {
                    'request': 'POST /api/upload',
                    'body': 'multipart/form-data with file field'
                }
            },
            'create_folder': {
                'method': 'POST',
                'path': '/api/folders',
                'description': 'Create a new folder',
                'example': {
                    'request': 'POST /api/folders',
                    'body': {'name': 'MyFolder', 'parent_id': None}
                }
            },
            'delete_file': {
                'method': 'DELETE',
                'path': '/api/delete/<filename>',
                'description': 'Delete a file',
                'example': {
                    'request': 'DELETE /api/delete/old.txt'
                }
            },
            'delete_folder': {
                'method': 'DELETE',
                'path': '/api/folders/<folder_id>',
                'description': 'Delete an empty folder',
                'example': {
                    'request': 'DELETE /api/folders/5'
                }
            }
        },
        'usage_example': {
            'step1': 'Login or use existing API key',
            'step2': 'Get API key: POST /api/api-key (requires login)',
            'step3': 'Use X-API-Key header for all requests'
        }
    }), 200
