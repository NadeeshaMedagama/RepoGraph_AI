# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Content Extractor Service
# ═══════════════════════════════════════════════════════════════════════════════
# Unified content extraction using processor registry pattern.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import List, Optional, Type

from interfaces import IContentExtractor
from models import Document, FileMetadata, ProcessingStatus
from processors import (
    BaseProcessor,
    ImageProcessor,
    DiagramProcessor,
    DocumentProcessor,
    SpreadsheetProcessor,
    StructuredProcessor,
    CodeProcessor,
    TextProcessor,
    VideoProcessor,
)
from utils import get_logger

logger = get_logger(__name__)


class ContentExtractor(IContentExtractor):
    """
    Unified content extraction service.

    Uses the Strategy pattern with a processor registry
    to handle different file types appropriately.
    """

    def __init__(self):
        """Initialize the extractor with all processors."""
        self.processors: List[BaseProcessor] = [
            ImageProcessor(),
            DiagramProcessor(),
            DocumentProcessor(),
            SpreadsheetProcessor(),
            StructuredProcessor(),
            CodeProcessor(),
            TextProcessor(),
            VideoProcessor(),
        ]

    def can_process(self, file_metadata: FileMetadata) -> bool:
        """
        Check if any processor can handle this file.

        Args:
            file_metadata: Metadata about the file

        Returns:
            True if a processor exists for this file type
        """
        from models import Document

        # Create temporary document for checking
        temp_doc = Document(metadata=file_metadata)

        for processor in self.processors:
            if processor.can_process(temp_doc):
                return True

        return False

    def extract(self, document: Document) -> Document:
        """
        Extract content from a document.

        Finds the appropriate processor and delegates extraction.

        Args:
            document: Document to process

        Returns:
            Document with extracted content
        """
        # Find the appropriate processor
        processor = self._get_processor(document)

        if processor is None:
            logger.warning(
                f"No processor found for file type: {document.metadata.file_type}"
            )
            document.status = ProcessingStatus.SKIPPED
            document.error_message = f"Unsupported file type: {document.metadata.file_type}"
            return document

        logger.debug(
            "Processing document",
            file=document.metadata.name,
            processor=processor.__class__.__name__,
        )

        # Extract content
        return processor.extract(document)

    def extract_batch(self, documents: List[Document]) -> List[Document]:
        """
        Extract content from multiple documents.

        Args:
            documents: Documents to process

        Returns:
            Processed documents
        """
        results = []
        success_count = 0
        fail_count = 0

        for doc in documents:
            try:
                result = self.extract(doc)
                results.append(result)

                if result.status in (ProcessingStatus.COMPLETED, ProcessingStatus.ANALYZING):
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                logger.error(f"Extraction failed for {doc.metadata.name}: {e}")
                doc.status = ProcessingStatus.FAILED
                doc.error_message = str(e)
                results.append(doc)
                fail_count += 1

        logger.info(
            "Batch extraction complete",
            total=len(documents),
            success=success_count,
            failed=fail_count,
        )

        return results

    def _get_processor(self, document: Document) -> Optional[BaseProcessor]:
        """Find the appropriate processor for a document."""
        for processor in self.processors:
            if processor.can_process(document):
                return processor
        return None

    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions."""
        extensions = set()

        for processor in self.processors:
            for file_type in processor.supported_types:
                extensions.add(f".{file_type.value}")

        return sorted(extensions)

    def register_processor(self, processor: BaseProcessor) -> None:
        """
        Register a custom processor.

        Args:
            processor: Processor instance to register
        """
        self.processors.append(processor)
        logger.info(f"Registered processor: {processor.__class__.__name__}")
