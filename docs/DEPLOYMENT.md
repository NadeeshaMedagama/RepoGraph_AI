# RepoGraph AI - Deployment Guide

## Overview

This guide covers deploying RepoGraph AI in various environments, from local development to production cloud deployments.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Considerations](#production-considerations)
4. [Monitoring & Observability](#monitoring--observability)
5. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Access to Azure OpenAI
- Access to Pinecone

### Setup Steps

```bash
# 1. Navigate to project directory
cd "/home/nadeeshame/PycharmProjects/RepoGraph AI"

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 6. Verify setup
python test_setup.py

# 7. Run indexing
python main.py index

# 8. Start querying
python query.py interactive
```

### Development Server

For API development, you can run the FastAPI server:

```bash
# Start development server
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# http://localhost:8000/docs
```

---

## Docker Deployment

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Docker Image
# ═══════════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port for API
EXPOSE 8000

# Default command
CMD ["python", "main.py", "index"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  repograph-indexer:
    build: .
    container_name: repograph-indexer
    environment:
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=${AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT}
      - AZURE_OPENAI_CHAT_DEPLOYMENT=${AZURE_OPENAI_CHAT_DEPLOYMENT}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
      - GOOGLE_VISION_API_KEY=${GOOGLE_VISION_API_KEY}
      - DATA_DIRECTORY=/app/data
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data:ro
      - ./logs:/app/logs
    command: ["python", "main.py", "index"]

  repograph-api:
    build: .
    container_name: repograph-api
    environment:
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=${AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT}
      - AZURE_OPENAI_CHAT_DEPLOYMENT=${AZURE_OPENAI_CHAT_DEPLOYMENT}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    command: ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Building and Running

```bash
# Build image
docker build -t repograph-ai:latest .

# Run indexer
docker-compose up repograph-indexer

# Run API server
docker-compose up repograph-api

# Run both
docker-compose up -d
```

---

## Production Considerations

### Security

1. **Secrets Management**
   - Never commit `.env` files
   - Use environment variables or secret managers
   - Rotate API keys regularly

```bash
# Use environment variables in production
export AZURE_OPENAI_API_KEY=$(vault read -field=key secret/azure-openai)
export PINECONE_API_KEY=$(vault read -field=key secret/pinecone)
```

2. **Network Security**
   - Use HTTPS for all API endpoints
   - Restrict network access to required ports
   - Enable firewall rules

3. **Access Control**
   - Implement authentication for API endpoints
   - Use role-based access control
   - Log all access attempts

### Performance

1. **Resource Allocation**
```yaml
# Docker resource limits
services:
  repograph-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

2. **Connection Pooling**
   - The application uses connection pooling for API clients
   - Adjust `MAX_CONCURRENT_TASKS` based on available resources

3. **Caching**
   - Settings are cached with `@lru_cache`
   - Deduplication uses in-memory caching
   - Consider Redis for distributed caching

### Scaling

1. **Horizontal Scaling**
   - API servers can be scaled horizontally
   - Use load balancer for distribution
   - Ensure stateless operation

2. **Vertical Scaling**
   - Increase memory for large document processing
   - More CPU cores for concurrent embedding generation

### High Availability

```yaml
# Kubernetes deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: repograph-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: repograph-api
  template:
    metadata:
      labels:
        app: repograph-api
    spec:
      containers:
      - name: api
        image: repograph-ai:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        envFrom:
        - secretRef:
            name: repograph-secrets
```

---

## Monitoring & Observability

### Structured Logging

The application uses structured JSON logging:

```json
{
  "timestamp": "2026-01-23T10:30:00Z",
  "level": "INFO",
  "logger": "services.embedding_service",
  "message": "Chunks embedded",
  "count": 45,
  "duration_ms": 1250
}
```

### Log Aggregation

Configure log shipping to your log aggregation system:

```yaml
# Fluent Bit configuration example
[INPUT]
    Name        tail
    Path        /app/logs/*.log
    Parser      json

[OUTPUT]
    Name        elasticsearch
    Host        elasticsearch
    Port        9200
    Index       repograph-logs
```

### Metrics

Key metrics to monitor:

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `documents_processed_total` | Total documents processed | - |
| `processing_duration_seconds` | Processing time per document | > 60s |
| `embedding_errors_total` | Embedding generation failures | > 5/min |
| `vector_store_latency_seconds` | Pinecone operation latency | > 5s |
| `api_request_duration_seconds` | API response time | > 10s |

### Health Checks

Built-in health check endpoints:

```bash
# CLI health check
python main.py health

# Programmatic health check
from utils import check_all_services
import asyncio

health = asyncio.run(check_all_services())
print(f"Status: {health.status}")
```

### Alerting

Configure alerts for:
- Service health degradation
- High error rates
- Slow response times
- Resource exhaustion

---

## Troubleshooting

### Common Issues

#### 1. Azure OpenAI Connection Failures

**Symptoms:**
- "Connection refused" errors
- "401 Unauthorized" errors

**Solutions:**
```bash
# Verify endpoint
curl -X GET "${AZURE_OPENAI_ENDPOINT}openai/deployments?api-version=2024-02-01" \
  -H "api-key: ${AZURE_OPENAI_API_KEY}"

# Check deployment exists
# Ensure deployment names match exactly
```

#### 2. Pinecone Index Issues

**Symptoms:**
- "Index not found" errors
- Dimension mismatch errors

**Solutions:**
```python
# Verify index
from pinecone import Pinecone

pc = Pinecone(api_key="your_key")
indexes = pc.list_indexes()
print([idx.name for idx in indexes])

# Check dimension
index = pc.Index("your-index")
stats = index.describe_index_stats()
print(f"Dimension: {stats.dimension}")
```

#### 3. Memory Issues

**Symptoms:**
- Out of memory errors
- Slow processing

**Solutions:**
```bash
# Reduce batch sizes
export MAX_CONCURRENT_TASKS=2

# Increase memory
docker run -m 8g repograph-ai:latest

# Process in smaller batches
python main.py index --directory ./batch1
python main.py index --directory ./batch2
```

#### 4. File Processing Errors

**Symptoms:**
- "Unsupported file type" errors
- Extraction failures

**Solutions:**
```bash
# Check supported extensions
python -c "from utils import SUPPORTED_EXTENSIONS; print(SUPPORTED_EXTENSIONS)"

# Verify file isn't corrupted
file your-document.pdf

# Check file permissions
ls -la your-document.pdf
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# CLI
python main.py index --verbose

# Environment variable
export LOG_LEVEL=DEBUG
python main.py index
```

### Getting Help

If you encounter issues:

1. Check the logs: `./logs/repograph.log`
2. Run health checks: `python main.py health`
3. Verify configuration: `python test_setup.py`
4. Enable debug logging: `--verbose` flag

---

## Backup & Recovery

### Data Backup

The application stores data in:
- **Pinecone**: Vector embeddings and metadata
- **Local**: Processed document cache (optional)

### Recovery Procedures

1. **Re-index from source:**
```bash
# Force reprocess all documents
python main.py index --force
```

2. **Restore from Pinecone backup:**
```python
# Pinecone collections for backup
pc.create_collection(name="backup", source="main-index")
```

---

## Updates & Maintenance

### Updating Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade langchain
```

### Database Migrations

When updating the schema:

1. Create new index with updated dimension/config
2. Re-index all documents
3. Update application config
4. Delete old index

```python
# Example: Update to new embedding model
pc.create_index(
    name="new-index",
    dimension=3072,  # text-embedding-3-large
    metric="cosine",
)
# Re-run indexing
# Update PINECONE_INDEX_NAME in .env
```
