"""
Pydantic models for reranking requests and responses
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RerankRequest(BaseModel):
    """Request model for reranking endpoint"""
    query: str = Field(..., min_length=1, description="Search query")
    results: List[Dict[str, Any]] = Field(..., description="Search results to rerank")
    top_k: int = Field(20, ge=1, le=100, description="Number of results to rerank")
    retrieval_weight: float = Field(0.7, ge=0.0, le=1.0, description="Weight for retrieval scores")
    rerank_weight: float = Field(0.3, ge=0.0, le=1.0, description="Weight for rerank scores")
    min_rerank_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum rerank score threshold")
    use_cache: bool = Field(True, description="Use cached reranking results if available")


class RerankResultItem(BaseModel):
    """Single reranked result item"""
    chunk_id: str
    content: str
    retrieval_score: float
    rerank_score: float
    combined_score: float
    metadata: Dict[str, Any]
    rank: int
    original_rank: int


class RerankResponse(BaseModel):
    """Response model for reranking endpoint"""
    status: str
    query: str
    results: List[RerankResultItem]
    count: int
    reranking_time_ms: float
    model_info: Dict[str, Any]
    timestamp: str
