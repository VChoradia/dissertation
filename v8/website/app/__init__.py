# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_session import Session
import os

app = Flask(__name__, template_folder=os.path.abspath('./templates'), static_folder=os.path.abspath('./static'))
CORS(app)
app.config.from_object('config.Config')
Session(app)

API_BASE_URL = 'http://localhost:5500'

from app import routes
