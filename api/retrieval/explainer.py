"""Retrieval explainability for understanding search results."""

from typing import List, Dict, Optional
import re
import logging

from api.models.explanation import (
    RetrievalExplanation, QueryExplanation, ScoreBreakdown,
    MatchedKeyword, MatchedEntity
)
from api.retrieval.query_classifier import QueryClassifier

logger = logging.getLogger(__name__)


class RetrievalExplainer:
    """Explain retrieval results with score breakdowns and match details."""
    
    def __init__(self):
        """Initialize retrieval explainer."""
        self.classifier = QueryClassifier()
    
    def explain_query(
        self,
        query: str,
        query_type: Optional[str] = None,
        expansions: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        strategy: Optional[str] = None
    ) -> QueryExplanation:
        """
        Explain query processing.
        
        Args:
            query: Original query text
            query_type: Classified query type
            expansions: Query expansions
            filters: Applied filters
            strategy: Search strategy
            
        Returns:
            QueryExplanation
        """
        # Classify if not provided
        if query_type is None:
            query_type = self.classifier.classify(query).value
        
        # Extract entities
        entities_dict = self.classifier.extract_entities(query)
        extracted_entities = []
        
        for train_id in entities_dict.get("train_ids", []):
            extracted_entities.append(
                MatchedEntity(
                    entity=train_id,
                    entity_type="train_id",
                    confidence=1.0
                )
            )
        
        for component in entities_dict.get("components", []):
            extracted_entities.append(
                MatchedEntity(
                    entity=component,
                    entity_type="component",
                    confidence=0.9
                )
            )
        
        for standard in entities_dict.get("standards", []):
            extracted_entities.append(
                MatchedEntity(
                    entity=standard,
                    entity_type="standard",
                    confidence=1.0
                )
            )
        
        return QueryExplanation(
            original_query=query,
            query_type=query_type,
            extracted_entities=extracted_entities,
            query_expansion=expansions,
            filters_applied=filters,
            search_strategy=strategy
        )
    
    def explain_result(
        self,
        result: Dict,
        query: str,
        rank: int,
        debug: bool = False
    ) -> RetrievalExplanation:
        """
        Explain a single search result.
        
        Args:
            result: Search result dictionary
            query: Original query
            rank: Result rank
            debug: Include debug information
            
        Returns:
            RetrievalExplanation
        """
        # Build score breakdown
        score_breakdown = self._build_score_breakdown(result)
        
        # Find matched keywords
        chunk_text = result.get("text", "")
        matched_keywords = self._find_matched_keywords(query, chunk_text)
        
        # Find matched entities
        matched_entities = self._find_matched_entities(result, query)
        
        # Generate similarity explanation
        similarity_explanation = self._generate_similarity_explanation(
            score_breakdown,
            matched_keywords,
            matched_entities
        )
        
        # Extract metadata matches
        metadata_matches = self._extract_metadata_matches(result, query)
        
        # Build debug info if requested
        debug_info = None
        if debug:
            debug_info = {
                "raw_result": result,
                "query_tokens": query.lower().split(),
                "chunk_length": len(chunk_text),
                "metadata": result.get("metadata", {})
            }
        
        return RetrievalExplanation(
            chunk_id=result.get("id", "unknown"),
            rank=rank,
            score_breakdown=score_breakdown,
            matched_keywords=matched_keywords,
            matched_entities=matched_entities,
            similarity_explanation=similarity_explanation,
            metadata_matches=metadata_matches,
            debug_info=debug_info
        )
    
    def _build_score_breakdown(self, result: Dict) -> ScoreBreakdown:
        """Build score breakdown from result."""
        return ScoreBreakdown(
            semantic_score=result.get("semantic_score"),
            keyword_score=result.get("keyword_score"),
            metadata_boost=result.get("metadata_boost"),
            rerank_score=result.get("rerank_score"),
            quality_boost=result.get("quality_boost"),
            final_score=result.get("score", result.get("fused_score", 0.0)),
            fusion_method=result.get("fusion_strategy") or result.get("fusion_method")
        )
    
    def _find_matched_keywords(
        self,
        query: str,
        chunk_text: str
    ) -> List[MatchedKeyword]:
        """Find keywords from query that appear in chunk."""
        matched = []
        query_words = set(query.lower().split())
        chunk_lower = chunk_text.lower()
        
        for word in query_words:
            if len(word) < 3:  # Skip very short words
                continue
            
            # Find all occurrences
            pattern = r'\b' + re.escape(word) + r'\b'
            matches = list(re.finditer(pattern, chunk_lower, re.IGNORECASE))
            
            if matches:
                positions = [m.start() for m in matches]
                matched.append(
                    MatchedKeyword(
                        keyword=word,
                        frequency=len(matches),
                        positions=positions
                    )
                )
        
        # Sort by frequency
        matched.sort(key=lambda x: x.frequency, reverse=True)
        return matched
    
    def _find_matched_entities(
        self,
        result: Dict,
        query: str
    ) -> List[MatchedEntity]:
        """Find entities that match between query and result."""
        matched = []
        
        # Extract entities from query
        query_entities = self.classifier.extract_entities(query)
        
        # Check result metadata for matches
        result_train_id = result.get("train_id")
        if result_train_id and result_train_id in query_entities.get("train_ids", []):
            matched.append(
                MatchedEntity(
                    entity=result_train_id,
                    entity_type="train_id",
                    confidence=1.0
                )
            )
        
        result_component = result.get("component_type")
        if result_component and result_component in query_entities.get("components", []):
            matched.append(
                MatchedEntity(
                    entity=result_component,
                    entity_type="component",
                    confidence=0.9
                )
            )
        
        result_standards = result.get("standards", [])
        if isinstance(result_standards, list):
            for standard in result_standards:
                if standard in query_entities.get("standards", []):
                    matched.append(
                        MatchedEntity(
                            entity=standard,
                            entity_type="standard",
                            confidence=1.0
                        )
                    )
        
        return matched
    
    def _generate_similarity_explanation(
        self,
        score_breakdown: ScoreBreakdown,
        matched_keywords: List[MatchedKeyword],
        matched_entities: List[MatchedEntity]
    ) -> str:
        """Generate human-readable similarity explanation."""
        parts = []
        
        # Explain score components
        if score_breakdown.semantic_score is not None:
            parts.append(
                f"Semantic similarity: {score_breakdown.semantic_score:.3f}"
            )
        
        if score_breakdown.keyword_score is not None:
            parts.append(
                f"Keyword match: {score_breakdown.keyword_score:.3f}"
            )
        
        # Explain keyword matches
        if matched_keywords:
            top_keywords = [kw.keyword for kw in matched_keywords[:3]]
            parts.append(
                f"Matched keywords: {', '.join(top_keywords)}"
            )
        
        # Explain entity matches
        if matched_entities:
            entity_types = set(e.entity_type for e in matched_entities)
            parts.append(
                f"Matched entities: {', '.join(entity_types)}"
            )
        
        # Explain boosts
        if score_breakdown.metadata_boost:
            parts.append(
                f"Metadata boost: +{score_breakdown.metadata_boost:.3f}"
            )
        
        if score_breakdown.quality_boost:
            parts.append(
                f"Quality boost: +{score_breakdown.quality_boost:.3f}"
            )
        
        # Explain fusion
        if score_breakdown.fusion_method:
            parts.append(
                f"Fusion: {score_breakdown.fusion_method}"
            )
        
        return " | ".join(parts) if parts else "No explanation available"
    
    def _extract_metadata_matches(
        self,
        result: Dict,
        query: str
    ) -> Dict[str, any]:
        """Extract metadata fields that match query context."""
        matches = {}
        
        # Check document type
        if "document_type" in result:
            matches["document_type"] = result["document_type"]
        
        # Check quality score
        if "quality_score" in result:
            matches["quality_score"] = result["quality_score"]
        
        # Check safety critical flag
        if "safety_critical" in result:
            matches["safety_critical"] = result["safety_critical"]
        
        # Check train ID
        if "train_id" in result:
            matches["train_id"] = result["train_id"]
        
        # Check component type
        if "component_type" in result:
            matches["component_type"] = result["component_type"]
        
        # Check standards
        if "standards" in result and result["standards"]:
            matches["standards"] = result["standards"]
        
        return matches
    
    def explain_results(
        self,
        results: List[Dict],
        query: str,
        debug: bool = False
    ) -> List[RetrievalExplanation]:
        """
        Explain multiple search results.
        
        Args:
            results: List of search results
            query: Original query
            debug: Include debug information
            
        Returns:
            List of RetrievalExplanations
        """
        explanations = []
        
        for rank, result in enumerate(results, start=1):
            explanation = self.explain_result(result, query, rank, debug)
            explanations.append(explanation)
        
        return explanations
    
    def compare_results(
        self,
        result1: Dict,
        result2: Dict,
        query: str
    ) -> Dict[str, any]:
        """
        Compare two results to explain ranking.
        
        Args:
            result1: First result (higher ranked)
            result2: Second result (lower ranked)
            query: Original query
            
        Returns:
            Comparison explanation
        """
        exp1 = self.explain_result(result1, query, 1)
        exp2 = self.explain_result(result2, query, 2)
        
        comparison = {
            "higher_ranked": {
                "chunk_id": exp1.chunk_id,
                "score": exp1.score_breakdown.final_score,
                "advantages": []
            },
            "lower_ranked": {
                "chunk_id": exp2.chunk_id,
                "score": exp2.score_breakdown.final_score,
                "advantages": []
            },
            "score_difference": exp1.score_breakdown.final_score - exp2.score_breakdown.final_score
        }
        
        # Compare score components
        if exp1.score_breakdown.semantic_score and exp2.score_breakdown.semantic_score:
            if exp1.score_breakdown.semantic_score > exp2.score_breakdown.semantic_score:
                comparison["higher_ranked"]["advantages"].append(
                    f"Higher semantic similarity ({exp1.score_breakdown.semantic_score:.3f} vs {exp2.score_breakdown.semantic_score:.3f})"
                )
        
        # Compare keyword matches
        if len(exp1.matched_keywords) > len(exp2.matched_keywords):
            comparison["higher_ranked"]["advantages"].append(
                f"More keyword matches ({len(exp1.matched_keywords)} vs {len(exp2.matched_keywords)})"
            )
        elif len(exp2.matched_keywords) > len(exp1.matched_keywords):
            comparison["lower_ranked"]["advantages"].append(
                f"More keyword matches ({len(exp2.matched_keywords)} vs {len(exp1.matched_keywords)})"
            )
        
        # Compare entity matches
        if len(exp1.matched_entities) > len(exp2.matched_entities):
            comparison["higher_ranked"]["advantages"].append(
                f"More entity matches ({len(exp1.matched_entities)} vs {len(exp2.matched_entities)})"
            )
        
        return comparison
