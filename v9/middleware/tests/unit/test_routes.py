import pytest
from app import create_app, db
from app.models import Organization, User, Device, DeviceData
import requests
from flask import json
from unittest.mock import patch
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError


# Setup and teardown for the database
@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()  # Make sure to define a testing config

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # This is where the testing happens!

    ctx.pop()

@pytest.fixture(scope='module')
def init_database():
    # Create the database and the database table
    db.create_all()

    # Insert user data
    user1 = User(username='testuser1', phone_number='1234567890', organization_id=1)
    user2 = User(username='testuser2', phone_number='0987654321', organization_id=1)
    db.session.add(user1)
    db.session.add(user2)

    # Commit the changes for the users
    db.session.commit()

    yield db  # This is where the testing happens!

    db.drop_all()

# Tests
def test_register_organization(test_client, init_database):
    # Ensure that you can register an organization
    response = test_client.post('/register', data=json.dumps({'name': 'New Org', 'password': 'newpassword'}),
                                 content_type='application/json')
    assert response.status_code == 201
    assert 'Organization registered successfully' in response.get_data(as_text=True)

def test_login_organization(test_client, init_database):
    # Test login functionality
    response = test_client.post('/login', data=json.dumps({'name': 'New Org', 'password': 'newpassword'}),
                                 content_type='application/json')
    assert response.status_code == 200
    assert 'Login successful' in response.get_data(as_text=True)

def test_add_new_user(test_client, init_database):
    # Test adding a new user
    response = test_client.post('/add-new-user', data=json.dumps({
        'organization_id': 1,
        'username': 'newuser',
        'phone_number': '1112223333'
    }), content_type='application/json')
    assert response.status_code == 201
    assert 'User added successfully' in response.get_data(as_text=True)

def test_add_new_device(test_client, init_database):
    # Test adding a new device
    response = test_client.post('/add-new-device', data=json.dumps({
        'mac_address': '00:1A:22:33:44:55',
        'ip_address': '192.168.1.100',
        'nickname': 'Test Device',
        'passkey': 'passkey123'
    }), content_type='application/json')
    assert response.status_code == 201
    assert 'Device added or updated successfully' in response.get_data(as_text=True)

@pytest.mark.parametrize("status_code, expected_status, expected_message", [
    (200, 200, 'User details sent to the device successfully'),
    (400, 500, 'Failed to send user details to the device'),  # Simulate a failed response
    (500, 500, 'Failed to send user details to the device')
])
def test_assign_device_to_user(test_client, init_database, status_code, expected_status, expected_message):
    # Setup mock for requests.post
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = status_code
        if status_code != 200:
            mock_post.return_value.raise_for_status.side_effect = RequestException("Failed to send")

        # Test assigning a device to a user
        response = test_client.post('/assign-device-to-user', data=json.dumps({
            'user_id': 1,
            'device_id': 1
        }), content_type='application/json')

        assert response.status_code == expected_status
        assert expected_message in response.get_data(as_text=True)

        # Optional: Assert that the requests.post was called with the expected URL and data
        if status_code == 200:
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert 'http://192.168.1.1:80/receive-user-details' in args[0]
            assert 'username' in json.loads(kwargs['data'])

def test_add_or_update_device(test_client, init_database):
    # Add a new device
    device_data = {
        'mac_address': '00:1A:22:7B:88:3D',
        'ip_address': '192.168.0.1',
        'passkey': 'pass123',
        'nickname': 'DeviceOne'
    }
    response = test_client.post('/add-new-device', data=json.dumps(device_data), content_type='application/json')
    assert response.status_code == 201
    assert 'Device added or updated successfully' in response.get_data(as_text=True)

    # Update the existing device
    device_data['ip_address'] = '192.168.0.2'
    response = test_client.post('/add-new-device', data=json.dumps(device_data), content_type='application/json')
    assert response.status_code == 201
    assert 'Device added or updated successfully' in response.get_data(as_text=True)

def test_unassign_device(test_client, init_database):
    # Setup: Assume device and user exist and are linked
    device_id = 1
    user_id = 1
    
    with patch('requests.post') as mock_post:
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = test_client.post(f'/unassign-device/{device_id}/{user_id}')
        assert response.status_code == 200
        assert 'Device unassigned successfully' in response.get_data(as_text=True)

def test_register_organization_missing_fields(test_client, init_database):
    # Missing 'name'
    response = test_client.post('/register', data=json.dumps({'password': 'newpassword'}),
                                 content_type='application/json')
    assert response.status_code == 400
    assert 'Name and password are required' in response.get_data(as_text=True)

    # Missing 'password'
    response = test_client.post('/register', data=json.dumps({'name': 'New Org'}),
                                 content_type='application/json')
    assert response.status_code == 400
    assert 'Name and password are required' in response.get_data(as_text=True)

    # Both missing
    response = test_client.post('/register', data=json.dumps({}),
                                 content_type='application/json')
    assert response.status_code == 400
    assert 'Name and password are required' in response.get_data(as_text=True)

def test_register_existing_organization(test_client, init_database):
    organization = Organization(name='Existing Org', password_hash='hashed_pw')
    db.session.add(organization)
    db.session.commit()

    # Now test registration of the same organization
    response = test_client.post('/register', data=json.dumps({'name': 'Existing Org', 'password': 'newpassword'}),
                                content_type='application/json')
    assert response.status_code == 400
    assert 'Organization already exists' in response.get_data(as_text=True)

def test_add_user_db_commit_fail(test_client, init_database):
    with patch.object(db.session, 'commit', side_effect=Exception("DB Commit Fail")):
        response = test_client.post('/add-new-user', data=json.dumps({
            'organization_id': 1,
            'username': 'anotheruser',
            'phone_number': '1234567890'
        }), content_type='application/json')
        assert response.status_code == 500
        assert 'DB Commit Fail' in response.get_data(as_text=True)

def test_associate_device_not_found(test_client, init_database):
    response = test_client.post('/associate-device', data=json.dumps({
        'nickname': 'NonExistent',
        'passkey': 'None',
        'organization_id': 1
    }), content_type='application/json')
    assert response.status_code == 404
    assert 'Device not found with the provided nickname and passkey' in response.get_data(as_text=True)

def test_delete_nonexistent_user(test_client, init_database):
    response = test_client.delete('/delete-user/999')  # Assuming ID 999 does not exist
    assert response.status_code == 404
    assert 'User not found' in response.get_data(as_text=True)

def test_delete_nonexistent_device(test_client, init_database):
    response = test_client.delete('/delete-device/999')  # Assuming ID 999 does not exist
    assert response.status_code == 404
    assert 'Device not found' in response.get_data(as_text=True)

def test_save_device_data_missing_fields(test_client, init_database):
    # Missing 'bpm' and 'temperature'
    data = {'device_id': 1}
    response = test_client.post('/save-device-data', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400
    assert 'Missing data' in response.get_data(as_text=True)

def test_save_device_data_db_error(test_client, init_database):
    with patch.object(db.session, 'commit', side_effect=Exception("DB Insert Fail")):
        data = {'device_id': 1, 'bpm': 70.5, 'temp': 98.6}
        response = test_client.post('/save-device-data', data=json.dumps(data), content_type='application/json')
        assert response.status_code == 500
        assert 'DB Insert Fail' in response.get_data(as_text=True)

def test_update_user_details_with_device(test_client, init_database):
    # Setup user and device
    # Ensure the organization is setup and linked
    organization = Organization(name='Org for User', password_hash='hashed_pw')
    db.session.add(organization)
    db.session.commit()

    user = User(username='testuser', phone_number='1234567890', organization_id=organization.id)
    db.session.add(user)
    db.session.commit()


    # Mock requests.post to simulate device response
    with patch('requests.post') as mock_post:
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Attempt to update user details
        user_update = {'username': 'updateduser', 'user_id': 1}
        response = test_client.post('/update-user-details', data=json.dumps(user_update), content_type='application/json')
        assert response.status_code == 200
        assert 'User details updated successfully and sent to the device' in response.get_data(as_text=True)
        mock_post.assert_called_with(f"http://192.168.0.2:80/receive-user-details", json=any, timeout=5)

def test_add_user_duplicate_username_within_organization(test_client, init_database):
    # At the start of each test or in a fixture
    db.session.rollback()

    organization = Organization(name='Org for User Testing', password_hash='hashed_pw')
    db.session.add(organization)
    db.session.commit()

    # Now proceed with the test
    user = User(username='existinguser',phone_number= '9876543210', organization_id=organization.id)
    db.session.add(user)
    db.session.commit()

    response = test_client.post('/add-new-user', data=json.dumps({
        'organization_id': organization.id,
        'username': 'existinguser',  # Same username as added above
        'phone_number': '9876543210'
    }), content_type='application/json')
    assert response.status_code == 409
    assert 'A user with this username already exists within the organization' in response.get_data(as_text=True)

# Test registering an organization with an empty name
def test_register_organization_empty_name(test_client, init_database):
    response = test_client.post('/register', data=json.dumps({'name': '', 'password': 'newpassword'}),
                                 content_type='application/json')
    assert response.status_code == 400
    assert 'Name and password are required' in response.get_data(as_text=True)

# Test logging in with incorrect credentials
def test_login_organization_invalid_credentials(test_client, init_database):
    response = test_client.post('/login', data=json.dumps({'name': 'NonExistentOrg', 'password': 'invalidpassword'}),
                                 content_type='application/json')
    assert response.status_code == 401
    assert 'Invalid name or password' in response.get_data(as_text=True)

# Test adding a new user with missing data
def test_add_new_user_missing_data(test_client, init_database):
    response = test_client.post('/add-new-user', data=json.dumps({
        'organization_id': 1,
        'phone_number': '1112223333'
    }), content_type='application/json')
    assert response.status_code == 400
    assert 'Organization ID, username, and phone number are required' in response.get_data(as_text=True)

# Test adding a new device with missing data
def test_add_new_device_missing_data(test_client, init_database):
    response = test_client.post('/add-new-device', data=json.dumps({
        'mac_address': '00:1A:22:33:44:55',
        'ip_address': '192.168.1.100',
        'passkey': 'passkey123'
    }), content_type='application/json')
    assert response.status_code == 201
    assert 'Device added or updated successfully' in response.get_data(as_text=True)

# Test associating a device with an organization with missing data
def test_associate_device_missing_data(test_client, init_database):
    response = test_client.post('/associate-device', data=json.dumps({
        'nickname': 'TestDevice',
        'organization_id': 1
    }), content_type='application/json')
    assert response.status_code == 400
    assert 'Organization ID, nickname, and passkey are required' in response.get_data(as_text=True)

# Test assigning a device to a user with missing data
def test_assign_device_to_user_missing_data(test_client, init_database):
    response = test_client.post('/assign-device-to-user', data=json.dumps({
        'device_id': 1
    }), content_type='application/json')
    assert response.status_code == 400
    assert 'User ID and Device ID are required' in response.get_data(as_text=True)

# Test updating user details with missing data
import requests.exceptions
def test_update_user_details_missing_data(test_client, init_database):
    # Mock the requests.post function to simulate a failure
    with patch('app.routes.requests.post') as mock_post:
        # Set the side effect of the mocked function to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException

        # Send a request to update user details with missing data
        response = test_client.post('/update-user-details', data=json.dumps({
            'user_id': 1,
            'username': 'updateduser'
        }), content_type='application/json')

        # Assert that the response indicates a server error
        assert response.status_code == 500
        assert 'Request to device failed' in response.get_data(as_text=True)

# Test saving device data with missing data
def test_save_device_data_missing_data(test_client, init_database):
    response = test_client.post('/save-device-data', data=json.dumps({
        'bpm': 70.5,
        'temp': 98.6
    }), content_type='application/json')
    assert response.status_code == 400
    assert 'Missing data' in response.get_data(as_text=True)

# Test deleting a nonexistent user
def test_delete_nonexistent_user(test_client, init_database):
    response = test_client.delete('/delete-user/999')  # Assuming ID 999 does not exist
    assert response.status_code == 404
    assert 'User not found' in response.get_data(as_text=True)

