# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Document Chunker Service
# ═══════════════════════════════════════════════════════════════════════════════
# Intelligent text chunking for optimal embedding and retrieval.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import List, Dict, Any, Optional
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

from interfaces import IChunker
from models import Document, Chunk
from config import get_processing_settings
from utils import get_logger

logger = get_logger(__name__)


class DocumentChunker(IChunker):
    """
    Document chunking service.

    Splits documents into manageable chunks with configurable
    size and overlap, optimized for embedding and retrieval.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        settings = get_processing_settings()

        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Initialize the text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Paragraphs
                "\n",    # Lines
                ". ",    # Sentences
                ", ",    # Clauses
                " ",     # Words
                "",      # Characters
            ],
        )

    def chunk(self, document: Document) -> List[Chunk]:
        """
        Split a document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of chunks
        """
        # Get the best content for chunking
        content = document.get_content_for_embedding()

        if not content or len(content.strip()) < 10:
            return []

        # Build metadata
        metadata = {
            "document_id": str(document.id),
            "source_path": str(document.metadata.path),
            "file_name": document.metadata.name,
            "file_type": document.metadata.file_type.value,
            "category": document.metadata.category.value,
            "content_hash": document.metadata.content_hash,
        }

        return self.chunk_text(content, metadata)

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Chunk raw text with metadata.

        Args:
            text: Text to chunk
            metadata: Metadata to attach to chunks

        Returns:
            List of chunks
        """
        if not text or len(text.strip()) < 10:
            return []

        # Split the text
        split_texts = self.splitter.split_text(text)

        if not split_texts:
            return []

        # Create Chunk objects
        chunks = []
        current_position = 0

        for i, chunk_text in enumerate(split_texts):
            # Find position in original text
            start_pos = text.find(chunk_text, current_position)
            if start_pos == -1:
                start_pos = current_position
            end_pos = start_pos + len(chunk_text)
            current_position = start_pos + 1  # Move past for next search

            chunk = Chunk(
                id=uuid4(),
                document_id=uuid4() if "document_id" not in metadata
                           else metadata["document_id"],
                content=chunk_text,
                chunk_index=i,
                total_chunks=len(split_texts),
                start_char=start_pos,
                end_char=end_pos,
                metadata=metadata.copy(),
            )
            chunks.append(chunk)

        logger.debug(
            "Text chunked",
            input_length=len(text),
            num_chunks=len(chunks),
            avg_chunk_size=len(text) // len(chunks) if chunks else 0,
        )

        return chunks

    def chunk_documents(self, documents: List[Document]) -> Dict[str, List[Chunk]]:
        """
        Chunk multiple documents.

        Args:
            documents: Documents to chunk

        Returns:
            Dictionary mapping document IDs to their chunks
        """
        result = {}
        total_chunks = 0

        for doc in documents:
            chunks = self.chunk(doc)
            result[str(doc.id)] = chunks
            total_chunks += len(chunks)

        logger.info(
            "Documents chunked",
            num_documents=len(documents),
            total_chunks=total_chunks,
        )

        return result

    def estimate_chunks(self, text: str) -> int:
        """
        Estimate the number of chunks for a text.

        Args:
            text: Text to estimate

        Returns:
            Estimated number of chunks
        """
        if not text:
            return 0

        # Simple estimation based on chunk size and overlap
        effective_size = self.chunk_size - self.chunk_overlap
        return max(1, len(text) // effective_size)
