#!/usr/bin/env python3
"""Test newly ingested documents - Anlage 3 Excel and Anlage 3F DOCX"""

import sys
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

# Test queries designed to find content from the newly ingested documents
test_queries = [
    {
        "name": "Excel - Change Management Requirements",
        "query": "documentation change management must be updated annually",
        "expected_doc": "Anlage 3 - Anforderungen",
        "expected_content": ["updated", "year", "revised", "changes"],
        "min_score": 0.4
    },
    {
        "name": "DOCX - Soft Start Circuit",
        "query": "soft start circuit inrush current limiter vehicle fuses",
        "expected_doc": "Anlage 3F - Case Study",
        "expected_content": ["soft start", "inrush", "current", "fuses"],
        "min_score": 0.4
    },
    {
        "name": "DOCX - Power Supply Specifications",
        "query": "power supply compliant specifications",
        "expected_doc": "Anlage 3F",
        "expected_content": ["power supply", "compliant"],
        "min_score": 0.3
    },
    {
        "name": "Excel - Annual Document Updates",
        "query": "documents must be updated once a year",
        "expected_doc": "Anlage 3",
        "expected_content": ["year", "updated", "revised"],
        "min_score": 0.4
    },
    {
        "name": "General - Anlage 3 Requirements",
        "query": "Anlage 3 requirements documentation",
        "expected_doc": "Anlage",
        "expected_content": ["Anlage"],
        "min_score": 0.3
    },
    {
        "name": "General - Case Study Technical Content",
        "query": "Anlage 3F case study technical specifications",
        "expected_doc": "Anlage 3F",
        "expected_content": ["Anlage"],
        "min_score": 0.3
    },
    {
        "name": "Technical - Fuse Compatibility",
        "query": "vehicle fuse compatibility 10A specifications",
        "expected_doc": "Case Study",
        "expected_content": ["fuse", "10A"],
        "min_score": 0.3
    }
]

def test_semantic_search(query_info):
    """Test semantic search endpoint"""
    try:
        response = requests.post(
            f"{API_BASE}/search/semantic",
            json={
                "query": query_info['query'],
                "limit": 5,
                "min_score": query_info['min_score']
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def test_hybrid_search(query_info):
    """Test hybrid search endpoint"""
    try:
        response = requests.post(
            f"{API_BASE}/search/hybrid",
            json={
                "query": query_info['query'],
                "limit": 5,
                "vector_weight": 0.6,
                "keyword_weight": 0.4
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def check_result_quality(result, query_info):
    """Check if result matches expected criteria"""
    doc_name = result.get('metadata', {}).get('document_name', '')
    if not doc_name:
        doc_name = result.get('document_name', '')

    text = result.get('text', '') or result.get('content', '')
    score = result.get('score', 0)

    # Check document name match
    doc_match = query_info['expected_doc'].lower() in doc_name.lower()

    # Check content keywords
    text_lower = text.lower()
    content_matches = sum(1 for keyword in query_info['expected_content']
                         if keyword.lower() in text_lower)
    content_match = content_matches > 0

    return {
        'doc_match': doc_match,
        'content_match': content_match,
        'score': score,
        'doc_name': doc_name,
        'text': text[:200],
        'content_matches': content_matches
    }

def main():
    print("\n" + "=" * 80)
    print("TESTING NEWLY INGESTED DOCUMENTS")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base: {API_BASE}")
    print(f"Total Tests: {len(test_queries)}")

    # Check API health
    print("\n" + "-" * 80)
    print("Checking API Health...")
    print("-" * 80)
    try:
        health = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=5)
        if health.status_code == 200:
            print("✅ API is healthy and responding")
        else:
            print(f"⚠️  API returned status {health.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure the API is running: uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return

    # Run tests
    results_summary = {
        'total': len(test_queries),
        'passed': 0,
        'failed': 0,
        'errors': 0
    }

    for i, test in enumerate(test_queries, 1):
        print("\n" + "=" * 80)
        print(f"TEST {i}/{len(test_queries)}: {test['name']}")
        print("=" * 80)
        print(f"Query: {test['query']}")
        print(f"Expected Document: {test['expected_doc']}")
        print(f"Min Score: {test['min_score']}")

        # Test semantic search
        print("\n📊 Semantic Search Results:")
        print("-" * 80)

        results, error = test_semantic_search(test)

        if error:
            print(f"❌ ERROR: {error}")
            results_summary['errors'] += 1
            continue

        search_results = results.get('results', [])

        if not search_results:
            print("⚠️  No results returned")
            results_summary['failed'] += 1
            continue

        print(f"Found {len(search_results)} results\n")

        test_passed = False
        for j, result in enumerate(search_results[:3], 1):
            quality = check_result_quality(result, test)

            # Status indicator
            if quality['doc_match'] and quality['content_match']:
                status = "✅ MATCH"
                test_passed = True
            elif quality['doc_match']:
                status = "⚠️  DOC MATCH"
            elif quality['content_match']:
                status = "⚠️  CONTENT MATCH"
            else:
                status = "❌ NO MATCH"

            print(f"{status} Result {j}:")
            print(f"   Document: {quality['doc_name']}")
            print(f"   Score: {quality['score']:.4f}")
            print(f"   Content Matches: {quality['content_matches']}/{len(test['expected_content'])}")
            print(f"   Text: {quality['text']}...")
            print()

        if test_passed:
            results_summary['passed'] += 1
        else:
            results_summary['failed'] += 1

    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results_summary['total']}")
    print(f"✅ Passed: {results_summary['passed']}")
    print(f"❌ Failed: {results_summary['failed']}")
    print(f"⚠️  Errors: {results_summary['errors']}")
    print(f"Success Rate: {results_summary['passed']/results_summary['total']*100:.1f}%")

    if results_summary['passed'] == results_summary['total']:
        print("\n🎉 ALL TESTS PASSED! Documents are properly indexed and searchable.")
    elif results_summary['passed'] > 0:
        print("\n⚠️  SOME TESTS PASSED. Documents are indexed but retrieval needs tuning.")
    else:
        print("\n❌ NO TESTS PASSED. Check document indexing and search configuration.")

    print("=" * 80)

if __name__ == '__main__':
    main()
