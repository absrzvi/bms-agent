"""
Tests for answer generation functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from api.generation.answer_generator import (
    AnswerGenerator,
    RailwayAnswerGenerator,
    GeneratedAnswer,
    Citation
)


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
    return {
        "response": "This is a test answer based on the provided context.",
        "model": "mistral-nemo:12b-instruct"
    }


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing"""
    return [
        {
            "chunk_id": "chunk-1",
            "content": "Railway safety procedures require proper training.",
            "score": 0.95,
            "metadata": {
                "document_name": "safety_manual.pdf",
                "chunk_index": 0
            }
        },
        {
            "chunk_id": "chunk-2",
            "content": "All personnel must follow EN50155 standards.",
            "score": 0.88,
            "metadata": {
                "document_name": "standards.pdf",
                "chunk_index": 5
            }
        }
    ]


@pytest.fixture
def answer_generator():
    """Create answer generator instance"""
    return AnswerGenerator(
        ollama_url="http://localhost:11434",
        model_name="mistral-nemo:12b-instruct",
        temperature=0.7,
        max_tokens=500
    )


def test_answer_generator_initialization(answer_generator):
    """Test answer generator initialization"""
    assert answer_generator.ollama_url == "http://localhost:11434"
    assert answer_generator.model_name == "mistral-nemo:12b-instruct"
    assert answer_generator.temperature == 0.7
    assert answer_generator.max_tokens == 500


def test_build_context(answer_generator, sample_chunks):
    """Test context building from chunks"""
    context = answer_generator._build_context(sample_chunks)
    
    assert "safety_manual.pdf" in context
    assert "standards.pdf" in context
    assert "Railway safety procedures" in context
    assert "[1]" in context
    assert "[2]" in context


def test_create_citations(answer_generator, sample_chunks):
    """Test citation creation"""
    citations = answer_generator._create_citations(sample_chunks)
    
    assert len(citations) == 2
    assert all(isinstance(c, Citation) for c in citations)
    assert citations[0].document_name == "safety_manual.pdf"
    assert citations[1].document_name == "standards.pdf"
    assert citations[0].relevance_score == 0.95


def test_create_prompt(answer_generator):
    """Test prompt creation"""
    query = "What are the safety requirements?"
    context = "[1] Safety manual: Follow all procedures"
    
    prompt = answer_generator._create_prompt(query, context, include_citations=True)
    
    assert query in prompt
    assert context in prompt
    assert "cite" in prompt.lower() or "source" in prompt.lower()


def test_calculate_confidence(answer_generator, sample_chunks):
    """Test confidence calculation"""
    confidence = answer_generator._calculate_confidence(sample_chunks)
    
    assert 0.0 <= confidence <= 1.0
    # Should be high since top score is 0.95
    assert confidence > 0.8


def test_calculate_confidence_empty_chunks(answer_generator):
    """Test confidence with empty chunks"""
    confidence = answer_generator._calculate_confidence([])
    assert confidence == 0.0


@patch('requests.post')
def test_call_ollama_success(mock_post, answer_generator, mock_ollama_response):
    """Test successful Ollama API call"""
    mock_response = Mock()
    mock_response.json.return_value = mock_ollama_response
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    prompt = "Test prompt"
    answer = answer_generator._call_ollama(prompt)
    
    assert answer == "This is a test answer based on the provided context."
    mock_post.assert_called_once()


@patch('requests.post')
def test_call_ollama_failure(mock_post, answer_generator):
    """Test Ollama API failure"""
    mock_post.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        answer_generator._call_ollama("Test prompt")


@patch('requests.post')
def test_generate_answer_success(mock_post, answer_generator, sample_chunks, mock_ollama_response):
    """Test successful answer generation"""
    mock_response = Mock()
    mock_response.json.return_value = mock_ollama_response
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    result = answer_generator.generate_answer(
        query="What are safety requirements?",
        chunks=sample_chunks,
        max_chunks=5,
        include_citations=True
    )
    
    assert isinstance(result, GeneratedAnswer)
    assert result.answer == "This is a test answer based on the provided context."
    assert len(result.citations) == 2
    assert result.confidence > 0.0
    assert result.model_name == "mistral-nemo:12b-instruct"


@patch('requests.post')
def test_generate_answer_with_fallback(mock_post, answer_generator, sample_chunks):
    """Test fallback answer when LLM fails"""
    mock_post.side_effect = Exception("LLM Error")
    
    result = answer_generator.generate_answer(
        query="Test query",
        chunks=sample_chunks,
        max_chunks=5
    )
    
    assert isinstance(result, GeneratedAnswer)
    assert result.model_name == "fallback"
    assert result.confidence == 0.5  # Lower confidence for fallback


def test_validate_answer(answer_generator, sample_chunks):
    """Test answer validation"""
    answer = "Railway safety requires proper training and following EN50155 standards."
    query = "What are railway safety requirements?"
    
    validation = answer_generator.validate_answer(answer, query, sample_chunks)
    
    assert "is_relevant" in validation
    assert "is_complete" in validation
    assert "is_safe" in validation
    assert "quality_score" in validation
    assert validation["is_relevant"] is True
    assert validation["is_complete"] is True


def test_validate_answer_incomplete(answer_generator, sample_chunks):
    """Test validation of incomplete answer"""
    answer = "Short"
    query = "What are safety requirements?"
    
    validation = answer_generator.validate_answer(answer, query, sample_chunks)
    
    assert validation["is_complete"] is False
    assert validation["quality_score"] < 0.5


def test_railway_answer_generator_classify_query():
    """Test query classification"""
    generator = RailwayAnswerGenerator()
    
    assert generator._classify_query("What are the safety procedures?") == "safety"
    assert generator._classify_query("What is the technical specification?") == "technical"
    assert generator._classify_query("How to install this equipment?") == "procedural"
    assert generator._classify_query("General railway question") == "general"


def test_railway_answer_generator_safety_prompt():
    """Test safety-specific prompt creation"""
    generator = RailwayAnswerGenerator()
    
    query = "What are the safety requirements?"
    context = "Safety context"
    
    prompt = generator._create_safety_prompt(query, context, include_citations=True)
    
    assert "safety" in prompt.lower()
    assert "critical" in prompt.lower() or "warning" in prompt.lower()
    assert query in prompt
    assert context in prompt


def test_railway_answer_generator_technical_prompt():
    """Test technical prompt creation"""
    generator = RailwayAnswerGenerator()
    
    query = "What are the technical specifications?"
    context = "Technical context"
    
    prompt = generator._create_technical_prompt(query, context, include_citations=True)
    
    assert "technical" in prompt.lower()
    assert "specification" in prompt.lower() or "standard" in prompt.lower()


def test_railway_answer_generator_procedural_prompt():
    """Test procedural prompt creation"""
    generator = RailwayAnswerGenerator()
    
    query = "How to install the system?"
    context = "Installation context"
    
    prompt = generator._create_procedural_prompt(query, context, include_citations=True)
    
    assert "step" in prompt.lower() or "procedure" in prompt.lower()
    assert query in prompt


def test_citation_dataclass():
    """Test Citation dataclass"""
    citation = Citation(
        chunk_id="test-chunk",
        document_name="test.pdf",
        content="Test content",
        relevance_score=0.95,
        chunk_index=0
    )
    
    assert citation.chunk_id == "test-chunk"
    assert citation.document_name == "test.pdf"
    assert citation.relevance_score == 0.95


def test_generated_answer_dataclass():
    """Test GeneratedAnswer dataclass"""
    answer = GeneratedAnswer(
        answer="Test answer",
        citations=[],
        confidence=0.9,
        generation_time_ms=150.0,
        model_name="test-model"
    )
    
    assert answer.answer == "Test answer"
    assert answer.confidence == 0.9
    assert answer.generation_time_ms == 150.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
