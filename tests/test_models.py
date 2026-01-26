# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Unit Tests for Models
# ═══════════════════════════════════════════════════════════════════════════════

from uuid import uuid4

from models.document import (
    FileType,
    FileCategory,
    ProcessingStatus,
    FileMetadata,
    Document,
    Chunk,
    EmbeddedChunk,
    VectorMetadata,
    SearchResult,
    QueryResult,
)


class TestFileType:
    """Tests for FileType enum."""

    def test_file_type_values(self):
        """Test that all expected file types exist."""
        assert FileType.PDF.value == "pdf"
        assert FileType.DOCX.value == "docx"
        assert FileType.PNG.value == "png"
        assert FileType.PYTHON.value == "py"

    def test_file_type_enum_membership(self):
        """Test file type enum membership."""
        assert FileType.PDF in FileType
        assert FileType.PYTHON in FileType
        assert "pdf" == FileType.PDF.value


class TestFileCategory:
    """Tests for FileCategory enum."""

    def test_file_category_values(self):
        """Test that all expected categories exist."""
        assert FileCategory.IMAGE.value == "image"
        assert FileCategory.DOCUMENT.value == "document"
        assert FileCategory.CODE.value == "code"


class TestFileMetadata:
    """Tests for FileMetadata model."""

    def test_file_metadata_creation(self, tmp_path):
        """Test creating file metadata."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        metadata = FileMetadata(
            path=test_file,
            name="test.txt",
            extension=".txt",
            size_bytes=12,
        )

        assert metadata.name == "test.txt"
        assert metadata.extension == ".txt"
        assert metadata.size_bytes == 12

    def test_file_type_detection(self, tmp_path):
        """Test automatic file type detection."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf content")

        metadata = FileMetadata(
            path=test_file,
            name="test.pdf",
            extension=".pdf",
            size_bytes=100,
        )

        assert metadata.file_type == FileType.PDF
        assert metadata.category == FileCategory.DOCUMENT


class TestDocument:
    """Tests for Document model."""

    def test_document_creation(self, tmp_path):
        """Test creating a document."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        metadata = FileMetadata(
            path=test_file,
            name="test.md",
            extension=".md",
            size_bytes=6,
        )

        doc = Document(metadata=metadata)

        assert doc.metadata.name == "test.md"
        assert doc.status == ProcessingStatus.PENDING
        assert doc.id is not None

    def test_document_get_content(self, tmp_path):
        """Test getting content for embedding."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        metadata = FileMetadata(
            path=test_file,
            name="test.md",
            extension=".md",
            size_bytes=6,
        )

        doc = Document(
            metadata=metadata,
            summary="Test summary",
            extracted_text="Extracted text",
        )

        # Summary should be preferred
        content = doc.get_content_for_embedding()
        assert content == "Test summary"


class TestChunk:
    """Tests for Chunk model."""

    def test_chunk_creation(self):
        """Test creating a chunk."""
        chunk = Chunk(
            document_id=uuid4(),
            content="This is a test chunk",
            chunk_index=0,
            total_chunks=5,
            start_char=0,
            end_char=20,
        )

        assert chunk.content == "This is a test chunk"
        assert chunk.chunk_index == 0
        assert chunk.char_count == 20


class TestEmbeddedChunk:
    """Tests for EmbeddedChunk model."""

    def test_embedded_chunk_creation(self):
        """Test creating an embedded chunk."""
        chunk = Chunk(
            document_id=uuid4(),
            content="Test",
            chunk_index=0,
            total_chunks=1,
        )

        embedded = EmbeddedChunk(
            chunk=chunk,
            embedding=[0.1] * 1536,
            embedding_model="test-model",
        )

        assert embedded.dimension == 1536
        assert embedded.embedding_model == "test-model"


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        metadata = VectorMetadata(
            document_id="doc1",
            chunk_id="chunk1",
            source_path="/path/to/file",
            file_name="test.pdf",
            file_type="pdf",
            category="document",
            chunk_index=0,
            total_chunks=1,
        )

        result = SearchResult(
            id="vec1",
            score=0.95,
            metadata=metadata,
            content="Test content",
        )

        assert result.score == 0.95
        assert result.metadata.file_name == "test.pdf"


class TestQueryResult:
    """Tests for QueryResult model."""

    def test_query_result_creation(self):
        """Test creating a query result."""
        result = QueryResult(
            query="What is this?",
            answer="This is the answer.",
            sources=[],
            model_used="gpt-4",
            processing_time_ms=150,
        )

        assert result.query == "What is this?"
        assert result.answer == "This is the answer."
        assert result.processing_time_ms == 150
