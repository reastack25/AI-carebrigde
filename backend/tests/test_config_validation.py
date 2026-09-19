import pytest

from app.config import Config, _read_int_env


@pytest.mark.parametrize(
    ("attribute", "value", "message"),
    [
        ("AI_RATE_LIMIT", 0, "AI_RATE_LIMIT must be greater than zero"),
        ("AI_RATE_LIMIT", -1, "AI_RATE_LIMIT must be greater than zero"),
        ("AI_RATE_WINDOW_SECONDS", 0, "AI_RATE_WINDOW_SECONDS must be greater than zero"),
        ("AI_RATE_WINDOW_SECONDS", -1, "AI_RATE_WINDOW_SECONDS must be greater than zero"),
        ("JWT_ACCESS_TOKEN_EXPIRES", 0, "JWT_ACCESS_TOKEN_EXPIRES must be greater than zero"),
        ("JWT_ACCESS_TOKEN_EXPIRES", -1, "JWT_ACCESS_TOKEN_EXPIRES must be greater than zero"),
    ],
)
def test_validate_rejects_non_positive_numeric_settings(monkeypatch, attribute, value, message):
    monkeypatch.setattr(Config, attribute, value)

    with pytest.raises(RuntimeError, match=message):
        Config.validate()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("JWT_ACCESS_TOKEN_EXPIRES", "not-an-integer"),
        ("AI_RATE_LIMIT", "20.requests"),
        ("AI_RATE_WINDOW_SECONDS", ""),
    ],
)
def test_read_int_env_rejects_malformed_values(monkeypatch, name, value):
    monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match=f"{name} must be an integer"):
        _read_int_env(name, 1)


@pytest.mark.parametrize(
    ("attribute", "value", "message"),
    [
        ("APP_ENV", "staging", "APP_ENV must be one of: development, testing, production"),
        ("APP_ENV", "", "APP_ENV must be one of: development, testing, production"),
        ("SECRET_KEY", "dev-secret-change-me", "SECRET_KEY must be set in production"),
        ("SECRET_KEY", "   ", "SECRET_KEY must be set in production"),
        ("JWT_SECRET_KEY", "dev-jwt-secret-change-me", "JWT_SECRET_KEY must be set in production"),
        ("JWT_SECRET_KEY", "   ", "JWT_SECRET_KEY must be set in production"),
        ("GEMINI_API_KEY", None, "GEMINI_API_KEY must be set in production"),
        ("GEMINI_API_KEY", "   ", "GEMINI_API_KEY must be set in production"),
        ("CORS_ORIGINS", "   ", "CORS_ORIGINS must be set in production"),
        ("CORS_ORIGINS", "*", "CORS_ORIGINS must not contain wildcard origins in production"),
        ("CORS_ORIGINS", "https://app.example.com, *", "CORS_ORIGINS must not contain wildcard origins in production"),
        (
            "SQLALCHEMY_DATABASE_URI",
            "postgresql+psycopg://postgres:password@localhost:5432/carebridge_db",
            "DATABASE_URL must be set in production",
        ),
    ],
)
def test_validate_rejects_invalid_production_settings(monkeypatch, attribute, value, message):
    if attribute == "APP_ENV":
        monkeypatch.setattr(Config, attribute, value)
        with pytest.raises(RuntimeError, match=message):
            Config.validate()
        return

    monkeypatch.setattr(Config, "APP_ENV", "production")
    monkeypatch.setattr(Config, "SECRET_KEY", "production-secret")
    monkeypatch.setattr(Config, "JWT_SECRET_KEY", "production-jwt-secret")
    monkeypatch.setattr(Config, "GEMINI_API_KEY", "production-gemini-key")
    monkeypatch.setattr(Config, "CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "postgresql+psycopg://prod:secret@db.example.com:5432/carebridge")
    monkeypatch.setattr(Config, attribute, value)

    with pytest.raises(RuntimeError, match=message):
        Config.validate()


def test_validate_accepts_complete_production_configuration(monkeypatch):
    monkeypatch.setattr(Config, "APP_ENV", "production")
    monkeypatch.setattr(Config, "SECRET_KEY", "production-secret")
    monkeypatch.setattr(Config, "JWT_SECRET_KEY", "production-jwt-secret")
    monkeypatch.setattr(Config, "GEMINI_API_KEY", "production-gemini-key")
    monkeypatch.setattr(Config, "CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "postgresql+psycopg://prod:secret@db.example.com:5432/carebridge")
    monkeypatch.setattr(Config, "JWT_ACCESS_TOKEN_EXPIRES", 3600)
    monkeypatch.setattr(Config, "AI_RATE_LIMIT", 20)
    monkeypatch.setattr(Config, "AI_RATE_WINDOW_SECONDS", 3600)

    Config.validate()
