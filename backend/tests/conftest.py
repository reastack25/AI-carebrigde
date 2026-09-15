import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    APP_ENV = "test"
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = "http://localhost:5173"
    GEMINI_API_KEY = "test-key"
    JWT_ACCESS_TOKEN_EXPIRES = 3600

    @classmethod
    def validate(cls):
        return None

    @classmethod
    def cors_origins(cls):
        return ["http://localhost:5173"]


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
