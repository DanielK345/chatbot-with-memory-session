"""
Master test runner that executes all three test suites.
Runs with random query generation for comprehensive coverage.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_session_summarization import test_session_summarization
from tests.test_ambiguous_query_detection import test_ambiguous_query_detection
from tests.test_query_refinement import test_query_refinement


async def run_all_tests():
    """Run all test suites."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "AUTOMATED TEST SUITE - Chat Assistant Pipeline".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {
        "session_summarization": False,
        "ambiguous_detection": False,
        "query_refinement": False,
    }
    
    # Test 1: Session Summarization
    print("\n\n[1/3] Running Session Summarization Test...")
    try:
        results["session_summarization"] = await test_session_summarization()
    except Exception as e:
        print(f"❌ Session Summarization test crashed: {e}")
        results["session_summarization"] = False
    
    # Test 2: Ambiguous Query Detection
    print("\n\n[2/3] Running Ambiguous Query Detection Test...")
    try:
        results["ambiguous_detection"] = await test_ambiguous_query_detection()
    except Exception as e:
        print(f"❌ Ambiguous Query Detection test crashed: {e}")
        results["ambiguous_detection"] = False
    
    # Test 3: Query Refinement
    print("\n\n[3/3] Running Query Refinement Test...")
    try:
        results["query_refinement"] = await test_query_refinement()
    except Exception as e:
        print(f"❌ Query Refinement test crashed: {e}")
        results["query_refinement"] = False
    
    # Summary
    print("\n\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "TEST SUMMARY".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    print("\nResults:")
    print(f"  1. Session Summarization:       {'✅ PASSED' if results['session_summarization'] else '❌ FAILED'}")
    print(f"  2. Ambiguous Query Detection:   {'✅ PASSED' if results['ambiguous_detection'] else '❌ FAILED'}")
    print(f"  3. Query Refinement:            {'✅ PASSED' if results['query_refinement'] else '❌ FAILED'}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n  Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed or inconclusive")
        return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
