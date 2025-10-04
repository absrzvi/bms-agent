"""
Tests for semantic caching functionality
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from api.cache.semantic_cache import SemanticCache, CacheManager, CacheEntry


@pytest.fixture
def semantic_cache():
    """Create semantic cache instance"""
    return SemanticCache(
        max_size=10,
        similarity_threshold=0.95,
        ttl_seconds=3600
    )


def test_cache_initialization(semantic_cache):
    """Test cache initialization"""
    assert semantic_cache.max_size == 10
    assert semantic_cache.similarity_threshold == 0.95
    assert semantic_cache.ttl_seconds == 3600
    assert len(semantic_cache._cache) == 0


def test_cache_put_and_get(semantic_cache):
    """Test basic cache put and get"""
    query = "test query"
    embedding = [0.1] * 768
    results = [{"chunk_id": "1", "content": "test"}]
    
    # Put in cache
    semantic_cache.put(query, embedding, results)
    
    # Get from cache (exact match)
    cached_results = semantic_cache.get(query, embedding)
    
    assert cached_results is not None
    assert len(cached_results) == 1
    assert cached_results[0]["chunk_id"] == "1"


def test_cache_similarity_match(semantic_cache):
    """Test cache hit with similar query"""
    query1 = "railway safety procedures"
    embedding1 = [0.1, 0.2, 0.3] + [0.0] * 765
    results1 = [{"chunk_id": "1", "content": "safety"}]
    
    # Cache first query
    semantic_cache.put(query1, embedding1, results1)
    
    # Similar query (high similarity)
    query2 = "railway safety protocols"
    embedding2 = [0.11, 0.21, 0.31] + [0.0] * 765  # Very similar
    
    cached_results = semantic_cache.get(query2, embedding2)
    
    # Should get cache hit due to high similarity
    assert cached_results is not None


def test_cache_miss_low_similarity(semantic_cache):
    """Test cache miss with low similarity"""
    query1 = "railway safety"
    embedding1 = [1.0, 0.0, 0.0] + [0.0] * 765
    results1 = [{"chunk_id": "1"}]
    
    semantic_cache.put(query1, embedding1, results1)
    
    # Very different query
    query2 = "train schedule"
    embedding2 = [0.0, 1.0, 0.0] + [0.0] * 765
    
    cached_results = semantic_cache.get(query2, embedding2)
    
    # Should be cache miss
    assert cached_results is None


def test_cache_lru_eviction(semantic_cache):
    """Test LRU eviction when cache is full"""
    # Fill cache to max
    for i in range(10):
        query = f"query {i}"
        embedding = [float(i)] + [0.0] * 767
        results = [{"chunk_id": str(i)}]
        semantic_cache.put(query, embedding, results)
    
    assert len(semantic_cache._cache) == 10
    
    # Add one more - should evict oldest
    query_new = "query 10"
    embedding_new = [10.0] + [0.0] * 767
    results_new = [{"chunk_id": "10"}]
    semantic_cache.put(query_new, embedding_new, results_new)
    
    assert len(semantic_cache._cache) == 10
    assert semantic_cache._evictions == 1


def test_cache_ttl_expiration(semantic_cache):
    """Test TTL expiration"""
    # Create cache with short TTL
    short_ttl_cache = SemanticCache(max_size=10, ttl_seconds=1)
    
    query = "test query"
    embedding = [0.1] * 768
    results = [{"chunk_id": "1"}]
    
    short_ttl_cache.put(query, embedding, results)
    
    # Should be in cache
    cached = short_ttl_cache.get(query, embedding)
    assert cached is not None
    
    # Wait for expiration
    import time
    time.sleep(1.1)
    
    # Should be expired
    cached = short_ttl_cache.get(query, embedding)
    assert cached is None


def test_cache_stats(semantic_cache):
    """Test cache statistics"""
    query = "test"
    embedding = [0.1] * 768
    results = [{"chunk_id": "1"}]
    
    # Put and get
    semantic_cache.put(query, embedding, results)
    semantic_cache.get(query, embedding)  # Hit
    
    # Very different embedding for guaranteed miss
    different_embedding = [-0.9] * 768
    semantic_cache.get("other", different_embedding)  # Miss
    
    stats = semantic_cache.get_stats()
    
    assert stats["size"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["total_lookups"] == 2
    assert stats["hit_rate"] == 50.0


def test_cache_clear(semantic_cache):
    """Test cache clearing"""
    # Add some entries
    for i in range(5):
        semantic_cache.put(f"query {i}", [float(i)] * 768, [{"id": str(i)}])
    
    assert len(semantic_cache._cache) == 5
    
    semantic_cache.clear()
    
    assert len(semantic_cache._cache) == 0


def test_cache_warm(semantic_cache):
    """Test cache warming"""
    queries = [
        ("query 1", [0.1] * 768, [{"id": "1"}]),
        ("query 2", [0.2] * 768, [{"id": "2"}]),
        ("query 3", [0.3] * 768, [{"id": "3"}])
    ]
    
    semantic_cache.warm_cache(queries)
    
    assert len(semantic_cache._cache) == 3


def test_top_queries(semantic_cache):
    """Test getting top queries"""
    # Add queries with different hit counts
    for i in range(5):
        query = f"query {i}"
        embedding = [float(i)] * 768
        results = [{"id": str(i)}]
        
        semantic_cache.put(query, embedding, results)
        
        # Access some queries more than others
        for _ in range(i):
            semantic_cache.get(query, embedding)
    
    top_queries = semantic_cache.get_top_queries(limit=3)
    
    assert len(top_queries) == 3
    # Should be sorted by hit count (descending)
    assert top_queries[0]["hit_count"] >= top_queries[1]["hit_count"]


def test_invalidate_expired(semantic_cache):
    """Test invalidating expired entries"""
    # Create cache with short TTL
    short_ttl_cache = SemanticCache(max_size=10, ttl_seconds=1)
    
    # Add entries
    for i in range(5):
        short_ttl_cache.put(f"query {i}", [float(i)] * 768, [{"id": str(i)}])
    
    assert len(short_ttl_cache._cache) == 5
    
    # Wait for expiration
    import time
    time.sleep(1.1)
    
    # Invalidate expired
    short_ttl_cache.invalidate_expired()
    
    assert len(short_ttl_cache._cache) == 0


def test_cache_manager():
    """Test cache manager"""
    manager = CacheManager()
    
    # Create caches
    cache1 = manager.create_cache("cache1", max_size=100)
    cache2 = manager.create_cache("cache2", max_size=200)
    
    assert manager.get_cache("cache1") == cache1
    assert manager.get_cache("cache2") == cache2
    assert manager.get_cache("default") == cache1  # First created is default


def test_cache_manager_stats():
    """Test cache manager statistics"""
    manager = CacheManager()
    
    cache1 = manager.create_cache("cache1")
    cache2 = manager.create_cache("cache2")
    
    # Add some data
    cache1.put("query1", [0.1] * 768, [{"id": "1"}])
    cache2.put("query2", [0.2] * 768, [{"id": "2"}])
    
    all_stats = manager.get_all_stats()
    
    assert "cache1" in all_stats
    assert "cache2" in all_stats
    assert all_stats["cache1"]["size"] == 1
    assert all_stats["cache2"]["size"] == 1


def test_cache_entry_dataclass():
    """Test CacheEntry dataclass"""
    entry = CacheEntry(
        query="test query",
        query_embedding=[0.1] * 768,
        results=[{"id": "1"}],
        timestamp=datetime.now()
    )
    
    assert entry.query == "test query"
    assert len(entry.query_embedding) == 768
    assert entry.hit_count == 0
    assert isinstance(entry.last_accessed, datetime)


def test_cosine_similarity():
    """Test cosine similarity calculation"""
    import numpy as np
    
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([1.0, 0.0, 0.0])
    
    similarity = SemanticCache._cosine_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 0.01  # Identical vectors
    
    vec3 = np.array([0.0, 1.0, 0.0])
    similarity = SemanticCache._cosine_similarity(vec1, vec3)
    assert abs(similarity - 0.0) < 0.01  # Orthogonal vectors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
