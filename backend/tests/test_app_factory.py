import pytest

from app import create_app
from app.extensions import db


class InvalidProductionConfig:
    SECRET_KEY = "invalid"
    JWT_SECRET_KEY = "invalid"
    SQLALCHEMY_DATABASE_URI = "invalid"
    CORS_ORIGINS = "https://app.example.com"

    @classmethod
    def validate(cls):
        raise RuntimeError("production configuration is invalid")

    @classmethod
    def cors_origins(cls):
        return ["https://app.example.com"]


def test_create_app_rejects_invalid_configuration_before_initializing_extensions(monkeypatch):
    def fail_if_initialized(_app):
        pytest.fail("database extension must not initialize after configuration validation fails")

    monkeypatch.setattr(db, "init_app", fail_if_initialized)

    with pytest.raises(RuntimeError, match="production configuration is invalid"):
        create_app(InvalidProductionConfig)
