# syntax=docker/dockerfile:1

FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY agentic_ssw_rag_frontend/package*.json ./
RUN npm ci

COPY agentic_ssw_rag_frontend/ ./
RUN npm run build


FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    FRONTEND_DIST_DIR=/app/frontend_dist \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY agentic_ssw_rag_backend/pyproject.toml agentic_ssw_rag_backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY agentic_ssw_rag_backend/src ./src
COPY --from=frontend-builder /app/frontend/dist ./frontend_dist

EXPOSE 8010

CMD [".venv/bin/uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8010"]
