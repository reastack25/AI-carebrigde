import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _read_int_env(name, default):
    raw_value = os.getenv(name, str(default))
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


class Config:
    APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:password@localhost:5432/carebridge_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    JWT_ACCESS_TOKEN_EXPIRES = _read_int_env("JWT_ACCESS_TOKEN_EXPIRES", 3600)
    AI_RATE_LIMIT = _read_int_env("AI_RATE_LIMIT", 20)
    AI_RATE_WINDOW_SECONDS = _read_int_env("AI_RATE_WINDOW_SECONDS", 3600)

    @classmethod
    def validate(cls):
        if cls.APP_ENV not in {"development", "testing", "production"}:
            raise RuntimeError("APP_ENV must be one of: development, testing, production")

        if cls.APP_ENV == "production":
            if not cls.SECRET_KEY or not cls.SECRET_KEY.strip() or cls.SECRET_KEY == "dev-secret-change-me":
                raise RuntimeError("SECRET_KEY must be set in production")
            if len(cls.SECRET_KEY.strip()) < 32:
                raise RuntimeError("SECRET_KEY must be at least 32 characters in production")
            if not cls.JWT_SECRET_KEY or not cls.JWT_SECRET_KEY.strip() or cls.JWT_SECRET_KEY == "dev-jwt-secret-change-me":
                raise RuntimeError("JWT_SECRET_KEY must be set in production")
            if len(cls.JWT_SECRET_KEY.strip()) < 32:
                raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production")
            if not cls.GEMINI_API_KEY or not cls.GEMINI_API_KEY.strip():
                raise RuntimeError("GEMINI_API_KEY must be set in production")
            if not cls.CORS_ORIGINS.strip():
                raise RuntimeError("CORS_ORIGINS must be set in production")
            if "*" in cls.cors_origins():
                raise RuntimeError("CORS_ORIGINS must not contain wildcard origins in production")
            cls.validate_cors_origins()

            database_uri = cls.SQLALCHEMY_DATABASE_URI.strip()
            if database_uri == "postgresql+psycopg://postgres:password@localhost:5432/carebridge_db":
                raise RuntimeError("DATABASE_URL must be set in production")
            parsed_database_uri = urlparse(database_uri)
            if parsed_database_uri.scheme not in {"postgresql", "postgresql+psycopg"}:
                raise RuntimeError("DATABASE_URL must use PostgreSQL in production")
            if not parsed_database_uri.hostname:
                raise RuntimeError("DATABASE_URL must include a database host in production")

        if cls.JWT_ACCESS_TOKEN_EXPIRES <= 0:
            raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRES must be greater than zero")
        if cls.AI_RATE_LIMIT <= 0:
            raise RuntimeError("AI_RATE_LIMIT must be greater than zero")
        if cls.AI_RATE_WINDOW_SECONDS <= 0:
            raise RuntimeError("AI_RATE_WINDOW_SECONDS must be greater than zero")

    @classmethod
    def cors_origins(cls):
        return [origin.strip() for origin in cls.CORS_ORIGINS.split(",") if origin.strip()]

    @classmethod
    def validate_cors_origins(cls):
        invalid = []
        for origin in cls.cors_origins():
            parsed = urlparse(origin)
            hostname = (parsed.hostname or "").lower()
            try:
                parsed_port = parsed.port
            except ValueError:
                parsed_port = None
                invalid.append(origin)
                continue

            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.params
                or parsed.query
                or parsed.fragment
                or (parsed_port is not None and not 1 <= parsed_port <= 65535)
                or (
                    cls.APP_ENV == "production"
                    and hostname in {"localhost", "127.0.0.1", "::1"}
                )
            ):
                invalid.append(origin)

        if invalid:
            raise RuntimeError(
                "CORS_ORIGINS must contain valid HTTP(S) origins: "
                + ", ".join(invalid)
            )
