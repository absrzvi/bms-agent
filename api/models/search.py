"""
Search-related Pydantic models for BMS Agent API
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    """Base search request model"""
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")


class SemanticSearchRequest(SearchRequest):
    """Semantic search request model"""
    include_metadata: bool = Field(default=True, description="Include chunk metadata in results")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")


class HybridSearchRequest(SearchRequest):
    """Hybrid search request model"""
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight for vector similarity")
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for keyword matching")
    candidate_multiplier: int = Field(default=2, ge=1, le=10, description="Candidate multiplier for fusion")


class SearchResult(BaseModel):
    """Individual search result model"""
    chunk_id: UUID = Field(..., description="Chunk identifier")
    document_id: UUID = Field(..., description="Source document identifier")
    filename: str = Field(..., description="Source document filename")
    chunk_index: int = Field(..., description="Chunk position in document")
    text: str = Field(..., description="Chunk text content")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    score_dense: Optional[float] = Field(None, description="Dense vector similarity score")
    score_sparse: Optional[float] = Field(None, description="Sparse keyword matching score")
    quality_score: Optional[float] = Field(None, description="Document processing quality score")


class SearchResponse(BaseModel):
    """Search response model"""
    status: str = Field(default="success", description="Response status")
    query: str = Field(..., description="Original query text")
    results: List[SearchResult] = Field(..., description="Search results")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="Search metadata")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class RetrievalQuery(BaseModel):
    """Retrieval query entity model"""
    query_id: UUID = Field(default_factory=uuid4, description="Unique query identifier")
    user_id: Optional[UUID] = Field(None, description="User who made the query")
    query_text: str = Field(..., description="Search query text")
    filter_params: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Query timestamp")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")
    result_ids: List[UUID] = Field(default_factory=list, description="Result chunk IDs (max 10)")
    relevance_scores: List[float] = Field(default_factory=list, description="Relevance scores")
