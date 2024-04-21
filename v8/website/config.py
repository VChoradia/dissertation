# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'dissertation'
    SESSION_PERMISSION = False
    SESSION_TYPE = 'filesystem'

class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SESSION_TYPE = 'filesystem'  # Keep sessions on the filesystem
    SECRET_KEY = 'test_secret_key'
    SERVER_NAME = 'localhost:5000'  # Example server name
    APPLICATION_ROOT = '/'

