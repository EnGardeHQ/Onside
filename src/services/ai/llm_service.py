"""
LLM Service with Fallback Mechanisms.

This module provides a resilient interface for LLM interactions with built-in
fallback mechanisms to handle API outages or failures. It supports multiple
LLM providers and implements circuit breaker patterns to prevent cascading failures.
"""
import os
import json
import time
import random
import asyncio
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
import httpx
import backoff
import openai
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.services.ai.chain_of_thought import ChainOfThoughtReasoning

logger = logging.getLogger(__name__)

# Config classes for LLM providers
class LLMProviderConfig(BaseModel):
    """Base configuration for an LLM provider"""
    name: str
    api_key_env_var: str
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    is_enabled: bool = True
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key from environment variable"""
        return os.environ.get(self.api_key_env_var)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    HF_INFERENCE = "huggingface"
    FALLBACK = "fallback"  # Local fallback model or rule-based system


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Not allowing calls
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.
    
    If a service fails multiple times, the circuit opens and
    prevents further calls for a cooling-off period.
    """
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 2
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing service again
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    def record_success(self):
        """Record a successful call and reset circuit if needed"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            
        self.failure_count = 0
        self.half_open_calls = 0
    
    def record_failure(self):
        """Record a failed call and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit opened due to {self.failure_count} consecutive failures")
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed based on circuit state"""
        current_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has elapsed
            if self.last_failure_time and (current_time - self.last_failure_time) > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("Circuit moved to half-open state")
                return True
            return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return True


class LLMService:
    """
    Resilient LLM service with fallback mechanisms.
    
    Features:
    - Multiple LLM provider support
    - Automatic fallback between providers
    - Circuit breaker pattern to prevent cascading failures
    - Retry mechanisms with exponential backoff
    - Chain-of-thought reasoning integration
    - Comprehensive logging
    """
    
    def __init__(self):
        """Initialize the LLM service with providers and circuit breakers"""
        # Configure LLM providers
        self.providers = {
            LLMProvider.OPENAI: LLMProviderConfig(
                name="OpenAI",
                api_key_env_var="OPENAI_API_KEY",
            ),
            LLMProvider.ANTHROPIC: LLMProviderConfig(
                name="Anthropic",
                api_key_env_var="ANTHROPIC_API_KEY",
            ),
            LLMProvider.AZURE_OPENAI: LLMProviderConfig(
                name="Azure OpenAI",
                api_key_env_var="AZURE_OPENAI_API_KEY",
                base_url=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            ),
            LLMProvider.HF_INFERENCE: LLMProviderConfig(
                name="HuggingFace Inference API",
                api_key_env_var="HF_API_KEY",
            ),
        }
        
        # Initialize circuit breakers for each provider
        self.circuit_breakers = {
            provider: CircuitBreaker() for provider in LLMProvider
        }
        
        # Initialize provider-specific clients
        self._initialize_clients()
        
        # Preferred order of providers for fallback
        self.provider_fallback_order = [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.AZURE_OPENAI,
            LLMProvider.HF_INFERENCE,
            LLMProvider.FALLBACK
        ]
    
    def _initialize_clients(self):
        """Initialize API clients for each provider"""
        self.clients = {}
        
        # OpenAI client
        if self.providers[LLMProvider.OPENAI].api_key:
            try:
                self.clients[LLMProvider.OPENAI] = AsyncOpenAI(
                    api_key=self.providers[LLMProvider.OPENAI].api_key
                )
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        
        # Azure OpenAI client
        if (self.providers[LLMProvider.AZURE_OPENAI].api_key and 
            self.providers[LLMProvider.AZURE_OPENAI].base_url):
            try:
                self.clients[LLMProvider.AZURE_OPENAI] = AsyncOpenAI(
                    api_key=self.providers[LLMProvider.AZURE_OPENAI].api_key,
                    base_url=self.providers[LLMProvider.AZURE_OPENAI].base_url
                )
                logger.info("Azure OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
        
        # Other clients would be initialized similarly
        # For now, we'll use httpx for generic API calls to other providers
    
    def _get_available_providers(self) -> List[LLMProvider]:
        """Get a list of available providers that can be used"""
        available_providers = []
        
        for provider in self.provider_fallback_order:
            # Skip providers that don't have API keys configured
            if provider != LLMProvider.FALLBACK and not (self.providers.get(provider, None) and self.providers.get(provider).api_key):
                continue
            
            # Skip providers with open circuit breakers
            if not self.circuit_breakers[provider].allow_request():
                logger.info(f"Provider {provider.value} has an open circuit breaker, skipping")
                continue
                
            available_providers.append(provider)
        
        return available_providers
    
    async def _call_with_circuit_breaker(
        self, 
        provider: LLMProvider, 
        call_func: Callable
    ) -> Dict[str, Any]:
        """
        Execute a call with circuit breaker protection.
        
        Args:
            provider: LLM provider to use
            call_func: Async function to call the provider
            
        Returns:
            Response from the provider
        
        Raises:
            Exception: If all attempts fail
        """
        if not self.circuit_breakers[provider].allow_request():
            raise Exception(f"Circuit is open for provider {provider.value}")
        
        try:
            result = await call_func()
            self.circuit_breakers[provider].record_success()
            return result
        except Exception as e:
            self.circuit_breakers[provider].record_failure()
            logger.error(f"Failed call to {provider.value}: {str(e)}")
            raise
    
    @retry(
        retry=retry_if_exception_type(
            (httpx.RequestError, httpx.HTTPStatusError, openai.RateLimitError, openai.APITimeoutError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def _call_openai(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call OpenAI API with retry logic.
        
        Args:
            messages: List of message objects
            model: Model to use
            temperature: Temperature parameter
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters
            
        Returns:
            API response
        """
        try:
            client = self.clients.get(LLMProvider.OPENAI)
            if not client:
                raise Exception("OpenAI client not initialized")
                
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return {
                "provider": LLMProvider.OPENAI.value,
                "content": response.choices[0].message.content,
                "model": model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    # Similar methods for other providers...
    
    async def _call_fallback_model(
        self, 
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Use a simple rule-based fallback when all LLM providers fail.
        
        Args:
            messages: List of message objects
            **kwargs: Additional parameters
            
        Returns:
            Fallback response
        """
        # Extract the last user message
        last_user_message = "No input provided"
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user_message = message.get("content", "No input provided")
                break
        
        # Very simple response based on keywords
        response = "I'm sorry, but I'm currently operating in fallback mode due to service limitations. "
        
        if "sentiment" in last_user_message.lower():
            response += "The sentiment analysis could not be completed at this time."
        elif "recommend" in last_user_message.lower():
            response += "I cannot provide content recommendations at this time."
        elif "analyze" in last_user_message.lower():
            response += "Content analysis is unavailable at this time."
        else:
            response += "Please try again later when full services are restored."
        
        return {
            "provider": LLMProvider.FALLBACK.value,
            "content": response,
            "model": "fallback-rule-based",
            "finish_reason": "fallback",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        preferred_provider: Optional[LLMProvider] = None,
        with_reasoning: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion with fallback between providers.
        
        Args:
            messages: List of message objects
            preferred_provider: Provider to try first
            with_reasoning: Whether to record reasoning chain
            **kwargs: Additional parameters passed to the LLM
            
        Returns:
            Response with provider info and content
        """
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Initializing LLM request",
                {
                    "messages_count": len(messages),
                    "preferred_provider": preferred_provider.value if preferred_provider else "None",
                },
                {"status": "initialized"}
            )
        
        # Determine provider order
        available_providers = self._get_available_providers()
        
        if preferred_provider and preferred_provider in available_providers:
            # Move preferred provider to the front
            available_providers.remove(preferred_provider)
            available_providers.insert(0, preferred_provider)
        
        if reasoning:
            reasoning.add_step(
                "Selecting providers",
                {"preferred_provider": preferred_provider.value if preferred_provider else "None"},
                {"available_providers": [p.value for p in available_providers]}
            )
        
        # Try each provider in order
        last_error = None
        for provider in available_providers:
            try:
                if reasoning:
                    reasoning.add_step(
                        f"Attempting provider: {provider.value}",
                        {"provider": provider.value},
                        {"status": "attempting"}
                    )
                
                # Call the appropriate method based on provider
                if provider == LLMProvider.OPENAI:
                    response = await self._call_with_circuit_breaker(
                        provider,
                        lambda: self._call_openai(messages, **kwargs)
                    )
                elif provider == LLMProvider.AZURE_OPENAI:
                    # Same OpenAI client with different base URL
                    response = await self._call_with_circuit_breaker(
                        provider,
                        lambda: self._call_openai(messages, **kwargs)
                    )
                # Add other provider methods as implemented
                elif provider == LLMProvider.FALLBACK:
                    response = await self._call_fallback_model(messages, **kwargs)
                else:
                    # Skip providers we don't have implementations for yet
                    continue
                
                if reasoning:
                    reasoning.add_step(
                        f"Provider {provider.value} succeeded",
                        {"provider": provider.value},
                        {
                            "status": "success",
                            "model": response.get("model", "unknown")
                        }
                    )
                
                # Add reasoning chain to response if requested
                if reasoning:
                    response["reasoning_chain"] = reasoning.get_reasoning_chain()
                
                return response
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {provider.value} failed: {last_error}")
                
                if reasoning:
                    reasoning.add_step(
                        f"Provider {provider.value} failed",
                        {"provider": provider.value},
                        {"status": "failed", "error": last_error}
                    )
        
        # If we get here, all providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        
        if reasoning:
            reasoning.add_step(
                "All providers failed",
                {"available_providers": [p.value for p in available_providers]},
                {"status": "all_failed", "last_error": last_error}
            )
        
        raise Exception(error_msg)
    
    async def text_embedding(
        self,
        text: str,
        preferred_provider: Optional[LLMProvider] = None,
        with_reasoning: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text embeddings with fallback between providers.
        
        Args:
            text: Text to embed
            preferred_provider: Provider to try first
            with_reasoning: Whether to record reasoning chain
            **kwargs: Additional parameters
            
        Returns:
            Embeddings with provider info
        """
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Initializing embedding request",
                {
                    "text_length": len(text),
                    "preferred_provider": preferred_provider.value if preferred_provider else "None",
                },
                {"status": "initialized"}
            )
        
        # Implementation would be similar to chat_completion
        # but using embedding-specific API calls
        
        # For now, return a placeholder implementation
        raise NotImplementedError("Text embedding with fallback not yet implemented")
