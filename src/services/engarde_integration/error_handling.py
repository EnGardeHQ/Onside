"""Error handling framework for En Garde brand analysis integration.

This module provides comprehensive error handling, retry mechanisms,
and graceful degradation strategies for the brand analysis workflow.
"""

import logging
import asyncio
import functools
from typing import Dict, Any, Optional, Callable, TypeVar, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.brand_analysis import BrandAnalysisJob, AnalysisStatus

logger = logging.getLogger(__name__)

# Type variable for generic retry decorator
T = TypeVar('T')


# ============================================================================
# Custom Exception Classes
# ============================================================================

class BrandAnalysisError(Exception):
    """Base exception for all brand analysis errors.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error context
        suggestion: User-facing suggestion for resolution
        fallback_available: Whether a fallback option exists
    """

    def __init__(
        self,
        message: str,
        error_code: str = "BRAND_ANALYSIS_ERROR",
        details: Optional[str] = None,
        suggestion: Optional[str] = None,
        fallback_available: bool = False
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        self.suggestion = suggestion
        self.fallback_available = fallback_available
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "suggestion": self.suggestion,
                "fallback_available": self.fallback_available
            }
        }


class WebsiteUnreachableError(BrandAnalysisError):
    """Raised when the target website cannot be reached.

    Common causes:
    - Invalid URL
    - DNS resolution failure
    - Connection timeout
    - SSL certificate errors
    - Firewall/blocking
    """

    def __init__(
        self,
        url: str,
        reason: str,
        details: Optional[str] = None
    ):
        super().__init__(
            message=f"Could not reach website: {url}",
            error_code="WEBSITE_UNREACHABLE",
            details=details or reason,
            suggestion="Please verify the URL is correct and accessible, or try manual setup",
            fallback_available=True
        )
        self.url = url
        self.reason = reason


class InsufficientDataError(BrandAnalysisError):
    """Raised when insufficient data is available for analysis.

    Common causes:
    - Website has minimal content
    - Content is mostly images/videos
    - Content is behind authentication
    - JavaScript-heavy site with no fallback content
    """

    def __init__(
        self,
        data_type: str,
        threshold: int,
        actual: int,
        details: Optional[str] = None
    ):
        super().__init__(
            message=f"Insufficient {data_type} for analysis (found {actual}, need {threshold})",
            error_code="INSUFFICIENT_DATA",
            details=details,
            suggestion="Try adding manual keywords and competitors, or use industry defaults",
            fallback_available=True
        )
        self.data_type = data_type
        self.threshold = threshold
        self.actual = actual


class AnalysisTimeoutError(BrandAnalysisError):
    """Raised when analysis exceeds time limits.

    Common causes:
    - Large website with many pages
    - Slow website response times
    - SERP API rate limiting
    - System resource constraints
    """

    def __init__(
        self,
        operation: str,
        timeout_seconds: int,
        details: Optional[str] = None
    ):
        super().__init__(
            message=f"Analysis timed out during {operation} (limit: {timeout_seconds}s)",
            error_code="ANALYSIS_TIMEOUT",
            details=details,
            suggestion="Partial results have been saved. You can review what was found or retry with a smaller scope",
            fallback_available=True
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class InvalidQuestionnaireError(BrandAnalysisError):
    """Raised when questionnaire data is invalid or incomplete.

    Common causes:
    - Missing required fields
    - Invalid URL format
    - Malicious input detected
    - Data type mismatches
    """

    def __init__(
        self,
        field: str,
        reason: str,
        details: Optional[str] = None
    ):
        super().__init__(
            message=f"Invalid questionnaire field '{field}': {reason}",
            error_code="INVALID_QUESTIONNAIRE",
            details=details,
            suggestion=f"Please correct the {field} field and try again",
            fallback_available=False
        )
        self.field = field
        self.reason = reason


class SERPAPIError(BrandAnalysisError):
    """Raised when SERP API requests fail.

    Common causes:
    - API key invalid or expired
    - Rate limit exceeded
    - API service downtime
    - Invalid search parameters
    """

    def __init__(
        self,
        api_name: str,
        status_code: Optional[int] = None,
        reason: Optional[str] = None,
        details: Optional[str] = None
    ):
        super().__init__(
            message=f"SERP API error ({api_name}): {reason or 'Unknown error'}",
            error_code="SERP_API_ERROR",
            details=details or (f"HTTP {status_code}" if status_code else None),
            suggestion="Analysis will continue with cached data or skip SERP analysis",
            fallback_available=True
        )
        self.api_name = api_name
        self.status_code = status_code
        self.reason = reason


class ScrapingError(BrandAnalysisError):
    """Raised when web scraping fails.

    Common causes:
    - Anti-bot protection (Cloudflare, etc.)
    - Dynamic content requiring JavaScript
    - Malformed HTML
    - robots.txt blocking
    """

    def __init__(
        self,
        url: str,
        reason: str,
        status_code: Optional[int] = None,
        details: Optional[str] = None
    ):
        super().__init__(
            message=f"Failed to scrape {url}: {reason}",
            error_code="SCRAPING_ERROR",
            details=details or (f"HTTP {status_code}" if status_code else None),
            suggestion="Will attempt fallback scraping methods or use manual input",
            fallback_available=True
        )
        self.url = url
        self.reason = reason
        self.status_code = status_code


# ============================================================================
# Error Handler Functions
# ============================================================================

async def handle_analysis_failure(
    job_id: str,
    error: Exception,
    questionnaire: Dict[str, Any],
    db: Session,
    partial_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Handle analysis failure with graceful degradation.

    This function implements intelligent error recovery strategies:
    - Website unreachable → Suggest manual input
    - Insufficient data → Use industry defaults
    - Timeout → Return partial results
    - Unknown error → Log and notify

    Args:
        job_id: Brand analysis job ID
        error: The exception that occurred
        questionnaire: Original questionnaire data
        db: Database session
        partial_results: Any partial results collected before failure

    Returns:
        Dict containing error info and fallback suggestions
    """
    logger.error(
        f"Analysis failed for job {job_id}: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra={
            "job_id": job_id,
            "error_type": type(error).__name__,
            "questionnaire": questionnaire
        }
    )

    # Update job status with error
    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_id
    ).first()

    if not job:
        logger.error(f"Job {job_id} not found in database")
        return {
            "status": "error",
            "message": "Job not found"
        }

    # Determine error handling strategy based on error type
    if isinstance(error, WebsiteUnreachableError):
        return await _handle_website_unreachable(job, error, questionnaire, db)

    elif isinstance(error, InsufficientDataError):
        return await _handle_insufficient_data(job, error, questionnaire, db, partial_results)

    elif isinstance(error, AnalysisTimeoutError):
        return await _handle_timeout(job, error, db, partial_results)

    elif isinstance(error, SERPAPIError):
        return await _handle_serp_error(job, error, db, partial_results)

    elif isinstance(error, ScrapingError):
        return await _handle_scraping_error(job, error, questionnaire, db, partial_results)

    elif isinstance(error, InvalidQuestionnaireError):
        return await _handle_invalid_questionnaire(job, error, db)

    else:
        # Unknown error - log and fail gracefully
        return await _handle_unknown_error(job, error, db, partial_results)


async def _handle_website_unreachable(
    job: BrandAnalysisJob,
    error: WebsiteUnreachableError,
    questionnaire: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Handle website unreachable error."""
    job.status = AnalysisStatus.FAILED
    job.error_message = error.message
    job.results = {
        "error_code": error.error_code,
        "fallback_option": "manual_input",
        "suggestion": error.suggestion
    }
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.warning(
        f"Website unreachable for job {job.id}: {error.url}",
        extra={"job_id": str(job.id), "url": error.url}
    )

    return {
        "status": "failed",
        "error": error.to_dict(),
        "fallback": {
            "method": "manual_input",
            "message": "Please provide manual keywords and competitor information"
        }
    }


async def _handle_insufficient_data(
    job: BrandAnalysisJob,
    error: InsufficientDataError,
    questionnaire: Dict[str, Any],
    db: Session,
    partial_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle insufficient data error with industry defaults."""
    # Save partial results if available
    if partial_results:
        await save_partial_results(str(job.id), partial_results, db)

    job.status = AnalysisStatus.COMPLETED  # Mark as completed with limited data
    job.error_message = f"Warning: {error.message}"
    job.progress = 100
    job.results = {
        "warning": error.message,
        "data_quality": "limited",
        "partial_results": partial_results or {},
        "suggestion": error.suggestion
    }
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.warning(
        f"Insufficient data for job {job.id}, returning partial results",
        extra={"job_id": str(job.id), "data_type": error.data_type}
    )

    return {
        "status": "completed_with_warnings",
        "warning": error.to_dict(),
        "partial_results": partial_results,
        "suggestion": error.suggestion
    }


async def _handle_timeout(
    job: BrandAnalysisJob,
    error: AnalysisTimeoutError,
    db: Session,
    partial_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle timeout error by returning partial results."""
    # Save partial results
    if partial_results:
        await save_partial_results(str(job.id), partial_results, db)

    job.status = AnalysisStatus.COMPLETED  # Partial completion
    job.error_message = f"Warning: {error.message}"
    job.progress = 100
    job.results = {
        "warning": error.message,
        "partial": True,
        "operation_timeout": error.operation,
        "partial_results": partial_results or {},
        "suggestion": error.suggestion
    }
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.warning(
        f"Timeout for job {job.id} during {error.operation}, returning partial results",
        extra={"job_id": str(job.id), "operation": error.operation}
    )

    return {
        "status": "partial_completion",
        "warning": error.to_dict(),
        "partial_results": partial_results,
        "suggestion": "Review partial results or retry with smaller scope"
    }


async def _handle_serp_error(
    job: BrandAnalysisJob,
    error: SERPAPIError,
    db: Session,
    partial_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle SERP API error by continuing without SERP data."""
    # Continue analysis without SERP data
    if partial_results:
        await save_partial_results(str(job.id), partial_results, db)

    job.status = AnalysisStatus.COMPLETED
    job.error_message = f"Warning: SERP analysis unavailable - {error.message}"
    job.progress = 100
    job.results = {
        "warning": f"SERP analysis skipped: {error.message}",
        "serp_data_available": False,
        "partial_results": partial_results or {},
        "suggestion": "Results based on website content only"
    }
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.warning(
        f"SERP API error for job {job.id}, continuing without SERP data",
        extra={"job_id": str(job.id), "api_name": error.api_name}
    )

    return {
        "status": "completed_without_serp",
        "warning": error.to_dict(),
        "results": partial_results,
        "suggestion": "Analysis completed using website content only"
    }


async def _handle_scraping_error(
    job: BrandAnalysisJob,
    error: ScrapingError,
    questionnaire: Dict[str, Any],
    db: Session,
    partial_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle scraping error with fallback methods."""
    job.status = AnalysisStatus.FAILED
    job.error_message = error.message
    job.results = {
        "error_code": error.error_code,
        "url": error.url,
        "fallback_option": "manual_input",
        "partial_results": partial_results or {},
        "suggestion": error.suggestion
    }
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.error(
        f"Scraping failed for job {job.id}: {error.url}",
        extra={"job_id": str(job.id), "url": error.url, "status_code": error.status_code}
    )

    return {
        "status": "failed",
        "error": error.to_dict(),
        "fallback": {
            "method": "manual_input",
            "message": "Unable to scrape website. Please provide manual information."
        }
    }


async def _handle_invalid_questionnaire(
    job: BrandAnalysisJob,
    error: InvalidQuestionnaireError,
    db: Session
) -> Dict[str, Any]:
    """Handle invalid questionnaire error."""
    job.status = AnalysisStatus.FAILED
    job.error_message = error.message
    job.results = {
        "error_code": error.error_code,
        "invalid_field": error.field,
        "reason": error.reason,
        "suggestion": error.suggestion
    }
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.error(
        f"Invalid questionnaire for job {job.id}: {error.field}",
        extra={"job_id": str(job.id), "field": error.field, "reason": error.reason}
    )

    return {
        "status": "failed",
        "error": error.to_dict()
    }


async def _handle_unknown_error(
    job: BrandAnalysisJob,
    error: Exception,
    db: Session,
    partial_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle unknown error."""
    # Save partial results if available
    if partial_results:
        await save_partial_results(str(job.id), partial_results, db)

    job.status = AnalysisStatus.FAILED
    job.error_message = f"Unexpected error: {str(error)}"
    job.results = {
        "error_code": "UNKNOWN_ERROR",
        "error_type": type(error).__name__,
        "partial_results": partial_results or {},
        "suggestion": "An unexpected error occurred. Please try again or contact support."
    }
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.error(
        f"Unknown error for job {job.id}: {type(error).__name__}",
        exc_info=True,
        extra={"job_id": str(job.id)}
    )

    return {
        "status": "failed",
        "error": {
            "code": "UNKNOWN_ERROR",
            "message": "An unexpected error occurred",
            "details": str(error),
            "suggestion": "Please try again or contact support"
        },
        "partial_results": partial_results
    }


# ============================================================================
# Retry Mechanism
# ============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    fallback_value: Any = None
) -> Callable:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
        fallback_value: Value to return if all retries fail (None = raise)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_retries=3, exceptions=(ConnectionError,))
        async def fetch_data():
            # ... API call that might fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay}s delay. Error: {str(e)}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "delay": delay
                            }
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {str(e)}",
                            exc_info=True,
                            extra={
                                "function": func.__name__,
                                "max_retries": max_retries
                            }
                        )

            # All retries exhausted
            if fallback_value is not None:
                logger.info(f"Returning fallback value for {func.__name__}")
                return fallback_value
            else:
                raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay}s delay. Error: {str(e)}"
                        )
                        import time
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {str(e)}",
                            exc_info=True
                        )

            if fallback_value is not None:
                return fallback_value
            else:
                raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# Fallback Mechanisms
# ============================================================================

async def fallback_to_manual(job_id: str, db: Session) -> Dict[str, Any]:
    """Create manual input prompt for failed analysis.

    Args:
        job_id: Brand analysis job ID
        db: Database session

    Returns:
        Dict with manual input instructions
    """
    job = db.query(BrandAnalysisJob).filter(
        BrandAnalysisJob.id == job_id
    ).first()

    if not job:
        raise ValueError(f"Job {job_id} not found")

    manual_prompt = {
        "status": "manual_input_required",
        "message": "Automated analysis could not complete. Please provide manual information.",
        "required_inputs": {
            "keywords": {
                "description": "Enter 5-10 target keywords for your brand",
                "example": ["keyword1", "keyword2", "keyword3"]
            },
            "competitors": {
                "description": "List known competitor domains",
                "example": ["competitor1.com", "competitor2.com"]
            },
            "content_topics": {
                "description": "Describe key content topics for your industry",
                "example": ["topic1", "topic2"]
            }
        },
        "original_questionnaire": job.questionnaire
    }

    job.results = manual_prompt
    job.updated_at = datetime.utcnow()
    db.commit()

    logger.info(
        f"Created manual input prompt for job {job_id}",
        extra={"job_id": job_id}
    )

    return manual_prompt


async def save_partial_results(
    job_id: str,
    results: Dict[str, Any],
    db: Session
) -> bool:
    """Save partial analysis results.

    Args:
        job_id: Brand analysis job ID
        results: Partial results to save
        db: Database session

    Returns:
        True if successful, False otherwise
    """
    try:
        job = db.query(BrandAnalysisJob).filter(
            BrandAnalysisJob.id == job_id
        ).first()

        if not job:
            logger.error(f"Job {job_id} not found, cannot save partial results")
            return False

        # Merge with existing results
        existing_results = job.results or {}
        existing_results.update({
            "partial": True,
            "partial_data": results,
            "saved_at": datetime.utcnow().isoformat()
        })

        job.results = existing_results
        job.updated_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Saved partial results for job {job_id}",
            extra={
                "job_id": job_id,
                "result_keys": list(results.keys())
            }
        )

        return True

    except Exception as e:
        logger.error(
            f"Failed to save partial results for job {job_id}: {str(e)}",
            exc_info=True
        )
        return False
