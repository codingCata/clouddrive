import pytest
import io

class TestBatchDelete:
    def test_batch_delete_files(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content1'), 'file1.txt')
        })
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content2'), 'file2.txt')
        })
        
        response = user1.post('/api/batch-delete', json={
            'files': ['file1.txt', 'file2.txt'],
            'folders': []
        })
        assert response.status_code == 200
        assert response.json['deleted_files'] == ['file1.txt', 'file2.txt']

    def test_batch_delete_mixed(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content'), 'file.txt')
        })
        user1.post('/api/folders', json={'name': 'folder'})
        
        response = user1.post('/api/batch-delete', json={
            'files': ['file.txt'],
            'folders': []
        })
        assert response.status_code == 200

    def test_batch_delete_nonexistent(self, user1):
        response = user1.post('/api/batch-delete', json={
            'files': ['nonexistent.txt'],
            'folders': []
        })
        assert response.status_code == 200
        assert len(response.json['failed']) == 1

    def test_batch_delete_other_user_files(self, user1, client):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'private'), 'private.txt')
        })
        
        client.post('/api/register', json={'username': 'user2', 'password': 'pass2'})
        with client.session_transaction() as sess:
            sess.clear()
        client.post('/api/login', json={'username': 'user2', 'password': 'pass2'})
        
        response = client.post('/api/batch-delete', json={
            'files': ['private.txt'],
            'folders': []
        })
        assert response.status_code == 200
        assert response.json['failed'][0]['error'] == 'Not found'

    def test_batch_delete_unauthorized(self, client):
        response = client.post('/api/batch-delete', json={
            'files': ['file.txt'],
            'folders': []
        })
        assert response.status_code == 401


class TestBatchDownload:
    def test_batch_download(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content1'), 'file1.txt')
        })
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content2'), 'file2.txt')
        })
        
        response = user1.post('/api/batch-download', json={
            'files': ['file1.txt', 'file2.txt']
        })
        assert response.status_code == 200
        assert response.content_type == 'application/zip'

    def test_batch_download_empty(self, user1):
        response = user1.post('/api/batch-download', json={
            'files': []
        })
        assert response.status_code == 400

    def test_batch_download_other_user_files(self, user1, client):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'private'), 'private.txt')
        })
        
        client.post('/api/register', json={'username': 'user2', 'password': 'pass2'})
        with client.session_transaction() as sess:
            sess.clear()
        client.post('/api/login', json={'username': 'user2', 'password': 'pass2'})
        
        response = client.post('/api/batch-download', json={
            'files': ['private.txt']
        })
        assert response.status_code == 200
        import zipfile
        from io import BytesIO
        zf = zipfile.ZipFile(BytesIO(response.data))
        assert len(zf.namelist()) == 0

    def test_batch_download_unauthorized(self, client):
        response = client.post('/api/batch-download', json={
            'files': ['file.txt']
        })
        assert response.status_code == 401
