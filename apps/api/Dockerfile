FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        poppler-utils \
        fonts-dejavu-core \
        tesseract-ocr \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade "pip==26.2.1"

# Docling's local layout models need PyTorch. Use the official CPU wheel index so
# the local ingestion image does not acquire unused CUDA runtime packages.
RUN python -m pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch>=2.2.2,<3" "torchvision>=0,<1"

COPY pyproject.toml ./
COPY src ./src

FROM base AS test

RUN python -m pip install --no-cache-dir ".[test]"

COPY tests ./tests

CMD ["python", "-m", "pytest", "-q"]

FROM base AS runtime

RUN python -m pip install --no-cache-dir . \
    && groupadd --system kendra \
    && useradd --system --gid kendra --home-dir /nonexistent --shell /usr/sbin/nologin kendra

USER kendra

EXPOSE 8000

CMD ["python", "-m", "kendra_api.run"]
