"""
Contextual Retrieval Enhancement
Implements parent-child chunk relationships and hierarchical retrieval
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


@dataclass
class ContextualResult:
    """Enhanced search result with context"""
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    parent_content: Optional[str] = None
    child_contents: Optional[List[str]] = None
    full_doc_context: Optional[str] = None
    context_score: float = 0.0


class ContextualRetriever:
    """
    Contextual retrieval using parent-child chunk relationships
    Leverages hierarchical embeddings for improved context
    """
    
    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str = "nomad_bms_documents",
        parent_weight: float = 0.3,
        child_weight: float = 0.2,
        full_doc_weight: float = 0.1
    ):
        """
        Initialize contextual retriever
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection name
            parent_weight: Weight for parent chunk scores (0.0-1.0)
            child_weight: Weight for child chunk scores (0.0-1.0)
            full_doc_weight: Weight for full document scores (0.0-1.0)
        """
        self.client = qdrant_client
        self.collection_name = collection_name
        self.parent_weight = parent_weight
        self.child_weight = child_weight
        self.full_doc_weight = full_doc_weight
        
        # Validate weights
        total_weight = parent_weight + child_weight + full_doc_weight
        if total_weight > 1.0:
            logger.warning(f"Total context weights ({total_weight}) > 1.0, normalizing...")
            self.parent_weight = parent_weight / total_weight
            self.child_weight = child_weight / total_weight
            self.full_doc_weight = full_doc_weight / total_weight
    
    def search_with_context(
        self,
        query_embedding: List[float],
        limit: int = 10,
        include_context: bool = True,
        expand_parents: bool = True,
        expand_children: bool = False,
        filters: Optional[Filter] = None,
        min_score: Optional[float] = None
    ) -> List[ContextualResult]:
        """
        Search with contextual retrieval
        
        Args:
            query_embedding: Query embedding vector
            limit: Number of results
            include_context: Include parent/child context
            expand_parents: Retrieve parent chunks
            expand_children: Retrieve child chunks
            filters: Qdrant filters
            min_score: Minimum similarity score
            
        Returns:
            List of contextual results with expanded context
        """
        # Initial search using chunk embeddings
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=("chunk_embedding", query_embedding),
            query_filter=filters,
            limit=limit * 2,  # Get more for filtering
            with_payload=True,
            with_vectors=False
        )
        
        # Filter by min_score if provided
        if min_score is not None:
            search_results = [r for r in search_results if r.score >= min_score]
        
        # Limit results
        search_results = search_results[:limit]
        
        if not include_context:
            # Return simple results without context
            return [
                ContextualResult(
                    chunk_id=r.payload.get("chunk_id", str(r.id)),
                    content=r.payload.get("content", ""),
                    score=r.score,
                    metadata=r.payload
                )
                for r in search_results
            ]
        
        # Enhance with contextual information
        contextual_results = []
        for result in search_results:
            payload = result.payload
            
            # Get parent content if requested
            parent_content = None
            if expand_parents and payload.get("parent_chunk_id"):
                parent_content = self._get_parent_content(payload["parent_chunk_id"])
            
            # Get child contents if requested
            child_contents = None
            if expand_children and payload.get("chunk_id"):
                child_contents = self._get_child_contents(payload["chunk_id"])
            
            # Calculate context score using multi-vector retrieval
            context_score = self._calculate_context_score(
                query_embedding=query_embedding,
                chunk_id=str(result.id),
                payload=payload
            )
            
            contextual_results.append(
                ContextualResult(
                    chunk_id=payload.get("chunk_id", str(result.id)),
                    content=payload.get("content", ""),
                    score=result.score,
                    metadata=payload,
                    parent_content=parent_content,
                    child_contents=child_contents,
                    context_score=context_score
                )
            )
        
        # Re-rank by combined score (original + context)
        contextual_results.sort(
            key=lambda x: x.score + (x.context_score * 0.2),
            reverse=True
        )
        
        return contextual_results
    
    def _get_parent_content(self, parent_chunk_id: str) -> Optional[str]:
        """Retrieve parent chunk content"""
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_id",
                            match=MatchValue(value=parent_chunk_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if results[0]:
                return results[0][0].payload.get("content", "")
            return None
        except Exception as e:
            logger.error(f"Error retrieving parent content: {e}")
            return None
    
    def _get_child_contents(self, chunk_id: str) -> List[str]:
        """Retrieve child chunk contents"""
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="parent_chunk_id",
                            match=MatchValue(value=chunk_id)
                        )
                    ]
                ),
                limit=10,  # Max 10 children
                with_payload=True,
                with_vectors=False
            )
            
            return [r.payload.get("content", "") for r in results[0] if r.payload.get("content")]
        except Exception as e:
            logger.error(f"Error retrieving child contents: {e}")
            return []
    
    def _calculate_context_score(
        self,
        query_embedding: List[float],
        chunk_id: str,
        payload: Dict[str, Any]
    ) -> float:
        """
        Calculate context score using multi-vector retrieval
        Combines parent, child, and full_doc embeddings
        """
        try:
            # Get the point with all vectors
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[chunk_id],
                with_payload=False,
                with_vectors=True
            )
            
            if not points:
                return 0.0
            
            point = points[0]
            vectors = point.vector if isinstance(point.vector, dict) else {}
            
            context_score = 0.0
            
            # Parent embedding score
            if "parent_embedding" in vectors and self.parent_weight > 0:
                parent_score = self._cosine_similarity(
                    query_embedding,
                    vectors["parent_embedding"]
                )
                context_score += parent_score * self.parent_weight
            
            # Child embedding score (average if multiple)
            if "child_embedding" in vectors and self.child_weight > 0:
                child_score = self._cosine_similarity(
                    query_embedding,
                    vectors["child_embedding"]
                )
                context_score += child_score * self.child_weight
            
            # Full document embedding score
            if "full_doc_embedding" in vectors and self.full_doc_weight > 0:
                full_doc_score = self._cosine_similarity(
                    query_embedding,
                    vectors["full_doc_embedding"]
                )
                context_score += full_doc_score * self.full_doc_weight
            
            return context_score
            
        except Exception as e:
            logger.error(f"Error calculating context score: {e}")
            return 0.0
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_expanded_context(
        self,
        chunk_id: str,
        window_size: int = 2
    ) -> Dict[str, Any]:
        """
        Get expanded context window around a chunk
        Retrieves surrounding chunks from the same document
        
        Args:
            chunk_id: Target chunk ID
            window_size: Number of chunks before/after to retrieve
            
        Returns:
            Dict with before, current, and after chunks
        """
        try:
            # Get current chunk
            current = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_id",
                            match=MatchValue(value=chunk_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if not current[0]:
                return {"error": "Chunk not found"}
            
            current_chunk = current[0][0]
            payload = current_chunk.payload
            
            document_id = payload.get("document_id")
            chunk_index = payload.get("chunk_index", 0)
            
            if not document_id:
                return {
                    "current": payload.get("content", ""),
                    "before": [],
                    "after": []
                }
            
            # Get surrounding chunks from same document
            all_chunks = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=100,  # Reasonable limit
                with_payload=True,
                with_vectors=False
            )
            
            # Sort by chunk_index
            sorted_chunks = sorted(
                all_chunks[0],
                key=lambda x: x.payload.get("chunk_index", 0)
            )
            
            # Find current position and extract window
            current_pos = next(
                (i for i, c in enumerate(sorted_chunks) 
                 if c.payload.get("chunk_id") == chunk_id),
                None
            )
            
            if current_pos is None:
                return {
                    "current": payload.get("content", ""),
                    "before": [],
                    "after": []
                }
            
            before_chunks = [
                c.payload.get("content", "")
                for c in sorted_chunks[max(0, current_pos - window_size):current_pos]
            ]
            
            after_chunks = [
                c.payload.get("content", "")
                for c in sorted_chunks[current_pos + 1:current_pos + 1 + window_size]
            ]
            
            return {
                "current": payload.get("content", ""),
                "before": before_chunks,
                "after": after_chunks,
                "document_name": payload.get("document_name", ""),
                "chunk_index": chunk_index,
                "total_chunks": len(sorted_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error getting expanded context: {e}")
            return {"error": str(e)}
