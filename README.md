# RepoGraph AI

[//]: # (<p align="center">)

[//]: # (  <img src="docs/assets/logo.png" alt="RepoGraph AI Logo" width="200"/>)

[//]: # (</p>)

<p align="center">
  <strong>🚀 Enterprise-Grade Intelligent Document Processing & RAG System</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#api-reference">API Reference</a>
</p>

---

## 🌟 Overview

**RepoGraph AI** is a production-ready, microservices-based Retrieval-Augmented Generation (RAG) application that transforms your documents into an intelligent, searchable knowledge base. Built with enterprise requirements in mind, it processes 50+ file types, generates comprehensive summaries, and enables semantic search powered by Azure OpenAI and Pinecone.

### Key Capabilities

- 📊 **Multi-Format Processing**: Images, diagrams, documents, spreadsheets, code, and more
- 🤖 **AI-Powered Analysis**: Google Vision API for visual content, Azure OpenAI for understanding
- 🔍 **Semantic Search**: Find information using natural language queries
- 💬 **RAG Q&A**: Get accurate answers with source citations
- ⚡ **Incremental Processing**: Smart deduplication saves time and costs
- 🏗️ **Enterprise Architecture**: SOLID principles, microservices, comprehensive logging

---

## ✨ Features

### 📚 Multi-Format Document Processing

| Category | Supported Formats |
|----------|------------------|
| **Images** | PNG, JPG, JPEG, SVG, GIF, BMP, WEBP |
| **Diagrams** | DrawIO, Excalidraw |
| **Documents** | DOCX, PDF, PPTX, ODT |
| **Spreadsheets** | XLSX, XLS |
| **Structured** | JSON, GraphQL, YAML, XML |
| **Code** | Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, SQL, and more |
| **Text** | Markdown, TXT, LOG, config files |
| **Video** | MP4, AVI, MOV (metadata extraction) |

### 🧠 Intelligent Processing Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Scan      │────▶│   Extract   │────▶│   Analyze   │────▶│  Summarize  │
│   Files     │     │   Content   │     │   (Vision)  │     │   (LLM)     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                    │
                                                                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Query     │◀────│   Search    │◀────│   Store     │◀────│   Embed     │
│   (RAG)     │     │  (Vector)   │     │  (Pinecone) │     │  (Azure AI) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 🔧 Enterprise Features

- **Smart Deduplication**: Automatically skip already-indexed documents
- **Incremental Updates**: Only process new or modified files
- **Comprehensive Logging**: Structured JSON logging with timing metrics
- **Health Monitoring**: Service health checks for all external dependencies
- **Error Recovery**: Graceful handling of failures with detailed error reporting
- **Configurable**: Environment-based configuration for easy deployment

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure OpenAI account with API access
- Pinecone account (free tier works)
- Google Vision API key (optional, for image analysis)

### Installation

```bash
# Clone or navigate to project
cd "/home/nadeeshame/PycharmProjects/RepoGraph AI"

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

The `.env` file is pre-configured. Review and update as needed:

```bash
# Key configurations
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
PINECONE_API_KEY=your_pinecone_key
GOOGLE_VISION_API_KEY=your_vision_key  # Optional
DATA_DIRECTORY=./data/diagrams
```

### Verify Setup

```bash
python test_setup.py
```

### Index Documents

```bash
# Index all documents in the data directory
python main.py index

# Force reprocess all documents
python main.py index --force

# Index a specific directory
python main.py index --directory ./my-docs
```

### Query the Knowledge Base

```bash
# Single question
python query.py ask "What is the Choreo architecture?"

# Search documents
python query.py search "authentication flow"

# Interactive mode
python query.py interactive
```

---

## 🏗️ Architecture

### Microservices Design

RepoGraph AI follows a clean microservices architecture with clear separation of concerns:

```
┌────────────────────────────────────────────────────────────────┐
│                        CLI Layer (main.py, query.py)           │
└────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────┐
│                    Workflow Orchestrator (LangGraph)            │
│         ┌─────────────────────────────────────────────┐        │
│         │  scan → extract → analyze → summarize →     │        │
│         │  chunk → embed → store → finalize           │        │
│         └─────────────────────────────────────────────┘        │
└────────────────────────────────────────────────────────────────┘
                                  │
          ┌───────────┬───────────┼───────────┬───────────┐
          ▼           ▼           ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
     │Document │ │ Vision  │ │Summarize│ │Embedding│ │ Vector  │
     │ Scanner │ │ Service │ │ Service │ │ Service │ │  Store  │
     └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
          │           │           │           │           │
          ▼           ▼           ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
     │File     │ │ Google  │ │ Azure   │ │ Azure   │ │Pinecone │
     │System   │ │ Vision  │ │ OpenAI  │ │ OpenAI  │ │         │
     └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### SOLID Principles

| Principle | Implementation |
|-----------|----------------|
| **S**ingle Responsibility | Each service handles one specific task |
| **O**pen/Closed | Easy to extend with new processors without modifying existing code |
| **L**iskov Substitution | All implementations follow interface contracts |
| **I**nterface Segregation | Small, focused interfaces (IDocumentScanner, IVisionAnalyzer, etc.) |
| **D**ependency Inversion | High-level modules depend on abstractions |

### Project Structure

```
RepoGraph AI/
├── .github/                    # GitHub Actions CI/CD
│   ├── workflows/
│   │   ├── ci-cd.yml          # Main CI/CD pipeline
│   │   ├── codeql-analysis.yml # Security scanning
│   │   ├── dependency-updates.yml
│   │   ├── docker.yml         # Docker build & test
│   │   └── release.yml        # Release management
│   └── dependabot.yml         # Dependency updates
│
├── config/                     # Configuration management
│   ├── __init__.py
│   └── settings.py            # Pydantic settings with validation
│
├── interfaces/                 # Abstract base classes (contracts)
│   ├── __init__.py
│   └── service_interfaces.py  # IDocumentScanner, IEmbeddingService, etc.
│
├── models/                     # Domain models
│   ├── __init__.py
│   ├── document.py            # Document, Chunk, FileMetadata
│   └── state.py               # Workflow state models
│
├── processors/                 # Content extraction (Strategy pattern)
│   ├── __init__.py
│   ├── base_processor.py      # Abstract base processor
│   ├── image_processor.py     # PNG, JPG, SVG, etc.
│   ├── diagram_processor.py   # DrawIO, Excalidraw
│   ├── document_processor.py  # DOCX, PDF, PPTX
│   ├── spreadsheet_processor.py
│   ├── structured_processor.py # JSON, GraphQL, YAML
│   ├── code_processor.py      # Source code files
│   ├── text_processor.py      # Markdown, TXT
│   └── video_processor.py     # Video metadata
│
├── services/                   # Core microservices
│   ├── __init__.py
│   ├── document_scanner.py    # File discovery & metadata
│   ├── content_extractor.py   # Unified extraction with processor registry
│   ├── vision_service.py      # Google Vision API integration
│   ├── summarization_service.py # Azure OpenAI summarization
│   ├── embedding_service.py   # Azure OpenAI embeddings
│   ├── chunker_service.py     # Intelligent text chunking
│   ├── vector_store.py        # Pinecone operations
│   └── query_service.py       # RAG query handling
│
├── workflows/                  # LangGraph orchestration
│   ├── __init__.py
│   ├── states.py              # Workflow state definitions
│   ├── nodes.py               # Pipeline node functions
│   └── orchestrator.py        # Graph builder & runner
│
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── file_utils.py          # File operations, hashing
│   ├── logging_config.py      # Structured logging
│   └── health_check.py        # Service health monitoring
│
├── tests/                      # Unit & integration tests
│   ├── __init__.py
│   ├── test_models.py
│   └── test_services.py
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── CONFIGURATION.md
│   ├── DEPLOYMENT.md
│   └── CICD.md                # CI/CD pipeline documentation
│
├── data/                       # Data directory
│   └── diagrams/              # Your documents go here
│
├── main.py                    # CLI: Indexing entry point
├── query.py                   # CLI: Query entry point
├── api.py                     # FastAPI REST server
├── test_setup.py              # Setup verification
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Multi-service deployment
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Test configuration
├── cliff.toml                 # Changelog generator config
├── .env                       # Configuration (gitignored)
└── README.md                  # This file
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Architecture Guide](docs/ARCHITECTURE.md) | Detailed architecture and design patterns |
| [API Reference](docs/API_REFERENCE.md) | Service APIs and interfaces |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production deployment instructions |
| [Configuration Guide](docs/CONFIGURATION.md) | All configuration options |
| [CI/CD Pipeline](docs/CICD.md) | GitHub Actions workflows and deployment |

---

## ⚙️ Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Required |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | Required |
| `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` | Embedding model deployment | choreo-ai-embedding |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat model deployment | architect-agent-development |
| `PINECONE_API_KEY` | Pinecone API key | Required |
| `PINECONE_INDEX_NAME` | Pinecone index name | choreo-ai-assistant-v2 |
| `PINECONE_DIMENSION` | Embedding dimension | 1536 |
| `GOOGLE_VISION_API_KEY` | Google Vision API key | Optional |
| `DATA_DIRECTORY` | Directory to process | ./data/diagrams |
| `CHUNK_SIZE` | Text chunk size | 1000 |
| `CHUNK_OVERLAP` | Chunk overlap | 200 |
| `SKIP_EXISTING_DOCUMENTS` | Skip indexed documents | true |

---

## 🔧 CLI Commands

### Indexing (main.py)

```bash
# Index documents
python main.py index [OPTIONS]

Options:
  -d, --directory TEXT   Directory to process
  -f, --force           Force reprocess all documents
  --skip-existing       Skip already indexed (default)
  -v, --verbose         Verbose logging

# Check status
python main.py status

# Health check
python main.py health
```

### Querying (query.py)

```bash
# Ask a question
python query.py ask "Your question here" [OPTIONS]

Options:
  -k, --top-k INT       Number of sources (default: 5)
  --sources/--no-sources Show source documents

# Search documents
python query.py search "search query" [OPTIONS]

Options:
  -k, --top-k INT       Number of results (default: 10)
  -t, --type TEXT       Filter by file type

# Interactive mode
python query.py interactive
```

---

## 📊 Processing Statistics

When you run the indexer, you'll see detailed statistics:

```
📊 Processing Summary
┌────────────────────┬───────┐
│ Metric             │ Value │
├────────────────────┼───────┤
│ Total Files Found  │ 150   │
│ Files Skipped      │ 145   │
│ Files Processed    │ 5     │
│ Files Failed       │ 0     │
│ Chunks Created     │ 45    │
│ Embeddings Generated│ 45   │
│ Vectors Stored     │ 45    │
└────────────────────┴───────┘

✨ Indexing complete!
```

---

## 🔄 CI/CD Pipeline

RepoGraph AI includes a comprehensive, professional-grade CI/CD pipeline using GitHub Actions for automated building, testing, security scanning, and deployment to Google Cloud Run.

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD Pipeline                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────────────────────┐  │
│  │  Lint   │───▶│  Test   │───▶│Security │───▶│    Build Docker Image    │  │
│  │ (Black, │    │(Matrix) │    │  Scan   │    │                          │  │
│  │ flake8) │    │3.10-3.12│    │(CodeQL) │    │                          │  │
│  └─────────┘    └─────────┘    └─────────┘    └────────────┬─────────────┘  │
│                                                             │                │
│                                   ┌─────────────────────────┴──────────┐    │
│                                   │                                    │    │
│                                   ▼                                    ▼    │
│                          ┌─────────────────┐              ┌─────────────────┐│
│                          │ Deploy Staging  │─────────────▶│ Deploy Prod     ││
│                          │ (Cloud Run)     │              │ (Cloud Run)     ││
│                          └─────────────────┘              └────────┬────────┘│
│                                                                    │         │
│                                                                    ▼         │
│                                                           ┌─────────────────┐│
│                                                           │ Create Release  ││
│                                                           │ (GitHub)        ││
│                                                           └─────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Workflow Files

| Workflow | File | Purpose |
|----------|------|---------|
| **Main CI/CD** | `ci-cd.yml` | Complete pipeline: lint, test, build, deploy |
| **CodeQL Security** | `codeql-analysis.yml` | Advanced security analysis & SAST |
| **Dependency Updates** | `dependency-updates.yml` | Automated dependency management |
| **Release Management** | `release.yml` | Semantic versioning & releases |
| **Docker Build** | `docker.yml` | Docker image building & testing |
| **Dependabot** | `dependabot.yml` | Automated dependency PRs |

### Pipeline Features

#### 🔍 Code Quality
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

#### 🧪 Testing
- Matrix testing across Python 3.10, 3.11, 3.12
- pytest with coverage reporting
- Codecov integration

#### 🔒 Security
- **CodeQL** - Advanced static analysis
- **Bandit** - Python security linter
- **Semgrep** - SAST scanning
- **Trivy** - Container vulnerability scanning
- **Gitleaks** - Secret detection
- **pip-audit** - Dependency vulnerabilities

#### 🐳 Docker
- Multi-stage optimized builds
- Hadolint Dockerfile linting
- Security scanning with Trivy & Grype
- Automatic push to Google Container Registry

#### 🚀 Deployment
- **Staging**: Auto-deploy on `develop` branch
- **Production**: Auto-deploy on `main` branch or version tags
- Google Cloud Run serverless deployment
- Health check validation

#### 📦 Release Management
- Semantic versioning (X.Y.Z)
- Automated changelog generation
- GitHub Release creation
- Docker image tagging

### Quick Commands

```bash
# Trigger manual deployment
gh workflow run ci-cd.yml --ref main -f environment=production

# Create a release
git tag v1.0.0 && git push origin v1.0.0

# Force dependency update
gh workflow run dependency-updates.yml -f update_type=security
```

### Required Secrets

Configure in GitHub → Settings → Secrets:

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Google Cloud Project ID |
| `GCP_SA_KEY` | Service Account JSON key |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |
| `PINECONE_API_KEY` | Pinecone API key |

See [CI/CD Documentation](docs/CICD.md) for complete setup guide.

---

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build the image
docker build -t repograph-ai:latest .

# Run the API server
docker run -d -p 8000:8000 \
  -e AZURE_OPENAI_API_KEY=your_key \
  -e AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
  -e PINECONE_API_KEY=your_key \
  repograph-ai:latest \
  uvicorn api:app --host 0.0.0.0 --port 8000

# Access the API
curl http://localhost:8000/health
```

### Docker Compose

```bash
# Run indexer
docker-compose up repograph-indexer

# Run API server
docker-compose up -d repograph-api

# Interactive query mode
docker-compose --profile interactive run repograph-query
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Follow the existing architecture patterns
2. Implement interfaces for new services
3. Add comprehensive documentation
4. Include unit tests for new functionality
5. Follow SOLID principles
6. Use conventional commits for changelog generation

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and test
pytest tests/ -v

# Commit with conventional format
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 🙏 Acknowledgments

- **LangGraph** - Workflow orchestration
- **LangChain** - Document processing utilities
- **Azure OpenAI** - Embeddings and language models
- **Pinecone** - Vector database
- **Google Vision** - Image analysis
- **Google Cloud Run** - Serverless deployment
- **GitHub Actions** - CI/CD pipeline
- **Pydantic** - Data validation
- **Rich** - Beautiful terminal output
- **Typer** - CLI framework

---

<p align="center">
  Built with ❤️ for intelligent document processing
</p>
