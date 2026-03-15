import sqlite3
import bcrypt
from config import DB_PATH


def get_db():
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
        
        plain_key = api_key[8:]  # Remove 'cd_live_' prefix
        
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
        raw_key = secrets.token_hex(24)  # 48 char random
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
    def get_by_user(user_id, folder_id=None):
        conn = get_db()
        cursor = conn.cursor()
        if folder_id is None:
            cursor.execute('''
                SELECT id, filename, filesize, created_at 
                FROM files 
                WHERE user_id = ? AND folder_id IS NULL
                ORDER BY created_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, filename, filesize, created_at 
                FROM files 
                WHERE user_id = ? AND folder_id = ?
                ORDER BY created_at DESC
            ''', (user_id, folder_id))
        files = cursor.fetchall()
        conn.close()
        return files
    
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
    def delete(user_id, filename):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, filepath FROM files WHERE user_id = ? AND filename = ?',
            (user_id, filename)
        )
        file_record = cursor.fetchone()
        
        if file_record:
            cursor.execute('DELETE FROM files WHERE id = ?', (file_record['id'],))
            conn.commit()
            filepath = file_record['filepath']
        else:
            filepath = None
        
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
            WHERE user_id = ? AND filename LIKE ?
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
    def get_by_user(user_id, parent_id=None):
        conn = get_db()
        cursor = conn.cursor()
        if parent_id is None:
            cursor.execute(
                'SELECT id, name, parent_id, created_at FROM folders WHERE user_id = ? AND parent_id IS NULL ORDER BY name',
                (user_id,)
            )
        else:
            cursor.execute(
                'SELECT id, name, parent_id, created_at FROM folders WHERE user_id = ? AND parent_id = ? ORDER BY name',
                (user_id, parent_id)
            )
        folders = cursor.fetchall()
        conn.close()
        return folders
    
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
    def delete(folder_id, user_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM folders WHERE parent_id = ?', (folder_id,))
        if cursor.fetchall():
            conn.close()
            return False
        
        cursor.execute('SELECT id FROM files WHERE folder_id = ?', (folder_id,))
        if cursor.fetchall():
            conn.close()
            return False
        
        cursor.execute('DELETE FROM folders WHERE id = ? AND user_id = ?', (folder_id, user_id))
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
            WHERE user_id = ? AND name LIKE ?
            ORDER BY name
            LIMIT 20
        ''', (user_id, pattern))
        folders = cursor.fetchall()
        conn.close()
        return folders
