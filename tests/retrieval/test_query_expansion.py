"""Tests for query expansion and classification."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from api.retrieval.query_classifier import QueryClassifier, QueryType
from api.retrieval.query_expansion import QueryExpander, MultiQueryRetriever


class TestQueryClassifier:
    """Test query classification."""
    
    def test_classify_technical_query(self):
        """Test classification of technical queries."""
        classifier = QueryClassifier()
        
        query = "What is the voltage rating for R4600 traction motor?"
        assert classifier.classify(query) == QueryType.TECHNICAL
        
        query = "HVAC cooling system specifications"
        assert classifier.classify(query) == QueryType.TECHNICAL
    
    def test_classify_procedural_query(self):
        """Test classification of procedural queries."""
        classifier = QueryClassifier()
        
        query = "How to perform maintenance on braking system?"
        assert classifier.classify(query) == QueryType.PROCEDURAL
        
        query = "Installation procedure for door actuator"
        assert classifier.classify(query) == QueryType.PROCEDURAL
    
    def test_classify_safety_query(self):
        """Test classification of safety queries."""
        classifier = QueryClassifier()
        
        query = "EN50155 safety requirements for railway equipment"
        assert classifier.classify(query) == QueryType.SAFETY
        
        query = "Fire hazard protection in passenger compartment"
        assert classifier.classify(query) == QueryType.SAFETY
    
    def test_classify_general_query(self):
        """Test classification of general queries."""
        classifier = QueryClassifier()
        
        query = "What is the train schedule?"
        assert classifier.classify(query) == QueryType.GENERAL
        
        query = "Railway network overview"
        assert classifier.classify(query) == QueryType.GENERAL
    
    def test_safety_priority(self):
        """Test that safety queries take priority."""
        classifier = QueryClassifier()
        
        # Query with both technical and safety keywords
        query = "Safety requirements for traction motor voltage"
        assert classifier.classify(query) == QueryType.SAFETY
    
    def test_extract_train_ids(self):
        """Test extraction of train IDs."""
        classifier = QueryClassifier()
        
        query = "R4600 traction system specifications"
        entities = classifier.extract_entities(query)
        assert "R4600" in entities["train_ids"]
        
        query = "Cityjet HVAC maintenance procedure"
        entities = classifier.extract_entities(query)
        assert any("cityjet" in tid.lower() for tid in entities["train_ids"])
    
    def test_extract_components(self):
        """Test extraction of component types."""
        classifier = QueryClassifier()
        
        query = "How to repair the traction motor and braking system?"
        entities = classifier.extract_entities(query)
        assert "traction" in entities["components"]
        assert "braking" in entities["components"]
    
    def test_extract_standards(self):
        """Test extraction of standards."""
        classifier = QueryClassifier()
        
        query = "EN50155 and EN45545 compliance requirements"
        entities = classifier.extract_entities(query)
        assert len(entities["standards"]) >= 1
        
        query = "TSI technical specifications"
        entities = classifier.extract_entities(query)
        assert "TSI" in entities["standards"]


class TestQueryExpander:
    """Test query expansion."""
    
    @pytest.fixture
    def expander(self):
        """Create query expander instance."""
        return QueryExpander(
            ollama_url="http://localhost:11434",
            model="qwen2.5:14b",
            max_variations=3
        )
    
    @pytest.mark.asyncio
    async def test_rule_based_expansion(self, expander):
        """Test rule-based query expansion."""
        query = "R4600 traction motor specifications"
        variations = await expander.expand_query(query, use_llm=False)
        
        assert len(variations) >= 1
        assert query in variations  # Original included
        assert len(variations) <= expander.max_variations + 1
    
    @pytest.mark.asyncio
    async def test_expansion_includes_original(self, expander):
        """Test that expansion always includes original query."""
        query = "HVAC cooling system"
        variations = await expander.expand_query(query, use_llm=False)
        
        assert query in variations
        assert variations[0] == query  # Original is first
    
    @pytest.mark.asyncio
    async def test_technical_query_expansion(self, expander):
        """Test expansion of technical queries."""
        query = "voltage rating"
        variations = await expander.expand_query(query, use_llm=False)
        
        # Should add technical context
        assert any("specification" in v.lower() or "technical" in v.lower() 
                   for v in variations[1:])
    
    @pytest.mark.asyncio
    async def test_procedural_query_expansion(self, expander):
        """Test expansion of procedural queries."""
        query = "maintenance procedure for braking system"
        variations = await expander.expand_query(query, use_llm=False)
        
        # Should add procedural context
        assert any("procedure" in v.lower() or "how to" in v.lower() or "maintenance" in v.lower()
                   for v in variations[1:])
    
    @pytest.mark.asyncio
    async def test_safety_query_expansion(self, expander):
        """Test expansion of safety queries."""
        query = "fire safety requirements"
        variations = await expander.expand_query(query, use_llm=False)
        
        # Should add safety context
        assert any("safety" in v.lower() or "standards" in v.lower() or "compliance" in v.lower()
                   for v in variations[1:])
    
    @pytest.mark.asyncio
    async def test_llm_expansion_fallback(self, expander):
        """Test LLM expansion with fallback to rule-based."""
        query = "traction motor"
        
        # Mock failed LLM call
        with patch.object(expander, '_llm_expand', side_effect=Exception("LLM error")):
            variations = await expander.expand_query(query, use_llm=True)
            
            # Should fallback to rule-based
            assert len(variations) >= 1
            assert query in variations
    
    @pytest.mark.asyncio
    async def test_llm_expansion_success(self, expander):
        """Test successful LLM expansion."""
        query = "traction motor specifications"
        
        # Mock successful LLM response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "1. Electric traction motor technical specs\n2. Motor voltage and current ratings\n3. Traction drive system parameters"
        }
        
        with patch.object(expander._client, 'post', return_value=mock_response):
            variations = await expander.expand_query(query, use_llm=True)
            
            assert len(variations) >= 2  # Original + at least 1 variation
            assert query in variations
    
    def test_cached_expansion(self, expander):
        """Test cached expansion for common queries."""
        query = "HVAC system"
        
        # First call
        result1 = expander.get_cached_expansion(query)
        # Second call (should be cached)
        result2 = expander.get_cached_expansion(query)
        
        assert result1 == result2
        assert query in result1
    
    def test_parse_variations(self, expander):
        """Test parsing variations from LLM response."""
        generated_text = """1. Traction motor specifications
2. Electric motor technical parameters
3. Motor voltage and current ratings"""
        
        variations = expander._parse_variations(generated_text)
        
        assert len(variations) == 3
        assert "Traction motor specifications" in variations
        assert "Electric motor technical parameters" in variations
    
    def test_parse_variations_with_bullets(self, expander):
        """Test parsing variations with bullet points."""
        generated_text = """- Traction motor specs
- Motor technical documentation
- Electric drive system parameters"""
        
        variations = expander._parse_variations(generated_text)
        
        assert len(variations) == 3
        assert all(len(v) > 5 for v in variations)  # Minimum length check


class TestMultiQueryRetriever:
    """Test multi-query retrieval with fusion."""
    
    @pytest.fixture
    def expander(self):
        """Create query expander instance."""
        return QueryExpander(max_variations=2)
    
    @pytest.fixture
    def retriever(self, expander):
        """Create multi-query retriever instance."""
        return MultiQueryRetriever(expander)
    
    @pytest.mark.asyncio
    async def test_retrieve_and_fuse(self, retriever):
        """Test multi-query retrieval with fusion."""
        query = "traction motor"
        
        # Mock retrieval function
        async def mock_retrieval(q, k):
            if "traction" in q.lower():
                return [
                    {"id": "chunk1", "score": 0.9, "text": "Traction motor specs"},
                    {"id": "chunk2", "score": 0.8, "text": "Motor voltage"}
                ]
            else:
                return [
                    {"id": "chunk2", "score": 0.85, "text": "Motor voltage"},
                    {"id": "chunk3", "score": 0.75, "text": "Electric drive"}
                ]
        
        results = await retriever.retrieve_and_fuse(
            query,
            mock_retrieval,
            k=5,
            use_llm=False
        )
        
        assert len(results) >= 1
        assert all("rrf_score" in r for r in results)
        assert all("fusion_method" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_rrf_scoring(self, retriever):
        """Test Reciprocal Rank Fusion scoring."""
        result_lists = [
            [
                {"id": "chunk1", "score": 0.9},
                {"id": "chunk2", "score": 0.8},
                {"id": "chunk3", "score": 0.7}
            ],
            [
                {"id": "chunk2", "score": 0.85},
                {"id": "chunk1", "score": 0.75},
                {"id": "chunk4", "score": 0.65}
            ]
        ]
        
        fused = retriever._reciprocal_rank_fusion(result_lists, k=60)
        
        # chunk2 appears at rank 2 and 1, should have highest RRF score
        # chunk1 appears at rank 1 and 2, should have second highest
        assert len(fused) == 4
        assert all("rrf_score" in r for r in fused)
        
        # Verify scores are in descending order
        scores = [r["rrf_score"] for r in fused]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_retrieval_error_handling(self, retriever):
        """Test handling of retrieval errors."""
        query = "test query"
        
        # Mock retrieval function that fails
        async def failing_retrieval(q, k):
            raise Exception("Retrieval error")
        
        # Should not raise, but return empty or partial results
        results = await retriever.retrieve_and_fuse(
            query,
            failing_retrieval,
            k=5,
            use_llm=False
        )
        
        # Should handle gracefully
        assert isinstance(results, list)
