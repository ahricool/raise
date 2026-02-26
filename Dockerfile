# ===================================
# 生产环境镜像（多阶段：前端打包 + 后端，代码 COPY 进镜像）
# ===================================
# 使用方式: docker compose up -d  或  docker compose -f docker-compose.yml up -d
# 本文件位于项目根目录，build context 为 .

# ── Stage 1: Build Vue 3 frontend ──────────────────────────────────────────
FROM node:20-slim AS web-builder

WORKDIR /workspace/web

# Install deps first (layer cache friendly)
COPY web/package.json web/package-lock.json ./
RUN npm ci

# Copy source and build → outputs to /workspace/static
COPY web ./
RUN npm run build

# ── Stage 2: Python runtime ────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

WORKDIR /workspace

# Timezone
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# System deps (curl for healthcheck; gcc not needed, all packages ship binary wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps (cached layer)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# Application code
COPY *.py ./
COPY api/ ./api/
COPY data_provider/ ./data_provider/
COPY bot/ ./bot/
COPY src/ ./src/

# Copy built frontend
COPY --from=web-builder /workspace/static ./static/

# Runtime dirs
RUN mkdir -p /workspace/data /workspace/logs /workspace/reports

ENV PYTHONUNBUFFERED=1 \
    LOG_DIR=/workspace/logs \
    DATABASE_PATH=/workspace/data/raise.db \
    WEBUI_HOST=0.0.0.0 \
    API_PORT=8000

EXPOSE 8000

VOLUME ["/workspace/data", "/workspace/logs", "/workspace/reports"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || curl -f http://localhost:8000/health \
    || uv run python -c "import sys; sys.exit(0)"

CMD ["uv", "run", "python", "main.py", "--schedule"]
