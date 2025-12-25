"""
SEO Service for OnSide application.

This module provides comprehensive SEO analysis by integrating multiple data sources:
- SEMrush for competitive intelligence
- SERP APIs for search rankings
- Google Search Console for search analytics
- Google Analytics for traffic data
- PageSpeed Insights for performance metrics
"""
import os
import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, TypeVar, Callable, Union, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import Domain
from src.repositories.domain_repository import DomainRepository
from src.services.seo.semrush_service import SemrushService
from src.services.seo.serp_service import SerpService
from src.services.seo.google_search_console import GoogleSearchConsoleService
# from src.services.seo.google_analytics import GoogleAnalyticsService # Commented out: File does not exist
from src.services.seo.page_speed_insights import PageSpeedInsightsService
from src.exceptions import DomainValidationError, ServiceUnavailableError
from src.core.cache import cache

# Type variable for generic function typing
F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)

# Cache settings (in seconds)
CACHE_TTL = 3600  # 1 hour
SHORT_CACHE_TTL = 300  # 5 minutes

def cache_result(ttl: int = CACHE_TTL):
    """Decorator to cache method results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = f"seo:{func.__name__}:{':'.join(map(str, args))}:{json.dumps(kwargs, sort_keys=True)}"
            
            # Try to get from cache
            cached = await cache.get(cache_key)
            if cached is not None:
                return cached
                
            # Call the function
            result = await func(self, *args, **kwargs)
            
            # Cache the result if not None
            if result is not None:
                await cache.set(cache_key, result, ttl)
                
            return result
        return wrapper
    return decorator

class SEOService:
    """
    Comprehensive SEO analysis service that integrates multiple data sources.
    
    This service provides a unified interface for SEO analysis by aggregating
    data from various sources including SEMrush, Google Search Console,
    Google Analytics, and PageSpeed Insights.
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize the SEO service with database session and API clients.
        
        Args:
            db: Optional database session for persistent storage
        """
        logger.info("SEOService __init__ started.")
        self.db = db
        self.domain_repo = None # Initialize to None
        if db: # Only attempt to initialize if db is provided
            try:
                logger.info("Attempting to initialize DomainRepository...")
                self.domain_repo = DomainRepository(db)
                logger.info("DomainRepository initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing DomainRepository: {e}", exc_info=True)
                self.domain_repo = None # Ensure it's None on failure
        else:
            logger.info("No database session provided, DomainRepository not initialized.")
        
        # Initialize API clients only if API keys are available
        self.service_status = {}
        
        # SEMrush Service (currently not primary, SERP API is used instead)
        # try:
        #     self.semrush = SemrushService()
        #     self.service_status['semrush'] = bool(os.environ.get('SEMRUSH_API_KEY'))
        # except Exception as e:
        #     logger.error(f"Error initializing SEMrushService: {e}", exc_info=True)
        #     self.semrush = None
        #     self.service_status['semrush'] = False
        self.semrush = None # Explicitly set to None as SEMrush is not currently active
        self.service_status['semrush'] = False # Mark SEMrush as inactive
            
        try:
            logger.info("Attempting to initialize SerpService...")
            self.serp = SerpService() # Assumes SerpService reads env var internally or handles missing key
            self.service_status['serp'] = bool(os.environ.get('SERPAPI_KEY'))
            logger.info("SerpService initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing SerpService: {e}", exc_info=True)
            self.serp = None 
            self.service_status['serp'] = False
            
        try:
            logger.info("Attempting to initialize GoogleSearchConsoleService...")
            self.gsc = GoogleSearchConsoleService() # Assumes GSCService handles creds internally
            self.service_status['gsc'] = bool(os.environ.get('GOOGLE_CLIENT_EMAIL') and os.environ.get('GOOGLE_PRIVATE_KEY'))
            logger.info("GoogleSearchConsoleService initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing GoogleSearchConsoleService: {e}", exc_info=True)
            self.gsc = None 
            self.service_status['gsc'] = False
            
        # Google Analytics Service (Commented out due to missing file)
        # try:
        #     self.ga = GoogleAnalyticsService()
        #     self.service_status['ga'] = bool(os.environ.get('GOOGLE_ANALYTICS_PROPERTY_ID'))
        # except Exception as e:
        #     logger.error(f"Error initializing GoogleAnalyticsService: {e}", exc_info=True)
        #     self.ga = None
        #     self.service_status['ga'] = False
        self.ga = None # Explicitly set to None as GA module is missing
        self.service_status['ga'] = False # Mark GA as inactive
            
        try:
            logger.info("Attempting to initialize PageSpeedInsightsService...")
            self.psi = PageSpeedInsightsService() # Assumes PSI reads env var or works without key
            self.service_status['psi'] = bool(os.environ.get('GOOGLE_API_KEY')) # Note: uses GOOGLE_API_KEY
            logger.info("PageSpeedInsightsService initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing PageSpeedInsightsService: {e}", exc_info=True)
            self.psi = None 
            self.service_status['psi'] = False
            
        logger.info(f"SEOService __init__ finished. Final service status: {self.service_status}")
    
    @cache_result(ttl=86400)  # Cache for 24 hours
    async def get_competing_domains(self, domain: str) -> List[Dict[str, Any]]:
        """Get a comprehensive list of competing domains from multiple data sources.
        
        This method attempts to get competitor data from available services:
        - SEMrush (for SEO competitors)
        - Google Search Console (for search competitors)
        - SERP analysis (for organic search competitors)
        
        If no services are available, returns an empty list.
        
        Args:
            domain: The domain to analyze (e.g., 'example.com')
            
        Returns:
            List of competing domains with detailed metrics including:
            - domain: Competitor domain
            - common_keywords: Number of overlapping keywords
            - traffic_share: Estimated traffic share
            - backlinks: Number of backlinks
            - domain_score: Domain authority/trust score
            - source: Data source (e.g., 'semrush', 'gsc', 'serp')
            - last_updated: Timestamp of last data update
        """
        logger.info(f"Fetching competing domains for: {domain}")
        logger.debug(f"Available services: {[k for k, v in self.service_status.items() if v]}")
        
        competitors = []
        active_sources = []
        
        # 1. Get competitors from SEMrush if available
        if self.service_status.get('semrush', False):
            try:
                logger.debug("Trying to get competitors from SEMrush...")
                semrush_competitors = await self.semrush.get_competitors(domain)
                if semrush_competitors:
                    competitors.extend([{
                        **comp,
                        'source': 'semrush',
                        'last_updated': datetime.utcnow().isoformat()
                    } for comp in semrush_competitors])
                    active_sources.append('semrush')
                    logger.debug(f"Got {len(semrush_competitors)} competitors from SEMrush")
                else:
                    logger.debug("No competitors found in SEMrush")
            except Exception as e:
                self.service_status['semrush'] = False
                logger.error(f"SEMrush competitor lookup failed for {domain}: {e}", exc_info=True)
        
        # 2. Get competitors from Google Search Console if available
        if self.service_status.get('gsc', False):
            try:
                logger.debug("Trying to get competitors from Google Search Console...")
                gsc_competitors = await self.gsc.get_search_competitors(domain)
                if gsc_competitors:
                    competitors.extend([{
                        **comp,
                        'source': 'gsc',
                        'last_updated': datetime.utcnow().isoformat()
                    } for comp in gsc_competitors])
                    active_sources.append('gsc')
                    logger.debug(f"Got {len(gsc_competitors)} competitors from GSC")
                else:
                    logger.debug("No competitors found in GSC")
            except Exception as e:
                self.service_status['gsc'] = False
                logger.error(f"GSC competitor lookup failed for {domain}: {e}", exc_info=True)
        
        # 3. Get competitors from SERP analysis if available
        if self.service_status.get('serp', False):
            try:
                logger.debug("Trying to get competitors from SERP analysis...")
                serp_competitors = await self.serp.get_competitors(domain)
                if serp_competitors:
                    competitors.extend([{
                        **comp,
                        'source': 'serp',
                        'last_updated': datetime.utcnow().isoformat()
                    } for comp in serp_competitors])
                    active_sources.append('serp')
                    logger.debug(f"Got {len(serp_competitors)} competitors from SERP")
                else:
                    logger.debug("No competitors found in SERP")
            except Exception as e:
                self.service_status['serp'] = False
                logger.error(f"SERP competitor lookup failed for {domain}: {e}", exc_info=True)
        
        if not active_sources:
            logger.warning(f"No active data sources available for competitor analysis of {domain}")
            return []
        
        # Log which sources were successfully used
        logger.info(f"Successfully retrieved data from: {', '.join(active_sources) if active_sources else 'no sources'}")
        
        # Merge and deduplicate competitors
        merged_competitors = self._merge_competitors(competitors)
        
        # Sort by traffic_share (descending) and then by common_keywords (descending)
        merged_competitors.sort(
            key=lambda x: (x.get('traffic_share', 0), x.get('common_keywords', 0)),
            reverse=True
        )
        
        logger.info(f"Found {len(merged_competitors)} unique competitors for {domain} from {len(active_sources)} source(s)")
        return merged_competitors
    
    @cache_result(ttl=43200)  # Cache for 12 hours
    async def get_domain_metrics(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive SEO metrics from available data sources.
        
        This method attempts to get data from multiple sources:
        - SEMrush (for backlinks, keywords, traffic)
        - Google Search Console (for search performance)
        - Google Analytics (for traffic and engagement)
        - PageSpeed Insights (for performance metrics)
        
        If no services are available, returns a minimal response with just the timestamp.
        
        Args:
            domain: The domain to analyze (e.g., 'example.com')
            
        Returns:
            Dictionary containing available metrics:
            - overview: General domain information
            - traffic: Traffic metrics
            - backlinks: Backlink profile
            - keywords: Top performing keywords
            - performance: Page speed and performance
            - mobile_usability: Mobile usability metrics
            - last_updated: Timestamp of data collection
            - health_score: Overall health score (0-100)
        """
        logger.info(f"Fetching SEO metrics for domain: {domain}")
        logger.debug(f"Available services: {[k for k, v in self.service_status.items() if v]}")
        
        # Initialize metrics with default values
        metrics = {
            'overview': {},
            'traffic': {},
            'backlinks': {},
            'keywords': [],
            'performance': {},
            'mobile_usability': {},
            'last_updated': datetime.utcnow().isoformat(),
            'health_score': 0
        }
        
        active_sources = []
        
        # 1. Get data from SEMrush if available
        if self.service_status.get('semrush', False):
            try:
                logger.debug("Fetching data from SEMrush...")
                
                # Get domain overview
                overview = await self.semrush.get_domain_overview(domain)
                if overview:
                    metrics['overview'].update(overview)
                    active_sources.append('semrush:overview')
                
                # Get backlinks data
                backlinks = await self.semrush.get_backlinks(domain)
                if backlinks:
                    metrics['backlinks'].update(backlinks)
                    active_sources.append('semrush:backlinks')
                
                # Get top performing keywords
                keywords = await self.semrush.get_top_keywords(domain, limit=10)
                if keywords:
                    metrics['keywords'] = keywords
                    active_sources.append('semrush:keywords')
                    
                logger.debug(f"SEMrush data fetched: {', '.join([s for s in active_sources if s.startswith('semrush:')])}")
                    
            except Exception as e:
                self.service_status['semrush'] = False
                logger.error(f"SEMrush metrics fetch failed for {domain}: {e}", exc_info=True)
        
        # 2. Get data from Google Search Console if available
        if self.service_status.get('gsc', False):
            try:
                logger.debug("Fetching data from Google Search Console...")
                # Get search analytics
                search_analytics = await self.gsc.get_search_analytics(domain)
                if search_analytics:
                    metrics['traffic'].update(search_analytics)
                    active_sources.append('gsc:search_analytics')
                    logger.debug("Fetched search analytics from GSC")
                    
            except Exception as e:
                self.service_status['gsc'] = False
                logger.error(f"GSC metrics fetch failed for {domain}: {e}", exc_info=True)
        
        # Google Analytics Service (Commented out due to missing file)
        # if self.service_status.get('ga', False):
        #     try:
        #         logger.debug("Fetching data from Google Analytics...")
        #         # Get traffic data
        #         traffic_data = await self.ga.get_traffic_data(domain)
        #         if traffic_data:
        #             metrics['traffic'].update(traffic_data)
        #             active_sources.append('ga:traffic')
        #             logger.debug("Fetched traffic data from GA")
                    
        #     except Exception as e:
        #         self.service_status['ga'] = False
        #         logger.error(f"Google Analytics fetch failed for {domain}: {e}", exc_info=True)
        
        # 4. Get data from PageSpeed Insights if available
        if self.service_status.get('psi', False):
            try:
                logger.debug("Fetching data from PageSpeed Insights...")
                # Get performance data
                psi_data = await self.psi.analyze(domain)
                if psi_data:
                    metrics['performance'] = {
                        'score': psi_data.get('lighthouseResult', {}).get('categories', {}).get('performance', {}).get('score', 0) * 100,
                        'fcp': psi_data.get('loadingExperience', {}).get('metrics', {}).get('FIRST_CONTENTFUL_PAINT_MS', {}).get('percentile', 0),
                        'lcp': psi_data.get('loadingExperience', {}).get('metrics', {}).get('LARGEST_CONTENTFUL_PAINT_MS', {}).get('percentile', 0),
                        'fid': psi_data.get('loadingExperience', {}).get('metrics', {}).get('FIRST_INPUT_DELAY_MS', {}).get('percentile', 0),
                        'cls': psi_data.get('loadingExperience', {}).get('metrics', {}).get('CUMULATIVE_LAYOUT_SHIFT_SCORE', {}).get('percentile', 0)
                    }
                    metrics['mobile_usability'] = {
                        'passed': psi_data.get('mobileUsability', {}).get('passed', False),
                        'issues': psi_data.get('mobileUsability', {}).get('issues', [])
                    }
                    active_sources.append('psi:performance')
                    logger.debug("Fetched performance data from PageSpeed Insights")
                    
            except Exception as e:
                self.service_status['psi'] = False
                logger.error(f"PageSpeed Insights fetch failed for {domain}: {e}", exc_info=True)
        
        # Log which data points were successfully retrieved
        if active_sources:
            logger.info(f"Successfully retrieved data from: {', '.join(active_sources)}")
        else:
            logger.warning(f"No data sources available for {domain}")
        
        # Calculate an overall health score (0-100) if we have some data
        if any(metrics.values()):
            metrics['health_score'] = self._calculate_health_score(metrics)
        
        logger.info(f"Completed fetching metrics for {domain} from {len(active_sources)} data point(s)")
        return metrics
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate an overall health score (0-100) based on various SEO metrics.
        
        The score is calculated using weighted metrics from different sources:
        - Performance (40%): Page speed and Core Web Vitals
        - SEO (30%): Backlinks, domain authority, and keyword rankings
        - Usability (20%): Mobile usability and accessibility
        - Traffic (10%): Organic traffic and engagement
        
        Args:
            metrics: Dictionary containing all domain metrics
            
        Returns:
            Float score between 0 and 100 representing overall health
        """
        score = 0.0
        weights = {
            'performance': 0.4,
            'seo': 0.3,
            'usability': 0.2,
            'traffic': 0.1
        }
        
        # Performance score (0-100)
        perf_score = 0
        if metrics['performance']:
            perf_metrics = metrics['performance']
            # Core Web Vitals scoring
            lcp = perf_metrics.get('largest_contentful_paint', 0)
            fid = perf_metrics.get('first_input_delay', 0)
            cls = perf_metrics.get('cumulative_layout_shift', 0)
            
            # Convert metrics to scores (0-100)
            lcp_score = max(0, 100 - (max(0, lcp - 2500) / 25))
            fid_score = max(0, 100 - (max(0, fid - 100) * 2))
            cls_score = max(0, 100 - (cls * 1000))
            
            perf_score = (lcp_score * 0.4 + fid_score * 0.3 + cls_score * 0.3)
        
        # SEO score (0-100)
        seo_score = 0
        if metrics['overview'] and metrics['backlinks']:
            # Domain authority (0-100)
            da = metrics['overview'].get('authority_score', 0) or 0
            # Backlink quality (0-100)
            backlinks = metrics['backlinks'].get('total', 0) or 0
            ref_domains = metrics['backlinks'].get('referring_domains', 0) or 0
            backlink_score = min(100, math.log10(max(1, backlinks)) * 15)
            ref_domain_score = min(100, math.log10(max(1, ref_domains)) * 20)
            
            seo_score = (da * 0.5 + backlink_score * 0.3 + ref_domain_score * 0.2)
        
        # Usability score (0-100)
        usability_score = 0
        if metrics['mobile_usability']:
            # Mobile usability pass/fail (0 or 100)
            mobile_pass = 100 if metrics['mobile_usability'].get('passed', False) else 0
            # Deduct for mobile issues
            issue_penalty = min(30, len(metrics['mobile_usability'].get('issues', [])) * 5)
            usability_score = max(0, mobile_pass - issue_penalty)
        
        # Traffic score (0-100)
        traffic_score = 0
        if metrics['traffic']:
            # Normalize traffic metrics (assuming logarithmic scale)
            organic = metrics['traffic'].get('organic_traffic', 0) or 0
            sessions = metrics['traffic'].get('sessions', 0) or 0
            
            traffic_score = min(100, math.log10(max(1, organic + sessions)) * 15)
            
            # Adjust for engagement
            if 'bounce_rate' in metrics['traffic'] and 'avg_session_duration' in metrics['traffic']:
                bounce_rate = metrics['traffic']['bounce_rate'] or 0
                avg_duration = metrics['traffic']['avg_session_duration'] or 0
                
                # Reduce score for high bounce rates
                bounce_penalty = max(0, (bounce_rate - 70) * 0.5)
                # Reward longer session durations
                duration_boost = min(20, avg_duration / 3)
                
                traffic_score = max(0, min(100, traffic_score - bounce_penalty + duration_boost))
        
        # Calculate weighted final score
        final_score = (
            perf_score * weights['performance'] +
            seo_score * weights['seo'] +
            usability_score * weights['usability'] +
            traffic_score * weights['traffic']
        )
        
        return round(final_score, 1)

    async def get_domain_metrics_batch(self, domains: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get SEO metrics for multiple domains in batch.
        
        Args:
            domains: List of domains to get metrics for
            
        Returns:
            Dictionary mapping domains to their metrics
        """
        tasks = [self.get_domain_metrics(domain) for domain in domains]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling any errors
        metrics = {}
        for domain, result in zip(domains, results):
            if isinstance(result, Exception):
                logger.error(f"Error processing domain {domain}: {str(result)}")
                metrics[domain] = {}
            else:
                metrics[domain] = result
                
        return metrics
    
    def _merge_competitors(self, competitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate competitors from different data sources.
        
        Args:
            competitors: List of competitor dictionaries from different sources
            
        Returns:
            List of unique competitors with merged metrics
        """
        merged = {}
        
        for comp in competitors:
            domain = comp.get('domain', '').lower().strip()
            if not domain:
                continue
                
            if domain not in merged:
                # Initialize with the first occurrence of this domain
                merged[domain] = comp.copy()
                merged[domain]['sources'] = {comp.get('source', 'unknown')}
            else:
                # Merge metrics from different sources
                existing = merged[domain]
                
                # Track all sources
                existing_sources = existing.get('sources', set())
                existing_sources.add(comp.get('source', 'unknown'))
                existing['sources'] = existing_sources
                
                # Update metrics with the highest values (or average where appropriate)
                existing['common_keywords'] = max(
                    existing.get('common_keywords', 0),
                    comp.get('common_keywords', 0)
                )
                existing['traffic_share'] = max(
                    existing.get('traffic_share', 0),
                    comp.get('traffic_share', 0)
                )
                existing['backlinks'] = max(
                    existing.get('backlinks', 0),
                    comp.get('backlinks', 0)
                )
                existing['domain_score'] = max(
                    existing.get('domain_score', 0),
                    comp.get('domain_score', 0)
                )
                
                # Keep the most recent last_updated timestamp
                existing_last_updated = datetime.fromisoformat(existing.get('last_updated', '1970-01-01'))
                comp_last_updated = datetime.fromisoformat(comp.get('last_updated', '1970-01-01'))
                if comp_last_updated > existing_last_updated:
                    existing['last_updated'] = comp['last_updated']
        
        # Convert sources set to list for JSON serialization
        for comp in merged.values():
            if 'sources' in comp and isinstance(comp['sources'], set):
                comp['sources'] = list(comp['sources'])
        
        return list(merged.values())

    async def _update_domain_metrics(self, domain: str, metrics: Dict[str, Any]) -> None:
        """Update domain metrics in the database.
        
        Args:
            domain: Domain to update
            metrics: Domain metrics to store
        """
        if not self.domain_repo:
            return
            
        try:
            # Check if domain exists
            domain_obj = await self.domain_repo.get_by_domain(domain)
            
            if domain_obj:
                # Update existing domain
                update_data = {
                    'seo_metrics': metrics,
                    'updated_at': datetime.utcnow()
                }
                await self.domain_repo.update(domain_obj.id, update_data)
            
        except Exception as e:
            logger.error(f"Error updating domain metrics for {domain}: {str(e)}")
