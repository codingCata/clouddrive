import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())

STORAGE_DIR = os.environ.get('STORAGE_DIR', os.path.join(BASE_DIR, 'storage'))
DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'clouddrive.db'))

os.makedirs(STORAGE_DIR, exist_ok=True)
