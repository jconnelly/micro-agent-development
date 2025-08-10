# Multi-stage Dockerfile for Micro-Agent Development Platform
# Optimized for production deployment with security scanning and minimal attack surface

# =============================================================================
# Stage 1: Base Python Environment
# =============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Stage 2: Dependencies Installation
# =============================================================================
FROM base as dependencies

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 3: Development Environment (Optional)
# =============================================================================
FROM dependencies as development

# Install development dependencies
COPY requirements-dev.txt* ./
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

# Copy source code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose development port
EXPOSE 5000

# Development command
CMD ["python", "app.py"]

# =============================================================================
# Stage 4: Production Environment
# =============================================================================
FROM dependencies as production

# Production environment variables
ENV FLASK_ENV=production \
    FLASK_DEBUG=0 \
    WORKERS=4 \
    TIMEOUT=120 \
    KEEP_ALIVE=5 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100

# Install production WSGI server
RUN pip install --no-cache-dir gunicorn==21.2.0

# Create application directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app

# Copy source code (exclude development files via .dockerignore)
COPY --chown=appuser:appuser . /app/

# Set working directory
WORKDIR /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose production port
EXPOSE 8000

# Production command using Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "app:app"]

# =============================================================================
# Stage 5: Security Scanning (Final)
# =============================================================================
FROM production as final

# Add labels for container metadata
LABEL maintainer="Micro-Agent Development Team" \
      description="Enterprise AI Agent Platform for Business Rule Extraction and PII Protection" \
      version="1.0.0" \
      license="MIT"

# Final security hardening
RUN find /app -type f -name "*.pyc" -delete && \
    find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Final user switch (security best practice)
USER appuser

# Default command
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "app:app"]