"""Advanced metadata filtering for retrieval."""

from typing import List, Dict, Optional, Any
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Filter as QdrantFilter, FieldCondition, MatchValue, Range

from api.models.filter_builder import FilterBuilder, FacetedSearch, MetadataBooster

logger = logging.getLogger(__name__)


class AdvancedMetadataFilter:
    """Advanced metadata filtering for Qdrant retrieval."""
    
    def __init__(self, qdrant_client: QdrantClient, collection_name: str):
        """
        Initialize advanced metadata filter.
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection name
        """
        self.client = qdrant_client
        self.collection_name = collection_name
    
    def search_with_filter(
        self,
        query_vector: List[float],
        filter_builder: FilterBuilder,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search with advanced metadata filters.
        
        Args:
            query_vector: Query embedding vector
            filter_builder: FilterBuilder instance with configured filters
            limit: Maximum number of results
            score_threshold: Minimum score threshold
            
        Returns:
            Filtered search results
        """
        # Validate and build filter
        filter_builder.validate()
        filter_dict = filter_builder.build()
        
        # Convert to Qdrant filter format
        qdrant_filter = self._build_qdrant_filter(filter_dict)
        
        # Execute search
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convert to dict format
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Search with filter failed: {e}")
            raise
    
    def _build_qdrant_filter(self, filter_dict: Dict) -> Optional[QdrantFilter]:
        """
        Build Qdrant filter from filter dictionary.
        
        Args:
            filter_dict: Filter dictionary from FilterBuilder
            
        Returns:
            QdrantFilter instance or None
        """
        if not filter_dict:
            return None
        
        # Handle different filter structures
        if "must" in filter_dict:
            conditions = [
                self._build_condition(cond) for cond in filter_dict["must"]
            ]
            return QdrantFilter(must=conditions)
        elif "should" in filter_dict:
            conditions = [
                self._build_condition(cond) for cond in filter_dict["should"]
            ]
            return QdrantFilter(should=conditions)
        elif "must_not" in filter_dict:
            conditions = [
                self._build_condition(cond) for cond in filter_dict["must_not"]
            ]
            return QdrantFilter(must_not=conditions)
        else:
            # Single condition
            condition = self._build_condition(filter_dict)
            return QdrantFilter(must=[condition])
    
    def _build_condition(self, cond_dict: Dict) -> FieldCondition:
        """
        Build Qdrant field condition from condition dictionary.
        
        Args:
            cond_dict: Condition dictionary
            
        Returns:
            FieldCondition instance
        """
        key = cond_dict.get("key")
        
        if "match" in cond_dict:
            match_dict = cond_dict["match"]
            if "value" in match_dict:
                return FieldCondition(
                    key=key,
                    match=MatchValue(value=match_dict["value"])
                )
            elif "any" in match_dict:
                return FieldCondition(
                    key=key,
                    match=MatchValue(any=match_dict["any"])
                )
        
        elif "range" in cond_dict:
            range_dict = cond_dict["range"]
            return FieldCondition(
                key=key,
                range=Range(**range_dict)
            )
        
        raise ValueError(f"Unsupported condition format: {cond_dict}")
    
    def get_facets(
        self,
        faceted_search: FacetedSearch,
        query_vector: Optional[List[float]] = None,
        filter_builder: Optional[FilterBuilder] = None
    ) -> Dict[str, Dict[str, int]]:
        """
        Get facet counts for metadata fields.
        
        Args:
            faceted_search: FacetedSearch instance
            query_vector: Optional query vector for filtered facets
            filter_builder: Optional filter to apply before faceting
            
        Returns:
            Dictionary mapping facet fields to value counts
        """
        # Build base filter
        base_filter = None
        if filter_builder:
            filter_builder.validate()
            filter_dict = filter_builder.build()
            base_filter = self._build_qdrant_filter(filter_dict)
        
        # Get all documents (or filtered subset)
        if query_vector:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=base_filter,
                limit=1000  # Large limit for faceting
            )
        else:
            # Scroll through collection
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=base_filter,
                limit=1000
            )[0]
        
        # Count facet values
        facet_counts = {}
        for field in faceted_search.get_facet_fields():
            facet_counts[field] = {}
            
            for result in results:
                payload = result.payload if hasattr(result, 'payload') else result
                value = payload.get(field)
                
                if value is not None:
                    value_str = str(value)
                    facet_counts[field][value_str] = facet_counts[field].get(value_str, 0) + 1
        
        return facet_counts
    
    def search_with_boost(
        self,
        query_vector: List[float],
        metadata_booster: MetadataBooster,
        filter_builder: Optional[FilterBuilder] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search with metadata-based boosting.
        
        Args:
            query_vector: Query embedding vector
            metadata_booster: MetadataBooster instance with boost rules
            filter_builder: Optional filter builder
            limit: Maximum number of results (before boosting)
            score_threshold: Minimum score threshold
            
        Returns:
            Boosted and re-ranked results
        """
        # Get initial results (retrieve more for boosting)
        initial_limit = limit * 3  # Retrieve 3x for better boosting
        
        if filter_builder:
            results = self.search_with_filter(
                query_vector,
                filter_builder,
                limit=initial_limit,
                score_threshold=score_threshold
            )
        else:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=initial_limit,
                score_threshold=score_threshold
            )
            results = [
                {
                    "id": r.id,
                    "score": r.score,
                    **r.payload
                }
                for r in results
            ]
        
        # Apply boosts
        boosted_results = metadata_booster.apply_boosts(results)
        
        # Return top results after boosting
        return boosted_results[:limit]


class FilterPresets:
    """Common filter presets for railway documentation."""
    
    @staticmethod
    def high_quality_only(min_quality: float = 0.8) -> FilterBuilder:
        """Filter for high-quality documents only."""
        return FilterBuilder().quality_above(min_quality)
    
    @staticmethod
    def technical_documents() -> FilterBuilder:
        """Filter for technical documentation."""
        return FilterBuilder().document_types(["pdf", "docx"])
    
    @staticmethod
    def safety_critical() -> FilterBuilder:
        """Filter for safety-critical documents."""
        return (
            FilterBuilder()
            .standard_compliance("EN50155")
            .or_group()
            .standard_compliance("EN45545")
            .or_group()
            .standard_compliance("TSI")
        )
    
    @staticmethod
    def train_specific(train_id: str, min_quality: float = 0.7) -> FilterBuilder:
        """Filter for specific train documentation."""
        return (
            FilterBuilder()
            .train_id(train_id)
            .quality_above(min_quality)
        )
    
    @staticmethod
    def component_specific(
        component: str,
        doc_types: Optional[List[str]] = None
    ) -> FilterBuilder:
        """Filter for specific component documentation."""
        builder = FilterBuilder().component_type(component)
        
        if doc_types:
            builder.document_types(doc_types)
        
        return builder
    
    @staticmethod
    def recent_and_quality(
        min_quality: float = 0.75
    ) -> FilterBuilder:
        """Filter for recent, high-quality documents."""
        # Note: Requires processed_at field in metadata
        return FilterBuilder().quality_above(min_quality)


class FilterValidator:
    """Validate filter configurations."""
    
    @staticmethod
    def validate_quality_range(min_score: float, max_score: float):
        """Validate quality score range."""
        if min_score < 0.0 or min_score > 1.0:
            raise ValueError(f"min_score must be between 0.0 and 1.0, got {min_score}")
        
        if max_score < 0.0 or max_score > 1.0:
            raise ValueError(f"max_score must be between 0.0 and 1.0, got {max_score}")
        
        if min_score > max_score:
            raise ValueError(f"min_score ({min_score}) cannot be greater than max_score ({max_score})")
    
    @staticmethod
    def validate_document_type(doc_type: str):
        """Validate document type."""
        valid_types = ["pdf", "docx", "pptx", "xlsx", "csv", "txt"]
        if doc_type.lower() not in valid_types:
            raise ValueError(f"Invalid document type '{doc_type}'. Valid types: {valid_types}")
    
    @staticmethod
    def validate_boost_weight(weight: float):
        """Validate boost weight."""
        if weight < 0.0 or weight > 1.0:
            raise ValueError(f"Boost weight must be between 0.0 and 1.0, got {weight}")
