#!/usr/bin/env python3
"""
OpenWebUI Tool Integration Test - T023
Tests all 11 working functions in bms_search.py tool (including NEW search_smart)

Task: T023 - OpenWebUI Integration Testing
Status: Ready for execution
Date: 2025-10-04
"""

import sys
import json
import time
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from bms_search import Tools

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_function(tool, func_name, *args, **kwargs):
    """Test a single tool function"""
    print(f"Testing: {func_name}()")
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")
    
    try:
        start_time = time.time()
        func = getattr(tool, func_name)
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Check result
        if result and not result.startswith("❌"):
            print(f"✅ PASS ({elapsed:.2f}s)")
            print(f"Result preview: {result[:200]}...\n")
            return True
        else:
            print(f"❌ FAIL ({elapsed:.2f}s)")
            print(f"Error: {result}\n")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}\n")
        return False

def main():
    """Run comprehensive integration tests"""
    
    print_section("OpenWebUI Tool Integration Test - T023")
    print("Testing 11 fully working functions from bms_search.py")
    print("Including NEW search_smart() with metadata-boosted reranking (+12% POC improvement)")
    print("Expected: All tests pass with valid responses\n")
    
    # Initialize tool
    print("Initializing BMS Search Tool...")
    tool = Tools()
    
    # Configure for local testing
    tool.valves.BMS_API_URL = "http://localhost:8000"
    tool.valves.DEFAULT_LIMIT = 5
    tool.valves.TIMEOUT = 30
    
    print(f"✅ Tool initialized")
    print(f"   API URL: {tool.valves.BMS_API_URL}")
    print(f"   Default Limit: {tool.valves.DEFAULT_LIMIT}")
    print(f"   Timeout: {tool.valves.TIMEOUT}s\n")
    
    # Track results
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # ==================== UTILITY TESTS ====================
    print_section("1. UTILITY FUNCTIONS (1 test)")
    
    tests = [
        ("get_api_status", [], {})
    ]
    
    for func_name, args, kwargs in tests:
        results["total"] += 1
        if test_function(tool, func_name, *args, **kwargs):
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # ==================== CORE SEARCH TESTS ====================
    print_section("2. CORE SEARCH FUNCTIONS (4 tests)")
    
    tests = [
        ("search_semantic", ["railway safety procedures"], {"limit": 3}),
        ("search_hybrid", ["BMS-ENGI-FOR-003"], {"limit": 3}),
        ("search_documents", ["employee onboarding process"], {"limit": 3, "search_type": "hybrid"}),
        ("compare_search_types", ["material management"], {"limit": 2})
    ]
    
    for func_name, args, kwargs in tests:
        results["total"] += 1
        if test_function(tool, func_name, *args, **kwargs):
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)  # Rate limiting
    
    # ==================== SMART SEARCH TESTS (POC +12% IMPROVEMENT) ====================
    print_section("3. SMART SEARCH (METADATA-BOOSTED) - 1 test")
    
    tests = [
        ("search_smart", ["employee onboarding form"], {"limit": 3})
    ]
    
    for func_name, args, kwargs in tests:
        results["total"] += 1
        if test_function(tool, func_name, *args, **kwargs):
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)  # Rate limiting
    
    # ==================== FILTERED SEARCH TESTS ====================
    print_section("4. FILTERED SEARCH FUNCTIONS (6 tests)")
    
    tests = [
        ("search_by_document_type", ["quality forms", "xlsx"], {"limit": 3}),
        ("search_by_fleet_type", ["maintenance procedures", "Cityjet"], {"limit": 3}),
        ("search_by_standard", ["fire protection requirements", "EN45545"], {"limit": 3}),
        ("search_by_department", ["employee forms", "HUMR"], {"limit": 3}),
        ("search_with_context", ["complex procurement process"], {"limit": 3}),
        ("search_high_quality", ["safety procedures"], {"min_quality": 0.80, "limit": 3})
    ]
    
    for func_name, args, kwargs in tests:
        results["total"] += 1
        if test_function(tool, func_name, *args, **kwargs):
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)  # Rate limiting
    
    # ==================== SUMMARY ====================
    print_section("TEST SUMMARY")
    
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    
    pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\nPass Rate: {pass_rate:.1f}%")
    
    if pass_rate == 100:
        print("\n🎉 SUCCESS: All tests passed!")
        print("OpenWebUI tool is ready for POC signoff (T023)")
        return 0
    elif pass_rate >= 80:
        print("\n⚠️  PARTIAL SUCCESS: Most tests passed")
        print("Review failures and retry failed tests")
        return 1
    else:
        print("\n❌ FAILURE: Too many tests failed")
        print("Check API connectivity and configuration")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
