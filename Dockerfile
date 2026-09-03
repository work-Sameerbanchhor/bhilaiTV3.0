# ==============================================================================
# BHILAI_TV // Production Dockerfile for Google Cloud Run
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Install essential system dependencies and CA certificates for TLS
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for secure container execution
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser ${APP_HOME}

# Copy application source code
COPY app/ ./app/

# Switch to non-root user
USER appuser

# Expose default Cloud Run container port
EXPOSE 8080

# Launch application with Uvicorn listening on the dynamic $PORT injected by Cloud Run
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2
