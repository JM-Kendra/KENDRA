"""Start Uvicorn from the validated Kendra settings."""

import uvicorn

from kendra_api.config import Settings


def main() -> None:
    settings = Settings()
    uvicorn.run(
        "kendra_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
