"""Tests for hybrid search fusion strategies."""

import pytest
from api.retrieval.fusion import HybridFusion, FusionStrategy
from api.retrieval.bm25_optimizer import BM25Optimizer, QueryAdaptiveBM25


class TestHybridFusion:
    """Test hybrid search fusion."""
    
    @pytest.fixture
    def fusion(self):
        """Create fusion instance."""
        return HybridFusion(
            default_strategy=FusionStrategy.RRF,
            semantic_weight=0.7,
            keyword_weight=0.3,
            rrf_k=60
        )
    
    @pytest.fixture
    def sample_semantic_results(self):
        """Sample semantic search results."""
        return [
            {"id": "chunk1", "score": 0.95, "text": "Traction motor specs"},
            {"id": "chunk2", "score": 0.85, "text": "Motor voltage rating"},
            {"id": "chunk3", "score": 0.75, "text": "HVAC cooling system"}
        ]
    
    @pytest.fixture
    def sample_keyword_results(self):
        """Sample keyword search results."""
        return [
            {"id": "chunk2", "score": 0.90, "text": "Motor voltage rating"},
            {"id": "chunk4", "score": 0.80, "text": "Braking system specs"},
            {"id": "chunk1", "score": 0.70, "text": "Traction motor specs"}
        ]
    
    def test_linear_fusion(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test linear weighted fusion."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.LINEAR
        )
        
        assert len(results) == 4  # 4 unique chunks
        assert all("fused_score" in r for r in results)
        assert all("semantic_score" in r for r in results)
        assert all("keyword_score" in r for r in results)
        assert all("fusion_strategy" in r for r in results)
        
        # Verify scores are in descending order
        scores = [r["fused_score"] for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_linear_fusion_weights(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test that linear fusion applies correct weights."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.LINEAR
        )
        
        # chunk2 appears in both: should have highest score
        chunk2 = next(r for r in results if r["id"] == "chunk2")
        expected_score = 0.7 * 0.85 + 0.3 * 0.90  # semantic_weight * sem_score + keyword_weight * key_score
        assert abs(chunk2["fused_score"] - expected_score) < 0.01
    
    def test_rrf_fusion(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test Reciprocal Rank Fusion."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.RRF
        )
        
        assert len(results) == 4
        assert all("rrf_score" in r for r in results)
        assert all("semantic_rank" in r for r in results)
        assert all("keyword_rank" in r for r in results)
        
        # Verify RRF scores are in descending order
        scores = [r["rrf_score"] for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_rrf_ranking(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test RRF ranking logic."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.RRF
        )
        
        # chunk1: semantic rank 1, keyword rank 3
        # chunk2: semantic rank 2, keyword rank 1
        # chunk2 should rank higher due to better keyword rank
        chunk1 = next(r for r in results if r["id"] == "chunk1")
        chunk2 = next(r for r in results if r["id"] == "chunk2")
        
        assert chunk1["semantic_rank"] == 1
        assert chunk1["keyword_rank"] == 3
        assert chunk2["semantic_rank"] == 2
        assert chunk2["keyword_rank"] == 1
    
    def test_adaptive_fusion_technical(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test adaptive fusion for technical queries."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.ADAPTIVE,
            query_type="technical"
        )
        
        assert len(results) > 0
        assert all("fusion_strategy" in r for r in results)
        assert all(r["fusion_strategy"] == "adaptive" for r in results)
        assert all("query_type" in r for r in results)
        
        # Technical queries should favor keyword (60/40)
        chunk = results[0]
        assert chunk["fusion_weights"]["keyword"] == 0.6
        assert chunk["fusion_weights"]["semantic"] == 0.4
    
    def test_adaptive_fusion_general(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test adaptive fusion for general queries."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.ADAPTIVE,
            query_type="general"
        )
        
        # General queries should favor semantic (70/30)
        chunk = results[0]
        assert chunk["fusion_weights"]["semantic"] == 0.7
        assert chunk["fusion_weights"]["keyword"] == 0.3
    
    def test_adaptive_fusion_safety(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test adaptive fusion for safety queries."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.ADAPTIVE,
            query_type="safety"
        )
        
        # Safety queries should favor keyword (65/35)
        chunk = results[0]
        assert chunk["fusion_weights"]["keyword"] == 0.65
        assert chunk["fusion_weights"]["semantic"] == 0.35
    
    def test_adaptive_fusion_procedural(self, fusion, sample_semantic_results, sample_keyword_results):
        """Test adaptive fusion for procedural queries."""
        results = fusion.fuse(
            sample_semantic_results,
            sample_keyword_results,
            strategy=FusionStrategy.ADAPTIVE,
            query_type="procedural"
        )
        
        # Procedural queries should be balanced (50/50)
        chunk = results[0]
        assert chunk["fusion_weights"]["semantic"] == 0.5
        assert chunk["fusion_weights"]["keyword"] == 0.5
    
    def test_weight_normalization(self):
        """Test that weights are normalized if they don't sum to 1.0."""
        fusion = HybridFusion(
            semantic_weight=0.8,
            keyword_weight=0.3  # Sum = 1.1, should be normalized
        )
        
        # Weights should be normalized to sum to 1.0
        assert abs(fusion.semantic_weight + fusion.keyword_weight - 1.0) < 0.01
        assert abs(fusion.semantic_weight - 0.8/1.1) < 0.01
        assert abs(fusion.keyword_weight - 0.3/1.1) < 0.01
    
    def test_empty_results(self, fusion):
        """Test fusion with empty result sets."""
        results = fusion.fuse([], [], strategy=FusionStrategy.LINEAR)
        assert results == []
        
        results = fusion.fuse([], [], strategy=FusionStrategy.RRF)
        assert results == []
    
    def test_single_source_results(self, fusion, sample_semantic_results):
        """Test fusion when only one source has results."""
        results = fusion.fuse(
            sample_semantic_results,
            [],
            strategy=FusionStrategy.LINEAR
        )
        
        assert len(results) == 3
        assert all(r["keyword_score"] == 0.0 for r in results)


class TestBM25Optimizer:
    """Test BM25 parameter optimization."""
    
    @pytest.fixture
    def optimizer(self):
        """Create BM25 optimizer instance."""
        return BM25Optimizer()
    
    def test_default_parameters(self, optimizer):
        """Test default BM25 parameters."""
        params = optimizer.get_parameters()
        
        assert params["k1"] == 1.2
        assert params["b"] == 0.75
    
    def test_pdf_parameters(self, optimizer):
        """Test PDF-specific parameters."""
        params = optimizer.get_parameters("pdf")
        
        assert params["k1"] == 1.5  # Higher for longer documents
        assert params["b"] == 0.8   # More length normalization
    
    def test_xlsx_parameters(self, optimizer):
        """Test Excel-specific parameters."""
        params = optimizer.get_parameters("xlsx")
        
        assert params["k1"] == 0.8  # Lower for structured data
        assert params["b"] == 0.5   # Less length normalization
    
    def test_pptx_parameters(self, optimizer):
        """Test PowerPoint-specific parameters."""
        params = optimizer.get_parameters("pptx")
        
        assert params["k1"] == 1.0  # Lower for shorter content
        assert params["b"] == 0.6   # Less length normalization
    
    def test_unknown_document_type(self, optimizer):
        """Test handling of unknown document types."""
        params = optimizer.get_parameters("unknown")
        
        # Should return defaults
        assert params["k1"] == 1.2
        assert params["b"] == 0.75
    
    def test_case_insensitive(self, optimizer):
        """Test that document type matching is case-insensitive."""
        params_lower = optimizer.get_parameters("pdf")
        params_upper = optimizer.get_parameters("PDF")
        
        assert params_lower == params_upper
    
    def test_get_all_parameters(self, optimizer):
        """Test getting all document type parameters."""
        all_params = optimizer.get_all_parameters()
        
        assert "pdf" in all_params
        assert "docx" in all_params
        assert "xlsx" in all_params
        assert len(all_params) == 6  # 6 document types
    
    def test_tune_parameters(self, optimizer):
        """Test parameter tuning."""
        optimizer.tune_parameters("custom", k1=1.8, b=0.9, description="Custom type")
        
        params = optimizer.get_parameters("custom")
        assert params["k1"] == 1.8
        assert params["b"] == 0.9
    
    def test_tune_parameters_validation(self, optimizer):
        """Test parameter validation during tuning."""
        # Invalid k1
        with pytest.raises(ValueError):
            optimizer.tune_parameters("test", k1=5.0, b=0.5)
        
        # Invalid b
        with pytest.raises(ValueError):
            optimizer.tune_parameters("test", k1=1.2, b=1.5)
    
    def test_explain_parameters(self, optimizer):
        """Test parameter explanation."""
        explanation = optimizer.explain_parameters("pdf")
        
        assert "k1 = 1.5" in explanation
        assert "b = 0.8" in explanation
        assert "PDF technical documents" in explanation


class TestQueryAdaptiveBM25:
    """Test query-adaptive BM25 parameters."""
    
    @pytest.fixture
    def optimizer(self):
        """Create BM25 optimizer instance."""
        return BM25Optimizer()
    
    @pytest.fixture
    def adaptive(self, optimizer):
        """Create query-adaptive BM25 instance."""
        return QueryAdaptiveBM25(optimizer)
    
    def test_short_query_adaptation(self, adaptive):
        """Test adaptation for short queries."""
        query = "R4600 motor"  # 2 words
        params = adaptive.get_adaptive_parameters(query)
        
        # Short queries should increase k1
        base_params = adaptive.optimizer.get_parameters()
        assert params["k1"] > base_params["k1"]
    
    def test_long_query_adaptation(self, adaptive):
        """Test adaptation for long queries."""
        query = "What are the voltage and current specifications for the R4600 traction motor system?"  # 14 words
        params = adaptive.get_adaptive_parameters(query)
        
        # Long queries should decrease k1
        base_params = adaptive.optimizer.get_parameters()
        assert params["k1"] < base_params["k1"]
    
    def test_complex_query_adaptation(self, adaptive):
        """Test adaptation for complex queries with operators."""
        query = '"traction motor" AND voltage'
        params = adaptive.get_adaptive_parameters(query)
        
        # Complex queries should reduce b
        base_params = adaptive.optimizer.get_parameters()
        assert params["b"] < base_params["b"]
    
    def test_document_type_with_adaptation(self, adaptive):
        """Test that document type parameters are used as base."""
        query = "motor specs"
        params_pdf = adaptive.get_adaptive_parameters(query, document_type="pdf")
        params_xlsx = adaptive.get_adaptive_parameters(query, document_type="xlsx")
        
        # Should start from different base parameters
        assert params_pdf["k1"] != params_xlsx["k1"]
    
    def test_normal_query(self, adaptive):
        """Test that normal queries don't get heavily adapted."""
        query = "traction motor voltage specifications"  # 4 words, no operators
        params = adaptive.get_adaptive_parameters(query)
        base_params = adaptive.optimizer.get_parameters()
        
        # Should be close to base parameters
        assert abs(params["k1"] - base_params["k1"]) < 0.3
        assert abs(params["b"] - base_params["b"]) < 0.2
