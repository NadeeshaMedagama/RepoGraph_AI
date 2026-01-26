# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Document Scanner Service
# ═══════════════════════════════════════════════════════════════════════════════
# Responsible for discovering and cataloging files in a directory.
# Implements IDocumentScanner interface following SRP.
# ═══════════════════════════════════════════════════════════════════════════════

from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime

from interfaces import IDocumentScanner
from models import Document, FileMetadata, ProcessingStatus
from utils import (
    collect_files,
    create_file_metadata,
    get_logger,
)

logger = get_logger(__name__)


class DocumentScanner(IDocumentScanner):
    """
    Service for scanning directories and discovering processable files.

    This service handles:
    - Directory traversal
    - File type filtering
    - Metadata extraction
    - Deduplication checks
    """

    def __init__(
        self,
        recursive: bool = True,
        include_hidden: bool = False,
    ):
        """
        Initialize the document scanner.

        Args:
            recursive: Whether to scan subdirectories
            include_hidden: Whether to include hidden files
        """
        self.recursive = recursive
        self.include_hidden = include_hidden
        self._scanned_count = 0

    def scan_directory(self, directory: Path) -> List[FileMetadata]:
        """
        Scan a directory for processable files.

        Args:
            directory: Path to the directory to scan

        Returns:
            List of file metadata for discovered files
        """
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []

        if not directory.is_dir():
            logger.warning(f"Path is not a directory: {directory}")
            return []

        logger.info(
            "Scanning directory",
            directory=str(directory),
            recursive=self.recursive,
        )

        # Collect files
        files = collect_files(
            directory,
            recursive=self.recursive,
            include_hidden=self.include_hidden,
        )

        # Create metadata for each file
        metadata_list = []
        for file_path in files:
            try:
                metadata = create_file_metadata(file_path)
                metadata_list.append(metadata)
            except Exception as e:
                logger.error(f"Failed to create metadata for {file_path}: {e}")

        self._scanned_count = len(metadata_list)

        logger.info(
            "Directory scan complete",
            files_found=len(metadata_list),
        )

        return metadata_list

    def get_file_hash(self, file_path: Path) -> str:
        """
        Generate a content hash for a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash of file contents
        """
        from utils.file_utils import compute_file_hash
        return compute_file_hash(file_path)

    def filter_by_existing(
        self,
        files: List[FileMetadata],
        existing_paths: Set[str],
        existing_hashes: Set[str],
    ) -> tuple[List[FileMetadata], List[FileMetadata]]:
        """
        Filter files to exclude already indexed ones.

        Args:
            files: List of file metadata
            existing_paths: Set of already indexed paths
            existing_hashes: Set of already indexed content hashes

        Returns:
            Tuple of (new_files, skipped_files)
        """
        new_files = []
        skipped_files = []

        for file in files:
            path_str = str(file.path)

            # Check if already indexed by path or hash
            if path_str in existing_paths or file.content_hash in existing_hashes:
                skipped_files.append(file)
            else:
                new_files.append(file)

        logger.info(
            "Filter complete",
            total=len(files),
            new=len(new_files),
            skipped=len(skipped_files),
        )

        return new_files, skipped_files

    def create_documents(self, metadata_list: List[FileMetadata]) -> List[Document]:
        """
        Create Document objects from file metadata.

        Args:
            metadata_list: List of file metadata

        Returns:
            List of Document objects
        """
        documents = []

        for metadata in metadata_list:
            document = Document(
                metadata=metadata,
                status=ProcessingStatus.PENDING,
                created_at=datetime.utcnow(),
            )
            documents.append(document)

        return documents

    @property
    def scanned_count(self) -> int:
        """Get the number of files scanned in the last operation."""
        return self._scanned_count
