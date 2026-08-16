FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade "pip==26.2.1"

COPY pyproject.toml ./
COPY src ./src

FROM base AS test

COPY tests ./tests

RUN python -m pip install --no-cache-dir ".[test]"

CMD ["python", "-m", "pytest", "-q"]

FROM base AS runtime

RUN python -m pip install --no-cache-dir . \
    && groupadd --system kendra \
    && useradd --system --gid kendra --home-dir /nonexistent --shell /usr/sbin/nologin kendra

USER kendra

EXPOSE 8000

CMD ["python", "-m", "kendra_api.run"]
