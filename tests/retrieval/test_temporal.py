"""Tests for temporal and version-aware retrieval."""

import pytest
from datetime import datetime, timedelta
from api.retrieval.temporal import (
    TemporalFilter, VersionFilter, TemporalRetriever, RecencyScorer
)


class TestTemporalFilter:
    """Test temporal filter."""
    
    def test_filter_creation(self):
        """Test creating temporal filter."""
        tf = TemporalFilter(
            after="2024-01-01T00:00:00Z",
            before="2024-12-31T23:59:59Z"
        )
        
        assert tf.after is not None
        assert tf.before is not None
    
    def test_matches_within_range(self):
        """Test matching timestamp within range."""
        tf = TemporalFilter(
            after="2024-01-01T00:00:00Z",
            before="2024-12-31T23:59:59Z"
        )
        
        assert tf.matches("2024-06-15T12:00:00Z")
        assert tf.matches("2024-01-01T00:00:00Z")
        assert tf.matches("2024-12-31T23:59:59Z")
    
    def test_matches_outside_range(self):
        """Test matching timestamp outside range."""
        tf = TemporalFilter(
            after="2024-01-01T00:00:00Z",
            before="2024-12-31T23:59:59Z"
        )
        
        assert not tf.matches("2023-12-31T23:59:59Z")
        assert not tf.matches("2025-01-01T00:00:01Z")
    
    def test_matches_no_timestamp(self):
        """Test matching when no timestamp provided."""
        tf = TemporalFilter(after="2024-01-01T00:00:00Z")
        
        assert tf.matches(None)
        assert tf.matches("")
    
    def test_to_qdrant_filter(self):
        """Test converting to Qdrant filter."""
        tf = TemporalFilter(
            after="2024-01-01T00:00:00Z",
            before="2024-12-31T23:59:59Z"
        )
        
        qdrant_filter = tf.to_qdrant_filter()
        
        assert "must" in qdrant_filter
        assert len(qdrant_filter["must"]) == 2


class TestVersionFilter:
    """Test version filter."""
    
    def test_filter_creation(self):
        """Test creating version filter."""
        vf = VersionFilter(version="v1.0", latest_only=True)
        
        assert vf.version == "v1.0"
        assert vf.latest_only is True
    
    def test_matches_version(self):
        """Test matching specific version."""
        vf = VersionFilter(version="v1.0")
        
        assert vf.matches("v1.0")
        assert not vf.matches("v2.0")
    
    def test_matches_no_version_filter(self):
        """Test matching when no version specified."""
        vf = VersionFilter()
        
        assert vf.matches("v1.0")
        assert vf.matches("v2.0")
        assert vf.matches(None)
    
    def test_to_qdrant_filter(self):
        """Test converting to Qdrant filter."""
        vf = VersionFilter(version="v1.0")
        
        qdrant_filter = vf.to_qdrant_filter()
        
        assert qdrant_filter["key"] == "version"
        assert qdrant_filter["match"]["value"] == "v1.0"


class TestTemporalRetriever:
    """Test temporal retriever."""
    
    @pytest.fixture
    def retriever(self):
        """Create retriever instance."""
        return TemporalRetriever(decay_factor=0.1)
    
    @pytest.fixture
    def sample_results(self):
        """Sample results with timestamps."""
        now = datetime.utcnow()
        return [
            {
                "id": "chunk1",
                "score": 0.9,
                "processed_at": now.isoformat() + "Z"
            },
            {
                "id": "chunk2",
                "score": 0.8,
                "processed_at": (now - timedelta(days=30)).isoformat() + "Z"
            },
            {
                "id": "chunk3",
                "score": 0.85,
                "processed_at": (now - timedelta(days=180)).isoformat() + "Z"
            }
        ]
    
    def test_apply_temporal_boost(self, retriever, sample_results):
        """Test applying temporal boost."""
        boosted = retriever.apply_temporal_boost(sample_results)
        
        assert len(boosted) == 3
        assert all("temporal_boost" in r for r in boosted)
        assert all("boosted_score" in r for r in boosted)
        
        # Most recent should have highest boost
        chunk1 = next(r for r in boosted if r["id"] == "chunk1")
        chunk3 = next(r for r in boosted if r["id"] == "chunk3")
        assert chunk1["temporal_boost"] > chunk3["temporal_boost"]
    
    def test_filter_by_date_range(self, retriever, sample_results):
        """Test filtering by date range."""
        now = datetime.utcnow()
        after = (now - timedelta(days=60)).isoformat() + "Z"
        
        filtered = retriever.filter_by_date_range(
            sample_results,
            after=after
        )
        
        # Should exclude chunk3 (180 days old)
        assert len(filtered) == 2
        assert all(r["id"] != "chunk3" for r in filtered)
    
    def test_get_latest_versions(self, retriever):
        """Test getting latest versions."""
        results = [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "score": 0.9,
                "processed_at": "2024-06-01T00:00:00Z"
            },
            {
                "id": "chunk2",
                "document_id": "doc1",
                "score": 0.8,
                "processed_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "chunk3",
                "document_id": "doc2",
                "score": 0.85,
                "processed_at": "2024-03-01T00:00:00Z"
            }
        ]
        
        latest = retriever.get_latest_versions(results)
        
        # Should have 2 documents (latest version of each)
        assert len(latest) == 2
        
        # doc1 latest should be chunk1 (June)
        doc1_latest = next(r for r in latest if r["document_id"] == "doc1")
        assert doc1_latest["id"] == "chunk1"
        assert doc1_latest["is_latest"] is True
        assert doc1_latest["version_count"] == 2
    
    def test_compare_versions(self, retriever):
        """Test comparing document versions."""
        results = [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "version": "v2.0",
                "score": 0.9,
                "processed_at": "2024-06-01T00:00:00Z"
            },
            {
                "id": "chunk2",
                "document_id": "doc1",
                "version": "v1.0",
                "score": 0.8,
                "processed_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "chunk3",
                "document_id": "doc2",
                "version": "v1.0",
                "score": 0.85,
                "processed_at": "2024-03-01T00:00:00Z"
            }
        ]
        
        comparison = retriever.compare_versions(results, "doc1")
        
        assert comparison["document_id"] == "doc1"
        assert comparison["version_count"] == 2
        assert comparison["latest_version"]["version"] == "v2.0"
        assert len(comparison["versions"]) == 2
    
    def test_compare_versions_not_found(self, retriever):
        """Test comparing versions for non-existent document."""
        results = [
            {"id": "chunk1", "document_id": "doc1", "score": 0.9}
        ]
        
        comparison = retriever.compare_versions(results, "doc999")
        
        assert comparison["document_id"] == "doc999"
        assert comparison["version_count"] == 0
        assert len(comparison["versions"]) == 0


class TestRecencyScorer:
    """Test recency scorer."""
    
    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return RecencyScorer(max_age_days=365, min_score=0.5)
    
    def test_calculate_recency_score_recent(self, scorer):
        """Test recency score for recent document."""
        now = datetime.utcnow()
        timestamp = now.isoformat() + "Z"
        
        score = scorer.calculate_recency_score(timestamp)
        
        assert score == 1.0
    
    def test_calculate_recency_score_old(self, scorer):
        """Test recency score for old document."""
        now = datetime.utcnow()
        old_date = now - timedelta(days=365)
        timestamp = old_date.isoformat() + "Z"
        
        score = scorer.calculate_recency_score(timestamp)
        
        assert score == 0.5  # min_score
    
    def test_calculate_recency_score_mid(self, scorer):
        """Test recency score for mid-age document."""
        now = datetime.utcnow()
        mid_date = now - timedelta(days=182)  # ~6 months
        timestamp = mid_date.isoformat() + "Z"
        
        score = scorer.calculate_recency_score(timestamp)
        
        # Should be between 0.5 and 1.0
        assert 0.5 < score < 1.0
        assert abs(score - 0.75) < 0.05  # Approximately 0.75
    
    def test_calculate_recency_score_no_timestamp(self, scorer):
        """Test recency score with no timestamp."""
        score = scorer.calculate_recency_score(None)
        
        assert score == 0.5  # min_score
    
    def test_score_results(self, scorer):
        """Test scoring results with recency."""
        now = datetime.utcnow()
        results = [
            {
                "id": "chunk1",
                "score": 0.8,
                "processed_at": now.isoformat() + "Z"
            },
            {
                "id": "chunk2",
                "score": 0.9,
                "processed_at": (now - timedelta(days=365)).isoformat() + "Z"
            }
        ]
        
        scored = scorer.score_results(results, weight=0.3)
        
        assert len(scored) == 2
        assert all("recency_score" in r for r in scored)
        assert all("combined_score" in r for r in scored)
        
        # Recent document with lower score might rank higher
        chunk1 = next(r for r in scored if r["id"] == "chunk1")
        chunk2 = next(r for r in scored if r["id"] == "chunk2")
        
        # chunk1 is recent (recency=1.0) with score 0.8
        # chunk2 is old (recency=0.5) with score 0.9
        # combined1 = 0.8 * 0.7 + 1.0 * 0.3 = 0.56 + 0.3 = 0.86
        # combined2 = 0.9 * 0.7 + 0.5 * 0.3 = 0.63 + 0.15 = 0.78
        assert chunk1["combined_score"] > chunk2["combined_score"]
