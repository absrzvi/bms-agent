"""Batch retrieval optimization for multiple queries."""

import asyncio
from typing import List, Dict, Optional, Callable
import logging
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class BatchRetriever:
    """Optimize retrieval for multiple queries with batching."""
    
    def __init__(
        self,
        embedding_fn: Callable,
        search_fn: Callable,
        max_batch_size: int = 50,
        dedup_threshold: float = 0.95
    ):
        """
        Initialize batch retriever.
        
        Args:
            embedding_fn: Function to generate embeddings (takes list of texts)
            search_fn: Function to search (takes embedding, k, filters)
            max_batch_size: Maximum queries per batch
            dedup_threshold: Similarity threshold for deduplication
        """
        self.embedding_fn = embedding_fn
        self.search_fn = search_fn
        self.max_batch_size = max_batch_size
        self.dedup_threshold = dedup_threshold
    
    async def batch_search(
        self,
        queries: List[str],
        k: int = 10,
        filters: Optional[Dict] = None,
        deduplicate: bool = True
    ) -> List[List[Dict]]:
        """
        Search multiple queries in batch.
        
        Args:
            queries: List of search queries
            k: Number of results per query
            filters: Optional filters to apply
            deduplicate: Whether to deduplicate results across queries
            
        Returns:
            List of result lists (one per query)
        """
        if not queries:
            return []
        
        if len(queries) > self.max_batch_size:
            logger.warning(
                f"Query batch size ({len(queries)}) exceeds maximum "
                f"({self.max_batch_size}). Processing in chunks."
            )
            return await self._batch_search_chunked(queries, k, filters, deduplicate)
        
        # Generate embeddings in batch
        embeddings = await self._batch_embed(queries)
        
        # Execute searches in parallel
        search_tasks = []
        for embedding in embeddings:
            task = self.search_fn(embedding, k, filters)
            search_tasks.append(task)
        
        results = await asyncio.gather(*search_tasks)
        
        # Convert to list if needed
        results = [list(r) if not isinstance(r, list) else r for r in results]
        
        # Deduplicate if requested
        if deduplicate:
            results = self._deduplicate_results(results)
        
        return results
    
    async def _batch_search_chunked(
        self,
        queries: List[str],
        k: int,
        filters: Optional[Dict],
        deduplicate: bool
    ) -> List[List[Dict]]:
        """Process queries in chunks when batch size exceeds maximum."""
        all_results = []
        
        for i in range(0, len(queries), self.max_batch_size):
            chunk = queries[i:i + self.max_batch_size]
            chunk_results = await self.batch_search(chunk, k, filters, deduplicate)
            all_results.extend(chunk_results)
        
        return all_results
    
    async def _batch_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Call embedding function (should support batch)
            if asyncio.iscoroutinefunction(self.embedding_fn):
                embeddings = await self.embedding_fn(texts)
            else:
                embeddings = self.embedding_fn(texts)
            
            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            # Fallback to sequential
            embeddings = []
            for text in texts:
                if asyncio.iscoroutinefunction(self.embedding_fn):
                    emb = await self.embedding_fn([text])
                else:
                    emb = self.embedding_fn([text])
                embeddings.append(emb[0] if isinstance(emb, list) else emb)
            return embeddings
    
    def _deduplicate_results(
        self,
        result_lists: List[List[Dict]]
    ) -> List[List[Dict]]:
        """
        Deduplicate results across queries.
        
        Args:
            result_lists: List of result lists
            
        Returns:
            Deduplicated result lists
        """
        # Track seen chunk IDs globally
        seen_chunks = set()
        deduped_results = []
        
        for results in result_lists:
            deduped_query_results = []
            
            for result in results:
                chunk_id = result.get("id") or result.get("chunk_id")
                
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    deduped_query_results.append(result)
            
            deduped_results.append(deduped_query_results)
        
        return deduped_results
    
    def aggregate_results(
        self,
        result_lists: List[List[Dict]],
        aggregation: str = "union"
    ) -> List[Dict]:
        """
        Aggregate results from multiple queries.
        
        Args:
            result_lists: List of result lists
            aggregation: Aggregation method ("union", "intersection", "ranked_fusion")
            
        Returns:
            Aggregated results
        """
        if aggregation == "union":
            return self._union_results(result_lists)
        elif aggregation == "intersection":
            return self._intersection_results(result_lists)
        elif aggregation == "ranked_fusion":
            return self._ranked_fusion(result_lists)
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
    
    def _union_results(self, result_lists: List[List[Dict]]) -> List[Dict]:
        """Union of all results (deduplicated)."""
        seen = set()
        union = []
        
        for results in result_lists:
            for result in results:
                chunk_id = result.get("id") or result.get("chunk_id")
                if chunk_id not in seen:
                    seen.add(chunk_id)
                    union.append(result)
        
        return union
    
    def _intersection_results(self, result_lists: List[List[Dict]]) -> List[Dict]:
        """Intersection of results (appear in all queries)."""
        if not result_lists:
            return []
        
        # Get chunk IDs from first query
        chunk_sets = []
        for results in result_lists:
            chunk_ids = {r.get("id") or r.get("chunk_id") for r in results}
            chunk_sets.append(chunk_ids)
        
        # Find intersection
        common_ids = set.intersection(*chunk_sets)
        
        # Return results from first query that are in intersection
        intersection = []
        for result in result_lists[0]:
            chunk_id = result.get("id") or result.get("chunk_id")
            if chunk_id in common_ids:
                intersection.append(result)
        
        return intersection
    
    def _ranked_fusion(self, result_lists: List[List[Dict]]) -> List[Dict]:
        """Reciprocal Rank Fusion across queries."""
        chunk_scores = defaultdict(float)
        chunk_data = {}
        
        for results in result_lists:
            for rank, result in enumerate(results, start=1):
                chunk_id = result.get("id") or result.get("chunk_id")
                if not chunk_id:
                    continue
                
                # RRF score
                rrf_score = 1.0 / (60 + rank)
                chunk_scores[chunk_id] += rrf_score
                
                if chunk_id not in chunk_data:
                    chunk_data[chunk_id] = result
        
        # Sort by fused score
        sorted_chunks = sorted(
            chunk_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        fused = []
        for chunk_id, score in sorted_chunks:
            result = chunk_data[chunk_id].copy()
            result["aggregated_score"] = score
            fused.append(result)
        
        return fused


class BatchEmbeddingCache:
    """Cache for batch embeddings to avoid recomputation."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize embedding cache.
        
        Args:
            max_size: Maximum number of cached embeddings
        """
        self.cache: Dict[str, List[float]] = {}
        self.max_size = max_size
        self.access_count: Dict[str, int] = {}
    
    def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        if text in self.cache:
            self.access_count[text] = self.access_count.get(text, 0) + 1
            return self.cache[text]
        return None
    
    def put(self, text: str, embedding: List[float]):
        """Cache an embedding."""
        if len(self.cache) >= self.max_size:
            # Evict least accessed
            min_access = min(self.access_count.values())
            for key, count in list(self.access_count.items()):
                if count == min_access:
                    del self.cache[key]
                    del self.access_count[key]
                    break
        
        self.cache[text] = embedding
        self.access_count[text] = 1
    
    def get_batch(self, texts: List[str]) -> tuple[List[List[float]], List[str]]:
        """
        Get cached embeddings for batch.
        
        Args:
            texts: List of texts
            
        Returns:
            Tuple of (cached_embeddings, uncached_texts)
        """
        cached = []
        uncached = []
        
        for text in texts:
            embedding = self.get(text)
            if embedding is not None:
                cached.append(embedding)
            else:
                uncached.append(text)
        
        return cached, uncached
    
    def put_batch(self, texts: List[str], embeddings: List[List[float]]):
        """Cache multiple embeddings."""
        for text, embedding in zip(texts, embeddings):
            self.put(text, embedding)
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_count.clear()
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_accesses": sum(self.access_count.values()),
            "unique_queries": len(self.access_count)
        }
