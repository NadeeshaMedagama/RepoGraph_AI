# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Base Content Processor
# ═══════════════════════════════════════════════════════════════════════════════
# Abstract base class for content extraction following Strategy pattern.
# ═══════════════════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from typing import Set

from models import Document, FileCategory, FileType


class BaseProcessor(ABC):
    """
    Abstract base class for content processors.

    Implements the Strategy pattern to handle different file types.
    Each processor knows which file types it can handle and how to
    extract content from them.
    """

    @property
    @abstractmethod
    def supported_types(self) -> Set[FileType]:
        """Return set of file types this processor can handle."""
        pass

    @property
    @abstractmethod
    def category(self) -> FileCategory:
        """Return the file category this processor handles."""
        pass

    def can_process(self, document: Document) -> bool:
        """
        Check if this processor can handle the document.

        Args:
            document: Document to check

        Returns:
            True if this processor can handle the file type
        """
        return document.metadata.file_type in self.supported_types

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

    def _read_text_file(self, document: Document) -> str:
        """
        Read text content from a file with encoding detection.

        Args:
            document: Document to read

        Returns:
            Text content
        """
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(document.metadata.path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        # Fallback: read as binary and decode with errors ignored
        with open(document.metadata.path, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')
