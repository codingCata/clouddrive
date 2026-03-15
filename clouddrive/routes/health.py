from flask import Blueprint, jsonify
import sqlite3
import os

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    checks = {
        'database': check_database(),
        'storage': check_storage()
    }
    
    all_ok = all(c['status'] == 'ok' for c in checks.values())
    status = 200 if all_ok else 503
    
    return jsonify({
        'status': 'healthy' if all_ok else 'unhealthy',
        'checks': checks
    }), status


def check_database():
    try:
        from .. import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.execute('SELECT 1')
        conn.close()
        return {'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def check_storage():
    try:
        from .. import STORAGE_DIR
        writable = os.access(STORAGE_DIR, os.W_OK)
        return {'status': 'ok' if writable else 'error', 'path': STORAGE_DIR, 'writable': writable}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
