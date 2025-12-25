#!/usr/bin/env python
"""
SEO Analysis Service for OnSide Reports

This service provides SEO analysis capabilities including:
- Backlink analysis
- Keyword rankings
- Content gap analysis
- Technical SEO audit
"""

import logging
from typing import Dict, List, Any, Optional
import aiohttp
import asyncio
from urllib.parse import urlparse
import json
import os

logger = logging.getLogger(__name__)

class SEOService:
    """Service for performing SEO analysis."""
    
    def __init__(self, api_key: str = None):
        """Initialize the SEO service."""
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        self.base_url = "https://serpapi.com/search.json"
        
    async def analyze_seo(self, domain: str) -> Dict[str, Any]:
        """
        Perform comprehensive SEO analysis for a domain.
        
        Args:
            domain: Domain to analyze (e.g., 'tcs.com')
            
        Returns:
            Dict containing SEO analysis results
        """
        logger.info(f"Starting SEO analysis for {domain}")
        
        # Run all SEO checks in parallel
        tasks = [
            self.get_keyword_rankings(domain),
            self.analyze_backlinks(domain),
            self.technical_seo_audit(domain),
            self.content_gap_analysis(domain)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        seo_data = {
            "domain": domain,
            "keywords": results[0] if not isinstance(results[0], Exception) else {},
            "backlinks": results[1] if not isinstance(results[1], Exception) else {},
            "technical_seo": results[2] if not isinstance(results[2], Exception) else {},
            "content_gaps": results[3] if not isinstance(results[3], Exception) else {},
            "overall_score": self._calculate_seo_score(results)
        }
        
        return seo_data
    
    async def get_keyword_rankings(self, domain: str, keywords: List[str] = None) -> Dict[str, Any]:
        """Get keyword rankings for the domain."""
        if not keywords:
            # Default keywords if none provided
            keywords = ["IT services", "digital transformation", "cloud consulting"]
            
        rankings = {}
        
        for keyword in keywords:
            try:
                params = {
                    'q': keyword,
                    'location': 'United States',
                    'hl': 'en',
                    'gl': 'us',
                    'google_domain': 'google.com',
                    'api_key': self.api_key,
                    'num': 50  # Get top 50 results
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.base_url, params=params) as response:
                        data = await response.json()
                        
                # Check if domain appears in top 50 results
                rankings[keyword] = {
                    'position': -1,  # -1 means not in top 50
                    'url': '',
                    'title': ''
                }
                
                if 'organic_results' in data:
                    for idx, result in enumerate(data['organic_results'], 1):
                        if domain in result.get('link', ''):
                            rankings[keyword] = {
                                'position': idx,
                                'url': result.get('link', ''),
                                'title': result.get('title', '')
                            }
                            break
                            
            except Exception as e:
                logger.error(f"Error getting keyword rankings for {keyword}: {str(e)}")
                rankings[keyword] = {'error': str(e)}
        
        return rankings
    
    async def analyze_backlinks(self, domain: str) -> Dict[str, Any]:
        """Analyze backlinks for the domain."""
        # In a real implementation, this would use a backlink API like Ahrefs or Moz
        # For now, return mock data
        return {
            'total_backlinks': 12500,
            'referring_domains': 850,
            'domain_authority': 85,
            'top_referrers': [
                {'domain': 'linkedin.com', 'backlinks': 1200},
                {'domain': 'twitter.com', 'backlinks': 850},
                {'domain': 'facebook.com', 'backlinks': 720},
            ],
            'anchor_text_distribution': {
                'branded': 45,
                'generic': 30,
                'naked_url': 15,
                'other': 10
            }
        }
    
    async def technical_seo_audit(self, domain: str) -> Dict[str, Any]:
        """Perform technical SEO audit of the domain."""
        # In a real implementation, this would crawl the site
        return {
            'mobile_friendly': True,
            'page_speed': 78,  # out of 100
            'ssl_enabled': True,
            'broken_links': 12,
            'missing_alt_tags': 8,
            'missing_meta_descriptions': 15,
            'duplicate_content': 3
        }
    
    async def content_gap_analysis(self, domain: str) -> Dict[str, Any]:
        """Identify content gaps compared to competitors."""
        # In a real implementation, this would analyze competitors' content
        return {
            'missing_keywords': [
                'digital transformation strategy',
                'cloud migration services',
                'AI consulting'
            ],
            'content_depth_score': 78,  # out of 100
            'content_freshness': '2 months',  # since last update
            'blog_posts_last_quarter': 8,
            'competitor_average': 15
        }
    
    def _calculate_seo_score(self, results: list) -> float:
        """Calculate overall SEO score from analysis results."""
        # Simple weighted average for now
        weights = {
            'keywords': 0.3,
            'backlinks': 0.3,
            'technical': 0.25,
            'content': 0.15
        }
        
        scores = {
            'keywords': self._score_keywords(results[0]) if not isinstance(results[0], Exception) else 0,
            'backlinks': self._score_backlinks(results[1]) if not isinstance(results[1], Exception) else 0,
            'technical': self._score_technical(results[2]) if not isinstance(results[2], Exception) else 0,
            'content': self._score_content(results[3]) if not isinstance(results[3], Exception) else 0
        }
        
        total_score = sum(scores[category] * weights[category] for category in scores)
        return round(total_score, 1)
    
    def _score_keywords(self, keywords_data: dict) -> float:
        """Calculate keyword score."""
        if not keywords_data:
            return 0
            
        total_position = 0
        count = 0
        
        for keyword, data in keywords_data.items():
            if isinstance(data, dict) and 'position' in data and data['position'] > 0:
                # Lower position is better, so we invert the score
                score = max(0, 100 - (data['position'] * 2))
                total_position += score
                count += 1
        
        return total_position / count if count > 0 else 0
    
    def _score_backlinks(self, backlinks_data: dict) -> float:
        """Calculate backlink score."""
        if not backlinks_data or 'domain_authority' not in backlinks_data:
            return 0
        return backlinks_data.get('domain_authority', 0)
    
    def _score_technical(self, tech_data: dict) -> float:
        """Calculate technical SEO score."""
        if not tech_data:
            return 0
            
        score = 0
        count = 0
        
        if tech_data.get('mobile_friendly'):
            score += 20
        if tech_data.get('ssl_enabled'):
            score += 20
            
        score += tech_data.get('page_speed', 0) * 0.6  # 60% weight to page speed
        
        # Deduct for issues
        score -= min(tech_data.get('broken_links', 0) * 0.5, 10)  # Max 10% deduction
        score -= min(tech_data.get('missing_alt_tags', 0) * 0.3, 5)  # Max 5% deduction
        score -= min(tech_data.get('duplicate_content', 0) * 1, 15)  # Max 15% deduction
        
        return max(0, min(100, score))
    
    def _score_content(self, content_data: dict) -> float:
        """Calculate content score."""
        if not content_data:
            return 0
            
        score = content_data.get('content_depth_score', 0)
        
        # Adjust based on content freshness
        freshness = content_data.get('content_freshness', '')
        if 'day' in freshness:
            score += 5
        elif 'week' in freshness:
            score += 3
        elif 'month' in freshness:
            score += 1
            
        # Adjust based on content volume
        posts = content_data.get('blog_posts_last_quarter', 0)
        competitor_avg = content_data.get('competitor_average', 10)
        if competitor_avg > 0:
            ratio = min(posts / competitor_avg, 1.5)  # Cap at 1.5x competitor average
            score *= ratio
            
        return min(100, score)
