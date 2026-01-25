# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Data Models
# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic models representing domain entities following DDD principles.
# These models are immutable and provide validation and serialization.
# ═══════════════════════════════════════════════════════════════════════════════

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field


class FileType(str, Enum):
    """Enumeration of supported file types."""

    # Images
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    SVG = "svg"
    GIF = "gif"
    BMP = "bmp"
    WEBP = "webp"

    # Diagrams
    DRAWIO = "drawio"
    EXCALIDRAW = "excalidraw"

    # Documents
    DOCX = "docx"
    DOC = "doc"
    PDF = "pdf"
    PPTX = "pptx"
    PPT = "ppt"
    ODT = "odt"

    # Spreadsheets
    XLSX = "xlsx"
    XLS = "xls"

    # Structured Data
    JSON = "json"
    GRAPHQL = "graphql"
    GQL = "gql"

    # Markdown & Text
    MARKDOWN = "md"
    TXT = "txt"
    LOG = "log"

    # Config Files
    YAML = "yaml"
    YML = "yml"
    XML = "xml"
    INI = "ini"
    CFG = "cfg"
    CONF = "conf"
    ENV = "env"

    # Source Code
    PYTHON = "py"
    JAVASCRIPT = "js"
    TYPESCRIPT = "ts"
    JAVA = "java"
    GO = "go"
    RUST = "rs"
    C = "c"
    CPP = "cpp"
    H = "h"
    SHELL = "sh"
    SQL = "sql"
    HTML = "html"
    CSS = "css"

    # Video
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"

    # Unknown
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Status of document processing."""

    PENDING = "pending"
    SCANNING = "scanning"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    SUMMARIZING = "summarizing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FileCategory(str, Enum):
    """High-level file category for processing strategy."""

    IMAGE = "image"
    DIAGRAM = "diagram"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    STRUCTURED = "structured"
    CODE = "code"
    TEXT = "text"
    VIDEO = "video"
    UNKNOWN = "unknown"


class FileMetadata(BaseModel):
    """Metadata about a file."""

    path: Path
    name: str
    extension: str
    size_bytes: int
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    content_hash: str = ""
    mime_type: Optional[str] = None

    @computed_field
    @property
    def file_type(self) -> FileType:
        """Determine file type from extension."""
        ext = self.extension.lower().lstrip(".")
        try:
            return FileType(ext)
        except ValueError:
            return FileType.UNKNOWN

    @computed_field
    @property
    def category(self) -> FileCategory:
        """Determine file category from type."""
        image_types = {FileType.PNG, FileType.JPG, FileType.JPEG,
                       FileType.GIF, FileType.BMP, FileType.WEBP, FileType.SVG}
        diagram_types = {FileType.DRAWIO, FileType.EXCALIDRAW}
        document_types = {FileType.DOCX, FileType.DOC, FileType.PDF,
                         FileType.PPTX, FileType.PPT, FileType.ODT}
        spreadsheet_types = {FileType.XLSX, FileType.XLS}
        structured_types = {FileType.JSON, FileType.GRAPHQL, FileType.GQL,
                           FileType.YAML, FileType.YML, FileType.XML}
        code_types = {FileType.PYTHON, FileType.JAVASCRIPT, FileType.TYPESCRIPT,
                     FileType.JAVA, FileType.GO, FileType.RUST, FileType.C,
                     FileType.CPP, FileType.H, FileType.SHELL, FileType.SQL,
                     FileType.HTML, FileType.CSS}
        video_types = {FileType.MP4, FileType.AVI, FileType.MOV,
                      FileType.MKV, FileType.WEBM}
        text_types = {FileType.MARKDOWN, FileType.TXT, FileType.LOG,
                     FileType.INI, FileType.CFG, FileType.CONF, FileType.ENV}

        ft = self.file_type
        if ft in image_types:
            return FileCategory.IMAGE
        elif ft in diagram_types:
            return FileCategory.DIAGRAM
        elif ft in document_types:
            return FileCategory.DOCUMENT
        elif ft in spreadsheet_types:
            return FileCategory.SPREADSHEET
        elif ft in structured_types:
            return FileCategory.STRUCTURED
        elif ft in code_types:
            return FileCategory.CODE
        elif ft in video_types:
            return FileCategory.VIDEO
        elif ft in text_types:
            return FileCategory.TEXT
        return FileCategory.UNKNOWN


class Document(BaseModel):
    """
    Represents a document to be processed.

    This is the primary entity in the system, representing any file
    that will be analyzed, summarized, and embedded.
    """

    id: UUID = Field(default_factory=uuid4)
    metadata: FileMetadata
    raw_content: str = ""
    extracted_text: str = ""
    vision_analysis: Optional[str] = None
    summary: str = ""
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    processing_time_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def source_path(self) -> str:
        """Get the source path as string."""
        return str(self.metadata.path)

    @computed_field
    @property
    def display_name(self) -> str:
        """Get a display-friendly name."""
        return self.metadata.name

    def get_content_for_embedding(self) -> str:
        """
        Get the best available content for embedding.

        Priority: summary > vision_analysis > extracted_text > raw_content
        """
        if self.summary:
            return self.summary
        if self.vision_analysis:
            return self.vision_analysis
        if self.extracted_text:
            return self.extracted_text
        return self.raw_content


class Chunk(BaseModel):
    """
    A chunk of text from a document.

    Documents are split into chunks for better embedding quality
    and more precise retrieval.
    """

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str
    chunk_index: int
    total_chunks: int
    start_char: int = 0
    end_char: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def char_count(self) -> int:
        """Get the character count of the chunk."""
        return len(self.content)


class EmbeddedChunk(BaseModel):
    """
    A chunk with its embedding vector.

    Ready to be stored in the vector database.
    """

    chunk: Chunk
    embedding: List[float]
    embedding_model: str = "choreo-ai-embedding"

    @computed_field
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return len(self.embedding)


class VectorMetadata(BaseModel):
    """
    Metadata stored alongside vectors in Pinecone.

    This is the searchable and filterable information.
    """

    document_id: str
    chunk_id: str
    source_path: str
    file_name: str
    file_type: str
    category: str
    chunk_index: int
    total_chunks: int
    content_preview: str = ""  # First 500 chars
    content_hash: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pinecone."""
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "source_path": self.source_path,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "category": self.category,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "content_preview": self.content_preview[:500],
            "content_hash": self.content_hash,
            "created_at": self.created_at,
        }


class SearchResult(BaseModel):
    """Result from vector similarity search."""

    id: str
    score: float
    metadata: VectorMetadata
    content: str = ""


class QueryResult(BaseModel):
    """Complete result from a RAG query."""

    query: str
    answer: str
    sources: List[SearchResult]
    model_used: str
    processing_time_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
