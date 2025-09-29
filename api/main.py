"""
BMS Agent FastAPI Application
Main API server with document upload and search endpoints
"""

import os
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our processor wrapper
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from processor_wrapper import get_processor, ProcessingResult

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

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class HybridSearchRequest(SearchRequest):
    vector_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for semantic search")
    keyword_weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for keyword search")

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
                "processing_result": {
                    "chunks_created": processing_result.chunks_created,
                    "quality_score": processing_result.quality_score,
                    "processing_time_ms": processing_result.processing_time_ms,
                    "features_extracted": processing_result.features_extracted
                }
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

@app.get("/api/v1/documents/{document_id}")
async def get_document_status(document_id: str):
    """Get document processing status and metadata"""
    
    # For POC, this is a placeholder - in production would query database
    # Currently just return a not found response since we don't persist document metadata
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error": "Document not found"
        }
    )

@app.post("/api/v1/search/semantic")
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search using dense vector embeddings
    
    - **query**: Search query text
    - **limit**: Maximum number of results (1-100)
    - **filters**: Optional filters for document type, profile, etc.
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
        if request.filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            conditions = []
            
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
        
        # Format results
        results = []
        for result in search_results:
            payload = result.payload
            results.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name"),
                "content": payload.get("content", "")[:500],  # Truncate for response
                "score": float(result.score),
                "metadata": {
                    "chunk_index": payload.get("chunk_index"),
                    "hierarchy_level": payload.get("hierarchy_level"),
                    "quality_score": payload.get("quality_score"),
                    "has_context": payload.get("has_context"),
                    "processing_version": payload.get("processing_version")
                }
            })
        
        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "search_metadata": {
                "total_results": len(results),
                "search_time_ms": int(search_time),
                "embedding_model": "snowflake-arctic-embed2"
            }
        }
        
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
        if request.filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            conditions = []
            
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
        
        # Format results with hybrid scoring simulation
        results = []
        for result in search_results:
            payload = result.payload
            
            # Simulate keyword scoring (in production, would use actual BM25)
            content = payload.get("content", "").lower()
            keyword_score = sum(1 for word in query_words if word in content) / max(len(query_words), 1)
            
            # Calculate hybrid score
            semantic_score = float(result.score)
            hybrid_score = (semantic_score * request.vector_weight) + (keyword_score * request.keyword_weight)
            
            results.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "document_name": payload.get("document_name"),
                "content": payload.get("content", "")[:500],
                "hybrid_score": hybrid_score,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "metadata": {
                    "chunk_index": payload.get("chunk_index"),
                    "hierarchy_level": payload.get("hierarchy_level"),
                    "quality_score": payload.get("quality_score"),
                    "keywords": payload.get("keywords"),
                    "technical_terms": payload.get("technical_terms")
                }
            })
        
        # Sort by hybrid score
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return {
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail="Hybrid search failed")

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
