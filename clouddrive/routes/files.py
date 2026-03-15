from flask import Blueprint, request, jsonify, send_file

from ..auth import login_required, get_current_user_id
from ..models import FileModel, FolderModel, FileFolderModel
from ..utils.storage import get_user_storage_path, validate_file_path, safe_filename
from ..utils.responses import success, error
from .. import STORAGE_DIR

files_bp = Blueprint('files', __name__, url_prefix='/api')

DEFAULT_PAGE_SIZE = 10


@files_bp.route('/files', methods=['GET'])
@login_required
def list_files():
    user_id = get_current_user_id()
    folder_id = request.args.get('folder_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', DEFAULT_PAGE_SIZE, type=int)
    
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    
    result = FileFolderModel.get_files_and_folders(user_id, folder_id, page, page_size)
    files = result['files']
    folders = result['folders']
    total_files = result['total_files']
    total_folders = result['total_folders']
    total_items = total_files + total_folders
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 1
    
    return success({
        'files': [
            {
                'id': row['id'],
                'filename': row['name'],
                'filesize': row['filesize'],
                'folder_id': row['folder_id'],
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
        ],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    })


@files_bp.route('/search', methods=['GET'])
@login_required
def search():
    user_id = get_current_user_id()
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 1:
        return success({'files': [], 'folders': []})
    
    files = FileModel.search(user_id, query)
    folders = FolderModel.search(user_id, query)
    
    return success({
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
    })


@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    import uuid
    import os
    
    user_id = get_current_user_id()
    folder_id = request.form.get('folder_id', type=int)
    
    if 'file' not in request.files:
        return error('No file provided', 'VALIDATION_ERROR', 400)
    
    file = request.files['file']
    if file.filename == '':
        return error('No file selected', 'VALIDATION_ERROR', 400)
    
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
    
    return success({
        'filename': original_filename,
        'filesize': file_size
    }, 'File uploaded successfully', 201)


@files_bp.route('/download/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    import os
    
    user_id = get_current_user_id()
    safe_name = safe_filename(filename)
    
    file_record = FileModel.get_by_filename(user_id, safe_name)
    
    if not file_record:
        return error('File not found', 'NOT_FOUND', 404)
    
    filepath = file_record['filepath']
    
    if not os.path.exists(filepath):
        return error('File not found on disk', 'NOT_FOUND', 404)
    
    if not validate_file_path(filepath, user_id, STORAGE_DIR):
        return error('Invalid file path', 'FORBIDDEN', 403)
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=file_record['filename']
    )


@files_bp.route('/preview/<filename>', methods=['GET'])
@login_required
def preview_file(filename):
    import os
    
    user_id = get_current_user_id()
    safe_name = safe_filename(filename)
    
    file_record = FileModel.get_by_filename(user_id, safe_name)
    
    if not file_record:
        return error('File not found', 'NOT_FOUND', 404)
    
    filepath = file_record['filepath']
    
    if not os.path.exists(filepath):
        return error('File not found on disk', 'NOT_FOUND', 404)
    
    if not validate_file_path(filepath, user_id, STORAGE_DIR):
        return error('Invalid file path', 'FORBIDDEN', 403)
    
    from ..constants import PREVIEWABLE_EXTS, MAX_PREVIEW_SIZE, PREVIEWABLE_TYPES
    
    ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
    
    if ext not in PREVIEWABLE_EXTS:
        return error('Preview not supported for this file type', 'VALIDATION_ERROR', 400)
    
    file_size = os.path.getsize(filepath)
    
    if file_size > MAX_PREVIEW_SIZE:
        return error(f'File too large to preview (max {MAX_PREVIEW_SIZE // 1024 // 1024}MB)', 'VALIDATION_ERROR', 400, {'max_size': MAX_PREVIEW_SIZE})
    
    content_type = PREVIEWABLE_TYPES.get(ext, 'application/octet-stream')
    
    return send_file(
        filepath,
        mimetype=content_type,
        as_attachment=False
    )


@files_bp.route('/delete/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    import os
    
    user_id = get_current_user_id()
    
    filepath = FileModel.delete(user_id, filename)
    
    if not filepath:
        return error('File not found', 'NOT_FOUND', 404)
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return success(message='File deleted successfully')


@files_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete():
    import os
    
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
    
    return success({
        'deleted_files': deleted_files,
        'deleted_folders': deleted_folders,
        'failed': failed
    }, f'{len(deleted_files)} files and {len(deleted_folders)} folders deleted')


@files_bp.route('/batch-download', methods=['POST'])
@login_required
def batch_download():
    import os
    import zipfile
    import tempfile
    
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    files = data.get('files', [])
    
    if not files:
        return error('No files selected', 'VALIDATION_ERROR', 400)
    
    if len(files) > 50:
        return error('Maximum 50 files allowed per download', 'VALIDATION_ERROR', 400)
    
    MAX_BATCH_SIZE = 500 * 1024 * 1024
    total_size = 0
    valid_files = []
    
    for filename in files:
        file_record = FileModel.get_by_filename(user_id, filename)
        if file_record and os.path.exists(file_record['filepath']):
            size = os.path.getsize(file_record['filepath'])
            total_size += size
            valid_files.append((file_record, filename))
    
    if total_size > MAX_BATCH_SIZE:
        return error(f'Total size exceeds {MAX_BATCH_SIZE // 1024 // 1024}MB limit', 'VALIDATION_ERROR', 400)
    
    temp_path = tempfile.NamedTemporaryFile(suffix='.zip', delete=False).name
    
    try:
        with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_record, filename in valid_files:
                zf.write(file_record['filepath'], filename)
        
        return send_file(
            temp_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name='files.zip'
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
