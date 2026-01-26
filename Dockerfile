# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Docker Image
# ═══════════════════════════════════════════════════════════════════════════════
# Multi-stage build for optimized production image
# ═══════════════════════════════════════════════════════════════════════════════

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim

LABEL maintainer="RepoGraph AI Team"
LABEL description="Enterprise-Grade Intelligent Document Processing & RAG System"
LABEL version="1.0.0"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY config/ ./config/
COPY interfaces/ ./interfaces/
COPY models/ ./models/
COPY processors/ ./processors/
COPY services/ ./services/
COPY workflows/ ./workflows/
COPY utils/ ./utils/
COPY main.py .
COPY query.py .
COPY api.py .

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Default data directory
ENV DATA_DIRECTORY=/app/data

# Expose port for API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["python", "main.py", "index"]
