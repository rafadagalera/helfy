FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY seeds/ seeds/

ENV PYTHONPATH=/app/src

EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && \
     uv run --no-sync python -m core_api.seed && \
     uv run --no-sync uvicorn core_api.main:app --host 0.0.0.0 --port 8000"]
