# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Structured Data Processor
# ═══════════════════════════════════════════════════════════════════════════════
# Processor for structured data files (JSON, GraphQL, YAML, XML)
# ═══════════════════════════════════════════════════════════════════════════════

import json
from typing import Set, Dict, Any, List

from models import Document, FileCategory, FileType, ProcessingStatus
from processors.base_processor import BaseProcessor
from utils import get_logger

logger = get_logger(__name__)


class StructuredProcessor(BaseProcessor):
    """
    Processor for structured data files.

    Handles JSON, GraphQL, YAML, and XML files.
    Extracts schema information and key-value relationships.
    """

    @property
    def supported_types(self) -> Set[FileType]:
        return {
            FileType.JSON,
            FileType.GRAPHQL,
            FileType.GQL,
            FileType.YAML,
            FileType.YML,
            FileType.XML,
        }

    @property
    def category(self) -> FileCategory:
        return FileCategory.STRUCTURED

    def extract(self, document: Document) -> Document:
        """
        Extract content from a structured data file.

        Args:
            document: Document to process

        Returns:
            Document with extracted_text populated
        """
        try:
            document.status = ProcessingStatus.EXTRACTING

            file_type = document.metadata.file_type

            if file_type == FileType.JSON:
                content = self._extract_json(document)
            elif file_type in (FileType.GRAPHQL, FileType.GQL):
                content = self._extract_graphql(document)
            elif file_type in (FileType.YAML, FileType.YML):
                content = self._extract_yaml(document)
            elif file_type == FileType.XML:
                content = self._extract_xml(document)
            else:
                content = self._read_text_file(document)

            document.extracted_text = content
            document.status = ProcessingStatus.COMPLETED

            logger.debug(
                "Structured file processed",
                file=document.metadata.name,
                type=file_type.value,
                text_length=len(content),
            )

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Failed to process structured file: {e}")
            return document

    def _extract_json(self, document: Document) -> str:
        """Extract and analyze JSON content."""
        try:
            with open(document.metadata.path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            texts = [f"JSON File: {document.metadata.name}\n"]

            # Analyze structure
            structure = self._analyze_json_structure(data)
            texts.append("Structure Analysis:")
            texts.append(structure)

            # Pretty print (limited)
            texts.append("\nContent Preview:")
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
            if len(pretty) > 5000:
                texts.append(pretty[:5000] + "\n... (truncated)")
            else:
                texts.append(pretty)

            return "\n".join(texts)

        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return self._read_text_file(document)

    def _analyze_json_structure(self, data: Any, prefix: str = "", depth: int = 0) -> str:
        """Analyze and describe JSON structure."""
        if depth > 5:  # Limit depth
            return f"{prefix}  ... (nested)"

        lines = []

        if isinstance(data, dict):
            lines.append(f"{prefix}Object with {len(data)} keys:")
            for key in list(data.keys())[:20]:  # Limit keys shown
                value = data[key]
                value_desc = self._describe_value(value)
                lines.append(f"{prefix}  • {key}: {value_desc}")

                # Recurse into nested objects
                if isinstance(value, (dict, list)) and depth < 3:
                    nested = self._analyze_json_structure(value, prefix + "    ", depth + 1)
                    if nested:
                        lines.append(nested)

            if len(data) > 20:
                lines.append(f"{prefix}  ... ({len(data) - 20} more keys)")

        elif isinstance(data, list):
            lines.append(f"{prefix}Array with {len(data)} items")
            if data:
                sample = data[0]
                lines.append(f"{prefix}  Item type: {self._describe_value(sample)}")
                if isinstance(sample, dict) and depth < 3:
                    nested = self._analyze_json_structure(sample, prefix + "    ", depth + 1)
                    if nested:
                        lines.append(nested)

        return "\n".join(lines)

    def _describe_value(self, value: Any) -> str:
        """Describe a JSON value's type and content."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return f"boolean ({value})"
        elif isinstance(value, int):
            return f"integer ({value})"
        elif isinstance(value, float):
            return f"number ({value})"
        elif isinstance(value, str):
            if len(value) > 50:
                return f'string ("{value[:50]}...")'
            return f'string ("{value}")'
        elif isinstance(value, list):
            return f"array[{len(value)}]"
        elif isinstance(value, dict):
            return f"object{{{len(value)} keys}}"
        return type(value).__name__

    def _extract_graphql(self, document: Document) -> str:
        """Extract and analyze GraphQL schema."""
        try:
            content = self._read_text_file(document)

            texts = [f"GraphQL Schema: {document.metadata.name}\n"]

            # Simple parsing to identify types, queries, mutations
            lines = content.split('\n')

            types = []
            queries = []
            mutations = []
            subscriptions = []
            current_block = None

            for line in lines:
                stripped = line.strip()

                if stripped.startswith('type '):
                    type_name = stripped.split()[1].rstrip('{').strip()
                    types.append(type_name)
                    if type_name == 'Query':
                        current_block = 'query'
                    elif type_name == 'Mutation':
                        current_block = 'mutation'
                    elif type_name == 'Subscription':
                        current_block = 'subscription'
                    else:
                        current_block = 'type'

                elif stripped.startswith('input '):
                    type_name = stripped.split()[1].rstrip('{').strip()
                    types.append(f"input {type_name}")

                elif stripped.startswith('enum '):
                    type_name = stripped.split()[1].rstrip('{').strip()
                    types.append(f"enum {type_name}")

                elif current_block == 'query' and ':' in stripped:
                    query_name = stripped.split('(')[0].split(':')[0].strip()
                    if query_name and not query_name.startswith('#'):
                        queries.append(query_name)

                elif current_block == 'mutation' and ':' in stripped:
                    mutation_name = stripped.split('(')[0].split(':')[0].strip()
                    if mutation_name and not mutation_name.startswith('#'):
                        mutations.append(mutation_name)

                elif stripped == '}':
                    current_block = None

            # Summary
            texts.append(f"Types defined: {len(types)}")
            for t in types[:20]:
                texts.append(f"  • {t}")
            if len(types) > 20:
                texts.append(f"  ... ({len(types) - 20} more)")

            if queries:
                texts.append(f"\nQueries: {len(queries)}")
                for q in queries[:15]:
                    texts.append(f"  • {q}")

            if mutations:
                texts.append(f"\nMutations: {len(mutations)}")
                for m in mutations[:15]:
                    texts.append(f"  • {m}")

            texts.append("\n--- Full Schema ---\n")
            texts.append(content)

            return "\n".join(texts)

        except Exception as e:
            logger.warning(f"Failed to parse GraphQL: {e}")
            return self._read_text_file(document)

    def _extract_yaml(self, document: Document) -> str:
        """Extract and analyze YAML content."""
        try:
            import yaml

            with open(document.metadata.path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            texts = [f"YAML File: {document.metadata.name}\n"]

            # Analyze structure
            if isinstance(data, dict):
                texts.append(f"Top-level keys: {len(data)}")
                for key in list(data.keys())[:20]:
                    value = data[key]
                    value_desc = self._describe_value(value)
                    texts.append(f"  • {key}: {value_desc}")
            elif isinstance(data, list):
                texts.append(f"Top-level array: {len(data)} items")

            # Include raw content
            texts.append("\n--- Content ---\n")
            texts.append(self._read_text_file(document))

            return "\n".join(texts)

        except Exception as e:
            logger.warning(f"Failed to parse YAML: {e}")
            return self._read_text_file(document)

    def _extract_xml(self, document: Document) -> str:
        """Extract and analyze XML content."""
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(document.metadata.path)
            root = tree.getroot()

            texts = [f"XML File: {document.metadata.name}\n"]
            texts.append(f"Root element: {root.tag}")

            if root.attrib:
                texts.append(f"Root attributes: {dict(root.attrib)}")

            # Count children
            children = list(root)
            child_tags = {}
            for child in children:
                tag = child.tag.split('}')[-1]  # Remove namespace
                child_tags[tag] = child_tags.get(tag, 0) + 1

            if child_tags:
                texts.append(f"\nChild elements:")
                for tag, count in sorted(child_tags.items()):
                    texts.append(f"  • {tag}: {count}")

            # Extract text content
            texts.append("\n--- Text Content ---\n")
            all_text = self._extract_xml_text(root)
            texts.append(all_text)

            return "\n".join(texts)

        except Exception as e:
            logger.warning(f"Failed to parse XML: {e}")
            return self._read_text_file(document)

    def _extract_xml_text(self, element, depth: int = 0) -> str:
        """Recursively extract text from XML element."""
        if depth > 10:
            return ""

        texts = []

        # Element text
        if element.text and element.text.strip():
            tag = element.tag.split('}')[-1]
            texts.append(f"{tag}: {element.text.strip()}")

        # Process children
        for child in element:
            child_text = self._extract_xml_text(child, depth + 1)
            if child_text:
                texts.append(child_text)

        return "\n".join(texts)
