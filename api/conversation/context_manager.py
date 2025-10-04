"""Conversation context management for multi-turn interactions."""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class ConversationTurn:
    """Single turn in a conversation."""
    
    def __init__(
        self,
        query: str,
        response: Optional[str] = None,
        retrieved_chunks: Optional[List[Dict]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Initialize conversation turn."""
        self.turn_id = str(uuid.uuid4())
        self.query = query
        self.response = response
        self.retrieved_chunks = retrieved_chunks or []
        self.timestamp = timestamp or datetime.utcnow()
        self.entities = {}
        self.topics = set()
    
    def add_entity(self, entity_type: str, entity_value: str):
        """Add extracted entity."""
        if entity_type not in self.entities:
            self.entities[entity_type] = []
        self.entities[entity_type].append(entity_value)
    
    def add_topic(self, topic: str):
        """Add conversation topic."""
        self.topics.add(topic)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "turn_id": self.turn_id,
            "query": self.query,
            "response": self.response,
            "num_chunks": len(self.retrieved_chunks),
            "timestamp": self.timestamp.isoformat(),
            "entities": self.entities,
            "topics": list(self.topics)
        }


class ConversationContext:
    """Manages conversation context across multiple turns."""
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        max_turns: int = 10,
        ttl_minutes: int = 30
    ):
        """
        Initialize conversation context.
        
        Args:
            session_id: Unique session identifier
            max_turns: Maximum turns to keep in history
            ttl_minutes: Time-to-live for session in minutes
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.turns: List[ConversationTurn] = []
        self.max_turns = max_turns
        self.ttl = timedelta(minutes=ttl_minutes)
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.metadata = {}
    
    def add_turn(self, turn: ConversationTurn):
        """Add a turn to the conversation."""
        self.turns.append(turn)
        self.last_accessed = datetime.utcnow()
        
        # Trim if exceeds max turns
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
    
    def get_recent_turns(self, n: int = 3) -> List[ConversationTurn]:
        """Get n most recent turns."""
        return self.turns[-n:] if self.turns else []
    
    def get_context_summary(self) -> Dict:
        """Get summary of conversation context."""
        all_entities = {}
        all_topics = set()
        
        for turn in self.turns:
            # Merge entities
            for entity_type, values in turn.entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = []
                all_entities[entity_type].extend(values)
            
            # Merge topics
            all_topics.update(turn.topics)
        
        return {
            "session_id": self.session_id,
            "num_turns": len(self.turns),
            "entities": all_entities,
            "topics": list(all_topics),
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat()
        }
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() - self.last_accessed > self.ttl
    
    def get_last_query(self) -> Optional[str]:
        """Get the last query in conversation."""
        return self.turns[-1].query if self.turns else None
    
    def get_conversation_history(self, max_chars: int = 1000) -> str:
        """
        Get conversation history as text.
        
        Args:
            max_chars: Maximum characters to return
            
        Returns:
            Formatted conversation history
        """
        history = []
        total_chars = 0
        
        for turn in reversed(self.turns):
            turn_text = f"Q: {turn.query}\n"
            if turn.response:
                turn_text += f"A: {turn.response}\n"
            
            if total_chars + len(turn_text) > max_chars:
                break
            
            history.insert(0, turn_text)
            total_chars += len(turn_text)
        
        return "\n".join(history)


class ContextManager:
    """Manages multiple conversation contexts."""
    
    def __init__(
        self,
        max_sessions: int = 100,
        default_ttl_minutes: int = 30
    ):
        """
        Initialize context manager.
        
        Args:
            max_sessions: Maximum number of active sessions
            default_ttl_minutes: Default TTL for sessions
        """
        self.sessions: Dict[str, ConversationContext] = {}
        self.max_sessions = max_sessions
        self.default_ttl_minutes = default_ttl_minutes
    
    def get_or_create_session(
        self,
        session_id: Optional[str] = None
    ) -> ConversationContext:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            ConversationContext
        """
        if session_id and session_id in self.sessions:
            context = self.sessions[session_id]
            if not context.is_expired():
                return context
            else:
                # Remove expired session
                del self.sessions[session_id]
        
        # Create new session
        context = ConversationContext(
            session_id=session_id,
            ttl_minutes=self.default_ttl_minutes
        )
        self.sessions[context.session_id] = context
        
        # Cleanup if too many sessions
        self._cleanup_sessions()
        
        return context
    
    def _cleanup_sessions(self):
        """Remove expired sessions and enforce max limit."""
        # Remove expired
        expired = [
            sid for sid, ctx in self.sessions.items()
            if ctx.is_expired()
        ]
        for sid in expired:
            del self.sessions[sid]
        
        # Enforce max sessions (remove oldest)
        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_accessed
            )
            to_remove = len(self.sessions) - self.max_sessions
            for sid, _ in sorted_sessions[:to_remove]:
                del self.sessions[sid]
    
    def add_turn(
        self,
        session_id: str,
        query: str,
        response: Optional[str] = None,
        retrieved_chunks: Optional[List[Dict]] = None
    ) -> ConversationTurn:
        """
        Add a turn to a session.
        
        Args:
            session_id: Session identifier
            query: User query
            response: System response
            retrieved_chunks: Retrieved chunks
            
        Returns:
            Created ConversationTurn
        """
        context = self.get_or_create_session(session_id)
        turn = ConversationTurn(query, response, retrieved_chunks)
        context.add_turn(turn)
        return turn
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for session."""
        return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str):
        """Clear a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_stats(self) -> Dict:
        """Get manager statistics."""
        active_sessions = sum(
            1 for ctx in self.sessions.values()
            if not ctx.is_expired()
        )
        
        total_turns = sum(
            len(ctx.turns) for ctx in self.sessions.values()
        )
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "total_turns": total_turns,
            "max_sessions": self.max_sessions
        }


class QueryDisambiguator:
    """Disambiguate follow-up queries using conversation context."""
    
    def __init__(self):
        """Initialize query disambiguator."""
        self.pronoun_patterns = {
            "it", "its", "this", "that", "these", "those",
            "they", "them", "their"
        }
    
    def needs_disambiguation(self, query: str) -> bool:
        """
        Check if query needs disambiguation.
        
        Args:
            query: User query
            
        Returns:
            True if query contains pronouns or is very short
        """
        query_lower = query.lower()
        words = query_lower.split()
        
        # Check for pronouns
        has_pronouns = any(word in self.pronoun_patterns for word in words)
        
        # Check if very short (likely follow-up)
        is_short = len(words) <= 3
        
        return has_pronouns or is_short
    
    def disambiguate(
        self,
        query: str,
        context: ConversationContext
    ) -> str:
        """
        Disambiguate query using conversation context.
        
        Args:
            query: Current query
            context: Conversation context
            
        Returns:
            Disambiguated query
        """
        if not self.needs_disambiguation(query):
            return query
        
        # Get context summary
        summary = context.get_context_summary()
        
        # Build disambiguated query
        disambiguated_parts = [query]
        
        # Add entities from context
        entities = summary.get("entities", {})
        if entities:
            # Add train IDs
            if "train_id" in entities and entities["train_id"]:
                train_id = entities["train_id"][-1]  # Most recent
                disambiguated_parts.append(f"(train: {train_id})")
            
            # Add components
            if "component" in entities and entities["component"]:
                component = entities["component"][-1]
                disambiguated_parts.append(f"(component: {component})")
        
        # Add topics
        topics = summary.get("topics", [])
        if topics:
            topic = topics[-1]  # Most recent topic
            disambiguated_parts.append(f"(topic: {topic})")
        
        return " ".join(disambiguated_parts)
    
    def extract_context_entities(
        self,
        query: str,
        context: ConversationContext
    ) -> Dict:
        """
        Extract entities that should be carried over from context.
        
        Args:
            query: Current query
            context: Conversation context
            
        Returns:
            Dictionary of context entities
        """
        context_entities = {}
        
        if not context.turns:
            return context_entities
        
        # Get last turn's entities
        last_turn = context.turns[-1]
        
        # Carry over entities if current query doesn't specify them
        query_lower = query.lower()
        
        for entity_type, values in last_turn.entities.items():
            # Check if entity type mentioned in current query
            if entity_type.lower() not in query_lower and values:
                context_entities[entity_type] = values[-1]
        
        return context_entities
