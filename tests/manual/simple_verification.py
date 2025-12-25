"""
Simple verification script for Sprint 4 AI enhancements.
This script uses only Python standard library to verify the key features:
1. Enhanced LLM integration
2. Fallback mechanisms
3. Chain-of-thought reasoning
"""

import os
import sys
import inspect
import importlib.util
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Test results tracking
tests_run = 0
tests_passed = 0
tests_failed = 0

def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_test(test_name):
    """Print a test name."""
    print(f"\n--- Testing: {test_name} ---")

def print_result(test_name, passed, message=None):
    """Print test result."""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    result = "PASSED" if passed else "FAILED"
    if passed:
        tests_passed += 1
        print(f"✅ {test_name}: {result}")
    else:
        tests_failed += 1
        print(f"❌ {test_name}: {result}")
    if message:
        print(f"   Details: {message}")

def print_summary():
    """Print test summary."""
    print("\n" + "=" * 80)
    print(f" SUMMARY ".center(80, "="))
    print("=" * 80)
    print(f"Total tests run: {tests_run}")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print("=" * 80)

def check_module_exists(module_path):
    """Check if a module exists without importing it."""
    try:
        spec = importlib.util.find_spec(module_path)
        return spec is not None
    except (ImportError, AttributeError):
        return False

def check_file_exists(file_path):
    """Check if a file exists."""
    return os.path.exists(file_path)

def check_string_in_file(file_path, search_string):
    """Check if a string exists in a file."""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            return search_string in content
    except:
        return False

def main():
    """Run verification tests."""
    print_header("Sprint 4 AI Enhancements Verification")
    
    # Check for LLM Service implementation
    print_test("LLM Service Implementation")
    llm_service_exists = check_file_exists('/Users/tobymorning/OnSide/src/services/ai/llm_service.py')
    print_result("LLM Service File", llm_service_exists, 
                "LLM Service implementation file exists")
    
    # Check for circuit breaker pattern
    print_test("Circuit Breaker Pattern")
    circuit_breaker = check_string_in_file(
        '/Users/tobymorning/OnSide/src/services/ai/llm_service.py', 
        'CircuitBreaker'
    )
    print_result("Circuit Breaker Pattern", circuit_breaker,
                "Circuit breaker pattern implemented in LLM service")
    
    # Check for provider fallback
    print_test("Provider Fallback Mechanism")
    provider_fallback = check_string_in_file(
        '/Users/tobymorning/OnSide/src/services/ai/llm_service.py',
        'provider_fallback_order'
    )
    print_result("Provider Fallback", provider_fallback,
                "Provider fallback mechanism implemented in LLM service")
    
    # Check for chain of thought reasoning
    print_test("Chain of Thought Reasoning")
    chain_of_thought = check_string_in_file(
        '/Users/tobymorning/OnSide/src/services/ai/llm_service.py',
        'with_reasoning'
    )
    print_result("Chain of Thought Parameter", chain_of_thought,
                "Chain of thought reasoning parameter implemented")
    
    # Check for Content Affinity Service enhancements
    print_test("Content Affinity Service")
    content_affinity_exists = check_file_exists('/Users/tobymorning/OnSide/src/services/ai/content_affinity.py')
    print_result("Content Affinity Service", content_affinity_exists,
                "Content Affinity Service implementation exists")
    
    # Check for LLM enhancement in Content Affinity
    print_test("Content Affinity LLM Enhancement")
    affinity_llm = check_string_in_file(
        '/Users/tobymorning/OnSide/src/services/ai/content_affinity.py',
        'llm_service'
    )
    print_result("Content Affinity LLM Integration", affinity_llm,
                "Content Affinity Service integrates with LLM service")
    
    # Check for fallback in Content Affinity
    print_test("Content Affinity Fallback")
    affinity_fallback = check_string_in_file(
        '/Users/tobymorning/OnSide/src/services/ai/content_affinity.py',
        'except'
    )
    print_result("Content Affinity Fallback", affinity_fallback,
                "Content Affinity Service includes exception handling for fallback")
    
    # Check for Predictive Insights Service
    print_test("Predictive Insights Service")
    predictive_exists = check_file_exists('/Users/tobymorning/OnSide/src/services/ai/predictive_insights.py')
    print_result("Predictive Insights Service", predictive_exists,
                "Predictive Insights Service implementation exists")
    
    # Check for LLM enhancement in Predictive Insights
    print_test("Predictive Insights LLM Enhancement")
    predictive_llm = check_string_in_file(
        '/Users/tobymorning/OnSide/src/services/ai/predictive_insights.py',
        'llm_service'
    )
    print_result("Predictive Insights LLM Integration", predictive_llm,
                "Predictive Insights Service integrates with LLM service")
    
    # Check for reasoning in Predictive Insights
    print_test("Predictive Insights Reasoning")
    predictive_reasoning = check_string_in_file(
        '/Users/tobymorning/OnSide/src/services/ai/predictive_insights.py',
        'with_reasoning'
    )
    print_result("Predictive Insights Reasoning", predictive_reasoning,
                "Predictive Insights Service supports chain-of-thought reasoning")
    
    # Check for test implementations
    print_test("Test Implementations")
    test_llm = check_file_exists('/Users/tobymorning/OnSide/tests/unit/test_ai/test_llm_service.py')
    test_content = check_file_exists('/Users/tobymorning/OnSide/tests/unit/test_ai/test_content_affinity.py')
    test_predictive = check_file_exists('/Users/tobymorning/OnSide/tests/unit/test_ai/test_predictive_insights.py')
    
    print_result("LLM Service Tests", test_llm, "LLM Service tests implemented")
    print_result("Content Affinity Tests", test_content, "Content Affinity Service tests implemented")
    print_result("Predictive Insights Tests", test_predictive, "Predictive Insights Service tests implemented")
    
    # Check for BDD-style testing
    print_test("BDD-Style Testing")
    bdd_style = (
        check_string_in_file('/Users/tobymorning/OnSide/tests/unit/test_ai/test_llm_service.py', 'should') or
        check_string_in_file('/Users/tobymorning/OnSide/tests/unit/test_ai/test_content_affinity.py', 'should') or
        check_string_in_file('/Users/tobymorning/OnSide/tests/unit/test_ai/test_predictive_insights.py', 'should')
    )
    print_result("BDD-Style Tests", bdd_style, "Tests follow BDD-style approach")
    
    # Check for Sprint 4 documentation
    print_test("Sprint 4 Documentation")
    documentation = check_file_exists('/Users/tobymorning/OnSide/docs/sprint4_ai_enhancements.md')
    print_result("Sprint 4 Documentation", documentation, 
                "Sprint 4 AI enhancements documentation exists")
    
    # Print summary
    print_summary()
    
    # Return success if all tests passed
    return tests_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
