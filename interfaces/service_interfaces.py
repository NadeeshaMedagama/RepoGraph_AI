# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Service Interfaces
# ═══════════════════════════════════════════════════════════════════════════════
# Abstract base classes defining service contracts.
# Follows Interface Segregation Principle (ISP) and Dependency Inversion (DIP).
# ═══════════════════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.document import (
    Document,
    Chunk,
    EmbeddedChunk,
    FileMetadata,
    SearchResult,
    QueryResult,
)


class IDocumentScanner(ABC):
    """
    Interface for document scanning and discovery.

    Responsible for finding and cataloging files in a directory.
    """

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


class IContentExtractor(ABC):
    """
    Interface for content extraction from files.

    Implementations handle specific file types (images, documents, etc.)
    """

    @abstractmethod
    def can_process(self, file_metadata: FileMetadata) -> bool:
        """
        Check if this extractor can process the given file.

        Args:
            file_metadata: Metadata about the file

        Returns:
            True if this extractor can handle the file type
        """
        pass

    @abstractmethod
    def extract(self, document: Document) -> Document:
        """
        Extract content from a document.

        Args:
            document: Document to process

        Returns:
            Document with extracted_text populated
        """
        pass


class IVisionAnalyzer(ABC):
    """
    Interface for vision-based content analysis.

    Uses AI vision models to analyze images and diagrams.
    """

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
        """
        Perform OCR on an image.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text from the image
        """
        pass


class ISummarizer(ABC):
    """
    Interface for text summarization.

    Creates comprehensive summaries of document content.
    """

    @abstractmethod
    def summarize(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a comprehensive summary of the text.

        Args:
            text: Text to summarize
            context: Optional context about the document

        Returns:
            Comprehensive summary
        """
        pass

    @abstractmethod
    def summarize_document(self, document: Document) -> Document:
        """
        Generate a summary for a document.

        Args:
            document: Document to summarize

        Returns:
            Document with summary field populated
        """
        pass


class IChunker(ABC):
    """
    Interface for text chunking.

    Splits documents into manageable chunks for embedding.
    """

    @abstractmethod
    def chunk(self, document: Document) -> List[Chunk]:
        """
        Split a document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of chunks
        """
        pass

    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Chunk raw text.

        Args:
            text: Text to chunk
            metadata: Metadata to attach to chunks

        Returns:
            List of chunks
        """
        pass


class IEmbeddingService(ABC):
    """
    Interface for text embedding.

    Converts text to vector embeddings.
    """

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def embed_chunks(self, chunks: List[Chunk]) -> List[EmbeddedChunk]:
        """
        Embed a list of chunks.

        Args:
            chunks: Chunks to embed

        Returns:
            Embedded chunks
        """
        pass


class IVectorStore(ABC):
    """
    Interface for vector database operations.

    Handles storage and retrieval of embeddings.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the vector store connection."""
        pass

    @abstractmethod
    def upsert(self, embedded_chunks: List[EmbeddedChunk], document: Document) -> int:
        """
        Store embedded chunks in the vector database.

        Args:
            embedded_chunks: Chunks with embeddings
            document: Source document

        Returns:
            Number of vectors stored
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def get_existing_paths(self) -> set:
        """
        Get all indexed file paths.

        Returns:
            Set of indexed file paths
        """
        pass

    @abstractmethod
    def get_existing_hashes(self) -> set:
        """
        Get all indexed content hashes.

        Returns:
            Set of content hashes
        """
        pass

    @abstractmethod
    def delete_by_path(self, path: str) -> int:
        """
        Delete vectors for a specific file path.

        Args:
            path: File path to delete

        Returns:
            Number of vectors deleted
        """
        pass


class IQueryService(ABC):
    """
    Interface for RAG query operations.

    Combines search and generation for Q&A.
    """

    @abstractmethod
    def query(self, question: str, top_k: int = 5) -> QueryResult:
        """
        Answer a question using RAG.

        Args:
            question: User's question
            top_k: Number of context documents to use

        Returns:
            Query result with answer and sources
        """
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Perform semantic search without generation.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Search results
        """
        pass
