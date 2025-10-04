"""Multi-document synthesis for cross-document reasoning."""

from typing import List, Dict, Optional, Set
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class DocumentCluster:
    """Cluster of related documents."""
    
    def __init__(self, cluster_id: str):
        """Initialize document cluster."""
        self.cluster_id = cluster_id
        self.chunks: List[Dict] = []
        self.document_ids: Set[str] = set()
        self.topics: Set[str] = set()
        self.combined_score: float = 0.0
    
    def add_chunk(self, chunk: Dict):
        """Add a chunk to the cluster."""
        self.chunks.append(chunk)
        
        # Track document IDs
        doc_id = chunk.get("document_id") or chunk.get("doc_id")
        if doc_id:
            self.document_ids.add(doc_id)
        
        # Track topics/components
        component = chunk.get("component_type")
        if component:
            self.topics.add(component)
        
        # Update combined score
        score = chunk.get("score", 0.0)
        self.combined_score += score
    
    def get_summary(self) -> Dict:
        """Get cluster summary."""
        return {
            "cluster_id": self.cluster_id,
            "num_chunks": len(self.chunks),
            "num_documents": len(self.document_ids),
            "document_ids": list(self.document_ids),
            "topics": list(self.topics),
            "combined_score": self.combined_score,
            "avg_score": self.combined_score / len(self.chunks) if self.chunks else 0.0
        }


class MultiDocumentSynthesizer:
    """Synthesize information across multiple documents."""
    
    def __init__(
        self,
        similarity_threshold: float = 0.7,
        max_cluster_size: int = 10
    ):
        """
        Initialize multi-document synthesizer.
        
        Args:
            similarity_threshold: Minimum similarity for clustering
            max_cluster_size: Maximum chunks per cluster
        """
        self.similarity_threshold = similarity_threshold
        self.max_cluster_size = max_cluster_size
    
    def synthesize(
        self,
        results: List[Dict],
        query: str,
        synthesis_strategy: str = "cluster"
    ) -> Dict:
        """
        Synthesize information from multiple documents.
        
        Args:
            results: Search results from multiple documents
            query: Original query
            synthesis_strategy: Strategy (cluster, timeline, hierarchy)
            
        Returns:
            Synthesized information
        """
        if synthesis_strategy == "cluster":
            return self._cluster_synthesis(results, query)
        elif synthesis_strategy == "timeline":
            return self._timeline_synthesis(results, query)
        elif synthesis_strategy == "hierarchy":
            return self._hierarchy_synthesis(results, query)
        else:
            raise ValueError(f"Unknown synthesis strategy: {synthesis_strategy}")
    
    def _cluster_synthesis(
        self,
        results: List[Dict],
        query: str
    ) -> Dict:
        """
        Cluster-based synthesis - group related chunks.
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Clustered synthesis
        """
        # Group by document
        doc_groups = defaultdict(list)
        for result in results:
            doc_id = result.get("document_id") or result.get("doc_id", "unknown")
            doc_groups[doc_id].append(result)
        
        # Create clusters
        clusters = []
        for doc_id, chunks in doc_groups.items():
            cluster = DocumentCluster(f"doc_{doc_id}")
            for chunk in chunks[:self.max_cluster_size]:
                cluster.add_chunk(chunk)
            clusters.append(cluster)
        
        # Sort clusters by combined score
        clusters.sort(key=lambda c: c.combined_score, reverse=True)
        
        return {
            "strategy": "cluster",
            "query": query,
            "num_clusters": len(clusters),
            "clusters": [c.get_summary() for c in clusters],
            "total_chunks": sum(len(c.chunks) for c in clusters),
            "total_documents": len(doc_groups)
        }
    
    def _timeline_synthesis(
        self,
        results: List[Dict],
        query: str
    ) -> Dict:
        """
        Timeline-based synthesis - organize by temporal order.
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Timeline synthesis
        """
        # Extract temporal information
        timeline_items = []
        for result in results:
            processed_at = result.get("processed_at")
            if processed_at:
                timeline_items.append({
                    "timestamp": processed_at,
                    "chunk": result,
                    "document_id": result.get("document_id", "unknown")
                })
        
        # Sort by timestamp
        timeline_items.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "strategy": "timeline",
            "query": query,
            "num_items": len(timeline_items),
            "timeline": timeline_items[:20],  # Limit to 20 most recent
            "earliest": timeline_items[-1]["timestamp"] if timeline_items else None,
            "latest": timeline_items[0]["timestamp"] if timeline_items else None
        }
    
    def _hierarchy_synthesis(
        self,
        results: List[Dict],
        query: str
    ) -> Dict:
        """
        Hierarchy-based synthesis - organize by component hierarchy.
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Hierarchical synthesis
        """
        # Group by component type
        hierarchy = defaultdict(list)
        for result in results:
            component = result.get("component_type", "general")
            hierarchy[component].append(result)
        
        # Build hierarchical structure
        hierarchy_tree = {}
        for component, chunks in hierarchy.items():
            hierarchy_tree[component] = {
                "num_chunks": len(chunks),
                "chunks": chunks[:5],  # Top 5 per component
                "avg_score": sum(c.get("score", 0) for c in chunks) / len(chunks)
            }
        
        return {
            "strategy": "hierarchy",
            "query": query,
            "num_components": len(hierarchy),
            "hierarchy": hierarchy_tree,
            "total_chunks": sum(len(chunks) for chunks in hierarchy.values())
        }
    
    def cross_document_comparison(
        self,
        results: List[Dict],
        comparison_field: str = "component_type"
    ) -> Dict:
        """
        Compare information across documents.
        
        Args:
            results: Search results
            comparison_field: Field to compare across documents
            
        Returns:
            Comparison analysis
        """
        # Group by document
        doc_data = defaultdict(lambda: {"chunks": [], "values": set()})
        
        for result in results:
            doc_id = result.get("document_id", "unknown")
            doc_data[doc_id]["chunks"].append(result)
            
            # Extract comparison field value
            value = result.get(comparison_field)
            if value:
                if isinstance(value, list):
                    doc_data[doc_id]["values"].update(value)
                else:
                    doc_data[doc_id]["values"].add(value)
        
        # Find commonalities and differences
        all_values = set()
        for data in doc_data.values():
            all_values.update(data["values"])
        
        comparison = {
            "field": comparison_field,
            "total_documents": len(doc_data),
            "all_values": list(all_values),
            "documents": {}
        }
        
        for doc_id, data in doc_data.items():
            comparison["documents"][doc_id] = {
                "values": list(data["values"]),
                "num_chunks": len(data["chunks"]),
                "unique_values": list(data["values"] - (all_values - data["values"]))
            }
        
        return comparison
    
    def extract_consensus(
        self,
        results: List[Dict],
        field: str = "text"
    ) -> Dict:
        """
        Extract consensus information across documents.
        
        Args:
            results: Search results
            field: Field to analyze for consensus
            
        Returns:
            Consensus analysis
        """
        # Count occurrences of key phrases
        phrase_counts = defaultdict(int)
        doc_sources = defaultdict(set)
        
        for result in results:
            text = result.get(field, "")
            doc_id = result.get("document_id", "unknown")
            
            # Simple phrase extraction (words 3+ chars)
            words = [w.lower() for w in text.split() if len(w) >= 3]
            for word in words:
                phrase_counts[word] += 1
                doc_sources[word].add(doc_id)
        
        # Find consensus phrases (appear in multiple documents)
        consensus_phrases = {
            phrase: {
                "count": count,
                "num_documents": len(doc_sources[phrase]),
                "documents": list(doc_sources[phrase])
            }
            for phrase, count in phrase_counts.items()
            if len(doc_sources[phrase]) >= 2  # At least 2 documents
        }
        
        # Sort by document coverage
        sorted_consensus = sorted(
            consensus_phrases.items(),
            key=lambda x: (x[1]["num_documents"], x[1]["count"]),
            reverse=True
        )
        
        return {
            "total_phrases": len(phrase_counts),
            "consensus_phrases": len(consensus_phrases),
            "top_consensus": dict(sorted_consensus[:20]),  # Top 20
            "coverage": {
                "2_docs": sum(1 for p in consensus_phrases.values() if p["num_documents"] == 2),
                "3_docs": sum(1 for p in consensus_phrases.values() if p["num_documents"] == 3),
                "4+_docs": sum(1 for p in consensus_phrases.values() if p["num_documents"] >= 4)
            }
        }
    
    def generate_summary(
        self,
        synthesis_result: Dict,
        max_length: int = 500
    ) -> str:
        """
        Generate human-readable summary from synthesis.
        
        Args:
            synthesis_result: Result from synthesis method
            max_length: Maximum summary length
            
        Returns:
            Human-readable summary
        """
        strategy = synthesis_result.get("strategy", "unknown")
        query = synthesis_result.get("query", "")
        
        if strategy == "cluster":
            num_clusters = synthesis_result.get("num_clusters", 0)
            total_docs = synthesis_result.get("total_documents", 0)
            
            summary = f"Found information across {total_docs} documents organized into {num_clusters} clusters. "
            
            # Add top cluster info
            clusters = synthesis_result.get("clusters", [])
            if clusters:
                top_cluster = clusters[0]
                summary += f"Primary cluster contains {top_cluster['num_chunks']} chunks "
                summary += f"covering topics: {', '.join(top_cluster['topics'][:3])}."
        
        elif strategy == "timeline":
            num_items = synthesis_result.get("num_items", 0)
            summary = f"Found {num_items} time-ordered results. "
            
            earliest = synthesis_result.get("earliest")
            latest = synthesis_result.get("latest")
            if earliest and latest:
                summary += f"Information spans from {earliest} to {latest}."
        
        elif strategy == "hierarchy":
            num_components = synthesis_result.get("num_components", 0)
            summary = f"Information organized across {num_components} component types. "
            
            hierarchy = synthesis_result.get("hierarchy", {})
            if hierarchy:
                top_components = sorted(
                    hierarchy.items(),
                    key=lambda x: x[1]["avg_score"],
                    reverse=True
                )[:3]
                component_names = [c[0] for c in top_components]
                summary += f"Top components: {', '.join(component_names)}."
        
        else:
            summary = f"Synthesis completed using {strategy} strategy."
        
        return summary[:max_length]
