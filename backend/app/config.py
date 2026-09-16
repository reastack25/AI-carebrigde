import os

from dotenv import load_dotenv

load_dotenv()


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
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))

    @classmethod
    def validate(cls):
        if cls.APP_ENV == "production":
            if cls.SECRET_KEY == "dev-secret-change-me":
                raise RuntimeError("SECRET_KEY must be set in production")
            if cls.JWT_SECRET_KEY == "dev-jwt-secret-change-me":
                raise RuntimeError("JWT_SECRET_KEY must be set in production")
            if not cls.GEMINI_API_KEY:
                raise RuntimeError("GEMINI_API_KEY must be set in production")
            if not cls.CORS_ORIGINS.strip():
                raise RuntimeError("CORS_ORIGINS must be set in production")

    @classmethod
    def cors_origins(cls):
        return [origin.strip() for origin in cls.CORS_ORIGINS.split(",") if origin.strip()]
