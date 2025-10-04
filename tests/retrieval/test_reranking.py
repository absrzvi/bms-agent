"""
Tests for cross-encoder reranking functionality
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from api.retrieval.reranker import CrossEncoderReranker, RerankingPipeline, RerankResult


@pytest.fixture
def mock_cross_encoder_model():
    """Mock CrossEncoder model"""
    model = Mock()
    model.predict = Mock(return_value=[0.8, 0.6, 0.4, 0.2])
    return model


@pytest.fixture
def reranker():
    """Create reranker instance without loading model"""
    return CrossEncoderReranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        retrieval_weight=0.7,
        rerank_weight=0.3,
        device="cpu"
    )


def test_reranker_initialization(reranker):
    """Test reranker initialization"""
    assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
    assert reranker.retrieval_weight == 0.7
    assert reranker.rerank_weight == 0.3
    assert reranker.device == "cpu"
    assert not reranker._model_loaded


def test_weight_normalization():
    """Test weight normalization"""
    reranker = CrossEncoderReranker(
        retrieval_weight=0.5,
        rerank_weight=0.8  # Total = 1.3, should normalize
    )
    
    total = reranker.retrieval_weight + reranker.rerank_weight
    assert abs(total - 1.0) < 0.01


def test_sigmoid_function():
    """Test sigmoid normalization"""
    assert abs(CrossEncoderReranker._sigmoid(0) - 0.5) < 0.01
    assert CrossEncoderReranker._sigmoid(10) > 0.99
    assert CrossEncoderReranker._sigmoid(-10) < 0.01


def test_rerank_without_model(reranker, mock_cross_encoder_model):
    """Test reranking with mocked model"""
    # Mock the model loading
    reranker._model = mock_cross_encoder_model
    reranker._model_loaded = True
    
    # Sample results
    results = [
        {"chunk_id": "1", "content": "Content 1", "score": 0.9, "metadata": {}},
        {"chunk_id": "2", "content": "Content 2", "score": 0.8, "metadata": {}},
        {"chunk_id": "3", "content": "Content 3", "score": 0.7, "metadata": {}},
        {"chunk_id": "4", "content": "Content 4", "score": 0.6, "metadata": {}}
    ]
    
    reranked = reranker.rerank("test query", results, top_k=4)
    
    assert len(reranked) == 4
    assert all(isinstance(r, RerankResult) for r in reranked)
    
    # Results should be sorted by combined score
    for i in range(len(reranked) - 1):
        assert reranked[i].combined_score >= reranked[i + 1].combined_score
    
    # Check ranks are assigned correctly
    for i, result in enumerate(reranked):
        assert result.rank == i


def test_rerank_with_top_k_limit(reranker, mock_cross_encoder_model):
    """Test reranking with top_k limit"""
    reranker._model = mock_cross_encoder_model
    reranker._model_loaded = True
    
    results = [
        {"chunk_id": str(i), "content": f"Content {i}", "score": 0.9 - i*0.1, "metadata": {}}
        for i in range(10)
    ]
    
    # Only rerank top 3
    reranked = reranker.rerank("test query", results, top_k=3)
    
    # Model should only be called with 3 pairs
    assert mock_cross_encoder_model.predict.call_count == 1
    call_args = mock_cross_encoder_model.predict.call_args[0][0]
    assert len(call_args) <= 3


def test_rerank_with_min_score_filter(reranker, mock_cross_encoder_model):
    """Test reranking with minimum score filter"""
    reranker._model = mock_cross_encoder_model
    reranker._model_loaded = True
    
    # Mock predict to return specific scores
    mock_cross_encoder_model.predict.return_value = [0.9, 0.5, 0.3, 0.1]
    
    results = [
        {"chunk_id": str(i), "content": f"Content {i}", "score": 0.8, "metadata": {}}
        for i in range(4)
    ]
    
    # Filter with min_rerank_score=0.6 (after sigmoid normalization)
    reranked = reranker.rerank("test query", results, min_rerank_score=0.6)
    
    # Should filter out results with low rerank scores
    assert all(r.rerank_score >= 0.6 for r in reranked)


def test_rerank_result_dataclass():
    """Test RerankResult dataclass"""
    result = RerankResult(
        chunk_id="test-1",
        content="Test content",
        retrieval_score=0.8,
        rerank_score=0.9,
        combined_score=0.83,
        metadata={"doc": "test.pdf"},
        rank=0,
        original_rank=5
    )
    
    assert result.chunk_id == "test-1"
    assert result.retrieval_score == 0.8
    assert result.rerank_score == 0.9
    assert result.combined_score == 0.83
    assert result.rank == 0
    assert result.original_rank == 5


def test_reranking_pipeline():
    """Test reranking pipeline with caching"""
    reranker = CrossEncoderReranker()
    pipeline = RerankingPipeline(reranker, enable_cache=True, cache_size=10)
    
    assert pipeline.enable_cache
    assert pipeline.cache_size == 10
    assert len(pipeline._cache) == 0


def test_pipeline_cache_operations():
    """Test pipeline cache operations"""
    reranker = Mock()
    reranker.rerank = Mock(return_value=[])
    
    pipeline = RerankingPipeline(reranker, enable_cache=True, cache_size=2)
    
    # Add items to cache
    pipeline._update_cache("key1", [])
    pipeline._update_cache("key2", [])
    
    assert len(pipeline._cache) == 2
    assert "key1" in pipeline._cache
    assert "key2" in pipeline._cache
    
    # Add third item, should evict oldest
    pipeline._update_cache("key3", [])
    
    assert len(pipeline._cache) == 2
    assert "key1" not in pipeline._cache  # Evicted
    assert "key2" in pipeline._cache
    assert "key3" in pipeline._cache


def test_pipeline_clear_cache():
    """Test cache clearing"""
    reranker = Mock()
    pipeline = RerankingPipeline(reranker, enable_cache=True)
    
    pipeline._cache = {"key1": [], "key2": []}
    pipeline._cache_order = ["key1", "key2"]
    
    pipeline.clear_cache()
    
    assert len(pipeline._cache) == 0
    assert len(pipeline._cache_order) == 0


def test_pipeline_cache_stats():
    """Test cache statistics"""
    reranker = Mock()
    pipeline = RerankingPipeline(reranker, enable_cache=True, cache_size=100)
    
    pipeline._cache = {"key1": [], "key2": []}
    
    stats = pipeline.get_cache_stats()
    
    assert stats["cache_size"] == 2
    assert stats["max_cache_size"] == 100
    assert stats["cache_enabled"] is True


def test_get_model_info(reranker):
    """Test getting model information"""
    info = reranker.get_model_info()
    
    assert info["model_name"] == "cross-encoder/ms-marco-MiniLM-L-6-v2"
    assert info["retrieval_weight"] == 0.7
    assert info["rerank_weight"] == 0.3
    assert info["device"] == "cpu"
    assert info["model_loaded"] is False


def test_rerank_with_empty_results(reranker):
    """Test reranking with empty results"""
    reranked = reranker.rerank("test query", [], top_k=10)
    assert len(reranked) == 0


def test_rerank_with_long_content(reranker, mock_cross_encoder_model):
    """Test reranking with content exceeding token limit"""
    reranker._model = mock_cross_encoder_model
    reranker._model_loaded = True
    
    # Create result with very long content
    long_content = "A" * 5000  # Exceeds 2000 char limit
    results = [
        {"chunk_id": "1", "content": long_content, "score": 0.9, "metadata": {}}
    ]
    
    reranked = reranker.rerank("test query", results)
    
    # Should truncate content
    call_args = mock_cross_encoder_model.predict.call_args[0][0]
    assert len(call_args[0][1]) <= 2003  # 2000 + "..."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
