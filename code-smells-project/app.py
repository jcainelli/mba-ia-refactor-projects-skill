"""Backwards-compatible entrypoint.

Composition root lives in ``src/app.py``. Run via ``python app.py`` or ``python -m src.app``.
"""
from src.app import create_app
from src.config.settings import settings

app = create_app()


if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
