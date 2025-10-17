"""Tests for retrieval explainability."""

import pytest
from api.retrieval.explainer import RetrievalExplainer
from api.models.explanation import ScoreBreakdown, MatchedKeyword, MatchedEntity


class TestRetrievalExplainer:
    """Test retrieval explainer."""
    
    @pytest.fixture
    def explainer(self):
        """Create explainer instance."""
        return RetrievalExplainer()
    
    def test_explain_query(self, explainer):
        """Test query explanation."""
        query = "R4600 traction motor specifications"
        
        explanation = explainer.explain_query(query)
        
        assert explanation.original_query == query
        assert explanation.query_type is not None
        assert len(explanation.extracted_entities) > 0
        
        # Should extract R4600 as train_id
        train_ids = [e for e in explanation.extracted_entities if e.entity_type == "train_id"]
        assert len(train_ids) > 0
        assert any("R4600" in e.entity for e in train_ids)
    
    def test_explain_query_with_expansions(self, explainer):
        """Test query explanation with expansions."""
        query = "traction motor"
        expansions = ["electric motor", "motor specifications"]
        
        explanation = explainer.explain_query(
            query,
            query_type="technical",
            expansions=expansions
        )
        
        assert explanation.query_type == "technical"
        assert explanation.query_expansion == expansions
    
    def test_explain_result_basic(self, explainer):
        """Test basic result explanation."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "The traction motor operates at high voltage",
            "semantic_score": 0.80,
            "keyword_score": 0.90
        }
        query = "traction motor voltage"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        assert explanation.chunk_id == "chunk123"
        assert explanation.rank == 1
        assert explanation.score_breakdown.final_score == 0.85
        assert explanation.score_breakdown.semantic_score == 0.80
        assert explanation.score_breakdown.keyword_score == 0.90
    
    def test_explain_result_with_keywords(self, explainer):
        """Test result explanation with keyword matching."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "The traction motor system provides power to the train wheels"
        }
        query = "traction motor power"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        assert len(explanation.matched_keywords) > 0
        
        # Should match "traction", "motor", "power"
        keywords = {kw.keyword for kw in explanation.matched_keywords}
        assert "traction" in keywords
        assert "motor" in keywords
        assert "power" in keywords
    
    def test_explain_result_with_entities(self, explainer):
        """Test result explanation with entity matching."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "R4600 specifications",
            "train_id": "R4600",
            "component_type": "traction"
        }
        query = "R4600 traction system"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        assert len(explanation.matched_entities) > 0
        
        # Should match train_id and component
        entity_types = {e.entity_type for e in explanation.matched_entities}
        assert "train_id" in entity_types
        assert "component" in entity_types
    
    def test_explain_result_with_debug(self, explainer):
        """Test result explanation with debug info."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "Test content",
            "metadata": {"quality": 0.9}
        }
        query = "test"
        
        explanation = explainer.explain_result(result, query, rank=1, debug=True)
        
        assert explanation.debug_info is not None
        assert "raw_result" in explanation.debug_info
        assert "query_tokens" in explanation.debug_info
        assert "chunk_length" in explanation.debug_info
    
    def test_explain_result_without_debug(self, explainer):
        """Test result explanation without debug info."""
        result = {"id": "chunk123", "score": 0.85, "text": "Test"}
        query = "test"
        
        explanation = explainer.explain_result(result, query, rank=1, debug=False)
        
        assert explanation.debug_info is None
    
    def test_similarity_explanation(self, explainer):
        """Test similarity explanation generation."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "traction motor specifications",
            "semantic_score": 0.80,
            "keyword_score": 0.90,
            "metadata_boost": 0.05
        }
        query = "traction motor"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        assert explanation.similarity_explanation is not None
        assert "Semantic similarity" in explanation.similarity_explanation
        assert "Keyword match" in explanation.similarity_explanation
        assert "Metadata boost" in explanation.similarity_explanation
    
    def test_metadata_matches(self, explainer):
        """Test metadata match extraction."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "Test",
            "document_type": "pdf",
            "quality_score": 0.95,
            "train_id": "R4600",
            "safety_critical": True
        }
        query = "test"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        assert "document_type" in explanation.metadata_matches
        assert explanation.metadata_matches["document_type"] == "pdf"
        assert "quality_score" in explanation.metadata_matches
        assert "train_id" in explanation.metadata_matches
        assert "safety_critical" in explanation.metadata_matches
    
    def test_explain_multiple_results(self, explainer):
        """Test explaining multiple results."""
        results = [
            {"id": "chunk1", "score": 0.9, "text": "traction motor"},
            {"id": "chunk2", "score": 0.8, "text": "motor system"},
            {"id": "chunk3", "score": 0.7, "text": "power supply"}
        ]
        query = "traction motor"
        
        explanations = explainer.explain_results(results, query)
        
        assert len(explanations) == 3
        assert explanations[0].rank == 1
        assert explanations[1].rank == 2
        assert explanations[2].rank == 3
        assert explanations[0].chunk_id == "chunk1"
    
    def test_compare_results(self, explainer):
        """Test comparing two results."""
        result1 = {
            "id": "chunk1",
            "score": 0.9,
            "text": "traction motor specifications with detailed parameters",
            "semantic_score": 0.85,
            "keyword_score": 0.95
        }
        result2 = {
            "id": "chunk2",
            "score": 0.7,
            "text": "motor information",
            "semantic_score": 0.65,
            "keyword_score": 0.75
        }
        query = "traction motor specifications"
        
        comparison = explainer.compare_results(result1, result2, query)
        
        assert comparison["higher_ranked"]["chunk_id"] == "chunk1"
        assert comparison["lower_ranked"]["chunk_id"] == "chunk2"
        assert comparison["score_difference"] > 0
        assert len(comparison["higher_ranked"]["advantages"]) > 0
    
    def test_keyword_frequency_tracking(self, explainer):
        """Test keyword frequency tracking."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "The motor system uses a motor controller to control the motor speed"
        }
        query = "motor system"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        # "motor" appears 3 times
        motor_keyword = next((kw for kw in explanation.matched_keywords if kw.keyword == "motor"), None)
        assert motor_keyword is not None
        assert motor_keyword.frequency == 3
        assert len(motor_keyword.positions) == 3
    
    def test_keyword_position_tracking(self, explainer):
        """Test keyword position tracking."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "The traction motor is a critical component"
        }
        query = "traction motor"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        traction_keyword = next((kw for kw in explanation.matched_keywords if kw.keyword == "traction"), None)
        assert traction_keyword is not None
        assert len(traction_keyword.positions) == 1
        assert traction_keyword.positions[0] == 4  # Position of "traction" in text
    
    def test_short_word_filtering(self, explainer):
        """Test that very short words are filtered out."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "The motor is a key component"
        }
        query = "motor is a key"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        # Should not match "is", "a" (too short, < 3 chars)
        keywords = {kw.keyword for kw in explanation.matched_keywords}
        assert "is" not in keywords
        assert "a" not in keywords
        # Should match "motor" and "key" (>= 3 chars)
        assert "motor" in keywords
        assert "key" in keywords
    
    def test_fusion_method_explanation(self, explainer):
        """Test fusion method in explanation."""
        result = {
            "id": "chunk123",
            "score": 0.85,
            "text": "Test content",
            "fusion_strategy": "rrf"
        }
        query = "test"
        
        explanation = explainer.explain_result(result, query, rank=1)
        
        assert explanation.score_breakdown.fusion_method == "rrf"
        assert "Fusion: rrf" in explanation.similarity_explanation
    
    def test_entity_confidence_scores(self, explainer):
        """Test entity confidence scores."""
        query = "R4600 traction system EN50155"
        
        explanation = explainer.explain_query(query)
        
        # Train IDs should have confidence 1.0
        train_entities = [e for e in explanation.extracted_entities if e.entity_type == "train_id"]
        assert all(e.confidence == 1.0 for e in train_entities)
        
        # Components should have confidence 0.9
        component_entities = [e for e in explanation.extracted_entities if e.entity_type == "component"]
        assert all(e.confidence == 0.9 for e in component_entities)
        
        # Standards should have confidence 1.0
        standard_entities = [e for e in explanation.extracted_entities if e.entity_type == "standard"]
        assert all(e.confidence == 1.0 for e in standard_entities)


class TestScoreBreakdown:
    """Test score breakdown model."""
    
    def test_score_breakdown_creation(self):
        """Test creating score breakdown."""
        breakdown = ScoreBreakdown(
            semantic_score=0.8,
            keyword_score=0.9,
            final_score=0.85
        )
        
        assert breakdown.semantic_score == 0.8
        assert breakdown.keyword_score == 0.9
        assert breakdown.final_score == 0.85
    
    def test_score_breakdown_optional_fields(self):
        """Test optional fields in score breakdown."""
        breakdown = ScoreBreakdown(final_score=0.85)
        
        assert breakdown.semantic_score is None
        assert breakdown.keyword_score is None
        assert breakdown.final_score == 0.85


class TestMatchedKeyword:
    """Test matched keyword model."""
    
    def test_matched_keyword_creation(self):
        """Test creating matched keyword."""
        keyword = MatchedKeyword(
            keyword="motor",
            frequency=3,
            positions=[10, 25, 40]
        )
        
        assert keyword.keyword == "motor"
        assert keyword.frequency == 3
        assert len(keyword.positions) == 3


class TestMatchedEntity:
    """Test matched entity model."""
    
    def test_matched_entity_creation(self):
        """Test creating matched entity."""
        entity = MatchedEntity(
            entity="R4600",
            entity_type="train_id",
            confidence=1.0
        )
        
        assert entity.entity == "R4600"
        assert entity.entity_type == "train_id"
        assert entity.confidence == 1.0
