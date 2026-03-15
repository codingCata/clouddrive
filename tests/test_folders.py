import pytest
import io

class TestFolderCreate:
    def test_create_folder_success(self, user1):
        response = user1.post('/api/folders', json={
            'name': 'MyFolder'
        })
        assert response.status_code == 201
        assert 'folder_id' in response.json

    def test_create_nested_folder(self, user1):
        parent_resp = user1.post('/api/folders', json={'name': 'Parent'})
        parent_id = parent_resp.json['folder_id']
        
        response = user1.post('/api/folders', json={
            'name': 'Child',
            'parent_id': parent_id
        })
        assert response.status_code == 201

    def test_create_folder_empty_name(self, user1):
        response = user1.post('/api/folders', json={
            'name': ''
        })
        assert response.status_code == 400

    def test_create_folder_unauthorized(self, client):
        response = client.post('/api/folders', json={
            'name': 'TestFolder'
        })
        assert response.status_code == 401


class TestFolderDelete:
    def test_delete_empty_folder(self, user1):
        folder_resp = user1.post('/api/folders', json={'name': 'ToDelete'})
        folder_id = folder_resp.json['folder_id']
        
        response = user1.delete(f'/api/folders/{folder_id}')
        assert response.status_code == 200

    def test_delete_folder_with_files(self, user1):
        folder_resp = user1.post('/api/folders', json={'name': 'WithFiles'})
        folder_id = folder_resp.json['folder_id']
        
        user1.post('/api/upload', data={
            'file': (io.BytesIO(b'content'), 'file.txt'),
            'folder_id': folder_id
        })
        
        response = user1.delete(f'/api/folders/{folder_id}')
        assert response.status_code == 400

    def test_delete_nonexistent_folder(self, user1):
        response = user1.delete('/api/folders/99999')
        assert response.status_code == 404

    def test_delete_other_user_folder(self, client):
        # Create user1 and folder
        client.post('/api/register', json={'username': 'user1', 'password': 'pass1'})
        client.post('/api/login', json={'username': 'user1', 'password': 'pass1'})
        folder_resp = client.post('/api/folders', json={'name': 'Private'})
        folder_id = folder_resp.json['folder_id']
        
        # Create user2
        client.post('/api/register', json={'username': 'user2', 'password': 'pass2'})
        with client.session_transaction() as sess:
            sess.clear()
        client.post('/api/login', json={'username': 'user2', 'password': 'pass2'})
        
        # User2 tries to delete user1's folder
        response = client.delete(f'/api/folders/{folder_id}')
        assert response.status_code == 404

    def test_delete_folder_unauthorized(self, client):
        response = client.delete('/api/folders/1')
        assert response.status_code == 401


class TestFolderList:
    def test_list_empty_folders(self, user1):
        response = user1.get('/api/files')
        assert response.status_code == 200
        assert response.json['folders'] == []

    def test_list_folders_with_content(self, user1):
        user1.post('/api/folders', json={'name': 'Folder1'})
        
        response = user1.get('/api/files')
        assert response.status_code == 200
        assert len(response.json['folders']) == 1

    def test_list_folders_in_folder(self, user1):
        parent_resp = user1.post('/api/folders', json={'name': 'Parent'})
        parent_id = parent_resp.json['folder_id']
        
        user1.post('/api/folders', json={
            'name': 'Child',
            'parent_id': parent_id
        })
        
        response = user1.get(f'/api/files?folder_id={parent_id}')
        assert response.status_code == 200
        assert len(response.json['folders']) == 1

    def test_list_root_vs_nested(self, user1):
        parent_resp = user1.post('/api/folders', json={'name': 'Parent'})
        parent_id = parent_resp.json['folder_id']
        
        user1.post('/api/folders', json={
            'name': 'Child',
            'parent_id': parent_id
        })
        
        root_response = user1.get('/api/files')
        assert len(root_response.json['folders']) == 1
