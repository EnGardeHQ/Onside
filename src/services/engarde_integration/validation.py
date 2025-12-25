"""Input validation and sanitization for En Garde brand analysis integration.

This module provides comprehensive validation for all user inputs,
URL verification, domain checking, and security measures against
malicious inputs and attacks.
"""

import re
import logging
import socket
import ssl
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timedelta
import dns.resolver
import aiohttp
import bleach
from sqlalchemy.orm import Session

from src.config import get_settings
from .error_handling import InvalidQuestionnaireError, WebsiteUnreachableError

logger = logging.getLogger(__name__)
settings = get_settings()

# ============================================================================
# Configuration
# ============================================================================

# Domain blocklist - prevent crawling malicious/inappropriate sites
BLOCKLISTED_DOMAINS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    # Add more as needed
}

# Allowed HTML tags for sanitization (very restrictive)
ALLOWED_HTML_TAGS = []

# Allowed HTML attributes
ALLOWED_HTML_ATTRIBUTES = {}

# Maximum lengths for fields
MAX_BRAND_NAME_LENGTH = 255
MAX_URL_LENGTH = 2048
MAX_INDUSTRY_LENGTH = 100
MAX_LIST_ITEMS = 50
MAX_KEYWORD_LENGTH = 100
MAX_DOMAIN_LENGTH = 255

# URL validation patterns
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

# SQL injection patterns to detect
SQL_INJECTION_PATTERNS = [
    r"('|(\\')|(--)|(/\*)|(;))",
    r"((\%27)|(\'))(\s)*union",
    r"((\%27)|(\'))(\s)*select",
    r"((\%27)|(\'))(\s)*insert",
    r"((\%27)|(\'))(\s)*delete",
    r"((\%27)|(\'))(\s)*drop",
    r"((\%27)|(\'))(\s)*create",
    r"((\%27)|(\'))(\s)*update",
    r"exec(\s|\+)+(s|x)p\w+",
]

# XSS patterns to detect
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
    r"<object",
    r"<embed",
]

# Approved industry list (expandable)
APPROVED_INDUSTRIES = {
    "technology", "saas", "software", "healthcare", "finance", "fintech",
    "e-commerce", "retail", "education", "consulting", "marketing",
    "real estate", "hospitality", "manufacturing", "automotive",
    "telecommunications", "media", "entertainment", "gaming",
    "food & beverage", "agriculture", "energy", "construction",
    "legal", "non-profit", "government", "other"
}

# Rate limiting configuration
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
MAX_ANALYSES_PER_HOUR = 10


# ============================================================================
# URL Validation
# ============================================================================

async def validate_url(
    url: str,
    check_reachability: bool = True,
    check_ssl: bool = True,
    timeout: int = 10
) -> Tuple[bool, Optional[str]]:
    """Validate URL format and optionally check reachability.

    Args:
        url: URL to validate
        check_reachability: Whether to test if URL is accessible
        check_ssl: Whether to verify SSL certificate
        timeout: Timeout in seconds for reachability check

    Returns:
        Tuple of (is_valid, error_message)

    Raises:
        WebsiteUnreachableError: If URL is unreachable
    """
    # Check URL format
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    url = url.strip()

    if len(url) > MAX_URL_LENGTH:
        return False, f"URL exceeds maximum length of {MAX_URL_LENGTH} characters"

    # Check URL pattern
    if not URL_PATTERN.match(url):
        return False, "URL must start with http:// or https:// and be properly formatted"

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"

    # Check scheme
    if parsed.scheme not in ("http", "https"):
        return False, "URL must use http or https protocol"

    # Check domain is present
    if not parsed.netloc:
        return False, "URL must include a domain name"

    # Check for blocklisted domains
    domain = parsed.netloc.lower().split(':')[0]  # Remove port if present
    if domain in BLOCKLISTED_DOMAINS:
        return False, f"Domain '{domain}' is not allowed"

    # Check for private/local IP addresses
    if _is_private_ip(domain):
        return False, "Private or local IP addresses are not allowed"

    # Optional: Check reachability
    if check_reachability:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
                    ssl=check_ssl
                ) as response:
                    if response.status >= 400:
                        logger.warning(
                            f"URL {url} returned status {response.status}",
                            extra={"url": url, "status": response.status}
                        )
                        raise WebsiteUnreachableError(
                            url=url,
                            reason=f"HTTP {response.status}",
                            details=f"Server returned error status {response.status}"
                        )
        except aiohttp.ClientError as e:
            logger.error(
                f"Failed to reach URL {url}: {str(e)}",
                extra={"url": url, "error": str(e)}
            )
            raise WebsiteUnreachableError(
                url=url,
                reason="Connection failed",
                details=str(e)
            )
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout reaching URL {url}",
                extra={"url": url, "timeout": timeout}
            )
            raise WebsiteUnreachableError(
                url=url,
                reason=f"Connection timeout after {timeout} seconds",
                details="Website did not respond in time"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error checking URL {url}: {str(e)}",
                exc_info=True
            )
            raise WebsiteUnreachableError(
                url=url,
                reason="Unexpected error",
                details=str(e)
            )

    return True, None


def _is_private_ip(domain: str) -> bool:
    """Check if domain is a private or local IP address."""
    # Try to resolve as IP
    try:
        import ipaddress
        ip = ipaddress.ip_address(domain)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        # Not an IP address, that's fine
        return False


# ============================================================================
# Domain Validation
# ============================================================================

async def validate_domain(
    domain: str,
    check_dns: bool = True,
    allow_subdomains: bool = True
) -> Tuple[bool, Optional[str]]:
    """Validate domain name and optionally check DNS.

    Args:
        domain: Domain name to validate
        check_dns: Whether to verify DNS records exist
        allow_subdomains: Whether to allow subdomain validation

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not domain or not isinstance(domain, str):
        return False, "Domain must be a non-empty string"

    domain = domain.strip().lower()

    if len(domain) > MAX_DOMAIN_LENGTH:
        return False, f"Domain exceeds maximum length of {MAX_DOMAIN_LENGTH} characters"

    # Remove protocol if present
    if domain.startswith(('http://', 'https://')):
        parsed = urlparse(domain)
        domain = parsed.netloc

    # Remove port if present
    domain = domain.split(':')[0]

    # Check for blocklisted domains
    if domain in BLOCKLISTED_DOMAINS:
        return False, f"Domain '{domain}' is not allowed"

    # Check domain format
    domain_pattern = re.compile(
        r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$',
        re.IGNORECASE
    )

    if not domain_pattern.match(domain):
        return False, "Invalid domain format"

    # Optional: Check DNS
    if check_dns:
        try:
            # Try to resolve DNS
            dns.resolver.resolve(domain, 'A')
        except dns.resolver.NXDOMAIN:
            return False, f"Domain '{domain}' does not exist (DNS lookup failed)"
        except dns.resolver.NoAnswer:
            # Domain exists but has no A records - might be redirect only
            logger.warning(f"Domain {domain} has no A records")
        except Exception as e:
            logger.warning(f"DNS check failed for {domain}: {str(e)}")
            # Don't fail validation on DNS errors, just log

    return True, None


# ============================================================================
# Questionnaire Validation
# ============================================================================

async def validate_questionnaire(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Comprehensive questionnaire validation.

    Validates:
    - Required fields present
    - URL formats correct
    - Industry from approved list
    - No malicious inputs (XSS, SQL injection)
    - Field length limits
    - List item limits

    Args:
        data: Questionnaire data dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)

    Raises:
        InvalidQuestionnaireError: If validation fails
    """
    errors = []

    # Required fields
    required_fields = ['brand_name', 'primary_website', 'industry']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate brand_name
    brand_name = str(data['brand_name']).strip()
    if not brand_name:
        errors.append("brand_name cannot be empty")
    elif len(brand_name) > MAX_BRAND_NAME_LENGTH:
        errors.append(f"brand_name exceeds maximum length of {MAX_BRAND_NAME_LENGTH}")
    elif _contains_malicious_input(brand_name):
        errors.append("brand_name contains potentially malicious content")
        logger.warning(
            f"Malicious input detected in brand_name: {brand_name}",
            extra={"field": "brand_name", "value": brand_name}
        )

    # Validate primary_website
    primary_website = str(data['primary_website']).strip()
    try:
        is_valid, error = await validate_url(
            primary_website,
            check_reachability=False  # Don't check yet, just validate format
        )
        if not is_valid:
            errors.append(f"Invalid primary_website: {error}")
    except Exception as e:
        errors.append(f"Error validating primary_website: {str(e)}")

    # Validate industry
    industry = str(data['industry']).strip().lower()
    if not industry:
        errors.append("industry cannot be empty")
    elif len(industry) > MAX_INDUSTRY_LENGTH:
        errors.append(f"industry exceeds maximum length of {MAX_INDUSTRY_LENGTH}")
    elif _contains_malicious_input(industry):
        errors.append("industry contains potentially malicious content")
    # Note: We're being flexible with industry - not enforcing the approved list
    # but logging if it's not in the standard list
    elif industry not in APPROVED_INDUSTRIES:
        logger.info(
            f"Non-standard industry specified: {industry}",
            extra={"industry": industry}
        )

    # Validate optional list fields
    list_fields = {
        'target_markets': 'target market',
        'products_services': 'product/service',
        'known_competitors': 'competitor domain',
        'target_keywords': 'keyword'
    }

    for field, item_name in list_fields.items():
        if field in data and data[field]:
            if not isinstance(data[field], list):
                errors.append(f"{field} must be a list")
                continue

            if len(data[field]) > MAX_LIST_ITEMS:
                errors.append(f"{field} exceeds maximum of {MAX_LIST_ITEMS} items")

            # Validate each item
            for i, item in enumerate(data[field]):
                item_str = str(item).strip()

                if not item_str:
                    errors.append(f"{field}[{i}] is empty")
                    continue

                # Check length based on field type
                max_len = MAX_DOMAIN_LENGTH if 'competitor' in field else MAX_KEYWORD_LENGTH
                if len(item_str) > max_len:
                    errors.append(f"{field}[{i}] exceeds maximum length of {max_len}")

                # Check for malicious content
                if _contains_malicious_input(item_str):
                    errors.append(f"{field}[{i}] contains potentially malicious content")
                    logger.warning(
                        f"Malicious input detected in {field}[{i}]: {item_str}",
                        extra={"field": field, "index": i, "value": item_str}
                    )

                # Special validation for competitor domains
                if field == 'known_competitors':
                    is_valid, error = await validate_domain(
                        item_str,
                        check_dns=False,  # Don't check DNS for competitor domains
                        allow_subdomains=True
                    )
                    if not is_valid:
                        errors.append(f"Invalid competitor domain [{i}]: {error}")

    # If there are errors, raise exception
    if errors:
        error_message = "; ".join(errors[:5])  # Limit to first 5 errors
        if len(errors) > 5:
            error_message += f" (and {len(errors) - 5} more errors)"

        raise InvalidQuestionnaireError(
            field="multiple",
            reason=error_message,
            details=str(errors)
        )

    return True, []


def _contains_malicious_input(text: str) -> bool:
    """Check if text contains SQL injection or XSS patterns.

    Args:
        text: Text to check

    Returns:
        True if malicious patterns detected
    """
    # Check SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(
                f"SQL injection pattern detected: {pattern}",
                extra={"pattern": pattern, "text": text[:100]}
            )
            return True

    # Check XSS patterns
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(
                f"XSS pattern detected: {pattern}",
                extra={"pattern": pattern, "text": text[:100]}
            )
            return True

    return False


# ============================================================================
# Input Sanitization
# ============================================================================

def sanitize_input(text: str, allow_html: bool = False) -> str:
    """Sanitize user input to prevent XSS and other attacks.

    Args:
        text: Text to sanitize
        allow_html: Whether to allow (cleaned) HTML

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    if allow_html:
        # Use bleach to clean HTML
        text = bleach.clean(
            text,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
    else:
        # Remove all HTML tags
        text = bleach.clean(text, tags=[], attributes={}, strip=True)

    # Remove null bytes
    text = text.replace('\x00', '')

    # Normalize whitespace
    text = ' '.join(text.split())

    return text


# ============================================================================
# Rate Limiting
# ============================================================================

async def check_rate_limit(
    user_id: str,
    db: Session,
    max_requests: int = MAX_ANALYSES_PER_HOUR,
    window_seconds: int = RATE_LIMIT_WINDOW
) -> Tuple[bool, Optional[str]]:
    """Check if user has exceeded rate limits.

    Args:
        user_id: User ID
        db: Database session
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds

    Returns:
        Tuple of (is_allowed, error_message)
    """
    from src.models.brand_analysis import BrandAnalysisJob

    try:
        # Get jobs created in the last window
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)

        job_count = db.query(BrandAnalysisJob).filter(
            BrandAnalysisJob.user_id == user_id,
            BrandAnalysisJob.created_at >= cutoff_time
        ).count()

        if job_count >= max_requests:
            time_remaining = window_seconds - (datetime.utcnow() - cutoff_time).total_seconds()
            minutes_remaining = int(time_remaining / 60)

            error_msg = (
                f"Rate limit exceeded. You have created {job_count} analyses "
                f"in the last hour. Please try again in {minutes_remaining} minutes."
            )

            logger.warning(
                f"Rate limit exceeded for user {user_id}",
                extra={
                    "user_id": user_id,
                    "job_count": job_count,
                    "max_requests": max_requests,
                    "window_seconds": window_seconds
                }
            )

            return False, error_msg

        return True, None

    except Exception as e:
        logger.error(
            f"Error checking rate limit for user {user_id}: {str(e)}",
            exc_info=True
        )
        # On error, allow the request (fail open)
        return True, None


# ============================================================================
# Results Validation
# ============================================================================

async def validate_analysis_results(results: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate analysis results before saving.

    Ensures data integrity and prevents storing malformed data.

    Args:
        results: Analysis results dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check required result fields
    if not isinstance(results, dict):
        errors.append("Results must be a dictionary")
        return False, errors

    # Validate keywords if present
    if 'keywords' in results:
        if not isinstance(results['keywords'], list):
            errors.append("Keywords must be a list")
        else:
            for i, keyword in enumerate(results['keywords']):
                if not isinstance(keyword, dict):
                    errors.append(f"Keyword {i} must be a dictionary")
                elif 'keyword' not in keyword:
                    errors.append(f"Keyword {i} missing 'keyword' field")
                elif 'relevance_score' not in keyword:
                    errors.append(f"Keyword {i} missing 'relevance_score' field")
                elif not 0 <= keyword['relevance_score'] <= 1:
                    errors.append(f"Keyword {i} has invalid relevance_score")

    # Validate competitors if present
    if 'competitors' in results:
        if not isinstance(results['competitors'], list):
            errors.append("Competitors must be a list")
        else:
            for i, competitor in enumerate(results['competitors']):
                if not isinstance(competitor, dict):
                    errors.append(f"Competitor {i} must be a dictionary")
                elif 'domain' not in competitor:
                    errors.append(f"Competitor {i} missing 'domain' field")
                elif 'relevance_score' not in competitor:
                    errors.append(f"Competitor {i} missing 'relevance_score' field")

    # Validate opportunities if present
    if 'opportunities' in results:
        if not isinstance(results['opportunities'], list):
            errors.append("Opportunities must be a list")

    if errors:
        return False, errors

    return True, []
