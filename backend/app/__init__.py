from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt, migrate
from .routes.auth import auth_bp
from .routes.health import health_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, origins=app.config["CORS_ORIGINS"].split(","))
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)

    return app
