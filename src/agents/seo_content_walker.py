"""SEO & Content Walker Agent for automated brand digital footprint analysis."""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter
import re
from urllib.parse import urlparse, urljoin
import json
import hashlib

# Web scraping imports
from bs4 import BeautifulSoup
import aiohttp
from playwright.async_api import async_playwright

# NLP and keyword extraction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Database
from sqlalchemy.orm import Session
from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus,
    KeywordSource,
    CompetitorCategory,
    GapType,
    ContentPriority
)

# Cache service
from src.services.cache_service import AsyncCacheService
from src.config import get_settings

# SERP Analysis
from src.services.serp_analyzer import SerpAnalyzer

# WebSocket progress notifications
from src.api.v1.websockets import (
    broadcast_progress,
    broadcast_status_change,
    broadcast_step_complete,
    broadcast_completion,
    broadcast_error
)

# Enhanced web scraping
from src.services.web_scraping import (
    EnhancedWebScrapingService,
    ScrapingConfig,
)

# Error handling and validation
from src.services.engarde_integration.error_handling import (
    WebsiteUnreachableError,
    InsufficientDataError,
    AnalysisTimeoutError,
    SERPAPIError,
    ScrapingError,
    handle_analysis_failure,
    retry_with_backoff,
    save_partial_results
)
from src.services.engarde_integration.validation import validate_url

logger = logging.getLogger(__name__)
settings = get_settings()


class BrandAnalysisQuestionnaire:
    """Data class for brand analysis questionnaire."""

    def __init__(
        self,
        brand_name: str,
        primary_website: str,
        industry: str,
        target_markets: List[str] = None,
        products_services: List[str] = None,
        known_competitors: List[str] = None,
        target_keywords: List[str] = None,
    ):
        self.brand_name = brand_name
        self.primary_website = primary_website
        self.industry = industry
        self.target_markets = target_markets or []
        self.products_services = products_services or []
        self.known_competitors = known_competitors or []
        self.target_keywords = target_keywords or []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrandAnalysisQuestionnaire':
        """Create questionnaire from dictionary."""
        return cls(
            brand_name=data.get('brand_name', ''),
            primary_website=data.get('primary_website', ''),
            industry=data.get('industry', ''),
            target_markets=data.get('target_markets', []),
            products_services=data.get('products_services', []),
            known_competitors=data.get('known_competitors', []),
            target_keywords=data.get('target_keywords', []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert questionnaire to dictionary."""
        return {
            'brand_name': self.brand_name,
            'primary_website': self.primary_website,
            'industry': self.industry,
            'target_markets': self.target_markets,
            'products_services': self.products_services,
            'known_competitors': self.known_competitors,
            'target_keywords': self.target_keywords,
        }


class SEOContentWalkerAgent:
    """Agent for automated SEO and content analysis."""

    def __init__(self, db: Session, cache: Optional[AsyncCacheService] = None):
        """Initialize the agent.

        Args:
            db: Database session for storing results
            cache: Optional cache service for performance optimization
        """
        self.db = db
        self.cache = cache
        self.max_pages_per_domain = 10
        self.max_keywords = 50
        self.max_competitors = 15

        # Initialize SERP analyzer
        self.serp_analyzer = SerpAnalyzer(cache=cache)

        # Initialize enhanced web scraping service
        scraping_config = ScrapingConfig(
            default_timeout=30,
            max_retries=3,
            respect_robots_txt=True,
            throttle_delay=1.0,
            use_playwright=False,  # Use lightweight scraping by default
            max_concurrent=5,
            enable_nlp=True,
        )
        self.enhanced_scraper = EnhancedWebScrapingService(config=scraping_config)

    async def analyze_brand(
        self,
        job_id: str,
        questionnaire: BrandAnalysisQuestionnaire
    ) -> Dict[str, Any]:
        """Perform complete brand digital footprint analysis.

        Args:
            job_id: UUID of the brand analysis job
            questionnaire: Brand analysis questionnaire data

        Returns:
            Dict containing analysis results
        """
        try:
            logger.info(f"Starting brand analysis for job {job_id}")

            # Update job status and broadcast
            await self._update_job_status(job_id, AnalysisStatus.CRAWLING, 10)
            await broadcast_progress(
                job_id, "crawling", 10,
                "Initializing website crawl...",
                total_steps=7, completed_steps=0
            )

            # Step 1: Crawl website
            await broadcast_progress(
                job_id, "crawling", 15,
                f"Crawling {questionnaire.primary_website}...",
                total_steps=7, completed_steps=1
            )
            site_data = await self.crawl_website(questionnaire.primary_website)
            await self._update_job_status(job_id, AnalysisStatus.CRAWLING, 30)
            await broadcast_step_complete(
                job_id, "Website Crawling", 1, 7,
                {"pages_crawled": len(site_data.get('pages', []))}
            )

            # Step 2: Extract keywords
            await self._update_job_status(job_id, AnalysisStatus.ANALYZING, 40)
            await broadcast_progress(
                job_id, "analyzing", 40,
                "Extracting keywords from website content...",
                total_steps=7, completed_steps=2
            )
            keywords = await self.extract_keywords(site_data, questionnaire)
            await self._save_keywords(job_id, keywords)
            await broadcast_step_complete(
                job_id, "Keyword Extraction", 2, 7,
                {"keywords_found": len(keywords)}
            )
            await self._update_job_status(job_id, AnalysisStatus.ANALYZING, 50)

            # Step 3: Analyze SERP using real SERP API
            await broadcast_progress(
                job_id, "analyzing", 55,
                "Analyzing search engine results...",
                total_steps=7, completed_steps=3
            )
            serp_data = await self.analyze_serp(keywords[:20])
            await broadcast_step_complete(
                job_id, "SERP Analysis", 3, 7,
                {"keywords_analyzed": len(serp_data)}
            )
            await self._update_job_status(job_id, AnalysisStatus.ANALYZING, 70)

            # Step 4: Identify competitors
            await self._update_job_status(job_id, AnalysisStatus.PROCESSING, 75)
            await broadcast_progress(
                job_id, "processing", 75,
                "Identifying competitors from SERP data...",
                total_steps=7, completed_steps=4
            )
            competitors = await self.identify_competitors(
                serp_data,
                questionnaire.known_competitors
            )
            await self._save_competitors(job_id, competitors)
            await broadcast_step_complete(
                job_id, "Competitor Identification", 4, 7,
                {"competitors_found": len(competitors)}
            )
            await self._update_job_status(job_id, AnalysisStatus.PROCESSING, 85)

            # Step 5: Generate content opportunities
            await broadcast_progress(
                job_id, "processing", 90,
                "Generating content opportunities...",
                total_steps=7, completed_steps=5
            )
            opportunities = await self.generate_content_opportunities(
                site_data,
                keywords,
                competitors
            )
            await self._save_content_opportunities(job_id, opportunities)
            await broadcast_step_complete(
                job_id, "Content Opportunity Analysis", 5, 7,
                {"opportunities_found": len(opportunities)}
            )

            # Step 6: Compile results
            await broadcast_progress(
                job_id, "processing", 95,
                "Finalizing analysis...",
                total_steps=7, completed_steps=6
            )
            results = {
                'keywords_found': len(keywords),
                'competitors_identified': len(competitors),
                'content_opportunities': len(opportunities),
                'analysis_timestamp': datetime.utcnow().isoformat(),
            }

            await self._update_job_status(
                job_id,
                AnalysisStatus.COMPLETED,
                100,
                results=results
            )

            # Broadcast completion
            await broadcast_completion(
                job_id,
                success=True,
                summary=results
            )
            await broadcast_step_complete(
                job_id, "Analysis Complete", 7, 7,
                results
            )

            logger.info(f"Completed brand analysis for job {job_id}")
            return results

        except Exception as e:
            logger.error(f"Error in brand analysis for job {job_id}: {str(e)}")

            # Broadcast error
            await broadcast_error(
                job_id,
                error_message=str(e),
                error_code="ANALYSIS_FAILED",
                recoverable=False
            )

            await self._update_job_status(
                job_id,
                AnalysisStatus.FAILED,
                error_message=str(e)
            )
            raise

    async def crawl_website(self, url: str) -> Dict[str, Any]:
        """Crawl website and extract content.

        Args:
            url: Website URL to crawl

        Returns:
            Dict containing crawled content and metadata
        """
        logger.info(f"Crawling website: {url}")

        # Check cache first
        if self.cache and settings.CACHE_ENABLED:
            cache_key = hashlib.md5(f"crawl:{url}".encode()).hexdigest()
            cached_result = await self.cache.get(
                cache_key,
                category="website_crawl"
            )
            if cached_result:
                logger.info(f"Cache hit for website crawl: {url}")
                return cached_result

        pages_content = []
        visited_urls = set()
        to_visit = [url]
        base_domain = urlparse(url).netloc

        async with aiohttp.ClientSession() as session:
            while to_visit and len(visited_urls) < self.max_pages_per_domain:
                current_url = to_visit.pop(0)

                if current_url in visited_urls:
                    continue

                try:
                    async with session.get(
                        current_url,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            continue

                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Extract text content
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text = soup.get_text()
                        text = ' '.join(text.split())  # Clean whitespace

                        pages_content.append({
                            'url': current_url,
                            'title': soup.find('title').string if soup.find('title') else '',
                            'content': text,
                            'meta_description': self._extract_meta_description(soup),
                            'headings': self._extract_headings(soup),
                        })

                        visited_urls.add(current_url)

                        # Find more links to crawl
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(current_url, href)

                            # Only crawl same domain
                            if urlparse(full_url).netloc == base_domain:
                                if full_url not in visited_urls and full_url not in to_visit:
                                    to_visit.append(full_url)

                except Exception as e:
                    logger.warning(f"Error crawling {current_url}: {str(e)}")
                    continue

        result = {
            'pages': pages_content,
            'total_pages': len(pages_content),
            'base_url': url,
            'domain': base_domain,
        }

        # Cache the result
        if self.cache and settings.CACHE_ENABLED:
            cache_key = hashlib.md5(f"crawl:{url}".encode()).hexdigest()
            await self.cache.set(
                cache_key,
                result,
                ttl=settings.CACHE_TTL_WEBSITE_CRAWL,
                category="website_crawl"
            )
            logger.info(f"Cached website crawl result for: {url}")

        return result

    async def extract_keywords(
        self,
        site_data: Dict[str, Any],
        questionnaire: BrandAnalysisQuestionnaire
    ) -> List[Dict[str, Any]]:
        """Extract keywords from website content using TF-IDF.

        Args:
            site_data: Crawled website data
            questionnaire: Brand questionnaire with context

        Returns:
            List of discovered keywords with relevance scores
        """
        logger.info("Extracting keywords from website content")

        # Combine all page content
        all_text = ' '.join([page['content'] for page in site_data['pages']])
        all_headings = ' '.join([
            ' '.join(page['headings'])
            for page in site_data['pages']
        ])

        # Weight headings more heavily
        combined_text = all_text + ' ' + (all_headings * 3)

        # Extract keywords using TF-IDF
        keywords = self._extract_tfidf_keywords(combined_text)

        # Extract bi-grams and tri-grams
        phrases = self._extract_phrases(combined_text)

        # Combine and score
        all_keywords = keywords + phrases

        # Filter and enhance with user-provided keywords
        if questionnaire.target_keywords:
            for keyword in questionnaire.target_keywords:
                if keyword.lower() in combined_text.lower():
                    all_keywords.append({
                        'keyword': keyword,
                        'source': KeywordSource.WEBSITE_CONTENT,
                        'relevance_score': 0.95,  # High relevance for user-provided
                    })

        # Sort by relevance and limit
        all_keywords.sort(key=lambda x: x['relevance_score'], reverse=True)
        return all_keywords[:self.max_keywords]

    async def analyze_serp(self, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze SERP results for keywords using SerpAPI integration.

        This method now uses the real SERP analyzer to fetch actual search
        engine results, keyword difficulty, search volume, and SERP features.

        Args:
            keywords: List of keywords to analyze

        Returns:
            Dict containing comprehensive SERP analysis data
        """
        logger.info(f"Analyzing SERP for {len(keywords)} keywords using SerpAnalyzer")

        serp_results = {}

        # Use the SERP analyzer to get real data
        async with self.serp_analyzer as analyzer:
            for kw_data in keywords:
                keyword = kw_data['keyword']

                try:
                    # Get SERP results for this keyword
                    serp_data = await analyzer.get_serp_results(
                        keyword,
                        location="United States"
                    )

                    # Extract domains from results
                    ranking_domains = analyzer.extract_domains_from_serp(serp_data)

                    # Calculate keyword difficulty
                    difficulty = analyzer.calculate_keyword_difficulty(serp_data)

                    # Get search volume
                    search_volume = await analyzer.get_search_volume(keyword)

                    # Identify SERP features
                    serp_features = analyzer.identify_serp_features(serp_data)

                    # Compile comprehensive results
                    serp_results[keyword] = {
                        'keyword': keyword,
                        'search_volume': search_volume,
                        'difficulty': difficulty,
                        'ranking_domains': [d['domain'] for d in ranking_domains[:10]],
                        'domain_data': ranking_domains[:10],  # Include full domain data
                        'serp_features': serp_features,
                        'top_3_urls': [
                            r.get('link', '') for r in
                            serp_data.get('organic_results', [])[:3]
                        ],
                        'related_searches': serp_features.get('related_searches', []),
                        'people_also_ask': serp_features.get('paa_questions', []),
                        'analyzed_at': datetime.utcnow().isoformat()
                    }

                    logger.info(
                        f"SERP analysis complete for '{keyword}': "
                        f"volume={search_volume}, difficulty={difficulty:.1f}"
                    )

                except Exception as e:
                    logger.error(f"Error analyzing SERP for '{keyword}': {str(e)}")
                    # Fallback to estimates if SERP API fails
                    serp_results[keyword] = {
                        'keyword': keyword,
                        'search_volume': self._estimate_search_volume(keyword),
                        'difficulty': self._estimate_difficulty(keyword),
                        'ranking_domains': self._get_placeholder_domains(),
                        'serp_features': {'has_featured_snippet': False, 'total_features': 0},
                        'error': str(e)
                    }

        return serp_results

    async def identify_competitors(
        self,
        serp_data: Dict[str, Any],
        known_competitors: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Identify competitors from SERP analysis.

        Args:
            serp_data: SERP analysis results
            known_competitors: List of known competitor domains

        Returns:
            List of identified competitors with relevance scores
        """
        logger.info("Identifying competitors from SERP data")

        # Count domain frequency in SERP
        domain_counter = Counter()

        for keyword, data in serp_data.items():
            for domain in data.get('ranking_domains', []):
                domain_counter[domain] += 1

        # Calculate relevance scores
        max_count = max(domain_counter.values()) if domain_counter else 1
        competitors = []

        for domain, count in domain_counter.most_common(self.max_competitors):
            relevance = count / max_count

            # Categorize competitor
            if count >= max_count * 0.7:
                category = CompetitorCategory.PRIMARY
            elif count >= max_count * 0.4:
                category = CompetitorCategory.SECONDARY
            elif count >= max_count * 0.2:
                category = CompetitorCategory.EMERGING
            else:
                category = CompetitorCategory.NICHE

            competitors.append({
                'domain': domain,
                'name': self._extract_brand_name(domain),
                'relevance_score': relevance,
                'category': category,
                'overlap_percentage': (count / len(serp_data)) * 100,
                'keyword_overlap': list(serp_data.keys())[:5],  # Sample keywords
            })

        # Add known competitors if not already found
        if known_competitors:
            existing_domains = {c['domain'] for c in competitors}
            for comp_domain in known_competitors:
                if comp_domain not in existing_domains:
                    competitors.append({
                        'domain': comp_domain,
                        'name': self._extract_brand_name(comp_domain),
                        'relevance_score': 0.5,
                        'category': CompetitorCategory.SECONDARY,
                        'confirmed': True,
                    })

        return competitors

    async def scrape_competitor_profiles(
        self,
        competitor_domains: List[str],
        max_blog_posts: int = 5
    ) -> Dict[str, Any]:
        """Scrape comprehensive competitor profiles using enhanced scraper.

        Args:
            competitor_domains: List of competitor domains to analyze
            max_blog_posts: Maximum blog posts to scrape per competitor

        Returns:
            Dict mapping domain to CompetitorProfile
        """
        logger.info(f"Scraping profiles for {len(competitor_domains)} competitors")

        profiles = {}

        for domain in competitor_domains:
            try:
                profile = await self.enhanced_scraper.scrape_competitor_profile(
                    domain=domain,
                    max_blog_posts=max_blog_posts
                )
                profiles[domain] = profile

                logger.info(
                    f"Competitor profile scraped for {domain}: "
                    f"{len(profile.blog_posts)} blog posts, "
                    f"{len(profile.social_links)} social links"
                )

            except Exception as e:
                logger.error(f"Failed to scrape competitor profile for {domain}: {str(e)}")
                profiles[domain] = None

        return profiles

    async def analyze_competitor_content(
        self,
        competitor_domains: List[str]
    ) -> Dict[str, List[Any]]:
        """Analyze content themes and sentiment for competitors.

        Args:
            competitor_domains: List of competitor domains

        Returns:
            Dict mapping domain to list of ContentAnalysis
        """
        logger.info(f"Analyzing content for {len(competitor_domains)} competitors")

        analyses = {}

        for domain in competitor_domains:
            try:
                # Get competitor URLs to analyze
                urls = [
                    f"https://{domain}",
                    f"https://{domain}/about",
                    f"https://{domain}/blog",
                ]

                content_analyses = await self.enhanced_scraper.analyze_content_themes(urls)
                analyses[domain] = content_analyses

                logger.info(f"Analyzed {len(content_analyses)} pages for {domain}")

            except Exception as e:
                logger.error(f"Failed to analyze content for {domain}: {str(e)}")
                analyses[domain] = []

        return analyses

    async def discover_competitor_backlinks(
        self,
        competitor_domains: List[str],
        limit_per_domain: int = 50
    ) -> Dict[str, List[Any]]:
        """Discover backlinks for competitor domains.

        Args:
            competitor_domains: List of competitor domains
            limit_per_domain: Maximum backlinks to discover per domain

        Returns:
            Dict mapping domain to list of BacklinkData
        """
        logger.info(f"Discovering backlinks for {len(competitor_domains)} competitors")

        backlinks = {}

        for domain in competitor_domains:
            try:
                domain_backlinks = await self.enhanced_scraper.discover_backlinks(
                    domain=domain,
                    limit=limit_per_domain
                )
                backlinks[domain] = domain_backlinks

                logger.info(f"Discovered {len(domain_backlinks)} backlinks for {domain}")

            except Exception as e:
                logger.error(f"Failed to discover backlinks for {domain}: {str(e)}")
                backlinks[domain] = []

        return backlinks

    async def generate_content_opportunities(
        self,
        site_data: Dict[str, Any],
        keywords: List[Dict[str, Any]],
        competitors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate content opportunity recommendations.

        Args:
            site_data: Crawled website data
            keywords: Discovered keywords
            competitors: Identified competitors

        Returns:
            List of content opportunities
        """
        logger.info("Generating content opportunities")

        opportunities = []

        # Find high-value keywords with low content coverage
        for kw in keywords[:20]:
            keyword = kw['keyword']

            # Check if keyword is covered in existing content
            coverage = sum(
                1 for page in site_data['pages']
                if keyword.lower() in page['content'].lower()
            )

            if coverage < 2:  # Low coverage
                opportunities.append({
                    'topic': f"Content about {keyword}",
                    'gap_type': GapType.MISSING_CONTENT,
                    'traffic_potential': kw.get('search_volume', 1000),
                    'difficulty': kw.get('difficulty', 50),
                    'priority': self._calculate_priority(
                        kw.get('relevance_score', 0.5),
                        coverage
                    ),
                    'recommended_format': 'blog',
                })

        return opportunities[:10]  # Return top 10 opportunities

    # Helper methods

    def _extract_tfidf_keywords(self, text: str, max_features: int = 30) -> List[Dict[str, Any]]:
        """Extract keywords using TF-IDF."""
        try:
            vectorizer = TfidfVectorizer(
                max_features=max_features,
                stop_words='english',
                ngram_range=(1, 1)
            )

            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            keywords = []
            for word, score in zip(feature_names, scores):
                if len(word) > 2 and score > 0:  # Filter short words
                    keywords.append({
                        'keyword': word,
                        'source': KeywordSource.NLP_EXTRACTION,
                        'relevance_score': float(score),
                    })

            return keywords
        except Exception as e:
            logger.warning(f"Error in TF-IDF extraction: {str(e)}")
            return []

    def _extract_phrases(self, text: str) -> List[Dict[str, Any]]:
        """Extract multi-word phrases."""
        try:
            vectorizer = TfidfVectorizer(
                max_features=20,
                stop_words='english',
                ngram_range=(2, 3)
            )

            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            phrases = []
            for phrase, score in zip(feature_names, scores):
                if score > 0:
                    phrases.append({
                        'keyword': phrase,
                        'source': KeywordSource.NLP_EXTRACTION,
                        'relevance_score': float(score),
                    })

            return phrases
        except Exception as e:
            logger.warning(f"Error in phrase extraction: {str(e)}")
            return []

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from HTML."""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta['content'] if meta and meta.get('content') else ''

    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract all headings from HTML."""
        headings = []
        for tag in ['h1', 'h2', 'h3']:
            for heading in soup.find_all(tag):
                text = heading.get_text().strip()
                if text:
                    headings.append(text)
        return headings

    def _estimate_search_volume(self, keyword: str) -> int:
        """Estimate search volume (placeholder)."""
        # In production, use actual API data
        return len(keyword.split()) * 1000

    def _estimate_difficulty(self, keyword: str) -> float:
        """Estimate keyword difficulty (placeholder)."""
        # In production, use actual SEO tools
        return min(len(keyword) * 5.0, 100.0)

    def _get_placeholder_domains(self) -> List[str]:
        """Get placeholder ranking domains."""
        return [
            'competitor1.com',
            'competitor2.com',
            'competitor3.com',
        ]

    def _extract_brand_name(self, domain: str) -> str:
        """Extract brand name from domain."""
        # Remove TLD and clean up
        name = domain.split('.')[0]
        return name.title()

    def _calculate_priority(self, relevance: float, coverage: int) -> ContentPriority:
        """Calculate content opportunity priority."""
        if relevance > 0.7 and coverage < 2:
            return ContentPriority.HIGH
        elif relevance > 0.4 or coverage < 3:
            return ContentPriority.MEDIUM
        else:
            return ContentPriority.LOW

    async def _update_job_status(
        self,
        job_id: str,
        status: AnalysisStatus,
        progress: int = None,
        results: Dict[str, Any] = None,
        error_message: str = None
    ):
        """Update job status in database."""
        job = self.db.query(BrandAnalysisJob).filter(
            BrandAnalysisJob.id == job_id
        ).first()

        if job:
            job.status = status
            if progress is not None:
                job.progress = progress
            if results:
                job.results = results
            if error_message:
                job.error_message = error_message
            if status == AnalysisStatus.COMPLETED:
                job.completed_at = datetime.utcnow()

            job.updated_at = datetime.utcnow()
            self.db.commit()

    async def _save_keywords(self, job_id: str, keywords: List[Dict[str, Any]]):
        """Save discovered keywords to database."""
        for kw_data in keywords:
            keyword = DiscoveredKeyword(
                job_id=job_id,
                keyword=kw_data['keyword'],
                source=kw_data['source'],
                search_volume=kw_data.get('search_volume'),
                difficulty=kw_data.get('difficulty'),
                relevance_score=kw_data['relevance_score'],
                current_ranking=kw_data.get('current_ranking'),
                serp_features=kw_data.get('serp_features'),
            )
            self.db.add(keyword)

        self.db.commit()

    async def _save_competitors(self, job_id: str, competitors: List[Dict[str, Any]]):
        """Save identified competitors to database."""
        for comp_data in competitors:
            competitor = IdentifiedCompetitor(
                job_id=job_id,
                domain=comp_data['domain'],
                name=comp_data.get('name'),
                relevance_score=comp_data['relevance_score'],
                category=comp_data['category'],
                overlap_percentage=comp_data.get('overlap_percentage'),
                keyword_overlap=comp_data.get('keyword_overlap'),
                content_similarity=comp_data.get('content_similarity'),
                confirmed=comp_data.get('confirmed', False),
            )
            self.db.add(competitor)

        self.db.commit()

    async def _save_content_opportunities(
        self,
        job_id: str,
        opportunities: List[Dict[str, Any]]
    ):
        """Save content opportunities to database."""
        for opp_data in opportunities:
            opportunity = ContentOpportunity(
                job_id=job_id,
                topic=opp_data['topic'],
                gap_type=opp_data['gap_type'],
                traffic_potential=opp_data.get('traffic_potential'),
                difficulty=opp_data.get('difficulty'),
                priority=opp_data['priority'],
                recommended_format=opp_data.get('recommended_format'),
            )
            self.db.add(opportunity)

        self.db.commit()
