import os

from flask import Flask
from dotenv import load_dotenv
from flasgger import Swagger

from config.config import Config
from app.extensions import db


load_dotenv()


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)
    app.config["SWAGGER"] = {
        "title": "LFAF API",
        "uiversion": 3,
        "openapi": "3.0.3",
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
    }

    Swagger(
        app,
        config={"specs_route": "/dev", "headers": []},
        template={
            "swagger": "2.0",
            "info": {
                "title": "LFAF API",
                "description": "API do projeto LFAF com documentação interativa.",
                "version": "1.0.0",
            },
            "schemes": ["http", "https"],
            "tags": [
                {"name": "Health", "description": "Health checks da aplicação."},
                {"name": "Sessions", "description": "Operações de sessões do usuário."},
                {"name": "Heart Rates", "description": "Recebimento e processamento de batimentos."},
            ],
        },
    )

    db.init_app(app)

    from models.user import User
    from models.phobia import Phobia
    from models.session import Session
    from models.heart_rate import HeartRate
    from models.adaptation_decision import AdaptationDecision

    with app.app_context():
        db.create_all()

    from routes.health import health_bp
    from routes.sessions import sessions_bp
    from routes.heart_rates import heart_rates_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(heart_rates_bp)

    return app