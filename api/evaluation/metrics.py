"""
Advanced Retrieval Metrics
Implements NDCG, MRR, MAP, and other evaluation metrics
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """Container for retrieval evaluation metrics"""
    ndcg_at_k: Dict[int, float]
    mrr: float
    map_score: float
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    hit_rate_at_k: Dict[int, float]
    num_queries: int


class MetricsCalculator:
    """
    Calculate advanced retrieval metrics
    """
    
    @staticmethod
    def ndcg_at_k(relevance_scores: List[float], k: int) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain at k
        
        Args:
            relevance_scores: List of relevance scores (0-1) in ranked order
            k: Cutoff position
            
        Returns:
            NDCG@k score (0-1)
        """
        if not relevance_scores or k <= 0:
            return 0.0
        
        # Truncate to k
        relevance_scores = relevance_scores[:k]
        
        # Calculate DCG
        dcg = relevance_scores[0]
        for i, score in enumerate(relevance_scores[1:], start=2):
            dcg += score / np.log2(i + 1)
        
        # Calculate ideal DCG (IDCG)
        ideal_scores = sorted(relevance_scores, reverse=True)
        idcg = ideal_scores[0]
        for i, score in enumerate(ideal_scores[1:], start=2):
            idcg += score / np.log2(i + 1)
        
        # Normalize
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def mrr(relevance_scores: List[float], threshold: float = 0.5) -> float:
        """
        Calculate Mean Reciprocal Rank
        
        Args:
            relevance_scores: List of relevance scores in ranked order
            threshold: Minimum score to consider relevant
            
        Returns:
            MRR score
        """
        if not relevance_scores:
            return 0.0
        
        for i, score in enumerate(relevance_scores, start=1):
            if score >= threshold:
                return 1.0 / i
        
        return 0.0
    
    @staticmethod
    def average_precision(relevance_scores: List[float], threshold: float = 0.5) -> float:
        """
        Calculate Average Precision
        
        Args:
            relevance_scores: List of relevance scores in ranked order
            threshold: Minimum score to consider relevant
            
        Returns:
            Average Precision score
        """
        if not relevance_scores:
            return 0.0
        
        relevant_count = 0
        precision_sum = 0.0
        
        for i, score in enumerate(relevance_scores, start=1):
            if score >= threshold:
                relevant_count += 1
                precision = relevant_count / i
                precision_sum += precision
        
        if relevant_count == 0:
            return 0.0
        
        return precision_sum / relevant_count
    
    @staticmethod
    def precision_at_k(relevance_scores: List[float], k: int, threshold: float = 0.5) -> float:
        """
        Calculate Precision at k
        
        Args:
            relevance_scores: List of relevance scores in ranked order
            k: Cutoff position
            threshold: Minimum score to consider relevant
            
        Returns:
            Precision@k score
        """
        if not relevance_scores or k <= 0:
            return 0.0
        
        top_k = relevance_scores[:k]
        relevant = sum(1 for score in top_k if score >= threshold)
        
        return relevant / k
    
    @staticmethod
    def recall_at_k(
        relevance_scores: List[float],
        k: int,
        total_relevant: int,
        threshold: float = 0.5
    ) -> float:
        """
        Calculate Recall at k
        
        Args:
            relevance_scores: List of relevance scores in ranked order
            k: Cutoff position
            total_relevant: Total number of relevant documents
            threshold: Minimum score to consider relevant
            
        Returns:
            Recall@k score
        """
        if not relevance_scores or k <= 0 or total_relevant == 0:
            return 0.0
        
        top_k = relevance_scores[:k]
        relevant = sum(1 for score in top_k if score >= threshold)
        
        return relevant / total_relevant
    
    @staticmethod
    def hit_rate_at_k(relevance_scores: List[float], k: int, threshold: float = 0.5) -> float:
        """
        Calculate Hit Rate at k (binary: 1 if any relevant in top-k, 0 otherwise)
        
        Args:
            relevance_scores: List of relevance scores in ranked order
            k: Cutoff position
            threshold: Minimum score to consider relevant
            
        Returns:
            Hit rate (0 or 1)
        """
        if not relevance_scores or k <= 0:
            return 0.0
        
        top_k = relevance_scores[:k]
        return 1.0 if any(score >= threshold for score in top_k) else 0.0


class RetrievalEvaluator:
    """
    Comprehensive retrieval evaluation with multiple metrics
    """
    
    def __init__(
        self,
        k_values: List[int] = [1, 3, 5, 10, 20],
        relevance_threshold: float = 0.5
    ):
        """
        Initialize evaluator
        
        Args:
            k_values: List of k values for @k metrics
            relevance_threshold: Minimum score to consider relevant
        """
        self.k_values = k_values
        self.relevance_threshold = relevance_threshold
        self.calculator = MetricsCalculator()
    
    def evaluate_query(
        self,
        relevance_scores: List[float],
        total_relevant: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single query
        
        Args:
            relevance_scores: List of relevance scores in ranked order
            total_relevant: Total number of relevant documents (for recall)
            
        Returns:
            Dictionary of metrics
        """
        if total_relevant is None:
            total_relevant = sum(1 for s in relevance_scores if s >= self.relevance_threshold)
        
        metrics = {
            "mrr": self.calculator.mrr(relevance_scores, self.relevance_threshold),
            "map": self.calculator.average_precision(relevance_scores, self.relevance_threshold),
            "ndcg": {},
            "precision": {},
            "recall": {},
            "hit_rate": {}
        }
        
        # Calculate @k metrics
        for k in self.k_values:
            metrics["ndcg"][f"@{k}"] = self.calculator.ndcg_at_k(relevance_scores, k)
            metrics["precision"][f"@{k}"] = self.calculator.precision_at_k(
                relevance_scores, k, self.relevance_threshold
            )
            metrics["recall"][f"@{k}"] = self.calculator.recall_at_k(
                relevance_scores, k, total_relevant, self.relevance_threshold
            )
            metrics["hit_rate"][f"@{k}"] = self.calculator.hit_rate_at_k(
                relevance_scores, k, self.relevance_threshold
            )
        
        return metrics
    
    def evaluate_batch(
        self,
        queries_results: List[Dict[str, Any]]
    ) -> RetrievalMetrics:
        """
        Evaluate multiple queries and aggregate metrics
        
        Args:
            queries_results: List of dicts with 'relevance_scores' and optional 'total_relevant'
            
        Returns:
            Aggregated metrics
        """
        if not queries_results:
            return RetrievalMetrics(
                ndcg_at_k={},
                mrr=0.0,
                map_score=0.0,
                precision_at_k={},
                recall_at_k={},
                hit_rate_at_k={},
                num_queries=0
            )
        
        # Aggregate metrics
        mrr_scores = []
        map_scores = []
        ndcg_scores = defaultdict(list)
        precision_scores = defaultdict(list)
        recall_scores = defaultdict(list)
        hit_rate_scores = defaultdict(list)
        
        for query_result in queries_results:
            relevance_scores = query_result.get("relevance_scores", [])
            total_relevant = query_result.get("total_relevant")
            
            metrics = self.evaluate_query(relevance_scores, total_relevant)
            
            mrr_scores.append(metrics["mrr"])
            map_scores.append(metrics["map"])
            
            for k in self.k_values:
                key = f"@{k}"
                ndcg_scores[k].append(metrics["ndcg"][key])
                precision_scores[k].append(metrics["precision"][key])
                recall_scores[k].append(metrics["recall"][key])
                hit_rate_scores[k].append(metrics["hit_rate"][key])
        
        # Calculate means
        return RetrievalMetrics(
            ndcg_at_k={k: np.mean(scores) for k, scores in ndcg_scores.items()},
            mrr=np.mean(mrr_scores),
            map_score=np.mean(map_scores),
            precision_at_k={k: np.mean(scores) for k, scores in precision_scores.items()},
            recall_at_k={k: np.mean(scores) for k, scores in recall_scores.items()},
            hit_rate_at_k={k: np.mean(scores) for k, scores in hit_rate_scores.items()},
            num_queries=len(queries_results)
        )
    
    def format_metrics(self, metrics: RetrievalMetrics) -> Dict[str, Any]:
        """Format metrics for display"""
        return {
            "summary": {
                "mrr": round(metrics.mrr, 4),
                "map": round(metrics.map_score, 4),
                "num_queries": metrics.num_queries
            },
            "ndcg": {f"ndcg@{k}": round(v, 4) for k, v in metrics.ndcg_at_k.items()},
            "precision": {f"p@{k}": round(v, 4) for k, v in metrics.precision_at_k.items()},
            "recall": {f"r@{k}": round(v, 4) for k, v in metrics.recall_at_k.items()},
            "hit_rate": {f"hr@{k}": round(v, 4) for k, v in metrics.hit_rate_at_k.items()}
        }


class ABTestFramework:
    """
    A/B testing framework for retrieval strategies
    """
    
    def __init__(self):
        """Initialize A/B test framework"""
        self.experiments = {}
        self.results = defaultdict(list)
    
    def create_experiment(
        self,
        experiment_id: str,
        variant_a: str,
        variant_b: str,
        description: str = ""
    ):
        """
        Create a new A/B test experiment
        
        Args:
            experiment_id: Unique experiment identifier
            variant_a: Name of variant A (baseline)
            variant_b: Name of variant B (treatment)
            description: Experiment description
        """
        self.experiments[experiment_id] = {
            "variant_a": variant_a,
            "variant_b": variant_b,
            "description": description,
            "created_at": np.datetime64('now')
        }
        
        logger.info(f"Created A/B test: {experiment_id} ({variant_a} vs {variant_b})")
    
    def record_result(
        self,
        experiment_id: str,
        variant: str,
        metrics: Dict[str, float]
    ):
        """
        Record result for a variant
        
        Args:
            experiment_id: Experiment identifier
            variant: Variant name (a or b)
            metrics: Metrics dictionary
        """
        if experiment_id not in self.experiments:
            logger.warning(f"Experiment {experiment_id} not found")
            return
        
        self.results[experiment_id].append({
            "variant": variant,
            "metrics": metrics,
            "timestamp": np.datetime64('now')
        })
    
    def analyze_experiment(
        self,
        experiment_id: str,
        metric_name: str = "ndcg@5"
    ) -> Dict[str, Any]:
        """
        Analyze A/B test results
        
        Args:
            experiment_id: Experiment identifier
            metric_name: Metric to compare
            
        Returns:
            Analysis results
        """
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}
        
        results = self.results.get(experiment_id, [])
        if not results:
            return {"error": "No results recorded"}
        
        # Separate results by variant
        variant_a_scores = []
        variant_b_scores = []
        
        for result in results:
            score = result["metrics"].get(metric_name, 0.0)
            if result["variant"] == "a":
                variant_a_scores.append(score)
            else:
                variant_b_scores.append(score)
        
        if not variant_a_scores or not variant_b_scores:
            return {"error": "Insufficient data for both variants"}
        
        # Calculate statistics
        mean_a = np.mean(variant_a_scores)
        mean_b = np.mean(variant_b_scores)
        std_a = np.std(variant_a_scores)
        std_b = np.std(variant_b_scores)
        
        # Calculate improvement
        improvement = ((mean_b - mean_a) / mean_a * 100) if mean_a > 0 else 0.0
        
        return {
            "experiment_id": experiment_id,
            "metric": metric_name,
            "variant_a": {
                "name": self.experiments[experiment_id]["variant_a"],
                "mean": round(mean_a, 4),
                "std": round(std_a, 4),
                "count": len(variant_a_scores)
            },
            "variant_b": {
                "name": self.experiments[experiment_id]["variant_b"],
                "mean": round(mean_b, 4),
                "std": round(std_b, 4),
                "count": len(variant_b_scores)
            },
            "improvement_pct": round(improvement, 2),
            "winner": "b" if mean_b > mean_a else "a"
        }
