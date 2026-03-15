import pytest
import io

class TestApiKey:
    def test_get_api_key_info_no_key(self, user1):
        response = user1.get('/api/api-key')
        assert response.status_code == 200
        assert response.json['has_key'] == False

    def test_create_api_key(self, user1):
        response = user1.post('/api/api-key')
        assert response.status_code == 201
        assert 'api_key' in response.json
        assert response.json['api_key'] is not None
        assert len(response.json['api_key']) > 0

    def test_create_api_key_already_exists(self, user1):
        user1.post('/api/api-key')
        
        response = user1.post('/api/api-key')
        assert response.status_code == 400
        assert 'already exists' in response.json['error']

    def test_get_api_key_info_with_key(self, user1):
        user1.post('/api/api-key')
        
        response = user1.get('/api/api-key')
        assert response.status_code == 200
        assert response.json['has_key'] == True

    def test_delete_api_key(self, user1):
        user1.post('/api/api-key')
        
        response = user1.delete('/api/api-key')
        assert response.status_code == 200
        
        response = user1.get('/api/api-key')
        assert response.json['has_key'] == False

    def test_delete_api_key_when_not_exists(self, user1):
        response = user1.delete('/api/api-key')
        assert response.status_code == 200

    def test_api_key_unauthorized(self, client):
        response = client.get('/api/api-key')
        assert response.status_code == 401

    def test_create_api_key_unauthorized(self, client):
        response = client.post('/api/api-key')
        assert response.status_code == 401

    def test_delete_api_key_unauthorized(self, client):
        response = client.delete('/api/api-key')
        assert response.status_code == 401


class TestAiDocs:
    def test_ai_docs(self, client):
        response = client.get('/api/ai-docs')
        assert response.status_code == 200
        assert 'name' in response.json
        assert response.json['name'] == 'CloudDrive API'

    def test_ai_docs_authentication_section(self, client):
        response = client.get('/api/ai-docs')
        assert response.status_code == 200
        assert 'authentication' in response.json
        assert 'session' in response.json['authentication']
        assert 'api_key' in response.json['authentication']
