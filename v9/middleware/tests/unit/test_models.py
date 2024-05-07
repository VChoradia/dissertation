# tests/unit/test_models.py
import pytest
from app.models import Organization, Device, User, DeviceData
from sqlalchemy.exc import IntegrityError

def test_new_organization(test_db):
    """Test creating a new organization."""
    organization = Organization(name="Test Org", password_hash="hashed_pw")
    test_db.session.add(organization)
    test_db.session.commit()
    assert organization in test_db.session

def test_organization_password_setter(test_db):
    organization = Organization(name="Test Org")
    organization.set_password("test123")
    assert organization.password_hash is not None
    assert organization.check_password("test123") is True

def test_organization_password_check(test_db):
    organization = Organization(name="Test Org")
    organization.set_password("test123")
    assert organization.check_password("test123") is True
    assert organization.check_password("wrongpassword") is False

def test_new_device(test_db):
    device = Device(mac_address="00:1B:44:11:3A:B7", ip_address="192.168.1.1", nickname="Test Device", passkey="12345")
    test_db.session.add(device)
    test_db.session.commit()
    assert device in test_db.session

@pytest.fixture(autouse=True)
def session_rollback(test_db):
    yield
    test_db.session.rollback()

def test_device_unique_constraint(test_db):
    device1 = Device(mac_address="00:1B:44:11:3A:C7", ip_address="192.168.1.1", nickname="Device 1", passkey="12345")
    test_db.session.add(device1)
    test_db.session.commit()  # Ensure this commit is outside the pytest.raises block

    device2 = Device(mac_address="00:1B:44:11:3A:C7", ip_address="192.168.1.2", nickname="Device 2", passkey="67890")
    test_db.session.add(device2)
    with pytest.raises(IntegrityError):
        test_db.session.commit()  # This should fail

    test_db.session.rollback()  # Cleanup the session.


def test_new_user(test_db):
    # Assuming that we must have an organization_id, create an organization first
    organization = Organization(name="Test Organization", password_hash="hashed_pw")
    test_db.session.add(organization)
    test_db.session.commit()

    user = User(username="user1", phone_number="1234567890", organization_id=organization.id)
    test_db.session.add(user)
    test_db.session.commit()

    # Cleanup
    test_db.session.delete(user)
    test_db.session.delete(organization)
    test_db.session.commit()

    

def test_user_phone_number(test_db):
    # Assuming that we must have an organization_id, create an organization first
    organization = Organization(name="Test Organization", password_hash="hashed_pw")
    test_db.session.add(organization)
    test_db.session.commit()

    user = User(username="user2", phone_number="1234567890", organization_id=organization.id)
    test_db.session.add(user)
    test_db.session.commit()

    test_db.session.delete(user)
    test_db.session.delete(organization)
    test_db.session.commit()


def test_device_data(test_db):
    device_data = DeviceData(device_id=1, bpm=72.5, temperature=36.6)
    test_db.session.add(device_data)
    test_db.session.commit()