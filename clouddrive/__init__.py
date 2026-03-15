import os
import sys
import secrets

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PACKAGE_DIR)
sys.path.insert(0, os.path.dirname(BASE_DIR))

TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
STORAGE_DIR = os.environ.get('STORAGE_DIR', os.path.join(BASE_DIR, 'storage'))
DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'clouddrive.db'))

env_secret = os.environ.get('SECRET_KEY')
if env_secret:
    SECRET_KEY = env_secret
else:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    print("WARNING: SECRET_KEY not set. Using generated key. Sessions will be invalid after restart.")

os.makedirs(STORAGE_DIR, exist_ok=True)

from flask import Flask
from .models import init_db
from .routes import register_blueprints


def create_app():
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
    app.secret_key = SECRET_KEY
    
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        SESSION_COOKIE_SAMESITE='Lax',
    )
    
    from .utils.logging import setup_logging
    logger = setup_logging(app)
    logger.info("CloudDrive application starting...")
    
    init_db()
    register_blueprints(app)
    
    logger.info("CloudDrive application ready")
    
    return app


app = create_app()
