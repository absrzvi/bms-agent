"""Advanced fusion techniques for hybrid search."""

from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FusionStrategy(str, Enum):
    """Fusion strategy types."""
    LINEAR = "linear"  # Weighted linear combination
    RRF = "rrf"  # Reciprocal Rank Fusion
    ADAPTIVE = "adaptive"  # Query-adaptive fusion


class HybridFusion:
    """Advanced fusion for combining semantic and keyword search results."""
    
    def __init__(
        self,
        default_strategy: FusionStrategy = FusionStrategy.RRF,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 60
    ):
        """
        Initialize hybrid fusion.
        
        Args:
            default_strategy: Default fusion strategy
            semantic_weight: Weight for semantic scores (linear fusion)
            keyword_weight: Weight for keyword scores (linear fusion)
            rrf_k: RRF constant (default 60)
        """
        self.default_strategy = default_strategy
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.rrf_k = rrf_k
        
        # Validate weights
        if abs(semantic_weight + keyword_weight - 1.0) > 0.01:
            logger.warning(
                f"Weights don't sum to 1.0: semantic={semantic_weight}, "
                f"keyword={keyword_weight}. Normalizing."
            )
            total = semantic_weight + keyword_weight
            self.semantic_weight = semantic_weight / total
            self.keyword_weight = keyword_weight / total
    
    def fuse(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        strategy: Optional[FusionStrategy] = None,
        query_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Fuse semantic and keyword search results.
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword/BM25 search
            strategy: Fusion strategy (uses default if None)
            query_type: Query type for adaptive fusion
            
        Returns:
            Fused and ranked results
        """
        strategy = strategy or self.default_strategy
        
        if strategy == FusionStrategy.LINEAR:
            return self._linear_fusion(semantic_results, keyword_results)
        elif strategy == FusionStrategy.RRF:
            return self._rrf_fusion(semantic_results, keyword_results)
        elif strategy == FusionStrategy.ADAPTIVE:
            return self._adaptive_fusion(
                semantic_results,
                keyword_results,
                query_type
            )
        else:
            raise ValueError(f"Unknown fusion strategy: {strategy}")
    
    def _linear_fusion(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict]
    ) -> List[Dict]:
        """
        Linear weighted fusion of scores.
        
        Args:
            semantic_results: Semantic search results
            keyword_results: Keyword search results
            
        Returns:
            Fused results with combined scores
        """
        # Build score maps
        chunk_scores = {}
        chunk_data = {}
        
        # Add semantic scores
        for result in semantic_results:
            chunk_id = result.get("id") or result.get("chunk_id")
            if not chunk_id:
                continue
            
            score = result.get("score", 0.0)
            chunk_scores[chunk_id] = {
                "semantic": score,
                "keyword": 0.0
            }
            chunk_data[chunk_id] = result
        
        # Add keyword scores
        for result in keyword_results:
            chunk_id = result.get("id") or result.get("chunk_id")
            if not chunk_id:
                continue
            
            score = result.get("score", 0.0)
            if chunk_id in chunk_scores:
                chunk_scores[chunk_id]["keyword"] = score
            else:
                chunk_scores[chunk_id] = {
                    "semantic": 0.0,
                    "keyword": score
                }
                chunk_data[chunk_id] = result
        
        # Compute fused scores
        fused_results = []
        for chunk_id, scores in chunk_scores.items():
            fused_score = (
                self.semantic_weight * scores["semantic"] +
                self.keyword_weight * scores["keyword"]
            )
            
            result = chunk_data[chunk_id].copy()
            result["fused_score"] = fused_score
            result["semantic_score"] = scores["semantic"]
            result["keyword_score"] = scores["keyword"]
            result["fusion_strategy"] = "linear"
            result["fusion_weights"] = {
                "semantic": self.semantic_weight,
                "keyword": self.keyword_weight
            }
            fused_results.append(result)
        
        # Sort by fused score
        fused_results.sort(key=lambda x: x["fused_score"], reverse=True)
        return fused_results
    
    def _rrf_fusion(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict]
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion.
        
        Args:
            semantic_results: Semantic search results
            keyword_results: Keyword search results
            
        Returns:
            RRF-fused results
        """
        chunk_scores = {}
        chunk_data = {}
        
        # Process semantic results
        for rank, result in enumerate(semantic_results, start=1):
            chunk_id = result.get("id") or result.get("chunk_id")
            if not chunk_id:
                continue
            
            rrf_score = 1.0 / (self.rrf_k + rank)
            chunk_scores[chunk_id] = {
                "rrf": rrf_score,
                "semantic_rank": rank,
                "keyword_rank": None
            }
            chunk_data[chunk_id] = result
        
        # Process keyword results
        for rank, result in enumerate(keyword_results, start=1):
            chunk_id = result.get("id") or result.get("chunk_id")
            if not chunk_id:
                continue
            
            rrf_score = 1.0 / (self.rrf_k + rank)
            
            if chunk_id in chunk_scores:
                chunk_scores[chunk_id]["rrf"] += rrf_score
                chunk_scores[chunk_id]["keyword_rank"] = rank
            else:
                chunk_scores[chunk_id] = {
                    "rrf": rrf_score,
                    "semantic_rank": None,
                    "keyword_rank": rank
                }
                chunk_data[chunk_id] = result
        
        # Build fused results
        fused_results = []
        for chunk_id, scores in chunk_scores.items():
            result = chunk_data[chunk_id].copy()
            result["rrf_score"] = scores["rrf"]
            result["semantic_rank"] = scores["semantic_rank"]
            result["keyword_rank"] = scores["keyword_rank"]
            result["fusion_strategy"] = "rrf"
            result["rrf_k"] = self.rrf_k
            fused_results.append(result)
        
        # Sort by RRF score
        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_results
    
    def _adaptive_fusion(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        query_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Query-adaptive fusion based on query type.
        
        Technical queries favor keyword search (more precise terminology).
        General queries favor semantic search (conceptual matching).
        
        Args:
            semantic_results: Semantic search results
            keyword_results: Keyword search results
            query_type: Query type (technical, procedural, safety, general)
            
        Returns:
            Adaptively fused results
        """
        # Determine adaptive weights based on query type
        if query_type == "technical":
            # Technical queries: favor keyword matching (60/40)
            sem_weight = 0.4
            key_weight = 0.6
        elif query_type == "procedural":
            # Procedural queries: balanced (50/50)
            sem_weight = 0.5
            key_weight = 0.5
        elif query_type == "safety":
            # Safety queries: favor keyword (standards/regulations)
            sem_weight = 0.35
            key_weight = 0.65
        else:
            # General queries: favor semantic (70/30)
            sem_weight = 0.7
            key_weight = 0.3
        
        # Use linear fusion with adaptive weights
        original_sem_weight = self.semantic_weight
        original_key_weight = self.keyword_weight
        
        self.semantic_weight = sem_weight
        self.keyword_weight = key_weight
        
        results = self._linear_fusion(semantic_results, keyword_results)
        
        # Restore original weights
        self.semantic_weight = original_sem_weight
        self.keyword_weight = original_key_weight
        
        # Update fusion metadata
        for result in results:
            result["fusion_strategy"] = "adaptive"
            result["query_type"] = query_type
        
        return results
