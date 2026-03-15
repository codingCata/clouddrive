import pytest
import io

class TestRegister:
    def test_register_success(self, client):
        response = client.post('/api/register', json={
            'username': 'newuser',
            'password': 'password123'
        })
        assert response.status_code == 201
        assert 'user_id' in response.json
        assert response.json['message'] == 'User registered successfully'

    def test_register_duplicate_username(self, client):
        client.post('/api/register', json={
            'username': 'duplicate',
            'password': 'password'
        })
        response = client.post('/api/register', json={
            'username': 'duplicate',
            'password': 'password'
        })
        assert response.status_code == 400
        assert 'error' in response.json

    def test_register_empty_username(self, client):
        response = client.post('/api/register', json={
            'username': '',
            'password': 'password123'
        })
        assert response.status_code == 400

    def test_register_empty_password(self, client):
        response = client.post('/api/register', json={
            'username': 'validuser',
            'password': ''
        })
        assert response.status_code == 400

    def test_register_missing_fields(self, client):
        response = client.post('/api/register', json={
            'username': 'validuser'
        })
        assert response.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        client.post('/api/register', json={
            'username': 'loginuser',
            'password': 'password123'
        })
        response = client.post('/api/login', json={
            'username': 'loginuser',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert response.json['message'] == 'Login successful'

    def test_login_wrong_password(self, client):
        client.post('/api/register', json={
            'username': 'wrongpass',
            'password': 'correct'
        })
        response = client.post('/api/login', json={
            'username': 'wrongpass',
            'password': 'incorrect'
        })
        assert response.status_code == 401
        assert 'error' in response.json

    def test_login_nonexistent_user(self, client):
        response = client.post('/api/login', json={
            'username': 'nonexistent',
            'password': 'password'
        })
        assert response.status_code == 401


class TestLogout:
    def test_logout_success(self, user1):
        response = user1.post('/api/logout')
        assert response.status_code == 200

    def test_logout_without_login(self, client):
        response = client.post('/api/logout')
        assert response.status_code == 200


class TestChangePassword:
    def test_change_password_success(self, user1):
        response = user1.post('/api/change-password', json={
            'current_password': 'password1',
            'new_password': 'newpassword'
        })
        assert response.status_code == 200

    def test_change_password_wrong_current(self, user1):
        response = user1.post('/api/change-password', json={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword'
        })
        assert response.status_code == 400

    def test_change_password_without_login(self, client):
        response = client.post('/api/change-password', json={
            'current_password': 'password',
            'new_password': 'newpassword'
        })
        assert response.status_code == 401


class TestGetUser:
    def test_get_user_info(self, user1):
        response = user1.get('/api/user')
        assert response.status_code == 200
        assert response.json['username'] == 'user1'

    def test_get_user_unauthorized(self, client):
        response = client.get('/api/user')
        assert response.status_code == 401
