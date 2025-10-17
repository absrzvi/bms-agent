#!/usr/bin/env python3
"""
Test script for BMS Search OpenWebUI Tool
Tests all functions without requiring OpenWebUI installation
"""

import sys
import json
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bms_search import Tools

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_api_status():
    """Test 1: Check BMS API status"""
    print_section("TEST 1: API Health Check")
    
    tool = Tools()
    result = tool.get_api_status()
    print(result)
    
    if "✅" in result:
        print("\n✅ PASS: API is healthy")
        return True
    else:
        print("\n❌ FAIL: API is not responding")
        return False

def test_semantic_search():
    """Test 2: Semantic search"""
    print_section("TEST 2: Semantic Search")
    
    tool = Tools()
    query = "business continuity planning"
    print(f"Query: '{query}'")
    print(f"Limit: 3\n")
    
    result = tool.search_semantic(query, limit=3)
    print(result)
    
    if "Found" in result and "results" in result.lower():
        print("\n✅ PASS: Semantic search returned results")
        return True
    elif "No results" in result:
        print("\n⚠️  WARN: Search completed but no results found")
        return True
    else:
        print("\n❌ FAIL: Semantic search failed")
        return False

def test_hybrid_search():
    """Test 3: Hybrid search"""
    print_section("TEST 3: Hybrid Search")
    
    tool = Tools()
    query = "railway safety procedures"
    print(f"Query: '{query}'")
    print(f"Limit: 3\n")
    
    result = tool.search_hybrid(query, limit=3)
    print(result)
    
    if "Found" in result or "No results" in result:
        print("\n✅ PASS: Hybrid search completed")
        return True
    else:
        print("\n❌ FAIL: Hybrid search failed")
        return False

def test_document_type_filter():
    """Test 4: Document type filtering"""
    print_section("TEST 4: Document Type Filter")
    
    tool = Tools()
    query = "maintenance"
    doc_type = "pdf"
    print(f"Query: '{query}'")
    print(f"Document Type: {doc_type}")
    print(f"Limit: 2\n")
    
    result = tool.search_by_document_type(query, doc_type, limit=2)
    print(result)
    
    if "Found" in result or "No results" in result:
        print("\n✅ PASS: Filtered search completed")
        return True
    else:
        print("\n❌ FAIL: Filtered search failed")
        return False

def test_custom_filters():
    """Test 5: Custom filters"""
    print_section("TEST 5: Custom Filters (Quality Threshold)")
    
    tool = Tools()
    query = "safety"
    filters = {"quality_score_min": 0.7}
    print(f"Query: '{query}'")
    print(f"Filters: {filters}")
    print(f"Limit: 3\n")
    
    result = tool.search_documents(query, limit=3, filters=filters)
    print(result)
    
    if "Found" in result or "No results" in result:
        print("\n✅ PASS: Custom filter search completed")
        return True
    else:
        print("\n❌ FAIL: Custom filter search failed")
        return False

def test_configuration():
    """Test 6: Configuration valves"""
    print_section("TEST 6: Configuration Valves")
    
    tool = Tools()
    
    print("Current Configuration:")
    print(f"  BMS_API_URL: {tool.valves.BMS_API_URL}")
    print(f"  DEFAULT_LIMIT: {tool.valves.DEFAULT_LIMIT}")
    print(f"  SEARCH_TYPE: {tool.valves.SEARCH_TYPE}")
    print(f"  HYBRID_WEIGHT_DENSE: {tool.valves.HYBRID_WEIGHT_DENSE}")
    print(f"  HYBRID_WEIGHT_SPARSE: {tool.valves.HYBRID_WEIGHT_SPARSE}")
    print(f"  QUALITY_THRESHOLD: {tool.valves.QUALITY_THRESHOLD}")
    print(f"  TIMEOUT: {tool.valves.TIMEOUT}")
    
    # Test configuration change
    print("\nTesting configuration change...")
    tool.valves.DEFAULT_LIMIT = 10
    print(f"  Changed DEFAULT_LIMIT to: {tool.valves.DEFAULT_LIMIT}")
    
    print("\n✅ PASS: Configuration accessible and modifiable")
    return True

def test_error_handling():
    """Test 7: Error handling"""
    print_section("TEST 7: Error Handling")
    
    tool = Tools()
    
    # Test invalid search type
    print("Test 7a: Invalid search type")
    result = tool.search_documents("test", search_type="invalid")
    print(result)
    
    if "Error" in result or "Invalid" in result:
        print("✅ PASS: Invalid search type handled\n")
    else:
        print("❌ FAIL: Invalid search type not handled\n")
    
    # Test with wrong API URL
    print("Test 7b: Wrong API URL")
    tool.valves.BMS_API_URL = "http://localhost:9999"
    result = tool.search_semantic("test", limit=1)
    print(result)
    
    if "Cannot connect" in result or "Error" in result:
        print("✅ PASS: Connection error handled")
        return True
    else:
        print("❌ FAIL: Connection error not handled")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("  BMS SEARCH TOOL - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    tests = [
        ("API Health Check", test_api_status),
        ("Semantic Search", test_semantic_search),
        ("Hybrid Search", test_hybrid_search),
        ("Document Type Filter", test_document_type_filter),
        ("Custom Filters", test_custom_filters),
        ("Configuration", test_configuration),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*70}")
    print(f"  Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 All tests passed! Tool is ready for OpenWebUI integration.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
