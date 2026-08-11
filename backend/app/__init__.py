import os

from flask import Flask
from dotenv import load_dotenv

from config.config import Config
from app.extensions import db


load_dotenv()


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    from models.user import User
    from models.phobia import Phobia
    from models.session import Session
    from models.heart_rate import HeartRate

    with app.app_context():
        db.create_all()

    from routes.health import health_bp
    from routes.sessions import sessions_bp
    from routes.heart_rates import heart_rates_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(heart_rates_bp)

    return app