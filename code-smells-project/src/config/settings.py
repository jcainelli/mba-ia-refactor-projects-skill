import os
from dotenv import load_dotenv

load_dotenv()


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


def _required(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Settings:
    SECRET_KEY = _required("SECRET_KEY")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    DEBUG = _bool(os.environ.get("DEBUG"), default=False)
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))

    _origins = os.environ.get("CORS_ORIGINS", "*")
    CORS_ORIGINS = _origins if _origins == "*" else [o.strip() for o in _origins.split(",") if o.strip()]

    VERSION = "2.0.0"

    SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "admin123")
    SEED_USER_PASSWORD = os.environ.get("SEED_USER_PASSWORD", "123456")

    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")


settings = Settings()
