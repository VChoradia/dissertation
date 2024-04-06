# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate

app = Flask(__name__, template_folder=os.path.abspath('./templates'), static_folder=os.path.abspath('./static'))
CORS(app)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import models, routes
