import pytest
import io

class TestFileUpload:
    def test_upload_file_to_root(self, user1):
        data = {
            'file': (io.BytesIO(b'test content'), 'test.txt')
        }
        response = user1.post('/api/upload', data=data)
        assert response.status_code == 201
        assert response.json['filename'] == 'test.txt'

    def test_upload_file_to_folder(self, user1):
        folder_resp = user1.post('/api/folders', json={'name': 'TestFolder'})
        folder_id = folder_resp.json['folder_id']
        
        data = {
            'file': (io.BytesIO(b'folder content'), 'folder.txt'),
            'folder_id': folder_id
        }
        response = user1.post('/api/upload', data=data)
        assert response.status_code == 201

    def test_upload_file_without_file(self, user1):
        response = user1.post('/api/upload', data={})
        assert response.status_code == 400

    def test_upload_duplicate_filename(self, user1):
        data = {
            'file': (io.BytesIO(b'content1'), 'duplicate.txt')
        }
        user1.post('/api/upload', data=data)
        
        data = {
            'file': (io.BytesIO(b'content2'), 'duplicate.txt')
        }
        response = user1.post('/api/upload', data=data)
        assert response.status_code == 201

    def test_upload_unauthorized(self, client):
        data = {
            'file': (io.BytesIO(b'test'), 'test.txt')
        }
        response = client.post('/api/upload', data=data)
        assert response.status_code == 401


class TestFileList:
    def test_list_empty_files(self, user1):
        response = user1.get('/api/files')
        assert response.status_code == 200
        assert response.json['files'] == []

    def test_list_files_with_content(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'test'), 'file1.txt')
        })
        response = user1.get('/api/files')
        assert response.status_code == 200
        assert len(response.json['files']) == 1

    def test_list_files_in_folder(self, user1):
        folder_resp = user1.post('/api/folders', json={'name': 'Folder'})
        folder_id = folder_resp.json['folder_id']
        
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'folder file'), 'infolder.txt'),
            'folder_id': folder_id
        })
        
        response = user1.get(f'/api/files?folder_id={folder_id}')
        assert response.status_code == 200
        assert len(response.json['files']) == 1

    def test_list_files_root_vs_folder(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'root file'), 'root.txt')
        })
        
        folder_resp = user1.post('/api/folders', json={'name': 'Folder'})
        folder_id = folder_resp.json['folder_id']
        
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'folder file'), 'folder.txt'),
            'folder_id': folder_id
        })
        
        root_response = user1.get('/api/files')
        assert len(root_response.json['files']) == 1

    def test_list_files_unauthorized(self, client):
        response = client.get('/api/files')
        assert response.status_code == 401


class TestFileDownload:
    def test_download_file(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'download content'), 'download.txt')
        })
        
        response = user1.get('/api/download/download.txt')
        assert response.status_code == 200
        assert b'download content' in response.data

    def test_download_nonexistent_file(self, user1):
        response = user1.get('/api/download/nonexistent.txt')
        assert response.status_code == 404

    def test_download_other_user_file(self, client):
        # Create user1 and upload file
        client.post('/api/register', json={'username': 'user1', 'password': 'pass1'})
        client.post('/api/login', json={'username': 'user1', 'password': 'pass1'})
        client.post('/api/upload', data={
            'file': (io.BytesIO(b'user1 file'), 'private.txt')
        })
        
        # Create separate session for user2
        client.post('/api/register', json={'username': 'user2', 'password': 'pass2'})
        # Clear and relogin as user2
        with client.session_transaction() as sess:
            sess.clear()
        client.post('/api/login', json={'username': 'user2', 'password': 'pass2'})
        
        # User2 tries to download user1's file
        response = client.get('/api/download/private.txt')
        assert response.status_code == 404


class TestFileDelete:
    def test_delete_file(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'to delete'), 'delete.txt')
        })
        
        response = user1.delete('/api/delete/delete.txt')
        assert response.status_code == 200

    def test_delete_nonexistent_file(self, user1):
        response = user1.delete('/api/delete/nonexistent.txt')
        assert response.status_code == 404

    def test_delete_other_user_file(self, client):
        # Create user1 and upload file
        client.post('/api/register', json={'username': 'user1', 'password': 'pass1'})
        client.post('/api/login', json={'username': 'user1', 'password': 'pass1'})
        client.post('/api/upload', data={
            'file': (io.BytesIO(b'user1 file'), 'private.txt')
        })
        
        # Create separate session for user2
        client.post('/api/register', json={'username': 'user2', 'password': 'pass2'})
        with client.session_transaction() as sess:
            sess.clear()
        client.post('/api/login', json={'username': 'user2', 'password': 'pass2'})
        
        # User2 tries to delete user1's file
        response = client.delete('/api/delete/private.txt')
        assert response.status_code == 404

    def test_delete_file_unauthorized(self, client):
        response = client.delete('/api/delete/any.txt')
        assert response.status_code == 401
