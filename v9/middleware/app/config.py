import os
from .cloudsql import connect_unix_socket

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
     

class DevelopmentConfig(Config):
    DEBUG = True
    ENGINE = connect_unix_socket() 
    SQLALCHEMY_DATABASE_URI = ENGINE.url
    # Additional development-specific settings

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory SQLite for tests

