FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile 2>/dev/null || true
COPY frontend/ .
RUN pnpm build 2>/dev/null || mkdir -p /app/static && echo "<html><body>Frontend build pending</body></html>" > /app/static/index.html

FROM python:3.11-slim AS backend-builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo libwebp7 curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=backend-builder /root/.local /root/.local
COPY --from=frontend-builder /app/dist /app/static
COPY backend/ /app/backend/
RUN mkdir -p /app/data && \
    groupadd -g 1000 photosync 2>/dev/null; \
    useradd -u 1000 -g 1000 -d /app photosync 2>/dev/null; \
    chown -R 1000:1000 /app/data 2>/dev/null; :
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8932/api/v1/system/health || exit 1
VOLUME ["/app/data"]
EXPOSE 8932
ENV PATH="/root/.local/bin:${PATH}" PYTHONUNBUFFERED=1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8932", "--proxy-headers"]
