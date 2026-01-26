# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Pinecone Vector Store Service
# ═══════════════════════════════════════════════════════════════════════════════
# Pinecone vector database operations for storing and retrieving embeddings.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from pinecone import Pinecone, ServerlessSpec

from interfaces import IVectorStore
from models import Document, EmbeddedChunk, VectorMetadata, SearchResult
from config import get_pinecone_settings
from utils import get_logger, truncate_text

logger = get_logger(__name__)


class PineconeVectorStore(IVectorStore):
    """
    Pinecone vector store implementation.

    Handles all vector database operations including:
    - Index initialization and management
    - Vector upserting with metadata
    - Similarity search
    - Deduplication tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None,
    ):
        """
        Initialize the Pinecone vector store.

        Args:
            api_key: Pinecone API key
            index_name: Index name
            namespace: Namespace for organizing vectors
        """
        settings = get_pinecone_settings()

        self.api_key = api_key or settings.api_key
        self.index_name = index_name or settings.index_name
        self.namespace = namespace or settings.namespace
        self.dimension = settings.dimension
        self.cloud = settings.cloud
        self.region = settings.region
        self.use_namespaces = settings.use_namespaces

        self.pc: Optional[Pinecone] = None
        self.index = None

        # Cache for deduplication
        self._existing_paths: Set[str] = set()
        self._existing_hashes: Set[str] = set()

    def initialize(self) -> None:
        """Initialize connection and ensure index exists."""
        try:
            self.pc = Pinecone(api_key=self.api_key)

            # Check if index exists
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]

            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=self.cloud,
                        region=self.region,
                    ),
                )
                logger.info("Index created successfully")

            # Connect to index
            self.index = self.pc.Index(self.index_name)

            # Get index stats
            stats = self.index.describe_index_stats()
            total_vectors = stats.total_vector_count

            logger.info(
                "Connected to Pinecone",
                index=self.index_name,
                total_vectors=total_vectors,
            )

            # Load existing paths for deduplication
            self._load_existing_records()

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

    def upsert(self, embedded_chunks: List[EmbeddedChunk], document: Document) -> int:
        """
        Store embedded chunks in Pinecone.

        Args:
            embedded_chunks: Chunks with embeddings
            document: Source document

        Returns:
            Number of vectors stored
        """
        if not embedded_chunks:
            return 0

        if self.index is None:
            self.initialize()

        try:
            # Prepare vectors for upsert
            vectors = []

            for ec in embedded_chunks:
                # Create unique ID
                vector_id = f"{document.metadata.content_hash}_{ec.chunk.chunk_index}"

                # Create metadata
                metadata = VectorMetadata(
                    document_id=str(document.id),
                    chunk_id=str(ec.chunk.id),
                    source_path=str(document.metadata.path),
                    file_name=document.metadata.name,
                    file_type=document.metadata.file_type.value,
                    category=document.metadata.category.value,
                    chunk_index=ec.chunk.chunk_index,
                    total_chunks=ec.chunk.total_chunks,
                    content_preview=truncate_text(ec.chunk.content, 500),
                    content_hash=document.metadata.content_hash,
                    created_at=datetime.utcnow().isoformat(),
                )

                vectors.append({
                    "id": vector_id,
                    "values": ec.embedding,
                    "metadata": metadata.to_dict(),
                })

            # Upsert in batches
            batch_size = 100
            total_upserted = 0

            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]

                if self.use_namespaces:
                    self.index.upsert(vectors=batch, namespace=self.namespace)
                else:
                    self.index.upsert(vectors=batch)

                total_upserted += len(batch)

            # Update cache
            self._existing_paths.add(str(document.metadata.path))
            self._existing_hashes.add(document.metadata.content_hash)

            logger.info(
                "Vectors upserted",
                document=document.metadata.name,
                vectors=total_upserted,
            )

            return total_upserted

        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector
            top_k: Number of results
            filter: Optional metadata filter

        Returns:
            Search results
        """
        if self.index is None:
            self.initialize()

        try:
            # Perform search
            query_params = {
                "vector": query_embedding,
                "top_k": top_k,
                "include_metadata": True,
            }

            if filter:
                query_params["filter"] = filter

            if self.use_namespaces:
                query_params["namespace"] = self.namespace

            response = self.index.query(**query_params)

            # Convert to SearchResult objects
            results = []
            for match in response.matches:
                metadata_dict = match.metadata or {}

                metadata = VectorMetadata(
                    document_id=metadata_dict.get("document_id", ""),
                    chunk_id=metadata_dict.get("chunk_id", ""),
                    source_path=metadata_dict.get("source_path", ""),
                    file_name=metadata_dict.get("file_name", ""),
                    file_type=metadata_dict.get("file_type", ""),
                    category=metadata_dict.get("category", ""),
                    chunk_index=metadata_dict.get("chunk_index", 0),
                    total_chunks=metadata_dict.get("total_chunks", 1),
                    content_preview=metadata_dict.get("content_preview", ""),
                    content_hash=metadata_dict.get("content_hash", ""),
                    created_at=metadata_dict.get("created_at", ""),
                )

                result = SearchResult(
                    id=match.id,
                    score=match.score,
                    metadata=metadata,
                    content=metadata_dict.get("content_preview", ""),
                )
                results.append(result)

            logger.debug(
                "Search completed",
                top_k=top_k,
                results_found=len(results),
            )

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_existing_paths(self) -> Set[str]:
        """Get all indexed file paths."""
        return self._existing_paths.copy()

    def get_existing_hashes(self) -> Set[str]:
        """Get all indexed content hashes."""
        return self._existing_hashes.copy()

    def delete_by_path(self, path: str) -> int:
        """
        Delete vectors for a specific file path.

        Args:
            path: File path to delete

        Returns:
            Number of vectors deleted (estimated)
        """
        if self.index is None:
            self.initialize()

        try:
            # Pinecone requires vector IDs for deletion
            # We need to query first to get IDs
            # This is a limitation - in production, you might use a metadata filter delete

            # For now, we'll note this as a limitation
            logger.warning(
                "Delete by path requires fetching IDs first",
                path=path,
            )

            # Remove from cache
            self._existing_paths.discard(path)

            return 0  # Actual deletion would require more complex logic

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return 0

    def _load_existing_records(self) -> None:
        """Load existing paths and hashes for deduplication."""
        if self.index is None:
            return

        try:
            # Get index stats to check if there are vectors
            stats = self.index.describe_index_stats()

            if self.use_namespaces:
                ns_stats = stats.namespaces.get(self.namespace, {})
                vector_count = ns_stats.vector_count if hasattr(ns_stats, 'vector_count') else 0
            else:
                vector_count = stats.total_vector_count

            if vector_count == 0:
                logger.info("No existing vectors found")
                return

            logger.info(f"Loading existing records for deduplication ({vector_count} vectors)")

            # Sample vectors to build deduplication cache
            # Note: This is a simplified approach. For large indexes,
            # you might want to maintain a separate metadata store.

            # Use a dummy query to fetch some records
            dummy_vector = [0.0] * self.dimension

            query_params = {
                "vector": dummy_vector,
                "top_k": min(10000, vector_count),  # Limit for performance
                "include_metadata": True,
            }

            if self.use_namespaces:
                query_params["namespace"] = self.namespace

            response = self.index.query(**query_params)

            for match in response.matches:
                if match.metadata:
                    path = match.metadata.get("source_path", "")
                    hash_val = match.metadata.get("content_hash", "")

                    if path:
                        self._existing_paths.add(path)
                    if hash_val:
                        self._existing_hashes.add(hash_val)

            logger.info(
                "Deduplication cache loaded",
                unique_paths=len(self._existing_paths),
                unique_hashes=len(self._existing_hashes),
            )

        except Exception as e:
            logger.warning(f"Failed to load existing records: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if self.index is None:
            self.initialize()

        try:
            stats = self.index.describe_index_stats()

            return {
                "index_name": self.index_name,
                "dimension": self.dimension,
                "total_vectors": stats.total_vector_count,
                "namespaces": {
                    ns: {"vector_count": data.vector_count}
                    for ns, data in stats.namespaces.items()
                } if stats.namespaces else {},
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
