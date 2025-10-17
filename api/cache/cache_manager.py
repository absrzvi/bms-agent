"""
Cached search wrapper for integrating semantic cache with search endpoints
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from .semantic_cache import SemanticCache

logger = logging.getLogger(__name__)


class CachedSearchWrapper:
    """
    Wrapper for search functions with semantic caching
    """
    
    def __init__(
        self,
        cache: SemanticCache,
        enable_cache: bool = True
    ):
        """
        Initialize cached search wrapper
        
        Args:
            cache: SemanticCache instance
            enable_cache: Enable/disable caching
        """
        self.cache = cache
        self.enable_cache = enable_cache
    
    def search(
        self,
        query: str,
        query_embedding: List[float],
        search_func: Callable,
        use_cache: bool = True,
        **search_kwargs
    ) -> Dict[str, Any]:
        """
        Perform search with caching
        
        Args:
            query: Search query
            query_embedding: Query embedding vector
            search_func: Search function to call on cache miss
            use_cache: Use cache for this search
            **search_kwargs: Additional arguments for search function
            
        Returns:
            Search results with cache metadata
        """
        cache_hit = False
        cache_time_ms = 0.0
        search_time_ms = 0.0
        
        # Try cache first if enabled
        if self.enable_cache and use_cache:
            start_time = time.time()
            cached_results = self.cache.get(query, query_embedding)
            cache_time_ms = (time.time() - start_time) * 1000
            
            if cached_results is not None:
                cache_hit = True
                logger.info(f"✅ Cache hit for query: {query[:50]}... ({cache_time_ms:.2f}ms)")
                
                return {
                    "results": cached_results,
                    "cache_hit": True,
                    "cache_time_ms": cache_time_ms,
                    "search_time_ms": 0.0,
                    "total_time_ms": cache_time_ms
                }
        
        # Cache miss - perform actual search
        start_time = time.time()
        results = search_func(query_embedding=query_embedding, **search_kwargs)
        search_time_ms = (time.time() - start_time) * 1000
        
        # Store in cache if enabled
        if self.enable_cache and use_cache:
            self.cache.put(query, query_embedding, results)
        
        total_time_ms = cache_time_ms + search_time_ms
        
        logger.info(f"Cache miss for query: {query[:50]}... ({search_time_ms:.2f}ms)")
        
        return {
            "results": results,
            "cache_hit": False,
            "cache_time_ms": cache_time_ms,
            "search_time_ms": search_time_ms,
            "total_time_ms": total_time_ms
        }
    
    def invalidate_cache(self):
        """Invalidate (clear) the cache"""
        self.cache.clear()
        logger.info("Cache invalidated")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
