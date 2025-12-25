"""
Performance Monitoring Service for OnSide
Following Semantic Seed BDD/TDD Coding Standards V2.0

This module provides telemetry and performance monitoring capabilities
to track execution times, resource usage, and identify bottlenecks
across the OnSide platform.
"""

import time
import logging
import asyncio
import functools
import statistics
from typing import Dict, List, Any, Optional, Callable, TypeVar, Union, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import traceback
import json
import os
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for function decorators
F = TypeVar('F', bound=Callable[..., Any])
AFT = TypeVar('AFT', bound=Callable[..., Awaitable[Any]])

@dataclass
class MetricRecord:
    """Data class for storing performance metric records."""
    name: str
    start_time: float
    end_time: float = 0
    duration: float = 0
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True) -> None:
        """Complete the metric record with an end time and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success


class PerformanceMonitor:
    """
    Performance monitoring service that tracks execution times and resource usage.
    
    Features:
    - Function/method execution time tracking
    - Async operation performance monitoring
    - Service health metrics
    - Bottleneck identification
    - Performance data persistence
    """
    
    def __init__(self, export_dir: str = "exports/metrics"):
        """Initialize the performance monitor."""
        self.metrics: Dict[str, List[MetricRecord]] = {}
        self.export_dir = export_dir
        
        # Create export directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
        logger.info("Performance monitoring initialized")
    
    def record_metric(self, name: str, **metadata) -> MetricRecord:
        """Start recording a new metric with the given name and metadata."""
        record = MetricRecord(name=name, start_time=time.time(), metadata=metadata)
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(record)
        return record
    
    @contextmanager
    def measure(self, operation_name: str, **metadata):
        """Context manager to measure the execution time of a block of code."""
        record = self.record_metric(operation_name, **metadata)
        try:
            yield record
            record.complete(True)
        except Exception as e:
            record.complete(False)
            record.metadata["error"] = str(e)
            record.metadata["traceback"] = traceback.format_exc()
            raise
    
    async def measure_async(self, operation_name: str, coro, **metadata):
        """Measure the execution time of an async coroutine."""
        record = self.record_metric(operation_name, **metadata)
        try:
            result = await coro
            record.complete(True)
            return result
        except Exception as e:
            record.complete(False)
            record.metadata["error"] = str(e)
            record.metadata["traceback"] = traceback.format_exc()
            raise
    
    def measure_function(self, func: F) -> F:
        """Decorator to measure the execution time of a function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.measure(func.__name__):
                return func(*args, **kwargs)
        return wrapper  # type: ignore
    
    def measure_async_function(self, func: AFT) -> AFT:
        """Decorator to measure the execution time of an async function."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            record = self.record_metric(func.__name__)
            try:
                result = await func(*args, **kwargs)
                record.complete(True)
                return result
            except Exception as e:
                record.complete(False)
                record.metadata["error"] = str(e)
                record.metadata["traceback"] = traceback.format_exc()
                raise
        return wrapper  # type: ignore
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all recorded metrics."""
        summary = {}
        
        for name, records in self.metrics.items():
            durations = [record.duration for record in records if record.success]
            if not durations:
                summary[name] = {
                    "count": 0,
                    "success_rate": 0,
                    "avg_duration": 0,
                    "min_duration": 0,
                    "max_duration": 0,
                    "median_duration": 0
                }
                continue
                
            success_count = sum(1 for record in records if record.success)
            
            summary[name] = {
                "count": len(records),
                "success_rate": success_count / len(records) if records else 0,
                "avg_duration": statistics.mean(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "median_duration": statistics.median(durations) if durations else 0
            }
        
        return summary
    
    def export_metrics(self) -> str:
        """Export all metrics to a JSON file and return the file path."""
        summary = self.get_metrics_summary()
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.export_dir, f"metrics_{timestamp}.json")
        
        # Convert to serializable format
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "raw_metrics": {
                name: [
                    {
                        "start_time": record.start_time,
                        "end_time": record.end_time,
                        "duration": record.duration,
                        "success": record.success,
                        "metadata": record.metadata
                    }
                    for record in records
                ]
                for name, records in self.metrics.items()
            }
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported performance metrics to {filepath}")
        return filepath
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = {}
        logger.info("Performance metrics reset")
    
    def identify_bottlenecks(self, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """Identify operations that are taking longer than the threshold."""
        bottlenecks = []
        
        for name, records in self.metrics.items():
            durations = [record.duration for record in records if record.success]
            if not durations:
                continue
            
            avg_duration = statistics.mean(durations)
            
            if avg_duration > threshold_seconds:
                bottlenecks.append({
                    "operation": name,
                    "avg_duration": avg_duration,
                    "count": len(records),
                    "impact_score": avg_duration * len(records)
                })
        
        # Sort by impact score (duration * frequency)
        bottlenecks.sort(key=lambda x: x["impact_score"], reverse=True)
        return bottlenecks


# Create a global instance for easy import
performance_monitor = PerformanceMonitor()

# Convenience decorators
def measure(func: F) -> F:
    """Decorator to measure function execution time using the global monitor."""
    return performance_monitor.measure_function(func)

def measure_async(func: AFT) -> AFT:
    """Decorator to measure async function execution time using the global monitor."""
    return performance_monitor.measure_async_function(func)
