import pytest
import io

class TestSearch:
    def test_search_with_results(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'document content'), 'myreport.pdf')
        })
        
        response = user1.get('/api/search?q=report')
        assert response.status_code == 200
        assert len(response.json['files']) == 1
        assert response.json['files'][0]['filename'] == 'myreport.pdf'

    def test_search_no_results(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content'), 'file.txt')
        })
        
        response = user1.get('/api/search?q=nonexistent')
        assert response.status_code == 200
        assert response.json['files'] == []

    def test_search_empty_query(self, user1):
        response = user1.get('/api/search?q=')
        assert response.status_code == 200
        assert response.json['files'] == []
        assert response.json['folders'] == []

    def test_search_folder_name(self, user1):
        user1.post('/api/folders', json={'name': 'ProjectDocs'})
        
        response = user1.get('/api/search?q=Project')
        assert response.status_code == 200
        assert len(response.json['folders']) == 1

    def test_search_mixed_results(self, user1):
        user1.post('/api/folders', json={'name': 'SearchTest'})
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content'), 'SearchTest.txt')
        })
        
        response = user1.get('/api/search?q=SearchTest')
        assert response.status_code == 200
        assert len(response.json['folders']) == 1
        assert len(response.json['files']) == 1

    def test_search_case_insensitive(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content'), 'UPPERCASE.txt')
        })
        
        response = user1.get('/api/search?q=uppercase')
        assert response.status_code == 200
        assert len(response.json['files']) == 1

    def test_search_other_user_files(self, client):
        # Create user1 and upload file
        client.post('/api/register', json={'username': 'user1', 'password': 'pass1'})
        client.post('/api/login', json={'username': 'user1', 'password': 'pass1'})
        client.post('/api/upload', data={
            'file': (io.BytesIO(b'private'), 'private.txt')
        })
        
        # Create user2
        client.post('/api/register', json={'username': 'user2', 'password': 'pass2'})
        with client.session_transaction() as sess:
            sess.clear()
        client.post('/api/login', json={'username': 'user2', 'password': 'pass2'})
        
        # User2 searches for user1's file
        response = client.get('/api/search?q=private')
        assert response.status_code == 200
        assert response.json['files'] == []

    def test_search_unauthorized(self, client):
        response = client.get('/api/search?q=test')
        assert response.status_code == 401

    def test_search_partial_match(self, user1):
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content'), 'testing123.txt')
        })
        
        response = user1.get('/api/search?q=test')
        assert response.status_code == 200
        assert len(response.json['files']) == 1
