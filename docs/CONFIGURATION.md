# RepoGraph AI - Configuration Guide

## Overview

RepoGraph AI uses environment-based configuration with Pydantic validation for type safety and automatic parsing. All configuration is loaded from a `.env` file in the project root.

---

## Quick Setup

1. Copy the example configuration:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials
3. Verify configuration:
```bash
python test_setup.py
```

---

## Configuration Sections

### Azure OpenAI Configuration

```bash
# ─────────────────────────────────────────────────────────────────────────────
# Azure OpenAI Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Your Azure OpenAI API key
AZURE_OPENAI_API_KEY=your_api_key_here

# Azure OpenAI endpoint (must end with /)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Embeddings Configuration
# The deployment name of your embedding model
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=choreo-ai-embedding

# API version for embeddings
AZURE_OPENAI_EMBEDDINGS_VERSION=2024-02-01

# Chat/Completion Configuration
# The deployment name of your chat model
AZURE_OPENAI_CHAT_DEPLOYMENT=architect-agent-development

# API version for chat completions
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**Notes:**
- Deployment names must match exactly what's configured in Azure Portal
- Embedding models: `text-embedding-ada-002`, `text-embedding-3-small`, `text-embedding-3-large`
- Chat models: `gpt-4`, `gpt-4-turbo`, `gpt-35-turbo`

### Pinecone Configuration

```bash
# ─────────────────────────────────────────────────────────────────────────────
# Pinecone Vector Database Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Your Pinecone API key
PINECONE_API_KEY=your_pinecone_api_key

# Index name (will be created if it doesn't exist)
PINECONE_INDEX_NAME=choreo-ai-assistant-v2

# Embedding dimension (must match your embedding model)
# 1536 for text-embedding-ada-002 or text-embedding-3-small
# 3072 for text-embedding-3-large
# 384 for sentence-transformers/all-MiniLM-L6-v2
PINECONE_DIMENSION=1536

# Serverless configuration
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Namespace configuration
PINECONE_USE_NAMESPACES=true
PINECONE_NAMESPACE=documents
```

**Notes:**
- Dimension must match your embedding model exactly
- Serverless is recommended for most use cases
- Namespaces help organize vectors by category or source

### Google Vision Configuration

```bash
# ─────────────────────────────────────────────────────────────────────────────
# Google Vision API Configuration
# ─────────────────────────────────────────────────────────────────────────────

# API Key for Google Vision (for image/diagram analysis)
GOOGLE_VISION_API_KEY=your_google_vision_api_key

# Alternative: Path to service account credentials JSON
# GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-vision.json
```

**Notes:**
- Google Vision is optional - system works without it
- Required for analyzing images and diagrams
- Get API key from Google Cloud Console

### GitHub Configuration

```bash
# ─────────────────────────────────────────────────────────────────────────────
# GitHub Configuration
# ─────────────────────────────────────────────────────────────────────────────

# GitHub personal access token (for higher rate limits)
GITHUB_TOKEN=ghp_your_github_token

# Default repository to process
GITHUB_REPO_URL=https://github.com/user/repo
```

### Processing Configuration

```bash
# ─────────────────────────────────────────────────────────────────────────────
# Data Processing Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Directory containing files to process
DATA_DIRECTORY=./data/diagrams

# Enable/disable local file processing
PROCESS_LOCAL_FILES=true

# Chunking configuration
CHUNK_SIZE=1000          # Characters per chunk
CHUNK_OVERLAP=200        # Overlap between chunks

# Deduplication
SKIP_EXISTING_DOCUMENTS=true    # Skip already indexed documents
FORCE_REPROCESS=false           # Force reprocess all documents

# Concurrency
MAX_CONCURRENT_TASKS=5          # Maximum parallel processing tasks
```

**Chunking Guidelines:**
| Content Type | Recommended Chunk Size | Overlap |
|--------------|----------------------|---------|
| Technical docs | 1000 | 200 |
| Code files | 500 | 100 |
| Long-form text | 1500 | 300 |
| Short documents | 500 | 100 |

### URL Processing (Optional)

```bash
# ─────────────────────────────────────────────────────────────────────────────
# URL Processing Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Enable URL processing
PROCESS_URLS=false

# Comma-separated list of URLs to process
URL_LIST=https://example.com/doc1,https://example.com/doc2

# Or: Path to file containing URLs (one per line)
URL_FILE_PATH=./urls.txt

# Request timeout in seconds
URL_TIMEOUT=30
```

### Logging Configuration

```bash
# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format: "json" or "console"
LOG_FORMAT=json

# Log file path (optional)
LOG_FILE=./logs/repograph.log
```

### API Server Configuration

```bash
# ─────────────────────────────────────────────────────────────────────────────
# API Server Configuration (for REST API mode)
# ─────────────────────────────────────────────────────────────────────────────

API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

---

## Configuration Profiles

### Development Profile

```bash
# Minimal configuration for development
AZURE_OPENAI_API_KEY=your_dev_key
AZURE_OPENAI_ENDPOINT=https://your-dev-resource.openai.azure.com/
PINECONE_API_KEY=your_dev_pinecone_key
DATA_DIRECTORY=./data/diagrams
LOG_LEVEL=DEBUG
SKIP_EXISTING_DOCUMENTS=false
```

### Production Profile

```bash
# Full configuration for production
AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
PINECONE_API_KEY=${PINECONE_API_KEY}
GOOGLE_VISION_API_KEY=${GOOGLE_VISION_API_KEY}
DATA_DIRECTORY=/data/documents
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_FILE=/var/log/repograph/app.log
SKIP_EXISTING_DOCUMENTS=true
MAX_CONCURRENT_TASKS=10
```

### Testing Profile

```bash
# Configuration for testing
AZURE_OPENAI_API_KEY=test_key
AZURE_OPENAI_ENDPOINT=https://test.openai.azure.com/
PINECONE_API_KEY=test_pinecone_key
PINECONE_INDEX_NAME=test-index
DATA_DIRECTORY=./test/data
LOG_LEVEL=DEBUG
FORCE_REPROCESS=true
```

---

## Programmatic Configuration

You can also configure the application programmatically:

```python
from config import get_settings

# Get all settings
settings = get_settings()

# Access specific sections
print(settings.azure_openai.endpoint)
print(settings.pinecone.index_name)
print(settings.processing.chunk_size)

# Override settings for a specific run
from services import AzureOpenAIEmbeddingService

service = AzureOpenAIEmbeddingService(
    api_key="override_key",
    endpoint="https://override.openai.azure.com/",
    deployment="custom-deployment",
)
```

---

## Environment Variable Reference

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | string | Yes | - | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | string | Yes | - | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` | string | No | choreo-ai-embedding | Embedding model deployment |
| `AZURE_OPENAI_EMBEDDINGS_VERSION` | string | No | 2024-02-01 | Embeddings API version |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | string | No | architect-agent-development | Chat model deployment |
| `AZURE_OPENAI_API_VERSION` | string | No | 2024-12-01-preview | Chat API version |
| `PINECONE_API_KEY` | string | Yes | - | Pinecone API key |
| `PINECONE_INDEX_NAME` | string | No | choreo-ai-assistant-v2 | Pinecone index name |
| `PINECONE_DIMENSION` | integer | No | 1536 | Embedding dimension |
| `PINECONE_CLOUD` | string | No | aws | Cloud provider |
| `PINECONE_REGION` | string | No | us-east-1 | Region |
| `PINECONE_USE_NAMESPACES` | boolean | No | true | Use namespaces |
| `PINECONE_NAMESPACE` | string | No | documents | Default namespace |
| `GOOGLE_VISION_API_KEY` | string | No | - | Google Vision API key |
| `GITHUB_TOKEN` | string | No | - | GitHub access token |
| `DATA_DIRECTORY` | path | No | ./data/diagrams | Data directory |
| `CHUNK_SIZE` | integer | No | 1000 | Chunk size |
| `CHUNK_OVERLAP` | integer | No | 200 | Chunk overlap |
| `SKIP_EXISTING_DOCUMENTS` | boolean | No | true | Skip indexed docs |
| `FORCE_REPROCESS` | boolean | No | false | Force reprocess |
| `LOG_LEVEL` | string | No | INFO | Logging level |
| `LOG_FORMAT` | string | No | json | Log format |

---

## Troubleshooting

### Common Issues

**Issue: "API key not configured"**
```
Solution: Ensure the API key is set in .env and the file is in the project root
```

**Issue: "Dimension mismatch"**
```
Solution: PINECONE_DIMENSION must match your embedding model:
- text-embedding-ada-002: 1536
- text-embedding-3-small: 1536
- text-embedding-3-large: 3072
```

**Issue: "Index not found"**
```
Solution: The index will be created automatically on first run.
Check that PINECONE_CLOUD and PINECONE_REGION are correct.
```

**Issue: "Permission denied" for data directory**
```
Solution: Ensure the DATA_DIRECTORY path exists and is readable
```

### Validation

Run the setup verification script to check all configuration:

```bash
python test_setup.py
```

This will verify:
- Python version
- Environment file presence
- Dependency installation
- Configuration loading
- Data directory accessibility
- Azure OpenAI connectivity
- Pinecone connectivity
- Google Vision accessibility (if configured)
