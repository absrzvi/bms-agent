"""Temporal and version-aware retrieval."""

from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TemporalFilter:
    """Filter for temporal queries."""
    
    def __init__(
        self,
        after: Optional[str] = None,
        before: Optional[str] = None,
        latest_only: bool = False
    ):
        """
        Initialize temporal filter.
        
        Args:
            after: ISO format date string (inclusive)
            before: ISO format date string (inclusive)
            latest_only: Return only latest versions
        """
        self.after = self._parse_date(after) if after else None
        self.before = self._parse_date(before) if before else None
        self.latest_only = latest_only
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse ISO format date string."""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None
    
    def matches(self, timestamp: str) -> bool:
        """
        Check if timestamp matches filter.
        
        Args:
            timestamp: ISO format timestamp
            
        Returns:
            True if matches filter criteria
        """
        if not timestamp:
            return True  # No timestamp, include by default
        
        dt = self._parse_date(timestamp)
        if not dt:
            return True
        
        if self.after and dt < self.after:
            return False
        
        if self.before and dt > self.before:
            return False
        
        return True
    
    def to_qdrant_filter(self) -> Dict:
        """Convert to Qdrant filter format."""
        conditions = []
        
        if self.after:
            conditions.append({
                "key": "processed_at",
                "range": {"gte": self.after.isoformat()}
            })
        
        if self.before:
            conditions.append({
                "key": "processed_at",
                "range": {"lte": self.before.isoformat()}
            })
        
        if not conditions:
            return {}
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {"must": conditions}


class VersionFilter:
    """Filter for version-aware queries."""
    
    def __init__(
        self,
        version: Optional[str] = None,
        latest_only: bool = False,
        compare_versions: bool = False
    ):
        """
        Initialize version filter.
        
        Args:
            version: Specific version to retrieve
            latest_only: Return only latest version
            compare_versions: Enable version comparison
        """
        self.version = version
        self.latest_only = latest_only
        self.compare_versions = compare_versions
    
    def matches(self, doc_version: Optional[str]) -> bool:
        """
        Check if document version matches filter.
        
        Args:
            doc_version: Document version string
            
        Returns:
            True if matches filter criteria
        """
        if not self.version:
            return True
        
        return doc_version == self.version
    
    def to_qdrant_filter(self) -> Dict:
        """Convert to Qdrant filter format."""
        if not self.version:
            return {}
        
        return {
            "key": "version",
            "match": {"value": self.version}
        }


class TemporalRetriever:
    """Retrieval with temporal and version awareness."""
    
    def __init__(self, decay_factor: float = 0.1):
        """
        Initialize temporal retriever.
        
        Args:
            decay_factor: Decay factor for temporal boosting (0.0-1.0)
        """
        self.decay_factor = decay_factor
    
    def apply_temporal_boost(
        self,
        results: List[Dict],
        reference_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Apply temporal boosting to results.
        
        Args:
            results: Search results
            reference_date: Reference date (default: now)
            
        Returns:
            Results with temporal boosting applied
        """
        if not reference_date:
            reference_date = datetime.utcnow()
        
        boosted_results = []
        
        for result in results:
            boosted = result.copy()
            
            # Get document timestamp
            timestamp_str = result.get("processed_at")
            if not timestamp_str:
                boosted_results.append(boosted)
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                boosted_results.append(boosted)
                continue
            
            # Calculate age in days
            # Make reference_date timezone-aware if needed
            if reference_date.tzinfo is None:
                from datetime import timezone
                reference_date = reference_date.replace(tzinfo=timezone.utc)
            
            age_days = (reference_date - timestamp).days
            
            # Apply decay: boost = 1 - (decay_factor * age_days / 365)
            # More recent documents get higher boost
            temporal_boost = max(0.0, 1.0 - (self.decay_factor * age_days / 365.0))
            
            # Apply boost to score
            original_score = result.get("score", 0.0)
            boosted_score = original_score * (1.0 + temporal_boost * 0.2)  # Up to 20% boost
            
            boosted["original_score"] = original_score
            boosted["temporal_boost"] = temporal_boost
            boosted["boosted_score"] = boosted_score
            boosted["score"] = boosted_score
            
            boosted_results.append(boosted)
        
        # Re-sort by boosted score
        boosted_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return boosted_results
    
    def filter_by_date_range(
        self,
        results: List[Dict],
        after: Optional[str] = None,
        before: Optional[str] = None
    ) -> List[Dict]:
        """
        Filter results by date range.
        
        Args:
            results: Search results
            after: Start date (ISO format)
            before: End date (ISO format)
            
        Returns:
            Filtered results
        """
        temporal_filter = TemporalFilter(after=after, before=before)
        
        filtered = []
        for result in results:
            timestamp = result.get("processed_at")
            if temporal_filter.matches(timestamp):
                filtered.append(result)
        
        return filtered
    
    def get_latest_versions(
        self,
        results: List[Dict],
        group_by: str = "document_id"
    ) -> List[Dict]:
        """
        Get only latest versions of documents.
        
        Args:
            results: Search results
            group_by: Field to group by (default: document_id)
            
        Returns:
            Latest versions only
        """
        # Group by document
        doc_groups = {}
        
        for result in results:
            doc_id = result.get(group_by)
            if not doc_id:
                continue
            
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            
            doc_groups[doc_id].append(result)
        
        # Get latest from each group
        latest_results = []
        
        for doc_id, group in doc_groups.items():
            # Sort by timestamp (most recent first)
            sorted_group = sorted(
                group,
                key=lambda x: x.get("processed_at", ""),
                reverse=True
            )
            
            # Take the most recent
            if sorted_group:
                latest = sorted_group[0].copy()
                latest["is_latest"] = True
                latest["version_count"] = len(sorted_group)
                latest_results.append(latest)
        
        # Sort by score
        latest_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return latest_results
    
    def compare_versions(
        self,
        results: List[Dict],
        document_id: str
    ) -> Dict:
        """
        Compare different versions of a document.
        
        Args:
            results: Search results
            document_id: Document to compare versions for
            
        Returns:
            Version comparison
        """
        # Filter for specific document
        doc_versions = [
            r for r in results
            if r.get("document_id") == document_id
        ]
        
        if not doc_versions:
            return {
                "document_id": document_id,
                "versions": [],
                "version_count": 0
            }
        
        # Sort by timestamp
        doc_versions.sort(
            key=lambda x: x.get("processed_at", ""),
            reverse=True
        )
        
        # Build comparison
        comparison = {
            "document_id": document_id,
            "version_count": len(doc_versions),
            "latest_version": doc_versions[0] if doc_versions else None,
            "versions": [
                {
                    "version": v.get("version", "unknown"),
                    "processed_at": v.get("processed_at"),
                    "score": v.get("score", 0),
                    "chunk_id": v.get("id")
                }
                for v in doc_versions
            ]
        }
        
        return comparison


class RecencyScorer:
    """Score documents based on recency."""
    
    def __init__(
        self,
        max_age_days: int = 365,
        min_score: float = 0.5
    ):
        """
        Initialize recency scorer.
        
        Args:
            max_age_days: Maximum age for full score
            min_score: Minimum score for old documents
        """
        self.max_age_days = max_age_days
        self.min_score = min_score
    
    def calculate_recency_score(
        self,
        timestamp: str,
        reference_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate recency score.
        
        Args:
            timestamp: Document timestamp (ISO format)
            reference_date: Reference date (default: now)
            
        Returns:
            Recency score (0.0-1.0)
        """
        if not timestamp:
            return self.min_score
        
        if not reference_date:
            reference_date = datetime.utcnow()
        
        try:
            doc_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return self.min_score
        
        # Calculate age in days
        # Make reference_date timezone-aware if needed
        if reference_date.tzinfo is None:
            from datetime import timezone
            reference_date = reference_date.replace(tzinfo=timezone.utc)
        
        age_days = (reference_date - doc_date).days
        
        if age_days < 0:
            age_days = 0  # Future date
        
        # Linear decay from 1.0 to min_score over max_age_days
        if age_days >= self.max_age_days:
            return self.min_score
        
        score_range = 1.0 - self.min_score
        decay = (age_days / self.max_age_days) * score_range
        
        return 1.0 - decay
    
    def score_results(
        self,
        results: List[Dict],
        weight: float = 0.3
    ) -> List[Dict]:
        """
        Apply recency scoring to results.
        
        Args:
            results: Search results
            weight: Weight for recency score (0.0-1.0)
            
        Returns:
            Results with recency scoring
        """
        scored_results = []
        
        for result in results:
            scored = result.copy()
            
            timestamp = result.get("processed_at")
            recency_score = self.calculate_recency_score(timestamp)
            
            # Combine with original score
            original_score = result.get("score", 0.0)
            combined_score = (
                original_score * (1.0 - weight) +
                recency_score * weight
            )
            
            scored["recency_score"] = recency_score
            scored["original_score"] = original_score
            scored["combined_score"] = combined_score
            scored["score"] = combined_score
            
            scored_results.append(scored)
        
        # Re-sort by combined score
        scored_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return scored_results
