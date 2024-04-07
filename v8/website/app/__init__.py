# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os
from flask_migrate import Migrate

app = Flask(__name__, template_folder=os.path.abspath('./templates'), static_folder=os.path.abspath('./static'))
CORS(app)
app.config.from_object('config.Config')
Session(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

API_BASE_URL = 'http://localhost:5500'

from app import models, routes
