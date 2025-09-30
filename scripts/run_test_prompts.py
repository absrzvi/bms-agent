#!/usr/bin/env python3
"""
Automated Test Script for BMS Search Tool
Runs all test prompts from TEST_PROMPTS.md and validates results
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

try:
    from bms_search import Tools
    TOOL_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing BMS search tool: {e}")
    TOOL_AVAILABLE = False
    sys.exit(1)

# Test categories with prompts
TEST_SUITES = {
    "🔍 Semantic Search": [
        "What is business continuity?",
        "How do we handle emergencies?",
        "What are our safety procedures?",
        "Explain the onboarding process",
    ],
    
    "⚡ Hybrid Search": [
        "Find BMS-BCON-FOR-001",
        "Show me documents with 'material management' in them",
        "Search for 'SharePoint permission' documents",
        "Locate 'commissioning report' templates",
    ],
    
    "📊 Multi-Format": [
        "Find all PDF documents about safety",
        "Show me Excel templates",
        "What PowerPoint presentations do we have?",
    ],
    
    "🎯 Scenario-Based": [
        "A new employee is starting Monday, what documents do they need?",
        "We have an IT incident, what procedures should we follow?",
        "How do we handle a business continuity event?",
    ],
    
    "📋 Domain-Specific": [
        "What is the employee onboarding process?",
        "Show me IT service management procedures",
        "Find engineering commissioning templates",
        "What's the ERP supplier approval process?",
        "Show me risk assessment templates",
    ],
}

def run_test_suite(tool: Tools, suite_name: str, prompts: List[str]) -> Dict:
    """Run a test suite and collect results"""
    print(f"\n{'='*70}")
    print(f"{suite_name}")
    print(f"{'='*70}\n")
    
    results = {
        "suite_name": suite_name,
        "total": len(prompts),
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] Testing: {prompt[:60]}...")
        
        try:
            start_time = time.time()
            
            # Determine search type based on prompt
            if any(keyword in prompt.lower() for keyword in ['find bms-', 'show me documents with', 'locate']):
                result = tool.search_hybrid(prompt, limit=3)
                search_type = "hybrid"
            else:
                result = tool.search_semantic(prompt, limit=3)
                search_type = "semantic"
            
            elapsed = time.time() - start_time
            
            # Check if results were found
            has_results = "No results found" not in result
            
            test_result = {
                "prompt": prompt,
                "search_type": search_type,
                "has_results": has_results,
                "elapsed_time": elapsed,
                "result_preview": result[:200] if has_results else "No results"
            }
            
            if has_results:
                print(f"   ✅ PASS - Found results in {elapsed:.2f}s")
                results["passed"] += 1
            else:
                print(f"   ⚠️  WARN - No results in {elapsed:.2f}s")
                results["failed"] += 1
            
            results["tests"].append(test_result)
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)[:100]}")
            results["failed"] += 1
            results["tests"].append({
                "prompt": prompt,
                "error": str(e)
            })
    
    return results

def print_summary(all_results: List[Dict]):
    """Print test summary"""
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}\n")
    
    total_tests = sum(r["total"] for r in all_results)
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    
    print(f"Total Tests:   {total_tests}")
    print(f"✅ Passed:     {total_passed} ({total_passed/total_tests*100:.1f}%)")
    print(f"❌ Failed:     {total_failed} ({total_failed/total_tests*100:.1f}%)")
    print()
    
    print("Results by Suite:")
    for result in all_results:
        suite_name = result["suite_name"]
        passed = result["passed"]
        total = result["total"]
        pct = (passed / total * 100) if total > 0 else 0
        status = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"
        print(f"  {status} {suite_name}: {passed}/{total} ({pct:.1f}%)")
    
    print(f"\n{'='*70}")
    
    # Overall status
    overall_pct = (total_passed / total_tests * 100) if total_tests > 0 else 0
    if overall_pct >= 90:
        print("✅ EXCELLENT - System performing very well!")
    elif overall_pct >= 75:
        print("✅ GOOD - System performing well with minor issues")
    elif overall_pct >= 50:
        print("⚠️  FAIR - System needs optimization")
    else:
        print("❌ POOR - System needs significant improvement")
    
    print(f"{'='*70}\n")

def save_results(all_results: List[Dict], output_file: str):
    """Save results to JSON file"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "suites": all_results,
            "summary": {
                "total_tests": sum(r["total"] for r in all_results),
                "total_passed": sum(r["passed"] for r in all_results),
                "total_failed": sum(r["failed"] for r in all_results),
            }
        }, f, indent=2)
    
    print(f"💾 Results saved to: {output_path}")

def main():
    """Main test runner"""
    print("🧪 BMS Agent Automated Test Suite")
    print("="*70)
    
    if not TOOL_AVAILABLE:
        print("❌ BMS search tool not available")
        return 1
    
    # Initialize tool
    print("\n🔧 Initializing BMS search tool...")
    tool = Tools()
    print(f"   API URL: {tool.valves.BMS_API_URL}")
    print(f"   Default Limit: {tool.valves.DEFAULT_LIMIT}")
    print(f"   Search Type: {tool.valves.SEARCH_TYPE}")
    
    # Check API health
    print("\n🏥 Checking API health...")
    try:
        status = tool.get_api_status()
        if "healthy" in status.lower() or "connected" in status.lower():
            print("   ✅ API is healthy")
        else:
            print(f"   ⚠️  API status: {status[:100]}")
    except Exception as e:
        print(f"   ❌ API health check failed: {e}")
        return 1
    
    # Run all test suites
    all_results = []
    for suite_name, prompts in TEST_SUITES.items():
        results = run_test_suite(tool, suite_name, prompts)
        all_results.append(results)
    
    # Print summary
    print_summary(all_results)
    
    # Save results
    output_file = Path(__file__).parent.parent / "reports" / "test_results.json"
    save_results(all_results, str(output_file))
    
    # Return exit code based on pass rate
    total_tests = sum(r["total"] for r in all_results)
    total_passed = sum(r["passed"] for r in all_results)
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    return 0 if pass_rate >= 75 else 1

if __name__ == "__main__":
    sys.exit(main())
