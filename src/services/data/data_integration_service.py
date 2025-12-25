from typing import Dict, List, Optional
import asyncio
import aiohttp
import os
from datetime import datetime
import logging
from fastapi import HTTPException
import random  # For mock data

logger = logging.getLogger(__name__)

class DataIntegrationService:
    def __init__(self):
        self.session = None
        self.api_keys = self._load_api_keys()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _load_api_keys(self) -> Dict:
        """Load API keys from environment variables"""
        return {
            "semrush": os.getenv("SEMRUSH_API_KEY"),
            "meltwater": os.getenv("MELTWATER_API_KEY"),
            "similarweb": os.getenv("SIMILARWEB_API_KEY"),
            "brandwatch": os.getenv("BRANDWATCH_API_KEY"),
            "buzzsumo": os.getenv("BUZZSUMO_API_KEY"),
            "ahrefs": os.getenv("AHREFS_API_KEY"),
            "youtube": os.getenv("YOUTUBE_API_KEY"),
            "spotify": os.getenv("SPOTIFY_API_KEY"),
            "apple_podcasts": os.getenv("APPLE_PODCASTS_API_KEY"),
            "linkedin": os.getenv("LINKEDIN_API_KEY")
        }

    def _validate_market(self, market: str) -> None:
        """Validate market value"""
        valid_markets = ["US", "UK", "EU", "APAC", "LATAM"]
        if market not in valid_markets:
            raise ValueError(f"Invalid market: {market}. Must be one of {valid_markets}")

    async def gather_comprehensive_data(self, content_asset: Dict) -> Dict:
        """Gather data from all available sources"""
        if not content_asset:
            raise ValueError("Content asset cannot be None")
            
        required_fields = ["id", "content", "target_keywords", "market"]
        missing_fields = [field for field in required_fields if field not in content_asset]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        self._validate_market(content_asset["market"])
            
        try:
            tasks = [
                self._gather_search_data(content_asset),
                self._gather_social_data(content_asset),
                self._gather_competitor_data(content_asset),
                self._gather_market_data(content_asset),
                self._gather_multimedia_data(content_asset)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return self._combine_results(results)
            
        except Exception as e:
            logger.error(f"Error gathering comprehensive data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error gathering data: {str(e)}"
            )

    async def _gather_search_data(self, content_asset: Dict) -> Dict:
        """Mock gathering search-related data"""
        # Simulated search metrics for testing
        return {
            "search_metrics": {
                "visibility_score": random.uniform(0, 100),
                "ranking_distribution": {
                    "1-3": random.randint(0, 10),
                    "4-10": random.randint(5, 20)
                },
                "keyword_performance": {
                    keyword: {
                        "volume": random.randint(500, 5000),
                        "position": random.randint(1, 10)
                    } for keyword in content_asset.get("target_keywords", [])
                },
                "click_through_rates": {
                    str(pos): random.uniform(0.1, 0.5)
                    for pos in range(1, 11)
                },
                "search_intent": {
                    "informational": random.uniform(0, 1),
                    "commercial": random.uniform(0, 1),
                    "navigational": random.uniform(0, 1)
                },
                "regional_performance": {
                    "US": {"traffic": random.randint(1000, 10000)},
                    "UK": {"traffic": random.randint(500, 5000)},
                    "EU": {"traffic": random.randint(800, 8000)}
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _gather_social_data(self, content_asset: Dict) -> Dict:
        """Mock gathering social media data"""
        return {
            "social_metrics": {
                "engagement_score": random.uniform(0, 100),
                "platform_metrics": {
                    "twitter": {
                        "shares": random.randint(0, 1000),
                        "likes": random.randint(0, 2000),
                        "comments": random.randint(0, 500)
                    },
                    "linkedin": {
                        "shares": random.randint(0, 500),
                        "likes": random.randint(0, 1000),
                        "comments": random.randint(0, 200)
                    }
                },
                "audience_demographics": {
                    "age_groups": {
                        "18-24": random.uniform(0, 0.2),
                        "25-34": random.uniform(0, 0.3),
                        "35-44": random.uniform(0, 0.3),
                        "45+": random.uniform(0, 0.2)
                    }
                },
                "sentiment_analysis": {
                    "positive": random.uniform(0, 1),
                    "neutral": random.uniform(0, 1),
                    "negative": random.uniform(0, 1)
                },
                "viral_potential": random.uniform(0, 1),
                "interaction_patterns": {
                    "peak_hours": [random.randint(8, 20) for _ in range(3)],
                    "engagement_velocity": random.uniform(0, 1)
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _gather_multimedia_data(self, content_asset: Dict) -> Dict:
        """Mock gathering multimedia content data"""
        return {
            "multimedia_metrics": {
                "view_metrics": {
                    "total_views": random.randint(1000, 100000),
                    "unique_viewers": random.randint(800, 80000)
                },
                "engagement_metrics": {
                    "likes": random.randint(100, 10000),
                    "shares": random.randint(50, 5000),
                    "comments": random.randint(20, 2000)
                },
                "audience_retention": {
                    "average_watch_time": random.uniform(0, 1),
                    "completion_rate": random.uniform(0, 1)
                },
                "quality_scores": {
                    "technical_quality": random.uniform(0, 1),
                    "content_quality": random.uniform(0, 1)
                },
                "platform_performance": {
                    "youtube": {
                        "views": random.randint(1000, 50000),
                        "engagement_rate": random.uniform(0, 1)
                    },
                    "spotify": {
                        "plays": random.randint(500, 25000),
                        "followers": random.randint(100, 5000)
                    }
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _gather_competitor_data(self, content_asset: Dict) -> Dict:
        """Mock gathering competitor data"""
        return {
            "competitor_metrics": {
                "direct_competitors": [
                    {
                        "name": f"Competitor {i}",
                        "market_share": random.uniform(0, 0.3),
                        "content_volume": random.randint(100, 1000),
                        "engagement_metrics": {
                            "avg_engagement_rate": random.uniform(0, 0.1),
                            "social_shares": random.randint(100, 10000),
                            "backlinks": random.randint(50, 5000)
                        },
                        "content_quality": {
                            "readability_score": random.uniform(0, 100),
                            "technical_seo_score": random.uniform(0, 100),
                            "content_depth_score": random.uniform(0, 100)
                        },
                        "keyword_overlap": random.uniform(0, 1),
                        "topic_authority": random.uniform(0, 1)
                    } for i in range(5)
                ],
                "industry_benchmarks": {
                    "avg_engagement_rate": random.uniform(0.01, 0.05),
                    "avg_content_length": random.randint(800, 2000),
                    "avg_publishing_frequency": random.randint(2, 10),
                    "avg_social_shares": random.randint(500, 5000)
                },
                "competitive_gaps": [
                    {
                        "topic": f"Topic {i}",
                        "opportunity_score": random.uniform(0, 100),
                        "competition_level": random.uniform(0, 1),
                        "estimated_impact": random.uniform(0, 1)
                    } for i in range(3)
                ],
                "market_position": {
                    "overall_rank": random.randint(1, 20),
                    "topic_leadership_score": random.uniform(0, 100),
                    "market_penetration": random.uniform(0, 1),
                    "growth_trajectory": random.uniform(-0.1, 0.3)
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _gather_market_data(self, content_asset: Dict) -> Dict:
        """Mock gathering market intelligence data"""
        return {
            "market_metrics": {
                "market_share": {
                    "overall": random.uniform(0, 1),
                    "segment": random.uniform(0, 1)
                },
                "competitor_analysis": {
                    "direct_competitors": random.randint(3, 10),
                    "market_leaders": [
                        {
                            "name": f"Competitor {i}",
                            "share": random.uniform(0, 0.3)
                        } for i in range(3)
                    ]
                },
                "trend_analysis": {
                    "growth_rate": random.uniform(-0.1, 0.3),
                    "momentum": random.uniform(-1, 1)
                },
                "audience_insights": {
                    "total_addressable_market": random.randint(10000, 1000000),
                    "market_penetration": random.uniform(0, 1)
                },
                "content_gaps": {
                    "opportunity_score": random.uniform(0, 100),
                    "competition_level": random.uniform(0, 1)
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    def _process_search_results(self, results: List) -> Dict:
        """Process and normalize search data"""
        processed_data = {
            "visibility_score": 0.0,
            "ranking_distribution": {},
            "keyword_performance": {},
            "click_through_rates": {},
            "search_intent": {},
            "regional_performance": {}
        }
        
        for result in results:
            if isinstance(result, Exception):
                continue
                
            # Update visibility score
            if "visibility_score" in result:
                processed_data["visibility_score"] += result["visibility_score"]
                
            # Merge ranking distribution
            if "ranking_distribution" in result:
                for position, count in result["ranking_distribution"].items():
                    processed_data["ranking_distribution"][position] = \
                        processed_data["ranking_distribution"].get(position, 0) + count
                        
            # Merge keyword performance
            if "keyword_performance" in result:
                for keyword, metrics in result["keyword_performance"].items():
                    if keyword not in processed_data["keyword_performance"]:
                        processed_data["keyword_performance"][keyword] = metrics
                    else:
                        # Average the metrics
                        for metric, value in metrics.items():
                            existing = processed_data["keyword_performance"][keyword][metric]
                            processed_data["keyword_performance"][keyword][metric] = \
                                (existing + value) / 2
                                
            # Merge CTR data
            if "click_through_rates" in result:
                for position, rate in result["click_through_rates"].items():
                    if position not in processed_data["click_through_rates"]:
                        processed_data["click_through_rates"][position] = rate
                    else:
                        processed_data["click_through_rates"][position] = \
                            (processed_data["click_through_rates"][position] + rate) / 2
                            
            # Merge search intent data
            if "search_intent" in result:
                for intent, score in result["search_intent"].items():
                    if intent not in processed_data["search_intent"]:
                        processed_data["search_intent"][intent] = score
                    else:
                        processed_data["search_intent"][intent] = \
                            (processed_data["search_intent"][intent] + score) / 2
                            
            # Merge regional performance
            if "regional_performance" in result:
                for region, metrics in result["regional_performance"].items():
                    if region not in processed_data["regional_performance"]:
                        processed_data["regional_performance"][region] = metrics
                    else:
                        for metric, value in metrics.items():
                            existing = processed_data["regional_performance"][region][metric]
                            processed_data["regional_performance"][region][metric] = \
                                (existing + value) / 2
        
        return processed_data

    def _combine_results(self, results: List) -> Dict:
        """Combine all results into a comprehensive dataset"""
        try:
            search_data, social_data, competitor_data, market_data, multimedia_data = results
            
            return {
                "search_metrics": search_data.get("search_metrics", {}),
                "social_metrics": social_data.get("social_metrics", {}),
                "competitor_metrics": competitor_data.get("competitor_metrics", {}),
                "market_metrics": market_data.get("market_metrics", {}),
                "multimedia_metrics": multimedia_data.get("multimedia_metrics", {}),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "data_sources": self._get_active_data_sources(results),
                    "coverage_score": self._calculate_coverage_score(results)
                }
            }
        except Exception as e:
            logger.error(f"Error combining results: {str(e)}")
            return {}

    def _get_active_data_sources(self, results: List) -> List[str]:
        """Get list of active data sources"""
        sources = []
        if results[0]: sources.append("search")
        if results[1]: sources.append("social")
        if results[2]: sources.append("competitor")
        if results[3]: sources.append("market")
        if results[4]: sources.append("multimedia")
        return sources

    def _calculate_coverage_score(self, results: List) -> float:
        """Calculate data coverage score"""
        valid_results = sum(1 for r in results if r and not isinstance(r, Exception))
        return (valid_results / len(results)) * 100 if results else 0
