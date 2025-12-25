"""LLM with Chain of Thought Reasoning Base Class

This module implements the base class for LLM services with chain-of-thought reasoning
capabilities following Sprint 4 requirements and Semantic Seed coding standards.

Features:
- Chain-of-thought reasoning
- Data quality validation
- Confidence scoring with weighted metrics
- Structured JSON prompts
- Error handling with graceful fallbacks
- Report object integration for tracking
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import config

logger = logging.getLogger(__name__)

class LLMWithChainOfThought(ABC):
    """Base class for LLM services with chain-of-thought reasoning.
    
    Following Sprint 4 requirements, this class implements:
    - Comprehensive logging of reasoning steps
    - Data quality validation
    - Confidence scoring with weighted metrics
    - Structured JSON prompts for LLM interactions
    - Error handling with graceful fallbacks
    - Report object integration for tracking
    """
    
    def __init__(
        self,
        session: AsyncSession,
        llm_manager: Optional["FallbackManager"] = None,
        confidence_threshold: float = 0.85,
        chain_of_thought_enabled: bool = True,
        data_quality_validation: bool = True,
        **kwargs
    ):
        """Initialize LLM service with chain-of-thought reasoning.
        
        Args:
            session: Database session
            llm_manager: LLM fallback manager
            confidence_threshold: Minimum confidence score for results
            chain_of_thought_enabled: Enable chain-of-thought reasoning
            data_quality_validation: Enable data quality validation
        """
        self.session = session
        self.llm_manager = llm_manager
        self.confidence_threshold = confidence_threshold
        self.chain_of_thought_enabled = chain_of_thought_enabled
        self.data_quality_validation = data_quality_validation
        self.reasoning_steps = []
        
        # Sprint 4: Configure additional settings
        self.structured_output = kwargs.get("structured_output", True)
        self.fallback_enabled = kwargs.get("fallback_enabled", True)
        self.max_retries = kwargs.get("max_retries", 3)
    
    async def execute_with_reasoning(
        self, 
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute LLM request with chain-of-thought reasoning.
        
        Args:
            prompt: Prompt to send to LLM
            context: Additional context for the prompt
            
        Returns:
            Dictionary with response, confidence, and reasoning
        """
        try:
            # Reset reasoning steps
            self.reasoning_steps = []
            
            # Add chain-of-thought instructions if enabled
            if self.chain_of_thought_enabled:
                prompt = self._add_chain_of_thought_instructions(prompt)
            
            # Add context if provided
            if context:
                prompt = self._add_context_to_prompt(prompt, context)
            
            # Log the prompt
            logger.info(f"Executing LLM request with reasoning")
            logger.debug(f"Prompt: {prompt[:100]}...")
            
            # Execute LLM request with fallback
            response, confidence = await self._execute_llm_request(prompt)
            
            # Parse and validate response
            result = self._parse_response(response)
            
            # Calculate final confidence score
            if self.data_quality_validation:
                final_confidence = self._calculate_confidence(result, confidence)
            else:
                final_confidence = confidence
            
            # Log the result
            logger.info(f"LLM request completed with confidence: {final_confidence:.2f}")
            
            return {
                "result": result,
                "confidence": final_confidence,
                "reasoning": self.reasoning_steps,
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing LLM request: {str(e)}")
            return {
                "result": {},
                "confidence": 0.0,
                "reasoning": self.reasoning_steps,
                "error": str(e)
            }
    
    @abstractmethod
    async def _execute_llm_request(
        self, 
        prompt: str
    ) -> Tuple[str, float]:
        """Execute LLM request implementation.
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            Tuple of (response, confidence)
        """
        pass
    
    def _add_chain_of_thought_instructions(self, prompt: str) -> str:
        """Add chain-of-thought instructions to prompt.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Modified prompt with chain-of-thought instructions
        """
        cot_instructions = """
        Important: Use chain-of-thought reasoning to explain your analysis step-by-step.
        
        1. First, carefully analyze the data provided
        2. Identify key patterns, trends, and insights
        3. Explain your reasoning for each conclusion
        4. Provide a confidence score (0.0-1.0) for each insight
        5. Structure your final answer as a JSON object
        
        Show your complete reasoning process before presenting your final answer.
        """
        
        return f"{cot_instructions}\n\n{prompt}"
    
    def _add_context_to_prompt(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> str:
        """Add context to prompt.
        
        Args:
            prompt: Original prompt
            context: Context to add
            
        Returns:
            Modified prompt with context
        """
        context_str = json.dumps(context, indent=2)
        return f"Context:\n{context_str}\n\n{prompt}"
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Parsed response as dictionary
        """
        try:
            # Extract reasoning steps
            self._extract_reasoning_steps(response)
            
            # Try to extract JSON
            if self.structured_output:
                return self._extract_json(response)
            
            # Return raw response if structured output not required
            return {"response": response}
            
        except Exception as e:
            logger.error(f"❌ Error parsing LLM response: {str(e)}")
            return {"response": response, "parse_error": str(e)}
    
    def _extract_reasoning_steps(self, response: str) -> None:
        """Extract reasoning steps from response.
        
        Args:
            response: Raw response from LLM
        """
        # Look for reasoning patterns
        lines = response.split("\n")
        current_step = ""
        in_reasoning = False
        
        for line in lines:
            # Check for reasoning section markers
            if "reasoning" in line.lower() or "step" in line.lower() or "analysis" in line.lower():
                in_reasoning = True
                
            if in_reasoning and line.strip() and not line.startswith("```"):
                current_step += line + "\n"
                
            # Check for end of reasoning section
            if in_reasoning and ("final answer" in line.lower() or "conclusion" in line.lower()):
                if current_step:
                    self.reasoning_steps.append(current_step.strip())
                in_reasoning = False
                current_step = ""
                
            # Check for step separation
            if in_reasoning and current_step and (line.strip() == "" or line.startswith("Step") or line.startswith("#")):
                if current_step.strip():
                    self.reasoning_steps.append(current_step.strip())
                current_step = line + "\n" if line.strip() else ""
        
        # Add final step if there is one
        if current_step.strip():
            self.reasoning_steps.append(current_step.strip())
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Extract JSON from response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Extracted JSON as dictionary
        """
        try:
            # Look for JSON block in code fences
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            
            # Look for JSON block in regular code fences
            if "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                # Skip if the code fence specifies a different language
                if not response[3:start].strip() or "json" in response[3:start].strip().lower():
                    json_str = response[start:end].strip()
                    return json.loads(json_str)
            
            # Look for JSON object with braces
            if "{" in response and "}" in response:
                start = response.find("{")
                # Find the matching closing brace
                brace_count = 0
                for i in range(start, len(response)):
                    if response[i] == "{":
                        brace_count += 1
                    elif response[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response[start:i+1].strip()
                            return json.loads(json_str)
            
            # Fallback: try to parse the entire response as JSON
            return json.loads(response)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not extract JSON from response: {str(e)}")
            return {"response": response}
    
    def _calculate_confidence(
        self, 
        result: Dict[str, Any], 
        base_confidence: float
    ) -> float:
        """Calculate final confidence score.
        
        Args:
            result: Parsed response
            base_confidence: Base confidence from LLM
            
        Returns:
            Final confidence score
        """
        try:
            # Use LLM's confidence if provided in the result
            if "confidence" in result:
                llm_confidence = float(result["confidence"])
            else:
                llm_confidence = base_confidence
            
            # Data quality factor
            data_quality = 1.0  # Default perfect quality
            if hasattr(self, "calculate_data_quality"):
                data_quality = self.calculate_data_quality()
            
            # Reasoning quality based on number of steps
            reasoning_quality = min(1.0, len(self.reasoning_steps) / 5.0) if self.reasoning_steps else 0.5
            
            # Calculate weighted confidence
            weights = config.ai.weights if hasattr(config.ai, "weights") else {
                "llm_confidence": 0.5,
                "data_quality": 0.3,
                "reasoning_quality": 0.2
            }
            
            final_confidence = (
                weights["llm_confidence"] * llm_confidence +
                weights["data_quality"] * data_quality +
                weights["reasoning_quality"] * reasoning_quality
            )
            
            return min(1.0, max(0.0, final_confidence))
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating confidence: {str(e)}")
            return base_confidence
