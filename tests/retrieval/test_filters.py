"""Tests for advanced metadata filtering."""

import pytest
from api.models.filter_builder import (
    FilterBuilder, Filter, FilterGroup, FilterOperator, LogicalOperator,
    FacetedSearch, MetadataBooster
)
from api.retrieval.filters import FilterPresets, FilterValidator


class TestFilterBuilder:
    """Test filter builder."""
    
    def test_single_filter(self):
        """Test building a single filter."""
        builder = FilterBuilder().document_type("pdf")
        filter_dict = builder.build()
        
        assert "key" in filter_dict
        assert filter_dict["key"] == "document_type"
    
    def test_quality_above(self):
        """Test quality threshold filter."""
        builder = FilterBuilder().quality_above(0.8)
        filter_dict = builder.build()
        
        assert "key" in filter_dict
        assert filter_dict["key"] == "quality_score"
        assert "range" in filter_dict
        assert filter_dict["range"]["gte"] == 0.8
    
    def test_quality_range(self):
        """Test quality range filter."""
        builder = FilterBuilder().quality_range(0.7, 0.9)
        filter_dict = builder.build()
        
        # Should create AND group with two conditions
        assert "must" in filter_dict
        assert len(filter_dict["must"]) == 2
    
    def test_multiple_filters_and(self):
        """Test multiple filters with AND logic."""
        builder = (
            FilterBuilder()
            .document_type("pdf")
            .quality_above(0.8)
        )
        filter_dict = builder.build()
        
        assert "must" in filter_dict
        assert len(filter_dict["must"]) == 2
    
    def test_document_types_in(self):
        """Test filtering by multiple document types."""
        builder = FilterBuilder().document_types(["pdf", "docx"])
        filter_dict = builder.build()
        
        assert "key" in filter_dict
        assert filter_dict["key"] == "document_type"
        assert "match" in filter_dict
        assert filter_dict["match"]["any"] == ["pdf", "docx"]
    
    def test_custom_field(self):
        """Test custom field filter."""
        builder = FilterBuilder().custom_field(
            "department",
            FilterOperator.EQUALS,
            "engineering"
        )
        filter_dict = builder.build()
        
        assert filter_dict["key"] == "department"
        assert filter_dict["match"]["value"] == "engineering"
    
    def test_train_id_filter(self):
        """Test train ID filter."""
        builder = FilterBuilder().train_id("R4600")
        filter_dict = builder.build()
        
        assert filter_dict["key"] == "train_id"
        assert filter_dict["match"]["value"] == "R4600"
    
    def test_component_type_filter(self):
        """Test component type filter."""
        builder = FilterBuilder().component_type("traction")
        filter_dict = builder.build()
        
        assert filter_dict["key"] == "component_type"
        assert filter_dict["match"]["value"] == "traction"
    
    def test_standard_compliance_filter(self):
        """Test standard compliance filter."""
        builder = FilterBuilder().standard_compliance("EN50155")
        filter_dict = builder.build()
        
        assert filter_dict["key"] == "standards"
    
    def test_chained_filters(self):
        """Test chaining multiple filters."""
        builder = (
            FilterBuilder()
            .document_type("pdf")
            .quality_above(0.8)
            .train_id("R4600")
        )
        filter_dict = builder.build()
        
        assert "must" in filter_dict
        assert len(filter_dict["must"]) == 3
    
    def test_reset(self):
        """Test resetting the builder."""
        builder = FilterBuilder().document_type("pdf").quality_above(0.8)
        builder.reset()
        filter_dict = builder.build()
        
        assert filter_dict == {}
    
    def test_validation_success(self):
        """Test successful validation."""
        builder = FilterBuilder().document_type("pdf")
        assert builder.validate() is True
    
    def test_validation_empty_field(self):
        """Test validation with empty field."""
        builder = FilterBuilder()
        builder._filters.append(Filter("", FilterOperator.EQUALS, "value"))
        
        with pytest.raises(ValueError, match="field cannot be empty"):
            builder.validate()
    
    def test_validation_none_value(self):
        """Test validation with None value."""
        builder = FilterBuilder()
        builder._filters.append(Filter("field", FilterOperator.EQUALS, None))
        
        with pytest.raises(ValueError, match="cannot be None"):
            builder.validate()
    
    def test_empty_builder(self):
        """Test building with no filters."""
        builder = FilterBuilder()
        filter_dict = builder.build()
        
        assert filter_dict == {}


class TestFilter:
    """Test individual filter conditions."""
    
    def test_equals_operator(self):
        """Test EQUALS operator."""
        f = Filter("type", FilterOperator.EQUALS, "pdf")
        cond = f.to_qdrant_condition()
        
        assert cond["key"] == "type"
        assert cond["match"]["value"] == "pdf"
    
    def test_greater_than_operator(self):
        """Test GREATER_THAN operator."""
        f = Filter("score", FilterOperator.GREATER_THAN, 0.8)
        cond = f.to_qdrant_condition()
        
        assert cond["key"] == "score"
        assert cond["range"]["gt"] == 0.8
    
    def test_in_operator(self):
        """Test IN operator."""
        f = Filter("type", FilterOperator.IN, ["pdf", "docx"])
        cond = f.to_qdrant_condition()
        
        assert cond["key"] == "type"
        assert cond["match"]["any"] == ["pdf", "docx"]
    
    def test_contains_operator(self):
        """Test CONTAINS operator."""
        f = Filter("text", FilterOperator.CONTAINS, "motor")
        cond = f.to_qdrant_condition()
        
        assert cond["key"] == "text"
        assert cond["match"]["text"] == "motor"


class TestFilterGroup:
    """Test filter groups."""
    
    def test_and_group(self):
        """Test AND group."""
        filters = [
            Filter("type", FilterOperator.EQUALS, "pdf"),
            Filter("quality", FilterOperator.GREATER_THAN, 0.8)
        ]
        group = FilterGroup(LogicalOperator.AND, filters)
        cond = group.to_qdrant_condition()
        
        assert "must" in cond
        assert len(cond["must"]) == 2
    
    def test_or_group(self):
        """Test OR group."""
        filters = [
            Filter("type", FilterOperator.EQUALS, "pdf"),
            Filter("type", FilterOperator.EQUALS, "docx")
        ]
        group = FilterGroup(LogicalOperator.OR, filters)
        cond = group.to_qdrant_condition()
        
        assert "should" in cond
        assert len(cond["should"]) == 2
    
    def test_not_group(self):
        """Test NOT group."""
        filters = [
            Filter("type", FilterOperator.EQUALS, "txt")
        ]
        group = FilterGroup(LogicalOperator.NOT, filters)
        cond = group.to_qdrant_condition()
        
        assert "must_not" in cond
        assert len(cond["must_not"]) == 1


class TestFacetedSearch:
    """Test faceted search."""
    
    def test_add_facet(self):
        """Test adding facets."""
        faceted = FacetedSearch()
        faceted.add_facet("document_type")
        faceted.add_facet("department", ["engineering", "operations"])
        
        assert "document_type" in faceted.facets
        assert "department" in faceted.facets
        assert faceted.facets["department"] == ["engineering", "operations"]
    
    def test_get_facet_fields(self):
        """Test getting facet fields."""
        faceted = FacetedSearch()
        faceted.add_facet("document_type")
        faceted.add_facet("quality_score")
        
        fields = faceted.get_facet_fields()
        assert "document_type" in fields
        assert "quality_score" in fields
        assert len(fields) == 2
    
    def test_build_aggregation(self):
        """Test building aggregation query."""
        faceted = FacetedSearch()
        faceted.add_facet("document_type")
        
        agg = faceted.build_aggregation()
        assert "facets" in agg
        assert "document_type" in agg["facets"]


class TestMetadataBooster:
    """Test metadata boosting."""
    
    def test_boost_by_quality(self):
        """Test quality-based boosting."""
        booster = MetadataBooster().boost_by_quality(weight=0.2)
        
        assert len(booster.boost_rules) == 1
        assert booster.boost_rules[0]["field"] == "quality_score"
        assert booster.boost_rules[0]["weight"] == 0.2
    
    def test_boost_by_field_match(self):
        """Test field match boosting."""
        booster = MetadataBooster().boost_by_field_match(
            "train_id", "R4600", boost=1.5
        )
        
        assert len(booster.boost_rules) == 1
        assert booster.boost_rules[0]["field"] == "train_id"
        assert booster.boost_rules[0]["value"] == "R4600"
        assert booster.boost_rules[0]["boost"] == 1.5
    
    def test_apply_quality_boost(self):
        """Test applying quality boost to results."""
        booster = MetadataBooster().boost_by_quality(weight=0.2)
        
        results = [
            {"id": "1", "score": 0.8, "quality_score": 0.9},
            {"id": "2", "score": 0.9, "quality_score": 0.7}
        ]
        
        boosted = booster.apply_boosts(results)
        
        assert len(boosted) == 2
        assert all("boosted_score" in r for r in boosted)
        assert all("original_score" in r for r in boosted)
        assert all("boost_factors" in r for r in boosted)
        
        # Higher quality should boost more
        result1 = next(r for r in boosted if r["id"] == "1")
        result2 = next(r for r in boosted if r["id"] == "2")
        assert result1["boosted_score"] > result1["original_score"]
        assert result2["boosted_score"] > result2["original_score"]
    
    def test_apply_field_match_boost(self):
        """Test applying field match boost."""
        booster = MetadataBooster().boost_by_field_match(
            "train_id", "R4600", boost=1.5
        )
        
        results = [
            {"id": "1", "score": 0.8, "train_id": "R4600"},
            {"id": "2", "score": 0.9, "train_id": "Cityjet"}
        ]
        
        boosted = booster.apply_boosts(results)
        
        # R4600 result should be boosted
        result1 = next(r for r in boosted if r["id"] == "1")
        assert result1["boosted_score"] == 0.8 * 1.5
        
        # Cityjet result should not be boosted
        result2 = next(r for r in boosted if r["id"] == "2")
        assert result2["boosted_score"] == 0.9
    
    def test_multiple_boosts(self):
        """Test applying multiple boost rules."""
        booster = (
            MetadataBooster()
            .boost_by_quality(weight=0.2)
            .boost_by_field_match("train_id", "R4600", boost=1.5)
        )
        
        results = [
            {"id": "1", "score": 0.8, "quality_score": 0.9, "train_id": "R4600"}
        ]
        
        boosted = booster.apply_boosts(results)
        
        # Should apply both boosts
        result = boosted[0]
        assert len(result["boost_factors"]) == 2
        assert result["boosted_score"] > result["original_score"]


class TestFilterPresets:
    """Test filter presets."""
    
    def test_high_quality_only(self):
        """Test high quality preset."""
        builder = FilterPresets.high_quality_only(min_quality=0.85)
        filter_dict = builder.build()
        
        assert "key" in filter_dict
        assert filter_dict["key"] == "quality_score"
        assert filter_dict["range"]["gte"] == 0.85
    
    def test_technical_documents(self):
        """Test technical documents preset."""
        builder = FilterPresets.technical_documents()
        filter_dict = builder.build()
        
        assert "key" in filter_dict
        assert filter_dict["key"] == "document_type"
        assert "pdf" in filter_dict["match"]["any"]
        assert "docx" in filter_dict["match"]["any"]
    
    def test_train_specific(self):
        """Test train-specific preset."""
        builder = FilterPresets.train_specific("R4600", min_quality=0.75)
        filter_dict = builder.build()
        
        assert "must" in filter_dict
        assert len(filter_dict["must"]) == 2
    
    def test_component_specific(self):
        """Test component-specific preset."""
        builder = FilterPresets.component_specific("traction", ["pdf", "docx"])
        filter_dict = builder.build()
        
        assert "must" in filter_dict


class TestFilterValidator:
    """Test filter validation."""
    
    def test_validate_quality_range_success(self):
        """Test successful quality range validation."""
        FilterValidator.validate_quality_range(0.7, 0.9)
        # Should not raise
    
    def test_validate_quality_range_invalid_min(self):
        """Test invalid minimum quality."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            FilterValidator.validate_quality_range(-0.1, 0.9)
    
    def test_validate_quality_range_invalid_max(self):
        """Test invalid maximum quality."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            FilterValidator.validate_quality_range(0.7, 1.5)
    
    def test_validate_quality_range_inverted(self):
        """Test inverted quality range."""
        with pytest.raises(ValueError, match="cannot be greater than"):
            FilterValidator.validate_quality_range(0.9, 0.7)
    
    def test_validate_document_type_success(self):
        """Test successful document type validation."""
        FilterValidator.validate_document_type("pdf")
        FilterValidator.validate_document_type("PDF")  # Case insensitive
        # Should not raise
    
    def test_validate_document_type_invalid(self):
        """Test invalid document type."""
        with pytest.raises(ValueError, match="Invalid document type"):
            FilterValidator.validate_document_type("invalid")
    
    def test_validate_boost_weight_success(self):
        """Test successful boost weight validation."""
        FilterValidator.validate_boost_weight(0.5)
        # Should not raise
    
    def test_validate_boost_weight_invalid(self):
        """Test invalid boost weight."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            FilterValidator.validate_boost_weight(1.5)
