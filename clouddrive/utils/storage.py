import os


def get_user_storage_path(user_id, folder_id=None, storage_dir=None):
    if storage_dir is None:
        from .. import STORAGE_DIR
        storage_dir = STORAGE_DIR
    
    if folder_id:
        from ..models import FolderModel
        folder = FolderModel.get_by_id(folder_id, user_id)
        if folder:
            user_path = os.path.join(storage_dir, str(user_id), 'folders', str(folder_id))
        else:
            user_path = os.path.join(storage_dir, str(user_id))
    else:
        user_path = os.path.join(storage_dir, str(user_id))
    
    os.makedirs(user_path, exist_ok=True)
    return user_path


def get_user_storage_used(user_id):
    from ..models import FileModel
    return FileModel.get_total_size(user_id)


def is_previewable(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    from ..constants import PREVIEWABLE_EXTS
    return ext in PREVIEWABLE_EXTS


def get_preview_content_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    from ..constants import PREVIEWABLE_TYPES
    return PREVIEWABLE_TYPES.get(ext, 'application/octet-stream')


def validate_file_path(filepath: str, user_id: int, storage_dir: str) -> bool:
    if not filepath or not user_id:
        return False
    abs_filepath = os.path.abspath(filepath)
    abs_storage = os.path.abspath(storage_dir)
    user_dir = os.path.join(abs_storage, str(user_id))
    return abs_filepath.startswith(user_dir + os.sep)


def safe_filename(filename: str) -> str:
    filename = filename.replace('/', '').replace('\\', '')
    filename = filename.replace('\x00', '')
    return filename[:255]
