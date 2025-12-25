#!/usr/bin/env python
"""
TCS Report Generator with API Integration and Visualizations

This script generates a comprehensive TCS report by:
1. Making real API calls to various services (OpenAI, GNews, WHOAPI, SERPAPI, IPInfo)
2. Creating data visualizations from the API responses
3. Generating a PDF report with visualizations and analysis

Following Semantic Seed Venture Studio Coding Standards V2.0
Implements BDD principles with proper error handling and logging.
"""

import os
import json
import logging
import traceback
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, UTC
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import visualization and PDF export modules
from scripts.report_generators.visualize_api_data import ReportVisualizer
from scripts.report_generators.services.pdf_export_service import PDFExportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tcs_report_generator")

class TCSReportGenerator:
    """
    TCS Report Generator with API Integration and Visualizations
    
    Generates a comprehensive report for Tata Consultancy Services using
    real API calls, data visualization, and PDF export.
    """
    
    def __init__(self):
        """Initialize the TCS report generator."""
        self.output_dir = Path("exports")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create API keys dictionary from environment variables
        self.api_keys = {
            "openai": os.environ.get("OPENAI_API_KEY", ""),
            "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
            "gnews": os.environ.get("GNEWS_API_KEY", ""),
            "whoapi": os.environ.get("WHOAPI_API_KEY", ""),
            "serpapi": os.environ.get("SERPAPI_API_KEY", ""),
            "ipinfo": os.environ.get("IPINFO_API_KEY", "")
        }
        
        # Initialize API usage counters
        self.api_usage = {key: 0 for key in self.api_keys.keys()}
        
        # Initialize services
        self.visualizer = ReportVisualizer()
        self.pdf_exporter = PDFExportService()
    
    async def call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call OpenAI API for AI analysis.
        
        Args:
            prompt: The prompt for analysis
            
        Returns:
            AI analysis response
        """
        logger.info("Calling AI API for TCS analysis...")
        
        # Check if API key is available
        if not self.api_keys["openai"]:
            logger.warning("No OpenAI API key found. Using fallback response.")
            return {
                "success": False,
                "error": "No API key",
                "content": "{}"
            }
        
        try:
            # Construct the prompt for competitor analysis
            system_prompt = (
                "You are an expert in competitive intelligence and market analysis. "
                "Provide a detailed analysis of the company based on the request."
            )
            
            prompt = (
                f"Provide a comprehensive competitive analysis of Tata Consultancy Services (TCS). "
                f"Format your response as a single JSON object with the following structure:\n"
                f"- competitive_positioning: A paragraph about TCS's market position\n"
                f"- strengths: An array of TCS's key strengths (as strings)\n"
                f"- weaknesses: An array of TCS's key weaknesses (as strings)\n"
                f"- market_share: A string describing TCS's market share\n"
                f"- industry_rank: A string indicating TCS's rank in the industry\n"
                f"- competitor_analysis: An array of objects for each major competitor with properties:\n"
                f"  - competitor_name: Name of the competitor\n"
                f"  - strengths: Array of the competitor's strengths\n"
                f"  - weaknesses: Array of the competitor's weaknesses\n"
                f"  - threat_level: String indicating threat level ('Low', 'Medium', 'High')\n\n"
                f"Format the entire response as a valid JSON object."
            )
            
            # Make OpenAI API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['openai']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2
                    },
                    timeout=30
                ) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        self.api_usage["openai"] += 1
                        
                        # Extract the response content
                        choices = data.get("choices", [])
                        if choices:
                            message = choices[0].get("message", {})
                            content = message.get("content", "{}")
                            finish_reason = choices[0].get("finish_reason")
                            
                            # Get token usage
                            usage = data.get("usage", {})
                            total_tokens = usage.get("total_tokens", 0)
                            
                            return {
                                "success": True,
                                "provider": "OpenAI",
                                "model": "gpt-4",
                                "content": content,
                                "metadata": {
                                    "finish_reason": finish_reason,
                                    "tokens": total_tokens
                                }
                            }
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    
                    # Try fallback to Anthropic if available
                    if self.api_keys["anthropic"]:
                        logger.info("Falling back to Anthropic API...")
                        return await self.call_anthropic_api(prompt)
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "content": "{}"
                    }
        
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try fallback to Anthropic if available
            if self.api_keys["anthropic"]:
                logger.info("Falling back to Anthropic API due to error...")
                return await self.call_anthropic_api(prompt)
            
            return {
                "success": False,
                "error": str(e),
                "content": "{}"
            }
    
    async def call_anthropic_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Anthropic API as a fallback for AI analysis.
        
        Args:
            prompt: The prompt for analysis
            
        Returns:
            AI analysis response
        """
        # Check if API key is available
        if not self.api_keys["anthropic"]:
            logger.warning("No Anthropic API key found. Using fallback response.")
            return {
                "success": False,
                "error": "No API key",
                "content": "{}"
            }
        
        try:
            # Make Anthropic API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_keys["anthropic"],
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-2",
                        "max_tokens": 1000,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2
                    },
                    timeout=30
                ) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        self.api_usage["anthropic"] += 1
                        
                        # Extract the response content
                        content = data.get("content", [{}])[0].get("text", "{}")
                        
                        return {
                            "success": True,
                            "provider": "Anthropic",
                            "model": "claude-2",
                            "content": content,
                            "metadata": {
                                "finish_reason": "stop",
                                "tokens": 0  # Anthropic doesn't provide token count in the same way
                            }
                        }
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"Anthropic API error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "content": "{}"
                    }
        
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "content": "{}"
            }
    
    async def call_gnews_api(self, query: str = "Tata Consultancy Services") -> Dict[str, Any]:
        """
        Call GNews API for news data.
        
        Args:
            query: Search query for news
            
        Returns:
            News API response
        """
        logger.info(f"Calling GNews API for {query} news...")
        
        # Check if API key is available
        if not self.api_keys["gnews"]:
            logger.warning("No GNews API key found. Using fallback response.")
            return {
                "success": False,
                "error": "No API key",
                "articles": []
            }
        
        try:
            # Calculate date range (last 30 days)
            from_date = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Construct the GNews API URL
            url = (
                f"https://gnews.io/api/v4/search"
                f"?q={query}"
                f"&lang=en"
                f"&country=us"
                f"&from={from_date}"
                f"&token={self.api_keys['gnews']}"
                f"&max=10"
            )
            
            # Make GNews API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        self.api_usage["gnews"] += 1
                        
                        # Extract articles
                        articles = data.get("articles", [])
                        
                        return {
                            "success": True,
                            "articles": articles
                        }
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"GNews API error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "articles": []
                    }
        
        except Exception as e:
            logger.error(f"Error calling GNews API: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "articles": []
            }
    
    async def call_whoapi(self, domain: str = "tcs.com") -> Dict[str, Any]:
        """
        Call WHOAPI for domain information.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            WHOAPI response with domain information
        """
        logger.info(f"Calling WHOAPI for domain information on {domain}...")
        
        # Check if API key is available
        if not self.api_keys["whoapi"]:
            logger.warning("No WHOAPI key found. Using fallback response.")
            return {
                "success": False,
                "error": "No API key",
                "domain": domain
            }
        
        try:
            # Construct the WHOAPI URL
            url = (
                f"https://api.whoapi.com/"
                f"?domain={domain}"
                f"&r=whois"
                f"&apikey={self.api_keys['whoapi']}"
            )
            
            # Make WHOAPI request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        self.api_usage["whoapi"] += 1
                        
                        # Extract domain information
                        return {
                            "success": True,
                            "domain": domain,
                            "registrar": data.get("registrar", {}).get("name", "Unknown"),
                            "creation_date": data.get("date_created", "Unknown"),
                            "expiration_date": data.get("date_expires", "Unknown"),
                            "nameservers": data.get("nameservers", []),
                            "status": data.get("status", "Unknown"),
                            "metadata": {
                                "api_provider": "WHOAPI",
                                "timestamp": datetime.now(UTC).isoformat()
                            }
                        }
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"WHOAPI error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "domain": domain
                    }
        
        except Exception as e:
            logger.error(f"Error calling WHOAPI: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "domain": domain
            }
    
    async def call_serpapi(self, query: str = "Tata Consultancy Services IT services") -> Dict[str, Any]:
        """
        Call SERPAPI for search engine data.
        
        Args:
            query: Search query
            
        Returns:
            SERPAPI response with search results
        """
        logger.info(f"Calling SERPAPI for search insights on '{query}'...")
        
        # Check if API key is available
        if not self.api_keys["serpapi"]:
            logger.warning("No SERPAPI key found. Using fallback response.")
            return {
                "success": False,
                "error": "No API key",
                "query": query
            }
        
        try:
            # Construct the SERPAPI URL
            url = (
                f"https://serpapi.com/search.json"
                f"?q={query}"
                f"&api_key={self.api_keys['serpapi']}"
                f"&num=10"
            )
            
            # Make SERPAPI request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=20) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        self.api_usage["serpapi"] += 1
                        
                        # Extract search information
                        organic_results = data.get("organic_results", [])
                        related_searches = data.get("related_searches", [])
                        
                        # Process top results
                        top_results = []
                        for result in organic_results:
                            top_results.append({
                                "position": result.get("position", 0),
                                "title": result.get("title", ""),
                                "link": result.get("link", ""),
                                "redirect_link": result.get("redirect_link", ""),
                                "displayed_link": result.get("displayed_link", ""),
                                "favicon": result.get("favicon", ""),
                                "snippet": result.get("snippet", ""),
                                "snippet_highlighted_words": result.get("snippet_highlighted_words", []),
                                "sitelinks": result.get("sitelinks", {}),
                                "source": result.get("source", "")
                            })
                        
                        # Process related searches
                        related_queries = []
                        for search in related_searches:
                            related_queries.append(search.get("query", None))
                        
                        # Check for ad information
                        ads = data.get("ads", [])
                        
                        return {
                            "success": True,
                            "query": query,
                            "result_count": len(organic_results),
                            "top_results": top_results,
                            "has_ads": bool(ads),
                            "ad_count": len(ads),
                            "related_queries": related_queries,
                            "metadata": {
                                "api_provider": "SERPAPI",
                                "timestamp": datetime.now(UTC).isoformat()
                            }
                        }
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"SERPAPI error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "query": query
                    }
        
        except Exception as e:
            logger.error(f"Error calling SERPAPI: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def call_ipinfo_api(self, ip: str = "1.1.1.1") -> Dict[str, Any]:
        """
        Call IPInfo API for location data.
        
        Args:
            ip: IP address to analyze
            
        Returns:
            IPInfo response with location data
        """
        logger.info(f"Calling IPInfo API for geographic data on {ip}...")
        
        # Check if API key is available
        if not self.api_keys["ipinfo"]:
            logger.warning("No IPInfo API key found. Using fallback response.")
            return {
                "success": False,
                "error": "No API key",
                "ip": ip
            }
        
        try:
            # Construct the IPInfo URL
            url = f"https://ipinfo.io/{ip}?token={self.api_keys['ipinfo']}"
            
            # Make IPInfo API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    # Check if the request was successful
                    if response.status == 200:
                        data = await response.json()
                        self.api_usage["ipinfo"] += 1
                        
                        # Extract location information
                        return {
                            "success": True,
                            "ip": ip,
                            "city": data.get("city", ""),
                            "region": data.get("region", ""),
                            "country": data.get("country", ""),
                            "org": data.get("org", ""),
                            "postal": data.get("postal", ""),
                            "timezone": data.get("timezone", ""),
                            "location": data.get("loc", ""),
                            "metadata": {
                                "api_provider": "IPInfo",
                                "timestamp": datetime.now(UTC).isoformat()
                            }
                        }
                    
                    # Handle API error
                    error_text = await response.text()
                    logger.error(f"IPInfo API error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "ip": ip
                    }
        
        except Exception as e:
            logger.error(f"Error calling IPInfo API: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "ip": ip
            }
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """
        Collect data from all API sources.
        
        Returns:
            Combined data from all API sources
        """
        logger.info("Collecting data from all API sources...")
        
        # Make all API calls asynchronously
        ai_task = self.call_openai_api(
            "Provide a comprehensive competitive analysis of Tata Consultancy Services (TCS)."
        )
        news_task = self.call_gnews_api("Tata Consultancy Services")
        domain_task = self.call_whoapi("tcs.com")
        search_task = self.call_serpapi("Tata Consultancy Services IT services")
        location_task = self.call_ipinfo_api("1.1.1.1")  # Example IP
        
        # Await all API responses
        ai_result, news_result, domain_result, search_result, location_result = await asyncio.gather(
            ai_task, news_task, domain_task, search_task, location_task
        )
        
        # Combine all data
        combined_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "company": "Tata Consultancy Services",
            "domain": "tcs.com",
            "ai_analysis": ai_result,
            "news": news_result,
            "domain_info": domain_result,
            "search_insights": search_result,
            "location_data": location_result
        }
        
        return combined_data
    
    async def generate_report(self) -> Tuple[str, str]:
        """
        Generate a complete TCS report with visualizations.
        
        Returns:
            Tuple of (JSON path, PDF path)
        """
        logger.info("===== STARTING TCS REPORT GENERATION =====")
        
        try:
            # 1. Collect data from all API sources
            data = await self.collect_all_data()
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 2. Save raw API data to JSON
            json_path = self.output_dir / f"tcs_api_data_{timestamp}.json"
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"API data saved to {json_path}")
            
            # 3. Create visualizations
            logger.info("Creating visualizations from API data...")
            visualization_paths = self.visualizer.create_all_visualizations(data)
            
            # 4. Generate PDF report
            logger.info("Generating PDF report with visualizations...")
            pdf_path = self.pdf_exporter.create_pdf_report(
                data,
                visualization_paths,
                f"tcs_report_{timestamp}"
            )
            
            # 5. Log API usage statistics
            logger.info("API Usage Stats:")
            for api, count in self.api_usage.items():
                if count > 0:
                    logger.info(f"- {api}: {count} calls")
            
            logger.info("===== TCS REPORT GENERATION COMPLETED =====")
            return str(json_path), pdf_path
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            logger.error(traceback.format_exc())
            return "", ""


async def main():
    """Main function to run the TCS report generator."""
    generator = TCSReportGenerator()
    json_path, pdf_path = await generator.generate_report()
    
    if pdf_path:
        print(f"\n✅ TCS Report Generation Successful")
        print(f"JSON data: {json_path}")
        print(f"PDF report: {pdf_path}")
        
        # Print API usage
        print("\nAPI Usage Stats:")
        for api, count in generator.api_usage.items():
            if count > 0:
                print(f"- {api}: {count} calls")
    else:
        print("\n❌ Error generating TCS report")


if __name__ == "__main__":
    asyncio.run(main())
