# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_session import Session
import os

API_BASE_URL = 'http://localhost:5500'

def create_app(config_class='config.Config'):
    # Create the Flask application
    app = Flask(__name__, template_folder=os.path.abspath('./templates'), static_folder=os.path.abspath('./static'))

    # Apply CORS and Session configurations
    CORS(app)
    app.config.from_object(config_class)
    Session(app)

    from app.routes import init_routes  # Import the initialization function from routes
    init_routes(app)  # Initialize routes with the app object

    return app



