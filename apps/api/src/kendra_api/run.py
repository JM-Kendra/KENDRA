"""Start Uvicorn from the validated Kendra settings."""

import uvicorn

from kendra_api.config import Settings


def main() -> None:
    # Required secrets are supplied by BaseSettings from the runtime environment.
    settings = Settings()  # type: ignore[call-arg]
    uvicorn.run(
        "kendra_api.asgi:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
