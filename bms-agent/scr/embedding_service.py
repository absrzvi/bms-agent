"""
Embedding Service Abstraction Layer
Supports dual embedding providers: sentence-transformers and Ollama
"""
import os
from typing import List, Literal, Optional
import logging

logger = logging.getLogger(__name__)

ServiceType = Literal["sentence-transformers", "ollama"]


class EmbeddingService:
    """
    Unified interface for embedding generation supporting multiple backends.

    Supported providers:
    - sentence-transformers: Local, fast, deterministic (all-mpnet-base-v2, 768d)
    - Ollama: API-based, flexible model selection (snowflake-arctic-embed2, 1024d)
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize embedding service with specified provider.

        Args:
            provider: "sentence-transformers" or "ollama". Auto-detect if None.
            model_name: Model identifier. Uses defaults if None.
            batch_size: Number of texts to embed at once (1-256)
        """
        self.provider = provider or os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
        self.batch_size = int(os.getenv("BMS_EMBEDDING_BATCH_SIZE", str(batch_size)))

        if self.provider == "sentence-transformers":
            self._init_sentence_transformers(model_name)
        elif self.provider == "ollama":
            self._init_ollama(model_name)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        logger.info(
            f"EmbeddingService initialized: provider={self.provider}, "
            f"model={self.model_name}, dimension={self.dimension}, batch_size={self.batch_size}"
        )

    def _init_sentence_transformers(self, model_name: Optional[str]):
        """Initialize sentence-transformers backend."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            ) from exc

        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-mpnet-base-v2"
        )
        # Remove provider prefix if present
        if self.model_name.startswith("sentence-transformers/"):
            model_id = self.model_name.split("/", 1)[1]
        else:
            model_id = self.model_name

        logger.info(f"Loading sentence-transformers model: {model_id}")
        self.model = SentenceTransformer(model_id)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def _init_ollama(self, model_name: Optional[str]):
        """Initialize Ollama backend."""
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "snowflake-arctic-embed2")
        self.endpoint = os.getenv("EMBEDDING_URL", "http://localhost:11434/api/embeddings")

        # Ollama dimensions depend on model
        model_dimensions = {
            "snowflake-arctic-embed2": 1024,
            "mxbai-embed-large": 1024,
            "nomic-embed-text": 768,
            "all-minilm": 384,
        }
        self.dimension = model_dimensions.get(self.model_name, 1024)
        self.model = None  # Ollama is API-based, no local model

        # Verify Ollama is accessible
        try:
            import httpx
            response = httpx.get(self.endpoint.replace("/api/embeddings", "/api/tags"), timeout=5.0)
            response.raise_for_status()
            logger.info(f"Ollama service accessible at {self.endpoint}")
        except Exception as exc:
            logger.warning(f"Ollama service not accessible: {exc}. Embeddings will fail until service is available.")

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of strings to embed

        Returns:
            List of embedding vectors (each is List[float] of length self.dimension)
        """
        if not texts:
            return []

        if self.provider == "sentence-transformers":
            return await self._embed_sentence_transformers(texts)
        elif self.provider == "ollama":
            return await self._embed_ollama(texts)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers (synchronous, CPU/GPU)."""
        import asyncio

        # Run in thread pool since sentence-transformers is synchronous
        loop = asyncio.get_running_loop()

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = await loop.run_in_executor(
                None,
                self.model.encode,
                batch,
                {"show_progress_bar": False, "convert_to_numpy": True}
            )
            all_embeddings.extend(embeddings.tolist())

        return all_embeddings

    async def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama API (asynchronous HTTP)."""
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            all_embeddings = []

            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]

                # Ollama API accepts one text at a time, so we parallelize within batch
                tasks = []
                for text in batch:
                    payload = {
                        "model": self.model_name,
                        "prompt": text
                    }
                    tasks.append(client.post(self.endpoint, json=payload))

                responses = await asyncio.gather(*tasks)

                for response in responses:
                    response.raise_for_status()
                    data = response.json()
                    embedding = data.get("embedding")
                    if not embedding:
                        raise ValueError(f"Ollama response missing 'embedding' field: {data}")
                    all_embeddings.append(embedding)

            return all_embeddings

    def health_check(self) -> dict:
        """
        Check embedding service health.

        Returns:
            dict with status, model_name, service_type, embedding_dimension
        """
        status = "unknown"

        if self.provider == "sentence-transformers":
            status = "loaded" if self.model is not None else "unloaded"
        elif self.provider == "ollama":
            try:
                import httpx
                response = httpx.get(
                    self.endpoint.replace("/api/embeddings", "/api/tags"),
                    timeout=5.0
                )
                response.raise_for_status()
                status = "accessible"
            except Exception as exc:
                status = f"unavailable: {exc}"

        return {
            "status": status,
            "model_name": self.model_name,
            "service_type": self.provider,
            "embedding_dimension": self.dimension,
            "batch_size": self.batch_size
        }


# Singleton instance for easy import
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(provider: Optional[str] = None) -> EmbeddingService:
    """
    Get or create the global embedding service instance.

    Args:
        provider: Force specific provider (sentence-transformers/ollama)

    Returns:
        EmbeddingService singleton
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(provider=provider)
    return _embedding_service
