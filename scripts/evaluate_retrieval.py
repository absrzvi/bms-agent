#!/usr/bin/env python3
"""
BMS Agent Retrieval Accuracy Evaluation Script

Evaluates retrieval accuracy against ground truth dataset.
Computes top-k accuracy, MRR, and quality metrics.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import requests
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class RetrievalEvaluator:
    """Evaluates retrieval system performance"""
    
    def __init__(self, api_url: str = "http://localhost:8000", k: int = 5):
        self.api_url = api_url
        self.k = k
        self.results = []
        
    def load_ground_truth(self, filepath: str) -> List[Dict]:
        """Load ground truth dataset from JSONL file"""
        ground_truth = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    ground_truth.append(json.loads(line))
        return ground_truth
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Perform semantic search via API"""
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/search/semantic",
                json={"query": query, "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            print(f"  ❌ Search error for '{query}': {e}")
            return []
    
    def evaluate_query(self, query: str, expected_docs: List[str]) -> Dict:
        """Evaluate a single query"""
        # Get search results
        results = self.search(query, limit=self.k)
        
        # Extract document names from results
        retrieved_docs = [r.get("document_name", "") for r in results]
        
        # Calculate metrics
        hits_at_k = []
        for i, doc in enumerate(retrieved_docs[:self.k], 1):
            # Check if any expected document matches (partial match for flexibility)
            is_hit = any(exp_doc.lower() in doc.lower() or doc.lower() in exp_doc.lower() 
                        for exp_doc in expected_docs)
            hits_at_k.append(is_hit)
        
        # Top-k accuracy: at least one expected doc in top-k
        top_k_hit = any(hits_at_k)
        
        # Mean Reciprocal Rank (MRR)
        mrr = 0.0
        for i, is_hit in enumerate(hits_at_k, 1):
            if is_hit:
                mrr = 1.0 / i
                break
        
        # Average quality score of top-k results
        quality_scores = [r.get("metadata", {}).get("quality_score", 0.0) for r in results]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Average relevance score
        relevance_scores = [r.get("score", 0.0) for r in results]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        return {
            "query": query,
            "expected": expected_docs,
            "retrieved": retrieved_docs,
            "top_k_hit": top_k_hit,
            "mrr": mrr,
            "avg_quality": avg_quality,
            "avg_relevance": avg_relevance,
            "num_results": len(results)
        }
    
    def evaluate_dataset(self, ground_truth: List[Dict]) -> Dict:
        """Evaluate entire dataset"""
        print(f"\n🔍 Evaluating {len(ground_truth)} queries...")
        print(f"   Top-k: {self.k}")
        print(f"   API: {self.api_url}")
        print()
        
        results = []
        category_stats = defaultdict(lambda: {"total": 0, "hits": 0})
        difficulty_stats = defaultdict(lambda: {"total": 0, "hits": 0})
        
        for i, item in enumerate(ground_truth, 1):
            query = item["query"]
            expected = item["expected_documents"]
            category = item.get("category", "unknown")
            difficulty = item.get("difficulty", "medium")
            
            print(f"[{i}/{len(ground_truth)}] Testing: {query[:50]}...")
            
            result = self.evaluate_query(query, expected)
            result["category"] = category
            result["difficulty"] = difficulty
            results.append(result)
            
            # Update category stats
            category_stats[category]["total"] += 1
            if result["top_k_hit"]:
                category_stats[category]["hits"] += 1
            
            # Update difficulty stats
            difficulty_stats[difficulty]["total"] += 1
            if result["top_k_hit"]:
                difficulty_stats[difficulty]["hits"] += 1
            
            # Show result
            status = "✅" if result["top_k_hit"] else "❌"
            print(f"   {status} MRR: {result['mrr']:.3f} | Quality: {result['avg_quality']:.2f} | Relevance: {result['avg_relevance']:.3f}")
        
        # Calculate overall metrics
        top_k_accuracy = sum(r["top_k_hit"] for r in results) / len(results)
        avg_mrr = sum(r["mrr"] for r in results) / len(results)
        avg_quality = sum(r["avg_quality"] for r in results) / len(results)
        avg_relevance = sum(r["avg_relevance"] for r in results) / len(results)
        
        return {
            "overall": {
                "top_k_accuracy": top_k_accuracy,
                "avg_mrr": avg_mrr,
                "avg_quality": avg_quality,
                "avg_relevance": avg_relevance,
                "total_queries": len(results),
                "successful_queries": sum(r["top_k_hit"] for r in results)
            },
            "by_category": dict(category_stats),
            "by_difficulty": dict(difficulty_stats),
            "detailed_results": results
        }
    
    def print_report(self, evaluation: Dict):
        """Print evaluation report"""
        overall = evaluation["overall"]
        
        print("\n" + "=" * 70)
        print("📊 RETRIEVAL EVALUATION REPORT")
        print("=" * 70)
        print()
        
        # Overall metrics
        print("🎯 Overall Performance:")
        print(f"   Top-{self.k} Accuracy: {overall['top_k_accuracy']:.1%}")
        print(f"   Mean Reciprocal Rank: {overall['avg_mrr']:.3f}")
        print(f"   Average Quality Score: {overall['avg_quality']:.3f}")
        print(f"   Average Relevance: {overall['avg_relevance']:.3f}")
        print(f"   Successful Queries: {overall['successful_queries']}/{overall['total_queries']}")
        print()
        
        # Pass/Fail
        threshold = 0.95
        passed = overall['top_k_accuracy'] >= threshold
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"🎓 Accuracy Threshold: {threshold:.1%}")
        print(f"   Status: {status}")
        print()
        
        # By category
        print("📂 Performance by Category:")
        for category, stats in sorted(evaluation["by_category"].items()):
            accuracy = stats["hits"] / stats["total"] if stats["total"] > 0 else 0
            print(f"   {category:20s}: {accuracy:.1%} ({stats['hits']}/{stats['total']})")
        print()
        
        # By difficulty
        print("⚡ Performance by Difficulty:")
        for difficulty, stats in sorted(evaluation["by_difficulty"].items()):
            accuracy = stats["hits"] / stats["total"] if stats["total"] > 0 else 0
            print(f"   {difficulty:10s}: {accuracy:.1%} ({stats['hits']}/{stats['total']})")
        print()
        
        # Failed queries
        failed = [r for r in evaluation["detailed_results"] if not r["top_k_hit"]]
        if failed:
            print(f"❌ Failed Queries ({len(failed)}):")
            for r in failed:
                print(f"   - {r['query']}")
                print(f"     Expected: {r['expected'][0] if r['expected'] else 'N/A'}")
                print(f"     Got: {r['retrieved'][0] if r['retrieved'] else 'No results'}")
        
        print("=" * 70)
        
        return passed
    
    def save_results(self, evaluation: Dict, filepath: str):
        """Save evaluation results to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(evaluation, f, indent=2)
        print(f"\n💾 Results saved to: {filepath}")


def main():
    """Main evaluation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate BMS Agent retrieval accuracy")
    parser.add_argument("--ground-truth", default="data/evaluation/ground_truth.jsonl",
                       help="Path to ground truth JSONL file")
    parser.add_argument("--api-url", default="http://localhost:8000",
                       help="BMS API URL")
    parser.add_argument("--k", type=int, default=5,
                       help="Top-k for accuracy calculation")
    parser.add_argument("--output", default="data/evaluation/results.json",
                       help="Output file for results")
    
    args = parser.parse_args()
    
    # Check if API is available
    try:
        response = requests.get(f"{args.api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not responding at {args.api_url}")
            print("   Please ensure BMS API is running")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Load ground truth
    evaluator = RetrievalEvaluator(api_url=args.api_url, k=args.k)
    
    try:
        ground_truth = evaluator.load_ground_truth(args.ground_truth)
        print(f"✅ Loaded {len(ground_truth)} test queries from {args.ground_truth}")
    except Exception as e:
        print(f"❌ Error loading ground truth: {e}")
        sys.exit(1)
    
    # Run evaluation
    evaluation = evaluator.evaluate_dataset(ground_truth)
    
    # Print report
    passed = evaluator.print_report(evaluation)
    
    # Save results
    evaluator.save_results(evaluation, args.output)
    
    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
