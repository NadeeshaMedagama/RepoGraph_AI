# RepoGraph AI - API Reference

## Overview

This document provides comprehensive API documentation for all services and interfaces in RepoGraph AI.

---

## Table of Contents

1. [Interfaces](#interfaces)
2. [Services](#services)
3. [Models](#models)
4. [Workflow](#workflow)
5. [Utilities](#utilities)

---

## Interfaces

### IDocumentScanner

Interface for document scanning and discovery.

```python
from interfaces import IDocumentScanner

class IDocumentScanner(ABC):
    @abstractmethod
    def scan_directory(self, directory: Path) -> List[FileMetadata]:
        """
        Scan a directory for processable files.
        
        Args:
            directory: Path to the directory to scan
            
        Returns:
            List of file metadata for discovered files
        """
        pass
    
    @abstractmethod
    def get_file_hash(self, file_path: Path) -> str:
        """
        Generate a content hash for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash of file contents
        """
        pass
```

### IContentExtractor

Interface for content extraction from files.

```python
from interfaces import IContentExtractor

class IContentExtractor(ABC):
    @abstractmethod
    def can_process(self, file_metadata: FileMetadata) -> bool:
        """Check if this extractor can process the given file."""
        pass
    
    @abstractmethod
    def extract(self, document: Document) -> Document:
        """Extract content from a document."""
        pass
```

### IVisionAnalyzer

Interface for vision-based content analysis.

```python
from interfaces import IVisionAnalyzer

class IVisionAnalyzer(ABC):
    @abstractmethod
    def analyze_image(self, image_path: Path) -> str:
        """
        Analyze an image and extract textual description.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Textual description/analysis of the image
        """
        pass
    
    @abstractmethod
    def extract_text_from_image(self, image_path: Path) -> str:
        """Perform OCR on an image."""
        pass
```

### ISummarizer

Interface for text summarization.

```python
from interfaces import ISummarizer

class ISummarizer(ABC):
    @abstractmethod
    def summarize(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a comprehensive summary of the text."""
        pass
    
    @abstractmethod
    def summarize_document(self, document: Document) -> Document:
        """Generate a summary for a document."""
        pass
```

### IChunker

Interface for text chunking.

```python
from interfaces import IChunker

class IChunker(ABC):
    @abstractmethod
    def chunk(self, document: Document) -> List[Chunk]:
        """Split a document into chunks."""
        pass
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Chunk raw text."""
        pass
```

### IEmbeddingService

Interface for text embedding.

```python
from interfaces import IEmbeddingService

class IEmbeddingService(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @abstractmethod
    def embed_chunks(self, chunks: List[Chunk]) -> List[EmbeddedChunk]:
        """Embed a list of chunks."""
        pass
```

### IVectorStore

Interface for vector database operations.

```python
from interfaces import IVectorStore

class IVectorStore(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the vector store connection."""
        pass
    
    @abstractmethod
    def upsert(self, embedded_chunks: List[EmbeddedChunk], document: Document) -> int:
        """Store embedded chunks in the vector database."""
        pass
    
    @abstractmethod
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def get_existing_paths(self) -> set:
        """Get all indexed file paths."""
        pass
    
    @abstractmethod
    def get_existing_hashes(self) -> set:
        """Get all indexed content hashes."""
        pass
    
    @abstractmethod
    def delete_by_path(self, path: str) -> int:
        """Delete vectors for a specific file path."""
        pass
```

### IQueryService

Interface for RAG query operations.

```python
from interfaces import IQueryService

class IQueryService(ABC):
    @abstractmethod
    def query(self, question: str, top_k: int = 5) -> QueryResult:
        """Answer a question using RAG."""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Perform semantic search without generation."""
        pass
```

---

## Services

### DocumentScanner

File discovery and metadata extraction service.

```python
from services import DocumentScanner

scanner = DocumentScanner(
    recursive=True,        # Scan subdirectories
    include_hidden=False,  # Skip hidden files
)

# Scan a directory
metadata_list = scanner.scan_directory(Path("./data/diagrams"))

# Get file hash
hash_value = scanner.get_file_hash(Path("./file.pdf"))

# Filter existing files
new_files, skipped = scanner.filter_by_existing(
    metadata_list,
    existing_paths={"./already/indexed.pdf"},
    existing_hashes={"abc123..."},
)

# Create Document objects
documents = scanner.create_documents(metadata_list)
```

### ContentExtractor

Unified content extraction with processor registry.

```python
from services import ContentExtractor

extractor = ContentExtractor()

# Check if file type is supported
can_process = extractor.can_process(file_metadata)

# Extract content from a document
document = extractor.extract(document)

# Batch extraction
documents = extractor.extract_batch(documents)

# Get supported extensions
extensions = extractor.get_supported_extensions()
# ['.docx', '.json', '.md', '.pdf', '.png', ...]

# Register custom processor
extractor.register_processor(MyCustomProcessor())
```

### GoogleVisionService

Google Vision API integration.

```python
from services import GoogleVisionService

vision = GoogleVisionService(api_key="your_api_key")

# Analyze image (OCR + labels + objects)
analysis = vision.analyze_image(Path("./diagram.png"))

# Extract text only (OCR)
text = vision.extract_text_from_image(Path("./screenshot.png"))

# Analyze document (updates document.vision_analysis)
document = vision.analyze_document(document)
```

### AzureOpenAISummarizer

Document summarization service.

```python
from services import AzureOpenAISummarizer

summarizer = AzureOpenAISummarizer(
    api_key="your_key",
    endpoint="https://your-resource.openai.azure.com/",
    deployment="architect-agent-development",
)

# Summarize text
summary = summarizer.summarize(
    text="Long document content...",
    context={"file_name": "report.pdf", "file_type": "pdf"}
)

# Summarize document (updates document.summary)
document = summarizer.summarize_document(document)

# Batch summarization
documents = summarizer.summarize_batch(documents)
```

### AzureOpenAIEmbeddingService

Embedding generation service.

```python
from services import AzureOpenAIEmbeddingService

embedding_service = AzureOpenAIEmbeddingService(
    api_key="your_key",
    endpoint="https://your-resource.openai.azure.com/",
    deployment="choreo-ai-embedding",
)

# Single embedding
embedding = embedding_service.embed("Some text")
# Returns: List[float] with 1536 dimensions

# Batch embeddings
embeddings = embedding_service.embed_batch(["Text 1", "Text 2", "Text 3"])
# Returns: List[List[float]]

# Embed chunks
embedded_chunks = embedding_service.embed_chunks(chunks)
# Returns: List[EmbeddedChunk]

# Get dimension
dim = embedding_service.dimension  # 1536
```

### DocumentChunker

Text chunking service.

```python
from services import DocumentChunker

chunker = DocumentChunker(
    chunk_size=1000,     # Characters per chunk
    chunk_overlap=200,   # Overlap between chunks
)

# Chunk a document
chunks = chunker.chunk(document)
# Returns: List[Chunk]

# Chunk raw text
chunks = chunker.chunk_text(
    text="Long text content...",
    metadata={"source": "file.txt"}
)

# Chunk multiple documents
doc_chunks = chunker.chunk_documents(documents)
# Returns: Dict[str, List[Chunk]]

# Estimate chunk count
estimate = chunker.estimate_chunks("Some text...")
```

### PineconeVectorStore

Pinecone vector database operations.

```python
from services import PineconeVectorStore

vector_store = PineconeVectorStore(
    api_key="your_pinecone_key",
    index_name="choreo-ai-assistant-v2",
    namespace="documents",
)

# Initialize connection (creates index if needed)
vector_store.initialize()

# Store vectors
count = vector_store.upsert(embedded_chunks, document)

# Search
results = vector_store.search(
    query_embedding=[0.1, 0.2, ...],
    top_k=10,
    filter={"file_type": "pdf"}
)
# Returns: List[SearchResult]

# Get existing records for deduplication
paths = vector_store.get_existing_paths()
hashes = vector_store.get_existing_hashes()

# Get statistics
stats = vector_store.get_stats()
# {'index_name': '...', 'dimension': 1536, 'total_vectors': 1000, ...}

# Delete by path
deleted = vector_store.delete_by_path("./old/file.pdf")
```

### RAGQueryService

RAG query handling service.

```python
from services import RAGQueryService

query_service = RAGQueryService(
    embedding_service=AzureOpenAIEmbeddingService(),
    vector_store=PineconeVectorStore(),
)

# RAG query with answer generation
result = query_service.query(
    question="What is the Choreo architecture?",
    top_k=5
)
# Returns: QueryResult
# result.answer - Generated answer
# result.sources - List of source documents
# result.processing_time_ms - Timing

# Semantic search only
results = query_service.search("authentication flow", top_k=10)
# Returns: List[SearchResult]

# Filtered search
results = query_service.search_by_filter(
    query="API gateway",
    filter={"category": "diagram"},
    top_k=10
)

# Get index stats
stats = query_service.get_index_stats()
```

---

## Models

### FileMetadata

```python
from models import FileMetadata

metadata = FileMetadata(
    path=Path("./data/report.pdf"),
    name="report.pdf",
    extension=".pdf",
    size_bytes=102400,
    created_at=datetime.now(),
    modified_at=datetime.now(),
    content_hash="sha256...",
    mime_type="application/pdf",
)

# Computed properties
metadata.file_type    # FileType.PDF
metadata.category     # FileCategory.DOCUMENT
```

### Document

```python
from models import Document

document = Document(
    metadata=file_metadata,
    raw_content="...",
    extracted_text="...",
    vision_analysis="...",
    summary="...",
    status=ProcessingStatus.COMPLETED,
)

# Get best content for embedding
content = document.get_content_for_embedding()
# Priority: summary > vision_analysis > extracted_text > raw_content

# Computed properties
document.source_path   # "/path/to/file.pdf"
document.display_name  # "file.pdf"
```

### Chunk

```python
from models import Chunk

chunk = Chunk(
    document_id=uuid4(),
    content="Chunk text content...",
    chunk_index=0,
    total_chunks=5,
    start_char=0,
    end_char=1000,
    metadata={"source": "file.pdf"},
)

# Computed properties
chunk.char_count  # 1000
```

### EmbeddedChunk

```python
from models import EmbeddedChunk

embedded = EmbeddedChunk(
    chunk=chunk,
    embedding=[0.1, 0.2, ...],  # 1536 floats
    embedding_model="choreo-ai-embedding",
)

# Computed properties
embedded.dimension  # 1536
```

### SearchResult

```python
from models import SearchResult

result = SearchResult(
    id="vector_id",
    score=0.92,
    metadata=vector_metadata,
    content="Matching text...",
)
```

### QueryResult

```python
from models import QueryResult

result = QueryResult(
    query="User's question",
    answer="Generated answer...",
    sources=[search_result1, search_result2],
    model_used="architect-agent-development",
    processing_time_ms=1250,
)
```

### Enums

```python
from models import FileType, FileCategory, ProcessingStatus

# FileType - All supported file extensions
FileType.PDF, FileType.DOCX, FileType.PNG, ...

# FileCategory - High-level categories
FileCategory.IMAGE, FileCategory.DOCUMENT, FileCategory.CODE, ...

# ProcessingStatus - Processing states
ProcessingStatus.PENDING
ProcessingStatus.EXTRACTING
ProcessingStatus.ANALYZING
ProcessingStatus.SUMMARIZING
ProcessingStatus.COMPLETED
ProcessingStatus.FAILED
ProcessingStatus.SKIPPED
```

---

## Workflow

### RAGWorkflowOrchestrator

```python
from workflows import RAGWorkflowOrchestrator, create_workflow

# Create workflow
workflow = create_workflow()
# or
workflow = RAGWorkflowOrchestrator()

# Run synchronously
final_state = workflow.run(
    data_directory="./data/diagrams",
    skip_existing=True,
    force_reprocess=False,
)

# Run with streaming
for output in workflow.run_with_streaming(
    data_directory="./data/diagrams",
):
    print(f"Phase: {output}")

# Get workflow visualization (Mermaid)
diagram = workflow.get_graph_visualization()
```

### Workflow State

```python
from workflows import RAGWorkflowState

# State contains all workflow data
state: RAGWorkflowState = {
    "data_directory": "./data",
    "documents": [...],
    "chunks_created": 45,
    "vectors_stored": 45,
    "errors": [],
    "is_complete": True,
}
```

---

## Utilities

### Logging

```python
from utils import setup_logging, get_logger, LogContext

# Setup structured logging
setup_logging(
    level="INFO",
    log_format="json",  # or "console"
    log_file=Path("./logs/app.log"),
)

# Get logger
logger = get_logger(__name__)
logger.info("Processing started", file="test.pdf")

# Timing context
with LogContext(logger, "process_document", file="test.pdf"):
    # ... processing ...
    pass
# Logs: "Starting process_document" and "Completed process_document (150ms)"
```

### File Utilities

```python
from utils import (
    compute_file_hash,
    get_mime_type,
    collect_files,
    create_file_metadata,
    truncate_text,
    SUPPORTED_EXTENSIONS,
)

# Hash a file
hash = compute_file_hash(Path("./file.pdf"))

# Get MIME type
mime = get_mime_type(Path("./file.pdf"))  # "application/pdf"

# Collect files from directory
files = collect_files(
    Path("./data"),
    recursive=True,
    include_hidden=False,
)

# Create metadata from path
metadata = create_file_metadata(Path("./file.pdf"))

# Truncate text
short = truncate_text("Long text...", max_length=100)

# Check supported extensions
SUPPORTED_EXTENSIONS  # {'.pdf', '.docx', '.png', ...}
```

### Health Checks

```python
from utils import (
    check_all_services,
    check_azure_openai_health,
    check_pinecone_health,
    check_google_vision_health,
    HealthStatus,
)

import asyncio

# Check all services
health = asyncio.run(check_all_services())
print(health.status)  # HealthStatus.HEALTHY

for service in health.services:
    print(f"{service.name}: {service.status} ({service.latency_ms}ms)")

# Individual checks
azure_health = asyncio.run(check_azure_openai_health())
pinecone_health = asyncio.run(check_pinecone_health())
```

---

## Configuration

### Settings Access

```python
from config import (
    get_settings,
    get_azure_settings,
    get_pinecone_settings,
    get_google_vision_settings,
    get_processing_settings,
)

# Full settings
settings = get_settings()
settings.azure_openai.api_key
settings.pinecone.index_name
settings.processing.chunk_size

# Service-specific settings
azure = get_azure_settings()
azure.endpoint
azure.embeddings_deployment

pinecone = get_pinecone_settings()
pinecone.api_key
pinecone.dimension
```

---

## Error Handling

All services implement consistent error handling:

```python
from models import ProcessingStatus

# Check document status after processing
if document.status == ProcessingStatus.FAILED:
    print(f"Error: {document.error_message}")

# Handle exceptions
try:
    result = query_service.query("question")
except Exception as e:
    logger.error(f"Query failed: {e}")
```

---

## Examples

### Complete Indexing Example

```python
from pathlib import Path
from workflows import create_workflow

# Create and run workflow
workflow = create_workflow()
result = workflow.run(
    data_directory="./data/diagrams",
    skip_existing=True,
)

print(f"Processed: {result['files_processed']}")
print(f"Vectors stored: {result['vectors_stored']}")
```

### Complete Query Example

```python
from services import RAGQueryService

# Initialize service
service = RAGQueryService()

# Ask question
result = service.query("What is the authentication flow?")

print(f"Answer: {result.answer}")
print(f"Sources:")
for source in result.sources:
    print(f"  - {source.metadata.file_name} ({source.score:.2f})")
```

### Custom Processing Pipeline

```python
from services import (
    DocumentScanner,
    ContentExtractor,
    AzureOpenAISummarizer,
    AzureOpenAIEmbeddingService,
    PineconeVectorStore,
    DocumentChunker,
)

# Initialize services
scanner = DocumentScanner()
extractor = ContentExtractor()
summarizer = AzureOpenAISummarizer()
chunker = DocumentChunker()
embedder = AzureOpenAIEmbeddingService()
store = PineconeVectorStore()
store.initialize()

# Process files
metadata_list = scanner.scan_directory(Path("./data"))
documents = scanner.create_documents(metadata_list)

for doc in documents:
    # Extract content
    doc = extractor.extract(doc)
    
    # Summarize
    doc = summarizer.summarize_document(doc)
    
    # Chunk
    chunks = chunker.chunk(doc)
    
    # Embed
    embedded = embedder.embed_chunks(chunks)
    
    # Store
    store.upsert(embedded, doc)
```
