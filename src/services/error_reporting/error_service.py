"""
Centralized Error Reporting Service

Provides standardized error reporting across all services with:
- Consistent error format
- Severity levels
- Context-specific error messages
- Error correlation IDs
- Comprehensive logging
- Error analytics
"""
import logging
import uuid
import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # System failure, immediate action required
    ERROR = "error"        # Feature failure, user impact
    WARNING = "warning"    # Degraded functionality, fallback in use
    INFO = "info"          # Notable events, non-critical


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    LLM_SERVICE = "llm_service"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


class ErrorReport:
    """Structured error report."""

    def __init__(
        self,
        correlation_id: str,
        severity: ErrorSeverity,
        category: ErrorCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """Initialize error report.

        Args:
            correlation_id: Unique ID for tracking related errors
            severity: Error severity level
            category: Error category
            message: User-friendly error message
            details: Additional error context
            exception: Original exception if any
            user_id: User ID if authenticated
            endpoint: API endpoint where error occurred
            request_id: Request ID if available
            timestamp: Error timestamp (defaults to now)
        """
        self.correlation_id = correlation_id
        self.severity = severity
        self.category = category
        self.message = message
        self.details = details or {}
        self.exception = exception
        self.user_id = user_id
        self.endpoint = endpoint
        self.request_id = request_id
        self.timestamp = timestamp or datetime.utcnow()

        # Add stack trace if exception provided
        if exception:
            self.details['exception_type'] = type(exception).__name__
            self.details['exception_message'] = str(exception)
            self.details['stack_trace'] = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error report to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'correlation_id': self.correlation_id,
            'severity': self.severity.value,
            'category': self.category.value,
            'message': self.message,
            'details': self.details,
            'user_id': self.user_id,
            'endpoint': self.endpoint,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat()
        }

    def to_json(self) -> str:
        """Convert error report to JSON.

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=2)


class ErrorReportingService:
    """
    Centralized error reporting service.

    Provides consistent error handling and reporting across the application.
    """

    # Error message templates
    ERROR_MESSAGES = {
        # Authentication errors
        'auth.invalid_credentials': 'Invalid email or password',
        'auth.token_expired': 'Your session has expired. Please log in again',
        'auth.token_invalid': 'Invalid authentication token',
        'auth.account_disabled': 'Your account has been disabled',
        'auth.account_not_found': 'Account not found',

        # Authorization errors
        'authz.insufficient_permissions': 'You do not have permission to perform this action',
        'authz.resource_access_denied': 'Access to this resource is denied',
        'authz.role_required': 'This action requires a different role',

        # Validation errors
        'validation.required_field': 'Required field is missing: {field}',
        'validation.invalid_format': 'Invalid format for {field}',
        'validation.value_out_of_range': 'Value for {field} is out of acceptable range',
        'validation.duplicate_entry': 'A record with this {field} already exists',

        # Database errors
        'db.connection_failed': 'Database connection failed',
        'db.query_failed': 'Database query failed',
        'db.record_not_found': '{resource} not found',
        'db.constraint_violation': 'Data integrity constraint violated',

        # External API errors
        'api.request_failed': 'External API request failed: {api_name}',
        'api.quota_exceeded': 'API quota exceeded for {api_name}',
        'api.timeout': 'Request to {api_name} timed out',
        'api.invalid_response': 'Invalid response from {api_name}',

        # LLM Service errors
        'llm.provider_unavailable': 'LLM provider {provider} is currently unavailable',
        'llm.all_providers_failed': 'All LLM providers failed',
        'llm.context_length_exceeded': 'Request exceeds maximum context length',
        'llm.rate_limit': 'LLM provider rate limit exceeded',

        # File system errors
        'fs.file_not_found': 'File not found: {path}',
        'fs.permission_denied': 'Permission denied: {path}',
        'fs.write_failed': 'Failed to write file: {path}',

        # Rate limiting
        'rate_limit.exceeded': 'Rate limit exceeded. Please try again later',

        # Business logic errors
        'business.invalid_state_transition': 'Invalid state transition from {from_state} to {to_state}',
        'business.operation_not_allowed': 'Operation not allowed in current state',
        'business.resource_locked': 'Resource is currently locked by another operation',

        # Generic
        'generic.internal_error': 'An internal error occurred. Please try again',
        'generic.not_implemented': 'This feature is not yet implemented',
        'generic.service_unavailable': 'Service temporarily unavailable'
    }

    def __init__(self):
        """Initialize error reporting service."""
        self.error_history: List[ErrorReport] = []
        self.max_history = 1000  # Keep last 1000 errors in memory

    def report_error(
        self,
        message_key: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None,
        format_args: Optional[Dict[str, Any]] = None
    ) -> ErrorReport:
        """Report an error.

        Args:
            message_key: Message template key or custom message
            severity: Error severity level
            category: Error category
            details: Additional error context
            exception: Original exception if any
            user_id: User ID if authenticated
            endpoint: API endpoint where error occurred
            request_id: Request ID if available
            format_args: Arguments for message formatting

        Returns:
            ErrorReport object
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Get message template or use key as message
        message_template = self.ERROR_MESSAGES.get(message_key, message_key)

        # Format message if args provided
        if format_args:
            try:
                message = message_template.format(**format_args)
            except KeyError as e:
                message = f"{message_template} (missing format arg: {e})"
        else:
            message = message_template

        # Create error report
        error_report = ErrorReport(
            correlation_id=correlation_id,
            severity=severity,
            category=category,
            message=message,
            details=details,
            exception=exception,
            user_id=user_id,
            endpoint=endpoint,
            request_id=request_id
        )

        # Log error
        self._log_error(error_report)

        # Store in history
        self._store_error(error_report)

        return error_report

    def _log_error(self, error_report: ErrorReport) -> None:
        """Log error to application logs.

        Args:
            error_report: Error report to log
        """
        log_data = {
            'correlation_id': error_report.correlation_id,
            'severity': error_report.severity.value,
            'category': error_report.category.value,
            'message': error_report.message,
            'user_id': error_report.user_id,
            'endpoint': error_report.endpoint,
            'request_id': error_report.request_id
        }

        log_message = f"[{error_report.correlation_id}] {error_report.message}"

        if error_report.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra=log_data)
        elif error_report.severity == ErrorSeverity.ERROR:
            logger.error(log_message, extra=log_data, exc_info=error_report.exception)
        elif error_report.severity == ErrorSeverity.WARNING:
            logger.warning(log_message, extra=log_data)
        else:
            logger.info(log_message, extra=log_data)

    def _store_error(self, error_report: ErrorReport) -> None:
        """Store error in history.

        Args:
            error_report: Error report to store
        """
        self.error_history.append(error_report)

        # Trim history if needed
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

    def get_error_by_correlation_id(self, correlation_id: str) -> Optional[ErrorReport]:
        """Get error by correlation ID.

        Args:
            correlation_id: Correlation ID to search for

        Returns:
            ErrorReport if found, None otherwise
        """
        for error in reversed(self.error_history):
            if error.correlation_id == correlation_id:
                return error
        return None

    def get_analytics(
        self,
        hours: int = 24,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None
    ) -> Dict[str, Any]:
        """Get error analytics.

        Args:
            hours: Number of hours to analyze
            severity: Filter by severity
            category: Filter by category

        Returns:
            Dictionary with analytics data
        """
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)

        # Filter errors
        filtered_errors = [
            error for error in self.error_history
            if error.timestamp.timestamp() >= cutoff_time
            and (severity is None or error.severity == severity)
            and (category is None or error.category == category)
        ]

        # Calculate statistics
        severity_counts = {}
        category_counts = {}
        endpoint_counts = {}

        for error in filtered_errors:
            # Count by severity
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1

            # Count by category
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1

            # Count by endpoint
            if error.endpoint:
                endpoint_counts[error.endpoint] = endpoint_counts.get(error.endpoint, 0) + 1

        return {
            'period_hours': hours,
            'total_errors': len(filtered_errors),
            'by_severity': severity_counts,
            'by_category': category_counts,
            'by_endpoint': endpoint_counts,
            'recent_errors': [
                {
                    'correlation_id': error.correlation_id,
                    'severity': error.severity.value,
                    'category': error.category.value,
                    'message': error.message,
                    'timestamp': error.timestamp.isoformat()
                }
                for error in filtered_errors[-10:]  # Last 10 errors
            ]
        }

    def clear_history(self) -> int:
        """Clear error history.

        Returns:
            Number of errors cleared
        """
        count = len(self.error_history)
        self.error_history.clear()
        return count


# Singleton instance
_error_service = None


def get_error_service() -> ErrorReportingService:
    """Get the global error reporting service instance.

    Returns:
        ErrorReportingService instance
    """
    global _error_service
    if _error_service is None:
        _error_service = ErrorReportingService()
    return _error_service
