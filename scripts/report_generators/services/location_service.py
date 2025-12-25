#!/usr/bin/env python
"""
Location Intelligence Service - Integrates with IPInfo API.

This service implements Sprint 4 requirements for geographic data integration
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
logger = logging.getLogger("location_service")

class LocationService:
    """
    Service for location intelligence using IPInfo API.
    
    This service integrates with IPInfo to provide geographic data
    for the TCS report.
    """
    
    def __init__(self):
        """Initialize the Location Service."""
        self.api_key = os.getenv("IPINFO_API_KEY")
        if not self.api_key:
            logger.warning("IPInfo API key not found in environment variables")
        
        self.base_url = "https://ipinfo.io"
        self.api_calls = 0
    
    async def get_company_locations(self, domains: List[str]) -> Dict[str, Any]:
        """Get geographic data for company domains using IPInfo.
        
        Args:
            domains: List of domains to analyze
            
        Returns:
            Dictionary with geographic data
        """
        results = {
            "success": True,
            "domains_analyzed": len(domains),
            "locations": [],
            "metadata": {
                "api_provider": "IPInfo",
                "query_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        for domain in domains:
            try:
                # First we need to resolve the domain to IP
                async with aiohttp.ClientSession() as session:
                    # Get domain info
                    url = f"https://ipinfo.io/domains/{domain}/json"
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    async with session.get(url, headers=headers) as response:
                        self.api_calls += 1
                        
                        if response.status != 200:
                            logger.error(f"IPInfo API error: {response.status} - {await response.text()}")
                            continue
                        
                        data = await response.json()
                        
                        # Extract relevant location data
                        ip_addresses = data.get("ips", [])
                        
                        if not ip_addresses or len(ip_addresses) == 0:
                            continue
                        
                        # Get location info for the first IP
                        primary_ip = ip_addresses[0]
                        
                        location_url = f"https://ipinfo.io/{primary_ip}/json"
                        async with session.get(location_url, headers=headers) as loc_response:
                            self.api_calls += 1
                            
                            if loc_response.status != 200:
                                logger.error(f"IPInfo API error: {loc_response.status} - {await loc_response.text()}")
                                continue
                            
                            loc_data = await loc_response.json()
                            
                            # Add to results
                            results["locations"].append({
                                "domain": domain,
                                "ip": primary_ip,
                                "city": loc_data.get("city", "Unknown"),
                                "region": loc_data.get("region", "Unknown"),
                                "country": loc_data.get("country", "Unknown"),
                                "org": loc_data.get("org", "Unknown"),
                                "postal": loc_data.get("postal", "Unknown"),
                                "timezone": loc_data.get("timezone", "Unknown"),
                                "coordinates": loc_data.get("loc", "0,0")
                            })
            except Exception as e:
                logger.error(f"Error analyzing location for {domain}: {str(e)}")
                continue
        
        # Update success status if no locations were found
        if len(results["locations"]) == 0:
            results["success"] = False
            results["error"] = "Failed to retrieve location data for any domains"
        
        return results
    
    async def get_country_distribution(self, domains: List[str]) -> Dict[str, Any]:
        """Get country distribution for a list of domains.
        
        Args:
            domains: List of domains to analyze
            
        Returns:
            Dictionary with country distribution data
        """
        # First get all locations
        locations_data = await self.get_company_locations(domains)
        
        if not locations_data.get("success", False):
            return locations_data
        
        # Analyze country distribution
        countries = {}
        for location in locations_data.get("locations", []):
            country = location.get("country", "Unknown")
            if country not in countries:
                countries[country] = 0
            countries[country] += 1
        
        # Calculate percentages
        total = sum(countries.values())
        country_percentages = {}
        for country, count in countries.items():
            country_percentages[country] = round((count / total) * 100, 2)
        
        return {
            "success": True,
            "domains_analyzed": len(domains),
            "country_distribution": country_percentages,
            "primary_countries": sorted(country_percentages.items(), key=lambda x: x[1], reverse=True)[:3],
            "metadata": {
                "api_provider": "IPInfo",
                "query_timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """Get statistics about API calls made by this service.
        
        Returns:
            Dictionary with API call statistics
        """
        return {"ipinfo_calls": self.api_calls}
