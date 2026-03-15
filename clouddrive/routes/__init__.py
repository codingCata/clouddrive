from .auth import auth_bp
from .user import user_bp
from .files import files_bp
from .folders import folders_bp
from .api_key import api_key_bp
from .health import health_bp
from .recycle import recycle_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(api_key_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(recycle_bp)
