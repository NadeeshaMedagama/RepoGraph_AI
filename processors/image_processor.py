# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Image Processor
# ═══════════════════════════════════════════════════════════════════════════════
# Processor for image files (PNG, JPG, SVG, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Set

from models import Document, FileCategory, FileType, ProcessingStatus
from processors.base_processor import BaseProcessor
from utils import get_logger

logger = get_logger(__name__)


class ImageProcessor(BaseProcessor):
    """
    Processor for image files.

    Handles PNG, JPG, JPEG, SVG, GIF, BMP, WEBP files.
    Prepares images for vision analysis by extracting basic metadata.
    """

    @property
    def supported_types(self) -> Set[FileType]:
        return {
            FileType.PNG,
            FileType.JPG,
            FileType.JPEG,
            FileType.SVG,
            FileType.GIF,
            FileType.BMP,
            FileType.WEBP,
        }

    @property
    def category(self) -> FileCategory:
        return FileCategory.IMAGE

    def extract(self, document: Document) -> Document:
        """
        Extract content from an image file.

        For images, we primarily rely on vision analysis.
        This method extracts basic metadata and prepares
        a description for the vision service.

        Args:
            document: Document to process

        Returns:
            Document with extracted_text populated
        """
        try:
            document.status = ProcessingStatus.EXTRACTING

            file_path = document.metadata.path

            # For SVG files, we can extract text content
            if document.metadata.file_type == FileType.SVG:
                svg_text = self._extract_svg_text(document)
                if svg_text:
                    document.extracted_text = svg_text
                    document.status = ProcessingStatus.COMPLETED
                    return document

            # For other images, create a description
            description = self._create_image_description(document)
            document.raw_content = description

            # Mark for vision analysis
            document.status = ProcessingStatus.ANALYZING

            logger.debug(
                "Image prepared for vision analysis",
                file=document.metadata.name,
            )

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Failed to process image: {e}")
            return document

    def _extract_svg_text(self, document: Document) -> str:
        """Extract text content from SVG file."""
        try:
            from bs4 import BeautifulSoup

            with open(document.metadata.path, 'r', encoding='utf-8') as f:
                svg_content = f.read()

            soup = BeautifulSoup(svg_content, 'xml')

            # Extract all text elements
            texts = []
            for text_elem in soup.find_all(['text', 'tspan', 'title', 'desc']):
                text = text_elem.get_text(strip=True)
                if text:
                    texts.append(text)

            return "\n".join(texts) if texts else ""

        except Exception as e:
            logger.warning(f"Failed to extract SVG text: {e}")
            return ""

    def _create_image_description(self, document: Document) -> str:
        """Create a basic description of the image."""
        try:
            from PIL import Image

            with Image.open(document.metadata.path) as img:
                width, height = img.size
                mode = img.mode
                format_type = img.format

            return (
                f"Image file: {document.metadata.name}\n"
                f"Dimensions: {width}x{height} pixels\n"
                f"Format: {format_type}\n"
                f"Mode: {mode}\n"
                f"Size: {document.metadata.size_bytes} bytes"
            )

        except Exception:
            return (
                f"Image file: {document.metadata.name}\n"
                f"Size: {document.metadata.size_bytes} bytes"
            )
