# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Text Processor
# ═══════════════════════════════════════════════════════════════════════════════
# Processor for text and markdown files
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Set
import re

from models import Document, FileCategory, FileType, ProcessingStatus
from processors.base_processor import BaseProcessor
from utils import get_logger

logger = get_logger(__name__)


class TextProcessor(BaseProcessor):
    """
    Processor for text and markdown files.

    Handles plain text, markdown, and config files.
    """

    @property
    def supported_types(self) -> Set[FileType]:
        return {
            FileType.MARKDOWN,
            FileType.TXT,
            FileType.LOG,
            FileType.INI,
            FileType.CFG,
            FileType.CONF,
            FileType.ENV,
        }

    @property
    def category(self) -> FileCategory:
        return FileCategory.TEXT

    def extract(self, document: Document) -> Document:
        """
        Extract content from a text file.

        Args:
            document: Document to process

        Returns:
            Document with extracted_text populated
        """
        try:
            document.status = ProcessingStatus.EXTRACTING

            content = self._read_text_file(document)

            # For markdown, add structural analysis
            if document.metadata.file_type == FileType.MARKDOWN:
                analysis = self._analyze_markdown(content)
                content = f"{analysis}\n\n--- Content ---\n\n{content}"

            document.extracted_text = content
            document.status = ProcessingStatus.COMPLETED

            logger.debug(
                "Text file processed",
                file=document.metadata.name,
                type=document.metadata.file_type.value,
            )

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Failed to process text file: {e}")
            return document

    def _analyze_markdown(self, content: str) -> str:
        """Analyze markdown structure."""
        lines = content.split('\n')

        analysis = ["Markdown Document Analysis:"]

        # Count headings
        h1 = len(re.findall(r'^# [^#]', content, re.M))
        h2 = len(re.findall(r'^## [^#]', content, re.M))
        h3 = len(re.findall(r'^### [^#]', content, re.M))

        analysis.append(f"  Headings: H1({h1}), H2({h2}), H3({h3})")

        # Count code blocks
        code_blocks = len(re.findall(r'```', content)) // 2
        analysis.append(f"  Code blocks: {code_blocks}")

        # Count links and images
        links = len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content))
        images = len(re.findall(r'!\[([^\]]*)\]\([^)]+\)', content))
        analysis.append(f"  Links: {links}, Images: {images}")

        # Count lists
        bullet_items = len(re.findall(r'^\s*[-*+]\s', content, re.M))
        numbered_items = len(re.findall(r'^\s*\d+\.\s', content, re.M))
        analysis.append(f"  List items: Bullet({bullet_items}), Numbered({numbered_items})")

        # Extract headings
        headings = re.findall(r'^(#{1,3})\s+(.+)$', content, re.M)
        if headings:
            analysis.append("\nTable of Contents:")
            for level, heading in headings[:20]:
                indent = "  " * (len(level) - 1)
                analysis.append(f"{indent}• {heading}")
            if len(headings) > 20:
                analysis.append(f"  ... ({len(headings) - 20} more headings)")

        return "\n".join(analysis)
