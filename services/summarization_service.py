# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Summarization Service
# ═══════════════════════════════════════════════════════════════════════════════
# Azure OpenAI integration for generating comprehensive document summaries.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Optional, Dict, Any, List
from openai import AzureOpenAI

from interfaces import ISummarizer
from models import Document, ProcessingStatus
from config import get_azure_settings
from utils import get_logger, truncate_text

logger = get_logger(__name__)


class AzureOpenAISummarizer(ISummarizer):
    """
    Azure OpenAI-based summarization service.

    Creates comprehensive, structured summaries of document content
    using Azure OpenAI's chat models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        """
        Initialize the summarization service.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint
            deployment: Chat model deployment name
            api_version: API version
        """
        settings = get_azure_settings()

        self.api_key = api_key or settings.api_key
        self.endpoint = endpoint or settings.endpoint
        self.deployment = deployment or settings.chat_deployment
        self.api_version = api_version or settings.api_version

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
        )

        # Token limits
        self.max_input_tokens = 12000  # Leave room for response
        self.max_output_tokens = 2000

    def summarize(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a comprehensive summary of the text.

        Args:
            text: Text to summarize
            context: Optional context about the document

        Returns:
            Comprehensive summary
        """
        if not text or len(text.strip()) < 50:
            return text

        try:
            # Truncate if necessary
            truncated_text = self._truncate_for_context(text)

            # Build the prompt
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(truncated_text, context)

            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=self.max_output_tokens,
            )

            summary = response.choices[0].message.content

            logger.debug(
                "Summary generated",
                input_length=len(text),
                output_length=len(summary),
            )

            return summary

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # Return truncated original text as fallback
            return truncate_text(text, 1000, suffix="\n\n[Summary generation failed]")

    def summarize_document(self, document: Document) -> Document:
        """
        Generate a summary for a document.

        Args:
            document: Document to summarize

        Returns:
            Document with summary field populated
        """
        try:
            document.status = ProcessingStatus.SUMMARIZING

            # Get content to summarize
            content = document.get_content_for_embedding()

            if not content or len(content.strip()) < 50:
                document.summary = content
                document.status = ProcessingStatus.COMPLETED
                return document

            # Build context from metadata
            context = {
                "file_name": document.metadata.name,
                "file_type": document.metadata.file_type.value,
                "category": document.metadata.category.value,
            }

            # Generate summary
            summary = self.summarize(content, context)
            document.summary = summary
            document.status = ProcessingStatus.COMPLETED

            logger.info(
                "Document summarized",
                file=document.metadata.name,
                summary_length=len(summary),
            )

            return document

        except Exception as e:
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            logger.error(f"Document summarization failed: {e}")
            return document

    def summarize_batch(self, documents: List[Document]) -> List[Document]:
        """
        Summarize multiple documents.

        Args:
            documents: List of documents to summarize

        Returns:
            List of documents with summaries
        """
        results = []
        for doc in documents:
            result = self.summarize_document(doc)
            results.append(result)
        return results

    def _truncate_for_context(self, text: str) -> str:
        """Truncate text to fit within context window."""
        # Rough estimate: 4 chars per token
        max_chars = self.max_input_tokens * 4

        if len(text) <= max_chars:
            return text

        # Keep beginning and end
        half = max_chars // 2
        return f"{text[:half]}\n\n[... content truncated ...]\n\n{text[-half:]}"

    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the system prompt for summarization."""
        prompt = """You are an expert technical documentation analyst. Your task is to create comprehensive, well-structured summaries of technical documents.

Your summaries should:
1. Capture the main purpose and key concepts
2. Identify important technical details, configurations, or specifications
3. Note any relationships, dependencies, or connections to other systems
4. Highlight action items, procedures, or workflows
5. Preserve critical data like names, versions, URLs, and identifiers
6. Use clear, professional language

Format your summary with:
- A brief overview (2-3 sentences)
- Key points as bullet points
- Technical details section if applicable
- Any important notes or caveats"""

        if context:
            file_type = context.get('file_type', 'document')
            category = context.get('category', 'unknown')
            prompt += f"\n\nDocument type: {file_type} ({category})"

        return prompt

    def _build_user_prompt(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the user prompt with the document content."""
        file_name = context.get('file_name', 'Document') if context else 'Document'

        return f"""Please create a comprehensive summary of the following document:

File: {file_name}

---
{text}
---

Provide a structured summary that captures all important information."""
