# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Workflow State Models
# ═══════════════════════════════════════════════════════════════════════════════
# State definitions for LangGraph workflow orchestration.
# ═══════════════════════════════════════════════════════════════════════════════

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from models.document import Document, EmbeddedChunk, ProcessingStatus


class WorkflowState(BaseModel):
    """
    State container for the RAG processing workflow.

    This is passed between LangGraph nodes and maintains
    all state needed for the processing pipeline.
    """

    # Input configuration
    data_directory: str = ""
    process_urls: bool = False
    url_list: List[str] = Field(default_factory=list)

    # Documents at various stages
    discovered_files: List[str] = Field(default_factory=list)
    documents: List[Document] = Field(default_factory=list)
    processed_documents: List[Document] = Field(default_factory=list)

    # Chunks and embeddings
    chunks: List[Any] = Field(default_factory=list)  # Chunk objects
    embedded_chunks: List[EmbeddedChunk] = Field(default_factory=list)

    # Deduplication tracking
    existing_hashes: Set[str] = Field(default_factory=set)
    existing_paths: Set[str] = Field(default_factory=set)

    # Processing statistics
    total_files_found: int = 0
    files_skipped: int = 0
    files_processed: int = 0
    files_failed: int = 0
    chunks_created: int = 0
    embeddings_created: int = 0
    vectors_stored: int = 0

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error handling
    errors: List[str] = Field(default_factory=list)
    current_status: ProcessingStatus = ProcessingStatus.PENDING

    # Configuration flags
    skip_existing: bool = True
    force_reprocess: bool = False

    class Config:
        arbitrary_types_allowed = True


class WorkflowResult(BaseModel):
    """Final result of workflow execution."""

    success: bool
    message: str
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    duration_seconds: float = 0.0

    @classmethod
    def from_state(cls, state: WorkflowState) -> "WorkflowResult":
        """Create result from workflow state."""
        duration = 0.0
        if state.started_at and state.completed_at:
            duration = (state.completed_at - state.started_at).total_seconds()

        return cls(
            success=len(state.errors) == 0,
            message="Workflow completed successfully" if not state.errors else "Workflow completed with errors",
            statistics={
                "total_files_found": state.total_files_found,
                "files_skipped": state.files_skipped,
                "files_processed": state.files_processed,
                "files_failed": state.files_failed,
                "chunks_created": state.chunks_created,
                "embeddings_created": state.embeddings_created,
                "vectors_stored": state.vectors_stored,
            },
            errors=state.errors,
            duration_seconds=duration,
        )
