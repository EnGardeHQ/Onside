"""Mock SERP API responses for testing.

Provides deterministic SERP data for testing without making
actual API calls to SerpAPI or other SERP providers.
"""
from typing import Dict, Any, List, Optional
import hashlib


class MockSerpAPI:
    """Mock SERP API for testing."""

    def __init__(self):
        """Initialize mock SERP API."""
        self.call_count = 0
        self.call_history = []

    def search(
        self,
        keyword: str,
        location: str = "United States",
        language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """Mock SERP search.

        Args:
            keyword: Search keyword
            location: Geographic location
            language: Search language
            **kwargs: Additional parameters

        Returns:
            Mock SERP results
        """
        self.call_count += 1
        self.call_history.append({
            'keyword': keyword,
            'location': location,
            'language': language,
            'kwargs': kwargs
        })

        # Generate deterministic results based on keyword
        keyword_hash = int(hashlib.md5(keyword.encode()).hexdigest()[:8], 16)

        search_volume = (keyword_hash % 50000) + 1000
        difficulty = min((len(keyword) * 5.0), 100.0)
        cpc = round(0.5 + (difficulty / 100) * 3.0, 2)

        # Generate ranking domains
        base_domains = [
            'mailchimp.com',
            'hubspot.com',
            'activecampaign.com',
            'constantcontact.com',
            'sendinblue.com',
            'getresponse.com',
            'convertkit.com',
            'aweber.com',
            'drip.com',
            'klaviyo.com'
        ]

        # Rotate domains based on keyword hash
        start_index = keyword_hash % len(base_domains)
        ranking_domains = (
            base_domains[start_index:] + base_domains[:start_index]
        )[:10]

        # Generate organic results
        organic_results = []
        for i, domain in enumerate(ranking_domains[:10]):
            organic_results.append({
                'position': i + 1,
                'title': f'{keyword.title()} - {domain.split(".")[0].title()}',
                'link': f'https://{domain}/{keyword.replace(" ", "-")}',
                'domain': domain,
                'snippet': f'Learn about {keyword} with our comprehensive guide. {domain.split(".")[0].title()} offers the best {keyword} solutions.',
                'displayed_link': f'{domain} › {keyword.replace(" ", "-")}'
            })

        # SERP features
        serp_features = ['organic']
        if keyword_hash % 3 == 0:
            serp_features.append('featured_snippet')
        if keyword_hash % 2 == 0:
            serp_features.append('people_also_ask')
        if keyword_hash % 5 == 0:
            serp_features.append('ads')
        if keyword_hash % 7 == 0:
            serp_features.append('related_searches')

        return {
            'search_metadata': {
                'id': f'mock_{keyword_hash}',
                'status': 'Success',
                'created_at': '2025-12-24 12:00:00 UTC',
                'processed_at': '2025-12-24 12:00:01 UTC',
                'total_time_taken': 0.5
            },
            'search_parameters': {
                'q': keyword,
                'location': location,
                'hl': language,
                'gl': 'us',
                'google_domain': 'google.com',
                'device': 'desktop'
            },
            'search_information': {
                'total_results': keyword_hash % 10000000 + 100000,
                'time_taken_displayed': 0.45,
                'query_displayed': keyword
            },
            'organic_results': organic_results,
            'serp_features': serp_features,
            'keyword_metrics': {
                'search_volume': search_volume,
                'difficulty': difficulty,
                'cpc': cpc,
                'competition': 'HIGH' if difficulty > 70 else 'MEDIUM' if difficulty > 40 else 'LOW'
            },
            'related_searches': [
                f'{keyword} best practices',
                f'{keyword} tools',
                f'{keyword} guide',
                f'best {keyword}',
                f'{keyword} tips'
            ]
        }

    def get_batch_results(self, keywords: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get batch SERP results for multiple keywords.

        Args:
            keywords: List of keywords to search

        Returns:
            Dict mapping keywords to SERP results
        """
        results = {}
        for keyword in keywords:
            results[keyword] = self.search(keyword)
        return results

    def reset(self):
        """Reset call count and history."""
        self.call_count = 0
        self.call_history = []


class MockSerpAPIError:
    """Mock SERP API that raises errors for testing error handling."""

    def __init__(self, error_type: str = 'rate_limit'):
        """Initialize mock error API.

        Args:
            error_type: Type of error to simulate (rate_limit, network, invalid_key)
        """
        self.error_type = error_type

    def search(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """Raise mock error.

        Raises:
            Exception: Simulated API error
        """
        if self.error_type == 'rate_limit':
            raise Exception('Rate limit exceeded. Please try again later.')
        elif self.error_type == 'network':
            raise Exception('Network error: Connection timeout')
        elif self.error_type == 'invalid_key':
            raise Exception('Invalid API key')
        else:
            raise Exception(f'Unknown error: {self.error_type}')


def generate_mock_keyword_metrics(keyword: str) -> Dict[str, Any]:
    """Generate mock keyword metrics.

    Args:
        keyword: Keyword to generate metrics for

    Returns:
        Dict containing keyword metrics
    """
    keyword_hash = int(hashlib.md5(keyword.encode()).hexdigest()[:8], 16)

    search_volume = (keyword_hash % 50000) + 1000
    difficulty = min((len(keyword) * 5.0), 100.0)
    cpc = round(0.5 + (difficulty / 100) * 3.0, 2)
    competition = 'HIGH' if difficulty > 70 else 'MEDIUM' if difficulty > 40 else 'LOW'

    # Generate trend data
    trend = []
    base_volume = search_volume
    for month in range(12):
        variance = (keyword_hash + month) % 30 - 15  # -15 to +15
        monthly_volume = max(100, base_volume + (base_volume * variance / 100))
        trend.append({
            'month': f'2024-{month + 1:02d}',
            'search_volume': int(monthly_volume)
        })

    return {
        'keyword': keyword,
        'search_volume': search_volume,
        'difficulty': difficulty,
        'cpc': cpc,
        'competition': competition,
        'trend': trend,
        'related_keywords': [
            f'{keyword} best practices',
            f'{keyword} tools',
            f'{keyword} guide',
            f'best {keyword}',
            f'{keyword} tips'
        ]
    }


def generate_mock_competitor_analysis(
    domain: str,
    keywords: List[str]
) -> Dict[str, Any]:
    """Generate mock competitor analysis.

    Args:
        domain: Competitor domain
        keywords: List of keywords to analyze

    Returns:
        Dict containing competitor analysis
    """
    domain_hash = int(hashlib.md5(domain.encode()).hexdigest()[:8], 16)

    organic_traffic = (domain_hash % 500000) + 50000
    domain_authority = min((domain_hash % 100), 100)

    # Generate keyword rankings
    rankings = []
    for i, keyword in enumerate(keywords[:20]):
        keyword_hash = int(hashlib.md5(f'{domain}{keyword}'.encode()).hexdigest()[:8], 16)
        position = (keyword_hash % 50) + 1

        rankings.append({
            'keyword': keyword,
            'position': position,
            'url': f'https://{domain}/{keyword.replace(" ", "-")}',
            'search_volume': (keyword_hash % 50000) + 1000,
            'traffic': int(((keyword_hash % 50000) + 1000) * (1 / position))
        })

    return {
        'domain': domain,
        'domain_authority': domain_authority,
        'organic_traffic': organic_traffic,
        'total_keywords': len(keywords),
        'ranking_keywords': len([r for r in rankings if r['position'] <= 10]),
        'top_keywords': sorted(rankings, key=lambda x: x['traffic'], reverse=True)[:10],
        'keyword_overlap': rankings
    }
