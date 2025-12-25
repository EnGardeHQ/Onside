import logging
import os
from typing import Dict, List, Optional
from serpapi.google_search import GoogleSearch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ratelimit import limits, sleep_and_retry
import backoff
from src.config import get_settings
from src.models.seo import Subject, Subtopic, ContentAsset

logger = logging.getLogger(__name__)
settings = get_settings()

class SerpService:
    def __init__(self, api_key: str = None):
        # Get API key from settings if not provided directly
        self.api_key = api_key or os.environ.get('SERPAPI_KEY', '')
        if not self.api_key:
            logger.warning("SERP API key not configured")
            
        self.calls_per_second = 5  # Adjust based on your API plan

    @sleep_and_retry
    @limits(calls=5, period=1)  # Rate limiting
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3
    )
    async def search(self, query: str, location: str = "United States", lang: str = "en") -> Dict:
        """
        Perform a Google search using SerpAPI
        """
        try:
            params = {
                "api_key": self.api_key,
                "q": query,
                "location": location,
                "hl": lang,
                "gl": "us",  # Google country
                "num": 100   # Number of results
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "error" in results:
                logger.error(f"SERP API error: {results['error']}")
                raise HTTPException(
                    status_code=400,
                    detail=f"SERP API error: {results['error']}"
                )
                
            return results
        except Exception as e:
            logger.error(f"Error performing SERP search: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error performing SERP search: {str(e)}"
            )

    async def analyze_rankings(
        self,
        db: Session,
        url: str,
        keywords: List[str],
        location: str = "United States"
    ) -> Dict[str, int]:
        """
        Analyze Google rankings for a specific URL across multiple keywords
        """
        rankings = {}
        
        for keyword in keywords:
            results = await self.search(keyword, location)
            organic_results = results.get("organic_results", [])
            
            # Find position of URL in results
            position = next(
                (i + 1 for i, result in enumerate(organic_results)
                if url in result.get("link", "")),
                None
            )
            
            rankings[keyword] = position
        
        return rankings

    async def analyze_serp_features(self, keyword: str, location: str = "United States") -> Dict:
        """
        Analyze SERP features for a keyword (featured snippets, knowledge graph, etc.)
        """
        results = await self.search(keyword, location)
        
        features = {
            "featured_snippet": results.get("answer_box"),
            "knowledge_graph": results.get("knowledge_graph"),
            "related_questions": results.get("related_questions"),
            "top_stories": results.get("top_stories"),
            "shopping_results": results.get("shopping_results"),
            "local_results": results.get("local_results")
        }
        
        return features

    async def track_content_rankings(
        self,
        db: Session,
        content_asset_id: int,
        location: str = "United States"
    ) -> Dict:
        """
        Track rankings for a specific content asset
        """
        content_asset = db.query(ContentAsset).filter(
            ContentAsset.id == content_asset_id
        ).first()
        
        if not content_asset:
            raise HTTPException(status_code=404, detail="Content asset not found")
        
        # Get related subtopics for the content's subject
        subtopics = db.query(Subtopic).filter(
            Subtopic.subject_id == content_asset.subject_id
        ).all()
        
        # Track rankings for each subtopic
        rankings = {}
        for subtopic in subtopics:
            ranking = await self.analyze_rankings(
                db,
                content_asset.url,
                [subtopic.name],
                location
            )
            rankings[subtopic.name] = ranking.get(subtopic.name)
        
        # Update content asset with new ranking data
        content_asset.google_ranking = min(
            (r for r in rankings.values() if r is not None),
            default=None
        )
        await db.commit()
        
        return rankings

    async def analyze_competition(
        self,
        db: Session,
        subtopic_id: int,
        location: str = "United States"
    ) -> Dict:
        """
        Analyze competition level for a subtopic based on SERP results
        """
        subtopic = db.query(Subtopic).filter(Subtopic.id == subtopic_id).first()
        if not subtopic:
            raise HTTPException(status_code=404, detail="Subtopic not found")
        
        results = await self.search(subtopic.name, location)
        organic_results = results.get("organic_results", [])
        
        competition_data = {
            "total_results": len(organic_results),
            "domain_authority_distribution": {},  # Would need integration with Moz API
            "content_types": {},
            "serp_features": await self.analyze_serp_features(subtopic.name, location)
        }
        
        # Analyze content types in results
        for result in organic_results:
            content_type = self._determine_content_type(result.get("snippet", ""))
            competition_data["content_types"][content_type] = \
                competition_data["content_types"].get(content_type, 0) + 1
        
        # Update subtopic with competition data
        subtopic.serp_data = competition_data
        await db.commit()
        
        return competition_data

    async def analyze_serp(self, urls: List[str], location: str = "United States") -> Dict:
        """
        Analyze SERP data for given URLs
        """
        try:
            results = []
            for url in urls:
                # Extract domain and path
                domain = url.split('/')[2]
                path = '/'.join(url.split('/')[3:])
                
                # Search for the URL
                search_results = await self.search(f"site:{domain} {path}")
                
                # Extract position and other metrics
                position = None
                for i, result in enumerate(search_results.get("organic_results", [])):
                    if result["link"] == url:
                        position = i + 1
                        break
                
                results.append({
                    "url": url,
                    "position": position,
                    "domain": domain,
                    "path": path,
                    "search_results": search_results.get("organic_results", [])[:3]  # Top 3 results
                })
            
            return results[0] if len(results) == 1 else results
            
        except Exception as e:
            logger.error(f"Error analyzing SERP data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing SERP data: {str(e)}"
            )

    def _determine_content_type(self, snippet: str) -> str:
        """
        Determine content type based on SERP snippet
        Basic implementation - could be enhanced with ML
        """
        snippet = snippet.lower()
        if "guide" in snippet or "how to" in snippet:
            return "guide"
        elif "vs" in snippet or "comparison" in snippet:
            return "comparison"
        elif "review" in snippet or "rating" in snippet:
            return "review"
        elif "news" in snippet or "announced" in snippet:
            return "news"
        else:
            return "article"
