# RepoGraph AI - Architecture Guide

## Overview

RepoGraph AI is designed following enterprise-grade software engineering principles, implementing a microservices architecture with clear separation of concerns, dependency injection, and comprehensive error handling.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Extension Guide](#extension-guide)

---

## Design Principles

### SOLID Principles Implementation

#### 1. Single Responsibility Principle (SRP)

Each class has one reason to change:

```python
# ✅ Good: Each service handles one specific task
class DocumentScanner:
    """Only responsible for discovering and cataloging files."""
    
class ContentExtractor:
    """Only responsible for extracting text from documents."""
    
class AzureOpenAIEmbeddingService:
    """Only responsible for generating embeddings."""
```

#### 2. Open/Closed Principle (OCP)

The system is open for extension but closed for modification:

```python
# New file types can be added by creating new processors
# without modifying existing code

class NewFormatProcessor(BaseProcessor):
    """Add support for a new file format."""
    
    @property
    def supported_types(self) -> Set[FileType]:
        return {FileType.NEW_FORMAT}
    
    def extract(self, document: Document) -> Document:
        # Implementation
        pass

# Register with extractor
extractor = ContentExtractor()
extractor.register_processor(NewFormatProcessor())
```

#### 3. Liskov Substitution Principle (LSP)

All implementations can be substituted for their base types:

```python
# Any IVectorStore implementation can be used
def process_documents(vector_store: IVectorStore):
    vector_store.initialize()
    vector_store.upsert(chunks, document)
    
# Works with any implementation
process_documents(PineconeVectorStore())
process_documents(MilvusVectorStore())  # Alternative implementation
```

#### 4. Interface Segregation Principle (ISP)

Clients depend only on interfaces they use:

```python
# Small, focused interfaces
class IDocumentScanner(ABC):
    @abstractmethod
    def scan_directory(self, directory: Path) -> List[FileMetadata]:
        pass

class IVisionAnalyzer(ABC):
    @abstractmethod
    def analyze_image(self, image_path: Path) -> str:
        pass

# Services implement only what they need
```

#### 5. Dependency Inversion Principle (DIP)

High-level modules depend on abstractions:

```python
class RAGWorkflowOrchestrator:
    def __init__(
        self,
        scanner: IDocumentScanner,
        extractor: IContentExtractor,
        embedding_service: IEmbeddingService,
        vector_store: IVectorStore,
    ):
        # Depends on interfaces, not concrete implementations
        self.scanner = scanner
        self.extractor = extractor
        self.embedding_service = embedding_service
        self.vector_store = vector_store
```

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Presentation Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │    CLI (main)   │  │  CLI (query)    │  │    REST API (FastAPI)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Orchestration Layer                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    LangGraph Workflow Orchestrator                 │  │
│  │                                                                    │  │
│  │   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐  │  │
│  │   │ Scan   │──▶│Extract │──▶│Analyze │──▶│Summarize──▶│ Chunk  │  │  │
│  │   └────────┘   └────────┘   └────────┘   └────────┘   └────────┘  │  │
│  │                                                            │       │  │
│  │   ┌────────┐   ┌────────┐   ┌────────┐                    ▼       │  │
│  │   │Finalize│◀──│ Store  │◀──│ Embed  │◀───────────────────┘       │  │
│  │   └────────┘   └────────┘   └────────┘                            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Service Layer                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│
│  │  Document   │ │   Content   │ │   Vision    │ │   Summarization     ││
│  │   Scanner   │ │  Extractor  │ │   Service   │ │      Service        ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│
│  │   Chunker   │ │  Embedding  │ │   Vector    │ │      Query          ││
│  │   Service   │ │   Service   │ │    Store    │ │      Service        ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Infrastructure Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│
│  │ File System │ │Azure OpenAI │ │Google Vision│ │      Pinecone       ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Components |
|-------|---------------|------------|
| **Presentation** | User interaction, input validation | CLI apps, REST API |
| **Orchestration** | Workflow coordination, state management | LangGraph, Workflow nodes |
| **Service** | Business logic, processing | All service classes |
| **Infrastructure** | External system integration | API clients, file system |

---

## Component Details

### 1. Configuration Management (`config/`)

```python
# Hierarchical settings with Pydantic validation
Settings
├── AzureOpenAISettings
├── PineconeSettings
├── GoogleVisionSettings
├── GitHubSettings
├── ProcessingSettings
├── LoggingSettings
└── APISettings
```

**Features:**
- Environment variable loading with `.env` support
- Type validation and coercion
- Default values with overrides
- Cached singleton pattern

### 2. Document Models (`models/`)

```python
# Core domain models
FileMetadata      # File system metadata
Document          # Processing unit with content and status
Chunk             # Text fragment for embedding
EmbeddedChunk     # Chunk with vector embedding
VectorMetadata    # Pinecone-stored metadata
SearchResult      # Query result item
QueryResult       # Complete RAG response

# Workflow models
WorkflowState     # LangGraph state container
WorkflowResult    # Execution summary
```

### 3. Processors (`processors/`)

Strategy pattern implementation for file type handling:

```python
BaseProcessor (Abstract)
├── ImageProcessor      # PNG, JPG, SVG, GIF, BMP, WEBP
├── DiagramProcessor    # DrawIO, Excalidraw
├── DocumentProcessor   # DOCX, PDF, PPTX, ODT
├── SpreadsheetProcessor # XLSX, XLS
├── StructuredProcessor # JSON, GraphQL, YAML, XML
├── CodeProcessor       # Python, JS, TS, Java, Go, etc.
├── TextProcessor       # Markdown, TXT, LOG
└── VideoProcessor      # MP4, AVI, MOV (metadata only)
```

### 4. Services (`services/`)

| Service | Interface | Responsibility |
|---------|-----------|----------------|
| DocumentScanner | IDocumentScanner | File discovery, metadata extraction |
| ContentExtractor | IContentExtractor | Unified content extraction |
| GoogleVisionService | IVisionAnalyzer | Image/diagram analysis |
| AzureOpenAISummarizer | ISummarizer | Document summarization |
| AzureOpenAIEmbeddingService | IEmbeddingService | Vector generation |
| DocumentChunker | IChunker | Text splitting |
| PineconeVectorStore | IVectorStore | Vector storage/retrieval |
| RAGQueryService | IQueryService | RAG query handling |

### 5. Workflow (`workflows/`)

LangGraph state machine implementation:

```python
RAGWorkflowOrchestrator
├── initialize_node       # Setup timing, state
├── scan_directory_node   # Discover files
├── load_existing_node    # Get indexed records
├── filter_documents_node # Deduplicate
├── extract_content_node  # Extract text
├── analyze_vision_node   # Vision API analysis
├── summarize_node        # Generate summaries
├── chunk_node            # Split documents
├── embed_node            # Generate embeddings
├── store_node            # Save to Pinecone
└── finalize_node         # Compute statistics
```

---

## Data Flow

### Indexing Pipeline

```
1. SCAN
   Input: Directory path
   Output: List[FileMetadata]
   Action: Traverse filesystem, collect metadata, compute hashes

2. DEDUPLICATE
   Input: List[FileMetadata], existing_paths, existing_hashes
   Output: List[FileMetadata] (filtered)
   Action: Remove already-indexed files

3. EXTRACT
   Input: List[Document]
   Output: List[Document] with extracted_text
   Action: Route to appropriate processor, extract content

4. ANALYZE (conditional)
   Input: List[Document] (images/diagrams)
   Output: List[Document] with vision_analysis
   Action: Call Google Vision API for visual content

5. SUMMARIZE
   Input: List[Document]
   Output: List[Document] with summary
   Action: Generate comprehensive summaries with Azure OpenAI

6. CHUNK
   Input: List[Document]
   Output: List[Chunk]
   Action: Split content into overlapping chunks

7. EMBED
   Input: List[Chunk]
   Output: List[EmbeddedChunk]
   Action: Generate embeddings with Azure OpenAI

8. STORE
   Input: List[EmbeddedChunk]
   Output: Vector count
   Action: Upsert to Pinecone with metadata
```

### Query Pipeline

```
1. EMBED QUERY
   Input: Question string
   Output: Query embedding vector
   Action: Generate embedding for question

2. SEARCH
   Input: Query embedding, filters
   Output: List[SearchResult]
   Action: Similarity search in Pinecone

3. BUILD CONTEXT
   Input: List[SearchResult]
   Output: Context string
   Action: Combine relevant chunks

4. GENERATE
   Input: Question, Context
   Output: Answer string
   Action: RAG generation with Azure OpenAI

5. FORMAT RESPONSE
   Input: Answer, Sources
   Output: QueryResult
   Action: Package response with citations
```

---

## Design Patterns

### 1. Strategy Pattern (Processors)

```python
class ContentExtractor:
    def __init__(self):
        self.processors = [
            ImageProcessor(),
            DiagramProcessor(),
            DocumentProcessor(),
            # ...
        ]
    
    def extract(self, document: Document) -> Document:
        for processor in self.processors:
            if processor.can_process(document):
                return processor.extract(document)
```

### 2. Factory Pattern (Service Creation)

```python
def create_workflow() -> RAGWorkflowOrchestrator:
    """Factory function for workflow creation."""
    return RAGWorkflowOrchestrator()
```

### 3. State Machine Pattern (LangGraph)

```python
graph = StateGraph(RAGWorkflowState)
graph.add_node("extract", extract_content_node)
graph.add_node("analyze", analyze_with_vision_node)
graph.add_conditional_edges(
    "filter",
    should_continue,
    {"continue": "extract", "skip": "finalize"}
)
```

### 4. Repository Pattern (Vector Store)

```python
class PineconeVectorStore(IVectorStore):
    def upsert(self, chunks, document) -> int: ...
    def search(self, embedding, top_k) -> List[SearchResult]: ...
    def delete_by_path(self, path) -> int: ...
```

---

## Extension Guide

### Adding a New File Type

1. **Add FileType enum value:**
```python
# models/document.py
class FileType(str, Enum):
    NEW_FORMAT = "newformat"
```

2. **Create processor:**
```python
# processors/new_format_processor.py
class NewFormatProcessor(BaseProcessor):
    @property
    def supported_types(self) -> Set[FileType]:
        return {FileType.NEW_FORMAT}
    
    def extract(self, document: Document) -> Document:
        # Implementation
        pass
```

3. **Register in package:**
```python
# processors/__init__.py
from processors.new_format_processor import NewFormatProcessor
```

### Adding a New Vector Store

1. **Implement interface:**
```python
class NewVectorStore(IVectorStore):
    def initialize(self) -> None: ...
    def upsert(self, chunks, doc) -> int: ...
    def search(self, embedding, top_k, filter) -> List[SearchResult]: ...
    # ...
```

2. **Use in workflow:**
```python
vector_store = NewVectorStore()
workflow = RAGWorkflowOrchestrator(vector_store=vector_store)
```

### Adding a New Workflow Node

1. **Create node function:**
```python
# workflows/nodes.py
def my_new_node(state: RAGWorkflowState) -> Dict[str, Any]:
    # Processing logic
    return {"new_field": value}
```

2. **Add to graph:**
```python
# workflows/orchestrator.py
graph.add_node("my_node", my_new_node)
graph.add_edge("previous_node", "my_node")
```

---

## Performance Considerations

### Batch Processing

- Embeddings generated in batches of 16
- Vector upserts in batches of 100
- Configurable concurrency limits

### Caching

- Settings cached with `@lru_cache`
- Existing paths/hashes cached for deduplication
- Connection pools for API clients

### Memory Management

- Streaming file reads for large documents
- Chunked processing for large batches
- Lazy loading of processors

---

## Error Handling

### Graceful Degradation

```python
try:
    analysis = vision_service.analyze_image(path)
except Exception as e:
    logger.warning(f"Vision analysis failed: {e}")
    analysis = fallback_description(path)
```

### Retry Logic

- Configurable retry counts for API calls
- Exponential backoff for rate limits
- Circuit breaker pattern for failing services

### Comprehensive Logging

```python
logger.info(
    "Processing document",
    file=document.metadata.name,
    type=document.metadata.file_type,
    size=document.metadata.size_bytes,
)
```

---

## Security Considerations

1. **Credential Management**: All secrets in `.env`, never in code
2. **Input Validation**: Pydantic models validate all inputs
3. **Path Traversal**: File operations restricted to data directory
4. **API Rate Limiting**: Configurable limits for external APIs
5. **Error Masking**: Sensitive info stripped from error messages

---

## Testing Strategy

### Unit Tests
- Individual processor tests
- Service method tests
- Model validation tests

### Integration Tests
- End-to-end pipeline tests
- API connectivity tests
- Vector store operations

### Performance Tests
- Large file handling
- Batch processing benchmarks
- Memory usage profiling
