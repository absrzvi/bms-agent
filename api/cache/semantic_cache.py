"""
Semantic Caching Layer
Implements embedding-based cache for improved search performance
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Semantic cache entry"""
    query: str
    query_embedding: List[float]
    results: List[Dict[str, Any]]
    timestamp: datetime
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class SemanticCache:
    """
    Semantic cache using embedding similarity for cache lookup
    Uses approximate nearest neighbor search for cache hits
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600,
        enable_analytics: bool = True
    ):
        """
        Initialize semantic cache
        
        Args:
            max_size: Maximum number of cache entries
            similarity_threshold: Minimum cosine similarity for cache hit (0.0-1.0)
            ttl_seconds: Time-to-live for cache entries in seconds
            enable_analytics: Enable cache analytics tracking
        """
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.enable_analytics = enable_analytics
        
        # Cache storage (OrderedDict for LRU)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Analytics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._total_lookups = 0
        
        logger.info(f"✅ Semantic cache initialized: max_size={max_size}, threshold={similarity_threshold}, ttl={ttl_seconds}s")
    
    def get(
        self,
        query: str,
        query_embedding: List[float]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results for query using semantic similarity
        
        Args:
            query: Search query
            query_embedding: Query embedding vector
            
        Returns:
            Cached results if found, None otherwise
        """
        self._total_lookups += 1
        
        if not self._cache:
            self._misses += 1
            return None
        
        # Find most similar cached query
        best_match = self._find_similar_query(query_embedding)
        
        if best_match is None:
            self._misses += 1
            logger.debug(f"Cache miss: {query[:50]}...")
            return None
        
        cache_key, similarity, entry = best_match
        
        # Check if similarity meets threshold
        if similarity < self.similarity_threshold:
            self._misses += 1
            logger.debug(f"Cache miss (low similarity {similarity:.3f}): {query[:50]}...")
            return None
        
        # Check TTL
        if self._is_expired(entry):
            logger.debug(f"Cache expired: {query[:50]}...")
            del self._cache[cache_key]
            self._misses += 1
            return None
        
        # Cache hit!
        self._hits += 1
        entry.hit_count += 1
        entry.last_accessed = datetime.now()
        
        # Move to end (most recently used)
        self._cache.move_to_end(cache_key)
        
        logger.debug(f"✅ Cache hit (similarity {similarity:.3f}): {query[:50]}...")
        return entry.results
    
    def put(
        self,
        query: str,
        query_embedding: List[float],
        results: List[Dict[str, Any]]
    ):
        """
        Store query results in cache
        
        Args:
            query: Search query
            query_embedding: Query embedding vector
            results: Search results to cache
        """
        # Generate cache key
        cache_key = self._generate_key(query, query_embedding)
        
        # Check if already cached
        if cache_key in self._cache:
            # Update existing entry
            entry = self._cache[cache_key]
            entry.results = results
            entry.timestamp = datetime.now()
            entry.last_accessed = datetime.now()
            self._cache.move_to_end(cache_key)
            logger.debug(f"Updated cache entry: {query[:50]}...")
            return
        
        # Check size limit
        if len(self._cache) >= self.max_size:
            # Evict oldest (LRU)
            evicted_key, evicted_entry = self._cache.popitem(last=False)
            self._evictions += 1
            logger.debug(f"Evicted cache entry: {evicted_entry.query[:50]}...")
        
        # Add new entry
        entry = CacheEntry(
            query=query,
            query_embedding=query_embedding,
            results=results,
            timestamp=datetime.now()
        )
        
        self._cache[cache_key] = entry
        logger.debug(f"Cached query: {query[:50]}...")
    
    def _find_similar_query(
        self,
        query_embedding: List[float]
    ) -> Optional[Tuple[str, float, CacheEntry]]:
        """
        Find most similar cached query using cosine similarity
        
        Returns:
            Tuple of (cache_key, similarity, entry) or None
        """
        best_similarity = 0.0
        best_match = None
        
        query_vec = np.array(query_embedding)
        
        for cache_key, entry in self._cache.items():
            # Skip expired entries
            if self._is_expired(entry):
                continue
            
            # Calculate cosine similarity
            cached_vec = np.array(entry.query_embedding)
            similarity = self._cosine_similarity(query_vec, cached_vec)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (cache_key, similarity, entry)
        
        return best_match
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        age = datetime.now() - entry.timestamp
        return age.total_seconds() > self.ttl_seconds
    
    def _generate_key(self, query: str, query_embedding: List[float]) -> str:
        """Generate cache key from query and embedding"""
        # Use hash of query + first few embedding values for uniqueness
        embedding_sample = str(query_embedding[:10])
        key_str = f"{query}:{embedding_sample}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")
    
    def invalidate_expired(self):
        """Remove expired entries from cache"""
        expired_keys = []
        
        for cache_key, entry in self._cache.items():
            if self._is_expired(entry):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Invalidated {len(expired_keys)} expired cache entries")
    
    def warm_cache(self, queries: List[Tuple[str, List[float], List[Dict[str, Any]]]]):
        """
        Warm cache with common queries
        
        Args:
            queries: List of (query, embedding, results) tuples
        """
        for query, embedding, results in queries:
            self.put(query, embedding, results)
        
        logger.info(f"Cache warmed with {len(queries)} queries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = (self._hits / self._total_lookups * 100) if self._total_lookups > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "evictions": self._evictions,
            "total_lookups": self._total_lookups,
            "similarity_threshold": self.similarity_threshold,
            "ttl_seconds": self.ttl_seconds
        }
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed queries"""
        sorted_entries = sorted(
            self._cache.values(),
            key=lambda x: x.hit_count,
            reverse=True
        )
        
        return [
            {
                "query": entry.query,
                "hit_count": entry.hit_count,
                "last_accessed": entry.last_accessed.isoformat(),
                "age_seconds": (datetime.now() - entry.timestamp).total_seconds()
            }
            for entry in sorted_entries[:limit]
        ]
    
    def reset_stats(self):
        """Reset cache statistics"""
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._total_lookups = 0
        logger.info("Cache statistics reset")


class CacheManager:
    """
    Cache manager with multiple cache instances and strategies
    """
    
    def __init__(self):
        """Initialize cache manager"""
        self._caches: Dict[str, SemanticCache] = {}
        self._default_cache = None
    
    def create_cache(
        self,
        name: str,
        max_size: int = 1000,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600
    ) -> SemanticCache:
        """Create a named cache instance"""
        cache = SemanticCache(
            max_size=max_size,
            similarity_threshold=similarity_threshold,
            ttl_seconds=ttl_seconds
        )
        
        self._caches[name] = cache
        
        if self._default_cache is None:
            self._default_cache = cache
        
        logger.info(f"Created cache: {name}")
        return cache
    
    def get_cache(self, name: str = "default") -> Optional[SemanticCache]:
        """Get cache by name"""
        if name == "default":
            return self._default_cache
        return self._caches.get(name)
    
    def clear_all(self):
        """Clear all caches"""
        for cache in self._caches.values():
            cache.clear()
        logger.info("All caches cleared")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }


# Global cache manager instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    return _cache_manager
