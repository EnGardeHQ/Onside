"""Custom exceptions for the OnSide application."""


class DomainValidationError(ValueError):
    """Raised when domain validation fails."""
    pass


class ServiceUnavailableError(Exception):
    """Raised when an external service is unavailable.

    Attributes:
        service_name: Name of the unavailable service
        message: Error message
        retry_after: Optional seconds to wait before retrying
    """

    def __init__(
        self,
        service_name: str,
        message: str = "Service is currently unavailable",
        retry_after: int = None
    ):
        self.service_name = service_name
        self.message = message
        self.retry_after = retry_after
        super().__init__(f"{service_name}: {message}")
