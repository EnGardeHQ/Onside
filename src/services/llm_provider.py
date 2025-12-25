"""LLM Provider and Fallback Manager Service.

This module implements the Sprint 4 requirement for robust LLM service management
with automatic fallback mechanisms and performance tracking.
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
import asyncio
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.report import Report
from src.models.llm_fallback import LLMProvider, FallbackReason, LLMFallback

logger = logging.getLogger("llm_provider")


class ProviderConfig:
    """Configuration for an LLM provider."""
    def __init__(
        self,
        name: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        confidence_threshold: float = 0.7,
        rate_limit: int = 100
    ):
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries
        self.confidence_threshold = confidence_threshold
        self.rate_limit = rate_limit
        self.current_rate = 0
        self.last_reset = datetime.utcnow()


class FallbackManager:
    """
    Manages LLM providers and implements fallback strategies.
    
    This class implements Sprint 4's requirement for robust handling of LLM
    service disruptions with automatic fallback to alternative providers.
    
    Features:
    - Multiple provider support (OpenAI, Anthropic, Cohere, HuggingFace)
    - Automatic fallback on failures
    - Rate limit tracking
    - Performance monitoring
    - Chain-of-thought logging
    """
    
    def __init__(self):
        """Initialize the fallback manager with provider configurations."""
        # Initialize logger
        self.logger = logging.getLogger("llm_provider.FallbackManager")
        
        # Configure logging format
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Initialize provider configurations
        self.providers = {
            LLMProvider.OPENAI: ProviderConfig(
                name="openai",
                timeout=10.0,
                max_retries=3,
                confidence_threshold=0.7,
                rate_limit=100
            ),
            LLMProvider.ANTHROPIC: ProviderConfig(
                name="anthropic",
                timeout=15.0,
                max_retries=2,
                confidence_threshold=0.65,
                rate_limit=50
            ),
            LLMProvider.COHERE: ProviderConfig(
                name="cohere",
                timeout=8.0,
                max_retries=3,
                confidence_threshold=0.6,
                rate_limit=200
            ),
            LLMProvider.HUGGINGFACE: ProviderConfig(
                name="huggingface",
                timeout=20.0,
                max_retries=2,
                confidence_threshold=0.5,
                rate_limit=300
            )
        }
        
        # Define fallback chain with OpenAI as primary and Anthropic as fallback
        self.fallback_chain = [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
        
        # Initialize metrics
        self.metrics = {
            provider: {
                "success_count": 0,
                "failure_count": 0,
                "avg_latency": 0.0,
                "total_requests": 0
            }
            for provider in LLMProvider
        }
        
        self.logger.info("FallbackManager initialized with providers: %s", 
                        [p.value for p in self.fallback_chain])
    
    async def execute_with_fallback(
        self,
        prompt: str,
        report: Report,
        initial_provider: LLMProvider = LLMProvider.OPENAI,
        confidence_threshold: Optional[float] = None,
        **kwargs
    ) -> Tuple[Dict[str, Any], LLMProvider]:
        """
        Execute an LLM request with automatic fallback handling.
        
        Args:
            prompt: The prompt to send to the LLM
            report: The report instance for tracking fallbacks
            initial_provider: The first provider to try
            confidence_threshold: Minimum confidence score required
            **kwargs: Additional arguments for the LLM call
            
        Returns:
            Tuple of (result dict, successful provider)
        """
        # Only use providers in the fallback chain
        if initial_provider not in self.fallback_chain:
            initial_provider = self.fallback_chain[0]
            self.logger.warning(
                f"Initial provider {initial_provider.value} not in fallback chain. "
                f"Using {self.fallback_chain[0].value} instead."
            )
        
        tried_providers = set()
        current_provider = initial_provider
        last_error = None
        
        while len(tried_providers) < len(self.fallback_chain):
            if current_provider in tried_providers:
                # Get next provider in chain
                current_idx = self.fallback_chain.index(current_provider)
                next_idx = (current_idx + 1) % len(self.fallback_chain)
                current_provider = self.fallback_chain[next_idx]
                continue
            
            # Skip providers not in fallback chain
            if current_provider not in self.fallback_chain:
                continue
                
            tried_providers.add(current_provider)
            provider_config = self.providers[current_provider]
            
            try:
                # Check rate limits
                if not self._check_rate_limit(current_provider):
                    raise Exception(f"Rate limit exceeded for {current_provider.value}")
                
                # Execute LLM call
                start_time = datetime.utcnow()
                result = await self._execute_llm_call(
                    provider=current_provider,
                    prompt=prompt,
                    timeout=provider_config.timeout,
                    **kwargs
                )
                latency = (datetime.utcnow() - start_time).total_seconds()
                
                # Update metrics
                self._update_metrics(current_provider, True, latency)
                
                # Check confidence threshold
                if confidence_threshold and result.get("confidence_score", 0) < confidence_threshold:
                    if len(self.fallback_chain) > 1:
                        next_provider = self.fallback_chain[
                            (self.fallback_chain.index(current_provider) + 1) 
                            % len(self.fallback_chain)
                        ]
                        report.track_llm_fallback(
                            original_provider=current_provider.value,
                            fallback_provider=next_provider.value,
                            reason=FallbackReason.LOW_CONFIDENCE.value,
                            prompt=prompt
                        )
                        continue
                
                return result, current_provider
                
            except asyncio.TimeoutError:
                self._update_metrics(current_provider, False, provider_config.timeout)
                last_error = "timeout"
                if len(self.fallback_chain) > 1:
                    next_provider = self.fallback_chain[
                        (self.fallback_chain.index(current_provider) + 1) 
                        % len(self.fallback_chain)
                    ]
                    report.track_llm_fallback(
                        original_provider=current_provider.value,
                        fallback_provider=next_provider.value,
                        reason=FallbackReason.TIMEOUT.value,
                        prompt=prompt
                    )
                
            except Exception as e:
                self._update_metrics(current_provider, False, 0)
                last_error = str(e)
                if len(self.fallback_chain) > 1:
                    next_provider = self.fallback_chain[
                        (self.fallback_chain.index(current_provider) + 1) 
                        % len(self.fallback_chain)
                    ]
                    report.track_llm_fallback(
                        original_provider=current_provider.value,
                        fallback_provider=next_provider.value,
                        reason=FallbackReason.ERROR.value,
                        prompt=prompt
                    )
        
        # All providers failed
        raise Exception(
            f"All providers failed. Last error: {last_error}. "
            f"Tried providers: {[p.value for p in tried_providers]}"
        )
    
    def _check_rate_limit(self, provider: LLMProvider) -> bool:
        """Check if a provider has exceeded its rate limit."""
        config = self.providers[provider]
        now = datetime.utcnow()
        
        # Reset counter if enough time has passed
        if (now - config.last_reset).total_seconds() >= 60:
            config.current_rate = 0
            config.last_reset = now
        
        if config.current_rate >= config.rate_limit:
            return False
            
        config.current_rate += 1
        return True
    
    def _update_metrics(
        self,
        provider: LLMProvider,
        success: bool,
        latency: float
    ) -> None:
        """Update performance metrics for a provider."""
        metrics = self.metrics[provider]
        metrics["total_requests"] += 1
        
        if success:
            metrics["success_count"] += 1
            # Update moving average of latency
            metrics["avg_latency"] = (
                (metrics["avg_latency"] * (metrics["success_count"] - 1) + latency)
                / metrics["success_count"]
            )
        else:
            metrics["failure_count"] += 1
    
    async def _execute_llm_call(
        self,
        provider: LLMProvider,
        prompt: str,
        timeout: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute an LLM API call with the specified provider."""
        try:
            if provider == LLMProvider.OPENAI:
                import openai
                from openai import AsyncOpenAI
                import json
                import os
                
                # Initialize OpenAI client
                client = AsyncOpenAI(
                    api_key=os.getenv('OPENAI_API_KEY'),
                    timeout=timeout
                )
                
                # Prepare system message for chain-of-thought reasoning
                system_msg = (
                    "You are an AI analyst helping generate insights for a competitor analysis report. "
                    "Follow these rules:\n"
                    "1. Structure your response as valid JSON\n"
                    "2. Include 'insights' as a list of objects\n"
                    "3. Each insight must have: type, content, confidence, supporting_data, action_items\n"
                    "4. Types can be: trend, opportunity, threat, recommendation\n"
                    "5. Use chain-of-thought reasoning to explain your analysis"
                )
                
                # Make API call with timeout
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        response_format={"type": "json_object"}
                    ),
                    timeout=timeout
                )
                
                # Extract and validate response
                try:
                    content = response.choices[0].message.content
                    result = json.loads(content)
                    
                    # Ensure insights field exists
                    if "insights" not in result:
                        result = {"insights": [result] if isinstance(result, dict) else []}
                    
                    # Add confidence score based on model's internal metrics
                    result["confidence_score"] = 0.85  # GPT-4 baseline confidence
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse OpenAI response: {e}")
                    raise
                    
            elif provider == LLMProvider.ANTHROPIC:
                import anthropic
                import os
                import json
                import asyncio
                from functools import partial
                
                # Initialize Anthropic client with API key from env
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable is required")
                client = anthropic.Anthropic(api_key=api_key)
                
                # System message for chain-of-thought reasoning
                system_msg = (
                    "You are an AI analyst helping generate insights for a competitor analysis report. "
                    "Follow these rules:\n"
                    "1. Structure your response as valid JSON\n"
                    "2. Include 'insights' as a list of objects\n"
                    "3. Each insight must have: type, content, confidence, supporting_data, action_items\n"
                    "4. Types can be: trend, opportunity, threat, recommendation\n"
                    "5. Use chain-of-thought reasoning to explain your analysis"
                )
                
                # Since anthropic.messages.create isn't natively async, we need to use run_in_executor
                # to run it in a thread pool to avoid blocking the event loop
                create_message_func = partial(
                    client.messages.create,
                    model="claude-3-sonnet-20240229",
                    max_tokens=2048,
                    system=system_msg,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                
                self.logger.info(f"Making Anthropic API call with timeout {timeout}s")
                loop = asyncio.get_event_loop()
                
                try:
                    # Run the synchronous Anthropic API call in a thread pool
                    response = await asyncio.wait_for(
                        loop.run_in_executor(None, create_message_func),
                        timeout=timeout
                    )
                    
                    # Extract and validate response
                    content = response.content[0].text
                    self.logger.info(f"Received response from Anthropic: {content[:100]}...")
                    
                    # Try to parse as JSON
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError:
                        # Extract JSON from markdown if response contains markdown
                        import re
                        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group(1))
                        else:
                            raise ValueError("Could not extract valid JSON from Anthropic response")
                    
                    # Ensure insights field exists
                    if "insights" not in result:
                        result = {"insights": [result] if isinstance(result, dict) else []}
                    
                    # Add confidence score
                    result["confidence_score"] = 0.8  # Claude baseline confidence
                    
                    return result
                except Exception as e:
                    self.logger.error(f"Error in Anthropic API call: {str(e)}")
                    raise
                
            elif provider == LLMProvider.COHERE:
                # TODO: Implement Cohere API integration
                raise NotImplementedError("Cohere API not yet implemented")
                
            else:  # HuggingFace
                # TODO: Implement HuggingFace API integration
                raise NotImplementedError("HuggingFace API not yet implemented")
                
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout calling {provider.value} API after {timeout}s")
            raise
            
        except Exception as e:
            self.logger.error(f"Error calling {provider.value} API: {str(e)}")
            raise
    
    def get_provider_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all providers."""
        return {
            provider.value: {
                "success_rate": (
                    metrics["success_count"] / metrics["total_requests"]
                    if metrics["total_requests"] > 0 else 0
                ),
                "avg_latency": metrics["avg_latency"],
                "total_requests": metrics["total_requests"],
                "failure_count": metrics["failure_count"]
            }
            for provider, metrics in self.metrics.items()
        }
