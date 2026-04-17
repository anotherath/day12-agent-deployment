# ============================================================
# Production Dockerfile — Multi-stage, < 500 MB, non-root
# ============================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Non-root user
RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

# Copy packages from builder
COPY --from=builder /root/.local /home/app/.local

# Copy application
COPY app/ ./app/
COPY agent.py .
COPY tools.py .
COPY system_prompt.txt .
COPY Sale.md .
COPY vinhomes_promotion.md .

RUN chown -R app:app /app

USER app

ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Install uvicorn globally for the app user
RUN pip install --user uvicorn

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
