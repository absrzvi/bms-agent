"""
Tests for contextual retrieval functionality
"""

import pytest
from unittest.mock import Mock, MagicMock
from api.retrieval.contextual import ContextualRetriever, ContextualResult


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    client = Mock()
    return client


@pytest.fixture
def contextual_retriever(mock_qdrant_client):
    """Create contextual retriever instance"""
    return ContextualRetriever(
        qdrant_client=mock_qdrant_client,
        collection_name="test_collection",
        parent_weight=0.3,
        child_weight=0.2,
        full_doc_weight=0.1
    )


def test_contextual_retriever_initialization(contextual_retriever):
    """Test contextual retriever initialization"""
    assert contextual_retriever.collection_name == "test_collection"
    assert contextual_retriever.parent_weight == 0.3
    assert contextual_retriever.child_weight == 0.2
    assert contextual_retriever.full_doc_weight == 0.1


def test_weight_normalization():
    """Test that weights are normalized if they exceed 1.0"""
    client = Mock()
    retriever = ContextualRetriever(
        qdrant_client=client,
        parent_weight=0.5,
        child_weight=0.5,
        full_doc_weight=0.5  # Total = 1.5, should normalize
    )
    
    # Weights should be normalized
    total = retriever.parent_weight + retriever.child_weight + retriever.full_doc_weight
    assert abs(total - 1.0) < 0.01  # Allow small floating point error


def test_search_without_context(contextual_retriever, mock_qdrant_client):
    """Test search without context expansion"""
    # Mock search results
    mock_result = Mock()
    mock_result.id = "test-id-1"
    mock_result.score = 0.95
    mock_result.payload = {
        "chunk_id": "chunk-1",
        "content": "Test content",
        "document_name": "test.pdf",
        "quality_score": 0.9
    }
    
    mock_qdrant_client.search.return_value = [mock_result]
    
    # Perform search
    query_embedding = [0.1] * 768
    results = contextual_retriever.search_with_context(
        query_embedding=query_embedding,
        limit=10,
        include_context=False
    )
    
    # Verify results
    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert results[0].content == "Test content"
    assert results[0].score == 0.95
    assert results[0].parent_content is None
    assert results[0].child_contents is None


def test_search_with_min_score_filter(contextual_retriever, mock_qdrant_client):
    """Test search with minimum score filtering"""
    # Mock search results with varying scores
    mock_results = []
    for i, score in enumerate([0.95, 0.85, 0.75, 0.65]):
        mock_result = Mock()
        mock_result.id = f"test-id-{i}"
        mock_result.score = score
        mock_result.payload = {
            "chunk_id": f"chunk-{i}",
            "content": f"Test content {i}",
            "quality_score": 0.9
        }
        mock_results.append(mock_result)
    
    mock_qdrant_client.search.return_value = mock_results
    
    # Search with min_score=0.8
    query_embedding = [0.1] * 768
    results = contextual_retriever.search_with_context(
        query_embedding=query_embedding,
        limit=10,
        include_context=False,
        min_score=0.8
    )
    
    # Should only return results with score >= 0.8
    assert len(results) == 2
    assert all(r.score >= 0.8 for r in results)


def test_cosine_similarity():
    """Test cosine similarity calculation"""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    
    similarity = ContextualRetriever._cosine_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 0.01  # Should be 1.0 for identical vectors
    
    vec3 = [0.0, 1.0, 0.0]
    similarity = ContextualRetriever._cosine_similarity(vec1, vec3)
    assert abs(similarity - 0.0) < 0.01  # Should be 0.0 for orthogonal vectors


def test_get_parent_content(contextual_retriever, mock_qdrant_client):
    """Test retrieving parent chunk content"""
    # Mock scroll results
    mock_point = Mock()
    mock_point.payload = {"content": "Parent chunk content"}
    mock_qdrant_client.scroll.return_value = ([mock_point], None)
    
    parent_content = contextual_retriever._get_parent_content("parent-chunk-id")
    
    assert parent_content == "Parent chunk content"
    mock_qdrant_client.scroll.assert_called_once()


def test_get_child_contents(contextual_retriever, mock_qdrant_client):
    """Test retrieving child chunk contents"""
    # Mock scroll results with multiple children
    mock_children = []
    for i in range(3):
        mock_child = Mock()
        mock_child.payload = {"content": f"Child content {i}"}
        mock_children.append(mock_child)
    
    mock_qdrant_client.scroll.return_value = (mock_children, None)
    
    child_contents = contextual_retriever._get_child_contents("parent-chunk-id")
    
    assert len(child_contents) == 3
    assert child_contents[0] == "Child content 0"
    assert child_contents[2] == "Child content 2"


def test_get_expanded_context(contextual_retriever, mock_qdrant_client):
    """Test getting expanded context window"""
    # Mock current chunk
    current_chunk = Mock()
    current_chunk.payload = {
        "chunk_id": "chunk-5",
        "content": "Current chunk",
        "document_id": "doc-1",
        "document_name": "test.pdf",
        "chunk_index": 5
    }
    
    # Mock all chunks from document
    all_chunks = []
    for i in range(10):
        chunk = Mock()
        chunk.payload = {
            "chunk_id": f"chunk-{i}",
            "content": f"Content {i}",
            "document_id": "doc-1",
            "chunk_index": i
        }
        all_chunks.append(chunk)
    
    mock_qdrant_client.scroll.side_effect = [
        ([current_chunk], None),  # First call for current chunk
        (all_chunks, None)  # Second call for all chunks
    ]
    
    context = contextual_retriever.get_expanded_context("chunk-5", window_size=2)
    
    assert context["current"] == "Current chunk"
    assert len(context["before"]) == 2
    assert len(context["after"]) == 2
    assert context["before"][0] == "Content 3"
    assert context["before"][1] == "Content 4"
    assert context["after"][0] == "Content 6"
    assert context["after"][1] == "Content 7"
    assert context["chunk_index"] == 5
    assert context["total_chunks"] == 10


def test_contextual_result_dataclass():
    """Test ContextualResult dataclass"""
    result = ContextualResult(
        chunk_id="test-chunk",
        content="Test content",
        score=0.95,
        metadata={"document_name": "test.pdf"},
        parent_content="Parent content",
        child_contents=["Child 1", "Child 2"],
        context_score=0.85
    )
    
    assert result.chunk_id == "test-chunk"
    assert result.content == "Test content"
    assert result.score == 0.95
    assert result.parent_content == "Parent content"
    assert len(result.child_contents) == 2
    assert result.context_score == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
