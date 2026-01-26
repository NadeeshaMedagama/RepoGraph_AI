# ═══════════════════════════════════════════════════════════════════════════════
# RepoGraph AI - Query Service
# ═══════════════════════════════════════════════════════════════════════════════
# RAG query service combining semantic search with LLM generation.
# ═══════════════════════════════════════════════════════════════════════════════

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import AzureOpenAI

from interfaces import IQueryService
from models import SearchResult, QueryResult
from services.embedding_service import AzureOpenAIEmbeddingService
from services.vector_store import PineconeVectorStore
from config import get_azure_settings
from utils import get_logger

logger = get_logger(__name__)


class RAGQueryService(IQueryService):
    """
    RAG (Retrieval-Augmented Generation) query service.

    Combines semantic search with LLM-based answer generation
    to provide accurate, context-aware responses.
    """

    def __init__(
        self,
        embedding_service: Optional[AzureOpenAIEmbeddingService] = None,
        vector_store: Optional[PineconeVectorStore] = None,
    ):
        """
        Initialize the query service.

        Args:
            embedding_service: Service for generating query embeddings
            vector_store: Vector store for similarity search
        """
        self.embedding_service = embedding_service or AzureOpenAIEmbeddingService()
        self.vector_store = vector_store or PineconeVectorStore()

        # Initialize Azure OpenAI for generation
        settings = get_azure_settings()
        self.llm_client = AzureOpenAI(
            api_key=settings.api_key,
            api_version=settings.api_version,
            azure_endpoint=settings.endpoint,
        )
        self.chat_deployment = settings.chat_deployment

        # Ensure vector store is initialized
        self.vector_store.initialize()

    def query(self, question: str, top_k: int = 5) -> QueryResult:
        """
        Answer a question using RAG.

        1. Generate embedding for the question
        2. Search for relevant documents
        3. Generate answer using context

        Args:
            question: User's question
            top_k: Number of context documents to use

        Returns:
            Query result with answer and sources
        """
        start_time = time.time()

        try:
            # Step 1: Generate query embedding
            query_embedding = self.embedding_service.embed(question)

            # Step 2: Search for relevant documents
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
            )

            if not search_results:
                return QueryResult(
                    query=question,
                    answer="I couldn't find any relevant information to answer your question.",
                    sources=[],
                    model_used=self.chat_deployment,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                )

            # Step 3: Build context from search results
            context = self._build_context(search_results)

            # Step 4: Generate answer
            answer = self._generate_answer(question, context)

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                "Query processed",
                question_length=len(question),
                sources_found=len(search_results),
                processing_time_ms=processing_time,
            )

            return QueryResult(
                query=question,
                answer=answer,
                sources=search_results,
                model_used=self.chat_deployment,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QueryResult(
                query=question,
                answer=f"An error occurred while processing your question: {str(e)}",
                sources=[],
                model_used=self.chat_deployment,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Perform semantic search without generation.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Search results
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed(query)

            # Search
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
            )

            logger.debug(
                "Search completed",
                query_length=len(query),
                results=len(results),
            )

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_by_filter(
        self,
        query: str,
        filter: Dict[str, Any],
        top_k: int = 10,
    ) -> List[SearchResult]:
        """
        Search with metadata filters.

        Args:
            query: Search query
            filter: Metadata filter (e.g., {"file_type": "pdf"})
            top_k: Number of results

        Returns:
            Filtered search results
        """
        try:
            query_embedding = self.embedding_service.embed(query)

            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter=filter,
            )

            return results

        except Exception as e:
            logger.error(f"Filtered search failed: {e}")
            return []

    def _build_context(self, results: List[SearchResult]) -> str:
        """Build context string from search results."""
        context_parts = []

        for i, result in enumerate(results, 1):
            source_info = f"[Source {i}: {result.metadata.file_name}]"
            content = result.metadata.content_preview or result.content

            context_parts.append(f"{source_info}\n{content}")

        return "\n\n---\n\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with context."""
        system_prompt = """You are a helpful AI assistant with access to a knowledge base. 
Answer questions based on the provided context. If the context doesn't contain 
enough information to answer the question, say so clearly.

Guidelines:
- Be accurate and cite specific information from the context
- If multiple sources provide relevant information, synthesize them
- Use clear, professional language
- If you're unsure, express uncertainty rather than making things up
- Format your response clearly with paragraphs or bullet points as appropriate"""

        user_prompt = f"""Context from knowledge base:

{context}

---

Question: {question}

Please provide a comprehensive answer based on the context above."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return f"I found relevant information but encountered an error generating the answer: {str(e)}"

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed documents."""
        return self.vector_store.get_stats()
