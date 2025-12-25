#!/usr/bin/env python
"""
Maps Visualization Service - Integrates with Google Maps API.

This service implements geographic visualization capabilities using Google Maps API
with proper error handling and fallback mechanisms.

Following Semantic Seed coding standards.
"""

import os
import logging
import aiohttp
import asyncio
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from io import BytesIO

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("maps_service")

class MapsService:
    """
    Service for geographic visualization using Google Maps API.
    
    This service integrates with Google Maps API to provide location-based
    visualizations for the TCS report.
    """
    
    def __init__(self):
        """Initialize the Maps Service."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key or self.api_key == "your-google-api-key-here":
            logger.warning("Google Maps API key not found or is a placeholder in environment variables")
            
        self.static_maps_url = "https://maps.googleapis.com/maps/api/staticmap"
        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.directions_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.api_calls = 0
        
        # Create export directory if it doesn't exist
        self.export_dir = Path("exports/maps")
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_static_map(self, locations: List[Dict[str, Any]], width: int = 800, height: int = 600, 
                           zoom: int = 1, map_type: str = "roadmap") -> Dict[str, Any]:
        """Get a static map with markers for specified locations.
        
        Args:
            locations: List of locations with latitude and longitude
            width: Width of the map image
            height: Height of the map image
            zoom: Zoom level of the map (1-20)
            map_type: Type of map (roadmap, satellite, hybrid, terrain)
            
        Returns:
            Dictionary with static map data including the file path
        """
        if not self.api_key or self.api_key == "your-google-api-key-here":
            logger.error("Cannot generate map without valid Google Maps API key")
            # Create a fallback map using matplotlib
            return await self._generate_fallback_map(locations, width, height)
            
        # Build markers string for the API request
        markers = []
        for location in locations:
            if "coordinates" in location and location["coordinates"]:
                markers.append(f"color:red|{location['coordinates']}")
            elif "lat" in location and "lng" in location:
                markers.append(f"color:red|{location['lat']},{location['lng']}")
        
        # Prepare parameters for the API request
        params = {
            "size": f"{width}x{height}",
            "zoom": zoom,
            "maptype": map_type,
            "key": self.api_key
        }
        
        for marker in markers:
            params["markers"] = marker
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.static_maps_url, params=params) as response:
                    self.api_calls += 1
                    
                    if response.status != 200:
                        logger.error(f"Google Maps API error: {response.status} - {await response.text()}")
                        return await self._generate_fallback_map(locations, width, height)
                    
                    # Save the map image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = self.export_dir / f"location_map_{timestamp}.png"
                    
                    with open(filepath, 'wb') as f:
                        f.write(await response.read())
                    
                    return {
                        "success": True,
                        "filepath": str(filepath),
                        "width": width,
                        "height": height,
                        "location_count": len(locations),
                        "metadata": {
                            "api_provider": "Google Maps",
                            "query_timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error generating map: {str(e)}")
            return await self._generate_fallback_map(locations, width, height)

    async def _generate_fallback_map(self, locations: List[Dict[str, Any]], width: int = 800, height: int = 600) -> Dict[str, Any]:
        """Generate a fallback map using matplotlib when Google Maps API is unavailable.
        
        Args:
            locations: List of locations with latitude and longitude
            width: Width of the map image
            height: Height of the map image
            
        Returns:
            Dictionary with fallback map data
        """
        try:
            # Create a world map as fallback
            plt.figure(figsize=(width/100, height/100), dpi=100)
            
            # Use a simple world map background
            img = plt.imread("exports/maps/world_map_bg.png") if Path("exports/maps/world_map_bg.png").exists() else None
            
            if img is not None:
                plt.imshow(img, extent=[-180, 180, -90, 90])
            
            # Plot location points
            for location in locations:
                coords = None
                if "coordinates" in location and location["coordinates"]:
                    try:
                        lat, lng = location["coordinates"].split(",")
                        coords = (float(lat), float(lng))
                    except (ValueError, AttributeError):
                        pass
                elif "lat" in location and "lng" in location:
                    coords = (location["lat"], location["lng"])
                
                if coords:
                    plt.plot(coords[1], coords[0], 'ro', markersize=5)
            
            plt.title("TCS Global Presence")
            plt.grid(True)
            
            # Save the map
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.export_dir / f"fallback_map_{timestamp}.png"
            
            plt.savefig(filepath)
            plt.close()
            
            return {
                "success": True,
                "filepath": str(filepath),
                "fallback": True,
                "width": width,
                "height": height,
                "location_count": len(locations),
                "metadata": {
                    "provider": "Matplotlib Fallback",
                    "query_timestamp": datetime.utcnow().isoformat()
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating fallback map: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }
    
    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """Geocode an address to get coordinates.
        
        Args:
            address: Address to geocode
            
        Returns:
            Dictionary with geocoding results
        """
        if not self.api_key or self.api_key == "your-google-api-key-here":
            logger.error("Cannot geocode without valid Google Maps API key")
            return {
                "success": False,
                "error": "Invalid API key",
                "address": address
            }
            
        params = {
            "address": address,
            "key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.geocoding_url, params=params) as response:
                    self.api_calls += 1
                    
                    if response.status != 200:
                        logger.error(f"Geocoding API error: {response.status} - {await response.text()}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "address": address
                        }
                    
                    data = await response.json()
                    
                    if data["status"] != "OK":
                        logger.error(f"Geocoding error: {data['status']}")
                        return {
                            "success": False,
                            "error": f"Geocoding error: {data['status']}",
                            "address": address
                        }
                    
                    # Extract the first result
                    result = data["results"][0]
                    location = result["geometry"]["location"]
                    
                    return {
                        "success": True,
                        "address": address,
                        "formatted_address": result["formatted_address"],
                        "lat": location["lat"],
                        "lng": location["lng"],
                        "place_id": result["place_id"],
                        "metadata": {
                            "api_provider": "Google Maps",
                            "query_timestamp": datetime.utcnow().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "address": address
            }
    
    async def visualize_global_presence(self, locations: List[Dict[str, Any]], 
                                       title: str = "Global Presence") -> Dict[str, Any]:
        """Generate a visualization of global presence using location data.
        
        Args:
            locations: List of location data with coordinates
            title: Title for the visualization
            
        Returns:
            Dictionary with visualization data
        """
        # First generate a static map
        map_result = await self.get_static_map(locations)
        
        if not map_result.get("success", False):
            return map_result
        
        # Count locations by region
        regions = {
            "North America": 0,
            "South America": 0,
            "Europe": 0,
            "Asia": 0,
            "Africa": 0,
            "Oceania": 0
        }
        
        # Simple region classification based on lat/lng
        # This is a very simplified approach - real implementation would be more sophisticated
        for location in locations:
            coords = None
            if "coordinates" in location and location["coordinates"]:
                try:
                    lat, lng = location["coordinates"].split(",")
                    lat, lng = float(lat), float(lng)
                except (ValueError, AttributeError):
                    continue
            elif "lat" in location and "lng" in location:
                lat, lng = location["lat"], location["lng"]
            else:
                continue
                
            # Very simple region classification
            if -60 <= lat <= 90:  # North of Antarctic Circle
                if -170 <= lng <= -30 and lat >= 15:
                    regions["North America"] += 1
                elif -80 <= lng <= -30 and lat < 15:
                    regions["South America"] += 1
                elif -30 <= lng <= 60:
                    regions["Europe"] += 1
                elif 60 <= lng <= 180:
                    regions["Asia"] += 1
                elif -30 <= lng <= 60 and lat <= 35:
                    regions["Africa"] += 1
                elif (lng <= -170 or lng >= 100) and lat <= 15:
                    regions["Oceania"] += 1
        
        # Generate a pie chart of regional distribution
        plt.figure(figsize=(10, 6))
        
        # Filter out regions with zero count
        regions = {k: v for k, v in regions.items() if v > 0}
        
        labels = regions.keys()
        sizes = regions.values()
        
        # Custom colors
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6']
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title(f"{title} - Regional Distribution")
        
        # Save the chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_path = self.export_dir / f"region_distribution_{timestamp}.png"
        
        plt.savefig(chart_path)
        plt.close()
        
        return {
            "success": True,
            "map_path": map_result.get("filepath"),
            "chart_path": str(chart_path),
            "region_distribution": regions,
            "location_count": len(locations),
            "metadata": {
                "title": title,
                "query_timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def get_api_call_stats(self) -> Dict[str, int]:
        """Get statistics about API calls made by this service.
        
        Returns:
            Dictionary with API call statistics
        """
        return {"google_maps_api_calls": self.api_calls}
