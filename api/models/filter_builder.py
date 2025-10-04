"""Filter builder for advanced metadata filtering."""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field


class FilterOperator(str, Enum):
    """Filter operators."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class LogicalOperator(str, Enum):
    """Logical operators for combining filters."""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class Filter:
    """Individual filter condition."""
    field: str
    operator: FilterOperator
    value: Any
    
    def to_qdrant_condition(self) -> Dict:
        """Convert to Qdrant filter condition."""
        if self.operator == FilterOperator.EQUALS:
            return {"key": self.field, "match": {"value": self.value}}
        elif self.operator == FilterOperator.NOT_EQUALS:
            return {"key": self.field, "match": {"value": self.value, "must_not": True}}
        elif self.operator == FilterOperator.GREATER_THAN:
            return {"key": self.field, "range": {"gt": self.value}}
        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return {"key": self.field, "range": {"gte": self.value}}
        elif self.operator == FilterOperator.LESS_THAN:
            return {"key": self.field, "range": {"lt": self.value}}
        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return {"key": self.field, "range": {"lte": self.value}}
        elif self.operator == FilterOperator.IN:
            return {"key": self.field, "match": {"any": self.value}}
        elif self.operator == FilterOperator.NOT_IN:
            return {"key": self.field, "match": {"any": self.value, "must_not": True}}
        elif self.operator == FilterOperator.CONTAINS:
            return {"key": self.field, "match": {"text": self.value}}
        elif self.operator == FilterOperator.STARTS_WITH:
            return {"key": self.field, "match": {"text": f"{self.value}*"}}
        elif self.operator == FilterOperator.ENDS_WITH:
            return {"key": self.field, "match": {"text": f"*{self.value}"}}
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


@dataclass
class FilterGroup:
    """Group of filters combined with logical operators."""
    operator: LogicalOperator
    filters: List[Union[Filter, 'FilterGroup']] = field(default_factory=list)
    
    def to_qdrant_condition(self) -> Dict:
        """Convert to Qdrant filter condition."""
        conditions = [
            f.to_qdrant_condition() for f in self.filters
        ]
        
        if self.operator == LogicalOperator.AND:
            return {"must": conditions}
        elif self.operator == LogicalOperator.OR:
            return {"should": conditions}
        elif self.operator == LogicalOperator.NOT:
            return {"must_not": conditions}
        else:
            raise ValueError(f"Unsupported logical operator: {self.operator}")


class FilterBuilder:
    """Fluent API for building complex metadata filters."""
    
    def __init__(self):
        """Initialize filter builder."""
        self._filters: List[Union[Filter, FilterGroup]] = []
        self._current_operator: LogicalOperator = LogicalOperator.AND
    
    def document_type(self, doc_type: str) -> 'FilterBuilder':
        """Filter by document type."""
        self._filters.append(
            Filter("document_type", FilterOperator.EQUALS, doc_type)
        )
        return self
    
    def document_types(self, doc_types: List[str]) -> 'FilterBuilder':
        """Filter by multiple document types."""
        self._filters.append(
            Filter("document_type", FilterOperator.IN, doc_types)
        )
        return self
    
    def quality_above(self, threshold: float) -> 'FilterBuilder':
        """Filter by minimum quality score."""
        self._filters.append(
            Filter("quality_score", FilterOperator.GREATER_THAN_OR_EQUAL, threshold)
        )
        return self
    
    def quality_below(self, threshold: float) -> 'FilterBuilder':
        """Filter by maximum quality score."""
        self._filters.append(
            Filter("quality_score", FilterOperator.LESS_THAN_OR_EQUAL, threshold)
        )
        return self
    
    def quality_range(self, min_score: float, max_score: float) -> 'FilterBuilder':
        """Filter by quality score range."""
        self._filters.append(
            Filter("quality_score", FilterOperator.GREATER_THAN_OR_EQUAL, min_score)
        )
        self._filters.append(
            Filter("quality_score", FilterOperator.LESS_THAN_OR_EQUAL, max_score)
        )
        return self
    
    def department(self, dept: str) -> 'FilterBuilder':
        """Filter by department."""
        self._filters.append(
            Filter("department", FilterOperator.EQUALS, dept)
        )
        return self
    
    def train_id(self, train_id: str) -> 'FilterBuilder':
        """Filter by train ID."""
        self._filters.append(
            Filter("train_id", FilterOperator.EQUALS, train_id)
        )
        return self
    
    def component_type(self, component: str) -> 'FilterBuilder':
        """Filter by component type."""
        self._filters.append(
            Filter("component_type", FilterOperator.EQUALS, component)
        )
        return self
    
    def standard_compliance(self, standard: str) -> 'FilterBuilder':
        """Filter by standard compliance."""
        self._filters.append(
            Filter("standards", FilterOperator.CONTAINS, standard)
        )
        return self
    
    def custom_field(
        self,
        field: str,
        operator: FilterOperator,
        value: Any
    ) -> 'FilterBuilder':
        """Add custom field filter."""
        self._filters.append(Filter(field, operator, value))
        return self
    
    def and_group(self) -> 'FilterBuilder':
        """Start an AND group."""
        self._current_operator = LogicalOperator.AND
        return self
    
    def or_group(self) -> 'FilterBuilder':
        """Start an OR group."""
        self._current_operator = LogicalOperator.OR
        return self
    
    def not_group(self) -> 'FilterBuilder':
        """Start a NOT group."""
        self._current_operator = LogicalOperator.NOT
        return self
    
    def build(self) -> Dict:
        """
        Build the final filter condition for Qdrant.
        
        Returns:
            Qdrant filter condition dictionary
        """
        if not self._filters:
            return {}
        
        if len(self._filters) == 1:
            # Single filter
            return self._filters[0].to_qdrant_condition()
        
        # Multiple filters - combine with current operator
        group = FilterGroup(self._current_operator, self._filters)
        return group.to_qdrant_condition()
    
    def reset(self) -> 'FilterBuilder':
        """Reset the builder."""
        self._filters = []
        self._current_operator = LogicalOperator.AND
        return self
    
    def validate(self) -> bool:
        """
        Validate the filter configuration.
        
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not self._filters:
            return True
        
        # Validate each filter
        for f in self._filters:
            if isinstance(f, Filter):
                if not f.field:
                    raise ValueError("Filter field cannot be empty")
                if f.value is None:
                    raise ValueError(f"Filter value for field '{f.field}' cannot be None")
        
        return True


class FacetedSearch:
    """Faceted search for metadata aggregation."""
    
    def __init__(self):
        """Initialize faceted search."""
        self.facets: Dict[str, List[str]] = {}
    
    def add_facet(self, field: str, values: Optional[List[str]] = None):
        """
        Add a facet field for aggregation.
        
        Args:
            field: Field name to facet on
            values: Optional list of specific values to include
        """
        self.facets[field] = values or []
    
    def get_facet_fields(self) -> List[str]:
        """Get list of facet fields."""
        return list(self.facets.keys())
    
    def build_aggregation(self) -> Dict:
        """
        Build aggregation query for facets.
        
        Returns:
            Aggregation configuration
        """
        return {
            "facets": {
                field: {"values": values} if values else {}
                for field, values in self.facets.items()
            }
        }


class MetadataBooster:
    """Boost search results based on metadata."""
    
    def __init__(self):
        """Initialize metadata booster."""
        self.boost_rules: List[Dict] = []
    
    def boost_by_quality(self, weight: float = 0.2) -> 'MetadataBooster':
        """
        Boost results by quality score.
        
        Args:
            weight: Boost weight (0.0-1.0)
        """
        self.boost_rules.append({
            "field": "quality_score",
            "type": "multiplicative",
            "weight": weight
        })
        return self
    
    def boost_by_recency(self, weight: float = 0.1) -> 'MetadataBooster':
        """
        Boost recent documents.
        
        Args:
            weight: Boost weight (0.0-1.0)
        """
        self.boost_rules.append({
            "field": "processed_at",
            "type": "temporal_decay",
            "weight": weight
        })
        return self
    
    def boost_by_field_match(
        self,
        field: str,
        value: Any,
        boost: float = 1.5
    ) -> 'MetadataBooster':
        """
        Boost results matching a specific field value.
        
        Args:
            field: Field name
            value: Value to match
            boost: Boost multiplier
        """
        self.boost_rules.append({
            "field": field,
            "value": value,
            "type": "field_match",
            "boost": boost
        })
        return self
    
    def apply_boosts(self, results: List[Dict]) -> List[Dict]:
        """
        Apply boost rules to search results.
        
        Args:
            results: Search results
            
        Returns:
            Boosted results
        """
        boosted_results = []
        
        for result in results:
            boosted_score = result.get("score", 0.0)
            boost_factors = []
            
            for rule in self.boost_rules:
                if rule["type"] == "multiplicative":
                    field_value = result.get(rule["field"], 0.0)
                    boost_factor = 1.0 + (field_value * rule["weight"])
                    boosted_score *= boost_factor
                    boost_factors.append({
                        "rule": f"{rule['field']}_multiplicative",
                        "factor": boost_factor
                    })
                
                elif rule["type"] == "field_match":
                    field_value = result.get(rule["field"])
                    if field_value == rule["value"]:
                        boosted_score *= rule["boost"]
                        boost_factors.append({
                            "rule": f"{rule['field']}_match",
                            "factor": rule["boost"]
                        })
            
            boosted_result = result.copy()
            boosted_result["original_score"] = result.get("score", 0.0)
            boosted_result["boosted_score"] = boosted_score
            boosted_result["boost_factors"] = boost_factors
            boosted_results.append(boosted_result)
        
        # Re-sort by boosted score
        boosted_results.sort(key=lambda x: x["boosted_score"], reverse=True)
        return boosted_results
