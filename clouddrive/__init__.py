import os
import sys

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PACKAGE_DIR)
sys.path.insert(0, os.path.dirname(BASE_DIR))

TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
STORAGE_DIR = os.environ.get('STORAGE_DIR', os.path.join(BASE_DIR, 'storage'))
DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'clouddrive.db'))

os.makedirs(STORAGE_DIR, exist_ok=True)

from flask import Flask
from .models import init_db
from .routes import register_blueprints


def create_app():
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
    app.secret_key = SECRET_KEY
    
    init_db()
    register_blueprints(app)
    
    return app


app = create_app()
