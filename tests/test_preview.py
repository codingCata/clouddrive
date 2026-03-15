import pytest
import io

class TestFilePreview:
    def test_preview_image(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'fake image'), 'test.png')
        })
        
        response = user1.get('/api/preview/test.png')
        assert response.status_code == 200

    def test_preview_text(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'Hello World'), 'test.txt')
        })
        
        response = user1.get('/api/preview/test.txt')
        assert response.status_code == 200

    def test_preview_nonexistent_file(self, user1):
        response = user1.get('/api/preview/nonexistent.txt')
        assert response.status_code == 404

    def test_preview_unsupported_type(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content'), 'test.exe')
        })
        
        response = user1.get('/api/preview/test.exe')
        assert response.status_code == 400

    def test_preview_other_user_file(self, user1, client):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'private'), 'private.txt')
        })
        
        client.post('/api/register', json={'username': 'user2', 'password': 'pass2'})
        with client.session_transaction() as sess:
            sess.clear()
        client.post('/api/login', json={'username': 'user2', 'password': 'pass2'})
        
        response = client.get('/api/preview/private.txt')
        assert response.status_code == 404

    def test_preview_unauthorized(self, client):
        response = client.get('/api/preview/test.txt')
        assert response.status_code == 401
