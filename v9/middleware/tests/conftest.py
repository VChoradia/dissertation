# tests/conftest.py
import pytest
from app import create_app, db
import os
from app.config import TestingConfig

@pytest.fixture(scope='module')
def test_app():
    os.environ['FLASK_ENV'] = 'testing'
    application = create_app()
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()

@pytest.fixture(scope='module')
def test_db(test_app):
    """Setup and teardown of the database for tests."""
    with test_app.app_context():
        yield db
