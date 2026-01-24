#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - REST API Server
# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI-based REST API for programmatic access to the RAG system.
# ═══════════════════════════════════════════════════════════════════════════════

from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import get_settings
from services import RAGQueryService, PineconeVectorStore
from utils import setup_logging, check_all_services, HealthStatus

# Initialize
setup_logging(level="INFO")
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="RepoGraph AI API",
    description="Enterprise-Grade Intelligent Document Processing & RAG System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    question: str = Field(..., description="Question to ask", min_length=1)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of sources")


class SearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")
    file_type: Optional[str] = Field(default=None, description="Filter by file type")
    category: Optional[str] = Field(default=None, description="Filter by category")


class SourceDocument(BaseModel):
    """Source document in response."""
    file_name: str
    file_type: str
    category: str
    score: float
    content_preview: str


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer: str
    sources: List[SourceDocument]
    query: str
    model_used: str
    processing_time_ms: int


class SearchResponse(BaseModel):
    """Response model for semantic search."""
    results: List[SourceDocument]
    query: str
    total_results: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    services: Dict[str, Dict[str, Any]]
    version: str
    timestamp: str


class StatsResponse(BaseModel):
    """Index statistics response."""
    index_name: str
    dimension: int
    total_vectors: int
    namespaces: Dict[str, Any]


class IndexRequest(BaseModel):
    """Request model for indexing."""
    directory: Optional[str] = Field(default=None, description="Directory to index")
    force_reprocess: bool = Field(default=False, description="Force reprocess all")


class IndexResponse(BaseModel):
    """Response model for indexing status."""
    status: str
    message: str
    job_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Service Instances
# ═══════════════════════════════════════════════════════════════════════════════

# Lazy initialization
_query_service: Optional[RAGQueryService] = None
_vector_store: Optional[PineconeVectorStore] = None


def get_query_service() -> RAGQueryService:
    """Get or create query service."""
    global _query_service
    if _query_service is None:
        _query_service = RAGQueryService()
    return _query_service


def get_vector_store() -> PineconeVectorStore:
    """Get or create vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = PineconeVectorStore()
        _vector_store.initialize()
    return _vector_store


# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RepoGraph AI API",
        "version": "1.0.0",
        "description": "Enterprise-Grade Intelligent Document Processing & RAG System",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Check health of all services.

    Returns the status of Azure OpenAI, Pinecone, and Google Vision.
    """
    import asyncio

    health = await check_all_services()

    services = {}
    for service in health.services:
        services[service.name] = {
            "status": service.status.value,
            "latency_ms": service.latency_ms,
            "message": service.message,
        }

    return HealthResponse(
        status=health.status.value,
        services=services,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/stats", response_model=StatsResponse, tags=["Info"])
async def get_stats():
    """
    Get index statistics.

    Returns information about the Pinecone index including vector count.
    """
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_stats()

        return StatsResponse(
            index_name=stats.get("index_name", ""),
            dimension=stats.get("dimension", 0),
            total_vectors=stats.get("total_vectors", 0),
            namespaces=stats.get("namespaces", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query(request: QueryRequest):
    """
    Ask a question using RAG.

    Retrieves relevant documents and generates an answer using the LLM.
    """
    try:
        service = get_query_service()
        result = service.query(
            question=request.question,
            top_k=request.top_k,
        )

        sources = [
            SourceDocument(
                file_name=s.metadata.file_name,
                file_type=s.metadata.file_type,
                category=s.metadata.category,
                score=s.score,
                content_preview=s.metadata.content_preview[:200],
            )
            for s in result.sources
        ]

        return QueryResponse(
            answer=result.answer,
            sources=sources,
            query=result.query,
            model_used=result.model_used,
            processing_time_ms=result.processing_time_ms,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest):
    """
    Perform semantic search.

    Search for documents matching the query without generating an answer.
    """
    try:
        service = get_query_service()

        # Build filter if provided
        filter_dict = {}
        if request.file_type:
            filter_dict["file_type"] = request.file_type
        if request.category:
            filter_dict["category"] = request.category

        if filter_dict:
            results = service.search_by_filter(
                query=request.query,
                filter=filter_dict,
                top_k=request.top_k,
            )
        else:
            results = service.search(
                query=request.query,
                top_k=request.top_k,
            )

        sources = [
            SourceDocument(
                file_name=r.metadata.file_name,
                file_type=r.metadata.file_type,
                category=r.metadata.category,
                score=r.score,
                content_preview=r.metadata.content_preview[:200],
            )
            for r in results
        ]

        return SearchResponse(
            results=sources,
            query=request.query,
            total_results=len(sources),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index", response_model=IndexResponse, tags=["Indexing"])
async def start_indexing(
    request: IndexRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start document indexing.

    Triggers the indexing workflow in the background.
    """
    import uuid

    job_id = str(uuid.uuid4())

    def run_indexing():
        from workflows import create_workflow

        workflow = create_workflow()
        workflow.run(
            data_directory=request.directory,
            force_reprocess=request.force_reprocess,
        )

    background_tasks.add_task(run_indexing)

    return IndexResponse(
        status="started",
        message="Indexing job started in background",
        job_id=job_id,
    )


@app.get("/supported-types", tags=["Info"])
async def get_supported_types():
    """
    Get list of supported file types.

    Returns all file extensions that can be processed.
    """
    from utils import SUPPORTED_EXTENSIONS
    from models import FileType, FileCategory

    # Group by category
    categories = {}
    for ext in SUPPORTED_EXTENSIONS:
        # Simplified categorization
        if ext in {'.png', '.jpg', '.jpeg', '.svg', '.gif', '.bmp', '.webp'}:
            cat = 'image'
        elif ext in {'.drawio', '.excalidraw'}:
            cat = 'diagram'
        elif ext in {'.docx', '.doc', '.pdf', '.pptx', '.ppt', '.odt'}:
            cat = 'document'
        elif ext in {'.xlsx', '.xls'}:
            cat = 'spreadsheet'
        elif ext in {'.json', '.graphql', '.gql', '.yaml', '.yml', '.xml'}:
            cat = 'structured'
        elif ext in {'.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp',
                     '.h', '.sh', '.sql', '.html', '.css'}:
            cat = 'code'
        elif ext in {'.md', '.txt', '.log'}:
            cat = 'text'
        elif ext in {'.mp4', '.avi', '.mov', '.mkv', '.webm'}:
            cat = 'video'
        else:
            cat = 'other'

        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ext)

    return {
        "total_extensions": len(SUPPORTED_EXTENSIONS),
        "categories": categories,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Startup/Shutdown Events
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Pre-initialize services for faster first request
    try:
        get_vector_store()
    except Exception as e:
        print(f"Warning: Failed to initialize vector store: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
        reload=True,  # Enable for development
    )
