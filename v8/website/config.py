# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'dissertation'
    SESSION_PERMISSION = False
    SESSION_TYPE = 'filesystem'
