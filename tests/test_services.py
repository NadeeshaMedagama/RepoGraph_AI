# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Unit Tests for Services
# ═══════════════════════════════════════════════════════════════════════════════

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from models.document import (
    FileMetadata,
    Document,
    Chunk,
    FileType,
    ProcessingStatus,
)


class TestDocumentScanner:
    """Tests for DocumentScanner service."""

    def test_scan_directory(self, tmp_path):
        """Test scanning a directory for files."""
        from services.document_scanner import DocumentScanner

        # Create test files
        (tmp_path / "test.txt").write_text("test")
        (tmp_path / "test.pdf").write_bytes(b"pdf content")
        (tmp_path / "test.py").write_text("print('hello')")

        scanner = DocumentScanner()
        metadata_list = scanner.scan_directory(tmp_path)

        assert len(metadata_list) == 3
        assert scanner.scanned_count == 3

    def test_scan_directory_recursive(self, tmp_path):
        """Test recursive directory scanning."""
        from services.document_scanner import DocumentScanner

        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.txt").write_text("root")
        (subdir / "nested.txt").write_text("nested")

        scanner = DocumentScanner(recursive=True)
        metadata_list = scanner.scan_directory(tmp_path)

        assert len(metadata_list) == 2

    def test_scan_nonexistent_directory(self, tmp_path):
        """Test scanning a non-existent directory."""
        from services.document_scanner import DocumentScanner

        scanner = DocumentScanner()
        metadata_list = scanner.scan_directory(tmp_path / "nonexistent")

        assert len(metadata_list) == 0

    def test_get_file_hash(self, tmp_path):
        """Test file hash generation."""
        from services.document_scanner import DocumentScanner

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        scanner = DocumentScanner()
        hash1 = scanner.get_file_hash(test_file)
        hash2 = scanner.get_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_filter_by_existing(self, tmp_path):
        """Test filtering existing documents."""
        from services.document_scanner import DocumentScanner

        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        scanner = DocumentScanner()
        metadata_list = scanner.scan_directory(tmp_path)

        existing_paths = {str(file1)}
        new_files, skipped = scanner.filter_by_existing(
            metadata_list, existing_paths, set()
        )

        assert len(new_files) == 1
        assert len(skipped) == 1


class TestContentExtractor:
    """Tests for ContentExtractor service."""

    def test_can_process(self, tmp_path):
        """Test checking if file can be processed."""
        from services.content_extractor import ContentExtractor

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        metadata = FileMetadata(
            path=test_file,
            name="test.txt",
            extension=".txt",
            size_bytes=4,
        )

        extractor = ContentExtractor()
        assert extractor.can_process(metadata) is True

    def test_extract_text_file(self, tmp_path):
        """Test extracting content from text file."""
        from services.content_extractor import ContentExtractor

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        metadata = FileMetadata(
            path=test_file,
            name="test.txt",
            extension=".txt",
            size_bytes=13,
        )
        doc = Document(metadata=metadata)

        extractor = ContentExtractor()
        result = extractor.extract(doc)

        assert "Hello, World!" in result.extracted_text

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        from services.content_extractor import ContentExtractor

        extractor = ContentExtractor()
        extensions = extractor.get_supported_extensions()

        assert ".txt" in extensions
        assert ".pdf" in extensions
        assert ".py" in extensions
        assert len(extensions) > 20


class TestDocumentChunker:
    """Tests for DocumentChunker service."""

    def test_chunk_text(self):
        """Test chunking text."""
        from services.chunker_service import DocumentChunker

        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)

        long_text = "This is a test. " * 50
        chunks = chunker.chunk_text(long_text, {"source": "test"})

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 100 + 50  # Allow some flexibility

    def test_chunk_short_text(self):
        """Test chunking short text."""
        from services.chunker_service import DocumentChunker

        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)

        short_text = "Short text."
        chunks = chunker.chunk_text(short_text, {"source": "test"})

        assert len(chunks) == 1
        assert chunks[0].content == "Short text."

    def test_estimate_chunks(self):
        """Test chunk estimation."""
        from services.chunker_service import DocumentChunker

        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)

        text = "x" * 500
        estimate = chunker.estimate_chunks(text)

        assert estimate >= 5


class TestEmbeddingService:
    """Tests for AzureOpenAIEmbeddingService."""

    @patch('services.embedding_service.AzureOpenAI')
    def test_embed_single(self, mock_azure):
        """Test embedding a single text."""
        from services.embedding_service import AzureOpenAIEmbeddingService

        # Mock the response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_azure.return_value.embeddings.create.return_value = mock_response

        service = AzureOpenAIEmbeddingService(
            api_key="test",
            endpoint="https://test.openai.azure.com/",
            deployment="test-model",
        )

        embedding = service.embed("test text")

        assert len(embedding) == 1536

    def test_embed_empty_text(self):
        """Test embedding empty text returns zero vector."""
        from services.embedding_service import AzureOpenAIEmbeddingService

        service = AzureOpenAIEmbeddingService(
            api_key="test",
            endpoint="https://test.openai.azure.com/",
            deployment="test-model",
        )

        embedding = service.embed("")

        assert len(embedding) == 1536
        assert all(v == 0.0 for v in embedding)


class TestVectorStore:
    """Tests for PineconeVectorStore."""

    @patch('services.vector_store.Pinecone')
    def test_initialize(self, mock_pinecone):
        """Test vector store initialization."""
        from services.vector_store import PineconeVectorStore

        # Mock the Pinecone client
        mock_pc = Mock()
        mock_pc.list_indexes.return_value = []
        mock_pinecone.return_value = mock_pc

        store = PineconeVectorStore(
            api_key="test",
            index_name="test-index",
        )

        # Should create index since it doesn't exist
        store.initialize()

        mock_pc.create_index.assert_called_once()

    def test_get_existing_paths(self):
        """Test getting existing paths."""
        from services.vector_store import PineconeVectorStore

        store = PineconeVectorStore(
            api_key="test",
            index_name="test-index",
        )
        store._existing_paths = {"/path/to/file1", "/path/to/file2"}

        paths = store.get_existing_paths()

        assert len(paths) == 2
        assert "/path/to/file1" in paths
