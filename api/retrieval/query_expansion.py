"""Query expansion using LLM for improved recall."""

import asyncio
from typing import List, Dict, Optional
import logging
import httpx
from functools import lru_cache

from api.retrieval.query_classifier import QueryClassifier, QueryType

logger = logging.getLogger(__name__)


class QueryExpander:
    """Expand queries using LLM to generate variations and improve recall."""
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
        max_variations: int = 3,
        timeout: float = 10.0
    ):
        """
        Initialize query expander.
        
        Args:
            ollama_url: Ollama API base URL
            model: LLM model to use for expansion
            max_variations: Maximum number of query variations to generate
            timeout: Request timeout in seconds
        """
        self.ollama_url = ollama_url
        self.model = model
        self.max_variations = max_variations
        self.timeout = timeout
        self.classifier = QueryClassifier()
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def expand_query(
        self,
        query: str,
        use_llm: bool = True
    ) -> List[str]:
        """
        Expand a query into multiple variations.
        
        Args:
            query: Original search query
            use_llm: Whether to use LLM for expansion (fallback to rule-based)
            
        Returns:
            List of query variations including the original
        """
        variations = [query]  # Always include original
        
        # Classify query to determine expansion strategy
        query_type = self.classifier.classify(query)
        
        if use_llm:
            try:
                llm_variations = await self._llm_expand(query, query_type)
                variations.extend(llm_variations)
            except Exception as e:
                logger.warning(f"LLM expansion failed, using rule-based: {e}")
                variations.extend(self._rule_based_expand(query, query_type))
        else:
            variations.extend(self._rule_based_expand(query, query_type))
        
        # Deduplicate and limit
        unique_variations = list(dict.fromkeys(variations))
        return unique_variations[:self.max_variations + 1]
    
    async def _llm_expand(
        self,
        query: str,
        query_type: QueryType
    ) -> List[str]:
        """
        Use LLM to generate query variations.
        
        Args:
            query: Original query
            query_type: Classified query type
            
        Returns:
            List of LLM-generated variations
        """
        # Create domain-specific prompt
        prompt = self._create_expansion_prompt(query, query_type)
        
        try:
            response = await self._client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 200
                    }
                }
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            # Parse variations from response
            variations = self._parse_variations(generated_text)
            return variations[:self.max_variations]
            
        except Exception as e:
            logger.error(f"LLM expansion error: {e}")
            raise
    
    def _create_expansion_prompt(
        self,
        query: str,
        query_type: QueryType
    ) -> str:
        """Create a domain-specific prompt for query expansion."""
        
        context_map = {
            QueryType.TECHNICAL: "technical railway documentation",
            QueryType.PROCEDURAL: "maintenance and operational procedures",
            QueryType.SAFETY: "safety standards and regulations",
            QueryType.GENERAL: "railway documentation"
        }
        
        context = context_map.get(query_type, "railway documentation")
        
        prompt = f"""You are a railway domain expert. Generate {self.max_variations} alternative search queries for finding relevant information in {context}.

Original query: "{query}"

Generate {self.max_variations} variations that:
1. Use different technical terminology or synonyms
2. Rephrase the question in different ways
3. Add relevant context or specifications

Format: Return only the variations, one per line, numbered 1-{self.max_variations}.

Variations:
"""
        return prompt
    
    def _parse_variations(self, generated_text: str) -> List[str]:
        """Parse query variations from LLM response."""
        variations = []
        
        # Split by lines and extract numbered items
        lines = generated_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            # Remove numbering (1., 2., etc.)
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove leading number/bullet and clean
                cleaned = line.lstrip('0123456789.-) ').strip()
                if cleaned and len(cleaned) > 5:  # Minimum length check
                    variations.append(cleaned)
        
        return variations
    
    def _rule_based_expand(
        self,
        query: str,
        query_type: QueryType
    ) -> List[str]:
        """
        Rule-based query expansion as fallback.
        
        Args:
            query: Original query
            query_type: Classified query type
            
        Returns:
            List of rule-based variations
        """
        variations = []
        
        # Extract entities
        entities = self.classifier.extract_entities(query)
        
        # Add entity-enhanced variations
        if entities["train_ids"]:
            train_id = entities["train_ids"][0]
            variations.append(f"{query} {train_id}")
        
        if entities["components"]:
            component = entities["components"][0]
            variations.append(f"{component} {query}")
        
        # Add type-specific variations
        if query_type == QueryType.TECHNICAL:
            variations.extend([
                f"{query} specification",
                f"{query} technical documentation",
                f"{query} parameters"
            ])
        elif query_type == QueryType.PROCEDURAL:
            variations.extend([
                f"{query} procedure",
                f"how to {query}",
                f"{query} maintenance"
            ])
        elif query_type == QueryType.SAFETY:
            variations.extend([
                f"{query} safety requirements",
                f"{query} standards",
                f"{query} compliance"
            ])
        else:
            # For GENERAL queries, add generic variations
            variations.extend([
                f"{query} information",
                f"{query} documentation",
                f"{query} guide"
            ])
        
        return variations[:self.max_variations]
    
    @lru_cache(maxsize=100)
    def get_cached_expansion(self, query: str) -> tuple:
        """
        Cached expansion for common queries (synchronous).
        Note: Returns tuple for hashability in lru_cache.
        """
        # This is a synchronous wrapper for caching
        # Actual async expansion happens in expand_query
        query_type = self.classifier.classify(query)
        variations = self._rule_based_expand(query, query_type)
        return tuple([query] + variations[:self.max_variations])
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


class MultiQueryRetriever:
    """Retrieve using multiple query variations and fuse results."""
    
    def __init__(self, expander: QueryExpander):
        """
        Initialize multi-query retriever.
        
        Args:
            expander: QueryExpander instance
        """
        self.expander = expander
    
    async def retrieve_and_fuse(
        self,
        query: str,
        retrieval_fn,
        k: int = 10,
        use_llm: bool = True
    ) -> List[Dict]:
        """
        Retrieve using multiple queries and fuse results with RRF.
        
        Args:
            query: Original search query
            retrieval_fn: Async function that takes (query, k) and returns results
            k: Number of results to retrieve per query
            use_llm: Whether to use LLM for expansion
            
        Returns:
            Fused and ranked results
        """
        # Expand query
        variations = await self.expander.expand_query(query, use_llm=use_llm)
        
        # Retrieve for each variation
        all_results = []
        for variation in variations:
            try:
                results = await retrieval_fn(variation, k)
                all_results.append(results)
            except Exception as e:
                logger.warning(f"Retrieval failed for variation '{variation}': {e}")
        
        # Fuse results using Reciprocal Rank Fusion (RRF)
        fused = self._reciprocal_rank_fusion(all_results, k=k)
        return fused
    
    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Dict]],
        k: int = 60
    ) -> List[Dict]:
        """
        Fuse multiple result lists using Reciprocal Rank Fusion.
        
        Args:
            result_lists: List of result lists from different queries
            k: RRF constant (default 60)
            
        Returns:
            Fused and re-ranked results
        """
        # Track scores for each unique chunk
        chunk_scores = {}
        chunk_data = {}
        
        for results in result_lists:
            for rank, result in enumerate(results, start=1):
                chunk_id = result.get("id") or result.get("chunk_id")
                if not chunk_id:
                    continue
                
                # RRF score: 1 / (k + rank)
                rrf_score = 1.0 / (k + rank)
                
                if chunk_id in chunk_scores:
                    chunk_scores[chunk_id] += rrf_score
                else:
                    chunk_scores[chunk_id] = rrf_score
                    chunk_data[chunk_id] = result
        
        # Sort by fused score
        sorted_chunks = sorted(
            chunk_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Build final result list
        fused_results = []
        for chunk_id, score in sorted_chunks:
            result = chunk_data[chunk_id].copy()
            result["rrf_score"] = score
            result["fusion_method"] = "reciprocal_rank_fusion"
            fused_results.append(result)
        
        return fused_results
