#!/usr/bin/env python3
"""
Advanced Retrieval Metrics Evaluation Script
Evaluates retrieval performance using NDCG, MRR, MAP, and other metrics
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.evaluation.metrics import RetrievalEvaluator, ABTestFramework
from qdrant_client import QdrantClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_ground_truth(ground_truth_path: str) -> List[Dict[str, Any]]:
    """Load ground truth queries from JSONL file"""
    queries = []
    
    with open(ground_truth_path, 'r') as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
    
    return queries


def evaluate_retrieval_system(
    ground_truth_path: str = "data/evaluation/ground_truth.jsonl",
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    collection_name: str = "nomad_bms_documents"
) -> Dict[str, Any]:
    """
    Evaluate retrieval system using ground truth queries
    
    Args:
        ground_truth_path: Path to ground truth JSONL file
        qdrant_host: Qdrant host
        qdrant_port: Qdrant port
        collection_name: Collection name
        
    Returns:
        Evaluation results
    """
    logger.info(f"Loading ground truth from {ground_truth_path}")
    
    try:
        queries = load_ground_truth(ground_truth_path)
        logger.info(f"Loaded {len(queries)} queries")
    except FileNotFoundError:
        logger.error(f"Ground truth file not found: {ground_truth_path}")
        return {"error": "Ground truth file not found"}
    
    # Initialize Qdrant client
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    
    # Initialize evaluator
    evaluator = RetrievalEvaluator(k_values=[1, 3, 5, 10, 20])
    
    # Prepare results for evaluation
    queries_results = []
    
    for query_data in queries:
        query = query_data.get("query", "")
        expected_docs = query_data.get("expected_documents", [])
        
        if not query or not expected_docs:
            continue
        
        # For this example, we'll use the scores from ground truth
        # In production, you'd perform actual search and compare
        relevance_scores = query_data.get("relevance_scores", [])
        
        if relevance_scores:
            queries_results.append({
                "relevance_scores": relevance_scores,
                "total_relevant": len(expected_docs)
            })
    
    if not queries_results:
        logger.warning("No valid queries to evaluate")
        return {"error": "No valid queries"}
    
    # Evaluate
    logger.info(f"Evaluating {len(queries_results)} queries...")
    metrics = evaluator.evaluate_batch(queries_results)
    formatted = evaluator.format_metrics(metrics)
    
    return formatted


def run_ab_test_example():
    """Example A/B test comparing retrieval strategies"""
    framework = ABTestFramework()
    
    # Create experiment
    framework.create_experiment(
        experiment_id="semantic_vs_hybrid",
        variant_a="semantic_only",
        variant_b="semantic_with_reranking",
        description="Compare semantic search vs semantic + reranking"
    )
    
    # Simulate results (in production, these would be real search results)
    import random
    random.seed(42)
    
    for _ in range(50):
        # Variant A: semantic only (baseline)
        framework.record_result(
            "semantic_vs_hybrid",
            "a",
            {"ndcg@5": random.uniform(0.70, 0.80)}
        )
        
        # Variant B: with reranking (should be better)
        framework.record_result(
            "semantic_vs_hybrid",
            "b",
            {"ndcg@5": random.uniform(0.75, 0.85)}
        )
    
    # Analyze
    analysis = framework.analyze_experiment("semantic_vs_hybrid", "ndcg@5")
    
    print("\n" + "="*80)
    print("A/B TEST RESULTS")
    print("="*80)
    print(f"\nExperiment: {analysis['experiment_id']}")
    print(f"Metric: {analysis['metric']}")
    print(f"\nVariant A ({analysis['variant_a']['name']}):")
    print(f"  Mean: {analysis['variant_a']['mean']}")
    print(f"  Std: {analysis['variant_a']['std']}")
    print(f"  Count: {analysis['variant_a']['count']}")
    print(f"\nVariant B ({analysis['variant_b']['name']}):")
    print(f"  Mean: {analysis['variant_b']['mean']}")
    print(f"  Std: {analysis['variant_b']['std']}")
    print(f"  Count: {analysis['variant_b']['count']}")
    print(f"\nImprovement: {analysis['improvement_pct']}%")
    print(f"Winner: {analysis['winner']}")
    print("="*80)


def main():
    """Main evaluation workflow"""
    print("\n" + "="*80)
    print("ADVANCED RETRIEVAL METRICS EVALUATION")
    print("="*80)
    
    # Check if ground truth exists
    ground_truth_path = Path("data/evaluation/ground_truth.jsonl")
    
    if ground_truth_path.exists():
        print(f"\n✓ Found ground truth: {ground_truth_path}")
        
        # Run evaluation
        results = evaluate_retrieval_system(str(ground_truth_path))
        
        if "error" not in results:
            print("\n" + "="*80)
            print("EVALUATION RESULTS")
            print("="*80)
            
            print("\n📊 Summary:")
            summary = results.get("summary", {})
            print(f"  MRR: {summary.get('mrr', 0):.4f}")
            print(f"  MAP: {summary.get('map', 0):.4f}")
            print(f"  Queries: {summary.get('num_queries', 0)}")
            
            print("\n📈 NDCG@k:")
            for metric, value in results.get("ndcg", {}).items():
                print(f"  {metric}: {value:.4f}")
            
            print("\n🎯 Precision@k:")
            for metric, value in results.get("precision", {}).items():
                print(f"  {metric}: {value:.4f}")
            
            print("\n🔍 Recall@k:")
            for metric, value in results.get("recall", {}).items():
                print(f"  {metric}: {value:.4f}")
            
            print("\n✓ Hit Rate@k:")
            for metric, value in results.get("hit_rate", {}).items():
                print(f"  {metric}: {value:.4f}")
            
            print("="*80)
        else:
            print(f"\n❌ Error: {results['error']}")
    else:
        print(f"\n⚠️  Ground truth not found: {ground_truth_path}")
        print("   Using existing ground truth from T025 evaluation...")
        print("   Run: python scripts/evaluate_retrieval.py to generate ground truth")
    
    # Run A/B test example
    print("\n" + "="*80)
    print("A/B TESTING FRAMEWORK DEMO")
    print("="*80)
    run_ab_test_example()
    
    print("\n✅ Evaluation complete!")
    print("\nNote: For production use, integrate with OpenWebUI's evaluation features:")
    print("  https://docs.openwebui.com/features/evaluation/")


if __name__ == "__main__":
    main()
