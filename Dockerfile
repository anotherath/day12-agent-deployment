# ============================================================
# Production Dockerfile — < 500 MB, non-root
# ============================================================

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

# Copy requirements first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY agent.py .
COPY tools.py .
COPY system_prompt.txt .
COPY Sale.md .
COPY vinhomes_promotion.md .

RUN chown -R app:app /app

USER app

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

CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
