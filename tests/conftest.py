import pytest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'clouddrive'))


@pytest.fixture(scope='function')
def test_db():
    modules_to_remove = [m for m in sys.modules if m.startswith('clouddrive')]
    for mod in modules_to_remove:
        del sys.modules[mod]
    
    test_dir = tempfile.mkdtemp()
    db_path = os.path.join(test_dir, 'test.db')
    storage_dir = os.path.join(test_dir, 'storage')
    os.makedirs(storage_dir, exist_ok=True)
    
    os.environ['DB_PATH'] = db_path
    os.environ['STORAGE_DIR'] = storage_dir
    
    from clouddrive import models
    models.init_db()
    
    from clouddrive import app
    
    yield db_path, storage_dir
    
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def client(test_db):
    from clouddrive import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def user1(client):
    client.post('/api/register', json={
        'username': 'user1',
        'password': 'password1'
    })
    client.post('/api/login', json={
        'username': 'user1',
        'password': 'password1'
    })
    return client


@pytest.fixture
def user2(test_db):
    from clouddrive import app
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        client.post('/api/register', json={
            'username': 'user2',
            'password': 'password2'
        })
        client.post('/api/login', json={
            'username': 'user2',
            'password': 'password2'
        })
        yield client
