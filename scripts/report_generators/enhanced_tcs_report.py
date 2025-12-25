#!/usr/bin/env python
"""
Enhanced TCS Report Generator

Generates a comprehensive TCS report with chain-of-thought reasoning,
confidence metrics, and advanced data visualizations that showcase
the full power of OnSide's competitive intelligence platform.

Following Semantic Seed Venture Studio Coding Standards V2.0.
Implements BDD principles with proper error handling and logging.
"""

import os
import json
import logging
import traceback
import asyncio
import urllib.request
import urllib.parse
import urllib.error
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure src directory is in the Python path for proper imports
os.environ['PYTHONPATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')) + os.pathsep + os.environ.get('PYTHONPATH', '')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Add the project root and src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

# This ensures OnSide core services can be imported

# Import enhanced services
from scripts.report_generators.services.enhanced_ai_service import EnhancedAIService
from scripts.report_generators.services.data_integration_service import DataIntegrationService
from scripts.report_generators.services.enhanced_visualization_service import EnhancedVisualizationService
from scripts.report_generators.services.enhanced_pdf_service import EnhancedPDFService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enhanced_tcs_report")

class EnhancedTCSReportGenerator:
    """
    Enhanced TCS Report Generator
    
    Generates a comprehensive TCS report with chain-of-thought reasoning,
    confidence metrics, and advanced data visualizations.
    """
    
    def __init__(self):
        """Initialize the enhanced TCS report generator."""
        # Initialize output directory
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
        self.ai_service = EnhancedAIService(self.api_keys)
        self.data_integration = DataIntegrationService()
        self.visualization = EnhancedVisualizationService()
        self.pdf_service = EnhancedPDFService()
        
        logger.info("Enhanced TCS Report Generator initialized")
    
    async def generate_report(self) -> Tuple[str, Dict[str, str], str]:
        """
        Generate the enhanced TCS report.
        
        Returns:
            Tuple of (JSON path, Visualization paths, PDF path)
        """
        logger.info("===== STARTING ENHANCED TCS REPORT GENERATION =====")
        
        try:
            # 1. Collect raw API data
            raw_data = await self._collect_api_data()
            
            # 2. Generate enhanced AI analysis with reasoning chains
            logger.info("Generating enhanced AI analysis with chain-of-thought reasoning")
            ai_analysis = await self.ai_service.generate_competitor_analysis_with_cot({
                "company": "Tata Consultancy Services",
                "domain": "tcs.com"
            })
            
            # Update raw data with enhanced AI analysis
            raw_data["ai_analysis"] = ai_analysis
            
            # 3. Save raw data to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = self.output_dir / f"tcs_enhanced_data_{timestamp}.json"
            with open(json_path, "w") as f:
                json.dump(raw_data, f, indent=2)
            
            logger.info(f"Enhanced raw data saved to {json_path}")
            
            # 4. Integrate data from all sources
            logger.info("Integrating data from all API sources")
            integrated_data = self.data_integration.integrate_data(raw_data)
            
            # Save integrated data
            integrated_path = self.output_dir / f"tcs_integrated_data_{timestamp}.json"
            with open(integrated_path, "w") as f:
                json.dump(integrated_data, f, indent=2)
            
            logger.info(f"Integrated data saved to {integrated_path}")
            
            # 5. Create enhanced visualizations
            logger.info("Creating enhanced visualizations with confidence indicators")
            visualizations = self.visualization.create_all_visualizations(integrated_data)
            
            visualization_paths = {}
            for name, path in visualizations.items():
                if path:
                    visualization_paths[name] = path
                    logger.info(f"Created visualization: {name} at {path}")
            
            # 6. Generate enhanced PDF report
            logger.info("Generating enhanced PDF report with reasoning chains")
            pdf_path = self.pdf_service.create_pdf_report(
                raw_data,
                integrated_data,
                visualizations
            )
            
            # 7. Log API usage statistics
            logger.info("API Usage Statistics:")
            for api, count in self.api_usage.items():
                if count > 0:
                    logger.info(f"- {api}: {count} calls")
            
            logger.info("===== ENHANCED TCS REPORT GENERATION COMPLETED =====")
            return str(json_path), visualization_paths, pdf_path
            
        except Exception as e:
            logger.error(f"Error generating enhanced report: {str(e)}")
            logger.error(traceback.format_exc())
            return "", {}, ""
    
    async def _collect_api_data(self) -> Dict[str, Any]:
        """
        Collect data from all API sources.
        
        Returns:
            Combined data from all API sources
        """
        logger.info("Collecting data from all API sources")
        
        # Make all API calls concurrently using asyncio
        news_task = self._call_gnews_api("Tata Consultancy Services")
        domain_task = self._call_whoapi("tcs.com")
        search_task = self._call_serpapi("Tata Consultancy Services IT services")
        location_task = self._call_ipinfo_api("1.1.1.1")  # Example IP
        
        # Await all API responses concurrently
        news_result, domain_result, search_result, location_result = await asyncio.gather(
            news_task, domain_task, search_task, location_task
        )
        
        # Combine all data
        combined_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "company": "Tata Consultancy Services",
            "domain": "tcs.com",
            "news": news_result,
            "domain_info": domain_result,
            "search_insights": search_result,
            "location_data": location_result
        }
        
        return combined_data
    
    async def _call_gnews_api(self, query: str = "Tata Consultancy Services") -> Dict[str, Any]:
        """
        Call GNews API for news data.
        
        Args:
            query: Search query for news
            
        Returns:
            News API response
        """
        logger.info(f"Calling GNews API for {query} news")
        
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
            from_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Construct the GNews API URL with proper URL encoding
            encoded_query = urllib.parse.quote_plus(query)
            url = (
                f"https://gnews.io/api/v4/search"
                f"?q={encoded_query}"
                f"&lang=en"
                f"&country=us"
                f"&from={from_date}"
                f"&token={self.api_keys['gnews']}"
                f"&max=10"
            )
            
            # Make GNews API request asynchronously
            try:
                # Use asyncio to run the blocking urllib call in a thread pool
                loop = asyncio.get_running_loop()
                req = urllib.request.Request(url)
                response = await loop.run_in_executor(
                    None, lambda: urllib.request.urlopen(req, timeout=15)
                )
                
                # Check if the request was successful
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    self.api_usage["gnews"] += 1
                    
                    # Extract articles
                    articles = data.get("articles", [])
                    
                    return {
                        "success": True,
                        "articles": articles
                    }
                    
                    # Handle API error
                    error_text = response.read().decode('utf-8')
                    logger.error(f"GNews API error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "articles": []
                    }
            except urllib.error.HTTPError as e:
                logger.error(f"GNews API HTTP error: {e.code} - {e.reason}")
                return {
                    "success": False,
                    "error": f"HTTP error: {e.code} - {e.reason}",
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
    
    async def _call_whoapi(self, domain: str = "tcs.com") -> Dict[str, Any]:
        """
        Call WHOAPI for domain information.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            WHOAPI response with domain information
        """
        logger.info(f"Calling WHOAPI for domain information on {domain}")
        
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
            
            # Make WHOAPI request asynchronously
            try:
                # Use asyncio to run the blocking urllib call in a thread pool
                loop = asyncio.get_running_loop()
                req = urllib.request.Request(url)
                response = await loop.run_in_executor(
                    None, lambda: urllib.request.urlopen(req, timeout=15)
                )
                
                # Check if the request was successful
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
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
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    
                    # Handle API error
                    error_text = response.read().decode('utf-8')
                    logger.error(f"WHOAPI error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "domain": domain
                    }
            except urllib.error.HTTPError as e:
                logger.error(f"WHOAPI HTTP error: {e.code} - {e.reason}")
                return {
                    "success": False,
                    "error": f"HTTP error: {e.code} - {e.reason}",
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
    
    async def _call_serpapi(self, query: str = "Tata Consultancy Services IT services") -> Dict[str, Any]:
        """
        Call SERPAPI for search engine data.
        
        Args:
            query: Search query
            
        Returns:
            SERPAPI response with search results
        """
        logger.info(f"Calling SERPAPI for search insights on '{query}'")
        
        # Check if API key is available
        if not self.api_keys["serpapi"]:
            logger.warning("No SERPAPI key found. Using fallback response.")
            return {
                "success": False,
                "error": "No API key",
                "query": query
            }
        
        try:
            # Construct the SERPAPI URL with proper URL encoding
            encoded_query = urllib.parse.quote_plus(query)
            url = (
                f"https://serpapi.com/search.json"
                f"?q={encoded_query}"
                f"&api_key={self.api_keys['serpapi']}"
                f"&num=10"
            )
            
            # Make SERPAPI request asynchronously
            try:
                # Use asyncio to run the blocking urllib call in a thread pool
                loop = asyncio.get_running_loop()
                req = urllib.request.Request(url)
                response = await loop.run_in_executor(
                    None, lambda: urllib.request.urlopen(req, timeout=20)
                )
                
                # Check if the request was successful
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
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
                            "snippet": result.get("snippet", ""),
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
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    
                    # Handle API error
                    error_text = response.read().decode('utf-8')
                    logger.error(f"SERPAPI error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "query": query
                    }
            except urllib.error.HTTPError as e:
                logger.error(f"SERPAPI HTTP error: {e.code} - {e.reason}")
                return {
                    "success": False,
                    "error": f"HTTP error: {e.code} - {e.reason}",
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
    
    async def _call_ipinfo_api(self, ip: str = "1.1.1.1") -> Dict[str, Any]:
        """
        Call IPInfo API for location data.
        
        Args:
            ip: IP address to analyze
            
        Returns:
            IPInfo response with location data
        """
        logger.info(f"Calling IPInfo API for geographic data on {ip}")
        
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
            
            # Make IPInfo API request asynchronously
            try:
                # Use asyncio to run the blocking urllib call in a thread pool
                loop = asyncio.get_running_loop()
                req = urllib.request.Request(url)
                response = await loop.run_in_executor(
                    None, lambda: urllib.request.urlopen(req, timeout=15)
                )
                
                # Check if the request was successful
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
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
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    
                    # Handle API error
                    error_text = response.read().decode('utf-8')
                    logger.error(f"IPInfo API error: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "ip": ip
                    }
            except urllib.error.HTTPError as e:
                logger.error(f"IPInfo HTTP error: {e.code} - {e.reason}")
                return {
                    "success": False,
                    "error": f"HTTP error: {e.code} - {e.reason}",
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


async def main():
    """Main function to run the enhanced TCS report generator."""
    generator = EnhancedTCSReportGenerator()
    json_path, visualizations, pdf_path = await generator.generate_report()
    
    if pdf_path:
        print(f"\n✅ Enhanced TCS Report Generation Successful")
        print(f"Raw data: {json_path}")
        print(f"PDF report: {pdf_path}")
        print("\nVisualizations:")
        for name, path in visualizations.items():
            print(f"- {name}: {path}")
        
        # Print API usage
        print("\nAPI Usage Stats:")
        for api, count in generator.api_usage.items():
            if count > 0:
                print(f"- {api}: {count} calls")
    else:
        print("\n❌ Error generating enhanced TCS report")


if __name__ == "__main__":
    asyncio.run(main())
