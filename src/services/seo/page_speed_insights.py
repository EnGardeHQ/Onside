"""
PageSpeed Insights Service

This module provides functionality to interact with the Google PageSpeed Insights API
to analyze and optimize web page performance.
"""
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PageSpeedInsightsService:
    """Service for interacting with Google PageSpeed Insights API."""
    
    BASE_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the PageSpeed Insights service.
        
        Args:
            api_key: Google Cloud API key with PageSpeed Insights API enabled
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def analyze(
        self,
        url: str,
        strategy: str = 'mobile',
        categories: Optional[List[str]] = None,
        locale: str = 'en-US',
        utm_campaign: Optional[str] = None,
        utm_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a URL using Google PageSpeed Insights.
        
        Args:
            url: The URL to analyze
            strategy: Analysis strategy ('mobile' or 'desktop')
            categories: List of categories to include (e.g., ['performance', 'accessibility', 'seo'])
            locale: Locale for results
            utm_campaign: Campaign name for tracking
            utm_source: Campaign source for tracking
            
        Returns:
            Dictionary containing PageSpeed Insights results
        """
        if not categories:
            categories = ['performance', 'accessibility', 'seo', 'best-practices']
        
        params = {
            'url': url,
            'strategy': strategy,
            'category': categories,
            'locale': locale,
        }
        
        if self.api_key:
            params['key'] = self.api_key
        
        if utm_campaign:
            params['utm_campaign'] = utm_campaign
        if utm_source:
            params['utm_source'] = utm_source
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"PageSpeed Insights API error: {e.response.status_code} - {e.response.text}")
            return {'error': f"API error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Error analyzing URL with PageSpeed Insights: {str(e)}")
            return {'error': str(e)}
    
    async def get_performance_score(
        self,
        url: str,
        strategy: str = 'mobile'
    ) -> Dict[str, Any]:
        """Get the performance score for a URL.
        
        Args:
            url: The URL to analyze
            strategy: Analysis strategy ('mobile' or 'desktop')
            
        Returns:
            Dictionary containing performance score and metrics
        """
        result = await self.analyze(url, strategy=strategy, categories=['performance'])
        
        if 'error' in result:
            return result
            
        try:
            lighthouse_result = result.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            audits = lighthouse_result.get('audits', {})
            
            # Get overall performance score
            performance_score = categories.get('performance', {}).get('score', 0) * 100
            
            # Get core web vitals
            cls = audits.get('cumulative-layout-shift', {}).get('displayValue', '0')
            cls_score = audits.get('cumulative-layout-shift', {}).get('score', 0) * 100
            
            lcp = audits.get('largest-contentful-paint', {}).get('displayValue', '0 s')
            lcp_score = audits.get('largest-contentful-paint', {}).get('score', 0) * 100
            
            fid = audits.get('max-potential-fid', {}).get('displayValue', '0 ms')
            fid_score = audits.get('max-potential-fid', {}).get('score', 0) * 100
            
            # Get other important metrics
            fcp = audits.get('first-contentful-paint', {}).get('displayValue', '0 s')
            si = audits.get('speed-index', {}).get('displayValue', '0 s')
            tti = audits.get('interactive', {}).get('displayValue', '0 s')
            tbt = audits.get('total-blocking-time', {}).get('displayValue', '0 ms')
            
            # Get opportunities and diagnostics
            opportunities = []
            diagnostics = []
            
            for audit_id, audit in audits.items():
                if audit.get('score') is not None and audit.get('score') < 1:
                    if audit.get('scoreDisplayMode') == 'numeric':
                        opportunities.append({
                            'id': audit_id,
                            'title': audit.get('title', audit_id),
                            'description': audit.get('description', ''),
                            'score': audit.get('score') * 100,
                            'display_value': audit.get('displayValue', ''),
                            'details': audit.get('details', {})
                        })
                    elif audit.get('scoreDisplayMode') == 'informative':
                        diagnostics.append({
                            'id': audit_id,
                            'title': audit.get('title', audit_id),
                            'description': audit.get('description', ''),
                            'score': audit.get('score') * 100,
                            'display_value': audit.get('displayValue', ''),
                            'details': audit.get('details', {})
                        })
            
            # Sort opportunities by potential savings (if available)
            opportunities.sort(key=lambda x: x.get('score', 0))
            
            return {
                'url': url,
                'strategy': strategy,
                'performance_score': performance_score,
                'core_web_vitals': {
                    'cumulative_layout_shift': {
                        'value': cls,
                        'score': cls_score
                    },
                    'largest_contentful_paint': {
                        'value': lcp,
                        'score': lcp_score
                    },
                    'first_input_delay': {
                        'value': fid,
                        'score': fid_score
                    }
                },
                'metrics': {
                    'first_contentful_paint': fcp,
                    'speed_index': si,
                    'time_to_interactive': tti,
                    'total_blocking_time': tbt
                },
                'opportunities': opportunities[:5],  # Top 5 opportunities
                'diagnostics': diagnostics[:5],      # Top 5 diagnostics
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing PageSpeed Insights results: {str(e)}")
            return {'error': f"Error processing results: {str(e)}"}
    
    async def get_seo_score(
        self,
        url: str,
        strategy: str = 'mobile'
    ) -> Dict[str, Any]:
        """Get the SEO score for a URL.
        
        Args:
            url: The URL to analyze
            strategy: Analysis strategy ('mobile' or 'desktop')
            
        Returns:
            Dictionary containing SEO score and recommendations
        """
        result = await self.analyze(url, strategy=strategy, categories=['seo'])
        
        if 'error' in result:
            return result
            
        try:
            lighthouse_result = result.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            audits = lighthouse_result.get('audits', {})
            
            # Get overall SEO score
            seo_score = categories.get('seo', {}).get('score', 0) * 100
            
            # Get SEO opportunities and diagnostics
            opportunities = []
            diagnostics = []
            
            for audit_id, audit in audits.items():
                if audit.get('score') is not None and audit.get('score') < 1:
                    item = {
                        'id': audit_id,
                        'title': audit.get('title', audit_id),
                        'description': audit.get('description', ''),
                        'score': audit.get('score') * 100,
                        'display_value': audit.get('displayValue', ''),
                        'details': audit.get('details', {})
                    }
                    
                    if audit.get('scoreDisplayMode') == 'binary':
                        opportunities.append(item)
                    else:
                        diagnostics.append(item)
            
            # Sort opportunities by score (worst first)
            opportunities.sort(key=lambda x: x.get('score', 0))
            
            return {
                'url': url,
                'strategy': strategy,
                'seo_score': seo_score,
                'opportunities': opportunities,
                'diagnostics': diagnostics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing SEO results: {str(e)}")
            return {'error': f"Error processing results: {str(e)}"}
    
    async def get_accessibility_score(
        self,
        url: str,
        strategy: str = 'mobile'
    ) -> Dict[str, Any]:
        """Get the accessibility score for a URL.
        
        Args:
            url: The URL to analyze
            strategy: Analysis strategy ('mobile' or 'desktop')
            
        Returns:
            Dictionary containing accessibility score and recommendations
        """
        result = await self.analyze(url, strategy=strategy, categories=['accessibility'])
        
        if 'error' in result:
            return result
            
        try:
            lighthouse_result = result.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            audits = lighthouse_result.get('audits', {})
            
            # Get overall accessibility score
            a11y_score = categories.get('accessibility', {}).get('score', 0) * 100
            
            # Get accessibility issues
            issues = []
            passed = []
            
            for audit_id, audit in audits.items():
                if audit.get('score') is not None:
                    item = {
                        'id': audit_id,
                        'title': audit.get('title', audit_id),
                        'description': audit.get('description', ''),
                        'score': audit.get('score') * 100,
                        'display_value': audit.get('displayValue', ''),
                        'details': audit.get('details', {})
                    }
                    
                    if audit.get('score') < 1:
                        issues.append(item)
                    else:
                        passed.append(item)
            
            # Sort issues by score (worst first)
            issues.sort(key=lambda x: x.get('score', 0))
            
            return {
                'url': url,
                'strategy': strategy,
                'accessibility_score': a11y_score,
                'issues': issues,
                'passed_checks': passed,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing accessibility results: {str(e)}")
            return {'error': f"Error processing results: {str(e)}"}
    
    async def get_best_practices_score(
        self,
        url: str,
        strategy: str = 'mobile'
    ) -> Dict[str, Any]:
        """Get the best practices score for a URL.
        
        Args:
            url: The URL to analyze
            strategy: Analysis strategy ('mobile' or 'desktop')
            
        Returns:
            Dictionary containing best practices score and recommendations
        """
        result = await self.analyze(url, strategy=strategy, categories=['best-practices'])
        
        if 'error' in result:
            return result
            
        try:
            lighthouse_result = result.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            audits = lighthouse_result.get('audits', {})
            
            # Get overall best practices score
            bp_score = categories.get('best-practices', {}).get('score', 0) * 100
            
            # Get best practices issues and passed checks
            issues = []
            passed = []
            
            for audit_id, audit in audits.items():
                if audit.get('score') is not None:
                    item = {
                        'id': audit_id,
                        'title': audit.get('title', audit_id),
                        'description': audit.get('description', ''),
                        'score': audit.get('score') * 100,
                        'display_value': audit.get('displayValue', ''),
                        'details': audit.get('details', {})
                    }
                    
                    if audit.get('score') < 1:
                        issues.append(item)
                    else:
                        passed.append(item)
            
            # Sort issues by score (worst first)
            issues.sort(key=lambda x: x.get('score', 0))
            
            return {
                'url': url,
                'strategy': strategy,
                'best_practices_score': bp_score,
                'issues': issues,
                'passed_checks': passed,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing best practices results: {str(e)}")
            return {'error': f"Error processing results: {str(e)}"}
    
    async def get_full_analysis(
        self,
        url: str,
        strategy: str = 'mobile'
    ) -> Dict[str, Any]:
        """Get a full analysis of a URL including all categories.
        
        Args:
            url: The URL to analyze
            strategy: Analysis strategy ('mobile' or 'desktop')
            
        Returns:
            Dictionary containing complete analysis results
        """
        # Run all analyses in parallel
        performance_task = asyncio.create_task(self.get_performance_score(url, strategy))
        seo_task = asyncio.create_task(self.get_seo_score(url, strategy))
        a11y_task = asyncio.create_task(self.get_accessibility_score(url, strategy))
        bp_task = asyncio.create_task(self.get_best_practices_score(url, strategy))
        
        # Wait for all tasks to complete
        performance, seo, a11y, best_practices = await asyncio.gather(
            performance_task,
            seo_task,
            a11y_task,
            bp_task
        )
        
        # Calculate overall score (weighted average)
        scores = {
            'performance': performance.get('performance_score', 0) if isinstance(performance, dict) else 0,
            'seo': seo.get('seo_score', 0) if isinstance(seo, dict) else 0,
            'accessibility': a11y.get('accessibility_score', 0) if isinstance(a11y, dict) else 0,
            'best_practices': best_practices.get('best_practices_score', 0) if isinstance(best_practices, dict) else 0
        }
        
        # Calculate weighted average (performance has higher weight)
        overall_score = (
            (scores['performance'] * 0.4) +
            (scores['seo'] * 0.2) +
            (scores['accessibility'] * 0.2) +
            (scores['best_practices'] * 0.2)
        )
        
        return {
            'url': url,
            'strategy': strategy,
            'overall_score': round(overall_score, 1),
            'categories': {
                'performance': performance if isinstance(performance, dict) else {'error': 'Failed to analyze performance'},
                'seo': seo if isinstance(seo, dict) else {'error': 'Failed to analyze SEO'},
                'accessibility': a11y if isinstance(a11y, dict) else {'error': 'Failed to analyze accessibility'},
                'best_practices': best_practices if isinstance(best_practices, dict) else {'error': 'Failed to analyze best practices'}
            },
            'timestamp': datetime.utcnow().isoformat()
        }
