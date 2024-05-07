# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from .cloudsql import connect_unix_socket

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'testing':
        from .config import TestingConfig as Config
        app.config.from_object(Config)
    else:
        from .config import DevelopmentConfig as Config
        app.config.from_object(Config)
        
        

    
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()
    
    from app.routes import init_routes  # Import the initialization function from routes
    init_routes(app)  # Initialize routes with the app object

    return app

