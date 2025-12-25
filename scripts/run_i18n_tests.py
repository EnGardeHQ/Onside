#!/usr/bin/env python
"""
Test runner for i18n integration tests.

This script runs the internationalization integration tests,
ensuring all dependencies are properly loaded.

Following Semantic Seed coding standards with proper error handling.
"""
import os
import sys
import asyncio
import unittest
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test module
from tests.integration.services.ai.test_i18n_ai_integration import TestI18nAIIntegration


class SimpleTestRunner:
    """Simple test runner for i18n integration tests."""
    
    def run_tests(self):
        """Run the i18n integration tests."""
        # Create a test suite
        suite = unittest.TestSuite()
        
        # Add the tests from TestI18nAIIntegration
        test_methods = [
            'test_i18n_prompt_translation',
            'test_i18n_result_translation',
            'test_chain_of_thought_i18n'
        ]
        
        for test_method in test_methods:
            suite.addTest(TestI18nAIIntegration(test_method))
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Return the result
        return result.wasSuccessful()


if __name__ == "__main__":
    # Run the tests
    runner = SimpleTestRunner()
    success = runner.run_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
