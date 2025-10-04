"""
Answer Generation Pipeline
LLM-based answer generation from retrieved chunks with citation tracking
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation for answer source"""
    chunk_id: str
    document_name: str
    content: str
    relevance_score: float
    chunk_index: int


@dataclass
class GeneratedAnswer:
    """Generated answer with citations"""
    answer: str
    citations: List[Citation]
    confidence: float
    generation_time_ms: float
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class AnswerGenerator:
    """
    LLM-based answer generator with citation tracking
    Uses local Ollama for answer generation
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "mistral-nemo:12b-instruct",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize answer generator
        
        Args:
            ollama_url: Ollama API URL
            model_name: LLM model name
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"✅ Answer generator initialized: {model_name} @ {ollama_url}")
    
    def generate_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        max_chunks: int = 5,
        include_citations: bool = True,
        stream: bool = False
    ) -> GeneratedAnswer:
        """
        Generate answer from retrieved chunks
        
        Args:
            query: User query
            chunks: Retrieved chunks with content and metadata
            max_chunks: Maximum chunks to use for context
            include_citations: Include citations in answer
            stream: Stream response (not implemented yet)
            
        Returns:
            Generated answer with citations
        """
        start_time = time.time()
        
        # Select top chunks for context
        context_chunks = chunks[:max_chunks]
        
        # Build context from chunks
        context = self._build_context(context_chunks)
        
        # Create citations
        citations = []
        if include_citations:
            citations = self._create_citations(context_chunks)
        
        # Generate prompt
        prompt = self._create_prompt(query, context, include_citations)
        
        # Call Ollama API
        try:
            answer_text = self._call_ollama(prompt)
            
            # Calculate confidence based on chunk scores
            confidence = self._calculate_confidence(context_chunks)
            
            generation_time = (time.time() - start_time) * 1000
            
            return GeneratedAnswer(
                answer=answer_text,
                citations=citations,
                confidence=confidence,
                generation_time_ms=generation_time,
                model_name=self.model_name
            )
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            # Fallback: return concatenated chunks
            return self._fallback_answer(query, context_chunks, start_time)
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "")
            doc_name = chunk.get("metadata", {}).get("document_name", "Unknown")
            
            context_parts.append(f"[{i}] From {doc_name}:\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _create_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        """Create citations from chunks"""
        citations = []
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            
            citation = Citation(
                chunk_id=chunk.get("chunk_id", ""),
                document_name=metadata.get("document_name", "Unknown"),
                content=chunk.get("content", "")[:200] + "...",  # Truncate
                relevance_score=chunk.get("score", 0.0),
                chunk_index=metadata.get("chunk_index", 0)
            )
            citations.append(citation)
        
        return citations
    
    def _create_prompt(
        self,
        query: str,
        context: str,
        include_citations: bool
    ) -> str:
        """Create prompt for LLM"""
        
        citation_instruction = ""
        if include_citations:
            citation_instruction = "\nWhen referencing information, cite the source using [1], [2], etc."
        
        prompt = f"""You are a helpful assistant for railway documentation. Answer the question based on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, accurate answer based on the context
- If the context doesn't contain enough information, say so
- Be concise but complete{citation_instruction}
- Focus on railway safety and technical accuracy

Answer:"""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for generation"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    def _calculate_confidence(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate answer confidence based on chunk scores"""
        if not chunks:
            return 0.0
        
        # Average of top chunk scores
        scores = [chunk.get("score", 0.0) for chunk in chunks]
        avg_score = sum(scores) / len(scores)
        
        # Boost if top score is high
        top_score = scores[0] if scores else 0.0
        confidence = (avg_score * 0.7) + (top_score * 0.3)
        
        return min(confidence, 1.0)
    
    def _fallback_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        start_time: float
    ) -> GeneratedAnswer:
        """Fallback answer when LLM fails"""
        
        # Return top chunks as answer
        answer_parts = []
        citations = []
        
        for i, chunk in enumerate(chunks[:3], 1):
            content = chunk.get("content", "")
            doc_name = chunk.get("metadata", {}).get("document_name", "Unknown")
            
            answer_parts.append(f"From {doc_name}:\n{content}")
            
            citations.append(Citation(
                chunk_id=chunk.get("chunk_id", ""),
                document_name=doc_name,
                content=content[:200] + "...",
                relevance_score=chunk.get("score", 0.0),
                chunk_index=chunk.get("metadata", {}).get("chunk_index", 0)
            ))
        
        answer = "\n\n".join(answer_parts)
        generation_time = (time.time() - start_time) * 1000
        
        logger.warning("Using fallback answer (LLM unavailable)")
        
        return GeneratedAnswer(
            answer=answer,
            citations=citations,
            confidence=0.5,  # Lower confidence for fallback
            generation_time_ms=generation_time,
            model_name="fallback"
        )
    
    def validate_answer(
        self,
        answer: str,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate answer quality
        
        Returns:
            Validation results with scores
        """
        validation = {
            "is_relevant": True,
            "is_complete": True,
            "is_safe": True,
            "quality_score": 0.8
        }
        
        # Basic validation checks
        if not answer or len(answer) < 10:
            validation["is_complete"] = False
            validation["quality_score"] = 0.3
        
        # Check if answer relates to query
        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        overlap = len(query_terms & answer_terms)
        
        if overlap < len(query_terms) * 0.3:
            validation["is_relevant"] = False
            validation["quality_score"] *= 0.7
        
        # Safety check for railway context
        safety_keywords = ["safety", "warning", "caution", "danger", "risk"]
        if any(kw in query.lower() for kw in safety_keywords):
            if not any(kw in answer.lower() for kw in safety_keywords):
                validation["is_safe"] = False
                validation["quality_score"] *= 0.5
        
        return validation


class RailwayAnswerGenerator(AnswerGenerator):
    """
    Railway-specific answer generator with domain prompts
    """
    
    def _create_prompt(
        self,
        query: str,
        context: str,
        include_citations: bool
    ) -> str:
        """Create railway-specific prompt"""
        
        # Detect query type
        query_type = self._classify_query(query)
        
        if query_type == "safety":
            return self._create_safety_prompt(query, context, include_citations)
        elif query_type == "technical":
            return self._create_technical_prompt(query, context, include_citations)
        elif query_type == "procedural":
            return self._create_procedural_prompt(query, context, include_citations)
        else:
            return super()._create_prompt(query, context, include_citations)
    
    def _classify_query(self, query: str) -> str:
        """Classify query type"""
        query_lower = query.lower()
        
        safety_keywords = ["safety", "danger", "risk", "hazard", "warning", "emergency"]
        technical_keywords = ["technical", "specification", "component", "system", "voltage", "current"]
        procedural_keywords = ["procedure", "process", "how to", "steps", "install", "maintain"]
        
        if any(kw in query_lower for kw in safety_keywords):
            return "safety"
        elif any(kw in query_lower for kw in technical_keywords):
            return "technical"
        elif any(kw in query_lower for kw in procedural_keywords):
            return "procedural"
        
        return "general"
    
    def _create_safety_prompt(self, query: str, context: str, include_citations: bool) -> str:
        """Create safety-focused prompt"""
        citation_instruction = "\nCite sources using [1], [2], etc." if include_citations else ""
        
        return f"""You are a railway safety expert. Answer the safety-related question based on the provided documentation.

Context:
{context}

Question: {query}

CRITICAL SAFETY INSTRUCTIONS:
- Prioritize safety information above all else
- Include all relevant warnings and cautions
- Reference applicable safety standards (EN50155, EN45545, TSI)
- If safety-critical information is missing, explicitly state this
- Never make assumptions about safety procedures{citation_instruction}

Answer:"""
    
    def _create_technical_prompt(self, query: str, context: str, include_citations: bool) -> str:
        """Create technical prompt"""
        citation_instruction = "\nCite sources using [1], [2], etc." if include_citations else ""
        
        return f"""You are a railway technical expert. Provide a detailed technical answer based on the documentation.

Context:
{context}

Question: {query}

Instructions:
- Provide precise technical specifications
- Include relevant standards and compliance information
- Use correct technical terminology
- Reference specific components and systems{citation_instruction}

Answer:"""
    
    def _create_procedural_prompt(self, query: str, context: str, include_citations: bool) -> str:
        """Create procedural prompt"""
        citation_instruction = "\nCite sources using [1], [2], etc." if include_citations else ""
        
        return f"""You are a railway procedures expert. Provide step-by-step guidance based on the documentation.

Context:
{context}

Question: {query}

Instructions:
- Provide clear, sequential steps
- Include prerequisites and safety checks
- Note any required tools or qualifications
- Highlight critical steps{citation_instruction}

Answer:"""
