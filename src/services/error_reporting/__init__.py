"""Error reporting service package."""

from .error_service import (
    ErrorReportingService,
    ErrorReport,
    ErrorSeverity,
    ErrorCategory,
    get_error_service
)

__all__ = [
    'ErrorReportingService',
    'ErrorReport',
    'ErrorSeverity',
    'ErrorCategory',
    'get_error_service'
]
