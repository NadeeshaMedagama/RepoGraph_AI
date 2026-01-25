# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Workflow State Definitions
# ═══════════════════════════════════════════════════════════════════════════════
# TypedDict definitions for LangGraph workflow state management.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import TypedDict, List, Set, Optional, Any
from datetime import datetime


class RAGWorkflowState(TypedDict, total=False):
    """
    State container for the RAG processing workflow.

    This TypedDict is used by LangGraph for state management
    across workflow nodes.
    """

    # Configuration
    data_directory: str
    skip_existing: bool
    force_reprocess: bool

    # Discovery phase
    discovered_files: List[str]
    file_metadata: List[Any]  # FileMetadata objects

    # Documents at various stages
    documents: List[Any]  # Document objects
    extracted_documents: List[Any]
    analyzed_documents: List[Any]
    summarized_documents: List[Any]

    # Chunks and embeddings
    all_chunks: List[Any]  # Chunk objects
    embedded_chunks: List[Any]  # EmbeddedChunk objects

    # Deduplication
    existing_paths: Set[str]
    existing_hashes: Set[str]
    new_documents: List[Any]
    skipped_documents: List[Any]

    # Statistics
    total_files_found: int
    files_to_process: int
    files_skipped: int
    files_processed: int
    files_failed: int
    chunks_created: int
    embeddings_created: int
    vectors_stored: int

    # Timing
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Status and errors
    current_phase: str
    errors: List[str]
    is_complete: bool
