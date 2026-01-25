# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - File Utilities
# ═══════════════════════════════════════════════════════════════════════════════
# Utility functions for file operations, hashing, and type detection.
# ═══════════════════════════════════════════════════════════════════════════════

import hashlib
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple

from models.document import FileMetadata, FileType

# Initialize mimetypes
mimetypes.init()


# Supported file extensions by category
SUPPORTED_EXTENSIONS: Set[str] = {
    # Images
    ".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".webp",
    # Diagrams
    ".drawio", ".excalidraw",
    # Documents
    ".docx", ".doc", ".pdf", ".pptx", ".ppt", ".odt",
    # Spreadsheets
    ".xlsx", ".xls",
    # Structured Data
    ".json", ".graphql", ".gql",
    # Markdown & Text
    ".md", ".markdown", ".txt", ".log",
    # Config Files
    ".yaml", ".yml", ".xml", ".ini", ".cfg", ".conf", ".env",
    # Source Code
    ".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp",
    ".h", ".sh", ".sql", ".html", ".css",
    # Video
    ".mp4", ".avi", ".mov", ".mkv", ".webm",
}


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute hash of a file's contents.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (IOError, OSError) as e:
        return ""


def get_mime_type(file_path: Path) -> Optional[str]:
    """
    Get MIME type of a file.

    Args:
        file_path: Path to the file

    Returns:
        MIME type string or None
    """
    # Try to guess from extension first
    mime_type, _ = mimetypes.guess_type(str(file_path))

    if mime_type:
        return mime_type

    # Handle some common types not in mimetypes
    extension = file_path.suffix.lower()
    custom_types = {
        ".drawio": "application/vnd.jgraph.mxfile",
        ".excalidraw": "application/json",
        ".graphql": "application/graphql",
        ".gql": "application/graphql",
        ".md": "text/markdown",
        ".ts": "application/typescript",
        ".tsx": "application/typescript",
    }

    return custom_types.get(extension)


def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes
    """
    try:
        return file_path.stat().st_size
    except (IOError, OSError):
        return 0


def get_file_timestamps(file_path: Path) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Get file creation and modification timestamps.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (created_at, modified_at) datetimes
    """
    try:
        stat = file_path.stat()
        created = datetime.fromtimestamp(stat.st_ctime)
        modified = datetime.fromtimestamp(stat.st_mtime)
        return created, modified
    except (IOError, OSError):
        return None, None


def is_supported_file(file_path: Path) -> bool:
    """
    Check if a file type is supported.

    Args:
        file_path: Path to the file

    Returns:
        True if the file type is supported
    """
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def collect_files(
    directory: Path,
    recursive: bool = True,
    include_hidden: bool = False,
) -> List[Path]:
    """
    Collect all supported files from a directory.

    Args:
        directory: Directory to scan
        recursive: Whether to scan subdirectories
        include_hidden: Whether to include hidden files

    Returns:
        List of file paths
    """
    if not directory.exists():
        return []

    files = []
    pattern = "**/*" if recursive else "*"

    for file_path in directory.glob(pattern):
        # Skip directories
        if file_path.is_dir():
            continue

        # Skip hidden files unless requested
        if not include_hidden and file_path.name.startswith("."):
            continue

        # Check if file type is supported
        if is_supported_file(file_path):
            files.append(file_path)

    return sorted(files)


def create_file_metadata(file_path: Path) -> FileMetadata:
    """
    Create FileMetadata from a file path.

    Args:
        file_path: Path to the file

    Returns:
        FileMetadata object
    """
    created_at, modified_at = get_file_timestamps(file_path)

    return FileMetadata(
        path=file_path,
        name=file_path.name,
        extension=file_path.suffix.lower(),
        size_bytes=get_file_size(file_path),
        created_at=created_at,
        modified_at=modified_at,
        content_hash=compute_file_hash(file_path),
        mime_type=get_mime_type(file_path),
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace problematic characters
    chars_to_replace = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    result = filename
    for char in chars_to_replace:
        result = result.replace(char, '_')
    return result


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
