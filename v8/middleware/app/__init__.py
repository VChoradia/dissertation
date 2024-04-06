# app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from .cloudsql import connect_unix_socket

app = Flask(__name__)
CORS(app)

engine = connect_unix_socket()

app.config['SQLALCHEMY_DATABASE_URI'] = engine.url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SERVER_NAME'] = 'localhost:5500'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def create_app():
    with app.app_context():
        # db.drop_all()
        db.create_all()  # Create database tables for our data models
        from . import routes  # Import routes
    
    return app

from app import models, routes
