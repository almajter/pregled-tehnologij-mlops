FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# lightgbm needs libgomp
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "--no-sync", "uvicorn", "price_forecaster.api:app", "--host", "0.0.0.0", "--port", "8000"]
