#!/usr/bin/env python
"""
Domain Analysis Service - Integrates with WHOAPI for domain information.

This service implements Sprint 4 requirements for domain intelligence
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
logger = logging.getLogger("domain_service")

class DomainService:
    """
    Service for domain analysis using WHOAPI.
    
    This service integrates with WHOAPI to provide domain intelligence
    for the TCS report.
    """
    
    def __init__(self):
        """Initialize the Domain Service."""
        self.api_key = os.getenv("WHOAPI_API_KEY")
        if not self.api_key:
            logger.warning("WHOAPI key not found in environment variables")
        
        self.base_url = "https://api.whoapi.com"
        self.api_calls = 0
    
    async def analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze a domain using WHOAPI.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            Dictionary with domain analysis data
        """
        url = f"{self.base_url}/"
        params = {
            "domain": domain,
            "r": "whois",
            "apikey": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.api_calls += 1
                    
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
                            "query_timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error analyzing domain {domain}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "domain": domain
            }
    
    async def get_domain_info(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive domain info using WHOAPI.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            Dictionary with domain information
        """
        url = f"{self.base_url}/"
        params = {
            "domain": domain,
            "r": "domain-info",
            "apikey": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.api_calls += 1
                    
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
                        "rank": data.get("rank", 0),
                        "country": data.get("country", "Unknown"),
                        "has_ssl": data.get("ssl_cert", False),
                        "dns_records": data.get("dns_records", {}),
                        "metadata": {
                            "api_provider": "WHOAPI",
                            "query_timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error getting domain info for {domain}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "domain": domain
            }
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """Get statistics about API calls made by this service.
        
        Returns:
            Dictionary with API call statistics
        """
        return {"whoapi_calls": self.api_calls}
