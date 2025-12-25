#!/usr/bin/env python
"""
News Service - Integrates with GNews API to fetch industry news.

Following Semantic Seed coding standards with proper error handling,
logging, and type hints.
"""

import os
import json
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("news_service")

class NewsService:
    """
    Service for fetching news data using the GNews API.
    
    This service implements Sprint 4 requirements for real data integration
    with third-party news APIs.
    """
    
    def __init__(self):
        """Initialize the News Service."""
        self.api_key = os.getenv("GNEWS_API_KEY")
        if not self.api_key:
            logger.warning("GNews API key not found in environment variables")
        
        self.base_url = "https://gnews.io/api/v4"
        self.api_calls = 0
    
    async def get_company_news(self, company_name: str, max_results: int = 10) -> Dict[str, Any]:
        """Get news articles about a specific company.
        
        Args:
            company_name: Name of the company to get news for
            max_results: Maximum number of news articles to return
            
        Returns:
            Dictionary with news data and metadata
        """
        # Calculate date for last 30 days
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Build the request URL
        url = f"{self.base_url}/search"
        params = {
            "q": company_name,
            "lang": "en",
            "max": max_results,
            "from": from_date,
            "sortby": "relevance",
            "apikey": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.api_calls += 1
                    
                    if response.status != 200:
                        logger.error(f"GNews API error: {response.status} - {await response.text()}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "articles": []
                        }
                    
                    data = await response.json()
                    
                    # Process the news data
                    articles = data.get("articles", [])
                    return {
                        "success": True,
                        "articles": articles,
                        "metadata": {
                            "company": company_name,
                            "article_count": len(articles),
                            "api_provider": "GNews",
                            "query_timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error fetching news data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "articles": []
            }
    
    async def get_industry_news(self, industry: str, max_results: int = 10) -> Dict[str, Any]:
        """Get news articles about a specific industry.
        
        Args:
            industry: Industry to get news for
            max_results: Maximum number of news articles to return
            
        Returns:
            Dictionary with news data and metadata
        """
        # Calculate date for last 30 days
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Build the request URL
        url = f"{self.base_url}/search"
        params = {
            "q": f"{industry} industry trends",
            "lang": "en",
            "max": max_results,
            "from": from_date,
            "sortby": "relevance",
            "apikey": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.api_calls += 1
                    
                    if response.status != 200:
                        logger.error(f"GNews API error: {response.status} - {await response.text()}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "articles": []
                        }
                    
                    data = await response.json()
                    
                    # Process the news data
                    articles = data.get("articles", [])
                    return {
                        "success": True,
                        "articles": articles,
                        "metadata": {
                            "industry": industry,
                            "article_count": len(articles),
                            "api_provider": "GNews",
                            "query_timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error fetching industry news data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "articles": []
            }
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """Get statistics about API calls made by this service.
        
        Returns:
            Dictionary with API call statistics
        """
        return {"gnews_api_calls": self.api_calls}
