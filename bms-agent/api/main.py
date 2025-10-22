"""FastAPI application exposing document ingestion and semantic search APIs."""
from __future__ import annotations

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import logging

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# Add API directory to path for imports
API_DIR = Path(__file__).resolve().parent
SCR_DIR = API_DIR.parent / "scr"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))
if str(SCR_DIR) not in sys.path:
    sys.path.insert(0, str(SCR_DIR))

from processor_wrapper import DocumentProcessorWrapper

# Import foundation components
try:
    from metrics_collector import get_metrics_collector, RequestTimer
    from embedding_service import get_embedding_service
    METRICS_AVAILABLE = True
except ImportError as exc:
    logging.warning(f"Metrics/Embedding services unavailable: {exc}")
    METRICS_AVAILABLE = False

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".xlsx", ".xls"}
DEFAULT_UPLOAD_ROOT = Path(os.getenv("BMS_UPLOAD_PATH", Path.home() / "persistent" / "bms_data" / "uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("BMS_UPLOAD_MAX_BYTES", str(100 * 1024 * 1024)))  # 100 MB

API_KEY = os.getenv("BMS_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global service instances
processor = None
metrics_collector = None
embedding_service = None

# Legacy metrics dict for backward compatibility
_metrics: Dict[str, Optional[float]] = {
    "documents_processed": 0,
    "search_requests": 0,
    "last_processing_started": None,
    "last_processing_duration": None,
    "last_search_latency": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes services on startup and cleans up on shutdown.
    """
    global processor, metrics_collector, embedding_service

    # Startup
    logger.info("Starting BMS Agent API services...")

    try:
        # Initialize document processor
        processor = DocumentProcessorWrapper()
        logger.info("✓ DocumentProcessorWrapper initialized")

        # Initialize metrics collector
        if METRICS_AVAILABLE:
            metrics_collector = get_metrics_collector(window_size=1000)
            logger.info("✓ MetricsCollector initialized")

            # Initialize embedding service (for health checks)
            try:
                embedding_service = get_embedding_service()
                logger.info(f"✓ EmbeddingService initialized: {embedding_service.provider}")
            except Exception as exc:
                logger.warning(f"EmbeddingService initialization failed: {exc}")
        else:
            logger.warning("Metrics/Embedding services not available")

        logger.info("BMS Agent API ready to accept requests")

    except Exception as exc:
        logger.error(f"Startup failed: {exc}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down BMS Agent API services...")
    # Add cleanup logic here if needed
    logger.info("BMS Agent API shutdown complete")


app = FastAPI(
    title="BMS Agent API",
    version="1.0.0",
    description="Railway documentation retrieval APIs",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("BMS_ALLOWED_ORIGINS", "http://localhost:5678,http://localhost:8080").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    if API_KEY:
        if api_key != API_KEY:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
        return API_KEY
    # If no API key configured, accept anonymous access for MVP usage
    return api_key or "anonymous"


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1024)
    limit: int = Field(5, ge=1, le=50)
    filters: Optional[Dict[str, str | list]] = Field(None, description="Metadata filters (department, category, document_name, etc.)")


@app.get("/", tags=["Info"])
async def root() -> Dict[str, str]:
    return {
        "service": "BMS Agent API",
        "version": app.version,
        "description": app.description,
    }


@app.get("/health", tags=["Health"])
async def health() -> Dict[str, object]:
    """
    Basic health check with optional metrics.
    Returns service status and operational metrics if available.
    """
    response = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "up",
            "processor": "up" if processor else "initializing"
        }
    }

    # Add metrics if available
    if METRICS_AVAILABLE and metrics_collector:
        try:
            metrics_data = metrics_collector.get_metrics()
            response["metrics"] = {
                "request_count": metrics_data["request_count"],
                "latency_p95_ms": metrics_data["latency_p95_ms"],
                "error_rate": metrics_data["error_rate"]
            }
        except Exception as exc:
            logger.warning(f"Failed to get metrics: {exc}")

    # Add embedding service status if available
    if embedding_service:
        try:
            emb_health = embedding_service.health_check()
            response["services"]["embedding"] = emb_health["status"]
        except Exception as exc:
            logger.warning(f"Failed to check embedding health: {exc}")

    return response


@app.get("/health/detailed", tags=["Health"])
async def detailed_health(_: str = Depends(verify_api_key)) -> Dict[str, object]:
    """
    Detailed health check including all service statuses and comprehensive metrics.
    Requires API key authentication.
    """
    try:
        collections = processor.qdrant.get_collections()
        qdrant_ok = True
        collection_names = [c.name for c in collections.collections]
        collection_exists = processor.collection_name in collection_names
    except Exception as exc:  # pragma: no cover - requires Qdrant
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Qdrant unavailable: {exc}") from exc

    response = {
        "api": "healthy",
        "qdrant": qdrant_ok,
        "collection_exists": collection_exists,
        "collection_name": processor.collection_name,
        "embedding_model": processor.embedding_model,
        "legacy_metrics": _metrics,
    }

    # Add comprehensive metrics from MetricsCollector
    if METRICS_AVAILABLE and metrics_collector:
        try:
            response["metrics"] = metrics_collector.get_metrics()
        except Exception as exc:
            logger.warning(f"Failed to get comprehensive metrics: {exc}")

    # Add embedding service details
    if embedding_service:
        try:
            response["embedding_service"] = embedding_service.health_check()
        except Exception as exc:
            logger.warning(f"Failed to get embedding service details: {exc}")

    return response


@app.get("/metrics", tags=["Metrics"])
async def get_metrics(_: str = Depends(verify_api_key)) -> Dict[str, object]:
    """
    Get comprehensive operational metrics.
    Returns latency percentiles, error rates, request counts, and queue depths.
    """
    if METRICS_AVAILABLE and metrics_collector:
        return metrics_collector.get_metrics()
    else:
        # Fallback to legacy metrics if MetricsCollector not available
        return {
            "message": "MetricsCollector not available, returning legacy metrics",
            "legacy_metrics": _metrics
        }


@app.get("/metrics/uplink", tags=["Metrics"])
async def metrics_uplink(_: str = Depends(verify_api_key)) -> Dict[str, Optional[float]]:
    """
    Legacy metrics endpoint for backward compatibility.
    Use /metrics for comprehensive metrics with percentiles.
    """
    return _metrics


@app.post("/api/v1/search/semantic", tags=["Search"])
async def semantic_search(payload: SemanticSearchRequest, _: str = Depends(verify_api_key)) -> Dict[str, object]:
    """
    Semantic search using dense vector similarity.
    Supports metadata filtering by department, category, document_name, etc.
    """
    # Use RequestTimer for automatic metrics collection
    if METRICS_AVAILABLE and metrics_collector:
        with RequestTimer(endpoint="/api/v1/search/semantic", collector=metrics_collector) as timer:
            try:
                results = await processor.search_documents(
                    payload.query,
                    limit=payload.limit,
                    filters=payload.filters
                )
                timer.set_status(200)
                # Update legacy metrics for backward compatibility
                _metrics["search_requests"] = (_metrics["search_requests"] or 0) + 1
                return results
            except Exception as exc:
                timer.set_status(500)
                raise
    else:
        # Fallback to manual timing if MetricsCollector not available
        start = datetime.utcnow()
        results = await processor.search_documents(
            payload.query,
            limit=payload.limit,
            filters=payload.filters
        )
        _metrics["search_requests"] = (_metrics["search_requests"] or 0) + 1
        _metrics["last_search_latency"] = (datetime.utcnow() - start).total_seconds()
        return results


@app.post("/api/v1/search/hybrid", tags=["Search"])
async def hybrid_search(payload: SemanticSearchRequest, _: str = Depends(verify_api_key)) -> Dict[str, object]:
    """
    Hybrid search combining semantic (vector) and keyword (BM25) search.
    Currently falls back to semantic search (TODO: implement true hybrid with sparse vectors).
    """
    # Use RequestTimer for automatic metrics collection
    if METRICS_AVAILABLE and metrics_collector:
        with RequestTimer(endpoint="/api/v1/search/hybrid", collector=metrics_collector) as timer:
            try:
                # TODO: Implement true hybrid search with BM25 keyword matching
                # For now, use semantic search for compatibility with bms_search.py
                results = await processor.search_documents(
                    payload.query,
                    limit=payload.limit,
                    filters=payload.filters
                )
                timer.set_status(200)
                # Update legacy metrics for backward compatibility
                _metrics["search_requests"] = (_metrics["search_requests"] or 0) + 1
                return results
            except Exception as exc:
                timer.set_status(500)
                raise
    else:
        # Fallback to manual timing if MetricsCollector not available
        start = datetime.utcnow()
        results = await processor.search_documents(
            payload.query,
            limit=payload.limit,
            filters=payload.filters
        )
        _metrics["search_requests"] = (_metrics["search_requests"] or 0) + 1
        _metrics["last_search_latency"] = (datetime.utcnow() - start).total_seconds()
        return results


@app.post("/api/v1/documents/upload", tags=["Documents"])
async def upload_document(file: UploadFile = File(...), _: str = Depends(verify_api_key)) -> JSONResponse:
    """
    Upload and process a document for ingestion into the vector database.
    Supports PDF, TXT, MD, CSV, XLSX, XLS files up to configured size limit.
    """
    # Use RequestTimer for automatic metrics collection
    if METRICS_AVAILABLE and metrics_collector:
        with RequestTimer(endpoint="/api/v1/documents/upload", collector=metrics_collector) as timer:
            try:
                extension = Path(file.filename).suffix.lower()
                if extension not in ALLOWED_EXTENSIONS:
                    timer.set_status(400)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported file type '{extension}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                    )

                upload_root = DEFAULT_UPLOAD_ROOT
                upload_root.mkdir(parents=True, exist_ok=True)
                destination = upload_root / file.filename

                size = 0
                start_time = datetime.utcnow()
                async with aiofile_writer(destination) as writer:
                    while True:
                        chunk = await file.read(1 << 20)  # 1 MB
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_UPLOAD_BYTES:
                            await file.close()
                            destination.unlink(missing_ok=True)
                            timer.set_status(413)
                            raise HTTPException(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail=f"File exceeds limit of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
                            )
                        await writer(chunk)

                result = await processor.process_document(destination)
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Update legacy metrics for backward compatibility
                _metrics["documents_processed"] = (_metrics["documents_processed"] or 0) + 1
                _metrics["last_processing_started"] = start_time.isoformat()
                _metrics["last_processing_duration"] = duration

                response_payload = {
                    "status": "success" if result.get("processing_success", False) else "warning",
                    "filename": file.filename,
                    "bytes_stored": size,
                    "processing": result,
                }
                timer.set_status(200)
                return JSONResponse(status_code=status.HTTP_200_OK, content=response_payload)
            except HTTPException:
                # Re-raise HTTP exceptions (status already set by timer)
                raise
            except Exception as exc:
                timer.set_status(500)
                raise
    else:
        # Fallback to legacy implementation if MetricsCollector not available
        extension = Path(file.filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{extension}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        upload_root = DEFAULT_UPLOAD_ROOT
        upload_root.mkdir(parents=True, exist_ok=True)
        destination = upload_root / file.filename

        size = 0
        start_time = datetime.utcnow()
        async with aiofile_writer(destination) as writer:
            while True:
                chunk = await file.read(1 << 20)  # 1 MB
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    await file.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds limit of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
                    )
                await writer(chunk)

        result = await processor.process_document(destination)
        duration = (datetime.utcnow() - start_time).total_seconds()
        _metrics["documents_processed"] = (_metrics["documents_processed"] or 0) + 1
        _metrics["last_processing_started"] = start_time.isoformat()
        _metrics["last_processing_duration"] = duration

        response_payload = {
            "status": "success" if result.get("processing_success", False) else "warning",
            "filename": file.filename,
            "bytes_stored": size,
            "processing": result,
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=response_payload)


class aiofile_writer:
    """Async context manager that exposes an awaitable writer callback."""

    def __init__(self, path: Path):
        self.path = path
        self._file = None

    async def __aenter__(self):
        loop = asyncio.get_running_loop()
        self._file = await loop.run_in_executor(None, self.path.open, "wb")

        async def _writer(data: bytes) -> None:
            if not self._file:
                raise RuntimeError("file handle not initialized")
            await loop.run_in_executor(None, self._file.write, data)

        self._writer = _writer
        return self._writer

    async def __aexit__(self, exc_type, exc, tb):
        if self._file:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._file.flush)
            await loop.run_in_executor(None, self._file.close)
        self._writer = None
        return False
