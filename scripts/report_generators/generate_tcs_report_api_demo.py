#!/usr/bin/env python
"""
TCS Report API Demo

This script demonstrates real API calls to all configured services in the .env file:
1. OpenAI (or Anthropic as fallback) for AI-driven analysis
2. GNews for industry news
3. SERPAPI for search insights
4. WHOAPI for domain information
5. IPInfo for geographic intelligence

Following Semantic Seed Venture Studio Coding Standards V2.0 with
comprehensive error handling and logging.
"""

import os
import json
import asyncio
import logging
import aiohttp
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tcs_api_demo")

# Load environment variables
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
WHOAPI_API_KEY = os.getenv("WHOAPI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
IPINFO_API_KEY = os.getenv("IPINFO_API_KEY")

class APIServices:
    """Class for making real API calls to various services."""
    
    def __init__(self):
        """Initialize the API services."""
        self.api_calls = {
            "openai": 0,
            "anthropic": 0,
            "gnews": 0,
            "whoapi": 0,
            "serpapi": 0,
            "ipinfo": 0
        }
        
        # Check API keys
        missing_keys = []
        if not OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        if not ANTHROPIC_API_KEY:
            missing_keys.append("ANTHROPIC_API_KEY")
        if not GNEWS_API_KEY:
            missing_keys.append("GNEWS_API_KEY")
        if not WHOAPI_API_KEY:
            missing_keys.append("WHOAPI_API_KEY")
        if not SERPAPI_API_KEY:
            missing_keys.append("SERPAPI_API_KEY")
        if not IPINFO_API_KEY:
            missing_keys.append("IPINFO_API_KEY")
        
        if missing_keys:
            logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
    
    async def call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API with fallback to Anthropic.
        
        Args:
            prompt: Prompt to send to the API
            
        Returns:
            Response from API with metadata
        """
        # First try OpenAI
        if OPENAI_API_KEY:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a competitive intelligence analyst providing insights with chain-of-thought reasoning."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                    
                    async with session.post(
                        "https://api.openai.com/v1/chat/completions", 
                        headers=headers, 
                        json=payload
                    ) as response:
                        self.api_calls["openai"] += 1
                        
                        if response.status != 200:
                            logger.error(f"OpenAI API error: {response.status} - {await response.text()}")
                            # Will attempt fallback to Anthropic below
                        else:
                            data = await response.json()
                            content = data["choices"][0]["message"]["content"]
                            return {
                                "success": True,
                                "provider": "OpenAI",
                                "model": OPENAI_MODEL,
                                "content": content,
                                "metadata": {
                                    "finish_reason": data["choices"][0].get("finish_reason"),
                                    "tokens": data.get("usage", {}).get("total_tokens", 0)
                                }
                            }
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {str(e)}")
                # Will attempt fallback to Anthropic below
        
        # Fallback to Anthropic if OpenAI fails or isn't configured
        if ANTHROPIC_API_KEY:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "anthropic-version": "2023-06-01",
                        "x-api-key": ANTHROPIC_API_KEY,
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": ANTHROPIC_MODEL,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 2000
                    }
                    
                    async with session.post(
                        "https://api.anthropic.com/v1/messages", 
                        headers=headers, 
                        json=payload
                    ) as response:
                        self.api_calls["anthropic"] += 1
                        
                        if response.status != 200:
                            logger.error(f"Anthropic API error: {response.status} - {await response.text()}")
                            return {
                                "success": False,
                                "error": f"Both OpenAI and Anthropic APIs failed",
                                "provider": "None"
                            }
                        
                        data = await response.json()
                        content = data["content"][0]["text"]
                        return {
                            "success": True,
                            "provider": "Anthropic",
                            "model": ANTHROPIC_MODEL,
                            "content": content,
                            "metadata": {
                                "stop_reason": data.get("stop_reason"),
                                "usage": data.get("usage", {})
                            }
                        }
            except Exception as e:
                logger.error(f"Error calling Anthropic API: {str(e)}")
        
        return {
            "success": False,
            "error": "All AI providers failed",
            "provider": "None",
            "content": "Unable to generate analysis due to API errors."
        }
    
    async def call_gnews(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Call GNews API to get news articles.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            News data with metadata
        """
        if not GNEWS_API_KEY:
            return {
                "success": False,
                "error": "GNews API key not configured",
                "articles": []
            }
        
        # Calculate date for last 30 days
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Build the request URL
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "max": max_results,
            "from": from_date,
            "sortby": "relevance",
            "apikey": GNEWS_API_KEY
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.api_calls["gnews"] += 1
                    
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
                            "article_count": len(articles),
                            "api_provider": "GNews",
                            "query": query,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error calling GNews API: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "articles": []
            }
    
    async def call_whoapi(self, domain: str) -> Dict[str, Any]:
        """Call WHOAPI to get domain information.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            Domain data with metadata
        """
        if not WHOAPI_API_KEY:
            return {
                "success": False,
                "error": "WHOAPI key not configured",
                "domain": domain
            }
        
        url = "https://api.whoapi.com/"
        params = {
            "domain": domain,
            "r": "whois",
            "apikey": WHOAPI_API_KEY
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.api_calls["whoapi"] += 1
                    
                    if response.status != 200:
                        logger.error(f"WHOAPI error: {response.status} - {await response.text()}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "domain": domain
                        }
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "domain": domain,
                        "registrar": data.get("registrar", "Unknown"),
                        "creation_date": data.get("date_created", "Unknown"),
                        "expiration_date": data.get("date_expires", "Unknown"),
                        "nameservers": data.get("nameservers", []),
                        "status": data.get("status", "Unknown"),
                        "metadata": {
                            "api_provider": "WHOAPI",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error calling WHOAPI: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "domain": domain
            }
    
    async def call_serpapi(self, query: str) -> Dict[str, Any]:
        """Call SERPAPI to get search results.
        
        Args:
            query: Search query
            
        Returns:
            Search results with metadata
        """
        if not SERPAPI_API_KEY:
            return {
                "success": False,
                "error": "SERPAPI key not configured",
                "query": query
            }
        
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "num": 10,
            "engine": "google",
            "api_key": SERPAPI_API_KEY
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.api_calls["serpapi"] += 1
                    
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
                        "top_results": organic_results[:3] if organic_results else [],
                        "has_ads": len(ads) > 0,
                        "ad_count": len(ads),
                        "related_queries": [item.get("query") for item in related_queries] if related_queries else [],
                        "metadata": {
                            "api_provider": "SERPAPI",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error calling SERPAPI: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def call_ipinfo(self, ip: str) -> Dict[str, Any]:
        """Call IPInfo API to get location data.
        
        Args:
            ip: IP address to analyze
            
        Returns:
            Location data with metadata
        """
        if not IPINFO_API_KEY:
            return {
                "success": False,
                "error": "IPInfo API key not configured",
                "ip": ip
            }
        
        url = f"https://ipinfo.io/{ip}/json"
        headers = {"Authorization": f"Bearer {IPINFO_API_KEY}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    self.api_calls["ipinfo"] += 1
                    
                    if response.status != 200:
                        logger.error(f"IPInfo API error: {response.status} - {await response.text()}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "ip": ip
                        }
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "ip": ip,
                        "city": data.get("city", "Unknown"),
                        "region": data.get("region", "Unknown"),
                        "country": data.get("country", "Unknown"),
                        "org": data.get("org", "Unknown"),
                        "postal": data.get("postal", "Unknown"),
                        "timezone": data.get("timezone", "Unknown"),
                        "location": data.get("loc", "0,0"),
                        "metadata": {
                            "api_provider": "IPInfo",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error calling IPInfo API: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ip": ip
            }
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """Get statistics about API calls made by this service.
        
        Returns:
            Dictionary with API call statistics
        """
        return self.api_calls


async def generate_tcs_api_demo():
    """Make real API calls to all configured services for TCS report data.
    
    Returns:
        Dictionary with the results of the API calls
    """
    logger.info("===== STARTING TCS API DEMO =====")
    
    # Initialize services
    api_services = APIServices()
    
    # Company info
    company_name = "Tata Consultancy Services"
    company_domain = "tcs.com"
    
    # Step 1: Call OpenAI API for TCS analysis (with fallback to Anthropic)
    logger.info("Calling AI API for TCS analysis...")
    ai_prompt = f"""
    Perform a comprehensive competitor analysis for {company_name}.
    
    Analyze the company's:
    1. Market position and competitive advantages
    2. Strengths and weaknesses compared to key competitors
    3. Key products, services, and value propositions
    4. Recent strategic initiatives and trends
    
    Structure your response as a JSON object with the following fields:
    - competitive_positioning: Overview of the company's market position
    - strengths: List of the company's key strengths
    - weaknesses: List of the company's key weaknesses
    - market_share: Estimated market share if available
    - industry_rank: Estimated industry rank if available
    - competitor_analysis: List of key competitors with their strengths, weaknesses, and threat level
    """
    ai_response = await api_services.call_openai(ai_prompt)
    
    # Step 2: Call GNews API for TCS news
    logger.info("Calling GNews API for TCS news...")
    news_response = await api_services.call_gnews(f"{company_name} technology services")
    
    # Step 3: Call WHOAPI for domain information
    logger.info("Calling WHOAPI for domain information...")
    domain_response = await api_services.call_whoapi(company_domain)
    
    # Step 4: Call SERPAPI for search insights
    logger.info("Calling SERPAPI for search insights...")
    search_response = await api_services.call_serpapi(f"{company_name} IT services")
    
    # Step 5: Call IPInfo API for geographic data
    # For demo purposes, we'll use Cloudflare's DNS which is 1.1.1.1
    # In a real scenario, we would resolve the domain to its IP first
    logger.info("Calling IPInfo API for geographic data...")
    ip_response = await api_services.call_ipinfo("1.1.1.1")
    
    # Collect all results
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "company": company_name,
        "domain": company_domain,
        "ai_analysis": ai_response,
        "news": news_response,
        "domain_info": domain_response,
        "search_insights": search_response,
        "location_data": ip_response,
        "api_calls": api_services.get_api_call_stats()
    }
    
    # Save results to file for examination
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"tcs_api_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"✅ API demo results saved to {output_file}")
    logger.info("===== TCS API DEMO COMPLETED =====")
    
    return {
        "success": True,
        "output_file": str(output_file),
        "api_calls": api_services.get_api_call_stats()
    }


if __name__ == "__main__":
    try:
        logger.info("Starting TCS API demo")
        result = asyncio.run(generate_tcs_api_demo())
        
        if result.get("success"):
            print(f"\n✅ TCS API Demo Successful")
            print(f"Output file: {result.get('output_file')}")
            
            # Print API stats
            print("\nAPI Usage Stats:")
            for api, count in result.get("api_calls", {}).items():
                print(f"- {api}: {count} calls")
        else:
            print(f"\n❌ TCS API Demo Failed")
            print(f"Error: {result.get('error')}")
    except Exception as e:
        print(f"\n❌ TCS API Demo Failed")
        print(f"Error: {str(e)}")
