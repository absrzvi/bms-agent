"""Batch search API endpoint."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
import logging

from api.retrieval.batch import BatchRetriever, BatchEmbeddingCache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["batch_search"])


class BatchSearchRequest(BaseModel):
    """Batch search request model."""
    queries: List[str] = Field(..., min_items=1, max_items=50, description="List of search queries")
    k: int = Field(10, ge=1, le=100, description="Number of results per query")
    deduplicate: bool = Field(True, description="Deduplicate results across queries")
    aggregation: Optional[str] = Field(None, description="Aggregation method: union, intersection, ranked_fusion")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")
    
    @validator('queries')
    def validate_queries(cls, v):
        """Validate queries are not empty."""
        if any(not q.strip() for q in v):
            raise ValueError("Queries cannot be empty")
        return v


class BatchSearchResponse(BaseModel):
    """Batch search response model."""
    results: List[List[dict]] = Field(..., description="Results for each query")
    query_count: int = Field(..., description="Number of queries processed")
    total_results: int = Field(..., description="Total number of results returned")
    aggregated_results: Optional[List[dict]] = Field(None, description="Aggregated results if requested")
    cache_stats: Optional[dict] = Field(None, description="Cache statistics")


class BatchSearchEndpoint:
    """Batch search endpoint handler."""
    
    def __init__(
        self,
        embedding_fn,
        search_fn,
        max_batch_size: int = 50
    ):
        """
        Initialize batch search endpoint.
        
        Args:
            embedding_fn: Function to generate embeddings
            search_fn: Function to perform search
            max_batch_size: Maximum batch size
        """
        self.cache = BatchEmbeddingCache(max_size=1000)
        self.retriever = BatchRetriever(
            embedding_fn=self._cached_embedding_fn,
            search_fn=search_fn,
            max_batch_size=max_batch_size
        )
        self.base_embedding_fn = embedding_fn
    
    async def _cached_embedding_fn(self, texts: List[str]) -> List[List[float]]:
        """Embedding function with caching."""
        cached_embeddings, uncached_texts = self.cache.get_batch(texts)
        
        if uncached_texts:
            # Generate embeddings for uncached texts
            new_embeddings = await self.base_embedding_fn(uncached_texts)
            self.cache.put_batch(uncached_texts, new_embeddings)
            
            # Combine cached and new embeddings in correct order
            all_embeddings = []
            cached_idx = 0
            uncached_idx = 0
            
            for text in texts:
                if self.cache.get(text) is not None and cached_idx < len(cached_embeddings):
                    all_embeddings.append(cached_embeddings[cached_idx])
                    cached_idx += 1
                else:
                    all_embeddings.append(new_embeddings[uncached_idx])
                    uncached_idx += 1
            
            return all_embeddings
        else:
            return cached_embeddings
    
    async def batch_search(
        self,
        request: BatchSearchRequest
    ) -> BatchSearchResponse:
        """
        Execute batch search.
        
        Args:
            request: Batch search request
            
        Returns:
            Batch search response
        """
        try:
            # Execute batch search
            results = await self.retriever.batch_search(
                queries=request.queries,
                k=request.k,
                filters=None,  # TODO: Add filter support
                deduplicate=request.deduplicate
            )
            
            # Apply score threshold if specified
            if request.min_score is not None:
                results = [
                    [r for r in query_results if r.get("score", 0) >= request.min_score]
                    for query_results in results
                ]
            
            # Aggregate if requested
            aggregated = None
            if request.aggregation:
                aggregated = self.retriever.aggregate_results(
                    results,
                    aggregation=request.aggregation
                )
            
            # Calculate statistics
            total_results = sum(len(r) for r in results)
            
            return BatchSearchResponse(
                results=results,
                query_count=len(request.queries),
                total_results=total_results,
                aggregated_results=aggregated,
                cache_stats=self.cache.stats()
            )
            
        except Exception as e:
            logger.error(f"Batch search failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Example route registration (to be integrated with main app)
def register_batch_search_routes(
    app,
    embedding_fn,
    search_fn,
    max_batch_size: int = 50
):
    """
    Register batch search routes.
    
    Args:
        app: FastAPI application
        embedding_fn: Embedding function
        search_fn: Search function
        max_batch_size: Maximum batch size
    """
    endpoint = BatchSearchEndpoint(embedding_fn, search_fn, max_batch_size)
    
    @app.post("/api/v1/search/batch", response_model=BatchSearchResponse)
    async def batch_search(request: BatchSearchRequest):
        """
        Search multiple queries in batch.
        
        - **queries**: List of search queries (1-50)
        - **k**: Number of results per query (default: 10)
        - **deduplicate**: Remove duplicate results across queries (default: true)
        - **aggregation**: Optional aggregation method (union, intersection, ranked_fusion)
        - **min_score**: Optional minimum similarity score filter
        
        Returns results for each query, plus optional aggregated results.
        """
        return await endpoint.batch_search(request)
    
    return endpoint
