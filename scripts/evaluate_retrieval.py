#!/usr/bin/env python3
"""
Retrieval Accuracy & Quality Evaluation Script
Computes top-5 accuracy, RAGAS metrics, and validates against ≥95% threshold
"""

import json
import sys
import requests
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# Configuration
API_URL = "http://localhost:8000"
GROUND_TRUTH_FILE = "data/evaluation/ground_truth_50.jsonl"  # Use 50-query dataset
MIN_ACCURACY_THRESHOLD = 0.95
TOP_K = 5

def load_ground_truth(filepath: str) -> List[Dict[str, Any]]:
    """Load ground truth queries and expected documents"""
    ground_truth = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                ground_truth.append(json.loads(line))
    return ground_truth

def search_semantic(query: str, limit: int = TOP_K) -> List[Dict[str, Any]]:
    """Perform semantic search via API"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/search/semantic",
            json={"query": query, "limit": limit},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"❌ Search failed for query '{query}': {e}")
        return []

def extract_document_names(results: List[Dict[str, Any]]) -> List[str]:
    """Extract document names from search results"""
    doc_names = []
    for result in results:
        # Try direct field first (current API format)
        doc_name = result.get("document_name", "")
        # Fallback to payload if nested (alternative format)
        if not doc_name:
            payload = result.get("payload", {})
            doc_name = payload.get("document_name", "")
        if doc_name:
            doc_names.append(doc_name)
    return doc_names

def calculate_top_k_accuracy(ground_truth: List[Dict], results_map: Dict) -> float:
    """Calculate top-K accuracy"""
    correct = 0
    total = len(ground_truth)
    
    for gt in ground_truth:
        query = gt["query"]
        expected_docs = set(gt["expected_documents"])
        retrieved_docs = set(results_map.get(query, []))
        
        # Check if any expected document is in top-K results
        if expected_docs & retrieved_docs:
            correct += 1
    
    return correct / total if total > 0 else 0.0

def calculate_precision_recall(ground_truth: List[Dict], results_map: Dict) -> Dict[str, float]:
    """Calculate precision and recall metrics"""
    precisions = []
    recalls = []
    
    for gt in ground_truth:
        query = gt["query"]
        expected_docs = set(gt["expected_documents"])
        retrieved_docs = set(results_map.get(query, []))
        
        if retrieved_docs:
            precision = len(expected_docs & retrieved_docs) / len(retrieved_docs)
            precisions.append(precision)
        
        if expected_docs:
            recall = len(expected_docs & retrieved_docs) / len(expected_docs)
            recalls.append(recall)
    
    avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    
    return {
        "precision": avg_precision,
        "recall": avg_recall,
        "f1_score": 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0.0
    }

def calculate_mrr(ground_truth: List[Dict], results_map: Dict) -> float:
    """Calculate Mean Reciprocal Rank"""
    reciprocal_ranks = []
    
    for gt in ground_truth:
        query = gt["query"]
        expected_docs = set(gt["expected_documents"])
        retrieved_docs = results_map.get(query, [])
        
        # Find rank of first relevant document
        for rank, doc in enumerate(retrieved_docs, 1):
            if doc in expected_docs:
                reciprocal_ranks.append(1.0 / rank)
                break
        else:
            reciprocal_ranks.append(0.0)
    
    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

def evaluate_retrieval():
    """Main evaluation function"""
    print("🔍 BMS Agent Retrieval Evaluation")
    print("=" * 60)
    
    # Load ground truth
    print(f"\n📋 Loading ground truth from: {GROUND_TRUTH_FILE}")
    try:
        ground_truth = load_ground_truth(GROUND_TRUTH_FILE)
        print(f"✅ Loaded {len(ground_truth)} test queries")
    except Exception as e:
        print(f"❌ Failed to load ground truth: {e}")
        return 1
    
    # Check API health
    print(f"\n🔗 Checking API health at: {API_URL}")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        print("✅ API is healthy")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        print("💡 Make sure the API is running: uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return 1
    
    # Perform searches
    print(f"\n🔎 Performing semantic searches (top-{TOP_K})...")
    results_map = {}
    failed_queries = []
    
    for i, gt in enumerate(ground_truth, 1):
        query = gt["query"]
        print(f"  [{i}/{len(ground_truth)}] {query[:60]}...")
        
        results = search_semantic(query, TOP_K)
        if results:
            doc_names = extract_document_names(results)
            results_map[query] = doc_names
            print(f"      ✅ Retrieved {len(doc_names)} documents")
        else:
            failed_queries.append(query)
            results_map[query] = []
            print(f"      ⚠️  No results")
    
    if failed_queries:
        print(f"\n⚠️  {len(failed_queries)} queries returned no results")
    
    # Calculate metrics
    print(f"\n📊 Calculating metrics...")
    
    top_k_accuracy = calculate_top_k_accuracy(ground_truth, results_map)
    precision_recall = calculate_precision_recall(ground_truth, results_map)
    mrr = calculate_mrr(ground_truth, results_map)
    
    # Display results
    print("\n" + "=" * 60)
    print("📈 EVALUATION RESULTS")
    print("=" * 60)
    print(f"\n🎯 Top-{TOP_K} Accuracy:  {top_k_accuracy:.2%}")
    print(f"   Threshold:         {MIN_ACCURACY_THRESHOLD:.2%}")
    print(f"   Status:            {'✅ PASS' if top_k_accuracy >= MIN_ACCURACY_THRESHOLD else '❌ FAIL'}")
    
    print(f"\n📊 Precision & Recall:")
    print(f"   Precision:         {precision_recall['precision']:.2%}")
    print(f"   Recall:            {precision_recall['recall']:.2%}")
    print(f"   F1 Score:          {precision_recall['f1_score']:.2%}")
    
    print(f"\n🏆 Mean Reciprocal Rank: {mrr:.4f}")
    
    print(f"\n📋 Query Statistics:")
    print(f"   Total queries:     {len(ground_truth)}")
    print(f"   Successful:        {len(ground_truth) - len(failed_queries)}")
    print(f"   Failed:            {len(failed_queries)}")
    
    # Save results
    results_file = "reports/retrieval_evaluation.json"
    Path("reports").mkdir(exist_ok=True)
    
    results_data = {
        "top_k_accuracy": top_k_accuracy,
        "threshold": MIN_ACCURACY_THRESHOLD,
        "passed": top_k_accuracy >= MIN_ACCURACY_THRESHOLD,
        "precision": precision_recall['precision'],
        "recall": precision_recall['recall'],
        "f1_score": precision_recall['f1_score'],
        "mrr": mrr,
        "total_queries": len(ground_truth),
        "failed_queries": len(failed_queries),
        "top_k": TOP_K
    }
    
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Final verdict
    print("\n" + "=" * 60)
    if top_k_accuracy >= MIN_ACCURACY_THRESHOLD:
        print("✅ EVALUATION PASSED - Retrieval accuracy meets threshold!")
        print("=" * 60)
        return 0
    else:
        print("❌ EVALUATION FAILED - Retrieval accuracy below threshold")
        print(f"   Required: {MIN_ACCURACY_THRESHOLD:.2%}")
        print(f"   Achieved: {top_k_accuracy:.2%}")
        print(f"   Gap:      {(MIN_ACCURACY_THRESHOLD - top_k_accuracy):.2%}")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(evaluate_retrieval())
