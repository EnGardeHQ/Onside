"""
Standardized Error Reporting Service (S5-02)

This module implements a centralized error reporting service with consistent
error format, severity levels, and context-specific error messages as specified
in the Sprint 5 plan (S5-02).

Following Semantic Seed Venture Studio Coding Standards V2.0, this service:
1. Provides a consistent error format across all services
2. Includes severity levels for better error prioritization
3. Preserves context for easier debugging
4. Integrates with logging system for comprehensive error logs

Usage:
    from src.utilities.error_reporting import ErrorReporter, ErrorSeverity
    
    # Report an error
    ErrorReporter.report("Failed to connect to database", 
                        severity=ErrorSeverity.CRITICAL,
                        context={"service": "DatabaseService"})
"""
import logging
import traceback
import json
import uuid
import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
import functools
import asyncio
import inspect

# Configure logger
logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Severity levels for error reporting."""
    DEBUG = "DEBUG"          # Information useful for debugging
    INFO = "INFO"            # Informational messages
    WARNING = "WARNING"      # Potential issues that aren't critical
    ERROR = "ERROR"          # Errors that affect specific operations
    CRITICAL = "CRITICAL"    # Serious errors affecting the whole system
    FATAL = "FATAL"          # Unrecoverable errors requiring restart

class ErrorReport:
    """Structure for standardized error reports."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        error_id: Optional[str] = None
    ):
        """Initialize a new error report.
        
        Args:
            message: Human-readable error description
            severity: Error severity level
            exception: Original exception if applicable
            context: Additional contextual information
            error_id: Unique ID for this error (generated if not provided)
        """
        self.error_id = error_id or str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()
        self.message = message
        self.severity = severity
        
        # Exception details
        self.exception_type = type(exception).__name__ if exception else None
        self.exception_message = str(exception) if exception else None
        self.stack_trace = traceback.format_exc() if exception else None
        
        # Context
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error report to dictionary for serialization."""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "message": self.message,
            "severity": self.severity.value,
            "exception": {
                "type": self.exception_type,
                "message": self.exception_message,
                "stack_trace": self.stack_trace
            } if self.exception_type else None,
            "context": self.context
        }
    
    def to_json(self) -> str:
        """Convert error report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def log(self):
        """Log this error report using the appropriate log level."""
        # Map severity to logging level
        log_level_map = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.FATAL: logging.CRITICAL  # Python logging has no FATAL
        }
        
        # Construct log message
        log_message = f"Error {self.error_id}: {self.message}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            log_message += f" | Context: {context_str}"
        
        # Log with appropriate level
        logger.log(log_level_map[self.severity], log_message)
        
        # For critical and fatal errors, also log the stack trace if available
        if self.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.FATAL) and self.stack_trace:
            logger.critical(f"Stack trace for error {self.error_id}:\n{self.stack_trace}")


class ErrorReporter:
    """Central error reporting and handling service."""
    
    # Global error handlers for different severity levels
    _global_handlers: Dict[ErrorSeverity, List[Callable]] = {
        severity: [] for severity in ErrorSeverity
    }
    
    # Collection of recent errors for inspection
    _recent_errors: List[ErrorReport] = []
    _max_recent_errors = 100
    
    @classmethod
    def report(
        cls,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        error_id: Optional[str] = None
    ) -> ErrorReport:
        """Report an error.
        
        Args:
            message: Human-readable error description
            severity: Error severity level
            exception: Original exception if applicable
            context: Additional contextual information
            error_id: Unique ID for this error (generated if not provided)
            
        Returns:
            The created ErrorReport object
        """
        # Create error report
        error_report = ErrorReport(
            message=message,
            severity=severity,
            exception=exception,
            context=context,
            error_id=error_id
        )
        
        # Log the error
        error_report.log()
        
        # Store in recent errors
        cls._recent_errors.append(error_report)
        if len(cls._recent_errors) > cls._max_recent_errors:
            cls._recent_errors.pop(0)
        
        # Trigger severity-specific handlers
        for handler in cls._global_handlers[severity]:
            try:
                handler(error_report)
            except Exception as e:
                # Don't use report here to avoid potential infinite recursion
                logger.error(f"Error in error handler: {str(e)}")
        
        return error_report
    
    @classmethod
    def register_handler(cls, severity: ErrorSeverity, handler: Callable[[ErrorReport], None]):
        """Register a global handler for errors of a specific severity.
        
        Args:
            severity: The error severity level to handle
            handler: Callback function that takes an ErrorReport object
        """
        cls._global_handlers[severity].append(handler)
    
    @classmethod
    def get_recent_errors(cls, count: Optional[int] = None) -> List[ErrorReport]:
        """Get the most recent errors.
        
        Args:
            count: Maximum number of errors to return, or None for all
            
        Returns:
            List of recent ErrorReport objects
        """
        if count is None:
            return list(cls._recent_errors)
        return list(cls._recent_errors[-count:])
    
    @classmethod
    def clear_recent_errors(cls):
        """Clear the list of recent errors."""
        cls._recent_errors.clear()


def with_error_reporting(
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    context: Optional[Dict[str, Any]] = None
):
    """Decorator for functions to automatically report errors.
    
    Args:
        severity: Default severity for reported errors
        context: Additional context to include in error reports
        
    Returns:
        Decorated function that reports errors when they occur
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Build context dict with function info
                    error_context = {
                        "function": func.__name__,
                        "module": func.__module__,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                    if context:
                        error_context.update(context)
                    
                    # Report the error
                    ErrorReporter.report(
                        message=f"Error in async function {func.__name__}: {str(e)}",
                        severity=severity,
                        exception=e,
                        context=error_context
                    )
                    raise  # Re-raise the exception
            return async_wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Build context dict with function info
                    error_context = {
                        "function": func.__name__,
                        "module": func.__module__,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                    if context:
                        error_context.update(context)
                    
                    # Report the error
                    ErrorReporter.report(
                        message=f"Error in function {func.__name__}: {str(e)}",
                        severity=severity,
                        exception=e,
                        context=error_context
                    )
                    raise  # Re-raise the exception
            return wrapper
    return decorator


# Example handlers for different severity levels
def email_critical_errors(error_report: ErrorReport):
    """Example handler to send emails for critical errors."""
    # This would integrate with an email service
    logger.info(f"Would send email for critical error: {error_report.error_id}")

def log_to_monitoring_service(error_report: ErrorReport):
    """Example handler to send errors to a monitoring service."""
    # This would integrate with services like Sentry, Datadog, etc.
    logger.info(f"Would send to monitoring service: {error_report.error_id}")

# Register example handlers
ErrorReporter.register_handler(ErrorSeverity.CRITICAL, email_critical_errors)
ErrorReporter.register_handler(ErrorSeverity.ERROR, log_to_monitoring_service)
ErrorReporter.register_handler(ErrorSeverity.CRITICAL, log_to_monitoring_service)
