"""Fixtures for brand analysis tests.

This module provides reusable test data fixtures for testing the
En Garde brand analysis integration including:
- Sample questionnaires
- Mock HTML content for crawling
- Mock SERP results
- Sample keywords, competitors, and opportunities
- Database fixtures with sample data
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List
import pytest


# Sample Questionnaires

SAMPLE_QUESTIONNAIRE_MINIMAL = {
    'brand_name': 'Test Brand',
    'primary_website': 'https://testbrand.com',
    'industry': 'Technology',
    'target_markets': [],
    'products_services': [],
    'known_competitors': [],
    'target_keywords': []
}

SAMPLE_QUESTIONNAIRE_COMPLETE = {
    'brand_name': 'Acme Corp',
    'primary_website': 'https://acmecorp.com',
    'industry': 'SaaS Marketing Tools',
    'target_markets': ['United States', 'Canada', 'United Kingdom'],
    'products_services': [
        'Email Marketing Platform',
        'Social Media Scheduler',
        'Analytics Dashboard',
        'CRM Integration'
    ],
    'known_competitors': [
        'mailchimp.com',
        'hubspot.com',
        'activecampaign.com'
    ],
    'target_keywords': [
        'email marketing',
        'marketing automation',
        'crm software',
        'social media management'
    ]
}

SAMPLE_QUESTIONNAIRE_EDGE_CASE = {
    'brand_name': 'X',  # Single character
    'primary_website': 'https://x.co',  # Short domain
    'industry': 'AI',
    'target_markets': ['Global'],
    'products_services': ['Platform'],
    'known_competitors': [],
    'target_keywords': []
}


# Mock HTML Content for Web Scraping

MOCK_HTML_HOMEPAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Acme Corp - Best Email Marketing Software</title>
    <meta name="description" content="Leading email marketing platform for small businesses. Automate your campaigns with our easy-to-use marketing automation software.">
    <meta name="keywords" content="email marketing, marketing automation, email campaigns">
</head>
<body>
    <h1>Transform Your Email Marketing</h1>
    <h2>Powerful Marketing Automation for Growing Businesses</h2>
    <p>Acme Corp provides the best email marketing software for small and medium businesses. Our platform combines email marketing, marketing automation, and analytics in one easy-to-use tool.</p>
    <h2>Key Features</h2>
    <ul>
        <li>Email campaign builder with drag-and-drop editor</li>
        <li>Advanced segmentation and personalization</li>
        <li>Marketing automation workflows</li>
        <li>Real-time analytics and reporting</li>
        <li>CRM integration</li>
    </ul>
    <h3>Why Choose Acme Corp?</h3>
    <p>Unlike other email marketing platforms, we focus on small business needs. Our software is designed to be simple yet powerful, giving you professional marketing automation without the complexity.</p>
    <p>Start your free trial today and see why thousands of businesses trust Acme Corp for their email marketing needs.</p>
</body>
</html>
"""

MOCK_HTML_PRICING = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Pricing - Acme Corp Email Marketing</title>
    <meta name="description" content="Simple, transparent pricing for email marketing software. Plans starting at $29/month.">
</head>
<body>
    <h1>Email Marketing Pricing</h1>
    <h2>Choose the Perfect Plan for Your Business</h2>
    <div class="pricing-tier">
        <h3>Starter - $29/month</h3>
        <p>Perfect for small businesses just starting with email marketing.</p>
        <ul>
            <li>Up to 1,000 subscribers</li>
            <li>10,000 emails per month</li>
            <li>Email campaign builder</li>
            <li>Basic templates</li>
        </ul>
    </div>
    <div class="pricing-tier">
        <h3>Professional - $79/month</h3>
        <p>Best for growing businesses with advanced marketing automation needs.</p>
        <ul>
            <li>Up to 10,000 subscribers</li>
            <li>Unlimited emails</li>
            <li>Marketing automation workflows</li>
            <li>Advanced segmentation</li>
            <li>A/B testing</li>
            <li>CRM integration</li>
        </ul>
    </div>
</body>
</html>
"""

MOCK_HTML_FEATURES = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Features - Marketing Automation Platform</title>
</head>
<body>
    <h1>Email Marketing Features</h1>
    <h2>Everything You Need for Successful Email Campaigns</h2>

    <h3>Drag-and-Drop Email Builder</h3>
    <p>Create beautiful email campaigns with our intuitive email editor. No coding required.</p>

    <h3>Marketing Automation</h3>
    <p>Set up automated email workflows triggered by subscriber behavior. Welcome series, abandoned cart emails, and more.</p>

    <h3>Advanced Segmentation</h3>
    <p>Target the right audience with powerful list segmentation based on demographics, behavior, and engagement.</p>

    <h3>Real-Time Analytics</h3>
    <p>Track open rates, click rates, conversions, and ROI in real-time with detailed email marketing analytics.</p>

    <h3>A/B Testing</h3>
    <p>Optimize your email campaigns with built-in A/B testing for subject lines, content, and send times.</p>

    <h3>CRM Integration</h3>
    <p>Seamlessly integrate with popular CRM platforms to sync your contacts and track customer journeys.</p>
</body>
</html>
"""

MOCK_HTML_BLOG = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Email Marketing Best Practices - Acme Corp Blog</title>
</head>
<body>
    <h1>Email Marketing Blog</h1>

    <article>
        <h2>10 Email Marketing Best Practices for 2024</h2>
        <p>Learn the latest email marketing strategies to improve your open rates and conversions.</p>
        <p>Email marketing remains one of the most effective digital marketing channels. With an average ROI of $42 for every dollar spent, it's crucial to implement email marketing best practices.</p>
    </article>

    <article>
        <h2>How to Build Effective Marketing Automation Workflows</h2>
        <p>Step-by-step guide to creating automated email sequences that nurture leads and drive sales.</p>
        <p>Marketing automation allows you to send the right message at the right time without manual effort.</p>
    </article>

    <article>
        <h2>Email Segmentation Strategies That Work</h2>
        <p>Boost engagement with smart email list segmentation techniques.</p>
    </article>
</body>
</html>
"""


# Mock SERP Results

def generate_mock_serp_result(keyword: str) -> Dict[str, Any]:
    """Generate mock SERP result for a keyword."""
    return {
        'keyword': keyword,
        'search_volume': hash(keyword) % 50000 + 1000,  # Deterministic volume
        'difficulty': min((len(keyword) * 5.0), 100.0),
        'ranking_domains': [
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
        ],
        'serp_features': ['organic', 'featured_snippet', 'people_also_ask', 'ads'],
        'top_results': [
            {
                'position': 1,
                'domain': 'mailchimp.com',
                'title': f'Best {keyword} - Mailchimp',
                'url': f'https://mailchimp.com/{keyword.replace(" ", "-")}'
            },
            {
                'position': 2,
                'domain': 'hubspot.com',
                'title': f'{keyword.title()} Guide - HubSpot',
                'url': f'https://hubspot.com/marketing/{keyword.replace(" ", "-")}'
            },
            {
                'position': 3,
                'domain': 'activecampaign.com',
                'title': f'{keyword} Platform - ActiveCampaign',
                'url': f'https://activecampaign.com/{keyword.replace(" ", "-")}'
            }
        ]
    }


MOCK_SERP_RESULTS = {
    'email marketing': generate_mock_serp_result('email marketing'),
    'marketing automation': generate_mock_serp_result('marketing automation'),
    'email campaign': generate_mock_serp_result('email campaign'),
    'crm software': generate_mock_serp_result('crm software'),
    'email marketing software': generate_mock_serp_result('email marketing software'),
    'marketing automation platform': generate_mock_serp_result('marketing automation platform'),
    'email marketing best practices': generate_mock_serp_result('email marketing best practices'),
    'email segmentation': generate_mock_serp_result('email segmentation'),
    'a/b testing email': generate_mock_serp_result('a/b testing email'),
    'email analytics': generate_mock_serp_result('email analytics'),
}


# Sample Keywords

SAMPLE_KEYWORDS = [
    {
        'keyword': 'email marketing',
        'source': 'website_content',
        'search_volume': 45000,
        'difficulty': 75.5,
        'relevance_score': 0.95,
        'current_ranking': None,
        'serp_features': ['featured_snippet', 'people_also_ask']
    },
    {
        'keyword': 'marketing automation',
        'source': 'nlp_extraction',
        'search_volume': 28000,
        'difficulty': 68.0,
        'relevance_score': 0.92,
        'current_ranking': 15,
        'serp_features': ['organic', 'ads']
    },
    {
        'keyword': 'email campaign builder',
        'source': 'serp_analysis',
        'search_volume': 12000,
        'difficulty': 55.0,
        'relevance_score': 0.88,
        'current_ranking': None,
        'serp_features': ['organic']
    },
    {
        'keyword': 'crm integration',
        'source': 'nlp_extraction',
        'search_volume': 8500,
        'difficulty': 62.5,
        'relevance_score': 0.75,
        'current_ranking': 25,
        'serp_features': ['organic', 'featured_snippet']
    },
    {
        'keyword': 'email segmentation',
        'source': 'website_content',
        'search_volume': 6200,
        'difficulty': 48.0,
        'relevance_score': 0.82,
        'current_ranking': None,
        'serp_features': ['organic']
    }
]


# Sample Competitors

SAMPLE_COMPETITORS = [
    {
        'domain': 'mailchimp.com',
        'name': 'Mailchimp',
        'relevance_score': 0.95,
        'category': 'primary',
        'overlap_percentage': 85.5,
        'keyword_overlap': ['email marketing', 'marketing automation', 'email campaigns'],
        'content_similarity': 0.78
    },
    {
        'domain': 'hubspot.com',
        'name': 'HubSpot',
        'relevance_score': 0.88,
        'category': 'primary',
        'overlap_percentage': 72.0,
        'keyword_overlap': ['marketing automation', 'crm software', 'email marketing'],
        'content_similarity': 0.65
    },
    {
        'domain': 'activecampaign.com',
        'name': 'ActiveCampaign',
        'relevance_score': 0.82,
        'category': 'secondary',
        'overlap_percentage': 68.5,
        'keyword_overlap': ['email marketing', 'automation workflows'],
        'content_similarity': 0.72
    },
    {
        'domain': 'constantcontact.com',
        'name': 'Constant Contact',
        'relevance_score': 0.75,
        'category': 'secondary',
        'overlap_percentage': 55.0,
        'keyword_overlap': ['email marketing', 'email campaigns'],
        'content_similarity': 0.58
    },
    {
        'domain': 'sendinblue.com',
        'name': 'Sendinblue',
        'relevance_score': 0.62,
        'category': 'emerging',
        'overlap_percentage': 42.0,
        'keyword_overlap': ['email marketing'],
        'content_similarity': 0.45
    }
]


# Sample Content Opportunities

SAMPLE_CONTENT_OPPORTUNITIES = [
    {
        'topic': 'Content about email marketing ROI calculation',
        'gap_type': 'missing_content',
        'traffic_potential': 8500,
        'difficulty': 45.0,
        'priority': 'high',
        'recommended_format': 'guide'
    },
    {
        'topic': 'Content about email automation workflows for ecommerce',
        'gap_type': 'missing_content',
        'traffic_potential': 6200,
        'difficulty': 52.0,
        'priority': 'high',
        'recommended_format': 'blog'
    },
    {
        'topic': 'Content about email list cleaning best practices',
        'gap_type': 'weak_content',
        'traffic_potential': 4500,
        'difficulty': 38.0,
        'priority': 'medium',
        'recommended_format': 'blog'
    },
    {
        'topic': 'Content about GDPR compliance for email marketing',
        'gap_type': 'competitor_strength',
        'traffic_potential': 7800,
        'difficulty': 65.0,
        'priority': 'medium',
        'recommended_format': 'guide'
    },
    {
        'topic': 'Content about email marketing metrics to track',
        'gap_type': 'missing_content',
        'traffic_potential': 3500,
        'difficulty': 35.0,
        'priority': 'low',
        'recommended_format': 'infographic'
    }
]


# Mock Website Crawl Data

MOCK_WEBSITE_CRAWL_DATA = {
    'pages': [
        {
            'url': 'https://acmecorp.com',
            'title': 'Acme Corp - Best Email Marketing Software',
            'content': ' '.join(MOCK_HTML_HOMEPAGE.split()),
            'meta_description': 'Leading email marketing platform for small businesses.',
            'headings': [
                'Transform Your Email Marketing',
                'Powerful Marketing Automation for Growing Businesses',
                'Key Features',
                'Why Choose Acme Corp?'
            ]
        },
        {
            'url': 'https://acmecorp.com/pricing',
            'title': 'Pricing - Acme Corp Email Marketing',
            'content': ' '.join(MOCK_HTML_PRICING.split()),
            'meta_description': 'Simple, transparent pricing for email marketing software.',
            'headings': [
                'Email Marketing Pricing',
                'Choose the Perfect Plan for Your Business',
                'Starter - $29/month',
                'Professional - $79/month'
            ]
        },
        {
            'url': 'https://acmecorp.com/features',
            'title': 'Features - Marketing Automation Platform',
            'content': ' '.join(MOCK_HTML_FEATURES.split()),
            'meta_description': '',
            'headings': [
                'Email Marketing Features',
                'Everything You Need for Successful Email Campaigns',
                'Drag-and-Drop Email Builder',
                'Marketing Automation',
                'Advanced Segmentation',
                'Real-Time Analytics',
                'A/B Testing',
                'CRM Integration'
            ]
        },
        {
            'url': 'https://acmecorp.com/blog',
            'title': 'Email Marketing Best Practices - Acme Corp Blog',
            'content': ' '.join(MOCK_HTML_BLOG.split()),
            'meta_description': '',
            'headings': [
                'Email Marketing Blog',
                '10 Email Marketing Best Practices for 2024',
                'How to Build Effective Marketing Automation Workflows',
                'Email Segmentation Strategies That Work'
            ]
        }
    ],
    'total_pages': 4,
    'base_url': 'https://acmecorp.com',
    'domain': 'acmecorp.com'
}


# Database Fixtures

@pytest.fixture
def sample_brand_analysis_job():
    """Create a sample brand analysis job."""
    return {
        'id': str(uuid.uuid4()),
        'user_id': 1,
        'questionnaire': SAMPLE_QUESTIONNAIRE_COMPLETE,
        'status': 'initiated',
        'progress': 0,
        'results': None,
        'error_message': None,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'completed_at': None
    }


@pytest.fixture
def completed_brand_analysis_job():
    """Create a completed brand analysis job with results."""
    return {
        'id': str(uuid.uuid4()),
        'user_id': 1,
        'questionnaire': SAMPLE_QUESTIONNAIRE_COMPLETE,
        'status': 'completed',
        'progress': 100,
        'results': {
            'keywords_found': len(SAMPLE_KEYWORDS),
            'competitors_identified': len(SAMPLE_COMPETITORS),
            'content_opportunities': len(SAMPLE_CONTENT_OPPORTUNITIES),
            'analysis_timestamp': datetime.utcnow().isoformat()
        },
        'error_message': None,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'completed_at': datetime.utcnow()
    }


@pytest.fixture
def sample_discovered_keywords():
    """Get sample discovered keywords."""
    return SAMPLE_KEYWORDS


@pytest.fixture
def sample_identified_competitors():
    """Get sample identified competitors."""
    return SAMPLE_COMPETITORS


@pytest.fixture
def sample_content_opportunities():
    """Get sample content opportunities."""
    return SAMPLE_CONTENT_OPPORTUNITIES
