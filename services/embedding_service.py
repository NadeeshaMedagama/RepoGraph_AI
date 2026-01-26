# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Embedding Service
# ═══════════════════════════════════════════════════════════════════════════════
# Azure OpenAI embeddings generation for vector storage.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import List, Optional
from openai import AzureOpenAI

from interfaces import IEmbeddingService
from models import Chunk, EmbeddedChunk
from config import get_azure_settings
from utils import get_logger

logger = get_logger(__name__)


class AzureOpenAIEmbeddingService(IEmbeddingService):
    """
    Azure OpenAI embedding service.

    Generates high-quality text embeddings using Azure OpenAI's
    embedding models (e.g., text-embedding-ada-002, text-embedding-3-small).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        """
        Initialize the embedding service.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint
            deployment: Embedding model deployment name
            api_version: API version
        """
        settings = get_azure_settings()

        self.api_key = api_key or settings.api_key
        self.endpoint = endpoint or settings.endpoint
        self.deployment = deployment or settings.embeddings_deployment
        self.api_version = api_version or settings.embeddings_version

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
        )

        # Batch processing settings
        self.batch_size = 16  # Azure OpenAI typical limit
        self.max_tokens_per_text = 8000

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * 1536

        try:
            # Truncate if necessary
            truncated = self._truncate_text(text)

            response = self.client.embeddings.create(
                model=self.deployment,
                input=truncated,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Handles batching automatically for large lists.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            # Truncate each text
            truncated_batch = [self._truncate_text(t) for t in batch]

            # Filter empty texts
            valid_indices = [j for j, t in enumerate(truncated_batch) if t.strip()]
            valid_texts = [truncated_batch[j] for j in valid_indices]

            if valid_texts:
                try:
                    response = self.client.embeddings.create(
                        model=self.deployment,
                        input=valid_texts,
                    )

                    # Map embeddings back to original indices
                    batch_embeddings = [None] * len(batch)
                    for idx, emb in zip(valid_indices, response.data):
                        batch_embeddings[idx] = emb.embedding

                    # Fill in zero vectors for empty texts
                    zero_vector = [0.0] * 1536
                    for j in range(len(batch)):
                        if batch_embeddings[j] is None:
                            batch_embeddings[j] = zero_vector

                    all_embeddings.extend(batch_embeddings)

                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    # Return zero vectors for failed batch
                    all_embeddings.extend([[0.0] * 1536] * len(batch))
            else:
                # All texts were empty
                all_embeddings.extend([[0.0] * 1536] * len(batch))

            logger.debug(
                "Batch embedded",
                batch_num=i // self.batch_size + 1,
                batch_size=len(batch),
            )

        return all_embeddings

    def embed_chunks(self, chunks: List[Chunk]) -> List[EmbeddedChunk]:
        """
        Embed a list of chunks.

        Args:
            chunks: Chunks to embed

        Returns:
            Embedded chunks with vectors
        """
        if not chunks:
            return []

        # Extract texts
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings
        embeddings = self.embed_batch(texts)

        # Create EmbeddedChunk objects
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            embedded_chunk = EmbeddedChunk(
                chunk=chunk,
                embedding=embedding,
                embedding_model=self.deployment,
            )
            embedded_chunks.append(embedded_chunk)

        logger.info(
            "Chunks embedded",
            count=len(embedded_chunks),
        )

        return embedded_chunks

    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within token limits."""
        if not text:
            return ""

        # Rough estimate: 4 chars per token
        max_chars = self.max_tokens_per_text * 4

        if len(text) <= max_chars:
            return text

        return text[:max_chars]

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        return 1536  # Default for ada-002 and embedding-3-small
