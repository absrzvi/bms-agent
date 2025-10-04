"""Tests for conversation context management."""

import pytest
from datetime import datetime, timedelta
from api.conversation.context_manager import (
    ConversationTurn, ConversationContext, ContextManager, QueryDisambiguator
)


class TestConversationTurn:
    """Test conversation turn."""
    
    def test_turn_creation(self):
        """Test creating a conversation turn."""
        turn = ConversationTurn("What is the traction motor voltage?")
        
        assert turn.query == "What is the traction motor voltage?"
        assert turn.response is None
        assert len(turn.retrieved_chunks) == 0
        assert turn.turn_id is not None
    
    def test_turn_with_response(self):
        """Test turn with response."""
        turn = ConversationTurn(
            "Test query",
            response="Test response",
            retrieved_chunks=[{"id": "chunk1"}]
        )
        
        assert turn.response == "Test response"
        assert len(turn.retrieved_chunks) == 1
    
    def test_add_entity(self):
        """Test adding entities to turn."""
        turn = ConversationTurn("R4600 specifications")
        turn.add_entity("train_id", "R4600")
        turn.add_entity("component", "traction")
        
        assert "train_id" in turn.entities
        assert "R4600" in turn.entities["train_id"]
        assert "traction" in turn.entities["component"]
    
    def test_add_topic(self):
        """Test adding topics."""
        turn = ConversationTurn("Test query")
        turn.add_topic("safety")
        turn.add_topic("maintenance")
        
        assert "safety" in turn.topics
        assert "maintenance" in turn.topics
    
    def test_to_dict(self):
        """Test converting turn to dictionary."""
        turn = ConversationTurn("Test query", response="Test response")
        turn.add_entity("train_id", "R4600")
        turn.add_topic("safety")
        
        data = turn.to_dict()
        
        assert data["query"] == "Test query"
        assert data["response"] == "Test response"
        assert "train_id" in data["entities"]
        assert "safety" in data["topics"]


class TestConversationContext:
    """Test conversation context."""
    
    def test_context_creation(self):
        """Test creating conversation context."""
        context = ConversationContext()
        
        assert context.session_id is not None
        assert len(context.turns) == 0
        assert not context.is_expired()
    
    def test_add_turn(self):
        """Test adding turns to context."""
        context = ConversationContext()
        turn1 = ConversationTurn("First query")
        turn2 = ConversationTurn("Second query")
        
        context.add_turn(turn1)
        context.add_turn(turn2)
        
        assert len(context.turns) == 2
        assert context.turns[0].query == "First query"
        assert context.turns[1].query == "Second query"
    
    def test_max_turns_limit(self):
        """Test max turns limit."""
        context = ConversationContext(max_turns=3)
        
        for i in range(5):
            turn = ConversationTurn(f"Query {i}")
            context.add_turn(turn)
        
        # Should only keep last 3
        assert len(context.turns) == 3
        assert context.turns[0].query == "Query 2"
        assert context.turns[-1].query == "Query 4"
    
    def test_get_recent_turns(self):
        """Test getting recent turns."""
        context = ConversationContext()
        
        for i in range(5):
            context.add_turn(ConversationTurn(f"Query {i}"))
        
        recent = context.get_recent_turns(n=2)
        
        assert len(recent) == 2
        assert recent[0].query == "Query 3"
        assert recent[1].query == "Query 4"
    
    def test_get_context_summary(self):
        """Test getting context summary."""
        context = ConversationContext()
        
        turn1 = ConversationTurn("R4600 traction")
        turn1.add_entity("train_id", "R4600")
        turn1.add_topic("traction")
        
        turn2 = ConversationTurn("Braking system")
        turn2.add_entity("component", "braking")
        turn2.add_topic("safety")
        
        context.add_turn(turn1)
        context.add_turn(turn2)
        
        summary = context.get_context_summary()
        
        assert summary["num_turns"] == 2
        assert "train_id" in summary["entities"]
        assert "component" in summary["entities"]
        assert "traction" in summary["topics"]
        assert "safety" in summary["topics"]
    
    def test_is_expired(self):
        """Test session expiration."""
        context = ConversationContext(ttl_minutes=1)
        
        # Not expired initially
        assert not context.is_expired()
        
        # Simulate expiration
        context.last_accessed = datetime.utcnow() - timedelta(minutes=2)
        assert context.is_expired()
    
    def test_get_last_query(self):
        """Test getting last query."""
        context = ConversationContext()
        
        assert context.get_last_query() is None
        
        context.add_turn(ConversationTurn("First query"))
        context.add_turn(ConversationTurn("Second query"))
        
        assert context.get_last_query() == "Second query"
    
    def test_get_conversation_history(self):
        """Test getting conversation history."""
        context = ConversationContext()
        
        turn1 = ConversationTurn("What is the voltage?", response="400V")
        turn2 = ConversationTurn("What about current?", response="100A")
        
        context.add_turn(turn1)
        context.add_turn(turn2)
        
        history = context.get_conversation_history()
        
        assert "What is the voltage?" in history
        assert "400V" in history
        assert "What about current?" in history
        assert "100A" in history


class TestContextManager:
    """Test context manager."""
    
    def test_manager_creation(self):
        """Test creating context manager."""
        manager = ContextManager()
        
        assert len(manager.sessions) == 0
        assert manager.max_sessions == 100
    
    def test_get_or_create_session(self):
        """Test getting or creating session."""
        manager = ContextManager()
        
        # Create new session
        context1 = manager.get_or_create_session()
        assert context1.session_id is not None
        assert len(manager.sessions) == 1
        
        # Get existing session
        context2 = manager.get_or_create_session(context1.session_id)
        assert context2.session_id == context1.session_id
        assert len(manager.sessions) == 1
    
    def test_add_turn(self):
        """Test adding turn via manager."""
        manager = ContextManager()
        
        turn = manager.add_turn(
            "session1",
            "Test query",
            response="Test response"
        )
        
        assert turn.query == "Test query"
        assert turn.response == "Test response"
        
        context = manager.get_context("session1")
        assert len(context.turns) == 1
    
    def test_session_cleanup_expired(self):
        """Test cleanup of expired sessions."""
        manager = ContextManager(max_sessions=10, default_ttl_minutes=1)
        
        # Create sessions
        for i in range(5):
            manager.get_or_create_session(f"session{i}")
        
        assert len(manager.sessions) == 5
        
        # Expire some sessions
        manager.sessions["session0"].last_accessed = datetime.utcnow() - timedelta(minutes=2)
        manager.sessions["session1"].last_accessed = datetime.utcnow() - timedelta(minutes=2)
        
        # Trigger cleanup by creating new session
        manager.get_or_create_session("new_session")
        
        # Expired sessions should be removed
        assert "session0" not in manager.sessions
        assert "session1" not in manager.sessions
        assert "session2" in manager.sessions
    
    def test_session_cleanup_max_limit(self):
        """Test cleanup when max sessions exceeded."""
        manager = ContextManager(max_sessions=3)
        
        # Create 5 sessions
        for i in range(5):
            manager.get_or_create_session(f"session{i}")
        
        # Should only keep 3 most recent
        assert len(manager.sessions) <= 3
    
    def test_clear_session(self):
        """Test clearing a session."""
        manager = ContextManager()
        
        manager.add_turn("session1", "Test query")
        assert "session1" in manager.sessions
        
        manager.clear_session("session1")
        assert "session1" not in manager.sessions
    
    def test_get_stats(self):
        """Test getting manager statistics."""
        manager = ContextManager()
        
        manager.add_turn("session1", "Query 1")
        manager.add_turn("session1", "Query 2")
        manager.add_turn("session2", "Query 3")
        
        stats = manager.get_stats()
        
        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 2
        assert stats["total_turns"] == 3


class TestQueryDisambiguator:
    """Test query disambiguator."""
    
    @pytest.fixture
    def disambiguator(self):
        """Create disambiguator instance."""
        return QueryDisambiguator()
    
    def test_needs_disambiguation_pronouns(self, disambiguator):
        """Test detecting queries with pronouns."""
        assert disambiguator.needs_disambiguation("What is its voltage?")
        assert disambiguator.needs_disambiguation("Tell me about this")
        assert disambiguator.needs_disambiguation("What about that?")
    
    def test_needs_disambiguation_short(self, disambiguator):
        """Test detecting short queries."""
        assert disambiguator.needs_disambiguation("More info")
        assert disambiguator.needs_disambiguation("Details?")
    
    def test_no_disambiguation_needed(self, disambiguator):
        """Test queries that don't need disambiguation."""
        assert not disambiguator.needs_disambiguation(
            "What is the R4600 traction motor voltage?"
        )
        assert not disambiguator.needs_disambiguation(
            "Show me braking system specifications"
        )
    
    def test_disambiguate_with_context(self, disambiguator):
        """Test disambiguating query with context."""
        context = ConversationContext()
        
        turn = ConversationTurn("R4600 traction motor specs")
        turn.add_entity("train_id", "R4600")
        turn.add_entity("component", "traction")
        turn.add_topic("specifications")
        
        context.add_turn(turn)
        
        disambiguated = disambiguator.disambiguate("What is its voltage?", context)
        
        assert "R4600" in disambiguated or "train" in disambiguated.lower()
    
    def test_disambiguate_no_context(self, disambiguator):
        """Test disambiguating without context."""
        context = ConversationContext()
        
        query = "What is its voltage?"
        disambiguated = disambiguator.disambiguate(query, context)
        
        # Should return original or minimally modified
        assert "voltage" in disambiguated.lower()
    
    def test_extract_context_entities(self, disambiguator):
        """Test extracting entities from context."""
        context = ConversationContext()
        
        turn = ConversationTurn("R4600 specifications")
        turn.add_entity("train_id", "R4600")
        turn.add_entity("component", "traction")
        
        context.add_turn(turn)
        
        # Query doesn't mention train_id
        entities = disambiguator.extract_context_entities(
            "What is the voltage?",
            context
        )
        
        # Should carry over train_id
        assert "train_id" in entities
        assert entities["train_id"] == "R4600"
    
    def test_extract_context_entities_override(self, disambiguator):
        """Test that explicit mentions override context."""
        context = ConversationContext()
        
        turn = ConversationTurn("R4600 specifications")
        turn.add_entity("train_id", "R4600")
        
        context.add_turn(turn)
        
        # Query explicitly mentions different train
        entities = disambiguator.extract_context_entities(
            "What about Cityjet train_id?",
            context
        )
        
        # Should not carry over train_id since it's mentioned
        assert "train_id" not in entities
