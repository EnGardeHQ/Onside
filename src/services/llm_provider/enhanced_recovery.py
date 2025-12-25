"""
Enhanced Recovery Service for LLM Providers
Following Semantic Seed BDD/TDD Coding Standards V2.0

This module extends the FallbackManager with enhanced error recovery capabilities,
backoff strategies, and detailed result evaluation to ensure robust AI service operations.
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional, Callable, TypeVar, Union, Awaitable, TypedDict, cast
from enum import Enum, auto
import traceback
import json
from datetime import datetime, timedelta
from functools import wraps

# Import from existing llm_provider modules
from src.models.llm_fallback import LLMProvider, FallbackReason
# Import conditionally to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.services.llm_provider.fallback_manager import FallbackManager

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for function decorators
T = TypeVar('T')
R = TypeVar('R')


class RecoveryStrategy(Enum):
    """Enumeration of recovery strategies for handling AI service errors."""
    RETRY = auto()           # Simple retry after delay
    EXPONENTIAL_BACKOFF = auto()  # Retry with exponential backoff
    PROVIDER_FALLBACK = auto()    # Fall back to alternative provider
    PROMPT_REFORMULATION = auto() # Retry with a simplified/reformulated prompt
    GRACEFUL_DEGRADATION = auto() # Return best-effort result or default


class RecoveryResult(TypedDict):
    """Type definition for recovery operation results."""
    success: bool
    result: Any
    strategy_used: Optional[RecoveryStrategy]
    provider_used: Optional[LLMProvider]
    attempts: int
    total_time: float
    error: Optional[str]


class EnhancedRecoveryService:
    """
    Enhanced recovery service for LLM providers with advanced error handling strategies.
    
    Features:
    - Multiple recovery strategies based on error type
    - Detailed telemetry for recovery operations
    - Prompt reformulation for handling context limitations
    - Graceful degradation with meaningful fallbacks
    """
    
    def __init__(self, fallback_manager: 'FallbackManager'):
        """Initialize the enhanced recovery service with a fallback manager."""
        self.fallback_manager = fallback_manager
        self.default_max_retries = 3
        self.default_backoff_base = 2
        self.default_initial_delay = 1.0  # seconds
        self.recovery_history: List[RecoveryResult] = []
        
        logger.info("Enhanced recovery service initialized")
    
    async def execute_with_recovery(
        self,
        operation: Callable[..., Awaitable[T]],
        *args: Any,
        strategies: Optional[List[RecoveryStrategy]] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_base: float = 2.0,
        jitter: bool = True,
        providers: Optional[List[LLMProvider]] = None,
        prompt_simplification: Optional[Callable[[str], str]] = None,
        default_result: Optional[T] = None,
        **kwargs: Any
    ) -> RecoveryResult:
        """
        Execute an operation with enhanced recovery strategies.
        
        Args:
            operation: The async operation to execute
            args: Positional arguments for the operation
            strategies: List of recovery strategies to try (in order)
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            backoff_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            providers: Alternative providers to try if PROVIDER_FALLBACK is used
            prompt_simplification: Function to simplify prompts if PROMPT_REFORMULATION is used
            default_result: Default result to return if all recovery attempts fail
            kwargs: Keyword arguments for the operation
            
        Returns:
            RecoveryResult containing the operation result and metadata
        """
        if strategies is None:
            strategies = [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.EXPONENTIAL_BACKOFF,
                RecoveryStrategy.PROVIDER_FALLBACK,
                RecoveryStrategy.PROMPT_REFORMULATION,
                RecoveryStrategy.GRACEFUL_DEGRADATION
            ]
        
        if providers is None and RecoveryStrategy.PROVIDER_FALLBACK in strategies:
            providers = [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.GEMINI]
        
        start_time = time.time()
        attempts = 0
        current_strategy_index = 0
        current_provider_index = 0
        original_prompt = kwargs.get("prompt", "") if isinstance(kwargs.get("prompt"), str) else ""
        current_error = None
        
        while attempts < max_retries and current_strategy_index < len(strategies):
            current_strategy = strategies[current_strategy_index]
            attempts += 1
            
            # Apply the current recovery strategy
            try:
                if current_strategy == RecoveryStrategy.PROVIDER_FALLBACK and providers:
                    # Try a different provider
                    provider = providers[current_provider_index % len(providers)]
                    kwargs["provider"] = provider
                    current_provider_index += 1
                    
                elif current_strategy == RecoveryStrategy.PROMPT_REFORMULATION and prompt_simplification and original_prompt:
                    # Reformulate the prompt
                    kwargs["prompt"] = prompt_simplification(original_prompt)
                
                # Execute the operation
                result = await operation(*args, **kwargs)
                
                # Success! Return the result
                recovery_result = {
                    "success": True,
                    "result": result,
                    "strategy_used": current_strategy,
                    "provider_used": kwargs.get("provider"),
                    "attempts": attempts,
                    "total_time": time.time() - start_time,
                    "error": None
                }
                self.recovery_history.append(recovery_result)
                return cast(RecoveryResult, recovery_result)
                
            except Exception as e:
                current_error = str(e)
                logger.warning(f"Recovery attempt {attempts} failed with strategy {current_strategy}: {current_error}")
                
                # Calculate delay based on the current strategy
                delay = 0
                if current_strategy == RecoveryStrategy.RETRY:
                    delay = initial_delay
                elif current_strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
                    delay = initial_delay * (backoff_base ** (attempts - 1))
                    
                if jitter:
                    delay *= (0.5 + random.random())
                
                # Wait before next attempt if a delay is specified
                if delay > 0:
                    await asyncio.sleep(delay)
                
                # If this strategy has been tried max_retries times, move to the next strategy
                if attempts % max_retries == 0:
                    current_strategy_index += 1
        
        # All recovery attempts failed, use graceful degradation
        if RecoveryStrategy.GRACEFUL_DEGRADATION in strategies and default_result is not None:
            recovery_result = {
                "success": False,
                "result": default_result,
                "strategy_used": RecoveryStrategy.GRACEFUL_DEGRADATION,
                "provider_used": None,
                "attempts": attempts,
                "total_time": time.time() - start_time,
                "error": current_error
            }
        else:
            recovery_result = {
                "success": False,
                "result": None,
                "strategy_used": None,
                "provider_used": None,
                "attempts": attempts,
                "total_time": time.time() - start_time,
                "error": current_error
            }
        
        self.recovery_history.append(recovery_result)
        return cast(RecoveryResult, recovery_result)
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get statistics on recovery operations."""
        if not self.recovery_history:
            return {
                "total_operations": 0,
                "success_rate": 0,
                "average_attempts": 0,
                "average_time": 0,
                "strategy_success": {}
            }
        
        successful = [r for r in self.recovery_history if r["success"]]
        success_rate = len(successful) / len(self.recovery_history)
        
        strategy_counts = {}
        strategy_success = {}
        
        for result in self.recovery_history:
            strategy = result["strategy_used"]
            if strategy:
                strategy_name = strategy.name
                if strategy_name not in strategy_counts:
                    strategy_counts[strategy_name] = 0
                    strategy_success[strategy_name] = 0
                
                strategy_counts[strategy_name] += 1
                if result["success"]:
                    strategy_success[strategy_name] += 1
        
        for strategy, count in strategy_counts.items():
            if count > 0:
                strategy_success[strategy] = strategy_success[strategy] / count
        
        return {
            "total_operations": len(self.recovery_history),
            "success_rate": success_rate,
            "average_attempts": sum(r["attempts"] for r in self.recovery_history) / len(self.recovery_history),
            "average_time": sum(r["total_time"] for r in self.recovery_history) / len(self.recovery_history),
            "strategy_success": strategy_success
        }
    
    def reset_stats(self) -> None:
        """Reset recovery statistics."""
        self.recovery_history = []
        logger.info("Recovery statistics reset")


# Standard prompt simplification function
def simplify_prompt(prompt: str) -> str:
    """
    Simplify a prompt to handle context limitations.
    
    This function reduces the length and complexity of prompts
    when hitting context limitations or other provider constraints.
    """
    lines = prompt.strip().split('\n')
    
    # If prompt is very long, keep only essential parts
    if len(lines) > 20:
        # Extract the first few lines (usually contains the task)
        header = lines[:5]
        
        # Extract the last few lines (usually contains the question)
        footer = lines[-5:]
        
        # Create a simplified version
        simplified = "\n".join(header) + "\n\n[Content truncated for brevity]\n\n" + "\n".join(footer)
        
        # If still too long, just keep the core question
        if len(simplified) > 1000:
            # Try to find the actual question or instruction
            question_markers = ["?", "write", "analyze", "explain", "describe", "list", "provide"]
            question_lines = []
            
            for line in lines:
                if any(marker in line.lower() for marker in question_markers):
                    question_lines.append(line)
            
            if question_lines:
                return "Based on the context discussed, please: \n\n" + "\n".join(question_lines[-3:])
        
        return simplified
    
    return prompt
