"""
Chain of Thought Reasoning Framework for AI services.

This module provides base classes and utilities for implementing chain-of-thought
reasoning in AI services, allowing for step-by-step logging of reasoning processes
and better explainability of AI decisions.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import logging
from uuid import uuid4


class ReasoningStep:
    """Represents a single step in a chain-of-thought reasoning process."""
    
    def __init__(
        self, 
        description: str, 
        input_data: Any, 
        output_data: Any, 
        step_number: Optional[int] = None
    ):
        """
        Initialize a reasoning step.
        
        Args:
            description: Human-readable description of the step
            input_data: Input data for this reasoning step
            output_data: Output produced by this reasoning step
            step_number: Optional step number (auto-assigned if not provided)
        """
        self.id = str(uuid4())
        self.description = description
        self.input_data = input_data
        self.output_data = output_data
        self.step_number = step_number
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the reasoning step to a dictionary."""
        return {
            "id": self.id,
            "step": self.step_number,
            "description": self.description,
            "input": self._serialize_data(self.input_data),
            "output": self._serialize_data(self.output_data),
            "timestamp": self.timestamp
        }
    
    def _serialize_data(self, data: Any) -> Any:
        """Safely serialize complex data structures."""
        if hasattr(data, "to_dict"):
            return data.to_dict()
        
        # Try to convert to a simple type if possible
        try:
            # Check if JSON serializable
            json.dumps(data)
            return data
        except (TypeError, OverflowError):
            # If not serializable, convert to string representation
            return str(data)


class ChainOfThoughtReasoning:
    """
    Implements chain-of-thought reasoning process for AI services.
    
    Provides a framework for logging step-by-step reasoning processes,
    which improves explainability and allows for better debugging of AI decisions.
    """
    
    def __init__(self, chain_id: Optional[str] = None):
        """
        Initialize a new reasoning chain.
        
        Args:
            chain_id: Optional ID for the reasoning chain (auto-generated if not provided)
        """
        self.chain_id = chain_id or str(uuid4())
        self.steps: List[ReasoningStep] = []
        self.logger = logging.getLogger("chain_of_thought")
        self.start_time = datetime.utcnow().isoformat()
    
    def add_step(self, description: str, input_data: Any, output_data: Any) -> str:
        """
        Add a reasoning step to the chain.
        
        Args:
            description: Human-readable description of the step
            input_data: Input data for this reasoning step
            output_data: Output produced by this reasoning step
            
        Returns:
            The ID of the created step
        """
        step = ReasoningStep(
            description=description,
            input_data=input_data,
            output_data=output_data,
            step_number=len(self.steps) + 1
        )
        self.steps.append(step)
        
        # Log the step
        self.logger.info(
            f"Chain {self.chain_id} Step {step.step_number}: {description}"
        )
        
        return step.id
    
    def get_reasoning_chain(self) -> Dict[str, Any]:
        """Get the complete reasoning chain as a dictionary."""
        return {
            "chain_id": self.chain_id,
            "steps": [step.to_dict() for step in self.steps],
            "summary": self._generate_summary(),
            "start_time": self.start_time,
            "end_time": datetime.utcnow().isoformat(),
            "step_count": len(self.steps)
        }
    
    def _generate_summary(self) -> str:
        """Generate a summary of the reasoning process."""
        if not self.steps:
            return "No reasoning steps recorded"
        
        return f"Chain of thought with {len(self.steps)} steps from {self.start_time} to {datetime.utcnow().isoformat()}"
    
    def clear(self) -> None:
        """Clear all reasoning steps."""
        self.steps = []
        self.start_time = datetime.utcnow().isoformat()


class LLMWithChainOfThought:
    """
    Base class for LLM services that implement chain-of-thought reasoning.
    
    Provides a standardized interface for LLM services to log their reasoning
    process and provide explainable outputs.
    """
    
    def __init__(self, service_name: str):
        """
        Initialize the LLM service with chain-of-thought capabilities.
        
        Args:
            service_name: Name of the service for logging purposes
        """
        self.service_name = service_name
        self.reasoning = ChainOfThoughtReasoning()
        self.logger = logging.getLogger(f"llm.{service_name}")
    
    def reset_reasoning(self) -> None:
        """Reset the reasoning chain for a new process."""
        self.reasoning = ChainOfThoughtReasoning()
    
    def log_step(self, description: str, input_data: Any, output_data: Any) -> str:
        """
        Log a reasoning step.
        
        Args:
            description: Human-readable description of the step
            input_data: Input data for this reasoning step
            output_data: Output produced by this reasoning step
            
        Returns:
            The ID of the created step
        """
        return self.reasoning.add_step(description, input_data, output_data)
    
    def get_reasoning(self) -> Dict[str, Any]:
        """Get the complete reasoning chain."""
        return self.reasoning.get_reasoning_chain()
    
    def get_reasoning_summary(self) -> str:
        """Get a summary of the reasoning process."""
        return self.reasoning._generate_summary()
