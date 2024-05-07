import pytest
import requests
from flask import url_for, session, template_rendered, get_flashed_messages
from contextlib import contextmanager
from unittest.mock import patch, Mock
from app import create_app

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


@pytest.fixture
def app():
    app = create_app('config.TestConfig')  
    return app

@pytest.fixture
def client(app):
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def logged_in_client(client):
    with client:
        with client.session_transaction() as sess:
            sess['organization_id'] = 1  
            sess['organization_name'] = "TestOrg"
        yield client

@pytest.fixture
def mock_response(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mock_post(*args, **kwargs):
        if '/register' in args[0]:
            return MockResponse({"organization_id": 1, "organization_name": "TestOrg"}, 201)
        return MockResponse(None, 404)

    monkeypatch.setattr("requests.post", mock_post)

@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

@pytest.fixture
def logged_in_client(client):
    """A test client with a session mimicking a logged-in state."""
    with client.session_transaction() as sess:
        sess['organization_id'] = 1
        sess['organization_name'] = 'Test Organization'
    return client

# Register Tests
def test_register(client):
    url = url_for('register')
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'organization_id': 1, 'organization_name': 'TestOrg'}
        response = client.post(url, data={'name': 'testuser', 'password': 'password'})
        assert response.status_code == 302
        assert session['organization_id'] == 1

def test_failed_register(client):
    url = url_for('register')
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'error': 'Invalid data'}
        response = client.post(url, data={'name': '', 'password': 'password'})
        assert response.status_code == 200
        assert b"Error: Invalid data" in response.data

# Login Tests
def test_login(client):
    url = url_for('login')
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'organization_id': 1, 'organization_name': 'TestOrg'}
        response = client.post(url, data={'name': 'testuser', 'password': 'password'})
        assert response.status_code == 302
        assert session['organization_id'] == 1

def test_failed_login(client):
    url = url_for('login')
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {'error': 'Invalid credentials'}
        response = client.post(url, data={'name': 'testuser', 'password': 'wrongpassword'})
        assert response.status_code == 200
        assert b"Error: Invalid credentials" in response.data

# Logout Test
def test_logout(logged_in_client):
    url = url_for('logout')
    response = logged_in_client.get(url)
    assert 'organization_id' not in session
    assert response.status_code == 302

# Device addition test
def test_add_device(logged_in_client):
    url = url_for('add_device')
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        response = logged_in_client.post(url, data={'nickname': 'Device1', 'passkey': '12345'})
        assert response.status_code == 302

# Test adding user
def test_add_user(logged_in_client):
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'user_id': 123}
        response = logged_in_client.post(url_for('add_user_page'), data={
            'user_name': 'John Doe',
            'phone_number': '1234567890',
            'bpm_upper_threshold': '120',
            'bpm_lower_threshold': '60',
            'temperature_upper_threshold': '37.5',
            'temperature_lower_threshold': '35.5',
            'device_id': '1'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'User added successfully!' in response.get_data(as_text=True)


def test_add_user_failure(logged_in_client):
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'error': 'Failed to add user.'}
        response = logged_in_client.post(url_for('add_user_page'), data={
            'user_name': 'Jane Doe',
            'phone_number': '0987654321',
            'bpm_upper_threshold': '100',
            'bpm_lower_threshold': '50',
            'temperature_upper_threshold': '38',
            'temperature_lower_threshold': '34'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Failed to add user.' in response.get_data(as_text=True)


# Test user detail updates and device management
def test_update_user_details(logged_in_client):
    user_id = 123
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        response = logged_in_client.post(url_for('user_page', user_id=user_id), data={
            'username': 'Updated Name',
            'phone_number': '9876543210',
            'bpm_upper_threshold': '110',
            'bpm_lower_threshold': '70',
            'temperature_upper_threshold': '36.5',
            'temperature_lower_threshold': '35.0',
            'update_details': 'true'
        }, follow_redirects=True)
        assert response.status_code == 200  # Adjusted to expect 200 instead of 302

# Test user deletion
def test_delete_user(logged_in_client):
    user_id = 123
    with patch('requests.delete') as mock_delete:
        mock_delete.return_value.status_code = 200
        response = logged_in_client.post(url_for('user_page', user_id=user_id), data={
            'delete_user': 'true'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'User deleted successfully' in response.get_data(as_text=True)


# Test handling device assignment
def test_assign_device_to_user(logged_in_client):
    user_id = 123
    device_id = 1
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        response = logged_in_client.post(url_for('user_page', user_id=user_id), data={
            'device_id': device_id,
            'assign_device': 'true'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Device assigned successfully' in response.get_data(as_text=True)


# Test live data stream
def test_data_stream(logged_in_client):
    response = logged_in_client.get(url_for('data_stream'))
    assert response.status_code == 200
    assert response.content_type == 'text/event-stream'

# Test organization details page
def test_organization_details(logged_in_client):
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'users': [], 'devices': []}
        response = logged_in_client.get(url_for('organization_details'))
        assert response.status_code == 200
        assert 'Hi,' in response.get_data(as_text=True) 

def test_index_network_failure(logged_in_client, monkeypatch):
    def mock_get(*args, **kwargs):
        raise requests.RequestException("Network error")
    monkeypatch.setattr("requests.get", mock_get)

    response = logged_in_client.get(url_for('index'))
    assert response.status_code == 500
    assert 'Network error' in response.get_data(as_text=True)

def test_successful_logout(logged_in_client):
    response = logged_in_client.get(url_for('logout'), follow_redirects=True)
    assert 'organization_id' not in session
    assert response.status_code == 200
    assert 'Login' in response.get_data(as_text=True) 


def test_organization_details_content_display(logged_in_client):
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'users': [{'id': 1, 'username': 'User1'}],
            'devices': [{'id': 1, 'mac_address': 'Device1'}]
        }
        response = logged_in_client.get(url_for('organization_details'))
        assert response.status_code == 200
        assert '1' in response.get_data(as_text=True)
        assert '1' in response.get_data(as_text=True)

def test_device_assignment_failure(logged_in_client):
    user_id = 123
    device_id = 1
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'error': 'Assignment failed'}
        response = logged_in_client.post(url_for('user_page', user_id=user_id), data={
            'device_id': device_id,
            'assign_device': 'true'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'Failed to assign new device' in response.get_data(as_text=True)

def test_index_redirect_when_not_logged_in(client):
    response = client.get(url_for('index'), follow_redirects=False)
    assert response.status_code == 302
    assert url_for('register_login_page') in response.headers['Location']

def test_index_with_no_users(logged_in_client, monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse(None, 404)  # Simulates an unsuccessful API call

    monkeypatch.setattr("requests.get", mock_get)
    response = logged_in_client.get(url_for('index'))
    assert response.status_code == 200
    assert 'Add New User' in response.get_data(as_text=True)

def test_add_device_page_authenticated(logged_in_client):

    response = logged_in_client.get(url_for('add_device_page'))
    assert response.status_code == 200
    assert 'Test Organization' in response.get_data(as_text=True) 

def test_add_device_page_unauthenticated(client):
    response = client.get(url_for('add_device_page'), follow_redirects=False)
    assert response.status_code == 302
    assert url_for('register_login_page') in response.headers['Location']

def test_add_device_failure(logged_in_client):
    # Set up data to send in the form
    device_data = {
        'nickname': 'NewDevice',
        'passkey': '12345'
    }
    
    # Mock the POST request to simulate API failure
    with patch('requests.post') as mock_post:
        # Configure the mock to return a failure status code
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'error': 'Failed to add device'}
        
        # Make a POST request to the add-device route
        response = logged_in_client.post(url_for('add_device'), data=device_data, follow_redirects=True)
        
        # Assert that the response indicates a redirection (back to the index or relevant page)
        assert response.status_code == 200
        
        # Check for the appropriate flash message
        flashed_messages = [message for category, message in get_flashed_messages(with_categories=True)]
        assert 'Failed to add device' in flashed_messages

def test_submit_user_details_unauthenticated(client):
    response = client.get(url_for('submit_user_details'), follow_redirects=False)
    assert response.status_code == 302
    assert url_for('register_login_page') in response.headers['Location']

def test_submit_user_details_success(logged_in_client):
    devices_data = {
        "devices": [
            {"id": 1, "nickname": "Device1", "is_assigned_to_user": False},
            {"id": 2, "nickname": "Device2", "is_assigned_to_user": True}  # This should be filtered out
        ]
    }
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = devices_data
        response = logged_in_client.get(url_for('submit_user_details'))
        assert response.status_code == 200
        assert 'Device1' in response.get_data(as_text=True)
        assert 'Device2' not in response.get_data(as_text=True)  # Ensure filtered devices are not displayed

def test_submit_user_details_failure(logged_in_client):
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 400
        mock_get.return_value.json.return_value = {"error": "Failed to fetch devices"}
        response = logged_in_client.get(url_for('submit_user_details'), follow_redirects=True)
        assert response.status_code == 200
        assert 'Failed to fetch devices. Please try again.' in get_flashed_messages()

def test_about_us_unauthenticated(client):
    response = client.get(url_for('organization_details'), follow_redirects=False)
    assert response.status_code == 302
    assert url_for('register_login_page') in response.headers['Location']

def test_about_us_missing_org_id(client):
    with client.session_transaction() as sess:
        sess['organization_name'] = 'TestOrg'  # No 'organization_id'
    response = client.get(url_for('organization_details'))
    assert response.status_code == 302
    assert url_for('register_login_page') in response.headers['Location']
    assert 'Organization ID not found. Please log in.' in get_flashed_messages()

# def test_stop_publishing_success():
#     with patch('requests.post') as mock_post:
#         mock_post.return_value = Mock(status_code=200)
#         assert stop_publishing_data_to_device('192.168.1.1') is True

# def test_stop_publishing_failure():
#     with patch('requests.post') as mock_post:
#         mock_post.return_value = Mock(status_code=400)
#         assert stop_publishing_data_to_device('192.168.1.1') is False


# def test_stop_publishing_exception():
#     with patch('requests.post') as mock_post:
#         mock_post.side_effect = requests.exceptions.RequestException("Network error")
#         assert stop_publishing_data_to_device('192.168.1.1') is False


