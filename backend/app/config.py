import os

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
        if cls.APP_ENV == "production":
            if not cls.SECRET_KEY or not cls.SECRET_KEY.strip() or cls.SECRET_KEY == "dev-secret-change-me":
                raise RuntimeError("SECRET_KEY must be set in production")
            if not cls.JWT_SECRET_KEY or not cls.JWT_SECRET_KEY.strip() or cls.JWT_SECRET_KEY == "dev-jwt-secret-change-me":
                raise RuntimeError("JWT_SECRET_KEY must be set in production")
            if not cls.GEMINI_API_KEY or not cls.GEMINI_API_KEY.strip():
                raise RuntimeError("GEMINI_API_KEY must be set in production")
            if not cls.CORS_ORIGINS.strip():
                raise RuntimeError("CORS_ORIGINS must be set in production")
            if "*" in cls.cors_origins():
                raise RuntimeError("CORS_ORIGINS must not contain wildcard origins in production")
            if cls.SQLALCHEMY_DATABASE_URI == "postgresql+psycopg://postgres:password@localhost:5432/carebridge_db":
                raise RuntimeError("DATABASE_URL must be set in production")
        if cls.JWT_ACCESS_TOKEN_EXPIRES <= 0:
            raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRES must be greater than zero")
        if cls.AI_RATE_LIMIT <= 0:
            raise RuntimeError("AI_RATE_LIMIT must be greater than zero")
        if cls.AI_RATE_WINDOW_SECONDS <= 0:
            raise RuntimeError("AI_RATE_WINDOW_SECONDS must be greater than zero")

    @classmethod
    def cors_origins(cls):
        return [origin.strip() for origin in cls.CORS_ORIGINS.split(",") if origin.strip()]
