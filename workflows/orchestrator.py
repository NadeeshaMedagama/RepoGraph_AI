# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Workflow Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════
# LangGraph-based workflow orchestration for the RAG pipeline.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Dict, Any, Optional
from pathlib import Path

from langgraph.graph import StateGraph, END

from workflows.states import RAGWorkflowState
from workflows.nodes import (
    initialize_node,
    scan_directory_node,
    load_existing_records_node,
    filter_documents_node,
    extract_content_node,
    analyze_with_vision_node,
    summarize_documents_node,
    chunk_documents_node,
    embed_chunks_node,
    store_vectors_node,
    finalize_node,
)
from config import get_processing_settings
from utils import get_logger

logger = get_logger(__name__)


class RAGWorkflowOrchestrator:
    """
    LangGraph-based workflow orchestrator for RAG processing.

    Orchestrates the complete document processing pipeline:
    1. Scan directory for files
    2. Load existing records for deduplication
    3. Filter out already-indexed documents
    4. Extract content from documents
    5. Analyze images/diagrams with Vision API
    6. Generate comprehensive summaries
    7. Chunk documents for embedding
    8. Generate embeddings
    9. Store vectors in Pinecone
    """

    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        # Create the graph
        graph = StateGraph(RAGWorkflowState)

        # Add nodes
        graph.add_node("initialize", initialize_node)
        graph.add_node("scan_directory", scan_directory_node)
        graph.add_node("load_existing", load_existing_records_node)
        graph.add_node("filter_documents", filter_documents_node)
        graph.add_node("extract_content", extract_content_node)
        graph.add_node("analyze_vision", analyze_with_vision_node)
        graph.add_node("summarize", summarize_documents_node)
        graph.add_node("chunk", chunk_documents_node)
        graph.add_node("embed", embed_chunks_node)
        graph.add_node("store", store_vectors_node)
        graph.add_node("finalize", finalize_node)

        # Define the flow
        graph.set_entry_point("initialize")

        graph.add_edge("initialize", "scan_directory")
        graph.add_edge("scan_directory", "load_existing")
        graph.add_edge("load_existing", "filter_documents")

        # Conditional edge: skip processing if no new documents
        graph.add_conditional_edges(
            "filter_documents",
            self._should_continue_processing,
            {
                "continue": "extract_content",
                "skip": "finalize",
            }
        )

        graph.add_edge("extract_content", "analyze_vision")
        graph.add_edge("analyze_vision", "summarize")
        graph.add_edge("summarize", "chunk")
        graph.add_edge("chunk", "embed")
        graph.add_edge("embed", "store")
        graph.add_edge("store", "finalize")
        graph.add_edge("finalize", END)

        return graph

    def _should_continue_processing(self, state: RAGWorkflowState) -> str:
        """Determine if we should continue processing or skip."""
        files_to_process = state.get("files_to_process", 0)

        if files_to_process == 0:
            logger.info("📭 No new documents to process - skipping to finalize")
            return "skip"

        return "continue"

    def run(
        self,
        data_directory: Optional[str] = None,
        skip_existing: bool = True,
        force_reprocess: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the complete RAG workflow.

        Args:
            data_directory: Directory containing files to process
            skip_existing: Skip already indexed documents
            force_reprocess: Force reprocess all documents

        Returns:
            Final workflow state
        """
        settings = get_processing_settings()

        # Build initial state
        initial_state: RAGWorkflowState = {
            "data_directory": data_directory or str(settings.data_directory),
            "skip_existing": skip_existing and not force_reprocess,
            "force_reprocess": force_reprocess,
        }

        logger.info(
            "🚀 Starting RAG workflow",
            data_directory=initial_state["data_directory"],
            skip_existing=initial_state["skip_existing"],
        )

        # Run the workflow
        final_state = self.app.invoke(initial_state)

        return final_state

    def run_with_streaming(
        self,
        data_directory: Optional[str] = None,
        skip_existing: bool = True,
        force_reprocess: bool = False,
    ):
        """
        Run the workflow with streaming updates.

        Yields state updates as each node completes.

        Args:
            data_directory: Directory containing files to process
            skip_existing: Skip already indexed documents
            force_reprocess: Force reprocess all documents

        Yields:
            State updates from each node
        """
        settings = get_processing_settings()

        initial_state: RAGWorkflowState = {
            "data_directory": data_directory or str(settings.data_directory),
            "skip_existing": skip_existing and not force_reprocess,
            "force_reprocess": force_reprocess,
        }

        # Stream the workflow
        for output in self.app.stream(initial_state):
            yield output

    def get_graph_visualization(self) -> str:
        """
        Get a Mermaid diagram of the workflow graph.

        Returns:
            Mermaid diagram string
        """
        try:
            return self.app.get_graph().draw_mermaid()
        except Exception:
            # Fallback: manual diagram
            return """
```mermaid
graph TD
    A[Initialize] --> B[Scan Directory]
    B --> C[Load Existing Records]
    C --> D[Filter Documents]
    D -->|Has Documents| E[Extract Content]
    D -->|No Documents| J[Finalize]
    E --> F[Analyze with Vision]
    F --> G[Summarize]
    G --> H[Chunk Documents]
    H --> I[Generate Embeddings]
    I --> K[Store in Pinecone]
    K --> J
```
"""


def create_workflow() -> RAGWorkflowOrchestrator:
    """Create and return a configured workflow orchestrator."""
    return RAGWorkflowOrchestrator()
