"""
Cross-Encoder Reranking Pipeline
Implements reranking stage for improved relevance using cross-encoder models
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Reranked search result"""
    chunk_id: str
    content: str
    retrieval_score: float
    rerank_score: float
    combined_score: float
    metadata: Dict[str, Any]
    rank: int
    original_rank: int


class CrossEncoderReranker:
    """
    Cross-encoder reranking for improved relevance
    Uses sentence-transformers cross-encoder models
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        retrieval_weight: float = 0.7,
        rerank_weight: float = 0.3,
        batch_size: int = 32,
        device: str = "cpu"
    ):
        """
        Initialize cross-encoder reranker
        
        Args:
            model_name: Cross-encoder model name
            retrieval_weight: Weight for original retrieval scores (0.0-1.0)
            rerank_weight: Weight for reranking scores (0.0-1.0)
            batch_size: Batch size for reranking
            device: Device for model inference (cpu/cuda)
        """
        self.model_name = model_name
        self.retrieval_weight = retrieval_weight
        self.rerank_weight = rerank_weight
        self.batch_size = batch_size
        self.device = device
        
        # Validate weights
        total_weight = retrieval_weight + rerank_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, normalizing...")
            self.retrieval_weight = retrieval_weight / total_weight
            self.rerank_weight = rerank_weight / total_weight
        
        # Lazy load model
        self._model = None
        self._model_loaded = False
    
    def _load_model(self):
        """Lazy load cross-encoder model"""
        if self._model_loaded:
            return
        
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            start_time = time.time()
            
            self._model = CrossEncoder(
                self.model_name,
                max_length=512,
                device=self.device
            )
            
            load_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Cross-encoder model loaded in {load_time:.2f}ms")
            self._model_loaded = True
            
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        min_rerank_score: Optional[float] = None
    ) -> List[RerankResult]:
        """
        Rerank search results using cross-encoder
        
        Args:
            query: Search query
            results: Initial search results with 'content' and 'score' fields
            top_k: Number of top results to rerank (None = all)
            min_rerank_score: Minimum reranking score threshold
            
        Returns:
            List of reranked results sorted by combined score
        """
        if not results:
            return []
        
        # Load model if not already loaded
        self._load_model()
        
        # Limit to top_k if specified
        results_to_rerank = results[:top_k] if top_k else results
        
        # Prepare query-document pairs
        pairs = []
        for result in results_to_rerank:
            content = result.get("content", "")
            # Truncate content if too long (cross-encoder has 512 token limit)
            if len(content) > 2000:
                content = content[:2000] + "..."
            pairs.append([query, content])
        
        # Batch reranking
        logger.debug(f"Reranking {len(pairs)} results in batches of {self.batch_size}")
        start_time = time.time()
        
        try:
            rerank_scores = self._model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False
            )
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return original results without reranking
            return self._format_results_without_reranking(results)
        
        rerank_time = (time.time() - start_time) * 1000
        logger.debug(f"Reranking completed in {rerank_time:.2f}ms")
        
        # Combine scores and create reranked results
        reranked_results = []
        for idx, (result, rerank_score) in enumerate(zip(results_to_rerank, rerank_scores)):
            retrieval_score = result.get("score", 0.0)
            
            # Normalize rerank score to 0-1 range (cross-encoder outputs can be negative)
            # Using sigmoid to map to 0-1
            normalized_rerank_score = self._sigmoid(float(rerank_score))
            
            # Calculate combined score
            combined_score = (
                self.retrieval_weight * retrieval_score +
                self.rerank_weight * normalized_rerank_score
            )
            
            # Apply min_rerank_score filter if specified
            if min_rerank_score is not None and normalized_rerank_score < min_rerank_score:
                continue
            
            reranked_results.append(
                RerankResult(
                    chunk_id=result.get("chunk_id", result.get("id", str(idx))),
                    content=result.get("content", ""),
                    retrieval_score=retrieval_score,
                    rerank_score=normalized_rerank_score,
                    combined_score=combined_score,
                    metadata=result.get("metadata", {}),
                    rank=0,  # Will be set after sorting
                    original_rank=idx
                )
            )
        
        # Sort by combined score
        reranked_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Update ranks
        for rank, result in enumerate(reranked_results):
            result.rank = rank
        
        return reranked_results
    
    def rerank_with_context(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        include_parent: bool = True
    ) -> List[RerankResult]:
        """
        Rerank with parent context for better relevance
        
        Args:
            query: Search query
            results: Search results with optional 'parent_content' field
            top_k: Number of results to rerank
            include_parent: Include parent content in reranking
            
        Returns:
            Reranked results
        """
        if not include_parent:
            return self.rerank(query, results, top_k)
        
        # Enhance content with parent context
        enhanced_results = []
        for result in results:
            enhanced_result = result.copy()
            
            content = result.get("content", "")
            parent_content = result.get("parent_content", "")
            
            if parent_content:
                # Combine parent and chunk content
                enhanced_content = f"{parent_content}\n\n{content}"
                enhanced_result["content"] = enhanced_content
            
            enhanced_results.append(enhanced_result)
        
        return self.rerank(query, enhanced_results, top_k)
    
    @staticmethod
    def _sigmoid(x: float) -> float:
        """Sigmoid function to normalize scores to 0-1 range"""
        import math
        try:
            return 1 / (1 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0
    
    def _format_results_without_reranking(
        self,
        results: List[Dict[str, Any]]
    ) -> List[RerankResult]:
        """Format results without reranking (fallback)"""
        formatted_results = []
        for idx, result in enumerate(results):
            formatted_results.append(
                RerankResult(
                    chunk_id=result.get("chunk_id", result.get("id", str(idx))),
                    content=result.get("content", ""),
                    retrieval_score=result.get("score", 0.0),
                    rerank_score=0.0,
                    combined_score=result.get("score", 0.0),
                    metadata=result.get("metadata", {}),
                    rank=idx,
                    original_rank=idx
                )
            )
        return formatted_results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "retrieval_weight": self.retrieval_weight,
            "rerank_weight": self.rerank_weight,
            "batch_size": self.batch_size,
            "device": self.device,
            "model_loaded": self._model_loaded
        }


class RerankingPipeline:
    """
    Complete reranking pipeline with caching and optimization
    """
    
    def __init__(
        self,
        reranker: CrossEncoderReranker,
        enable_cache: bool = True,
        cache_size: int = 1000
    ):
        """
        Initialize reranking pipeline
        
        Args:
            reranker: CrossEncoderReranker instance
            enable_cache: Enable result caching
            cache_size: Maximum cache size
        """
        self.reranker = reranker
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        
        # Simple LRU cache
        self._cache = {}
        self._cache_order = []
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 20,
        use_cache: bool = True
    ) -> List[RerankResult]:
        """
        Rerank with optional caching
        
        Args:
            query: Search query
            results: Search results
            top_k: Number of results to rerank
            use_cache: Use cached results if available
            
        Returns:
            Reranked results
        """
        # Check cache
        if use_cache and self.enable_cache:
            cache_key = self._get_cache_key(query, results[:top_k])
            if cache_key in self._cache:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return self._cache[cache_key]
        
        # Perform reranking
        reranked = self.reranker.rerank(query, results, top_k)
        
        # Update cache
        if self.enable_cache:
            self._update_cache(cache_key, reranked)
        
        return reranked
    
    def _get_cache_key(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate cache key from query and results"""
        import hashlib
        
        # Create hash from query and result IDs
        result_ids = [r.get("chunk_id", r.get("id", "")) for r in results]
        cache_str = f"{query}:{'|'.join(result_ids)}"
        
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _update_cache(self, key: str, value: List[RerankResult]):
        """Update cache with LRU eviction"""
        if key in self._cache:
            # Move to end (most recent)
            self._cache_order.remove(key)
            self._cache_order.append(key)
        else:
            # Add new entry
            if len(self._cache) >= self.cache_size:
                # Evict oldest
                oldest_key = self._cache_order.pop(0)
                del self._cache[oldest_key]
            
            self._cache[key] = value
            self._cache_order.append(key)
    
    def clear_cache(self):
        """Clear reranking cache"""
        self._cache.clear()
        self._cache_order.clear()
        logger.info("Reranking cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size,
            "cache_enabled": self.enable_cache
        }
