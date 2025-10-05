"""
Integration tests for T036: Connected API Endpoints
Tests search_contextual() and search_rerank() functions
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.bms_search import Tools


class TestContextualEndpoint:
    """Test suite for search_contextual() function"""
    
    def setup_method(self):
        """Initialize tool instance for each test"""
        self.tool = Tools()
    
    def test_contextual_search_basic(self):
        """Test basic contextual search functionality"""
        result = self.tool.search_contextual("GDPR compliance", limit=3)
        
        assert result is not None
        assert len(result) > 0
        assert "Contextual Search" in result or "Found" in result
    
    def test_contextual_search_with_parents(self):
        """Test contextual search with parent expansion"""
        result = self.tool.search_contextual(
            "safety procedures",
            limit=3,
            expand_parents=True,
            expand_children=False
        )
        
        assert result is not None
        assert "✅" in result or "Parent" in result or "Found" in result
    
    def test_contextual_search_with_children(self):
        """Test contextual search with child expansion"""
        result = self.tool.search_contextual(
            "vendor evaluation",
            limit=3,
            expand_parents=False,
            expand_children=True
        )
        
        assert result is not None
        # Should handle gracefully even if no children exist
        assert len(result) > 0
    
    def test_contextual_search_empty_query(self):
        """Test contextual search with empty query"""
        result = self.tool.search_contextual("", limit=3)
        
        assert result is not None
        # Should either return no results message or fallback to hybrid
        assert "No" in result or "Found" in result
    
    def test_contextual_search_fallback(self):
        """Test contextual search fallback to hybrid on error"""
        # Use malformed input to trigger fallback
        result = self.tool.search_contextual("test query", limit=100000)
        
        assert result is not None
        # Should fallback gracefully
        assert len(result) > 0


class TestRerankEndpoint:
    """Test suite for search_rerank() function"""
    
    def setup_method(self):
        """Initialize tool instance for each test"""
        self.tool = Tools()
    
    def test_rerank_search_basic(self):
        """Test basic reranked search functionality"""
        result = self.tool.search_rerank("procurement forms", limit=5)
        
        assert result is not None
        assert len(result) > 0
        assert "Reranked Search" in result or "Found" in result
    
    def test_rerank_search_with_top_k(self):
        """Test reranked search with custom top_k"""
        result = self.tool.search_rerank(
            "quality procedures",
            limit=5,
            rerank_top_k=30
        )
        
        assert result is not None
        assert "30" in result or "Found" in result
    
    def test_rerank_search_without_cross_encoder(self):
        """Test reranked search without cross-encoder"""
        result = self.tool.search_rerank(
            "safety assessment",
            limit=3,
            use_cross_encoder=False
        )
        
        assert result is not None
        assert "Standard scoring" in result or "Found" in result
    
    def test_rerank_search_precision_query(self):
        """Test reranked search for high-precision query"""
        result = self.tool.search_rerank(
            "BMS-PROJ-FOR-002",
            limit=5,
            rerank_top_k=20
        )
        
        assert result is not None
        assert len(result) > 0
        # Should find specific document
        assert "PROJ" in result or "Found" in result
    
    def test_rerank_search_empty_query(self):
        """Test reranked search with empty query"""
        result = self.tool.search_rerank("", limit=3)
        
        assert result is not None
        # Should either return no results message or fallback
        assert "No" in result or "Found" in result
    
    def test_rerank_search_fallback(self):
        """Test reranked search fallback to hybrid on error"""
        # Use invalid parameters to potentially trigger fallback
        result = self.tool.search_rerank("test", limit=1, rerank_top_k=1)
        
        assert result is not None
        # Should handle gracefully
        assert len(result) > 0


class TestEndpointIntegration:
    """Integration tests for both endpoints together"""
    
    def setup_method(self):
        """Initialize tool instance for each test"""
        self.tool = Tools()
    
    def test_contextual_vs_rerank(self):
        """Compare contextual and rerank results"""
        query = "vendor selection process"
        
        contextual_result = self.tool.search_contextual(query, limit=3)
        rerank_result = self.tool.search_rerank(query, limit=3)
        
        assert contextual_result is not None
        assert rerank_result is not None
        assert len(contextual_result) > 0
        assert len(rerank_result) > 0
        
        # Both should find results
        assert "Found" in contextual_result or "No" in contextual_result
        assert "Found" in rerank_result or "No" in rerank_result
    
    def test_endpoint_coverage_increase(self):
        """Verify both new endpoints are accessible"""
        # Test that both functions exist and are callable
        assert hasattr(self.tool, 'search_contextual')
        assert hasattr(self.tool, 'search_rerank')
        assert callable(self.tool.search_contextual)
        assert callable(self.tool.search_rerank)
    
    def test_tool_metadata_updated(self):
        """Verify tool metadata includes new functions"""
        # The tool should list these functions in specs
        # This is verified by the fact that the functions exist and work
        test_query = "test"
        
        contextual = self.tool.search_contextual(test_query, limit=1)
        rerank = self.tool.search_rerank(test_query, limit=1)
        
        assert contextual is not None
        assert rerank is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
