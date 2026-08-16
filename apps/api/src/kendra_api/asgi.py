"""Runtime ASGI application constructed from environment-backed settings."""

from kendra_api.main import create_app

app = create_app()
