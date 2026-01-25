# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Code Processor
# ═══════════════════════════════════════════════════════════════════════════════
# Processor for source code files
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Set, List
import re

from models import Document, FileCategory, FileType, ProcessingStatus
from processors.base_processor import BaseProcessor
from utils import get_logger

logger = get_logger(__name__)


class CodeProcessor(BaseProcessor):
    """
    Processor for source code files.

    Handles various programming languages.
    Extracts code structure, comments, and documentation.
    """

    @property
    def supported_types(self) -> Set[FileType]:
        return {
            FileType.PYTHON,
            FileType.JAVASCRIPT,
            FileType.TYPESCRIPT,
            FileType.JAVA,
            FileType.GO,
            FileType.RUST,
            FileType.C,
            FileType.CPP,
            FileType.H,
            FileType.SHELL,
            FileType.SQL,
            FileType.HTML,
            FileType.CSS,
        }

    @property
    def category(self) -> FileCategory:
        return FileCategory.CODE

    def extract(self, document: Document) -> Document:
        """
        Extract content from a source code file.

        Args:
            document: Document to process

        Returns:
            Document with extracted_text populated
        """
        try:
            document.status = ProcessingStatus.EXTRACTING

            content = self._read_text_file(document)
            analysis = self._analyze_code(content, document.metadata.file_type)

            full_content = f"{analysis}\n\n--- Source Code ---\n\n{content}"
            document.extracted_text = full_content
            document.status = ProcessingStatus.COMPLETED

            logger.debug(
                "Code file processed",
                file=document.metadata.name,
                type=document.metadata.file_type.value,
                lines=content.count('\n') + 1,
            )

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Failed to process code file: {e}")
            return document

    def _analyze_code(self, content: str, file_type: FileType) -> str:
        """Analyze code and extract structure."""
        lines = content.split('\n')

        analysis = []
        analysis.append(f"File type: {file_type.value}")
        analysis.append(f"Lines of code: {len(lines)}")

        # Count various metrics
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = self._count_comments(lines, file_type)

        analysis.append(f"Blank lines: {blank_lines}")
        analysis.append(f"Comment lines: ~{comment_lines}")

        # Extract structure based on language
        if file_type == FileType.PYTHON:
            structure = self._analyze_python(content)
        elif file_type in (FileType.JAVASCRIPT, FileType.TYPESCRIPT):
            structure = self._analyze_js_ts(content)
        elif file_type == FileType.JAVA:
            structure = self._analyze_java(content)
        elif file_type == FileType.GO:
            structure = self._analyze_go(content)
        elif file_type == FileType.SQL:
            structure = self._analyze_sql(content)
        else:
            structure = self._analyze_generic(content)

        if structure:
            analysis.append("\nCode Structure:")
            analysis.extend(structure)

        # Extract imports/includes
        imports = self._extract_imports(content, file_type)
        if imports:
            analysis.append(f"\nImports/Dependencies ({len(imports)}):")
            for imp in imports[:20]:
                analysis.append(f"  • {imp}")
            if len(imports) > 20:
                analysis.append(f"  ... ({len(imports) - 20} more)")

        return "\n".join(analysis)

    def _count_comments(self, lines: List[str], file_type: FileType) -> int:
        """Count approximate comment lines."""
        count = 0
        in_block = False

        for line in lines:
            stripped = line.strip()

            # Block comments
            if '/*' in stripped:
                in_block = True
            if '*/' in stripped:
                in_block = False
                count += 1
                continue

            if in_block:
                count += 1
                continue

            # Line comments
            if stripped.startswith('//') or stripped.startswith('#'):
                count += 1
            elif stripped.startswith('--') and file_type == FileType.SQL:
                count += 1

        return count

    def _analyze_python(self, content: str) -> List[str]:
        """Analyze Python code structure."""
        structure = []

        # Find classes
        classes = re.findall(r'class\s+(\w+)\s*[:\(]', content)
        if classes:
            structure.append(f"  Classes: {', '.join(classes[:10])}")

        # Find functions
        functions = re.findall(r'def\s+(\w+)\s*\(', content)
        if functions:
            structure.append(f"  Functions: {', '.join(functions[:15])}")
            if len(functions) > 15:
                structure.append(f"    ... ({len(functions) - 15} more)")

        # Find decorators
        decorators = set(re.findall(r'@(\w+)', content))
        if decorators:
            structure.append(f"  Decorators used: {', '.join(sorted(decorators)[:10])}")

        return structure

    def _analyze_js_ts(self, content: str) -> List[str]:
        """Analyze JavaScript/TypeScript code structure."""
        structure = []

        # Find classes
        classes = re.findall(r'class\s+(\w+)', content)
        if classes:
            structure.append(f"  Classes: {', '.join(classes[:10])}")

        # Find functions
        functions = re.findall(r'function\s+(\w+)\s*\(', content)
        arrow_funcs = re.findall(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(', content)
        all_funcs = functions + arrow_funcs
        if all_funcs:
            structure.append(f"  Functions: {', '.join(all_funcs[:15])}")

        # Find exports
        exports = re.findall(r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)', content)
        if exports:
            structure.append(f"  Exports: {', '.join(exports[:10])}")

        # Find interfaces (TypeScript)
        interfaces = re.findall(r'interface\s+(\w+)', content)
        if interfaces:
            structure.append(f"  Interfaces: {', '.join(interfaces[:10])}")

        return structure

    def _analyze_java(self, content: str) -> List[str]:
        """Analyze Java code structure."""
        structure = []

        # Find package
        package = re.search(r'package\s+([\w.]+);', content)
        if package:
            structure.append(f"  Package: {package.group(1)}")

        # Find classes
        classes = re.findall(r'class\s+(\w+)', content)
        if classes:
            structure.append(f"  Classes: {', '.join(classes[:10])}")

        # Find interfaces
        interfaces = re.findall(r'interface\s+(\w+)', content)
        if interfaces:
            structure.append(f"  Interfaces: {', '.join(interfaces[:10])}")

        # Find methods
        methods = re.findall(r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\(', content)
        if methods:
            structure.append(f"  Methods: {', '.join(methods[:15])}")

        return structure

    def _analyze_go(self, content: str) -> List[str]:
        """Analyze Go code structure."""
        structure = []

        # Find package
        package = re.search(r'package\s+(\w+)', content)
        if package:
            structure.append(f"  Package: {package.group(1)}")

        # Find structs
        structs = re.findall(r'type\s+(\w+)\s+struct', content)
        if structs:
            structure.append(f"  Structs: {', '.join(structs[:10])}")

        # Find interfaces
        interfaces = re.findall(r'type\s+(\w+)\s+interface', content)
        if interfaces:
            structure.append(f"  Interfaces: {', '.join(interfaces[:10])}")

        # Find functions
        functions = re.findall(r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(', content)
        if functions:
            structure.append(f"  Functions: {', '.join(functions[:15])}")

        return structure

    def _analyze_sql(self, content: str) -> List[str]:
        """Analyze SQL code structure."""
        structure = []

        # Find CREATE statements
        tables = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?(\w+)', content, re.I)
        if tables:
            structure.append(f"  Tables: {', '.join(tables[:10])}")

        # Find views
        views = re.findall(r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+[`"\[]?(\w+)', content, re.I)
        if views:
            structure.append(f"  Views: {', '.join(views[:10])}")

        # Find procedures
        procs = re.findall(r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+[`"\[]?(\w+)', content, re.I)
        if procs:
            structure.append(f"  Procedures: {', '.join(procs[:10])}")

        # Count queries
        selects = len(re.findall(r'\bSELECT\b', content, re.I))
        inserts = len(re.findall(r'\bINSERT\b', content, re.I))
        updates = len(re.findall(r'\bUPDATE\b', content, re.I))

        if any([selects, inserts, updates]):
            structure.append(f"  Queries: SELECT({selects}), INSERT({inserts}), UPDATE({updates})")

        return structure

    def _analyze_generic(self, content: str) -> List[str]:
        """Generic code analysis."""
        structure = []

        # Find function-like patterns
        functions = re.findall(r'(?:function|func|def|fn)\s+(\w+)', content)
        if functions:
            structure.append(f"  Functions: {', '.join(functions[:15])}")

        return structure

    def _extract_imports(self, content: str, file_type: FileType) -> List[str]:
        """Extract import statements."""
        imports = []

        if file_type == FileType.PYTHON:
            # Python imports
            imports.extend(re.findall(r'^import\s+([\w.]+)', content, re.M))
            imports.extend(re.findall(r'^from\s+([\w.]+)\s+import', content, re.M))

        elif file_type in (FileType.JAVASCRIPT, FileType.TYPESCRIPT):
            # JS/TS imports
            imports.extend(re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content))
            imports.extend(re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', content))

        elif file_type == FileType.JAVA:
            # Java imports
            imports.extend(re.findall(r'^import\s+([\w.]+);', content, re.M))

        elif file_type == FileType.GO:
            # Go imports
            imports.extend(re.findall(r'import\s+"([^"]+)"', content))
            imports.extend(re.findall(r'^\s+"([^"]+)"', content, re.M))

        elif file_type in (FileType.C, FileType.CPP, FileType.H):
            # C/C++ includes
            imports.extend(re.findall(r'#include\s*[<"]([^>"]+)[>"]', content))

        return list(set(imports))
