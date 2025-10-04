#!/usr/bin/env python3
"""
BMS Agent Retrieval Evaluation - Direct Qdrant Access
Evaluates retrieval accuracy directly against Qdrant without requiring API.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict, Counter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DirectRetrievalEvaluator:
    """Evaluates retrieval directly against Qdrant"""
    
    def __init__(self, collection_name: str = "nomad_bms_documents", k: int = 5):
        self.collection_name = collection_name
        self.k = k
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        
        # Initialize embedding model (same as used in processing)
        print("Loading embedding model...")
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        print("✅ Model loaded")
        
    def load_ground_truth(self, filepath: str) -> List[Dict]:
        """Load ground truth dataset from JSONL file"""
        ground_truth = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    ground_truth.append(json.loads(line))
        return ground_truth
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Perform semantic search directly on Qdrant"""
        try:
            # Generate query embedding
            query_embedding = self.model.encode(query).tolist()
            
            # Search Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=("chunk_embedding", query_embedding),
                limit=limit
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "document_name": result.payload.get("document_name", ""),
                    "chunk_id": result.payload.get("chunk_id", ""),
                    "score": result.score,
                    "quality_score": result.payload.get("quality_score", 0.0),
                    "content_preview": result.payload.get("content", "")[:200]
                })
            
            return results
            
        except Exception as e:
            print(f"  ❌ Search error: {e}")
            return []
    
    def evaluate_query(self, query_data: Dict) -> Dict:
        """Evaluate a single query"""
        query = query_data["query"]
        expected_docs = query_data.get("expected_documents", [])
        query_id = query_data.get("query_id", "")
        category = query_data.get("category", "")
        
        # Get search results
        results = self.search(query, limit=self.k)
        
        if not results:
            return {
                "query_id": query_id,
                "category": category,
                "query": query,
                "expected_docs": expected_docs,
                "retrieved_docs": [],
                "top_1": False,
                "top_3": False,
                "top_5": False,
                "mrr": 0.0,
                "avg_score": 0.0,
                "error": "No results returned"
            }
        
        # Extract document names from results
        retrieved_docs = [r["document_name"] for r in results]
        
        # Calculate hits at each position
        hits_at_position = []
        for i, doc in enumerate(retrieved_docs[:self.k], 1):
            # Check if any expected document matches (exact or partial match)
            is_hit = any(
                exp_doc.lower() == doc.lower() or  # Exact match
                exp_doc.lower() in doc.lower() or  # Expected is substring of retrieved
                doc.lower() in exp_doc.lower()     # Retrieved is substring of expected
                for exp_doc in expected_docs
            )
            hits_at_position.append(is_hit)
        
        # Calculate top-k metrics
        top_1 = hits_at_position[0] if len(hits_at_position) >= 1 else False
        top_3 = any(hits_at_position[:3]) if len(hits_at_position) >= 3 else any(hits_at_position)
        top_5 = any(hits_at_position[:5]) if len(hits_at_position) >= 5 else any(hits_at_position)
        
        # Mean Reciprocal Rank (MRR)
        mrr = 0.0
        for i, is_hit in enumerate(hits_at_position, 1):
            if is_hit:
                mrr = 1.0 / i
                break
        
        # Average relevance score
        avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
        
        return {
            "query_id": query_id,
            "category": category,
            "query": query,
            "expected_docs": expected_docs,
            "retrieved_docs": retrieved_docs,
            "retrieved_scores": [r["score"] for r in results],
            "top_1": top_1,
            "top_3": top_3,
            "top_5": top_5,
            "mrr": mrr,
            "avg_score": avg_score,
            "hits_at_position": hits_at_position
        }
    
    def evaluate_dataset(self, ground_truth_path: str) -> Dict:
        """Evaluate entire dataset"""
        print("=" * 80)
        print("BMS AGENT RETRIEVAL EVALUATION")
        print("=" * 80)
        print(f"\nGround truth file: {ground_truth_path}")
        print(f"Collection: {self.collection_name}")
        print(f"Top-K: {self.k}")
        print()
        
        # Load ground truth
        ground_truth = self.load_ground_truth(ground_truth_path)
        print(f"Loaded {len(ground_truth)} queries\n")
        
        # Evaluate each query
        results = []
        category_results = defaultdict(list)
        
        for i, query_data in enumerate(ground_truth, 1):
            query_id = query_data.get("query_id", f"Q{i:03d}")
            category = query_data.get("category", "Unknown")
            query = query_data["query"]
            
            print(f"[{i}/{len(ground_truth)}] {query_id}: {query[:60]}...")
            
            result = self.evaluate_query(query_data)
            results.append(result)
            category_results[category].append(result)
            
            # Show immediate result
            if result["top_5"]:
                print(f"  ✅ Top-5 Hit (position {result['hits_at_position'].index(True) + 1})")
            else:
                print(f"  ❌ Miss - Expected: {', '.join(result['expected_docs'][:2])}")
                print(f"        Got: {result['retrieved_docs'][0] if result['retrieved_docs'] else 'None'}")
        
        # Calculate overall metrics
        print("\n" + "=" * 80)
        print("OVERALL RESULTS")
        print("=" * 80)
        
        total_queries = len(results)
        top_1_accuracy = sum(1 for r in results if r["top_1"]) / total_queries * 100
        top_3_accuracy = sum(1 for r in results if r["top_3"]) / total_queries * 100
        top_5_accuracy = sum(1 for r in results if r["top_5"]) / total_queries * 100
        avg_mrr = sum(r["mrr"] for r in results) / total_queries
        avg_score = sum(r["avg_score"] for r in results) / total_queries
        
        print(f"\nTotal Queries: {total_queries}")
        print(f"Top-1 Accuracy: {top_1_accuracy:.1f}%")
        print(f"Top-3 Accuracy: {top_3_accuracy:.1f}%")
        print(f"Top-5 Accuracy: {top_5_accuracy:.1f}%")
        print(f"Mean Reciprocal Rank: {avg_mrr:.3f}")
        print(f"Average Relevance Score: {avg_score:.3f}")
        
        # Category breakdown
        print("\n" + "=" * 80)
        print("CATEGORY PERFORMANCE")
        print("=" * 80)
        
        for category, cat_results in sorted(category_results.items()):
            cat_total = len(cat_results)
            cat_top5 = sum(1 for r in cat_results if r["top_5"])
            cat_accuracy = (cat_top5 / cat_total * 100) if cat_total > 0 else 0
            print(f"  {category}: {cat_accuracy:.1f}% ({cat_top5}/{cat_total})")
        
        # POC requirement check
        print("\n" + "=" * 80)
        print("POC ACCEPTANCE CRITERIA")
        print("=" * 80)
        
        poc_target = 95.0
        if top_5_accuracy >= poc_target:
            print(f"✅ PASS: Top-5 Accuracy {top_5_accuracy:.1f}% >= {poc_target}%")
        else:
            print(f"❌ FAIL: Top-5 Accuracy {top_5_accuracy:.1f}% < {poc_target}%")
            print(f"   Gap: {poc_target - top_5_accuracy:.1f}% improvement needed")
        
        print("=" * 80)
        
        # Return summary
        return {
            "total_queries": total_queries,
            "top_1_accuracy": top_1_accuracy,
            "top_3_accuracy": top_3_accuracy,
            "top_5_accuracy": top_5_accuracy,
            "mrr": avg_mrr,
            "avg_score": avg_score,
            "category_results": {
                cat: {
                    "total": len(cat_results),
                    "top_5_hits": sum(1 for r in cat_results if r["top_5"]),
                    "accuracy": sum(1 for r in cat_results if r["top_5"]) / len(cat_results) * 100
                }
                for cat, cat_results in category_results.items()
            },
            "detailed_results": results,
            "poc_pass": top_5_accuracy >= poc_target
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate BMS Agent retrieval accuracy")
    parser.add_argument(
        "--ground-truth",
        default="/workspace/bms_data/evaluations/ground_truth.jsonl",
        help="Path to ground truth JSONL file"
    )
    parser.add_argument(
        "--output",
        default="/workspace/bms_data/evaluations/evaluation_results.json",
        help="Path to save results JSON"
    )
    parser.add_argument(
        "--collection",
        default="nomad_bms_documents",
        help="Qdrant collection name"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to evaluate (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    evaluator = DirectRetrievalEvaluator(
        collection_name=args.collection,
        k=args.top_k
    )
    
    results = evaluator.evaluate_dataset(args.ground_truth)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_path}")
    
    # Exit with appropriate code
    sys.exit(0 if results["poc_pass"] else 1)


if __name__ == "__main__":
    main()
