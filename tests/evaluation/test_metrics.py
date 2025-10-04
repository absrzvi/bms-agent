"""
Tests for advanced retrieval metrics
"""

import pytest
import numpy as np
from api.evaluation.metrics import (
    MetricsCalculator,
    RetrievalEvaluator,
    RetrievalMetrics,
    ABTestFramework
)


@pytest.fixture
def metrics_calculator():
    """Create metrics calculator instance"""
    return MetricsCalculator()


@pytest.fixture
def retrieval_evaluator():
    """Create retrieval evaluator instance"""
    return RetrievalEvaluator(k_values=[1, 3, 5, 10])


def test_ndcg_perfect_ranking(metrics_calculator):
    """Test NDCG with perfect ranking"""
    relevance_scores = [1.0, 0.9, 0.8, 0.7, 0.6]
    
    ndcg = metrics_calculator.ndcg_at_k(relevance_scores, k=5)
    
    # Perfect ranking should have NDCG = 1.0
    assert abs(ndcg - 1.0) < 0.01


def test_ndcg_worst_ranking(metrics_calculator):
    """Test NDCG with worst ranking"""
    relevance_scores = [0.1, 0.2, 0.3, 0.9, 1.0]
    
    ndcg = metrics_calculator.ndcg_at_k(relevance_scores, k=5)
    
    # Worst ranking should have lower NDCG than perfect
    assert ndcg < 1.0
    # But still > 0 since relevant items are present
    assert ndcg > 0.0


def test_ndcg_empty_scores(metrics_calculator):
    """Test NDCG with empty scores"""
    ndcg = metrics_calculator.ndcg_at_k([], k=5)
    assert ndcg == 0.0


def test_mrr_first_position(metrics_calculator):
    """Test MRR when relevant document is first"""
    relevance_scores = [0.9, 0.3, 0.2]
    
    mrr = metrics_calculator.mrr(relevance_scores, threshold=0.5)
    
    assert mrr == 1.0


def test_mrr_second_position(metrics_calculator):
    """Test MRR when relevant document is second"""
    relevance_scores = [0.3, 0.9, 0.2]
    
    mrr = metrics_calculator.mrr(relevance_scores, threshold=0.5)
    
    assert mrr == 0.5


def test_mrr_no_relevant(metrics_calculator):
    """Test MRR when no relevant documents"""
    relevance_scores = [0.1, 0.2, 0.3]
    
    mrr = metrics_calculator.mrr(relevance_scores, threshold=0.5)
    
    assert mrr == 0.0


def test_average_precision(metrics_calculator):
    """Test Average Precision calculation"""
    relevance_scores = [1.0, 0.0, 1.0, 0.0, 1.0]
    
    ap = metrics_calculator.average_precision(relevance_scores, threshold=0.5)
    
    # AP = (1/1 + 2/3 + 3/5) / 3 = 0.756
    assert abs(ap - 0.756) < 0.01


def test_precision_at_k(metrics_calculator):
    """Test Precision@k"""
    relevance_scores = [1.0, 0.0, 1.0, 0.0, 1.0]
    
    p_at_3 = metrics_calculator.precision_at_k(relevance_scores, k=3, threshold=0.5)
    
    # 2 relevant in top 3
    assert abs(p_at_3 - 0.667) < 0.01


def test_recall_at_k(metrics_calculator):
    """Test Recall@k"""
    relevance_scores = [1.0, 0.0, 1.0, 0.0, 1.0]
    total_relevant = 5
    
    r_at_3 = metrics_calculator.recall_at_k(
        relevance_scores, k=3, total_relevant=total_relevant, threshold=0.5
    )
    
    # 2 out of 5 relevant retrieved
    assert abs(r_at_3 - 0.4) < 0.01


def test_hit_rate_at_k_hit(metrics_calculator):
    """Test Hit Rate@k with hit"""
    relevance_scores = [0.3, 0.9, 0.2]
    
    hr = metrics_calculator.hit_rate_at_k(relevance_scores, k=3, threshold=0.5)
    
    assert hr == 1.0


def test_hit_rate_at_k_miss(metrics_calculator):
    """Test Hit Rate@k with miss"""
    relevance_scores = [0.3, 0.2, 0.1]
    
    hr = metrics_calculator.hit_rate_at_k(relevance_scores, k=3, threshold=0.5)
    
    assert hr == 0.0


def test_evaluate_query(retrieval_evaluator):
    """Test single query evaluation"""
    relevance_scores = [0.9, 0.8, 0.3, 0.7, 0.2]
    
    metrics = retrieval_evaluator.evaluate_query(relevance_scores)
    
    assert "mrr" in metrics
    assert "map" in metrics
    assert "ndcg" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "hit_rate" in metrics
    
    # Check @k metrics
    assert "@1" in metrics["ndcg"]
    assert "@5" in metrics["precision"]


def test_evaluate_batch(retrieval_evaluator):
    """Test batch evaluation"""
    queries_results = [
        {"relevance_scores": [0.9, 0.8, 0.7]},
        {"relevance_scores": [0.6, 0.9, 0.5]},
        {"relevance_scores": [0.8, 0.7, 0.9]}
    ]
    
    metrics = retrieval_evaluator.evaluate_batch(queries_results)
    
    assert isinstance(metrics, RetrievalMetrics)
    assert metrics.num_queries == 3
    assert metrics.mrr > 0.0
    assert metrics.map_score > 0.0
    assert len(metrics.ndcg_at_k) > 0


def test_evaluate_batch_empty(retrieval_evaluator):
    """Test batch evaluation with empty results"""
    metrics = retrieval_evaluator.evaluate_batch([])
    
    assert metrics.num_queries == 0
    assert metrics.mrr == 0.0


def test_format_metrics(retrieval_evaluator):
    """Test metrics formatting"""
    metrics = RetrievalMetrics(
        ndcg_at_k={1: 0.8, 5: 0.75},
        mrr=0.85,
        map_score=0.80,
        precision_at_k={1: 0.9, 5: 0.7},
        recall_at_k={1: 0.2, 5: 0.6},
        hit_rate_at_k={1: 1.0, 5: 1.0},
        num_queries=10
    )
    
    formatted = retrieval_evaluator.format_metrics(metrics)
    
    assert "summary" in formatted
    assert "ndcg" in formatted
    assert "precision" in formatted
    assert formatted["summary"]["mrr"] == 0.85
    assert formatted["summary"]["num_queries"] == 10


def test_ab_test_create_experiment():
    """Test creating A/B test experiment"""
    framework = ABTestFramework()
    
    framework.create_experiment(
        experiment_id="test_exp",
        variant_a="baseline",
        variant_b="new_reranker",
        description="Test reranking improvement"
    )
    
    assert "test_exp" in framework.experiments
    assert framework.experiments["test_exp"]["variant_a"] == "baseline"


def test_ab_test_record_result():
    """Test recording A/B test results"""
    framework = ABTestFramework()
    
    framework.create_experiment("test_exp", "baseline", "treatment")
    
    framework.record_result("test_exp", "a", {"ndcg@5": 0.75})
    framework.record_result("test_exp", "b", {"ndcg@5": 0.82})
    
    assert len(framework.results["test_exp"]) == 2


def test_ab_test_analyze_experiment():
    """Test analyzing A/B test experiment"""
    framework = ABTestFramework()
    
    framework.create_experiment("test_exp", "baseline", "treatment")
    
    # Record multiple results
    for _ in range(10):
        framework.record_result("test_exp", "a", {"ndcg@5": 0.75})
        framework.record_result("test_exp", "b", {"ndcg@5": 0.82})
    
    analysis = framework.analyze_experiment("test_exp", "ndcg@5")
    
    assert "variant_a" in analysis
    assert "variant_b" in analysis
    assert "improvement_pct" in analysis
    assert "winner" in analysis
    assert analysis["winner"] == "b"  # Treatment is better
    assert analysis["improvement_pct"] > 0


def test_ab_test_analyze_nonexistent():
    """Test analyzing non-existent experiment"""
    framework = ABTestFramework()
    
    analysis = framework.analyze_experiment("nonexistent", "ndcg@5")
    
    assert "error" in analysis


def test_retrieval_metrics_dataclass():
    """Test RetrievalMetrics dataclass"""
    metrics = RetrievalMetrics(
        ndcg_at_k={5: 0.8},
        mrr=0.85,
        map_score=0.80,
        precision_at_k={5: 0.7},
        recall_at_k={5: 0.6},
        hit_rate_at_k={5: 1.0},
        num_queries=10
    )
    
    assert metrics.mrr == 0.85
    assert metrics.num_queries == 10
    assert metrics.ndcg_at_k[5] == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
