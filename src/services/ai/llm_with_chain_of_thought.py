"""LLM with Chain of Thought Base Class.

This module implements the base class for AI services that use LLMs with
chain-of-thought reasoning, following Sprint 4 requirements.

Following Semantic Seed coding standards with proper error handling,
logging, and type hints.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from datetime import datetime

from src.models.llm_fallback import LLMProvider

# Import Report using a string literal for the type hint to avoid circular imports
if TYPE_CHECKING:
    from src.models.report import Report
else:
    Report = 'Report'  # type: ignore

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.services.llm_provider.fallback_manager import FallbackManager


class LLMWithChainOfThought:
    """
    Base class for AI services that use LLMs with chain-of-thought reasoning.
    
    This class implements the Sprint 4 requirement for chain-of-thought reasoning
    and comprehensive logging of AI reasoning steps.
    
    Features:
    - Chain-of-thought reasoning
    - Confidence scoring
    - Detailed logging of reasoning steps
    - Fallback mechanisms
    """
    
    def __init__(self, llm_manager: 'FallbackManager'):
        """Initialize the LLM with chain of thought base class.
        
        Args:
            llm_manager: The LLM fallback manager
        """
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.chain_of_thought_steps = []
    
    async def _execute_llm_with_reasoning(
        self,
        prompt: str,
        report: Report,
        with_chain_of_thought: bool = True,
        confidence_threshold: Optional[float] = None,
        **kwargs
    ) -> Tuple[Dict[str, Any], float]:
        """
        Execute an LLM call with chain-of-thought reasoning.
        
        Args:
            prompt: The prompt to send to the LLM
            report: The report instance for tracking
            with_chain_of_thought: Whether to include chain-of-thought reasoning
            confidence_threshold: Minimum confidence score required
            **kwargs: Additional arguments for the LLM call
            
        Returns:
            Tuple of (result dict, confidence score)
        """
        # Add chain-of-thought instruction if enabled
        if with_chain_of_thought:
            prompt = self._add_chain_of_thought_instruction(prompt)
        
        # Log the prompt
        self.logger.info(f"Executing LLM call with prompt: {prompt[:100]}...")
        self._add_reasoning_step("Preparing LLM prompt", prompt[:200] + "...")
        
        # Execute LLM call with fallback
        try:
            result, provider = await self.llm_manager.execute_with_fallback(
                prompt=prompt,
                report=report,
                confidence_threshold=confidence_threshold,
                **kwargs
            )
            
            # Extract and log chain-of-thought reasoning if present
            if with_chain_of_thought and "reasoning" in result:
                reasoning = result["reasoning"]
                self._add_reasoning_step("LLM reasoning", reasoning)
                
                # Store reasoning in report
                report.chain_of_thought = {
                    "steps": self.chain_of_thought_steps,
                    "provider": provider.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Log confidence score
            confidence_score = result.get("confidence_score", 0.7)
            self._add_reasoning_step(
                "Confidence assessment", 
                f"Confidence score: {confidence_score}"
            )
            
            return result, confidence_score
            
        except Exception as e:
            self.logger.error(f"Error executing LLM with reasoning: {str(e)}")
            self._add_reasoning_step("Error", f"Failed to execute LLM: {str(e)}")
            
            # Return empty result with low confidence
            return {}, 0.5
    
    def _add_chain_of_thought_instruction(self, prompt: str) -> str:
        """
        Add chain-of-thought instruction to the prompt.
        
        Args:
            prompt: The original prompt
            
        Returns:
            Modified prompt with chain-of-thought instruction
        """
        cot_instruction = """
        Please provide your reasoning step by step before giving your final answer.
        Include your thought process, any assumptions you make, and how you arrived at your conclusions.
        Structure your response as follows:
        
        {
            "reasoning": "Your detailed step-by-step reasoning here...",
            "result": {
                // Your structured analysis result here
            },
            "confidence_score": 0.0 to 1.0 // Your confidence in the result
        }
        """
        
        return f"{prompt}\n\n{cot_instruction}"
    
    def _add_reasoning_step(self, step_name: str, details: str):
        """
        Add a reasoning step to the chain of thought.
        
        Args:
            step_name: Name of the reasoning step
            details: Details of the reasoning step
        """
        timestamp = datetime.utcnow().isoformat()
        step = f"[{timestamp}] {step_name}: {details}"
        self.chain_of_thought_steps.append(step)
        self.logger.debug(f"Chain of thought step: {step_name}")
    
    def _calculate_confidence_score(
        self,
        data_quality: float,
        llm_confidence: float,
        analysis_confidence: float
    ) -> float:
        """
        Calculate overall confidence score based on multiple factors.
        
        Args:
            data_quality: Score representing data quality (0.0-1.0)
            llm_confidence: Confidence score from LLM (0.0-1.0)
            analysis_confidence: Confidence in analysis method (0.0-1.0)
            
        Returns:
            Overall confidence score (0.0-1.0)
        """
        # Weighted average of confidence factors
        weights = {
            "data_quality": 0.4,
            "llm_confidence": 0.4,
            "analysis_confidence": 0.2
        }
        
        weighted_score = (
            data_quality * weights["data_quality"] +
            llm_confidence * weights["llm_confidence"] +
            analysis_confidence * weights["analysis_confidence"]
        )
        
        # Round to 2 decimal places
        return round(weighted_score, 2)
    
    def reset_chain_of_thought(self):
        """Reset the chain of thought steps."""
        self.chain_of_thought_steps = []
