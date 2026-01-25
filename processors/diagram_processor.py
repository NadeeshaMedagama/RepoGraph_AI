# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Diagram Processor
# ═══════════════════════════════════════════════════════════════════════════════
# Processor for diagram files (.drawio, .excalidraw)
# ═══════════════════════════════════════════════════════════════════════════════

import json
import xml.etree.ElementTree as ET
import base64
import zlib
from typing import Set, List
from urllib.parse import unquote

from models import Document, FileCategory, FileType, ProcessingStatus
from processors.base_processor import BaseProcessor
from utils import get_logger

logger = get_logger(__name__)


class DiagramProcessor(BaseProcessor):
    """
    Processor for diagram files.

    Handles .drawio (draw.io/diagrams.net) and .excalidraw files.
    Extracts text labels, shape descriptions, and structural information.
    """

    @property
    def supported_types(self) -> Set[FileType]:
        return {
            FileType.DRAWIO,
            FileType.EXCALIDRAW,
        }

    @property
    def category(self) -> FileCategory:
        return FileCategory.DIAGRAM

    def extract(self, document: Document) -> Document:
        """
        Extract content from a diagram file.

        Args:
            document: Document to process

        Returns:
            Document with extracted_text populated
        """
        try:
            document.status = ProcessingStatus.EXTRACTING

            if document.metadata.file_type == FileType.DRAWIO:
                content = self._extract_drawio(document)
            elif document.metadata.file_type == FileType.EXCALIDRAW:
                content = self._extract_excalidraw(document)
            else:
                content = ""

            document.extracted_text = content
            document.status = ProcessingStatus.ANALYZING  # Mark for vision analysis

            logger.debug(
                "Diagram processed",
                file=document.metadata.name,
                text_length=len(content),
            )

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Failed to process diagram: {e}")
            return document

    def _extract_drawio(self, document: Document) -> str:
        """
        Extract text content from a .drawio file.

        Draw.io files are XML-based and may contain compressed content.
        """
        try:
            # Read and parse XML
            tree = ET.parse(document.metadata.path)
            root = tree.getroot()

            texts = []
            diagram_name = root.get('name', document.metadata.name)
            texts.append(f"Diagram: {diagram_name}")

            # Process each diagram/page
            for diagram in root.findall('.//diagram'):
                page_name = diagram.get('name', 'Unnamed Page')
                texts.append(f"\n=== Page: {page_name} ===")

                # Get the content (may be compressed)
                content = diagram.text
                if content:
                    try:
                        # Try to decompress if it's compressed
                        decompressed = self._decompress_drawio_content(content)
                        page_texts = self._parse_mxgraph_model(decompressed)
                        texts.extend(page_texts)
                    except Exception:
                        # Not compressed, try direct parsing
                        pass

                # Also check for mxGraphModel elements directly
                for mxgraph in diagram.findall('.//mxGraphModel'):
                    page_texts = self._extract_mxgraph_texts(mxgraph)
                    texts.extend(page_texts)

            # Also extract from root-level mxGraphModel
            for mxgraph in root.findall('.//mxGraphModel'):
                page_texts = self._extract_mxgraph_texts(mxgraph)
                texts.extend(page_texts)

            return "\n".join(texts)

        except Exception as e:
            logger.warning(f"Failed to parse drawio XML: {e}")
            # Fallback: read as text
            return self._read_text_file(document)

    def _decompress_drawio_content(self, content: str) -> str:
        """Decompress drawio diagram content."""
        try:
            # URL decode
            decoded = unquote(content)
            # Base64 decode
            data = base64.b64decode(decoded)
            # Inflate (decompress)
            xml_string = zlib.decompress(data, -15).decode('utf-8')
            return xml_string
        except Exception:
            return content

    def _parse_mxgraph_model(self, xml_string: str) -> List[str]:
        """Parse mxGraphModel XML and extract texts."""
        try:
            root = ET.fromstring(xml_string)
            return self._extract_mxgraph_texts(root)
        except Exception:
            return []

    def _extract_mxgraph_texts(self, mxgraph: ET.Element) -> List[str]:
        """Extract text from mxGraphModel elements."""
        texts = []

        # Find all mxCell elements with value attribute
        for cell in mxgraph.findall('.//mxCell'):
            value = cell.get('value', '')
            if value and not value.startswith('<'):
                # Clean HTML if present
                clean_text = self._clean_html(value)
                if clean_text.strip():
                    texts.append(f"  • {clean_text.strip()}")

        # Also check for UserObject elements
        for obj in mxgraph.findall('.//UserObject'):
            label = obj.get('label', '')
            if label:
                clean_text = self._clean_html(label)
                if clean_text.strip():
                    texts.append(f"  • {clean_text.strip()}")

        return texts

    def _clean_html(self, html_string: str) -> str:
        """Remove HTML tags from string."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_string, 'html.parser')
            return soup.get_text()
        except Exception:
            # Simple regex fallback
            import re
            return re.sub(r'<[^>]+>', '', html_string)

    def _extract_excalidraw(self, document: Document) -> str:
        """
        Extract text content from an .excalidraw file.

        Excalidraw files are JSON-based.
        """
        try:
            with open(document.metadata.path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            texts = [f"Excalidraw Diagram: {document.metadata.name}"]

            # Extract from elements
            elements = data.get('elements', [])

            for element in elements:
                elem_type = element.get('type', '')

                # Extract text from text elements
                if elem_type == 'text':
                    text = element.get('text', '')
                    if text.strip():
                        texts.append(f"  • {text.strip()}")

                # Extract from bound text
                elif 'boundElements' in element:
                    for bound in element.get('boundElements', []):
                        if bound.get('type') == 'text':
                            # Find the text element
                            text_id = bound.get('id')
                            for el in elements:
                                if el.get('id') == text_id:
                                    text = el.get('text', '')
                                    if text.strip():
                                        texts.append(f"  • {text.strip()}")

            # Count shapes for context
            shape_counts = {}
            for element in elements:
                elem_type = element.get('type', 'unknown')
                shape_counts[elem_type] = shape_counts.get(elem_type, 0) + 1

            if shape_counts:
                texts.append("\nDiagram composition:")
                for shape, count in sorted(shape_counts.items()):
                    texts.append(f"  - {shape}: {count}")

            return "\n".join(texts)

        except Exception as e:
            logger.warning(f"Failed to parse excalidraw: {e}")
            return self._read_text_file(document)
