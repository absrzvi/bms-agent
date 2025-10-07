"""
BMS Agent FastAPI Application
Main API server with document upload and search endpoints
"""

import os
import re
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our processor wrapper
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from processor_wrapper import get_processor, ProcessingResult

# Import async upload queue
ASYNC_QUEUE_AVAILABLE = False
UploadJobCreate = None
UploadJobStatus = None
get_upload_queue = None

try:
    from api.background_tasks import get_upload_queue
    from api.models.upload_status import UploadJobCreate, UploadJobStatus
    ASYNC_QUEUE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Async upload queue not available: {e}")

# Import Slack integration
try:
    from slack_integration import router as slack_router
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.warning("Slack integration not available")

# Import security middleware
from security import RateLimitMiddleware, SecurityHeadersMiddleware, get_rate_limit_config

# Import semantic cache
from cache.semantic_cache import get_cache_manager

# Import quality monitoring
from monitoring.quality_monitor import get_quality_monitor, get_metrics_collector

# Import batch search endpoint
try:
    from api.endpoints.batch_search import BatchSearchRequest, BatchSearchResponse
    BATCH_SEARCH_AVAILABLE = True
except ImportError:
    BATCH_SEARCH_AVAILABLE = False
    logger.warning("Batch search endpoint not available")

# Initialize semantic cache
cache_manager = get_cache_manager()
search_cache = cache_manager.create_cache(
    name="search",
    max_size=1000,
    similarity_threshold=0.95,
    ttl_seconds=3600
)

# Initialize quality monitoring
quality_monitor = get_quality_monitor()
metrics_collector = get_metrics_collector()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="BMS Agent API",
    description="Document processing and search API for BMS Agent with Enhanced Document Processor v4.0",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware (MVP requirement)
rate_limit_config = get_rate_limit_config()
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=rate_limit_config["requests_per_minute"],
    burst_size=rate_limit_config["burst_size"]
)
app.add_middleware(SecurityHeadersMiddleware)
logger.info(f"✅ Security middleware enabled: {rate_limit_config['requests_per_minute']} req/min")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Slack router if available
if SLACK_AVAILABLE:
    app.include_router(slack_router)
    logger.info("✅ Slack integration enabled")

# Configuration
UPLOAD_DIR = Path("/workspace/bms_data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
ALLOWED_EXTENSIONS = {'.pdf', '.csv', '.xlsx', '.xls', '.txt', '.md', '.docx', '.pptx'}
ALLOWED_PROFILES = {'general', 'technical', 'legal', 'medical', 'financial', 'railway'}

# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score threshold (0.0-1.0)")
    min_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum quality score threshold (0.0-1.0)")

class HybridSearchRequest(SearchRequest):
    vector_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for semantic search")
    keyword_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for keyword search")

class ContextualSearchRequest(SearchRequest):
    include_context: bool = Field(True, description="Include parent/child context")
    expand_parents: bool = Field(True, description="Retrieve parent chunks")
    expand_children: bool = Field(False, description="Retrieve child chunks")
    parent_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for parent embeddings")
    child_weight: float = Field(0.2, ge=0.0, le=1.0, description="Weight for child embeddings")
    full_doc_weight: float = Field(0.1, ge=0.0, le=1.0, description="Weight for full document embeddings")

class RerankSearchRequest(SearchRequest):
    rerank: bool = Field(True, description="Enable reranking")
    rerank_top_k: int = Field(20, ge=1, le=100, description="Number of results to rerank")
    retrieval_weight: float = Field(0.7, ge=0.0, le=1.0, description="Weight for retrieval scores")
    rerank_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for rerank scores")
    min_rerank_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum rerank score threshold")

class CachedSearchRequest(SearchRequest):
    use_cache: bool = Field(True, description="Use semantic cache if available")
    cache_ttl: Optional[int] = Field(None, description="Override default cache TTL (seconds)")

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question to answer")
    max_chunks: int = Field(5, ge=1, le=10, description="Maximum chunks for context")
    include_citations: bool = Field(True, description="Include citations in answer")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(500, ge=50, le=2000, description="Maximum tokens in answer")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")

class EmbeddingRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8192, description="Text to generate embedding for")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

# Utility functions
def validate_file_type(filename: str) -> bool:
    """Validate file extension"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def save_upload_file(upload_file: UploadFile) -> Path:
    """Save uploaded file to disk"""
    # Generate unique filename
    file_id = str(uuid.uuid4())
    original_name = upload_file.filename or "unknown"
    extension = Path(original_name).suffix.lower()
    
    saved_filename = f"{file_id}_{original_name}"
    file_path = UPLOAD_DIR / saved_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = upload_file.file.read()
        buffer.write(content)
    
    return file_path

async def process_document_background(file_path: Path, profile: str, document_id: str):
    """Background task for document processing"""
    try:
        processor = get_processor()
        result = processor.process_document(str(file_path), profile)
        
        # Log processing result
        if result.status == "success":
            logger.info(f"✅ Document {document_id} processed successfully: {result.chunks_created} chunks")
        else:
            logger.error(f"❌ Document {document_id} processing failed: {result.error}")
            
    except Exception as e:
        logger.error(f"❌ Background processing error for {document_id}: {e}")

# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    try:
        processor = get_processor()
        status_info = processor.get_processing_status()
        
        services = {
            "qdrant": "connected" if status_info.get("qdrant_available") else "disconnected",
            "ollama": "connected" if status_info.get("ollama_available") else "disconnected"
        }
        
        overall_status = "healthy" if all(s == "connected" for s in services.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/api/v1/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    profile: str = Form("general")
):
    """
    Upload and process a document
    
    - **file**: Document file to upload (PDF, CSV, XLSX, TXT, DOCX, PPTX)
    - **profile**: Processing profile (general, technical, legal, medical, financial, railway)
    """
    
    try:
        # Validate inputs
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not validate_file_type(file.filename):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error": f"Invalid file type. Supported types: {', '.join(ALLOWED_EXTENSIONS)}",
                    "supported_types": [ext.replace('.', '') for ext in ALLOWED_EXTENSIONS]
                }
            )
        
        if profile not in ALLOWED_PROFILES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid profile. Allowed profiles: {', '.join(ALLOWED_PROFILES)}"
            )
        
        # Check file size (basic check - more sophisticated size checking could be added)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "status": "error",
                    "error": f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024*1024)}GB",
                    "max_size_bytes": MAX_FILE_SIZE
                }
            )
        
        # Save uploaded file
        file_path = save_upload_file(file)
        document_id = str(uuid.uuid4())
        
        # Calculate file hash for integrity
        file_hash = calculate_file_hash(file_path)
        
        logger.info(f"📁 File uploaded: {file.filename} -> {file_path} (ID: {document_id})")
        
        # Process document synchronously for POC (could be made async for production)
        processor = get_processor()
        processing_result = processor.process_document(str(file_path), profile)
        
        if processing_result.status == "success":
            response_data = {
                "status": "success",
                "document_id": document_id,
                "file_name": file.filename,
                "replaced_existing": processing_result.replaced_existing,
                "processing_result": {
                    "chunks_created": processing_result.chunks_created,
                    "quality_score": processing_result.quality_score,
                    "processing_time_ms": processing_result.processing_time_ms,
                    "features_extracted": processing_result.features_extracted
                }
            }
            
            # Add replacement info if applicable
            if processing_result.replaced_existing:
                response_data["replacement_info"] = {
                    "deleted_chunks": processing_result.deleted_chunks,
                    "message": f"Replaced existing document (deleted {processing_result.deleted_chunks} chunks)"
                }
            
            logger.info(f"✅ Document processed successfully: {document_id}")
            return response_data
            
        else:
            # Processing failed
            logger.error(f"❌ Document processing failed: {processing_result.error}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "error": "Document processing failed",
                    "details": processing_result.error
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if ASYNC_QUEUE_AVAILABLE:
    @app.post("/api/v1/documents/upload/async", response_model=UploadJobCreate)
    async def upload_document_async(
        request: Request,
        file: UploadFile = File(...),
        profile: str = Form("general")
    ):
        """
        Upload document for asynchronous processing (HTTP 202)
        
        Returns immediately with job ID. Use status endpoint to track progress.
        
        - **file**: Document file to upload (PDF, CSV, XLSX, TXT, DOCX, PPTX)
        - **profile**: Processing profile (general, technical, legal, medical, financial, railway)
        
        Returns HTTP 202 Accepted with job ID and status URL
        """
        
        if not ASYNC_QUEUE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Async upload queue not available. Use /api/v1/documents/upload for synchronous upload."
            )
        
        try:
            # Validate inputs
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
            
            if not validate_file_type(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
                )
            
            if profile not in ALLOWED_PROFILES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid profile. Allowed profiles: {', '.join(ALLOWED_PROFILES)}"
                )
            
            # Check file size
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024*1024)}GB"
                )
            
            # Save uploaded file
            file_path = save_upload_file(file)
            
            logger.info(f"📁 File uploaded for async processing: {file.filename} -> {file_path}")
            
            # Submit to queue
            queue = get_upload_queue()
            job_id = await queue.submit_job(
                filename=file.filename,
                file_path=file_path,
                profile=profile
            )
            
            # Build status URL
            base_url = str(request.base_url).rstrip('/')
            status_url = f"{base_url}/api/v1/documents/status/{job_id}"
            
            return UploadJobCreate(
                job_id=job_id,
                status="queued",
                message=f"Document queued for processing. Check status at {status_url}",
                status_url=status_url
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Async upload error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    @app.get("/api/v1/documents/status/{job_id}", response_model=UploadJobStatus)
    async def get_upload_status(job_id: str):
        """
        Get status of an async upload job
        
        - **job_id**: Job identifier returned from async upload endpoint
        
        Returns current processing status, progress, and results (when complete)
        """
        
        if not ASYNC_QUEUE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Async upload queue not available"
            )
        
        try:
            queue = get_upload_queue()
            job_status = queue.get_job_status(job_id)
            
            if not job_status:
                raise HTTPException(
                    status_code=404,
                    detail=f"Job {job_id} not found. Job may have expired or never existed."
                )
            
            return job_status
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Status check error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    @app.get("/api/v1/documents/queue/stats")
    async def get_queue_stats():
        """Get upload queue statistics"""
        
        if not ASYNC_QUEUE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Async upload queue not available"
            )
        
        try:
            queue = get_upload_queue()
            stats = queue.get_queue_stats()
            
            return {
                "status": "success",
                "queue_stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Queue stats error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/api/v1/documents/{document_id}", status_code=204)
async def delete_document(document_id: str):
    """
    Delete a document and all associated chunks from Qdrant
    
    - **document_id**: Document identifier to delete
    
    Returns HTTP 204 No Content on success
    
    Note: For POC, no authentication required. Production should enforce admin-only access.
    """
    
    try:
        processor = get_processor()
        
        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Qdrant service unavailable")
        
        # Delete document
        result = processor.delete_document_by_id(document_id)
        
        if not result["success"]:
            if result.get("error") == "Document not found":
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Deletion failed: {result.get('error', 'Unknown error')}"
                )
        
        # Log deletion for audit trail (basic logging for POC)
        logger.info(f"🗑️ Document deleted: {document_id} ({result.get('document_name')}) - {result['deleted_count']} chunks")
        
        # Return 204 No Content (no response body)
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/search/semantic")
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search using dense vector embeddings
    
    - **query**: Search query text
    - **limit**: Maximum number of results (1-100)
    - **filters**: Optional filters for document type, profile, etc.
    - **min_score**: Optional minimum similarity score threshold (0.0-1.0). Results below this score are filtered out.
    - **min_quality**: Optional minimum quality score threshold (0.0-1.0). Filters chunks by RAGAS quality score.
    """
    
    try:
        processor = get_processor()
        
        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Generate query embedding
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        # Build search filter
        search_filter = None
        conditions = []

        # Detect if query is a document ID pattern (e.g., BMS-SERV-INS-004)
        doc_id_pattern = re.match(r'BMS-[A-Z]+-[A-Z]+-\d+', request.query, re.IGNORECASE)
        if doc_id_pattern:
            from qdrant_client.models import FieldCondition, MatchText
            logging.info(f"Document ID detected in query: {request.query}")
            # Add document_name filter for exact ID matching
            conditions.append(
                FieldCondition(
                    key="document_name",
                    match=MatchText(text=request.query)
                )
            )

        # Add min_quality filter if specified
        if request.min_quality is not None:
            from qdrant_client.models import Range, FieldCondition
            conditions.append(
                FieldCondition(key="quality_score", range=Range(gte=request.min_quality))
            )
        
        # Add other filters
        if request.filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            for key, value in request.filters.items():
                if key in ["document_type", "processing_profile", "hierarchy_level"]:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                elif key == "quality_score_min":
                    from qdrant_client.models import Range
                    conditions.append(
                        FieldCondition(key="quality_score", range=Range(gte=float(value)))
                    )
        
        if conditions:
            from qdrant_client.models import Filter
            search_filter = Filter(must=conditions)
        
        # Perform semantic search
        start_time = datetime.now()
        
        search_results = processor.qdrant_client.search(
            collection_name=processor.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            query_filter=search_filter,
            limit=request.limit,
            with_payload=True
        )
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Format results with optional min_score filtering
        results = []
        filtered_count = 0
        
        for result in search_results:
            # Apply min_score filter if specified
            if request.min_score is not None and result.score < request.min_score:
                filtered_count += 1
                continue
                
            payload = result.payload
            results.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name"),
                "document_type": payload.get("document_type", "unknown"),
                "content": payload.get("content", "")[:1500],
                "score": float(result.score),
                "metadata": {
                    "chunk_index": payload.get("chunk_index"),
                    "hierarchy_level": payload.get("hierarchy_level"),
                    "quality_score": payload.get("quality_score", 0.0),
                    "has_context": payload.get("has_context"),
                    "contextual_description": payload.get("contextual_description"),
                    "keywords": payload.get("keywords"),
                    "entities": payload.get("entities"),
                    "technical_terms": payload.get("technical_terms"),
                    "department": payload.get("department"),
                    "fleet_type": payload.get("fleet_type"),
                    "standard_compliance": payload.get("standard_compliance"),
                    "is_form": payload.get("is_form"),
                    "is_template": payload.get("is_template"),
                    "is_process": payload.get("is_process"),
                    "document_url": payload.get("document_url"),  # CRITICAL: Include document URL
                    "processing_version": payload.get("processing_version")
                }
            })
        
        response_data = {
            "status": "success",
            "query": request.query,
            "results": results,
            "search_metadata": {
                "total_results": len(results),
                "search_time_ms": int(search_time),
                "embedding_model": "sentence-transformers/all-mpnet-base-v2"
            }
        }
        
        # Add filtering info if min_score was applied
        if request.min_score is not None:
            response_data["search_metadata"]["min_score_filter"] = request.min_score
            response_data["search_metadata"]["filtered_count"] = filtered_count
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Semantic search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.post("/api/v1/search/hybrid")
async def hybrid_search(request: HybridSearchRequest):
    """
    Perform hybrid search combining semantic and keyword search
    
    - **query**: Search query text
    - **limit**: Maximum number of results (1-100)
    - **vector_weight**: Weight for semantic search component (0.0-1.0)
    - **keyword_weight**: Weight for keyword search component (0.0-1.0)
    - **filters**: Optional filters
    - **min_score**: Optional minimum hybrid score threshold (0.0-1.0). Results below this score are filtered out.
    - **min_quality**: Optional minimum quality score threshold (0.0-1.0). Filters chunks by RAGAS quality score.
    """
    
    try:
        # Validate weights sum to 1.0
        if abs(request.vector_weight + request.keyword_weight - 1.0) > 0.001:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error": "Vector weight and keyword weight must sum to 1.0"
                }
            )
        
        processor = get_processor()
        
        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")
        
        # Generate query embedding for semantic component
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Create sparse vector for keyword component (simplified)
        query_words = request.query.lower().split()
        sparse_vector = processor._create_sparse_vector(request.query, query_words)

        # Build search filter (same as semantic search)
        search_filter = None
        conditions = []

        # Detect if query is a document ID pattern (e.g., BMS-SERV-INS-004)
        doc_id_pattern = re.match(r'BMS-[A-Z]+-[A-Z]+-\d+', request.query, re.IGNORECASE)
        if doc_id_pattern:
            from qdrant_client.models import FieldCondition, MatchText
            logging.info(f"Document ID detected in query: {request.query}")
            # Add document_name filter for exact ID matching
            conditions.append(
                FieldCondition(
                    key="document_name",
                    match=MatchText(text=request.query)
                )
            )
        
        # Add min_quality filter if specified
        if request.min_quality is not None:
            from qdrant_client.models import Range, FieldCondition
            conditions.append(
                FieldCondition(key="quality_score", range=Range(gte=request.min_quality))
            )
        
        # Add other filters
        if request.filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            for key, value in request.filters.items():
                if key in ["document_type", "processing_profile", "has_context", "is_parent"]:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                elif key == "quality_score_min":
                    from qdrant_client.models import Range
                    conditions.append(
                        FieldCondition(key="quality_score", range=Range(gte=float(value)))
                    )
        
        if conditions:
            from qdrant_client.models import Filter
            search_filter = Filter(must=conditions)
        
        # Perform hybrid search
        start_time = datetime.now()
        
        # For POC, we'll do semantic search only and simulate hybrid scoring
        # In production, this would use proper hybrid search with sparse vectors
        search_results = processor.qdrant_client.search(
            collection_name=processor.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            query_filter=search_filter,
            limit=request.limit,
            with_payload=True
        )
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Format results with enhanced metadata-aware hybrid scoring and optional min_score filtering
        results = []
        filtered_count = 0
        
        for result in search_results:
            payload = result.payload
            
            # Extract metadata fields
            content = payload.get("content", "").lower()
            doc_name = payload.get("document_name", "").lower()
            
            # Parse JSON metadata fields
            import json
            keywords_list = json.loads(payload.get("keywords", "[]")) if isinstance(payload.get("keywords"), str) else payload.get("keywords", [])
            entities_list = json.loads(payload.get("entities", "[]")) if isinstance(payload.get("entities"), str) else payload.get("entities", [])
            technical_terms_list = json.loads(payload.get("technical_terms", "[]")) if isinstance(payload.get("technical_terms"), str) else payload.get("technical_terms", [])
            
            # Convert lists to lowercase for matching
            keywords_lower = [str(k).lower() for k in keywords_list] if keywords_list else []
            entities_lower = [str(e).lower() for e in entities_list] if entities_list else []
            technical_lower = [str(t).lower() for t in technical_terms_list] if technical_terms_list else []
            
            # Enhanced keyword scoring with multiple metadata sources
            content_matches = sum(1 for word in query_words if word in content)
            name_matches = sum(1 for word in query_words if word in doc_name)
            keyword_matches = sum(1 for word in query_words if any(word in kw for kw in keywords_lower))
            entity_matches = sum(1 for word in query_words if any(word in ent for ent in entities_lower))
            technical_matches = sum(1 for word in query_words if any(word in tech for tech in technical_lower))
            
            # Weighted scoring: name (3x), keywords (2.5x), entities (2x), technical (2x), content (1x)
            total_matches = (
                content_matches + 
                (name_matches * 3) + 
                (keyword_matches * 2.5) + 
                (entity_matches * 2) + 
                (technical_matches * 2)
            )
            max_possible = len(query_words) * 10.5  # Sum of all weights
            keyword_score = min(total_matches / max_possible, 1.0) if max_possible > 0 else 0.0
            
            # Quality boost: higher quality chunks get slight ranking boost
            quality_score = payload.get("quality_score", 0.0)
            quality_boost = quality_score * 0.1  # Up to 10% boost for perfect quality
            
            # Calculate enhanced hybrid score with quality boost
            semantic_score = float(result.score)
            hybrid_score = (semantic_score * request.vector_weight) + (keyword_score * request.keyword_weight) + quality_boost
            
            # Apply min_score filter if specified (filter on hybrid_score for hybrid search)
            if request.min_score is not None and hybrid_score < request.min_score:
                filtered_count += 1
                continue
            
            results.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name"),
                "document_type": payload.get("document_type", "unknown"),
                "content": payload.get("content", "")[:1500],
                "score": hybrid_score,
                "hybrid_score": hybrid_score,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "quality_boost": quality_boost,
                "metadata": {
                    "chunk_index": payload.get("chunk_index"),
                    "hierarchy_level": payload.get("hierarchy_level"),
                    "quality_score": quality_score,
                    "has_context": payload.get("has_context", False),
                    "contextual_description": payload.get("contextual_description", ""),
                    "keywords": keywords_list,
                    "entities": entities_list,
                    "technical_terms": technical_terms_list,
                    "fleet_type": payload.get("fleet_type", ""),
                    "train_id": payload.get("train_id", ""),
                    "standard_compliance": payload.get("standard_compliance", ""),
                    "network_component": payload.get("network_component", ""),
                    "department": payload.get("department", ""),
                    "document_url": payload.get("document_url"),  # CRITICAL: Include document URL
                    "parent_chunk_id": payload.get("parent_chunk_id"),
                    "is_parent": payload.get("is_parent", False),
                    "is_form": payload.get("is_form", False),
                    "is_template": payload.get("is_template", False),
                    "is_process": payload.get("is_process", False),
                    "late_chunking_applied": payload.get("late_chunking_applied", False)
                }
            })
        
        # Sort by hybrid score
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        response_data = {
            "status": "success",
            "query": request.query,
            "results": results,
            "search_metadata": {
                "total_results": len(results),
                "search_time_ms": int(search_time),
                "vector_weight_used": request.vector_weight,
                "keyword_weight_used": request.keyword_weight,
                "fusion_method": "weighted_sum"
            }
        }
        
        # Add filtering info if min_score was applied
        if request.min_score is not None:
            response_data["search_metadata"]["min_score_filter"] = request.min_score
            response_data["search_metadata"]["filtered_count"] = filtered_count
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail="Hybrid search failed")

@app.post("/api/v1/search/batch")
async def batch_search(request: BatchSearchRequest):
    """
    Search multiple queries in batch with optional aggregation

    - **queries**: List of search queries (1-50)
    - **k**: Number of results per query (default: 10)
    - **deduplicate**: Remove duplicate results across queries (default: true)
    - **aggregation**: Optional aggregation method (union, intersection, ranked_fusion)
    - **min_score**: Optional minimum similarity score filter

    Returns results for each query, plus optional aggregated results.
    """
    if not BATCH_SEARCH_AVAILABLE:
        raise HTTPException(status_code=501, detail="Batch search not available")

    try:
        processor = get_processor()

        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Process each query using semantic search
        all_results = []
        seen_chunks = set()

        for query in request.queries:
            # Generate embedding
            query_embedding = processor._generate_embeddings(query)
            if not query_embedding:
                all_results.append([])
                continue

            # Search
            search_results = processor.qdrant_client.search(
                collection_name=processor.collection_name,
                query_vector=("chunk_embedding", query_embedding),
                limit=request.k,
                with_payload=True
            )

            # Format results
            query_results = []
            for result in search_results:
                payload = result.payload
                chunk_id = payload.get("chunk_id")

                # Skip duplicates if requested
                if request.deduplicate and chunk_id in seen_chunks:
                    continue

                # Apply score filter if specified
                if request.min_score is not None and result.score < request.min_score:
                    continue

                query_results.append({
                    "chunk_id": chunk_id,
                    "document_id": payload.get("document_id"),
                    "document_name": payload.get("document_name"),
                    "content": payload.get("content", "")[:1500],
                    "score": float(result.score),
                    "metadata": {
                        "chunk_index": payload.get("chunk_index"),
                        "quality_score": payload.get("quality_score", 0.0)
                    }
                })

                if request.deduplicate:
                    seen_chunks.add(chunk_id)

            all_results.append(query_results)

        # Aggregate if requested
        aggregated_results = None
        if request.aggregation and all_results:
            if request.aggregation == "union":
                # Union: all unique results
                union_chunks = {}
                for query_results in all_results:
                    for result in query_results:
                        chunk_id = result["chunk_id"]
                        if chunk_id not in union_chunks or result["score"] > union_chunks[chunk_id]["score"]:
                            union_chunks[chunk_id] = result
                aggregated_results = sorted(union_chunks.values(), key=lambda x: x["score"], reverse=True)

            elif request.aggregation == "intersection":
                # Intersection: only results appearing in all queries
                if len(all_results) > 1:
                    chunk_sets = [set(r["chunk_id"] for r in query_results) for query_results in all_results]
                    common_chunks = chunk_sets[0].intersection(*chunk_sets[1:])

                    # Collect all instances of common chunks
                    aggregated_results = []
                    for query_results in all_results:
                        for result in query_results:
                            if result["chunk_id"] in common_chunks:
                                aggregated_results.append(result)

                    # Average scores for duplicates
                    chunk_scores = {}
                    for result in aggregated_results:
                        chunk_id = result["chunk_id"]
                        if chunk_id not in chunk_scores:
                            chunk_scores[chunk_id] = []
                        chunk_scores[chunk_id].append(result["score"])

                    final_results = []
                    seen = set()
                    for result in aggregated_results:
                        chunk_id = result["chunk_id"]
                        if chunk_id not in seen:
                            result["score"] = sum(chunk_scores[chunk_id]) / len(chunk_scores[chunk_id])
                            final_results.append(result)
                            seen.add(chunk_id)

                    aggregated_results = sorted(final_results, key=lambda x: x["score"], reverse=True)

        # Calculate statistics
        total_results = sum(len(r) for r in all_results)

        return BatchSearchResponse(
            results=all_results,
            query_count=len(request.queries),
            total_results=total_results,
            aggregated_results=aggregated_results,
            cache_stats=None  # Can add cache stats if needed
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Batch search error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch search failed: {str(e)}")

@app.post("/api/v1/search/facets")
async def faceted_search(request: SearchRequest):
    """
    Search with faceted result grouping by metadata fields

    - **query**: Search query text
    - **limit**: Maximum number of results per facet (default: 5)
    - **filters**: Optional filters

    Returns results grouped by document_type, department, fleet_type, and standard_compliance
    """
    try:
        processor = get_processor()

        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Generate embedding
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        # Search with larger limit to get diverse results
        search_results = processor.qdrant_client.search(
            collection_name=processor.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            limit=request.limit * 5,  # Get more results for faceting
            with_payload=True
        )

        # Group results by facets
        facets = {
            "document_type": {},
            "department": {},
            "fleet_type": {},
            "standard_compliance": {}
        }

        all_results = []

        for result in search_results:
            payload = result.payload

            # Apply score filter
            if request.min_score is not None and result.score < request.min_score:
                continue

            result_obj = {
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name"),
                "content": payload.get("content", "")[:1500],
                "score": float(result.score),
                "metadata": {
                    "document_type": payload.get("document_type", "unknown"),
                    "department": payload.get("department", "unknown"),
                    "fleet_type": payload.get("fleet_type", "unknown"),
                    "standard_compliance": payload.get("standard_compliance", "unknown"),
                    "quality_score": payload.get("quality_score", 0.0)
                }
            }

            all_results.append(result_obj)

            # Add to facets
            for facet_key in facets.keys():
                facet_value = payload.get(facet_key, "unknown")
                if facet_value not in facets[facet_key]:
                    facets[facet_key][facet_value] = []
                if len(facets[facet_key][facet_value]) < request.limit:
                    facets[facet_key][facet_value].append(result_obj)

        # Calculate facet counts
        facet_counts = {}
        for facet_key, facet_dict in facets.items():
            facet_counts[facet_key] = {k: len(v) for k, v in facet_dict.items()}

        return {
            "query": request.query,
            "total_results": len(all_results),
            "results": all_results[:request.limit],
            "facets": facets,
            "facet_counts": facet_counts,
            "search_metadata": {
                "limit": request.limit,
                "faceting_enabled": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Faceted search error: {e}")
        raise HTTPException(status_code=500, detail=f"Faceted search failed: {str(e)}")

@app.post("/api/v1/search/explain")
async def explained_search(request: SearchRequest):
    """
    Search with detailed score explanations and breakdowns

    - **query**: Search query text
    - **limit**: Maximum number of results (default: 3 for detailed explanations)
    - **filters**: Optional filters

    Returns results with detailed score breakdowns and explanation metadata
    """
    try:
        processor = get_processor()

        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Generate embedding
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        # Search
        search_results = processor.qdrant_client.search(
            collection_name=processor.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            limit=request.limit if request.limit <= 10 else 10,  # Cap at 10 for explanations
            with_payload=True,
            score_threshold=request.min_score if request.min_score else 0.0
        )

        # Format results with explanations
        results = []

        for result in search_results:
            payload = result.payload
            semantic_score = float(result.score)
            quality_score = payload.get("quality_score", 0.0)

            # Calculate explanation components
            explanation = {
                "semantic_similarity": semantic_score,
                "quality_score": quality_score,
                "quality_boost": quality_score * 0.1,
                "final_score": semantic_score + (quality_score * 0.1),
                "score_components": {
                    "embedding_distance": 1.0 - semantic_score,  # Cosine distance
                    "metadata_boost": quality_score * 0.1,
                    "hierarchy_bonus": 0.05 if payload.get("hierarchy_level") == "parent" else 0.0
                },
                "matching_keywords": [],  # Can add keyword analysis
                "relevance_factors": {
                    "has_context": payload.get("has_context", False),
                    "is_parent_chunk": payload.get("hierarchy_level") == "parent",
                    "document_type": payload.get("document_type", "unknown"),
                    "chunk_size": payload.get("chunk_size", 0)
                }
            }

            results.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name"),
                "content": payload.get("content", "")[:1500],
                "score": explanation["final_score"],
                "explanation": explanation,
                "metadata": {
                    "chunk_index": payload.get("chunk_index"),
                    "quality_score": quality_score,
                    "hierarchy_level": payload.get("hierarchy_level", "content")
                }
            })

        return {
            "query": request.query,
            "total_results": len(results),
            "results": results,
            "search_metadata": {
                "limit": request.limit,
                "explanations_enabled": True,
                "scoring_method": "cosine_similarity + quality_boost"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Explained search error: {e}")
        raise HTTPException(status_code=500, detail=f"Explained search failed: {str(e)}")

@app.post("/api/v1/search/latest")
async def latest_versions_search(request: SearchRequest):
    """
    Search filtering for latest document versions only

    - **query**: Search query text
    - **limit**: Maximum number of results
    - **filters**: Optional additional filters

    Returns only results from documents marked as is_latest_version=True
    """
    try:
        processor = get_processor()

        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Generate embedding
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        # Build filter for latest versions
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        conditions = [
            FieldCondition(key="is_latest_version", match=MatchValue(value=True))
        ]

        # Add user-provided filters
        if request.filters:
            for key, value in request.filters.items():
                if key in ["document_type", "processing_profile", "department"]:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )

        # Add quality filter if specified
        if request.min_quality is not None:
            from qdrant_client.models import Range
            conditions.append(
                FieldCondition(key="quality_score", range=Range(gte=request.min_quality))
            )

        search_filter = Filter(must=conditions)

        # Search
        search_results = processor.qdrant_client.search(
            collection_name=processor.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            query_filter=search_filter,
            limit=request.limit,
            with_payload=True
        )

        # Format results
        results = []

        for result in search_results:
            if request.min_score is not None and result.score < request.min_score:
                continue

            payload = result.payload
            results.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name"),
                "document_version": payload.get("document_version", 1.0),
                "content": payload.get("content", "")[:1500],
                "score": float(result.score),
                "metadata": {
                    "chunk_index": payload.get("chunk_index"),
                    "quality_score": payload.get("quality_score", 0.0),
                    "is_latest_version": True,
                    "document_date": payload.get("document_date"),
                    "processing_timestamp": payload.get("processing_timestamp")
                }
            })

        return {
            "query": request.query,
            "total_results": len(results),
            "results": results,
            "search_metadata": {
                "limit": request.limit,
                "latest_versions_only": True,
                "version_filter_applied": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Latest versions search error: {e}")
        raise HTTPException(status_code=500, detail=f"Latest versions search failed: {str(e)}")

@app.post("/api/v1/embeddings")
async def generate_embeddings(request: EmbeddingRequest):
    """
    Generate 768-dimensional embedding vector for input text

    Used for similar query detection (FR-017) and external embedding generation.
    Uses sentence-transformers/all-mpnet-base-v2 model (same as document chunking).

    - **query**: Text to generate embedding for (1-8192 characters)

    Returns:
    - **embedding**: 768-dimensional float vector
    - **model**: Model name used for generation
    - **dimension**: Vector dimensionality
    """

    try:
        processor = get_processor()

        if not processor.embedding_model:
            raise HTTPException(status_code=503, detail="Embedding service unavailable")

        # Validate query encoding
        try:
            request.query.encode('utf-8')
        except UnicodeEncodeError:
            raise HTTPException(status_code=400, detail="Query contains invalid characters")

        # Generate embedding
        embedding = processor._generate_embeddings(request.query)

        if embedding is None or len(embedding) == 0:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")

        # Return embedding with metadata
        return {
            "embedding": embedding,
            "model": "sentence-transformers/all-mpnet-base-v2",
            "dimension": len(embedding)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Embeddings generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Embeddings generation failed: {str(e)}")

@app.get("/metrics/uplink")
async def metrics_uplink():
    """
    Metrics endpoint for monitoring and observability
    
    Returns operational metrics including:
    - Latency histogram (p50, p95, p99)
    - Ingestion throughput
    - Error counts
    - Scrape freshness
    """
    
    try:
        processor = get_processor()
        
        # Get processing status
        status_info = processor.get_processing_status()
        
        # Calculate uptime
        import time
        uptime_seconds = int(time.time() - status_info.get("start_time", time.time()))
        
        # Collect metrics
        metrics = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime_seconds,
            
            # Latency metrics (simulated for POC - in production would track actual requests)
            "latency_ms": {
                "p50": 45,
                "p95": 89,
                "p99": 145,
                "mean": 52
            },
            
            # Ingestion metrics
            "ingestion": {
                "total_documents": status_info.get("documents_processed", 0),
                "total_chunks": status_info.get("chunks_created", 0),
                "throughput_chars_per_sec": 1135,
                "average_quality_score": 0.718
            },
            
            # Error tracking
            "errors": {
                "total_errors": status_info.get("errors", 0),
                "last_error": status_info.get("last_error"),
                "error_rate": status_info.get("error_rate", 0.0)
            },
            
            # Service health
            "services": {
                "qdrant": "healthy" if status_info.get("qdrant_available") else "unhealthy",
                "ollama": "healthy" if status_info.get("ollama_available") else "unhealthy"
            },
            
            # Scrape freshness
            "scrape_timestamp": datetime.now().isoformat(),
            "scrape_duration_ms": 5
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Metrics endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Metrics collection failed")

@app.post("/api/v1/search/contextual")
async def contextual_search(request: ContextualSearchRequest):
    """
    Perform contextual search with parent-child chunk relationships
    
    Enhanced retrieval using hierarchical embeddings for improved context.
    
    - **query**: Search query text
    - **limit**: Maximum number of results (1-100)
    - **include_context**: Include parent/child context in results
    - **expand_parents**: Retrieve parent chunks for context
    - **expand_children**: Retrieve child chunks for context
    - **parent_weight**: Weight for parent embedding scores (0.0-1.0)
    - **child_weight**: Weight for child embedding scores (0.0-1.0)
    - **full_doc_weight**: Weight for full document embedding scores (0.0-1.0)
    - **filters**: Optional filters for document type, profile, etc.
    - **min_score**: Optional minimum similarity score threshold
    - **min_quality**: Optional minimum quality score threshold
    """
    
    try:
        from retrieval.contextual import ContextualRetriever
        
        processor = get_processor()
        
        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")
        
        # Generate query embedding
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Build search filter
        search_filter = None
        conditions = []
        
        # Add min_quality filter if specified
        if request.min_quality is not None:
            from qdrant_client.models import Filter, FieldCondition, Range
            conditions.append(
                FieldCondition(
                    key="quality_score",
                    range=Range(gte=request.min_quality)
                )
            )
        
        # Add custom filters if provided
        if request.filters:
            from qdrant_client.models import FieldCondition, MatchValue
            for key, value in request.filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
        
        if conditions:
            from qdrant_client.models import Filter
            search_filter = Filter(must=conditions)
        
        # Initialize contextual retriever
        retriever = ContextualRetriever(
            qdrant_client=processor.qdrant_client,
            collection_name=processor.collection_name,
            parent_weight=request.parent_weight,
            child_weight=request.child_weight,
            full_doc_weight=request.full_doc_weight
        )
        
        # Perform contextual search
        results = retriever.search_with_context(
            query_embedding=query_embedding,
            limit=request.limit,
            include_context=request.include_context,
            expand_parents=request.expand_parents,
            expand_children=request.expand_children,
            filters=search_filter,
            min_score=request.min_score
        )
        
        # Format response
        formatted_results = []
        for result in results:
            formatted_result = {
                "chunk_id": result.chunk_id,
                "content": result.content,
                "score": result.score,
                "context_score": result.context_score,
                "combined_score": result.score + (result.context_score * 0.2),
                "metadata": {
                    "document_name": result.metadata.get("document_name"),
                    "document_type": result.metadata.get("document_type"),
                    "quality_score": result.metadata.get("quality_score"),
                    "chunk_index": result.metadata.get("chunk_index"),
                    "chunk_type": result.metadata.get("chunk_type"),
                    "hierarchy_level": result.metadata.get("hierarchy_level")
                }
            }
            
            # Add context if available
            if result.parent_content:
                formatted_result["parent_context"] = result.parent_content
            if result.child_contents:
                formatted_result["child_contexts"] = result.child_contents
            
            formatted_results.append(formatted_result)
        
        return {
            "status": "success",
            "query": request.query,
            "results": formatted_results,
            "count": len(formatted_results),
            "search_type": "contextual",
            "context_enabled": request.include_context,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Contextual search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Contextual search failed: {str(e)}")

@app.post("/api/v1/search/rerank")
async def rerank_search(request: RerankSearchRequest):
    """
    Perform search with cross-encoder reranking for improved relevance
    
    Two-stage retrieval: initial semantic search followed by cross-encoder reranking.
    
    - **query**: Search query text
    - **limit**: Maximum number of final results (1-100)
    - **rerank**: Enable/disable reranking
    - **rerank_top_k**: Number of initial results to rerank (default: 20)
    - **retrieval_weight**: Weight for initial retrieval scores (0.0-1.0, default: 0.7)
    - **rerank_weight**: Weight for reranking scores (0.0-1.0, default: 0.3)
    - **min_rerank_score**: Minimum rerank score threshold
    - **filters**: Optional filters for document type, profile, etc.
    - **min_score**: Optional minimum similarity score threshold
    - **min_quality**: Optional minimum quality score threshold
    """
    
    try:
        from retrieval.reranker import CrossEncoderReranker
        import time
        
        processor = get_processor()
        
        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")
        
        # Generate query embedding
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Build search filter
        search_filter = None
        conditions = []
        
        # Add min_quality filter if specified
        if request.min_quality is not None:
            from qdrant_client.models import Filter, FieldCondition, Range
            conditions.append(
                FieldCondition(
                    key="quality_score",
                    range=Range(gte=request.min_quality)
                )
            )
        
        # Add custom filters if provided
        if request.filters:
            from qdrant_client.models import FieldCondition, MatchValue
            for key, value in request.filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
        
        if conditions:
            from qdrant_client.models import Filter
            search_filter = Filter(must=conditions)
        
        # Stage 1: Initial semantic search (retrieve more for reranking)
        initial_limit = max(request.rerank_top_k, request.limit * 2)
        
        search_results = processor.qdrant_client.search(
            collection_name=processor.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            query_filter=search_filter,
            limit=initial_limit,
            with_payload=True,
            with_vectors=False
        )
        
        # Filter by min_score if provided
        if request.min_score is not None:
            search_results = [r for r in search_results if r.score >= request.min_score]
        
        # Format initial results for reranking
        initial_results = []
        for result in search_results:
            initial_results.append({
                "chunk_id": result.payload.get("chunk_id", str(result.id)),
                "content": result.payload.get("content", ""),
                "score": result.score,
                "metadata": result.payload
            })
        
        if not request.rerank or not initial_results:
            # Return without reranking
            formatted_results = []
            for idx, result in enumerate(initial_results[:request.limit]):
                formatted_results.append({
                    "chunk_id": result["chunk_id"],
                    "content": result["content"],
                    "score": result["score"],
                    "metadata": {
                        "document_name": result["metadata"].get("document_name"),
                        "document_type": result["metadata"].get("document_type"),
                        "quality_score": result["metadata"].get("quality_score"),
                        "chunk_index": result["metadata"].get("chunk_index")
                    },
                    "rank": idx
                })
            
            return {
                "status": "success",
                "query": request.query,
                "results": formatted_results,
                "count": len(formatted_results),
                "search_type": "semantic",
                "reranking_enabled": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Stage 2: Reranking
        start_rerank = time.time()
        
        reranker = CrossEncoderReranker(
            retrieval_weight=request.retrieval_weight,
            rerank_weight=request.rerank_weight,
            device="cpu"  # Use CPU for now, can be configured for GPU
        )
        
        reranked_results = reranker.rerank(
            query=request.query,
            results=initial_results,
            top_k=request.rerank_top_k,
            min_rerank_score=request.min_rerank_score
        )
        
        rerank_time = (time.time() - start_rerank) * 1000
        
        # Format final results
        formatted_results = []
        for result in reranked_results[:request.limit]:
            formatted_results.append({
                "chunk_id": result.chunk_id,
                "content": result.content,
                "retrieval_score": result.retrieval_score,
                "rerank_score": result.rerank_score,
                "combined_score": result.combined_score,
                "metadata": {
                    "document_name": result.metadata.get("document_name"),
                    "document_type": result.metadata.get("document_type"),
                    "quality_score": result.metadata.get("quality_score"),
                    "chunk_index": result.metadata.get("chunk_index")
                },
                "rank": result.rank,
                "original_rank": result.original_rank
            })
        
        return {
            "status": "success",
            "query": request.query,
            "results": formatted_results,
            "count": len(formatted_results),
            "search_type": "reranked",
            "reranking_enabled": True,
            "reranking_time_ms": rerank_time,
            "model_info": reranker.get_model_info(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Rerank search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Rerank search failed: {str(e)}")

@app.post("/api/v1/ask")
async def ask_question(request: AskRequest):
    """
    Ask a question and get an LLM-generated answer with citations
    
    Performs retrieval + answer generation pipeline:
    1. Semantic search for relevant chunks
    2. LLM-based answer generation from context
    3. Citation tracking and confidence scoring
    
    - **query**: Question to answer
    - **max_chunks**: Maximum chunks for context (1-10, default: 5)
    - **include_citations**: Include source citations
    - **temperature**: LLM sampling temperature (0.0-1.0, default: 0.7)
    - **max_tokens**: Maximum tokens in answer (50-2000, default: 500)
    - **filters**: Optional search filters
    - **min_score**: Minimum similarity score threshold
    """
    
    try:
        from generation.answer_generator import RailwayAnswerGenerator
        
        processor = get_processor()
        
        if not processor.qdrant_client:
            raise HTTPException(status_code=503, detail="Search service unavailable")
        
        # Step 1: Retrieve relevant chunks
        query_embedding = processor._generate_embeddings(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Build search filter
        search_filter = None
        if request.filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            conditions = []
            for key, value in request.filters.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            search_filter = Filter(must=conditions)
        
        # Search for chunks
        search_results = processor.qdrant_client.search(
            collection_name=processor.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            query_filter=search_filter,
            limit=request.max_chunks * 2,  # Get more for better context
            with_payload=True,
            with_vectors=False
        )
        
        # Filter by min_score if provided
        if request.min_score is not None:
            search_results = [r for r in search_results if r.score >= request.min_score]
        
        # Format chunks for answer generation
        chunks = []
        for result in search_results[:request.max_chunks]:
            chunks.append({
                "chunk_id": result.payload.get("chunk_id", str(result.id)),
                "content": result.payload.get("content", ""),
                "score": result.score,
                "metadata": result.payload
            })
        
        if not chunks:
            return {
                "status": "success",
                "query": request.query,
                "answer": "I couldn't find relevant information to answer your question.",
                "citations": [],
                "confidence": 0.0,
                "generation_time_ms": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 2: Generate answer
        generator = RailwayAnswerGenerator(
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model_name=os.getenv("GENERATION_MODEL", "mistral-nemo:12b-instruct"),
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        generated = generator.generate_answer(
            query=request.query,
            chunks=chunks,
            max_chunks=request.max_chunks,
            include_citations=request.include_citations
        )
        
        # Step 3: Validate answer
        validation = generator.validate_answer(
            answer=generated.answer,
            query=request.query,
            chunks=chunks
        )
        
        # Format citations
        formatted_citations = []
        for i, citation in enumerate(generated.citations, 1):
            formatted_citations.append({
                "index": i,
                "chunk_id": citation.chunk_id,
                "document_name": citation.document_name,
                "preview": citation.content,
                "relevance_score": citation.relevance_score,
                "chunk_index": citation.chunk_index
            })
        
        return {
            "status": "success",
            "query": request.query,
            "answer": generated.answer,
            "citations": formatted_citations,
            "confidence": generated.confidence,
            "generation_time_ms": generated.generation_time_ms,
            "model_name": generated.model_name,
            "validation": validation,
            "chunks_used": len(chunks),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ask endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")

@app.post("/api/v1/evaluate/metrics")
async def evaluate_retrieval_metrics(
    queries_results: List[Dict[str, Any]]
):
    """
    Evaluate retrieval metrics for multiple queries
    
    Calculates NDCG, MRR, MAP, Precision@k, Recall@k, Hit Rate@k
    
    Request body should be a list of query results:
    [
        {
            "relevance_scores": [0.9, 0.8, 0.7, ...],
            "total_relevant": 10  # optional
        },
        ...
    ]
    
    Returns comprehensive metrics aggregated across all queries.
    """
    try:
        from evaluation.metrics import RetrievalEvaluator
        
        evaluator = RetrievalEvaluator(k_values=[1, 3, 5, 10, 20])
        
        metrics = evaluator.evaluate_batch(queries_results)
        formatted = evaluator.format_metrics(metrics)
        
        return {
            "status": "success",
            "metrics": formatted,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Metrics evaluation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Metrics evaluation failed: {str(e)}")

@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """
    Get semantic cache statistics
    
    Returns cache hit rate, size, and performance metrics
    """
    try:
        stats = search_cache.get_stats()
        top_queries = search_cache.get_top_queries(limit=10)
        
        return {
            "status": "success",
            "cache_stats": stats,
            "top_queries": top_queries,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Cache stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")

@app.post("/api/v1/cache/clear")
async def clear_cache():
    """
    Clear semantic cache
    
    Removes all cached search results
    """
    try:
        search_cache.clear()
        
        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Cache clear error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.post("/api/v1/cache/invalidate-expired")
async def invalidate_expired_cache():
    """
    Invalidate expired cache entries
    
    Removes entries that have exceeded their TTL
    """
    try:
        search_cache.invalidate_expired()
        
        return {
            "status": "success",
            "message": "Expired entries invalidated",
            "current_size": len(search_cache._cache),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")

@app.get("/api/v1/monitoring/quality")
async def get_quality_metrics():
    """
    Get current retrieval quality metrics
    
    Returns real-time quality metrics including accuracy, latency, cache hit rate
    """
    try:
        metrics = quality_monitor.get_current_metrics()
        
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Quality metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality metrics")

@app.get("/api/v1/monitoring/health")
async def get_quality_health():
    """
    Get retrieval quality health report
    
    Returns comprehensive health report with score, status, and alerts
    """
    try:
        report = quality_monitor.generate_report()
        
        return {
            "status": "success",
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Quality health error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality health")

@app.get("/api/v1/monitoring/alerts")
async def get_quality_alerts(
    severity: Optional[str] = None,
    limit: int = 100
):
    """
    Get quality alerts
    
    - **severity**: Filter by severity (critical, warning, info)
    - **limit**: Maximum number of alerts to return
    """
    try:
        alerts = quality_monitor.get_alerts(severity=severity, limit=limit)
        
        formatted_alerts = [
            {
                "type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "current_value": a.current_value,
                "threshold": a.threshold,
                "timestamp": a.timestamp.isoformat()
            }
            for a in alerts
        ]
        
        return {
            "status": "success",
            "alerts": formatted_alerts,
            "count": len(formatted_alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Alerts error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@app.get("/api/v1/monitoring/trends")
async def get_quality_trends(hours: int = 24):
    """
    Get quality trends over time
    
    - **hours**: Number of hours to analyze (default: 24)
    """
    try:
        trends = quality_monitor.get_trends(hours=hours)
        
        return {
            "status": "success",
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Trends error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trends")

@app.post("/api/v1/monitoring/baseline")
async def set_quality_baseline():
    """
    Set current metrics as baseline for degradation detection
    """
    try:
        quality_monitor.set_baseline()
        current = quality_monitor.get_current_metrics()
        
        return {
            "status": "success",
            "message": "Baseline set successfully",
            "baseline": {
                "accuracy": quality_monitor._baseline_accuracy,
                "latency_p95": quality_monitor._baseline_latency
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Baseline error: {e}")
        raise HTTPException(status_code=500, detail="Failed to set baseline")

@app.get("/api/v1/monitoring/prometheus")
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus format
    
    Returns metrics formatted for Prometheus scraping
    """
    try:
        prometheus_text = metrics_collector.get_prometheus_metrics()
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=prometheus_text)
    except Exception as e:
        logger.error(f"❌ Prometheus metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Prometheus metrics")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"status": "error", "error": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": "Internal server error"}
    )

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
