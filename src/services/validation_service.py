"""Data validation service for brand analysis results.

This service provides:
- Keyword quality validation
- Competitor domain validation
- URL format validation
- Data completeness checks
- Deduplication logic
"""
import re
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from urllib.parse import urlparse
from dataclasses import dataclass
from collections import defaultdict

import tldextract

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_value: Optional[Any] = None


@dataclass
class KeywordValidation:
    """Validation result for a keyword."""
    keyword: str
    is_valid: bool
    issues: List[str]
    normalized: str
    relevance_adjustment: float = 1.0  # Multiplier for relevance score


@dataclass
class CompetitorValidation:
    """Validation result for a competitor domain."""
    domain: str
    is_valid: bool
    issues: List[str]
    normalized_domain: str
    extracted_name: Optional[str] = None


class ValidationService:
    """Service for validating and cleaning brand analysis data.

    Validates:
    - Keyword quality (length, relevance, duplicates)
    - Competitor domain validity
    - URL formats
    - Data completeness
    """

    # Keyword validation rules
    MIN_KEYWORD_LENGTH = 2
    MAX_KEYWORD_LENGTH = 100
    MIN_WORD_LENGTH = 2  # Minimum length for individual words in multi-word keywords

    # Common stop words to flag (not necessarily invalid, but low quality)
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where',
        'why', 'how'
    }

    # Invalid keyword patterns
    INVALID_PATTERNS = [
        r'^\d+$',  # Only numbers
        r'^[^a-zA-Z0-9]+$',  # Only special characters
        r'(http|https|www\.)',  # URLs
        r'^\s+$',  # Only whitespace
    ]

    def __init__(self):
        """Initialize the validation service."""
        self.keyword_cache: Dict[str, KeywordValidation] = {}
        self.domain_cache: Dict[str, CompetitorValidation] = {}

    def validate_keyword(
        self,
        keyword: str,
        context: Optional[Dict[str, Any]] = None
    ) -> KeywordValidation:
        """Validate a single keyword.

        Args:
            keyword: Keyword to validate
            context: Optional context (e.g., source, industry)

        Returns:
            KeywordValidation result
        """
        # Check cache
        cache_key = keyword.lower().strip()
        if cache_key in self.keyword_cache:
            return self.keyword_cache[cache_key]

        issues = []
        normalized = keyword.strip().lower()
        relevance_adjustment = 1.0

        # Length validation
        if len(normalized) < self.MIN_KEYWORD_LENGTH:
            issues.append(f"Keyword too short (min {self.MIN_KEYWORD_LENGTH} characters)")

        if len(normalized) > self.MAX_KEYWORD_LENGTH:
            issues.append(f"Keyword too long (max {self.MAX_KEYWORD_LENGTH} characters)")
            normalized = normalized[:self.MAX_KEYWORD_LENGTH]

        # Pattern validation
        for pattern in self.INVALID_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                issues.append(f"Keyword matches invalid pattern: {pattern}")

        # Check for excessive special characters
        special_char_count = sum(1 for c in normalized if not c.isalnum() and not c.isspace())
        if special_char_count > len(normalized) * 0.3:
            issues.append("Keyword contains too many special characters")
            relevance_adjustment *= 0.7

        # Check word length in multi-word keywords
        words = normalized.split()
        short_words = [w for w in words if len(w) < self.MIN_WORD_LENGTH and w not in self.STOP_WORDS]
        if short_words:
            issues.append(f"Contains very short words: {', '.join(short_words)}")
            relevance_adjustment *= 0.9

        # Check for stop words dominance
        if len(words) > 1:
            stop_word_count = sum(1 for w in words if w in self.STOP_WORDS)
            stop_word_ratio = stop_word_count / len(words)
            if stop_word_ratio > 0.6:
                issues.append(f"Too many stop words ({stop_word_count}/{len(words)})")
                relevance_adjustment *= 0.8

        # Check for repetitive words
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        repeated_words = [w for w, count in word_counts.items() if count > 1]
        if repeated_words:
            issues.append(f"Repetitive words: {', '.join(repeated_words)}")
            relevance_adjustment *= 0.85

        is_valid = len(issues) == 0 or all('too' not in issue.lower() for issue in issues)

        result = KeywordValidation(
            keyword=keyword,
            is_valid=is_valid,
            issues=issues,
            normalized=normalized,
            relevance_adjustment=relevance_adjustment
        )

        # Cache result
        self.keyword_cache[cache_key] = result

        return result

    def validate_keywords_batch(
        self,
        keywords: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Validate and deduplicate a batch of keywords.

        Args:
            keywords: List of keyword dicts with 'keyword' and other fields

        Returns:
            Tuple of (valid_keywords, duplicate_keywords)
        """
        seen_normalized: Set[str] = set()
        valid_keywords = []
        duplicates = []

        for kw_data in keywords:
            keyword = kw_data.get('keyword', '')

            # Validate
            validation = self.validate_keyword(keyword)

            if not validation.is_valid:
                logger.warning(f"Invalid keyword '{keyword}': {validation.issues}")
                continue

            # Check for duplicates
            if validation.normalized in seen_normalized:
                duplicates.append(keyword)
                logger.debug(f"Duplicate keyword: {keyword}")
                continue

            seen_normalized.add(validation.normalized)

            # Add to valid keywords with adjusted relevance
            kw_dict = kw_data.copy()
            kw_dict['keyword'] = validation.normalized  # Use normalized version

            # Adjust relevance score if present
            if 'relevance_score' in kw_dict:
                kw_dict['relevance_score'] *= validation.relevance_adjustment

            valid_keywords.append(kw_dict)

        logger.info(
            f"Keyword validation: {len(valid_keywords)} valid, "
            f"{len(duplicates)} duplicates, "
            f"{len(keywords) - len(valid_keywords) - len(duplicates)} invalid"
        )

        return valid_keywords, duplicates

    def validate_domain(self, domain: str) -> CompetitorValidation:
        """Validate a competitor domain.

        Args:
            domain: Domain to validate

        Returns:
            CompetitorValidation result
        """
        # Check cache
        cache_key = domain.lower().strip()
        if cache_key in self.domain_cache:
            return self.domain_cache[cache_key]

        issues = []
        normalized = domain.strip().lower()

        # Remove protocol if present
        if normalized.startswith(('http://', 'https://')):
            normalized = urlparse(f"http://{normalized}").netloc or normalized

        # Remove www prefix
        if normalized.startswith('www.'):
            normalized = normalized[4:]

        # Extract domain parts
        extracted = tldextract.extract(normalized)

        # Validation checks
        if not extracted.domain:
            issues.append("Invalid domain format - no domain name found")

        if not extracted.suffix:
            issues.append("Invalid domain format - no TLD found")

        # Check for suspicious patterns
        if '..' in normalized:
            issues.append("Domain contains consecutive dots")

        if normalized.endswith('.'):
            issues.append("Domain ends with a dot")
            normalized = normalized.rstrip('.')

        # Check for IP addresses
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', normalized):
            issues.append("Domain is an IP address (not recommended)")

        # Check for localhost
        if 'localhost' in normalized or '127.0.0.1' in normalized:
            issues.append("Domain is localhost")

        # Reconstruct normalized domain
        if extracted.domain and extracted.suffix:
            normalized_domain = f"{extracted.domain}.{extracted.suffix}"
            if extracted.subdomain and extracted.subdomain != 'www':
                normalized_domain = f"{extracted.subdomain}.{normalized_domain}"
        else:
            normalized_domain = normalized

        # Extract brand name from domain
        brand_name = extracted.domain.replace('-', ' ').replace('_', ' ').title() if extracted.domain else None

        is_valid = len(issues) == 0 or all('invalid' not in issue.lower() for issue in issues)

        result = CompetitorValidation(
            domain=domain,
            is_valid=is_valid,
            issues=issues,
            normalized_domain=normalized_domain,
            extracted_name=brand_name
        )

        # Cache result
        self.domain_cache[cache_key] = result

        return result

    def validate_competitors_batch(
        self,
        competitors: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Validate and deduplicate a batch of competitors.

        Args:
            competitors: List of competitor dicts with 'domain' and other fields

        Returns:
            Tuple of (valid_competitors, duplicate_domains)
        """
        seen_domains: Set[str] = set()
        valid_competitors = []
        duplicates = []

        for comp_data in competitors:
            domain = comp_data.get('domain', '')

            # Validate
            validation = self.validate_domain(domain)

            if not validation.is_valid:
                logger.warning(f"Invalid domain '{domain}': {validation.issues}")
                continue

            # Check for duplicates
            if validation.normalized_domain in seen_domains:
                duplicates.append(domain)
                logger.debug(f"Duplicate domain: {domain}")
                continue

            seen_domains.add(validation.normalized_domain)

            # Add to valid competitors
            comp_dict = comp_data.copy()
            comp_dict['domain'] = validation.normalized_domain  # Use normalized version

            # Set name if not present
            if not comp_dict.get('name') and validation.extracted_name:
                comp_dict['name'] = validation.extracted_name

            valid_competitors.append(comp_dict)

        logger.info(
            f"Competitor validation: {len(valid_competitors)} valid, "
            f"{len(duplicates)} duplicates, "
            f"{len(competitors) - len(valid_competitors) - len(duplicates)} invalid"
        )

        return valid_competitors, duplicates

    def validate_url(self, url: str) -> ValidationResult:
        """Validate a URL format.

        Args:
            url: URL to validate

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        cleaned_url = url.strip()

        # Basic URL validation
        if not url:
            errors.append("URL is empty")
            return ValidationResult(False, errors, warnings)

        # Check for protocol
        if not cleaned_url.startswith(('http://', 'https://')):
            warnings.append("URL missing protocol, assuming https://")
            cleaned_url = f"https://{cleaned_url}"

        # Parse URL
        try:
            parsed = urlparse(cleaned_url)

            if not parsed.netloc:
                errors.append("URL has no domain")

            if not parsed.scheme:
                errors.append("URL has no scheme")

            # Validate scheme
            if parsed.scheme not in ['http', 'https']:
                errors.append(f"Invalid URL scheme: {parsed.scheme}")

            # Check for localhost
            if 'localhost' in parsed.netloc or '127.0.0.1' in parsed.netloc:
                warnings.append("URL points to localhost")

        except Exception as e:
            errors.append(f"URL parsing error: {str(e)}")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            cleaned_value=cleaned_url if is_valid else None
        )

    def validate_completeness(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> ValidationResult:
        """Validate data completeness.

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif data[field] is None:
                errors.append(f"Required field is null: {field}")
            elif isinstance(data[field], str) and not data[field].strip():
                errors.append(f"Required field is empty: {field}")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )

    def deduplicate_keywords(
        self,
        keywords: List[Dict[str, Any]],
        merge_strategy: str = 'highest_score'
    ) -> List[Dict[str, Any]]:
        """Deduplicate keywords with merge strategy.

        Args:
            keywords: List of keyword dicts
            merge_strategy: Strategy for merging duplicates
                - 'highest_score': Keep keyword with highest relevance score
                - 'most_recent': Keep most recently discovered
                - 'merge_data': Merge data from duplicates

        Returns:
            Deduplicated list of keywords
        """
        keyword_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Group by normalized keyword
        for kw in keywords:
            validation = self.validate_keyword(kw.get('keyword', ''))
            if validation.is_valid:
                keyword_groups[validation.normalized].append(kw)

        deduplicated = []

        for normalized, group in keyword_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
                continue

            # Apply merge strategy
            if merge_strategy == 'highest_score':
                best = max(group, key=lambda x: x.get('relevance_score', 0))
                deduplicated.append(best)

            elif merge_strategy == 'most_recent':
                best = max(group, key=lambda x: x.get('created_at', ''))
                deduplicated.append(best)

            elif merge_strategy == 'merge_data':
                # Merge data from all duplicates
                merged = group[0].copy()
                merged['relevance_score'] = max(x.get('relevance_score', 0) for x in group)
                merged['search_volume'] = max((x.get('search_volume') or 0) for x in group)

                # Combine sources
                sources = set()
                for kw in group:
                    if 'source' in kw:
                        sources.add(str(kw['source']))
                merged['sources'] = list(sources)

                deduplicated.append(merged)

        logger.info(f"Deduplicated {len(keywords)} keywords to {len(deduplicated)}")

        return deduplicated

    def deduplicate_competitors(
        self,
        competitors: List[Dict[str, Any]],
        merge_strategy: str = 'highest_score'
    ) -> List[Dict[str, Any]]:
        """Deduplicate competitors with merge strategy.

        Args:
            competitors: List of competitor dicts
            merge_strategy: Strategy for merging duplicates

        Returns:
            Deduplicated list of competitors
        """
        domain_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Group by normalized domain
        for comp in competitors:
            validation = self.validate_domain(comp.get('domain', ''))
            if validation.is_valid:
                domain_groups[validation.normalized_domain].append(comp)

        deduplicated = []

        for normalized_domain, group in domain_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
                continue

            # Apply merge strategy
            if merge_strategy == 'highest_score':
                best = max(group, key=lambda x: x.get('relevance_score', 0))
                deduplicated.append(best)

            elif merge_strategy == 'merge_data':
                # Merge data from all duplicates
                merged = group[0].copy()
                merged['relevance_score'] = max(x.get('relevance_score', 0) for x in group)
                merged['overlap_percentage'] = max((x.get('overlap_percentage') or 0) for x in group)

                # Use first non-null name
                for comp in group:
                    if comp.get('name'):
                        merged['name'] = comp['name']
                        break

                deduplicated.append(merged)

        logger.info(f"Deduplicated {len(competitors)} competitors to {len(deduplicated)}")

        return deduplicated

    def clear_cache(self):
        """Clear validation caches."""
        self.keyword_cache.clear()
        self.domain_cache.clear()
        logger.info("Validation cache cleared")
