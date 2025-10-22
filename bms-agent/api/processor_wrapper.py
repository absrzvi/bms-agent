"""Document processing wrapper integrating EnhancedDocumentProcessor outputs.

This module provides a higher-level interface around `EnhancedDocumentProcessor`
from `scr/enhanced_document_processor.py`. It coordinates chunk embedding via
Ollama, persists enriched payloads to Qdrant, and returns the full processing
result (including cleaning utilities, quality scores, and metadata).
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# Optional numeric backends for serialization
try:  # pragma: no cover - optional dependency
    import numpy as _np  # type: ignore
except ImportError:  # pragma: no cover
    _np = None

try:  # pragma: no cover - optional dependency
    import torch as _torch  # type: ignore
except ImportError:  # pragma: no cover
    _torch = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCR_PATH = PROJECT_ROOT / "scr"
if str(SCR_PATH) not in sys.path:
    sys.path.append(str(SCR_PATH))

from enhanced_document_processor import (  # type: ignore  # isort:skip
    ChunkingStrategy,
    EnhancedDocumentProcessor,
    ProcessingConfig,
    ProcessingProfile,
)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

_DEFAULT_EMBEDDING_MODEL = "snowflake-arctic-embed2"
_DEFAULT_EMBEDDING_URL = "http://localhost:11434/api/embeddings"
_DEFAULT_COLLECTION = "nomad_bms_documents"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _enum_value(enum, raw: Optional[str], fallback):
    if not raw:
        return fallback
    try:
        return enum[raw.strip().upper()]
    except KeyError:
        LOGGER.warning("Unknown value '%s' for enum %s. Using fallback %s.", raw, enum, fallback)
        return fallback


class DocumentProcessorWrapper:
    """High level orchestrator for document ingestion and indexing."""

    def __init__(
        self,
        qdrant_client: Optional[QdrantClient] = None,
        *,
        embedding_model: Optional[str] = None,
        embedding_url: Optional[str] = None,
        collection_name: Optional[str] = None,
        processing_config: Optional[ProcessingConfig] = None,
    ) -> None:
        # Use sentence-transformers model name instead of Ollama
        self.embedding_model_name = embedding_model or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION", _DEFAULT_COLLECTION)

        # Initialize sentence-transformers model
        LOGGER.info(f"Loading sentence-transformers model: {self.embedding_model_name}")
        self.embedder = SentenceTransformer(self.embedding_model_name)
        LOGGER.info("✅ Embedding model loaded")

        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        qdrant_timeout = int(os.getenv("QDRANT_TIMEOUT", "60"))
        self.qdrant = qdrant_client or QdrantClient(host=qdrant_host, port=qdrant_port, timeout=qdrant_timeout)

        self.config = processing_config or self._build_processing_config()
        self.processor = EnhancedDocumentProcessor(self.config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def process_document(self, file_path: str | Path, *, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a document, index resulting chunks, and return enriched metadata."""

        file_path = Path(file_path)
        processor_result = self.processor.process_document(file_path, document_id=document_id)
        doc_id = processor_result["document_id"]

        points: List[PointStruct] = []
        indexed_chunks: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(processor_result.get("chunks", [])):
            chunk_content = chunk.get("vector_content") or chunk.get("content")
            if not chunk_content:
                continue

            embedding = await self.get_embedding(chunk_content)
            parent_vector = self._try_vector(chunk.get("full_doc_embedding")) or embedding

            payload = self._build_payload(processor_result, chunk, idx)
            point_id = f"{doc_id}::{payload['chunk_key']}"

            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        "chunk_embedding": embedding,
                        "parent_embedding": parent_vector,
                    },
                    payload=payload,
                )
            )
            indexed_chunks.append(payload)

        qdrant_error: Optional[str] = None
        if points:
            LOGGER.info("Indexing %s chunks for document %s into collection '%s'", len(points), doc_id, self.collection_name)
            try:
                self.qdrant.upsert(collection_name=self.collection_name, points=points)
            except Exception as exc:  # pragma: no cover - depends on external service
                qdrant_error = str(exc)
                LOGGER.warning("Qdrant upsert failed: %s", exc)
        else:
            LOGGER.warning("No indexable chunks produced for document %s", doc_id)

        sanitized_result = self._sanitize(processor_result)
        sanitized_result["indexed_chunks"] = indexed_chunks
        sanitized_result["chunks_indexed"] = len(indexed_chunks)
        sanitized_result["collection_name"] = self.collection_name
        sanitized_result["embedding_model"] = self.embedding_model_name
        if qdrant_error:
            sanitized_result["qdrant_upsert_error"] = qdrant_error

        return sanitized_result

    async def search_documents(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a semantic search against Qdrant using stored embeddings.

        Args:
            query: Search query text
            limit: Maximum number of results
            filters: Optional metadata filters (department, category, document_name, etc.)
        """
        if not query:
            raise ValueError("query must be a non-empty string")

        # Build Qdrant filter from metadata filters
        query_filter = self._build_filter(filters) if filters else None

        embedding = await self.get_embedding(query)
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=("chunk_embedding", embedding),
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=False,
        )

        # Format results to match bms_search.py expectations
        formatted = []
        for result in results:
            payload = dict(result.payload) if result.payload else {}
            formatted.append({
                "id": result.id,
                "score": result.score,
                "text": payload.get("content", ""),  # Add 'text' field from content
                "metadata": self._sanitize(payload),  # Rename 'payload' to 'metadata'
            })

        return {
            "count": len(formatted),
            "results": formatted,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name,
        }

    async def search_documents_hybrid(
        self,
        query: str,
        *,
        limit: int = 5,
        alpha: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute hybrid search combining semantic and keyword matching.

        Args:
            query: Search query text
            limit: Maximum number of results
            alpha: Weight for semantic search (0.0=keyword only, 1.0=semantic only)
            filters: Optional metadata filters

        Note: This is a simplified hybrid implementation. For production,
        use QdrantSchemaV4.search_hybrid() which has full RRF implementation.
        """
        if not query:
            raise ValueError("query must be a non-empty string")

        # For now, fall back to semantic search with a note
        # TODO: Integrate proper sparse vector hybrid search when keyword vectors are available
        LOGGER.info(f"Hybrid search requested (alpha={alpha}), falling back to semantic search")

        return await self.search_documents(query, limit=limit, filters=filters)

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers."""
        if not text:
            raise ValueError("Cannot embed empty text")

        # Run encoding in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.embedder.encode(text, convert_to_tensor=False, show_progress_bar=False)
        )

        return embedding.tolist()

    def _build_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """Build Qdrant Filter from metadata filters dict.

        Args:
            filters: Dict of field:value pairs to filter on
                Supported fields: department, category, document_name, document_type, chunk_type
                Multiple values for same field use OR logic, different fields use AND logic

        Returns:
            Qdrant Filter object or None if no valid filters
        """
        if not filters:
            return None

        must_conditions = []

        # Handle each filter field
        for field, value in filters.items():
            if value is None:
                continue

            # Support both single values and lists
            if isinstance(value, list) and len(value) > 1:
                # Multiple values for same field - use OR logic (should)
                should_conditions = [
                    FieldCondition(key=field, match=MatchValue(value=v))
                    for v in value
                ]
                # Wrap in a sub-filter with OR logic
                must_conditions.append(Filter(should=should_conditions))
            elif isinstance(value, list) and len(value) == 1:
                # Single value in a list
                must_conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value[0]))
                )
            else:
                # Single value
                must_conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )

        if not must_conditions:
            return None

        # Return filter with AND logic across different fields
        return Filter(must=must_conditions)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_processing_config(self) -> ProcessingConfig:
        profile = _enum_value(
            ProcessingProfile,
            os.getenv("BMS_PROCESSING_PROFILE"),
            ProcessingProfile.RAILWAY,
        )
        chunking = _enum_value(
            ChunkingStrategy,
            os.getenv("BMS_CHUNKING_STRATEGY"),
            ChunkingStrategy.HIERARCHICAL,
        )
        config = ProcessingConfig(
            chunk_size=int(os.getenv("BMS_CHUNK_SIZE", str(ProcessingConfig.chunk_size))),
            chunk_overlap=int(os.getenv("BMS_CHUNK_OVERLAP", str(ProcessingConfig.chunk_overlap))),
            min_chunk_size=int(os.getenv("BMS_MIN_CHUNK_SIZE", str(ProcessingConfig.min_chunk_size))),
            max_chunk_size=int(os.getenv("BMS_MAX_CHUNK_SIZE", str(ProcessingConfig.max_chunk_size))),
            chunking_strategy=chunking,
            parent_chunk_size=int(os.getenv("BMS_PARENT_CHUNK_SIZE", str(ProcessingConfig.parent_chunk_size))),
            child_chunk_size=int(os.getenv("BMS_CHILD_CHUNK_SIZE", str(ProcessingConfig.child_chunk_size))),
            processing_profile=profile,
            enable_ocr=_env_bool("BMS_ENABLE_OCR", ProcessingConfig.enable_ocr),
            extract_tables=_env_bool("BMS_EXTRACT_TABLES", ProcessingConfig.extract_tables),
            extract_images=_env_bool("BMS_EXTRACT_IMAGES", ProcessingConfig.extract_images),
            enable_contextual_retrieval=_env_bool(
                "BMS_ENABLE_CONTEXTUAL_RETRIEVAL", ProcessingConfig.enable_contextual_retrieval
            ),
            enable_late_chunking=_env_bool("BMS_ENABLE_LATE_CHUNKING", ProcessingConfig.enable_late_chunking),
            quality_threshold=float(os.getenv("BMS_QUALITY_THRESHOLD", str(ProcessingConfig.quality_threshold))),
            min_quality_score=float(os.getenv("BMS_MIN_QUALITY_SCORE", str(ProcessingConfig.min_quality_score))),
            enable_quality_validation=_env_bool(
                "BMS_ENABLE_QUALITY_VALIDATION", ProcessingConfig.enable_quality_validation
            ),
            enable_hybrid_search=_env_bool("BMS_ENABLE_HYBRID_SEARCH", ProcessingConfig.enable_hybrid_search),
            vector_weight=float(os.getenv("BMS_VECTOR_WEIGHT", str(ProcessingConfig.vector_weight))),
            keyword_weight=float(os.getenv("BMS_KEYWORD_WEIGHT", str(ProcessingConfig.keyword_weight))),
            enable_distributed=_env_bool("BMS_ENABLE_DISTRIBUTED", ProcessingConfig.enable_distributed),
            num_workers=int(os.getenv("BMS_NUM_WORKERS", str(ProcessingConfig.num_workers))),
            use_gpu=_env_bool("BMS_USE_GPU", ProcessingConfig.use_gpu),
            enable_versioning=_env_bool("BMS_ENABLE_VERSIONING", ProcessingConfig.enable_versioning),
            track_changes=_env_bool("BMS_TRACK_CHANGES", ProcessingConfig.track_changes),
            preserve_technical_terms=_env_bool(
                "BMS_PRESERVE_TECHNICAL_TERMS", ProcessingConfig.preserve_technical_terms
            ),
            railway_terminology_path=os.getenv("BMS_RAILWAY_TERMINOLOGY_PATH"),
        )
        config.embedding_model = os.getenv("BMS_EMBEDDING_MODEL", config.embedding_model)
        config.embedding_batch_size = int(os.getenv("BMS_EMBEDDING_BATCH_SIZE", str(config.embedding_batch_size)))
        return config

    def _build_payload(self, processor_result: Dict[str, Any], chunk: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        sanitized_chunk = self._sanitize(chunk)
        chunk_key = sanitized_chunk.get("index") or sanitized_chunk.get("metadata", {}).get("position") or chunk_index

        payload = {
            "document_id": processor_result.get("document_id"),
            "file_name": processor_result.get("file_name"),
            "chunk_index": chunk_index,
            "chunk_key": chunk_key,
            "content": sanitized_chunk.get("content", ""),
            "metadata": sanitized_chunk.get("metadata"),
            "quality": sanitized_chunk.get("quality"),
            "has_context": sanitized_chunk.get("has_context"),
            "context_similarity": sanitized_chunk.get("context_similarity"),
            "keyword_content": sanitized_chunk.get("keyword_content"),
            "term_frequencies": sanitized_chunk.get("term_frequencies"),
        }

        if processor_result.get("railway_metadata"):
            payload["railway_metadata"] = self._sanitize(processor_result["railway_metadata"])
        if processor_result.get("entities"):
            payload["entities"] = self._sanitize(processor_result["entities"])

        return payload

    def _try_vector(self, value: Any) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if _np is not None and isinstance(value, _np.ndarray):  # pragma: no cover - requires numpy
            return value.astype(float).tolist()
        if _torch is not None and hasattr(value, "detach") and hasattr(value, "cpu"):  # pragma: no cover - requires torch
            return value.detach().cpu().tolist()
        if hasattr(value, "tolist"):
            return value.tolist()
        return None

    def _sanitize(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._sanitize(v) for k, v in data.items() if v is not None}
        if isinstance(data, list):
            return [self._sanitize(v) for v in data]
        if isinstance(data, tuple):
            return [self._sanitize(v) for v in data]
        if isinstance(data, set):  # pragma: no cover - rarely used
            return [self._sanitize(v) for v in data]
        if isinstance(data, (str, int, float, bool)) or data is None:
            return data
        if _np is not None and isinstance(data, _np.generic):  # pragma: no cover
            return data.item()
        if hasattr(data, "tolist"):
            return data.tolist()
        return str(data)


async def process_document(file_path: str | Path, *, document_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience coroutine to process a document with default configuration."""
    wrapper = DocumentProcessorWrapper()
    return await wrapper.process_document(file_path, document_id=document_id)


def process_document_sync(file_path: str | Path, *, document_id: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous helper that runs the async processor via `asyncio.run`."""
    return asyncio.run(process_document(file_path, document_id=document_id))
