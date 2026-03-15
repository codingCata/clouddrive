from flask import Blueprint

from ..auth import login_required, get_current_user_id
from ..models import UserModel
from ..utils.responses import success, error

api_key_bp = Blueprint('api_key', __name__, url_prefix='/api')


@api_key_bp.route('/api-key', methods=['GET'])
@login_required
def get_api_key_info():
    user_id = get_current_user_id()
    info = UserModel.get_api_key_info(user_id)
    return success(info)


@api_key_bp.route('/api-key', methods=['POST'])
@login_required
def create_api_key():
    user_id = get_current_user_id()
    info = UserModel.get_api_key_info(user_id)
    
    if info['has_key']:
        return error('API key already exists. Delete it first.', 'DUPLICATE', 400)
    
    api_key = UserModel.generate_api_key(user_id)
    return success({
        'api_key': api_key
    }, 'Save this API key now. You won\'t be able to see it again.', 201)


@api_key_bp.route('/api-key', methods=['DELETE'])
@login_required
def delete_api_key():
    user_id = get_current_user_id()
    UserModel.delete_api_key(user_id)
    return success(message='API key deleted successfully')


@api_key_bp.route('/ai-docs', methods=['GET'])
def ai_docs():
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
