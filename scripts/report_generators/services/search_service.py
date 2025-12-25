#!/usr/bin/env python
"""
Search Insights Service - Integrates with SERPAPI for search engine data.

This service implements Sprint 4 requirements for search data integration
with proper error handling and fallback mechanisms.

Following Semantic Seed coding standards.
"""

import os
import json
import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("search_service")

class SearchService:
    """
    Service for search engine insights using SERPAPI.
    
    This service integrates with SERPAPI to provide search engine positioning
    and trend data for the TCS report.
    """
    
    def __init__(self):
        """Initialize the Search Service."""
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("SERPAPI key not found in environment variables")
        
        self.base_url = "https://serpapi.com/search"
        self.api_calls = 0
    
    async def get_search_insights(self, query: str, num_results: int = 20) -> Dict[str, Any]:
        """Get search engine insights for a query.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Dictionary with search insight data
        """
        params = {
            "q": query,
            "num": num_results,
            "engine": "google",
            "api_key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    self.api_calls += 1
                    
                    if response.status != 200:
                        logger.error(f"SERPAPI error: {response.status} - {await response.text()}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "query": query
                        }
                    
                    data = await response.json()
                    
                    # Extract and structure the results
                    organic_results = data.get("organic_results", [])
                    ads = data.get("ads", [])
                    related_queries = data.get("related_searches", [])
                    
                    return {
                        "success": True,
                        "query": query,
                        "result_count": len(organic_results),
                        "top_results": organic_results[:5] if organic_results else [],
                        "has_ads": len(ads) > 0,
                        "ad_count": len(ads),
                        "related_queries": [item.get("query") for item in related_queries] if related_queries else [],
                        "metadata": {
                            "api_provider": "SERPAPI",
                            "query_timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error getting search insights for '{query}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def get_company_positioning(self, company_name: str, industry: str) -> Dict[str, Any]:
        """Get search engine positioning data for a company in its industry.
        
        Args:
            company_name: Name of the company
            industry: Industry for competitive analysis
            
        Returns:
            Dictionary with positioning data
        """
        # Construct industry query
        industry_query = f"top {industry} companies"
        
        try:
            # Get industry search results
            industry_results = await self.get_search_insights(industry_query)
            
            # Get company-specific results
            company_results = await self.get_search_insights(company_name)
            
            # Analyze company position in industry results
            industry_position = None
            if industry_results.get("success"):
                top_results = industry_results.get("top_results", [])
                for i, result in enumerate(top_results):
                    if company_name.lower() in result.get("title", "").lower() or \
                       company_name.lower() in result.get("snippet", "").lower():
                        industry_position = i + 1
                        break
            
            # Get direct competitors from related queries
            competitors = []
            if company_results.get("success"):
                related = company_results.get("related_queries", [])
                for query in related:
                    if "vs" in query.lower() or "alternative" in query.lower() or "competitor" in query.lower():
                        competitors.append(query)
            
            return {
                "success": True,
                "company": company_name,
                "industry": industry,
                "industry_position": industry_position,
                "search_volume_indicators": {
                    "has_knowledge_panel": "knowledge_graph" in company_results,
                    "ad_count": company_results.get("ad_count", 0),
                    "result_count": company_results.get("result_count", 0)
                },
                "potential_competitors": competitors[:5],
                "metadata": {
                    "api_provider": "SERPAPI",
                    "query_timestamp": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing company positioning: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "company": company_name
            }
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """Get statistics about API calls made by this service.
        
        Returns:
            Dictionary with API call statistics
        """
        return {"serpapi_calls": self.api_calls}
