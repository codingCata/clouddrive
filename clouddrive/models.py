import sqlite3
import bcrypt
import time
from threading import Lock
from flask import request


# Rate limiting storage
_rate_limit_store = {}
_rate_lock = Lock()


class RateLimiter:
    """Simple in-memory rate limiter to prevent brute force attacks"""
    
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes
    WINDOW_SIZE = 60  # 60 seconds
    
    @classmethod
    def check_rate_limit(cls, identifier: str) -> tuple:
        """Check if request is allowed. Returns (is_allowed, remaining_attempts_or_lockout_time)"""
        now = time.time()
        
        with _rate_lock:
            if identifier not in _rate_limit_store:
                _rate_limit_store[identifier] = {
                    'attempts': 0,
                    'locked_until': 0,
                    'first_attempt': now
                }
            
            record = _rate_limit_store[identifier]
            
            # Check if locked out
            if record['locked_until'] > now:
                remaining = int(record['locked_until'] - now)
                return False, remaining
            
            # Reset window if expired
            if now - record['first_attempt'] > cls.WINDOW_SIZE:
                record['attempts'] = 0
                record['first_attempt'] = now
            
            remaining = cls.MAX_ATTEMPTS - record['attempts']
            return remaining > 0, max(0, remaining)
    
    @classmethod
    def record_failure(cls, identifier: str):
        """Record failed attempt"""
        with _rate_lock:
            if identifier not in _rate_limit_store:
                _rate_limit_store[identifier] = {
                    'attempts': 0,
                    'locked_until': 0,
                    'first_attempt': time.time()
                }
            
            record = _rate_limit_store[identifier]
            record['attempts'] += 1
            
            if record['attempts'] >= cls.MAX_ATTEMPTS:
                record['locked_until'] = time.time() + cls.LOCKOUT_DURATION
    
    @classmethod
    def record_success(cls, identifier: str):
        """Reset on successful authentication"""
        with _rate_lock:
            if identifier in _rate_limit_store:
                _rate_limit_store[identifier] = {
                    'attempts': 0,
                    'locked_until': 0,
                    'first_attempt': time.time()
                }
    
    @classmethod
    def is_locked_out(cls, identifier: str) -> bool:
        """Check if identifier is currently locked out"""
        with _rate_lock:
            if identifier not in _rate_limit_store:
                return False
            return _rate_limit_store[identifier]['locked_until'] > time.time()


def get_db():
    from . import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            parent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (parent_id) REFERENCES folders(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER NOT NULL,
            folder_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_user_folder ON files(user_id, folder_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_user_created ON files(user_id, created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_folders_user_parent ON folders(user_id, parent_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_folders_user_name ON folders(user_id, name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key)')
    
    conn.commit()
    conn.close()
    
    run_migrations()


def get_schema_version(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('SELECT MAX(version) FROM schema_migrations')
    result = cursor.fetchone()[0]
    return result if result else 0


def run_migrations():
    conn = get_db()
    cursor = conn.cursor()
    
    current_version = get_schema_version(conn)
    
    migrations = [
        (1, 'ALTER TABLE files ADD COLUMN folder_id INTEGER'),
        (2, 'ALTER TABLE users ADD COLUMN api_key TEXT'),
        (3, 'ALTER TABLE users ADD COLUMN api_key_created TIMESTAMP'),
        (4, 'ALTER TABLE files ADD COLUMN deleted_at TIMESTAMP'),
        (5, 'ALTER TABLE folders ADD COLUMN deleted_at TIMESTAMP'),
    ]
    
    for version, sql in migrations:
        if version > current_version:
            try:
                cursor.execute(sql)
                cursor.execute('INSERT INTO schema_migrations (version) VALUES (?)', (version,))
                conn.commit()
                print(f'Migration {version} applied successfully')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    cursor.execute('INSERT INTO schema_migrations (version) VALUES (?)', (version,))
                    conn.commit()
                    print(f'Migration {version} already applied (column exists)')
                else:
                    print(f'Migration {version} failed: {e}')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recycle_bin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            original_name TEXT NOT NULL,
            filepath TEXT,
            filesize INTEGER,
            folder_id INTEGER,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO schema_migrations (version) VALUES (6)')
    conn.commit()
    
    conn.close()


class UserModel:
    @staticmethod
    def create(username, password):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash.decode('utf-8'))
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    
    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def update_password(user_id, new_password):
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash.decode('utf-8'), user_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def verify_password(password, password_hash):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def get_by_api_key(api_key):
        if not api_key or not api_key.startswith('cd_live_'):
            return None
        
        rate_key = f"api_key:{request.remote_addr}"
        
        if RateLimiter.is_locked_out(rate_key):
            return None
        
        allowed, remaining = RateLimiter.check_rate_limit(rate_key)
        if not allowed:
            return None
        
        plain_key = api_key[8:]
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, api_key FROM users WHERE api_key IS NOT NULL LIMIT 100')
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            if user['api_key']:
                try:
                    if bcrypt.checkpw(plain_key.encode('utf-8'), user['api_key'].encode('utf-8')):
                        RateLimiter.record_success(rate_key)
                        return user
                except:
                    pass
        
        RateLimiter.record_failure(rate_key)
        return None
        
        plain_key = api_key[8:]
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, api_key FROM users WHERE api_key IS NOT NULL')
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            if user['api_key']:
                stored_hash = user['api_key']
                try:
                    if bcrypt.checkpw(plain_key.encode('utf-8'), stored_hash.encode('utf-8')):
                        return user
                except:
                    pass
        return None
    
    @staticmethod
    def generate_api_key(user_id):
        import secrets
        raw_key = secrets.token_hex(24)
        api_key = f"cd_live_{raw_key}"
        
        api_key_hash = bcrypt.hashpw(raw_key.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET api_key = ?, api_key_created = CURRENT_TIMESTAMP WHERE id = ?',
            (api_key_hash.decode('utf-8'), user_id)
        )
        conn.commit()
        conn.close()
        return api_key
    
    @staticmethod
    def delete_api_key(user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET api_key = NULL, api_key_created = NULL WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_api_key_info(user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT api_key, api_key_created FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result['api_key']:
            return {
                'has_key': True,
                'created_at': result['api_key_created']
            }
        return {'has_key': False, 'created_at': None}


class FileModel:
    @staticmethod
    def create(user_id, filename, filepath, filesize, folder_id=None):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO files (user_id, filename, filepath, filesize, folder_id) VALUES (?, ?, ?, ?, ?)',
            (user_id, filename, filepath, filesize, folder_id)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_user(user_id, folder_id=None, page=1, page_size=10):
        offset = (page - 1) * page_size
        conn = get_db()
        cursor = conn.cursor()
        if folder_id is None:
            cursor.execute('''
                SELECT id, filename, filesize, folder_id, created_at 
                FROM files 
                WHERE user_id = ? AND folder_id IS NULL
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, page_size, offset))
        else:
            cursor.execute('''
                SELECT id, filename, filesize, folder_id, created_at 
                FROM files 
                WHERE user_id = ? AND folder_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, folder_id, page_size, offset))
        files = cursor.fetchall()
        conn.close()
        return files
    
    @staticmethod
    def count_by_user(user_id, folder_id=None):
        conn = get_db()
        cursor = conn.cursor()
        if folder_id is None:
            cursor.execute('''
                SELECT COUNT(*) FROM files WHERE user_id = ? AND folder_id IS NULL AND deleted_at IS NULL
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT COUNT(*) FROM files WHERE user_id = ? AND folder_id = ? AND deleted_at IS NULL
            ''', (user_id, folder_id))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def get_by_filename(user_id, filename):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, filepath, filename FROM files WHERE user_id = ? AND filename = ?',
            (user_id, filename)
        )
        file = cursor.fetchone()
        conn.close()
        return file
    
    @staticmethod
    def delete(user_id, filename, permanent=False):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, filepath, filesize, folder_id FROM files WHERE user_id = ? AND filename = ? AND deleted_at IS NULL',
            (user_id, filename)
        )
        file_record = cursor.fetchone()
        
        if not file_record:
            conn.close()
            return None
        
        if permanent:
            cursor.execute('DELETE FROM files WHERE id = ?', (file_record['id'],))
            conn.commit()
            filepath = file_record['filepath']
        else:
            from datetime import datetime
            cursor.execute('UPDATE files SET deleted_at = ? WHERE id = ?', (datetime.now(), file_record['id']))
            conn.commit()
            RecycleBinModel.move_to_recycle_bin(
                user_id, 'file', file_record['id'], filename,
                file_record['filepath'], file_record['filesize'], file_record['folder_id']
            )
            filepath = file_record['filepath']
        
        conn.close()
        return filepath
    
    @staticmethod
    def get_total_size(user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(filesize) FROM files WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0

    @staticmethod
    def search(user_id, query):
        conn = get_db()
        cursor = conn.cursor()
        pattern = f'%{query}%'
        cursor.execute('''
            SELECT id, filename, filesize, created_at, folder_id
            FROM files 
            WHERE user_id = ? AND filename LIKE ? AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id, pattern))
        files = cursor.fetchall()
        conn.close()
        return files


class FolderModel:
    @staticmethod
    def create(user_id, name, parent_id=None):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO folders (user_id, name, parent_id) VALUES (?, ?, ?)',
            (user_id, name, parent_id)
        )
        conn.commit()
        folder_id = cursor.lastrowid
        conn.close()
        return folder_id
    
    @staticmethod
    def get_by_user(user_id, parent_id=None, page=1, page_size=10):
        offset = (page - 1) * page_size
        conn = get_db()
        cursor = conn.cursor()
        if parent_id is None:
            cursor.execute(
                'SELECT id, name, parent_id, created_at FROM folders WHERE user_id = ? AND parent_id IS NULL ORDER BY name LIMIT ? OFFSET ?',
                (user_id, page_size, offset)
            )
        else:
            cursor.execute(
                'SELECT id, name, parent_id, created_at FROM folders WHERE user_id = ? AND parent_id = ? ORDER BY name LIMIT ? OFFSET ?',
                (user_id, parent_id, page_size, offset)
            )
        folders = cursor.fetchall()
        conn.close()
        return folders
    
    @staticmethod
    def count_by_user(user_id, parent_id=None):
        conn = get_db()
        cursor = conn.cursor()
        if parent_id is None:
            cursor.execute(
                'SELECT COUNT(*) FROM folders WHERE user_id = ? AND parent_id IS NULL AND deleted_at IS NULL',
                (user_id,)
            )
        else:
            cursor.execute(
                'SELECT COUNT(*) FROM folders WHERE user_id = ? AND parent_id = ? AND deleted_at IS NULL',
                (user_id, parent_id)
            )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def get_by_id(folder_id, user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, parent_id FROM folders WHERE id = ? AND user_id = ?',
            (folder_id, user_id)
        )
        folder = cursor.fetchone()
        conn.close()
        return folder
    
    @staticmethod
    def delete(folder_id, user_id, permanent=False):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, parent_id FROM folders WHERE id = ? AND user_id = ?', (folder_id, user_id))
        folder = cursor.fetchone()
        
        if not folder:
            conn.close()
            return False
        
        if not permanent:
            cursor.execute('SELECT id FROM folders WHERE parent_id = ? AND deleted_at IS NULL', (folder_id,))
            if cursor.fetchall():
                conn.close()
                return False
            
            cursor.execute('SELECT id FROM files WHERE folder_id = ? AND deleted_at IS NULL', (folder_id,))
            if cursor.fetchall():
                conn.close()
                return False
        
        if permanent:
            cursor.execute('DELETE FROM files WHERE folder_id = ?', (folder_id,))
            cursor.execute('DELETE FROM folders WHERE id = ? AND user_id = ?', (folder_id, user_id))
            conn.commit()
        else:
            from datetime import datetime
            cursor.execute('UPDATE folders SET deleted_at = ? WHERE id = ?', (datetime.now(), folder_id))
            cursor.execute('UPDATE files SET deleted_at = ? WHERE folder_id = ?', (datetime.now(), folder_id))
            RecycleBinModel.move_to_recycle_bin(user_id, 'folder', folder_id, folder['name'], folder_id=folder['parent_id'])
            conn.commit()
        
        conn.close()
        return True

    @staticmethod
    def search(user_id, query):
        conn = get_db()
        cursor = conn.cursor()
        pattern = f'%{query}%'
        cursor.execute('''
            SELECT id, name, parent_id, created_at
            FROM folders 
            WHERE user_id = ? AND name LIKE ? AND deleted_at IS NULL
            ORDER BY name
            LIMIT 20
        ''', (user_id, pattern))
        folders = cursor.fetchall()
        conn.close()
        return folders


class FileFolderModel:
    @staticmethod
    def get_files_and_folders(user_id, folder_id=None, page=1, page_size=10):
        offset = (page - 1) * page_size
        conn = get_db()
        cursor = conn.cursor()
        
        if folder_id is None:
            cursor.execute('''
                SELECT id, filename as name, filesize, folder_id, created_at
                FROM files 
                WHERE user_id = ? AND folder_id IS NULL AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, page_size, offset))
            files = cursor.fetchall()
            
            cursor.execute('''
                SELECT id, name, parent_id as folder_id, created_at
                FROM folders 
                WHERE user_id = ? AND parent_id IS NULL AND deleted_at IS NULL
                ORDER BY name
                LIMIT ? OFFSET ?
            ''', (user_id, page_size, offset))
            folders = cursor.fetchall()
            
            cursor.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM files WHERE user_id = ? AND folder_id IS NULL AND deleted_at IS NULL) as file_count,
                    (SELECT COUNT(*) FROM folders WHERE user_id = ? AND parent_id IS NULL AND deleted_at IS NULL) as folder_count
            ''', (user_id, user_id))
        else:
            cursor.execute('''
                SELECT id, filename as name, filesize, folder_id, created_at
                FROM files 
                WHERE user_id = ? AND folder_id = ? AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, folder_id, page_size, offset))
            files = cursor.fetchall()
            
            cursor.execute('''
                SELECT id, name, parent_id as folder_id, created_at
                FROM folders 
                WHERE user_id = ? AND parent_id = ? AND deleted_at IS NULL
                ORDER BY name
                LIMIT ? OFFSET ?
            ''', (user_id, folder_id, page_size, offset))
            folders = cursor.fetchall()
            
            cursor.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM files WHERE user_id = ? AND folder_id = ? AND deleted_at IS NULL) as file_count,
                    (SELECT COUNT(*) FROM folders WHERE user_id = ? AND parent_id = ? AND deleted_at IS NULL) as folder_count
            ''', (user_id, folder_id, user_id, folder_id))
        
        counts = cursor.fetchone()
        conn.close()
        
        return {
            'files': files,
            'folders': folders,
            'total_files': counts['file_count'],
            'total_folders': counts['folder_count']
        }


class RecycleBinModel:
    RETENTION_DAYS = 30
    
    @staticmethod
    def move_to_recycle_bin(user_id, item_type, item_id, original_name, filepath=None, filesize=None, folder_id=None):
        from datetime import datetime, timedelta
        conn = get_db()
        cursor = conn.cursor()
        expires_at = datetime.now() + timedelta(days=RecycleBinModel.RETENTION_DAYS)
        cursor.execute('''
            INSERT INTO recycle_bin 
            (user_id, item_type, item_id, original_name, filepath, filesize, folder_id, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, item_type, item_id, original_name, filepath, filesize, folder_id, expires_at))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all(user_id, page=1, page_size=20):
        offset = (page - 1) * page_size
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, item_type, item_id, original_name, filepath, filesize, folder_id, deleted_at, expires_at
            FROM recycle_bin
            WHERE user_id = ?
            ORDER BY deleted_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, page_size, offset))
        items = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) FROM recycle_bin WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]
        conn.close()
        return {'items': items, 'total': total}
    
    @staticmethod
    def restore(user_id, item_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM recycle_bin WHERE id = ? AND user_id = ?', (item_id, user_id))
        item = cursor.fetchone()
        
        if not item:
            conn.close()
            return False
        
        if item['item_type'] == 'file':
            cursor.execute('UPDATE files SET deleted_at = NULL WHERE id = ?', (item['item_id'],))
        else:
            cursor.execute('UPDATE folders SET deleted_at = NULL WHERE id = ?', (item['item_id'],))
        
        cursor.execute('DELETE FROM recycle_bin WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def permanent_delete(user_id, item_id):
        import os
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM recycle_bin WHERE id = ? AND user_id = ?', (item_id, user_id))
        item = cursor.fetchone()
        
        if not item:
            conn.close()
            return False
        
        if item['item_type'] == 'file' and item['filepath']:
            if os.path.exists(item['filepath']):
                os.remove(item['filepath'])
            cursor.execute('DELETE FROM files WHERE id = ?', (item['item_id'],))
        else:
            cursor.execute('DELETE FROM folders WHERE id = ?', (item['item_id'],))
        
        cursor.execute('DELETE FROM recycle_bin WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def empty(user_id):
        import os
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT filepath FROM recycle_bin WHERE user_id = ? AND item_type = ?', (user_id, 'file'))
        files = cursor.fetchall()
        for f in files:
            if f['filepath'] and os.path.exists(f['filepath']):
                os.remove(f['filepath'])
        
        cursor.execute('DELETE FROM recycle_bin WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def cleanup_expired():
        from datetime import datetime
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM recycle_bin WHERE expires_at < ?', (datetime.now(),))
        expired = cursor.fetchall()
        
        import os
        for item in expired:
            if item['item_type'] == 'file' and item['filepath']:
                if os.path.exists(item['filepath']):
                    os.remove(item['filepath'])
            cursor.execute('DELETE FROM files WHERE id = ?', (item['item_id'],)) if item['item_type'] == 'file' else cursor.execute('DELETE FROM folders WHERE id = ?', (item['item_id'],))
        
        cursor.execute('DELETE FROM recycle_bin WHERE expires_at < ?', (datetime.now(),))
        conn.commit()
        conn.close()
        return len(expired)
