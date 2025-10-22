"""
Pydantic Data Models for BMS Agent API
Defines request/response schemas for all API endpoints
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


# ============================================================================
# Enums
# ============================================================================

class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    DOCX = "docx"
    PPTX = "pptx"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchType(str, Enum):
    """Search strategy types"""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    HIERARCHICAL = "hierarchical"
    RAILWAY_SPECIFIC = "railway_specific"


# ============================================================================
# Core Entity Models (T035-T036)
# ============================================================================

class Document(BaseModel):
    """
    Document entity model (T035)
    Represents an uploaded document in the system
    """
    document_id: str = Field(..., description="Unique document identifier (UUID)")
    document_name: str = Field(..., min_length=1, max_length=500, description="Original filename")
    document_type: DocumentType = Field(..., description="File type/extension")
    department: str = Field(..., min_length=1, max_length=100, description="Department owning the document")
    category: Optional[str] = Field(None, max_length=100, description="Document category/classification")
    file_path: str = Field(..., description="Persistent storage path on disk")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")

    # Processing metadata
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Current processing status")
    processing_started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    processing_error: Optional[str] = Field(None, description="Error message if processing failed")

    # Document metadata
    total_chunks: int = Field(default=0, ge=0, description="Total number of chunks generated")
    total_pages: Optional[int] = Field(None, ge=0, description="Total pages (for PDFs)")
    chapter_count: int = Field(default=0, ge=0, description="Number of chapters detected")

    # Railway-specific metadata (optional)
    fleet_type: Optional[str] = Field(None, max_length=50, description="Fleet type (EMU, DMU, locomotive)")
    train_id: Optional[str] = Field(None, max_length=50, description="Specific train identifier")
    standard_compliance: Optional[List[str]] = Field(None, description="Railway standards referenced")
    network_component: Optional[str] = Field(None, max_length=100, description="Network component (track, signaling, etc)")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Document upload timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "document_name": "Safety_Manual_2024.pdf",
                "document_type": "pdf",
                "department": "Safety",
                "category": "Manuals",
                "file_path": "/workspace/bms-agent/upload-files/Safety/Safety_Manual_2024.pdf",
                "file_size_bytes": 2048576,
                "processing_status": "completed",
                "total_chunks": 42,
                "total_pages": 120,
                "chapter_count": 8
            }
        }


class ChapterContext(BaseModel):
    """Chapter metadata for contextual retrieval"""
    chapter_number: Optional[str] = Field(None, description="Chapter number (e.g., '5.2.1')")
    chapter_title: Optional[str] = Field(None, max_length=500, description="Chapter title/heading")
    chapter_level: int = Field(default=0, ge=0, le=10, description="Nesting level (0=document, 1=chapter, 2=section)")
    chapter_path: Optional[str] = Field(None, description="Full chapter path (e.g., '5 > 5.2 > 5.2.1')")
    sub_chapter: Optional[str] = Field(None, max_length=200, description="Sub-chapter or sub-section")


class Chunk(BaseModel):
    """
    Chunk entity model (T036)
    Represents a text chunk with embeddings and metadata
    """
    chunk_id: str = Field(..., description="Unique chunk identifier (UUID)")
    document_id: str = Field(..., description="Parent document ID")
    chunk_text: str = Field(..., min_length=1, max_length=10000, description="Chunk content text")
    chunk_index: int = Field(..., ge=0, description="Sequential index within document")

    # Hierarchical relationships
    parent_chunk_id: Optional[str] = Field(None, description="Parent chunk ID for hierarchical retrieval")
    child_chunk_ids: List[str] = Field(default_factory=list, description="List of child chunk IDs")

    # Chapter context
    chapter_context: Optional[ChapterContext] = Field(None, description="Chapter/section metadata")

    # Quality metrics
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Quality score (0-100)")
    faithfulness: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS faithfulness score")
    answer_relevancy: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS relevancy score")
    context_precision: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS precision score")
    context_recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="RAGAS recall score")

    # Embedding metadata
    embedding_model: str = Field(default="sentence-transformers/all-mpnet-base-v2", description="Model used for embeddings")
    embedding_dimension: int = Field(default=768, ge=384, le=1536, description="Embedding vector dimension")

    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Chunk creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "c50e8400-e29b-41d4-a716-446655440001",
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "chunk_text": "Emergency braking procedures must be followed...",
                "chunk_index": 15,
                "chapter_context": {
                    "chapter_number": "5.2.1",
                    "chapter_title": "Emergency Procedures",
                    "chapter_level": 3,
                    "chapter_path": "5 > 5.2 > 5.2.1"
                },
                "quality_score": 92.5,
                "embedding_model": "sentence-transformers/all-mpnet-base-v2",
                "embedding_dimension": 768
            }
        }


# ============================================================================
# Search Request/Response Models (T037-T039)
# ============================================================================

class SearchRequest(BaseModel):
    """
    Search request model (T037)
    Common request schema for all search endpoints
    """
    query: str = Field(..., min_length=1, max_length=1024, description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")

    # Metadata filters
    filter_department: Optional[str] = Field(None, max_length=100, description="Filter by department")
    filter_category: Optional[str] = Field(None, max_length=100, description="Filter by category")
    filter_document_name: Optional[str] = Field(None, max_length=500, description="Filter by document name (partial match)")
    filter_chapter_number: Optional[str] = Field(None, max_length=50, description="Filter by chapter number")

    # Railway-specific filters
    filter_fleet_type: Optional[str] = Field(None, max_length=50, description="Filter by fleet type")
    filter_train_id: Optional[str] = Field(None, max_length=50, description="Filter by train ID")
    filter_standard_compliance: Optional[str] = Field(None, max_length=100, description="Filter by railway standard")
    filter_network_component: Optional[str] = Field(None, max_length=100, description="Filter by network component")

    # Quality filtering
    min_quality_score: float = Field(default=85.0, ge=0.0, le=100.0, description="Minimum quality score threshold")

    # Hybrid search parameters
    alpha: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Hybrid search weight (0=keyword, 1=semantic)")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "emergency braking procedures",
                "limit": 10,
                "filter_department": "Safety",
                "min_quality_score": 85.0
            }
        }

    @validator('query')
    def validate_query(cls, v):
        """Ensure query is not just whitespace"""
        if not v.strip():
            raise ValueError("Query cannot be empty or just whitespace")
        return v.strip()


class SearchResult(BaseModel):
    """
    Individual search result model (T039)
    Represents a single ranked result from search
    """
    chunk_id: str = Field(..., description="Chunk identifier")
    chunk_text: str = Field(..., description="Chunk content text")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (cosine similarity)")
    ranking_position: int = Field(..., ge=1, description="Position in result list (1-indexed)")

    # Source document metadata
    source_document: str = Field(..., description="Source document filename")
    document_id: str = Field(..., description="Source document ID")
    department: str = Field(..., description="Department owning the document")
    category: Optional[str] = Field(None, description="Document category")

    # Chapter context for navigation
    chapter_context: Optional[ChapterContext] = Field(None, description="Chapter/section metadata")

    # Quality indicators
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Chunk quality score")

    # Railway-specific metadata (if available)
    fleet_type: Optional[str] = Field(None, description="Fleet type")
    train_id: Optional[str] = Field(None, description="Train ID")
    standard_compliance: Optional[List[str]] = Field(None, description="Referenced standards")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "c50e8400-e29b-41d4-a716-446655440001",
                "chunk_text": "Emergency braking procedures must be followed in all scenarios...",
                "relevance_score": 0.89,
                "ranking_position": 1,
                "source_document": "Safety_Manual_2024.pdf",
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "department": "Safety",
                "chapter_context": {
                    "chapter_number": "5.2.1",
                    "chapter_title": "Emergency Procedures",
                    "chapter_path": "5 > 5.2 > 5.2.1"
                },
                "quality_score": 92.5
            }
        }


class SearchResponse(BaseModel):
    """
    Search response model (T038)
    Complete response for search endpoints
    """
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(default_factory=list, description="Ranked search results")
    total_results: int = Field(..., ge=0, description="Total number of results returned")
    search_time_ms: float = Field(..., ge=0.0, description="Search execution time in milliseconds")

    # Search metadata
    search_type: SearchType = Field(default=SearchType.SEMANTIC, description="Search strategy used")
    filters_applied: Dict[str, str] = Field(default_factory=dict, description="Active filters")

    # Collection statistics (optional)
    collection_total_chunks: Optional[int] = Field(None, description="Total chunks in collection")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "emergency braking procedures",
                "results": [
                    {
                        "chunk_id": "c50e8400-e29b-41d4-a716-446655440001",
                        "chunk_text": "Emergency braking procedures must be followed...",
                        "relevance_score": 0.89,
                        "ranking_position": 1,
                        "source_document": "Safety_Manual_2024.pdf",
                        "document_id": "550e8400-e29b-41d4-a716-446655440000",
                        "department": "Safety",
                        "quality_score": 92.5
                    }
                ],
                "total_results": 1,
                "search_time_ms": 145.2,
                "search_type": "semantic"
            }
        }


# ============================================================================
# Upload/Processing Models
# ============================================================================

class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    department: str = Field(..., min_length=1, max_length=100, description="Department for document")
    category: Optional[str] = Field(None, max_length=100, description="Document category")
    fleet_type: Optional[str] = Field(None, max_length=50, description="Fleet type (optional)")
    train_id: Optional[str] = Field(None, max_length=50, description="Train ID (optional)")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    status: str = Field(..., description="Upload status (success/error)")
    document_id: Optional[str] = Field(None, description="Generated document ID")
    filename: str = Field(..., description="Uploaded filename")
    bytes_stored: int = Field(..., ge=0, description="File size in bytes")
    processing: Dict = Field(default_factory=dict, description="Processing details")


# ============================================================================
# Health/Metrics Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Service statuses")
    metrics: Optional[Dict] = Field(None, description="Operational metrics")


class MetricsResponse(BaseModel):
    """Operational metrics response"""
    request_count: int = Field(..., ge=0, description="Total requests in window")
    latency_p50_ms: float = Field(..., ge=0.0, description="50th percentile latency")
    latency_p95_ms: float = Field(..., ge=0.0, description="95th percentile latency")
    latency_p99_ms: float = Field(..., ge=0.0, description="99th percentile latency")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate (0.0-1.0)")
    queue_depth: int = Field(..., ge=0, description="Current queue depth")
    max_queue_depth: int = Field(..., ge=0, description="Maximum queue depth seen")
    total_requests: int = Field(..., ge=0, description="Total requests since startup")
    total_errors: int = Field(..., ge=0, description="Total errors since startup")
