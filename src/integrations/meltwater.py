from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from src.config import Config

class MeltwaterClient:
    """Client for interacting with the Meltwater API"""
    
    def __init__(self, api_key: str, base_url: str):
        """Initialize the Meltwater client"""
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Create aiohttp session when entering context"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session when exiting context"""
        if self.session:
            await self.session.close()
            
    async def get_mentions(
        self,
        search_terms: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get mentions for the specified search terms and date range"""
        endpoint = f"{self.base_url}/mentions/search"
        
        payload = {
            "searchTerms": search_terms,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "sources": ["news", "blogs", "social"]
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("mentions", [])
            
    async def create_alert(
        self,
        search_terms: List[str],
        config: Dict
    ) -> str:
        """Create a new alert for the specified search terms"""
        endpoint = f"{self.base_url}/alerts"
        
        payload = {
            "name": f"Competitor Alert: {', '.join(search_terms)}",
            "searchTerms": search_terms,
            "frequency": config.get("frequency", "realtime"),
            "channels": config.get("channels", ["email"]),
            "threshold": config.get("threshold", "all")
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data["alertId"]
            
    async def update_alert(
        self,
        alert_id: str,
        config: Dict
    ) -> bool:
        """Update an existing alert configuration"""
        endpoint = f"{self.base_url}/alerts/{alert_id}"
        
        async with self.session.put(endpoint, json=config) as response:
            response.raise_for_status()
            return True
            
    async def delete_alert(self, alert_id: str) -> bool:
        """Delete an existing alert"""
        endpoint = f"{self.base_url}/alerts/{alert_id}"
        
        async with self.session.delete(endpoint) as response:
            response.raise_for_status()
            return True
            
    async def get_alert_history(
        self,
        alert_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get alert history for the specified alert"""
        endpoint = f"{self.base_url}/alerts/{alert_id}/history"
        
        params = {
            "days": days
        }
        
        async with self.session.get(endpoint, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("history", [])
