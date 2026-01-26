# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Workflow Nodes
# ═══════════════════════════════════════════════════════════════════════════════
# LangGraph node functions for the RAG processing pipeline.
# ═══════════════════════════════════════════════════════════════════════════════

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from workflows.states import RAGWorkflowState
from services import (
    DocumentScanner,
    ContentExtractor,
    GoogleVisionService,
    AzureOpenAISummarizer,
    DocumentChunker,
    AzureOpenAIEmbeddingService,
    PineconeVectorStore,
)
from models import Document, ProcessingStatus, FileCategory
from utils import get_logger

logger = get_logger(__name__)


def initialize_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Initialize the workflow state.

    Sets up timing and initial state values.
    """
    logger.info("🚀 Initializing RAG workflow")

    return {
        "started_at": datetime.utcnow(),
        "current_phase": "initializing",
        "errors": [],
        "is_complete": False,
        "total_files_found": 0,
        "files_to_process": 0,
        "files_skipped": 0,
        "files_processed": 0,
        "files_failed": 0,
        "chunks_created": 0,
        "embeddings_created": 0,
        "vectors_stored": 0,
    }


def scan_directory_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Scan the data directory for files to process.
    """
    logger.info("📂 Scanning directory for files")

    data_dir = Path(state.get("data_directory", "./data/diagrams"))

    scanner = DocumentScanner(recursive=True)
    metadata_list = scanner.scan_directory(data_dir)

    logger.info(f"Found {len(metadata_list)} files")

    return {
        "file_metadata": metadata_list,
        "total_files_found": len(metadata_list),
        "current_phase": "scanned",
    }


def load_existing_records_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Load existing records from vector store for deduplication.
    """
    logger.info("🔍 Loading existing records for deduplication")

    if state.get("force_reprocess", False):
        logger.info("Force reprocess enabled - skipping deduplication")
        return {
            "existing_paths": set(),
            "existing_hashes": set(),
            "current_phase": "deduplication_loaded",
        }

    try:
        vector_store = PineconeVectorStore()
        vector_store.initialize()

        existing_paths = vector_store.get_existing_paths()
        existing_hashes = vector_store.get_existing_hashes()

        logger.info(
            f"Found {len(existing_paths)} existing paths, "
            f"{len(existing_hashes)} existing hashes"
        )

        return {
            "existing_paths": existing_paths,
            "existing_hashes": existing_hashes,
            "current_phase": "deduplication_loaded",
        }

    except Exception as e:
        logger.warning(f"Failed to load existing records: {e}")
        return {
            "existing_paths": set(),
            "existing_hashes": set(),
            "current_phase": "deduplication_loaded",
            "errors": state.get("errors", []) + [str(e)],
        }


def filter_documents_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Filter out already-indexed documents.
    """
    logger.info("🔄 Filtering documents")

    metadata_list = state.get("file_metadata", [])
    existing_paths = state.get("existing_paths", set())
    existing_hashes = state.get("existing_hashes", set())
    skip_existing = state.get("skip_existing", True)

    scanner = DocumentScanner()

    if skip_existing and (existing_paths or existing_hashes):
        new_files, skipped_files = scanner.filter_by_existing(
            metadata_list, existing_paths, existing_hashes
        )
    else:
        new_files = metadata_list
        skipped_files = []

    # Create Document objects for new files
    documents = scanner.create_documents(new_files)
    skipped_docs = scanner.create_documents(skipped_files)

    logger.info(
        f"📊 To process: {len(documents)}, Skipped: {len(skipped_docs)}"
    )

    return {
        "documents": documents,
        "new_documents": documents,
        "skipped_documents": skipped_docs,
        "files_to_process": len(documents),
        "files_skipped": len(skipped_docs),
        "current_phase": "filtered",
    }


def extract_content_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Extract content from all documents.
    """
    documents = state.get("documents", [])

    if not documents:
        logger.info("📭 No documents to extract")
        return {
            "extracted_documents": [],
            "current_phase": "extracted",
        }

    logger.info(f"📄 Extracting content from {len(documents)} documents")

    extractor = ContentExtractor()
    extracted = extractor.extract_batch(documents)

    success_count = sum(
        1 for d in extracted
        if d.status in (ProcessingStatus.COMPLETED, ProcessingStatus.ANALYZING)
    )

    logger.info(f"✅ Extracted: {success_count}/{len(documents)}")

    return {
        "extracted_documents": extracted,
        "current_phase": "extracted",
    }


def analyze_with_vision_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Analyze images and diagrams with Vision API.
    """
    documents = state.get("extracted_documents", [])

    # Filter documents that need vision analysis
    vision_docs = [
        d for d in documents
        if d.metadata.category in (FileCategory.IMAGE, FileCategory.DIAGRAM)
        and d.status == ProcessingStatus.ANALYZING
    ]

    if not vision_docs:
        logger.info("🖼️ No documents require vision analysis")
        return {
            "analyzed_documents": documents,
            "current_phase": "analyzed",
        }

    logger.info(f"🖼️ Analyzing {len(vision_docs)} images/diagrams with Vision API")

    vision_service = GoogleVisionService()

    for doc in vision_docs:
        try:
            vision_service.analyze_document(doc)
        except Exception as e:
            logger.error(f"Vision analysis failed for {doc.metadata.name}: {e}")
            doc.error_message = str(e)

    return {
        "analyzed_documents": documents,
        "current_phase": "analyzed",
    }


def summarize_documents_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Generate comprehensive summaries for all documents.
    """
    documents = state.get("analyzed_documents", [])

    # Filter successful documents
    valid_docs = [
        d for d in documents
        if d.status not in (ProcessingStatus.FAILED, ProcessingStatus.SKIPPED)
    ]

    if not valid_docs:
        logger.info("📝 No documents to summarize")
        return {
            "summarized_documents": documents,
            "current_phase": "summarized",
        }

    logger.info(f"📝 Summarizing {len(valid_docs)} documents")

    summarizer = AzureOpenAISummarizer()

    for doc in valid_docs:
        try:
            summarizer.summarize_document(doc)
        except Exception as e:
            logger.error(f"Summarization failed for {doc.metadata.name}: {e}")
            doc.error_message = str(e)

    return {
        "summarized_documents": documents,
        "current_phase": "summarized",
    }


def chunk_documents_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Chunk documents for embedding.
    """
    documents = state.get("summarized_documents", [])

    # Filter successful documents
    valid_docs = [
        d for d in documents
        if d.status not in (ProcessingStatus.FAILED, ProcessingStatus.SKIPPED)
    ]

    if not valid_docs:
        logger.info("📦 No documents to chunk")
        return {
            "all_chunks": [],
            "chunks_created": 0,
            "current_phase": "chunked",
        }

    logger.info(f"📦 Chunking {len(valid_docs)} documents")

    chunker = DocumentChunker()
    all_chunks = []

    for doc in valid_docs:
        chunks = chunker.chunk(doc)
        all_chunks.extend(chunks)

    logger.info(f"Created {len(all_chunks)} chunks")

    return {
        "all_chunks": all_chunks,
        "chunks_created": len(all_chunks),
        "current_phase": "chunked",
    }


def embed_chunks_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Generate embeddings for all chunks.
    """
    chunks = state.get("all_chunks", [])

    if not chunks:
        logger.info("🧠 No chunks to embed")
        return {
            "embedded_chunks": [],
            "embeddings_created": 0,
            "current_phase": "embedded",
        }

    logger.info(f"🧠 Generating embeddings for {len(chunks)} chunks")

    embedding_service = AzureOpenAIEmbeddingService()
    embedded_chunks = embedding_service.embed_chunks(chunks)

    logger.info(f"Generated {len(embedded_chunks)} embeddings")

    return {
        "embedded_chunks": embedded_chunks,
        "embeddings_created": len(embedded_chunks),
        "current_phase": "embedded",
    }


def store_vectors_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Store embedded chunks in Pinecone.
    """
    embedded_chunks = state.get("embedded_chunks", [])
    documents = state.get("summarized_documents", [])

    if not embedded_chunks:
        logger.info("💾 No vectors to store")
        return {
            "vectors_stored": 0,
            "current_phase": "stored",
        }

    logger.info(f"💾 Storing {len(embedded_chunks)} vectors in Pinecone")

    vector_store = PineconeVectorStore()
    vector_store.initialize()

    total_stored = 0

    # Group chunks by document
    doc_chunks = {}
    for ec in embedded_chunks:
        doc_id = str(ec.chunk.document_id)
        if doc_id not in doc_chunks:
            doc_chunks[doc_id] = []
        doc_chunks[doc_id].append(ec)

    # Store by document
    for doc in documents:
        doc_id = str(doc.id)
        if doc_id in doc_chunks:
            try:
                stored = vector_store.upsert(doc_chunks[doc_id], doc)
                total_stored += stored
            except Exception as e:
                logger.error(f"Failed to store vectors for {doc.metadata.name}: {e}")

    logger.info(f"Stored {total_stored} vectors")

    return {
        "vectors_stored": total_stored,
        "current_phase": "stored",
    }


def finalize_node(state: RAGWorkflowState) -> Dict[str, Any]:
    """
    Finalize the workflow and compute statistics.
    """
    logger.info("🏁 Finalizing workflow")

    documents = state.get("summarized_documents", [])

    # Count successes and failures
    files_processed = sum(
        1 for d in documents
        if d.status not in (ProcessingStatus.FAILED, ProcessingStatus.SKIPPED)
    )
    files_failed = sum(
        1 for d in documents
        if d.status == ProcessingStatus.FAILED
    )

    completed_at = datetime.utcnow()
    started_at = state.get("started_at", completed_at)
    duration = (completed_at - started_at).total_seconds()

    # Preserve statistics from previous nodes
    chunks_created = state.get('chunks_created', 0)
    embeddings_created = state.get('embeddings_created', 0)
    vectors_stored = state.get('vectors_stored', 0)

    logger.info(
        f"✨ Workflow complete!\n"
        f"   📁 Total files found: {state.get('total_files_found', 0)}\n"
        f"   ⏭️  Files skipped: {state.get('files_skipped', 0)}\n"
        f"   ✅ Files processed: {files_processed}\n"
        f"   ❌ Files failed: {files_failed}\n"
        f"   📦 Chunks created: {chunks_created}\n"
        f"   🧠 Embeddings: {embeddings_created}\n"
        f"   💾 Vectors stored: {vectors_stored}\n"
        f"   ⏱️  Duration: {duration:.2f}s"
    )

    return {
        "files_processed": files_processed,
        "files_failed": files_failed,
        "chunks_created": chunks_created,
        "embeddings_created": embeddings_created,
        "vectors_stored": vectors_stored,
        "completed_at": completed_at,
        "current_phase": "completed",
        "is_complete": True,
    }
