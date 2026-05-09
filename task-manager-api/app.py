from src.app import app
from src.config.database import db  # noqa: F401  (re-exported for legacy `from app import db`)
from src.config.settings import settings


if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
