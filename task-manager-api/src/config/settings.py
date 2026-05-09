import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _required(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _bool(name, default="false"):
    return os.environ.get(name, default).lower() in ("1", "true", "yes", "on")


def _int(name, default):
    raw = os.environ.get(name, str(default))
    try:
        return int(raw)
    except ValueError:
        raise RuntimeError(f"Invalid integer for env var {name}: {raw!r}")


class Settings:
    SECRET_KEY = _required("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    DEBUG = _bool("DEBUG")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = _int("PORT", 5000)
    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",")]

    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_EXP_HOURS = _int("JWT_EXP_HOURS", 1)

    SMTP_ENABLED = _bool("SMTP_ENABLED")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = _int("SMTP_PORT", 587)
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")


settings = Settings()
