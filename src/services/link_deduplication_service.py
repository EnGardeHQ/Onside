"""Link deduplication service for detecting and merging duplicate links.

This module provides URL normalization, fuzzy matching, and deduplication
capabilities for link management.
"""
import logging
import re
from typing import List, Dict, Optional, Tuple, Set
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from src.models.link import Link

logger = logging.getLogger(__name__)


class LinkDeduplicationService:
    """Service for detecting and managing duplicate links.

    Provides URL normalization, similarity detection, and deduplication
    with configurable similarity thresholds.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize the link deduplication service.

        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider links as duplicates
        """
        self.similarity_threshold = similarity_threshold

    def normalize_url(self, url: str) -> str:
        """Normalize a URL for comparison.

        Normalization includes:
        - Converting to lowercase
        - Removing trailing slashes
        - Sorting query parameters
        - Removing common tracking parameters
        - Removing fragments
        - Removing www prefix

        Args:
            url: URL to normalize

        Returns:
            Normalized URL string
        """
        try:
            # Parse URL
            parsed = urlparse(url.lower().strip())

            # Remove common tracking parameters
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'msclkid', '_ga', 'mc_cid', 'mc_eid'
            }

            # Parse and filter query parameters
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items()
                if k.lower() not in tracking_params
            }

            # Sort parameters for consistency
            sorted_query = urlencode(sorted(filtered_params.items()), doseq=True)

            # Remove 'www.' from netloc
            netloc = parsed.netloc
            if netloc.startswith('www.'):
                netloc = netloc[4:]

            # Remove trailing slashes from path
            path = parsed.path.rstrip('/')
            if not path:
                path = '/'

            # Rebuild URL without fragment
            normalized = urlunparse((
                parsed.scheme or 'https',
                netloc,
                path,
                parsed.params,
                sorted_query,
                ''  # No fragment
            ))

            return normalized

        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {str(e)}")
            return url.lower().strip()

    def calculate_similarity(self, url1: str, url2: str) -> float:
        """Calculate similarity score between two URLs.

        Uses a combination of normalized URL comparison and fuzzy string matching.

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            Similarity score between 0 and 1
        """
        # Normalize URLs
        norm1 = self.normalize_url(url1)
        norm2 = self.normalize_url(url2)

        # Exact match after normalization
        if norm1 == norm2:
            return 1.0

        # Parse normalized URLs
        parsed1 = urlparse(norm1)
        parsed2 = urlparse(norm2)

        # Domain must match
        if parsed1.netloc != parsed2.netloc:
            return 0.0

        # Compare paths using sequence matcher
        path_similarity = SequenceMatcher(None, parsed1.path, parsed2.path).ratio()

        # Compare query parameters
        params1 = set(parse_qs(parsed1.query).keys())
        params2 = set(parse_qs(parsed2.query).keys())

        if params1 or params2:
            param_similarity = len(params1 & params2) / len(params1 | params2) if (params1 | params2) else 1.0
        else:
            param_similarity = 1.0

        # Weight: path is more important than query params
        overall_similarity = (path_similarity * 0.7) + (param_similarity * 0.3)

        return overall_similarity

    def find_duplicates_for_url(
        self,
        db: Session,
        url: str,
        company_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Tuple[Link, float]]:
        """Find potential duplicates for a given URL.

        Args:
            db: Database session
            url: URL to find duplicates for
            company_id: Optional company ID to scope search
            limit: Maximum number of duplicates to return

        Returns:
            List of (Link, similarity_score) tuples
        """
        # Normalize the input URL
        normalized = self.normalize_url(url)
        parsed = urlparse(normalized)
        domain = parsed.netloc

        # Query links from the same domain
        query = db.query(Link).filter(Link.url.ilike(f'%{domain}%'))

        if company_id:
            query = query.filter(Link.company_id == company_id)

        candidate_links = query.all()

        # Calculate similarity for each candidate
        duplicates = []
        for link in candidate_links:
            if link.url == url:
                continue  # Skip exact match

            similarity = self.calculate_similarity(url, link.url)

            if similarity >= self.similarity_threshold:
                duplicates.append((link, similarity))

        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x[1], reverse=True)

        return duplicates[:limit]

    def find_all_duplicates(
        self,
        db: Session,
        company_id: Optional[int] = None,
        batch_size: int = 100
    ) -> List[Dict]:
        """Find all duplicate links in the database.

        Args:
            db: Database session
            company_id: Optional company ID to scope search
            batch_size: Number of links to process per batch

        Returns:
            List of duplicate groups with similarity scores
        """
        # Query all links
        query = db.query(Link)

        if company_id:
            query = query.filter(Link.company_id == company_id)

        all_links = query.all()

        # Group by normalized URL
        normalized_groups: Dict[str, List[Link]] = {}

        for link in all_links:
            normalized = self.normalize_url(link.url)

            if normalized not in normalized_groups:
                normalized_groups[normalized] = []

            normalized_groups[normalized].append(link)

        # Find groups with duplicates
        duplicate_groups = []

        for normalized_url, links in normalized_groups.items():
            if len(links) > 1:
                # Sort by creation date (oldest first)
                links.sort(key=lambda x: x.created_at)

                group = {
                    'normalized_url': normalized_url,
                    'count': len(links),
                    'canonical': links[0],  # Oldest link as canonical
                    'duplicates': links[1:],
                    'similarity': 1.0  # Exact match after normalization
                }

                duplicate_groups.append(group)

        # Also find fuzzy duplicates (similar but not exact after normalization)
        # This is computationally expensive, so we limit it
        processed_urls: Set[str] = set()

        for link in all_links[:batch_size]:
            if link.url in processed_urls:
                continue

            fuzzy_dupes = self.find_duplicates_for_url(
                db, link.url, company_id, limit=5
            )

            if fuzzy_dupes:
                processed_urls.add(link.url)
                for dupe_link, similarity in fuzzy_dupes:
                    processed_urls.add(dupe_link.url)

                group = {
                    'normalized_url': self.normalize_url(link.url),
                    'count': len(fuzzy_dupes) + 1,
                    'canonical': link,
                    'duplicates': [d[0] for d in fuzzy_dupes],
                    'similarity': fuzzy_dupes[0][1] if fuzzy_dupes else 1.0,
                    'fuzzy': True
                }

                duplicate_groups.append(group)

        return duplicate_groups

    def merge_duplicate_links(
        self,
        db: Session,
        canonical_id: int,
        duplicate_ids: List[int]
    ) -> Link:
        """Merge duplicate links into a canonical link.

        Args:
            db: Database session
            canonical_id: ID of the canonical link to keep
            duplicate_ids: List of duplicate link IDs to merge

        Returns:
            Updated canonical Link

        Raises:
            ValueError: If canonical link not found
        """
        # Get canonical link
        canonical = db.query(Link).filter(Link.id == canonical_id).first()

        if not canonical:
            raise ValueError(f"Canonical link not found: {canonical_id}")

        # Get duplicate links
        duplicates = (
            db.query(Link)
            .filter(Link.id.in_(duplicate_ids))
            .all()
        )

        # Merge metadata and tags
        merged_tags = set(canonical.tags or [])
        merged_sources = set()
        merged_sources.add(canonical.source if canonical.source else 'unknown')

        for duplicate in duplicates:
            # Merge tags
            if duplicate.tags:
                merged_tags.update(duplicate.tags)

            # Track sources
            if duplicate.source:
                merged_sources.add(duplicate.source)

            # Update click count
            if hasattr(canonical, 'click_count') and hasattr(duplicate, 'click_count'):
                canonical.click_count = (canonical.click_count or 0) + (duplicate.click_count or 0)

        # Update canonical with merged data
        canonical.tags = list(merged_tags) if merged_tags else None

        # Store merge information in metadata
        if not canonical.metadata:
            canonical.metadata = {}

        canonical.metadata['merged_from'] = [
            {
                'id': d.id,
                'url': d.url,
                'source': d.source
            }
            for d in duplicates
        ]
        canonical.metadata['merge_sources'] = list(merged_sources)
        canonical.metadata['merged_at'] = datetime.utcnow().isoformat()

        # Delete duplicates
        for duplicate in duplicates:
            db.delete(duplicate)

        # Commit changes
        db.commit()
        db.refresh(canonical)

        logger.info(
            f"Merged {len(duplicates)} duplicate links into canonical link {canonical_id}"
        )

        return canonical

    def generate_duplicate_report(
        self,
        db: Session,
        company_id: Optional[int] = None
    ) -> Dict:
        """Generate a report of duplicate links.

        Args:
            db: Database session
            company_id: Optional company ID to scope report

        Returns:
            Dict containing duplicate statistics and recommendations
        """
        duplicate_groups = self.find_all_duplicates(db, company_id)

        total_duplicates = sum(group['count'] - 1 for group in duplicate_groups)
        exact_duplicates = sum(
            group['count'] - 1
            for group in duplicate_groups
            if not group.get('fuzzy', False)
        )
        fuzzy_duplicates = sum(
            group['count'] - 1
            for group in duplicate_groups
            if group.get('fuzzy', False)
        )

        # Calculate potential savings
        query = db.query(Link)
        if company_id:
            query = query.filter(Link.company_id == company_id)
        total_links = query.count()

        savings_percentage = (total_duplicates / total_links * 100) if total_links > 0 else 0

        return {
            'summary': {
                'total_links': total_links,
                'total_duplicates': total_duplicates,
                'exact_duplicates': exact_duplicates,
                'fuzzy_duplicates': fuzzy_duplicates,
                'unique_links': total_links - total_duplicates,
                'savings_percentage': round(savings_percentage, 2)
            },
            'duplicate_groups': duplicate_groups[:50],  # Top 50 groups
            'recommendations': [
                {
                    'canonical_id': group['canonical'].id,
                    'canonical_url': group['canonical'].url,
                    'duplicate_ids': [d.id for d in group['duplicates']],
                    'count': group['count'],
                    'similarity': group['similarity']
                }
                for group in duplicate_groups
            ],
            'generated_at': datetime.utcnow().isoformat()
        }


# Import datetime
from datetime import datetime
