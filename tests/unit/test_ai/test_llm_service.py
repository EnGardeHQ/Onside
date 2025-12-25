import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import os
from datetime import datetime, timedelta

from src.services.ai.llm_service import LLMService, LLMProvider, LLMResponse

class TestLLMService(unittest.TestCase):
    """BDD-style tests for the LLMService with circuit breaker pattern and fallback mechanisms"""
    
    def setUp(self):
        """Setup before each test"""
        self.env_patcher = patch.dict(os.environ, {"OPENAI_API_KEY": "mock-key"})
        self.env_patcher.start()
        self.llm_service = LLMService()
    
    def tearDown(self):
        """Cleanup after each test"""
        self.env_patcher.stop()
    
    def asyncTest(async_test):
        """Decorator to run async tests"""
        def wrapper(*args, **kwargs):
            return asyncio.run(async_test(*args, **kwargs))
        return wrapper
    
    @asyncTest
    async def test_openai_generate_response_success(self):
        """Should successfully generate a response using OpenAI when it works"""
        # Arrange
        prompt = "Test prompt for AI"
        mock_response = "This is a test response from AI"
        
        # Mock the OpenAI API call
        with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_openai:
            mock_openai.return_value = {
                "choices": [{"message": {"content": mock_response}}],
                "usage": {"total_tokens": 10}
            }
            
            # Act
            response = await self.llm_service.generate_response(prompt)
            
            # Assert
            self.assertEqual(response, mock_response)
            self.assertTrue(mock_openai.called)
            # Should have used OpenAI by default
            self.assertEqual(self.llm_service._last_provider_used, LLMProvider.OPENAI)
    
    @asyncTest
    async def test_provider_fallback_mechanism(self):
        """Should fall back to alternative providers when primary provider fails"""
        # Arrange
        prompt = "Test prompt for fallback"
        mock_response = "This is a response from fallback provider"
        
        # Make OpenAI fail but other provider succeed
        with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_openai:
            mock_openai.side_effect = Exception("OpenAI API error")
            
            # Mock the Anthropic provider (assuming it's the fallback)
            with patch.object(llm_service, '_generate_anthropic_response', new_callable=AsyncMock) as mock_anthropic:
                mock_anthropic.return_value = LLMResponse(
                    content=mock_response,
                    tokens_used=15,
                    provider=LLMProvider.ANTHROPIC
                )
                
                # Act
                response = await self.llm_service.generate_response(prompt)
                
                # Assert
                self.assertEqual(response, mock_response)
                self.assertTrue(mock_openai.called)
                self.assertTrue(mock_anthropic.called)
                # Should have used the fallback provider
                self.assertEqual(self.llm_service._last_provider_used, LLMProvider.ANTHROPIC)
    
    @asyncTest
    async def test_circuit_breaker_pattern(self):
        """Should implement circuit breaker pattern to prevent repeated calls to failing providers"""
        # Arrange
        prompt = "Test prompt for circuit breaker"
        mock_response = "This is a response with circuit breaker"
        
        # Set up the failure tracking
        self.llm_service._provider_failures[LLMProvider.OPENAI] = 3
        self.llm_service._provider_failure_times[LLMProvider.OPENAI] = datetime.now()
        
        # Mock alternative provider
        with patch.object(self.llm_service, '_generate_anthropic_response', new_callable=AsyncMock) as mock_anthropic:
            mock_anthropic.return_value = LLMResponse(
                content=mock_response,
                tokens_used=15,
                provider=LLMProvider.ANTHROPIC
            )
            
            # Mock OpenAI to verify it's not called
            with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_openai:
                # Act
                response = await self.llm_service.generate_response(prompt)
                
                # Assert
                self.assertEqual(response, mock_response)
                self.assertFalse(mock_openai.called)
                self.assertTrue(mock_anthropic.called)
                # Should have skipped OpenAI due to circuit breaker
                self.assertEqual(self.llm_service._last_provider_used, LLMProvider.ANTHROPIC)
    
    @asyncTest
    async def test_circuit_breaker_reset(self):
        """Should reset circuit breaker after cooldown period"""
        # Arrange
        prompt = "Test prompt for circuit reset"
        mock_response = "This is a response after circuit reset"
        
        # Set up the failure tracking with an old timestamp
        self.llm_service._provider_failures[LLMProvider.OPENAI] = 3
        self.llm_service._provider_failure_times[LLMProvider.OPENAI] = datetime.now() - timedelta(minutes=20)
        
        # Mock OpenAI to succeed this time
        with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_openai:
            mock_openai.return_value = {
                "choices": [{"message": {"content": mock_response}}],
                "usage": {"total_tokens": 10}
            }
            
            # Act
            response = await self.llm_service.generate_response(prompt)
            
            # Assert
            self.assertEqual(response, mock_response)
            self.assertTrue(mock_openai.called)
            # Should have reset the failure count
            self.assertEqual(self.llm_service._provider_failures[LLMProvider.OPENAI], 0)
            # Should have used OpenAI again after reset
            self.assertEqual(self.llm_service._last_provider_used, LLMProvider.OPENAI)
    
    @asyncTest
    async def test_all_providers_fail(self):
        """Should raise exception when all providers fail"""
        # Arrange
        prompt = "Test prompt that fails everywhere"
        
        # Make all providers fail
        with patch.object(llm_service, '_generate_openai_response', new_callable=AsyncMock) as mock_openai:
            mock_openai.side_effect = Exception("OpenAI API error")
            
            with patch.object(llm_service, '_generate_anthropic_response', new_callable=AsyncMock) as mock_anthropic:
                mock_anthropic.side_effect = Exception("Anthropic API error")
                
                with patch.object(llm_service, '_generate_cohere_response', new_callable=AsyncMock) as mock_cohere:
                    mock_cohere.side_effect = Exception("Cohere API error")
                    
                    # Act / Assert
                    with self.assertRaises(Exception) as excinfo:
                        await self.llm_service.generate_response(prompt)
                    
                    self.assertIn("All LLM providers failed", str(excinfo.exception))
    
    def test_provider_selection_algorithm(self):
        """Should select providers based on history and availability"""
        # Arrange - Set up some failure history
        self.llm_service._provider_failures = {
            LLMProvider.OPENAI: 1,
            LLMProvider.ANTHROPIC: 2,
            LLMProvider.COHERE: 0
        }
        
        # Act - Get next provider after OPENAI
        next_provider = self.llm_service._get_next_provider(LLMProvider.OPENAI)
        
        # Assert - Should choose COHERE as it has fewest failures
        self.assertEqual(next_provider, LLMProvider.COHERE)
        
        # Change failure counts
        self.llm_service._provider_failures[LLMProvider.COHERE] = 3
        
        # Act again
        next_provider = self.llm_service._get_next_provider(LLMProvider.ANTHROPIC)
        
        # Assert - Should now choose OPENAI as it has fewest failures
        self.assertEqual(next_provider, LLMProvider.OPENAI)

    @asyncTest
    async def test_chain_of_thought_reasoning(self):
        """Should support chain-of-thought reasoning when requested"""
        # Arrange
        prompt = "Test prompt for reasoning"
        mock_response = "This is a reasoned response"
        mock_reasoning = "Here is my step-by-step reasoning: 1. First... 2. Then..."
        
        # Mock the OpenAI API call with reasoning
        with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": f"{mock_reasoning}\n\nFinal answer: {mock_response}"
                    }
                }],
                "usage": {"total_tokens": 30}
            }
            
            # Act - Call with reasoning flag
            response = await self.llm_service.generate_response(prompt, with_reasoning=True)
            
            # Assert - Should include both reasoning and response
            self.assertIn(mock_reasoning, response)
            self.assertIn(mock_response, response)
            self.assertTrue(mock_openai.called)
            
            # Verify the prompt was modified to request reasoning
            call_args = mock_openai.call_args[1]
            messages = call_args.get('messages', [])
            system_message = next((m for m in messages if m.get('role') == 'system'), None)
            self.assertIsNotNone(system_message)
            self.assertIn('step-by-step', system_message.get('content', ''))

if __name__ == "__main__":
    unittest.main()
