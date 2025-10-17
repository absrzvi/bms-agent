"""Tests for multi-document synthesis."""

import pytest
from api.synthesis.multi_doc import (
    MultiDocumentSynthesizer, DocumentCluster
)


class TestDocumentCluster:
    """Test document cluster."""
    
    def test_cluster_creation(self):
        """Test creating a document cluster."""
        cluster = DocumentCluster("test_cluster")
        
        assert cluster.cluster_id == "test_cluster"
        assert len(cluster.chunks) == 0
        assert len(cluster.document_ids) == 0
        assert cluster.combined_score == 0.0
    
    def test_add_chunk(self):
        """Test adding chunks to cluster."""
        cluster = DocumentCluster("test_cluster")
        
        chunk = {
            "id": "chunk1",
            "document_id": "doc1",
            "score": 0.9,
            "component_type": "traction"
        }
        
        cluster.add_chunk(chunk)
        
        assert len(cluster.chunks) == 1
        assert "doc1" in cluster.document_ids
        assert "traction" in cluster.topics
        assert cluster.combined_score == 0.9
    
    def test_multiple_chunks(self):
        """Test adding multiple chunks."""
        cluster = DocumentCluster("test_cluster")
        
        chunks = [
            {"id": "c1", "document_id": "doc1", "score": 0.9, "component_type": "traction"},
            {"id": "c2", "document_id": "doc1", "score": 0.8, "component_type": "braking"},
            {"id": "c3", "document_id": "doc2", "score": 0.7, "component_type": "traction"}
        ]
        
        for chunk in chunks:
            cluster.add_chunk(chunk)
        
        assert len(cluster.chunks) == 3
        assert len(cluster.document_ids) == 2
        assert len(cluster.topics) == 2
        assert abs(cluster.combined_score - 2.4) < 0.01
    
    def test_get_summary(self):
        """Test getting cluster summary."""
        cluster = DocumentCluster("test_cluster")
        
        chunk = {"id": "c1", "document_id": "doc1", "score": 0.9}
        cluster.add_chunk(chunk)
        
        summary = cluster.get_summary()
        
        assert summary["cluster_id"] == "test_cluster"
        assert summary["num_chunks"] == 1
        assert summary["num_documents"] == 1
        assert summary["combined_score"] == 0.9
        assert summary["avg_score"] == 0.9


class TestMultiDocumentSynthesizer:
    """Test multi-document synthesizer."""
    
    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer instance."""
        return MultiDocumentSynthesizer()
    
    @pytest.fixture
    def sample_results(self):
        """Sample search results from multiple documents."""
        return [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "score": 0.9,
                "text": "Traction motor specifications",
                "component_type": "traction"
            },
            {
                "id": "chunk2",
                "document_id": "doc1",
                "score": 0.8,
                "text": "Motor voltage requirements",
                "component_type": "traction"
            },
            {
                "id": "chunk3",
                "document_id": "doc2",
                "score": 0.85,
                "text": "Braking system specifications",
                "component_type": "braking"
            },
            {
                "id": "chunk4",
                "document_id": "doc2",
                "score": 0.75,
                "text": "Emergency braking procedures",
                "component_type": "braking"
            },
            {
                "id": "chunk5",
                "document_id": "doc3",
                "score": 0.7,
                "text": "HVAC cooling system",
                "component_type": "hvac"
            }
        ]
    
    def test_cluster_synthesis(self, synthesizer, sample_results):
        """Test cluster-based synthesis."""
        result = synthesizer.synthesize(
            sample_results,
            query="railway systems",
            synthesis_strategy="cluster"
        )
        
        assert result["strategy"] == "cluster"
        assert result["num_clusters"] == 3  # 3 documents
        assert result["total_documents"] == 3
        assert result["total_chunks"] == 5
        assert len(result["clusters"]) == 3
    
    def test_cluster_sorting(self, synthesizer, sample_results):
        """Test clusters are sorted by combined score."""
        result = synthesizer.synthesize(
            sample_results,
            query="test",
            synthesis_strategy="cluster"
        )
        
        clusters = result["clusters"]
        # doc1 has 2 chunks (0.9 + 0.8 = 1.7)
        # doc2 has 2 chunks (0.85 + 0.75 = 1.6)
        # doc3 has 1 chunk (0.7)
        
        assert abs(clusters[0]["combined_score"] - 1.7) < 0.01  # doc1
        assert abs(clusters[1]["combined_score"] - 1.6) < 0.01  # doc2
        assert abs(clusters[2]["combined_score"] - 0.7) < 0.01  # doc3
    
    def test_timeline_synthesis(self, synthesizer):
        """Test timeline-based synthesis."""
        results = [
            {
                "id": "c1",
                "document_id": "doc1",
                "processed_at": "2024-01-01T10:00:00Z",
                "text": "Old document"
            },
            {
                "id": "c2",
                "document_id": "doc2",
                "processed_at": "2024-06-01T10:00:00Z",
                "text": "Recent document"
            },
            {
                "id": "c3",
                "document_id": "doc3",
                "processed_at": "2024-03-01T10:00:00Z",
                "text": "Middle document"
            }
        ]
        
        result = synthesizer.synthesize(
            results,
            query="test",
            synthesis_strategy="timeline"
        )
        
        assert result["strategy"] == "timeline"
        assert result["num_items"] == 3
        assert result["earliest"] == "2024-01-01T10:00:00Z"
        assert result["latest"] == "2024-06-01T10:00:00Z"
        
        # Should be sorted by timestamp (most recent first)
        timeline = result["timeline"]
        assert timeline[0]["timestamp"] == "2024-06-01T10:00:00Z"
        assert timeline[1]["timestamp"] == "2024-03-01T10:00:00Z"
        assert timeline[2]["timestamp"] == "2024-01-01T10:00:00Z"
    
    def test_hierarchy_synthesis(self, synthesizer, sample_results):
        """Test hierarchy-based synthesis."""
        result = synthesizer.synthesize(
            sample_results,
            query="test",
            synthesis_strategy="hierarchy"
        )
        
        assert result["strategy"] == "hierarchy"
        assert result["num_components"] == 3  # traction, braking, hvac
        assert result["total_chunks"] == 5
        
        hierarchy = result["hierarchy"]
        assert "traction" in hierarchy
        assert "braking" in hierarchy
        assert "hvac" in hierarchy
        
        # Check traction has 2 chunks
        assert hierarchy["traction"]["num_chunks"] == 2
        assert abs(hierarchy["traction"]["avg_score"] - 0.85) < 0.01  # (0.9 + 0.8) / 2
    
    def test_invalid_strategy(self, synthesizer, sample_results):
        """Test invalid synthesis strategy."""
        with pytest.raises(ValueError, match="Unknown synthesis strategy"):
            synthesizer.synthesize(
                sample_results,
                query="test",
                synthesis_strategy="invalid"
            )
    
    def test_cross_document_comparison(self, synthesizer, sample_results):
        """Test cross-document comparison."""
        comparison = synthesizer.cross_document_comparison(
            sample_results,
            comparison_field="component_type"
        )
        
        assert comparison["field"] == "component_type"
        assert comparison["total_documents"] == 3
        assert set(comparison["all_values"]) == {"traction", "braking", "hvac"}
        
        # Check doc1 has traction
        assert "traction" in comparison["documents"]["doc1"]["values"]
        # Check doc2 has braking
        assert "braking" in comparison["documents"]["doc2"]["values"]
    
    def test_extract_consensus(self, synthesizer):
        """Test consensus extraction."""
        results = [
            {
                "id": "c1",
                "document_id": "doc1",
                "text": "The motor system requires voltage specifications"
            },
            {
                "id": "c2",
                "document_id": "doc2",
                "text": "Motor voltage must meet specifications"
            },
            {
                "id": "c3",
                "document_id": "doc3",
                "text": "System voltage requirements are critical"
            }
        ]
        
        consensus = synthesizer.extract_consensus(results, field="text")
        
        assert consensus["total_phrases"] > 0
        assert consensus["consensus_phrases"] > 0
        
        # "voltage" and "specifications" should appear in multiple docs
        top_consensus = consensus["top_consensus"]
        assert any("voltage" in phrase for phrase in top_consensus.keys())
    
    def test_consensus_coverage(self, synthesizer):
        """Test consensus coverage statistics."""
        results = [
            {"id": "c1", "document_id": "doc1", "text": "motor voltage system"},
            {"id": "c2", "document_id": "doc2", "text": "motor voltage control"},
            {"id": "c3", "document_id": "doc3", "text": "motor system power"}
        ]
        
        consensus = synthesizer.extract_consensus(results)
        coverage = consensus["coverage"]
        
        # "motor" appears in all 3 docs
        # "voltage" appears in 2 docs
        # "system" appears in 2 docs
        assert coverage["2_docs"] >= 1
        assert coverage["3_docs"] >= 1
    
    def test_generate_summary_cluster(self, synthesizer, sample_results):
        """Test summary generation for cluster synthesis."""
        synthesis_result = synthesizer.synthesize(
            sample_results,
            query="railway systems",
            synthesis_strategy="cluster"
        )
        
        summary = synthesizer.generate_summary(synthesis_result)
        
        assert "3 documents" in summary
        assert "3 clusters" in summary
        assert len(summary) <= 500
    
    def test_generate_summary_timeline(self, synthesizer):
        """Test summary generation for timeline synthesis."""
        results = [
            {
                "id": "c1",
                "document_id": "doc1",
                "processed_at": "2024-01-01T10:00:00Z"
            },
            {
                "id": "c2",
                "document_id": "doc2",
                "processed_at": "2024-06-01T10:00:00Z"
            }
        ]
        
        synthesis_result = synthesizer.synthesize(
            results,
            query="test",
            synthesis_strategy="timeline"
        )
        
        summary = synthesizer.generate_summary(synthesis_result)
        
        assert "time-ordered" in summary or "2" in summary
        assert len(summary) <= 500
    
    def test_generate_summary_hierarchy(self, synthesizer, sample_results):
        """Test summary generation for hierarchy synthesis."""
        synthesis_result = synthesizer.synthesize(
            sample_results,
            query="test",
            synthesis_strategy="hierarchy"
        )
        
        summary = synthesizer.generate_summary(synthesis_result)
        
        assert "component" in summary.lower()
        assert len(summary) <= 500
    
    def test_max_cluster_size(self):
        """Test max cluster size limit."""
        synthesizer = MultiDocumentSynthesizer(max_cluster_size=2)
        
        results = [
            {"id": f"c{i}", "document_id": "doc1", "score": 0.9}
            for i in range(5)
        ]
        
        synthesis = synthesizer.synthesize(results, "test", "cluster")
        
        # Should only include 2 chunks per cluster
        clusters = synthesis["clusters"]
        assert clusters[0]["num_chunks"] == 2
    
    def test_empty_results(self, synthesizer):
        """Test synthesis with empty results."""
        result = synthesizer.synthesize([], "test", "cluster")
        
        assert result["num_clusters"] == 0
        assert result["total_chunks"] == 0
        assert result["total_documents"] == 0
    
    def test_single_document(self, synthesizer):
        """Test synthesis with single document."""
        results = [
            {"id": "c1", "document_id": "doc1", "score": 0.9},
            {"id": "c2", "document_id": "doc1", "score": 0.8}
        ]
        
        synthesis = synthesizer.synthesize(results, "test", "cluster")
        
        assert synthesis["num_clusters"] == 1
        assert synthesis["total_documents"] == 1
        assert synthesis["total_chunks"] == 2
