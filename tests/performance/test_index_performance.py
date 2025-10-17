"""Tests for index performance optimization."""

import pytest
from unittest.mock import Mock, MagicMock
from scripts.optimize_qdrant_index import QdrantIndexOptimizer


class TestQdrantIndexOptimizer:
    """Test Qdrant index optimizer."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Qdrant client."""
        client = Mock()
        
        # Mock collection info
        collection_info = Mock()
        collection_info.vectors_count = 1000
        collection_info.points_count = 1000
        collection_info.status = "green"
        collection_info.config = Mock()
        collection_info.config.dict.return_value = {}
        
        client.get_collection.return_value = collection_info
        client.update_collection.return_value = True
        client.search.return_value = []
        
        return client
    
    @pytest.fixture
    def optimizer(self, mock_client, monkeypatch):
        """Create optimizer with mocked client."""
        optimizer = QdrantIndexOptimizer()
        monkeypatch.setattr(optimizer, "client", mock_client)
        return optimizer
    
    def test_optimizer_creation(self):
        """Test creating optimizer."""
        optimizer = QdrantIndexOptimizer(qdrant_url="http://localhost:6333")
        assert optimizer.client is not None
    
    def test_hnsw_configs(self):
        """Test HNSW configuration presets."""
        assert "balanced" in QdrantIndexOptimizer.HNSW_CONFIGS
        assert "high_recall" in QdrantIndexOptimizer.HNSW_CONFIGS
        assert "fast_search" in QdrantIndexOptimizer.HNSW_CONFIGS
        assert "memory_efficient" in QdrantIndexOptimizer.HNSW_CONFIGS
        
        # Check balanced config
        balanced = QdrantIndexOptimizer.HNSW_CONFIGS["balanced"]
        assert balanced["m"] == 16
        assert balanced["ef_construct"] == 100
    
    def test_get_collection_info(self, optimizer, mock_client):
        """Test getting collection info."""
        info = optimizer.get_collection_info("test_collection")
        
        assert info["vectors_count"] == 1000
        assert info["points_count"] == 1000
        assert info["status"] == "green"
        
        mock_client.get_collection.assert_called_once_with("test_collection")
    
    def test_update_hnsw_config_preset(self, optimizer, mock_client):
        """Test updating HNSW config with preset."""
        success = optimizer.update_hnsw_config("test_collection", preset="balanced")
        
        assert success is True
        mock_client.update_collection.assert_called_once()
    
    def test_update_hnsw_config_custom(self, optimizer, mock_client):
        """Test updating HNSW config with custom parameters."""
        custom_config = {"m": 24, "ef_construct": 150}
        
        success = optimizer.update_hnsw_config(
            "test_collection",
            custom_config=custom_config
        )
        
        assert success is True
        mock_client.update_collection.assert_called_once()
    
    def test_update_hnsw_config_invalid_preset(self, optimizer):
        """Test updating with invalid preset."""
        success = optimizer.update_hnsw_config("test_collection", preset="invalid")
        
        assert success is False
    
    def test_enable_quantization(self, optimizer, mock_client):
        """Test enabling quantization."""
        success = optimizer.enable_quantization("test_collection")
        
        assert success is True
        mock_client.update_collection.assert_called_once()
    
    def test_optimize_for_production_small(self, optimizer, mock_client):
        """Test production optimization for small collection."""
        # Mock small collection
        collection_info = Mock()
        collection_info.vectors_count = 5000
        collection_info.points_count = 5000
        collection_info.status = "green"
        collection_info.config = Mock()
        collection_info.config.dict.return_value = {}
        
        mock_client.get_collection.return_value = collection_info
        
        success = optimizer.optimize_for_production("test_collection")
        
        assert success is True
        # Should use balanced preset for small collections
        assert mock_client.update_collection.called
    
    def test_optimize_for_production_large(self, optimizer, mock_client):
        """Test production optimization for large collection."""
        # Mock large collection
        collection_info = Mock()
        collection_info.vectors_count = 150000
        collection_info.points_count = 150000
        collection_info.status = "green"
        collection_info.config = Mock()
        collection_info.config.dict.return_value = {}
        
        mock_client.get_collection.return_value = collection_info
        
        success = optimizer.optimize_for_production(
            "test_collection",
            enable_quantization=True
        )
        
        assert success is True
        # Should enable quantization for large collections
        assert mock_client.update_collection.call_count >= 2
    
    def test_benchmark_search(self, optimizer, mock_client):
        """Test search benchmarking."""
        query_vector = [0.1] * 768
        
        results = optimizer.benchmark_search(
            "test_collection",
            query_vector,
            num_queries=10,
            k=5
        )
        
        assert "avg_latency_ms" in results
        assert "p95_latency_ms" in results
        assert "p99_latency_ms" in results
        assert results["num_queries"] == 10
        
        # Should have called search 10 times
        assert mock_client.search.call_count == 10


class TestHNSWPresets:
    """Test HNSW preset configurations."""
    
    def test_balanced_preset(self):
        """Test balanced preset values."""
        config = QdrantIndexOptimizer.HNSW_CONFIGS["balanced"]
        
        assert config["m"] == 16
        assert config["ef_construct"] == 100
        assert config["full_scan_threshold"] == 10000
    
    def test_high_recall_preset(self):
        """Test high recall preset values."""
        config = QdrantIndexOptimizer.HNSW_CONFIGS["high_recall"]
        
        assert config["m"] == 32
        assert config["ef_construct"] == 200
        assert config["full_scan_threshold"] == 20000
    
    def test_fast_search_preset(self):
        """Test fast search preset values."""
        config = QdrantIndexOptimizer.HNSW_CONFIGS["fast_search"]
        
        assert config["m"] == 8
        assert config["ef_construct"] == 64
        assert config["full_scan_threshold"] == 5000
    
    def test_memory_efficient_preset(self):
        """Test memory efficient preset values."""
        config = QdrantIndexOptimizer.HNSW_CONFIGS["memory_efficient"]
        
        assert config["m"] == 12
        assert config["ef_construct"] == 80
        assert config["full_scan_threshold"] == 8000
