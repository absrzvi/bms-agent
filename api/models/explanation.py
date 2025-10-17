"""Models for retrieval explanations."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Breakdown of score components."""
    semantic_score: Optional[float] = Field(None, description="Semantic similarity score")
    keyword_score: Optional[float] = Field(None, description="Keyword/BM25 score")
    metadata_boost: Optional[float] = Field(None, description="Metadata-based boost")
    rerank_score: Optional[float] = Field(None, description="Reranking score")
    quality_boost: Optional[float] = Field(None, description="Quality score boost")
    final_score: float = Field(..., description="Final combined score")
    fusion_method: Optional[str] = Field(None, description="Fusion method used")


class MatchedKeyword(BaseModel):
    """Matched keyword information."""
    keyword: str = Field(..., description="Matched keyword")
    frequency: int = Field(..., description="Frequency in chunk")
    positions: List[int] = Field(default_factory=list, description="Character positions")


class MatchedEntity(BaseModel):
    """Matched entity information."""
    entity: str = Field(..., description="Matched entity")
    entity_type: str = Field(..., description="Entity type (train_id, component, standard)")
    confidence: float = Field(..., description="Match confidence")


class RetrievalExplanation(BaseModel):
    """Explanation for why a chunk was retrieved."""
    chunk_id: str = Field(..., description="Chunk identifier")
    rank: int = Field(..., description="Rank in results")
    score_breakdown: ScoreBreakdown = Field(..., description="Score component breakdown")
    matched_keywords: List[MatchedKeyword] = Field(default_factory=list, description="Matched keywords")
    matched_entities: List[MatchedEntity] = Field(default_factory=list, description="Matched entities")
    similarity_explanation: Optional[str] = Field(None, description="Human-readable similarity explanation")
    metadata_matches: Dict[str, Any] = Field(default_factory=dict, description="Metadata field matches")
    debug_info: Optional[Dict] = Field(None, description="Additional debug information")


class QueryExplanation(BaseModel):
    """Explanation for query processing."""
    original_query: str = Field(..., description="Original query text")
    query_type: Optional[str] = Field(None, description="Classified query type")
    extracted_entities: List[MatchedEntity] = Field(default_factory=list, description="Extracted entities")
    query_expansion: Optional[List[str]] = Field(None, description="Expanded query variations")
    filters_applied: Optional[Dict] = Field(None, description="Filters applied to search")
    search_strategy: Optional[str] = Field(None, description="Search strategy used")
