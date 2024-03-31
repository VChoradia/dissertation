# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, template_folder=os.path.abspath('./templates'))
CORS(app)
app.config.from_object('config.Config')

db = SQLAlchemy(app)

from app import models, routes
