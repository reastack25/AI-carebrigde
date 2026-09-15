from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt, migrate
from .routes.ai import ai_bp
from .routes.auth import auth_bp
from .routes.clinical import clinical_bp
from .routes.health import health_bp
from .routes.medications import medications_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.validate()

    CORS(app, origins=config_class.cors_origins())
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(medications_bp)
    app.register_blueprint(clinical_bp)

    return app
