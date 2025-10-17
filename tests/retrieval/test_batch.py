"""Tests for batch retrieval optimization."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from api.retrieval.batch import BatchRetriever, BatchEmbeddingCache


class TestBatchRetriever:
    """Test batch retrieval."""
    
    @pytest.fixture
    def mock_embedding_fn(self):
        """Mock embedding function."""
        async def embed(texts):
            # Return simple embeddings based on text length
            return [[float(len(t))] * 768 for t in texts]
        return embed
    
    @pytest.fixture
    def mock_search_fn(self):
        """Mock search function."""
        async def search(embedding, k, filters=None):
            # Return mock results based on embedding
            score = embedding[0] / 100.0  # Use first dimension
            return [
                {"id": f"chunk{i}", "score": score - (i * 0.1), "text": f"Result {i}"}
                for i in range(k)
            ]
        return search
    
    @pytest.fixture
    def retriever(self, mock_embedding_fn, mock_search_fn):
        """Create batch retriever instance."""
        return BatchRetriever(
            embedding_fn=mock_embedding_fn,
            search_fn=mock_search_fn,
            max_batch_size=50
        )
    
    @pytest.mark.asyncio
    async def test_batch_search(self, retriever):
        """Test basic batch search."""
        queries = ["query one", "query two", "query three"]
        results = await retriever.batch_search(queries, k=5, deduplicate=False)
        
        assert len(results) == 3
        assert all(len(r) == 5 for r in results)
        assert all(isinstance(r, list) for r in results)
    
    @pytest.mark.asyncio
    async def test_batch_search_empty(self, retriever):
        """Test batch search with empty query list."""
        results = await retriever.batch_search([], k=5)
        assert results == []
    
    @pytest.mark.asyncio
    async def test_batch_search_deduplication(self, retriever):
        """Test result deduplication."""
        queries = ["query", "query"]  # Same query twice
        results = await retriever.batch_search(queries, k=5, deduplicate=True)
        
        # Second query should have fewer results due to deduplication
        assert len(results) == 2
        assert len(results[1]) < len(results[0])
    
    @pytest.mark.asyncio
    async def test_batch_search_no_deduplication(self, retriever):
        """Test without deduplication."""
        queries = ["query", "query"]
        results = await retriever.batch_search(queries, k=5, deduplicate=False)
        
        # Both should have same number of results
        assert len(results) == 2
        assert len(results[0]) == len(results[1])
    
    @pytest.mark.asyncio
    async def test_batch_search_large_batch(self, retriever):
        """Test with batch size exceeding maximum."""
        queries = [f"query {i}" for i in range(100)]  # Exceeds max_batch_size of 50
        results = await retriever.batch_search(queries, k=3, deduplicate=False)
        
        assert len(results) == 100
        assert all(len(r) == 3 for r in results)
    
    def test_union_results(self, retriever):
        """Test union aggregation."""
        result_lists = [
            [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}],
            [{"id": "2", "score": 0.85}, {"id": "3", "score": 0.7}]
        ]
        
        union = retriever.aggregate_results(result_lists, aggregation="union")
        
        assert len(union) == 3  # 3 unique chunks
        chunk_ids = {r["id"] for r in union}
        assert chunk_ids == {"1", "2", "3"}
    
    def test_intersection_results(self, retriever):
        """Test intersection aggregation."""
        result_lists = [
            [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}],
            [{"id": "2", "score": 0.85}, {"id": "3", "score": 0.7}]
        ]
        
        intersection = retriever.aggregate_results(result_lists, aggregation="intersection")
        
        assert len(intersection) == 1  # Only chunk 2 appears in both
        assert intersection[0]["id"] == "2"
    
    def test_ranked_fusion(self, retriever):
        """Test ranked fusion aggregation."""
        result_lists = [
            [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}],
            [{"id": "2", "score": 0.85}, {"id": "3", "score": 0.7}]
        ]
        
        fused = retriever.aggregate_results(result_lists, aggregation="ranked_fusion")
        
        assert len(fused) == 3
        assert all("aggregated_score" in r for r in fused)
        
        # chunk 2 appears in both, should have highest aggregated score
        chunk2 = next(r for r in fused if r["id"] == "2")
        assert chunk2["aggregated_score"] > fused[1]["aggregated_score"]
    
    def test_invalid_aggregation(self, retriever):
        """Test invalid aggregation method."""
        result_lists = [[{"id": "1"}]]
        
        with pytest.raises(ValueError, match="Unknown aggregation method"):
            retriever.aggregate_results(result_lists, aggregation="invalid")


class TestBatchEmbeddingCache:
    """Test batch embedding cache."""
    
    @pytest.fixture
    def cache(self):
        """Create cache instance."""
        return BatchEmbeddingCache(max_size=10)
    
    def test_cache_put_get(self, cache):
        """Test basic put and get."""
        embedding = [0.1, 0.2, 0.3]
        cache.put("test query", embedding)
        
        result = cache.get("test query")
        assert result == embedding
    
    def test_cache_miss(self, cache):
        """Test cache miss."""
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_eviction(self, cache):
        """Test LRU eviction when cache is full."""
        # Fill cache to max
        for i in range(10):
            cache.put(f"query{i}", [float(i)])
        
        # Access some queries to increase their count
        cache.get("query5")
        cache.get("query5")
        cache.get("query7")
        
        # Add one more (should evict least accessed)
        cache.put("query10", [10.0])
        
        # query0 should be evicted (least accessed)
        assert cache.get("query0") is None
        # query5 should still be there (most accessed)
        assert cache.get("query5") is not None
    
    def test_get_batch(self, cache):
        """Test batch get."""
        cache.put("query1", [1.0])
        cache.put("query2", [2.0])
        
        texts = ["query1", "query2", "query3"]
        cached, uncached = cache.get_batch(texts)
        
        assert len(cached) == 2
        assert uncached == ["query3"]
    
    def test_put_batch(self, cache):
        """Test batch put."""
        texts = ["query1", "query2", "query3"]
        embeddings = [[1.0], [2.0], [3.0]]
        
        cache.put_batch(texts, embeddings)
        
        assert cache.get("query1") == [1.0]
        assert cache.get("query2") == [2.0]
        assert cache.get("query3") == [3.0]
    
    def test_clear(self, cache):
        """Test cache clear."""
        cache.put("query1", [1.0])
        cache.put("query2", [2.0])
        
        cache.clear()
        
        assert cache.get("query1") is None
        assert cache.get("query2") is None
        assert len(cache.cache) == 0
    
    def test_stats(self, cache):
        """Test cache statistics."""
        cache.put("query1", [1.0])
        cache.put("query2", [2.0])
        cache.get("query1")
        cache.get("query1")
        
        stats = cache.stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["unique_queries"] == 2
        assert stats["total_accesses"] > 0
    
    def test_access_count_tracking(self, cache):
        """Test that access counts are tracked correctly."""
        cache.put("query1", [1.0])
        
        # Access multiple times
        for _ in range(5):
            cache.get("query1")
        
        assert cache.access_count["query1"] == 6  # 1 from put + 5 from gets


class TestBatchRetrievalIntegration:
    """Integration tests for batch retrieval."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_batch_search(self):
        """Test end-to-end batch search workflow."""
        # Mock functions
        async def embed(texts):
            return [[float(len(t))] * 10 for t in texts]
        
        async def search(embedding, k, filters=None):
            return [
                {"id": f"chunk{i}", "score": 0.9 - (i * 0.1)}
                for i in range(k)
            ]
        
        retriever = BatchRetriever(embed, search, max_batch_size=10)
        
        queries = ["short", "medium length", "very long query text"]
        results = await retriever.batch_search(queries, k=5, deduplicate=False)
        
        assert len(results) == 3
        assert all(len(r) == 5 for r in results)
    
    @pytest.mark.asyncio
    async def test_batch_with_caching(self):
        """Test batch retrieval with caching."""
        call_count = 0
        
        async def embed(texts):
            nonlocal call_count
            call_count += len(texts)
            return [[1.0] * 10 for _ in texts]
        
        async def search(embedding, k, filters=None):
            return [{"id": f"chunk{i}", "score": 0.9} for i in range(k)]
        
        cache = BatchEmbeddingCache(max_size=100)
        
        # Pre-populate cache
        cache.put("query1", [1.0] * 10)
        cache.put("query2", [1.0] * 10)
        
        # Create retriever with cached embedding function
        async def cached_embed(texts):
            cached, uncached = cache.get_batch(texts)
            if uncached:
                new_embs = await embed(uncached)
                cache.put_batch(uncached, new_embs)
                return cached + new_embs
            return cached
        
        retriever = BatchRetriever(cached_embed, search)
        
        # Search with mix of cached and uncached
        queries = ["query1", "query2", "query3"]
        results = await retriever.batch_search(queries, k=3)
        
        # Should only embed query3 (2 were cached)
        assert call_count == 1
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_parallel_search_performance(self):
        """Test that parallel search is faster than sequential."""
        import time
        
        async def slow_search(embedding, k, filters=None):
            await asyncio.sleep(0.1)  # Simulate slow search
            return [{"id": f"chunk{i}", "score": 0.9} for i in range(k)]
        
        async def embed(texts):
            return [[1.0] * 10 for _ in texts]
        
        retriever = BatchRetriever(embed, slow_search)
        
        queries = [f"query{i}" for i in range(5)]
        
        start = time.time()
        results = await retriever.batch_search(queries, k=3)
        elapsed = time.time() - start
        
        # Parallel execution should take ~0.1s, sequential would take ~0.5s
        assert elapsed < 0.3  # Allow some overhead
        assert len(results) == 5
