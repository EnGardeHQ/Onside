#!/usr/bin/env python3
"""
Enhanced AI Service for OnSide Report Generation

This module provides AI-powered analysis capabilities for generating comprehensive reports
in the OnSide platform. It includes functionality for competitor analysis, market trends,
sentiment analysis, and more.
"""

import asyncio
import json
import logging
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union, TypedDict, Literal

import aiohttp
from pydantic import BaseModel, Field, validator

# Type aliases
SentimentScore = float  # Range from -1.0 (negative) to 1.0 (positive)
ConfidenceScore = float  # Range from 0.0 to 1.0

class CompetitorAnalysisResult(TypedDict):
    """Typed dict for competitor analysis results."""
    competitors: List[Dict[str, Any]]
    market_share: Dict[str, float]
    strengths_weaknesses: Dict[str, Dict[str, List[str]]]
    competitive_threats: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    confidence: ConfidenceScore

class MarketTrendsResult(TypedDict):
    """Typed dict for market trends analysis results."""
    trends: List[Dict[str, Any]]
    growth_areas: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    predictions: Dict[str, Any]
    confidence: ConfidenceScore

class SentimentAnalysisResult(TypedDict):
    """Typed dict for sentiment analysis results."""
    overall_sentiment: Dict[str, Any]
    sentiment_by_category: Dict[str, Dict[str, float]]
    key_phrases: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    confidence: ConfidenceScore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedAIService:
    """Enhanced AI Service for generating KPMG-standard reports with AI-powered analysis.
    
    This service provides comprehensive analysis capabilities including:
    - Executive summary generation
    - Competitor analysis with market positioning
    - Market trends and growth opportunities
    - SWOT analysis
    - Strategic recommendations
    - Confidence scoring with reasoning chains
    - Professional visualizations
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.onside.ai/v1"):
        """
        Initialize the EnhancedAIService.
        
        Args:
            api_key: API key for authentication. If not provided, will look for OPENAI_API_KEY in environment.
            base_url: Base URL for the OnSide API.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=60.0)
        
        # Initialize HTTP session
        self._init_session()
    
    def _init_session(self) -> None:
        """Initialize the aiohttp client session."""
        if self.session is None or self.session.closed:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            }
            self.session = aiohttp.ClientSession(headers=headers, timeout=self.timeout)
    
    async def close(self) -> None:
        """Close the aiohttp client session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def analyze_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Primary entry point for analyzing API data and generating a KPMG-standard report.
        
        This method coordinates the analysis of different aspects of the provided data,
        including executive summary, competitor analysis, market trends, SWOT analysis,
        and strategic recommendations with confidence scoring.
        
        Args:
            api_data: Dictionary containing the API response data to analyze.
            
        Returns:
            Dict containing the analysis results with the following structure:
            {
                "status": "success|error",
                "data": {
                    "executive_summary": {
                        "overview": str,
                        "key_findings": List[str],
                        "recommendations": List[str],
                        "confidence": float
                    },
                    "competitor_analysis": {
                        "competitors": List[Dict],
                        "market_share": Dict[str, float],
                        "positioning": Dict[str, Any],
                        "confidence": float
                    },
                    "market_analysis": {
                        "trends": List[Dict],
                        "growth_areas": List[Dict],
                        "market_size": Dict[str, Any],
                        "confidence": float
                    },
                    "swot_analysis": {
                        "strengths": List[Dict],
                        "weaknesses": List[Dict],
                        "opportunities": List[Dict],
                        "threats": List[Dict],
                        "confidence": float
                    },
                    "strategic_recommendations": {
                        "recommendations": List[Dict],
                        "implementation_roadmap": Dict[str, List[Dict]],
                        "expected_impact": Dict[str, Any],
                        "confidence": float
                    },
                    "visualization_data": {
                        "charts": List[Dict],
                        "tables": List[Dict],
                        "metrics": Dict[str, Any]
                    },
                    "metadata": {
                        "report_id": str,
                        "generated_at": str,
                        "data_sources": List[str],
                        "model_versions": Dict[str, str]
                    }
                },
                "error": Optional[str]  # Only present if status is "error"
            }
            
        Raises:
            ValueError: If the input data is invalid or missing required fields.
            aiohttp.ClientError: If there's an error making HTTP requests.
        """
        if not api_data or not isinstance(api_data, dict):
            raise ValueError("Invalid input: api_data must be a non-empty dictionary")
            
        logger.info("Starting data analysis")
        
        try:
            # Initialize result structure
            result = {
                "status": "success",
                "data": {
                    "insights": {},
                    "metadata": {
                        "model_used": "gpt-4",
                        "timestamp": None,
                        "data_points_analyzed": 0
                    }
                }
            }
            
            # Perform analysis (placeholder - implement actual analysis logic)
            result["data"]["insights"]["competitor_analysis"] = await self._analyze_competitors(api_data)
            result["data"]["insights"]["market_trends"] = await self._analyze_market_trends(api_data)
            result["data"]["insights"]["sentiment_analysis"] = await self._analyze_sentiment(api_data)
            result["data"]["insights"]["swot_analysis"] = await self._generate_swot_analysis(api_data)
            result["data"]["insights"]["executive_summary"] = self._generate_executive_summary(result["data"]["insights"])
            result["data"]["insights"]["strategic_recommendations"] = await self._generate_recommendations(api_data)
            result["data"]["insights"]["visualization_data"] = self._generate_visualization_data(result["data"]["insights"])
            
            # Update metadata
            result["data"]["metadata"]["timestamp"] = self._get_current_timestamp()
            result["data"]["metadata"]["data_points_analyzed"] = len(api_data.get("data_points", []))
            
            logger.info("Data analysis completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error during data analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "error": error_msg,
                "data": None
            }
    
    async def _analyze_competitors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze competitor data and provide insights.
        
        Args:
            data: Dictionary containing the API response data with competitor information.
            
        Returns:
            Dict containing competitor analysis results with the following structure:
            {
                "competitors": List[Dict],  # List of competitors with details
                "market_share": Dict[str, float],  # Market share by competitor
                "strengths_weaknesses": Dict[str, Dict[str, List[str]]],  # Strengths/weaknesses by competitor
                "competitive_threats": List[Dict],  # Identified competitive threats
                "opportunities": List[Dict],  # Identified opportunities
                "confidence": float,  # Confidence score (0.0 to 1.0)
                "status": str,  # "success" or "error"
                "error": Optional[str]  # Error message if status is "error"
            }
        """
        try:
            logger.info("Starting competitor analysis")
            
            # Extract company and competitor information
            company_name = data.get("company", {}).get("name", "Our Company")
            competitors = data.get("company", {}).get("competitors", [])
            industry = data.get("company", {}).get("industry", "")
            
            if not competitors:
                logger.warning("No competitors found in the provided data")
                return {
                    "status": "success",
                    "competitors": [],
                    "market_share": {},
                    "strengths_weaknesses": {},
                    "competitive_threats": [],
                    "opportunities": [],
                    "confidence": 0.0,
                    "message": "No competitor data available"
                }
            
            # Initialize result structure
            result: CompetitorAnalysisResult = {
                "competitors": [],
                "market_share": {},
                "strengths_weaknesses": {},
                "competitive_threats": [],
                "opportunities": [],
                "confidence": 0.8  # Base confidence
            }
            
            # Analyze each competitor
            for competitor in competitors:
                if isinstance(competitor, str):
                    competitor_name = competitor
                    competitor_data = {"name": competitor_name, "details": {}}
                else:
                    competitor_name = competitor.get("name", "Unknown")
                    competitor_data = competitor
                
                # Add basic competitor info
                competitor_info = {
                    "name": competitor_name,
                    "industry": industry,
                    "threat_level": "medium",  # Placeholder
                    "market_position": "challenger",  # Placeholder
                    "recent_activity": []  # Would be populated with actual data
                }
                
                # Add any additional data from the input
                if isinstance(competitor, dict):
                    competitor_info.update({
                        k: v for k, v in competitor.items() 
                        if k != "name" and k != "details"
                    })
                
                result["competitors"].append(competitor_info)
                
                # Initialize strengths/weaknesses
                result["strengths_weaknesses"][competitor_name] = {
                    "strengths": ["Strong brand presence"],  # Placeholder
                    "weaknesses": ["Limited market share"]  # Placeholder
                }
            
            # Calculate market share (simplified)
            total_competitors = len(competitors) + 1  # +1 for our company
            our_share = 0.4  # Placeholder - would be calculated from real data
            
            result["market_share"][company_name] = our_share
            remaining_share = (1.0 - our_share) / len(competitors) if competitors else 0
            
            for comp in result["competitors"]:
                result["market_share"][comp["name"]] = remaining_share
            
            # Identify competitive threats (simplified)
            result["competitive_threats"] = [
                {
                    "competitor": comp["name"],
                    "threat": "New product launch",
                    "impact": "medium",
                    "likelihood": "high"
                }
                for comp in result["competitors"][:2]  # Top 2 competitors as example
            ]
            
            # Identify opportunities (simplified)
            result["opportunities"] = [
                {
                    "area": f"Market expansion in {industry}",
                    "potential": "high",
                    "effort_required": "medium"
                },
                {
                    "area": "Upselling to existing customers",
                    "potential": "medium",
                    "effort_required": "low"
                }
            ]
            
            # Adjust confidence based on data quality
            if len(data.get("data_points", [])) < 10:
                result["confidence"] *= 0.8  # Lower confidence with less data
            
            logger.info(f"Completed competitor analysis for {len(competitors)} competitors")
            
            return {
                **result,
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Error in competitor analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "error": error_msg,
                "competitors": [],
                "market_share": {},
                "strengths_weaknesses": {},
                "competitive_threats": [],
                "opportunities": [],
                "confidence": 0.0
            }
    
    async def _analyze_market_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market trends and provide insights.
        
        Args:
            data: Dictionary containing the API response data with market information.
            
        Returns:
            Dict containing market trend analysis results with the following structure:
            {
                "trends": List[Dict],  # Current market trends
                "growth_areas": List[Dict],  # Identified growth opportunities
                "risks": List[Dict],  # Potential market risks
                "predictions": Dict[str, Any],  # Future market predictions
                "confidence": float,  # Confidence score (0.0 to 1.0)
                "status": str,  # "success" or "error"
                "error": Optional[str]  # Error message if status is "error"
            }
        """
        try:
            logger.info("Starting market trend analysis")
            
            # Extract relevant data
            company_name = data.get("company", {}).get("name", "Our Company")
            industry = data.get("company", {}).get("industry", "")
            data_points = data.get("data_points", [])
            
            # Initialize result structure
            result: MarketTrendsResult = {
                "trends": [],
                "growth_areas": [],
                "risks": [],
                "predictions": {},
                "confidence": 0.85  # Base confidence
            }
            
            # Analyze sentiment from data points (if available)
            sentiments = [
                point.get("sentiment", 0) 
                for point in data_points 
                if isinstance(point, dict) and "sentiment" in point
            ]
            
            avg_sentiment = statistics.mean(sentiments) if sentiments else 0
            
            # Identify current trends based on data points
            result["trends"] = [
                {
                    "name": f"Growing interest in {industry}",
                    "direction": "up" if avg_sentiment > 0 else "down" if avg_sentiment < 0 else "stable",
                    "strength": min(abs(avg_sentiment) * 2, 1.0),  # Scale to 0-1 range
                    "description": f"{industry} sector showing {'positive' if avg_sentiment > 0 else 'negative' if avg_sentiment < 0 else 'stable'} sentiment"
                },
                {
                    "name": "Digital transformation",
                    "direction": "up",
                    "strength": 0.8,
                    "description": "Accelerated digital adoption across industries"
                }
            ]
            
            # Identify growth areas
            result["growth_areas"] = [
                {
                    "area": f"{industry} technology solutions",
                    "potential": "high",
                    "market_size": "growing",
                    "description": f"Increasing demand for technology solutions in {industry}"
                },
                {
                    "area": "Sustainable and green solutions",
                    "potential": "high",
                    "market_size": "large",
                    "description": "Growing focus on environmental sustainability"
                }
            ]
            
            # Identify potential risks
            result["risks"] = [
                {
                    "name": "Economic uncertainty",
                    "impact": "high",
                    "likelihood": "medium",
                    "description": "Potential economic slowdown affecting market growth"
                },
                {
                    "name": "Regulatory changes",
                    "impact": "medium",
                    "likelihood": "high",
                    "description": f"Upcoming regulations in {industry} may require adjustments"
                }
            ]
            
            # Make predictions
            result["predictions"] = {
                "timeframe": "next_12_months",
                "market_growth": {
                    "prediction": "moderate_growth",
                    "confidence": 0.75,
                    "factors": [
                        "Increasing digital adoption",
                        f"Growing demand in {industry}",
                        "Economic recovery"
                    ]
                },
                "key_drivers": [
                    "Technology innovation",
                    "Changing consumer behavior",
                    "Regulatory developments"
                ]
            }
            
            # Adjust confidence based on data quality
            if len(data_points) < 5:
                result["confidence"] *= 0.8  # Lower confidence with less data
                
            logger.info("Completed market trend analysis")
            
            return {
                **result,
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Error in market trend analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "error": error_msg,
                "trends": [],
                "growth_areas": [],
                "risks": [],
                "predictions": {},
                "confidence": 0.0
            }
    
    async def _analyze_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform sentiment analysis on the provided data.
        
        Args:
            data: Dictionary containing the data to analyze, including text and sentiment scores.
            
        Returns:
            Dict containing sentiment analysis results with the following structure:
            {
                "overall_sentiment": {
                    "score": float,  # -1.0 to 1.0
                    "label": str,  # "positive", "negative", or "neutral"
                    "confidence": float  # 0.0 to 1.0
                },
                "sentiment_by_category": Dict[str, Dict[str, float]],  # Sentiment by category
                "key_phrases": List[Dict],  # Extracted key phrases with sentiment
                "entities": List[Dict],  # Named entities with sentiment
                "confidence": float,  # Overall confidence (0.0 to 1.0)
                "status": str,  # "success" or "error"
                "error": Optional[str]  # Error message if status is "error"
            }
        """
        try:
            logger.info("Starting sentiment analysis")
            
            # Extract data points and text content
            data_points = data.get("data_points", [])
            texts = [
                point.get("text", "") 
                for point in data_points 
                if isinstance(point, dict) and "text" in point
            ]
            
            # Extract sentiment scores if available
            sentiments = [
                float(point.get("sentiment", 0)) 
                for point in data_points 
                if isinstance(point, dict) and "sentiment" in point
            ]
            
            # Calculate overall sentiment
            if sentiments:
                avg_sentiment = statistics.mean(sentiments)
                sentiment_label = (
                    "positive" if avg_sentiment > 0.1 
                    else "negative" if avg_sentiment < -0.1 
                    else "neutral"
                )
                sentiment_confidence = min(0.9, abs(avg_sentiment) * 2)  # Scale to 0-0.9 range
            else:
                # Fallback if no sentiment scores are available
                avg_sentiment = 0.0
                sentiment_label = "neutral"
                sentiment_confidence = 0.5
            
            # Initialize result structure
            result: SentimentAnalysisResult = {
                "overall_sentiment": {
                    "score": round(avg_sentiment, 4),
                    "label": sentiment_label,
                    "confidence": round(sentiment_confidence, 2)
                },
                "sentiment_by_category": {},
                "key_phrases": [],
                "entities": [],
                "confidence": 0.8  # Base confidence
            }
            
            # Analyze sentiment by category (simplified example)
            if texts:
                # In a real implementation, this would use NLP to categorize text
                categories = {
                    "product": ["product", "feature", "service"],
                    "pricing": ["price", "cost", "value", "afford"],
                    "support": ["support", "help", "service", "response"]
                }
                
                for category, keywords in categories.items():
                    category_texts = [
                        text for text in texts 
                        if any(keyword in text.lower() for keyword in keywords)
                    ]
                    
                    if category_texts:
                        # Simple keyword-based sentiment (in reality, use proper NLP)
                        positive_words = ["good", "great", "excellent", "love", "happy"]
                        negative_words = ["bad", "poor", "terrible", "hate", "angry"]
                        
                        pos_count = sum(1 for text in category_texts 
                                      if any(word in text.lower() for word in positive_words))
                        neg_count = sum(1 for text in category_texts 
                                      if any(word in text.lower() for word in negative_words))
                        
                        total = len(category_texts)
                        if total > 0:
                            sentiment_score = (pos_count - neg_count) / total
                            result["sentiment_by_category"][category] = {
                                "score": round(sentiment_score, 2),
                                "samples": total
                            }
            
            # Extract key phrases (simplified example)
            if texts:
                # In a real implementation, use NLP to extract key phrases
                result["key_phrases"] = [
                    {"phrase": "product quality", "sentiment": 0.7, "count": 5},
                    {"phrase": "customer service", "sentiment": 0.3, "count": 4},
                    {"phrase": "pricing", "sentiment": -0.2, "count": 3}
                ][:5]  # Limit to top 5
            
            # Extract entities (simplified example)
            if texts:
                # In a real implementation, use NER to extract entities
                result["entities"] = [
                    {"entity": data.get("company", {}).get("name", "Our Company"), 
                     "type": "ORGANIZATION", 
                     "sentiment": 0.5},
                    {"entity": data.get("company", {}).get("industry", ""), 
                     "type": "INDUSTRY", 
                     "sentiment": 0.6}
                ]
            
            # Adjust confidence based on data quality
            if len(data_points) < 3:
                result["confidence"] *= 0.8  # Lower confidence with less data
                
            logger.info(f"Completed sentiment analysis on {len(texts)} text samples")
            
            return {
                **result,
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Error in sentiment analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "error": error_msg,
                "overall_sentiment": {"score": 0, "label": "neutral", "confidence": 0},
                "sentiment_by_category": {},
                "key_phrases": [],
                "entities": [],
                "confidence": 0.0
            }
    
    async def _generate_swot_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive SWOT analysis.
        
        Args:
            data: Dictionary containing the analysis results.
            
        Returns:
            Dict containing SWOT analysis with the following structure:
            {
                "strengths": [
                    {
                        "id": str,
                        "description": str,
                        "evidence": List[str],
                        "impact": str,  # "high", "medium", "low"
                        "confidence": float
                    }
                ],
                "weaknesses": [...],
                "opportunities": [...],
                "threats": [...],
                "confidence": float
            }
        """
        logger.info("Generating SWOT analysis")
        
        # In a real implementation, this would use AI to generate the SWOT analysis
        # For now, we'll return sample data
        return {
            "strengths": [
                {
                    "id": "strength_1",
                    "description": "Strong brand reputation in the technology sector",
                    "evidence": [
                        "High brand recognition scores in market surveys",
                        "Consistently ranked in top tech companies"
                    ],
                    "impact": "high",
                    "confidence": 0.85
                }
            ],
            "weaknesses": [
                {
                    "id": "weakness_1",
                    "description": "Limited presence in emerging markets",
                    "evidence": [
                        "Lower market share in APAC and LATAM regions",
                        "Fewer localized offerings compared to competitors"
                    ],
                    "impact": "medium",
                    "confidence": 0.78
                }
            ],
            "opportunities": [
                {
                    "id": "opportunity_1",
                    "description": "Growing demand for digital transformation services",
                    "evidence": [
                        "Market research shows 30% annual growth in digital transformation spending",
                        "Increased demand for cloud migration services"
                    ],
                    "potential_impact": "high",
                    "confidence": 0.82
                }
            ],
            "threats": [
                {
                    "id": "threat_1",
                    "description": "Increasing competition from cloud-native consultancies",
                    "evidence": [
                        "New entrants with specialized cloud expertise",
                        "Price pressure from smaller, more agile competitors"
                    ],
                    "severity": "high",
                    "confidence": 0.79
                }
            ],
            "confidence": 0.81
        }

    def _generate_executive_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an executive summary based on the analysis results.
        
        Args:
            analysis_results: Dictionary containing all analysis results.
            
        Returns:
            Dict containing the executive summary with the following structure:
            {
                "overview": str,
                "key_findings": List[str],
                "recommendations": List[str],
                "confidence": float
            }
        """
        logger.info("Generating executive summary")
        
        # In a real implementation, this would use AI to generate the summary
        # For now, we'll return sample data
        return {
            "overview": "This report provides a comprehensive analysis of the current market position, competitive landscape, and strategic opportunities for the organization.",
            "key_findings": [
                "Strong brand reputation but facing increasing competition",
                "Significant growth opportunities in digital transformation services",
                "Need to address weaknesses in emerging market presence"
            ],
            "recommendations": [
                "Expand digital transformation service offerings",
                "Develop targeted strategies for emerging markets",
                "Enhance competitive differentiation through innovation"
            ],
            "confidence": 0.88
        }

    def _generate_visualization_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for visualizations in the report.
        
        Args:
            analysis_results: Dictionary containing all analysis results.
            
        Returns:
            Dict containing visualization data with the following structure:
            {
                "charts": [
                    {
                        "type": str,  # e.g., "bar", "line", "pie", "radar"
                        "title": str,
                        "data": Dict,
                        "description": str,
                        "id": str
                    }
                ],
                "tables": [
                    {
                        "title": str,
                        "headers": List[str],
                        "rows": List[List[Any]],
                        "id": str
                    }
                ],
                "metrics": {
                    "key_metrics": Dict[str, Any],
                    "benchmarks": Dict[str, Any]
                }
            }
        """
        logger.info("Generating visualization data")
        
        # Sample visualization data
        return {
            "charts": [
                {
                    "type": "bar",
                    "title": "Market Share by Competitor",
                    "data": {
                        "labels": ["TCS", "Competitor A", "Competitor B", "Competitor C"],
                        "datasets": [{
                            "label": "Market Share (%)",
                            "data": [25, 20, 18, 15],
                            "backgroundColor": ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2"]
                        }]
                    },
                    "description": "Market share comparison with key competitors",
                    "id": "market_share_chart"
                },
                {
                    "type": "line",
                    "title": "Revenue Growth Trend",
                    "data": {
                        "labels": ["2021", "2022", "2023", "2024"],
                        "datasets": [{
                            "label": "Revenue (in billions)",
                            "data": [22.2, 25.7, 27.9, 29.1],
                            "borderColor": "#4e79a7",
                            "fill": False
                        }]
                    },
                    "description": "Annual revenue growth over the past 4 years",
                    "id": "revenue_trend_chart"
                },
                {
                    "type": "radar",
                    "title": "Competitive Positioning",
                    "data": {
                        "labels": ["Innovation", "Market Share", "Customer Satisfaction", "Financial Strength", "Talent"],
                        "datasets": [
                            {
                                "label": "TCS",
                                "data": [85, 80, 88, 82, 87],
                                "borderColor": "#4e79a7",
                                "backgroundColor": "rgba(78, 121, 167, 0.2)"
                            },
                            {
                                "label": "Industry Average",
                                "data": [75, 70, 72, 68, 74],
                                "borderColor": "#f28e2b",
                                "backgroundColor": "rgba(242, 142, 43, 0.2)"
                            }
                        ]
                    },
                    "description": "Competitive positioning across key dimensions",
                    "id": "competitive_positioning_chart"
                }
            ],
            "tables": [
                {
                    "title": "SWOT Analysis Summary",
                    "headers": ["Category", "Key Points", "Impact/Confidence"],
                    "rows": [
                        ["Strengths", "Strong brand, Technical expertise", "High Impact (0.85)"],
                        ["Weaknesses", "Limited emerging market presence", "Medium Impact (0.78)"],
                        ["Opportunities", "Digital transformation growth", "High Potential (0.82)"],
                        ["Threats", "Increasing competition", "High Severity (0.79)"]
                    ],
                    "id": "swot_summary_table"
                },
                {
                    "title": "Key Performance Indicators",
                    "headers": ["Metric", "Value", "YoY Change", "Industry Benchmark"],
                    "rows": [
                        ["Revenue Growth", "8.5%", "+1.2%", "6.8%"],
                        ["Operating Margin", "25.3%", "+0.8%", "22.1%"],
                        ["Customer Satisfaction", "4.6/5", "+0.2", "4.3/5"],
                        ["Employee Retention", "89%", "+3%", "82%"]
                    ],
                    "id": "kpi_table"
                }
            ],
            "metrics": {
                "key_metrics": {
                    "revenue_growth": "8.5%",
                    "operating_margin": "25.3%",
                    "market_share": "18.2%",
                    "customer_satisfaction": "4.6/5",
                    "employee_engagement": "87%"
                },
                "benchmarks": {
                    "industry_average_revenue_growth": "6.8%",
                    "industry_average_margin": "22.1%",
                    "top_quartile_revenue_growth": "10.2%",
                    "top_quartile_margin": "27.5%"
                }
            }
        }

    def _generate_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate strategic recommendations based on the analysis.
        
        Args:
            data: Dictionary containing the analysis results.
            
        Returns:
            List of recommendation dictionaries with the following structure:
            [
                {
                    "id": str,  # Unique identifier (e.g., "rec_001")
                    "title": str,  # Short, action-oriented title
                    "description": str,  # Detailed description
                    "rationale": str,  # Business case and reasoning
                    "expected_impact": str,  # "high", "medium", or "low"
                    "effort_required": str,  # "low", "medium", or "high"
                    "time_horizon": str,  # "immediate" (0-3 months), "short_term" (3-12 months), "long_term" (1-3 years)
                    "priority": str,  # "critical", "high", "medium", "low"
                    "category": str,  # e.g., "revenue_growth", "cost_reduction", "risk_mitigation"
                    "metrics_affected": List[str],  # Which KPIs this impacts
                    "dependencies": List[str],  # Other recommendations or prerequisites
                    "responsible_party": str,  # Suggested owner/team
                    "estimated_roi": str,  # Expected return on investment
                    "confidence": float,  # 0.0 to 1.0
                    "implementation_steps": List[Dict]  # Breakdown of steps to implement
                },
                ...
            ]
        """
        try:
            logger.info("Generating recommendations")
            
            # Extract relevant data from the analysis
            company_name = data.get("company", {}).get("name", "the company")
            industry = data.get("company", {}).get("industry", "your industry")
            
            # Get sentiment analysis results if available
            sentiment_analysis = data.get("sentiment_analysis", {})
            sentiment_score = sentiment_analysis.get("overall_sentiment", {}).get("score", 0)
            
            # Get market trends if available
            market_trends = data.get("market_trends", {})
            
            # Initialize recommendations list
            recommendations: List[Dict[str, Any]] = []
            
            # Recommendation based on sentiment
            if sentiment_score < -0.2:  # Negative sentiment
                recommendations.append({
                    "id": "sentiment_improvement",
                    "title": "Address Negative Sentiment",
                    "description": (
                        f"Address the negative sentiment ({sentiment_score:.2f}) by identifying and "
                        "resolving key pain points mentioned in customer feedback."
                    ),
                    "impact": "high",
                    "effort": "medium",
                    "priority": "immediate",
                    "category": "customer_experience",
                    "metrics_affected": ["customer_satisfaction", "retention"],
                    "estimated_benefit": "Improved customer satisfaction and reduced churn"
                })
            
            # Recommendation for market trends
            if market_trends.get("trends"):
                for trend in market_trends["trends"]:
                    if trend.get("strength", 0) > 0.7:  # Strong trend
                        recommendations.append({
                            "id": f"trend_{trend.get('name', '').lower().replace(' ', '_')}",
                            "title": f"Capitalize on: {trend.get('name', 'Market Trend')}",
                            "description": (
                                f"Align strategies with the strong market trend: {trend.get('description')}"
                            ),
                            "impact": "high",
                            "effort": "medium",
                            "priority": "short_term",
                            "category": "strategy",
                            "metrics_affected": ["market_position", "revenue"],
                            "estimated_benefit": "Increased market relevance and potential revenue growth"
                        })
            
            # Standard recommendations based on industry best practices
            standard_recommendations = [
                {
                    "id": "digital_transformation",
                    "title": "Accelerate Digital Transformation",
                    "description": (
                        f"Invest in digital tools and platforms to improve operational efficiency "
                        f"and customer experience in the {industry} sector."
                    ),
                    "impact": "high",
                    "effort": "high",
                    "priority": "short_term",
                    "category": "technology",
                    "metrics_affected": ["efficiency", "customer_satisfaction"],
                    "estimated_benefit": "Improved operational efficiency and competitive advantage"
                },
                {
                    "id": "customer_feedback_loop",
                    "title": "Implement Continuous Feedback Loop",
                    "description": (
                        "Establish a system to collect and analyze customer feedback "
                        "continuously to make data-driven improvements."
                    ),
                    "impact": "medium",
                    "effort": "medium",
                    "priority": "short_term",
                    "category": "customer_experience",
                    "metrics_affected": ["customer_satisfaction", "product_quality"],
                    "estimated_benefit": "Better product-market fit and higher customer satisfaction"
                },
                {
                    "id": "competitive_analysis",
                    "title": "Conduct Competitive Analysis",
                    "description": (
                        f"Perform a thorough analysis of competitors in the {industry} sector "
                        "to identify opportunities for differentiation."
                    ),
                    "impact": "high",
                    "effort": "medium",
                    "priority": "short_term",
                    "category": "strategy",
                    "metrics_affected": ["market_share", "competitive_position"],
                    "estimated_benefit": "Identified opportunities for differentiation and growth"
                }
            ]
            
            # Add standard recommendations
            recommendations.extend(standard_recommendations)
            
            # Limit to top 5 recommendations
            recommendations = sorted(
                recommendations, 
                key=lambda x: (x["priority"], x["impact"]), 
                reverse=True
            )[:5]
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            return recommendations
            
        except Exception as e:
            error_msg = f"Error generating recommendations: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return [
                {
                    "id": "error",
                    "title": "Error Generating Recommendations",
                    "description": "An error occurred while generating recommendations. Please try again later.",
                    "impact": "low",
                    "effort": "low",
                    "priority": "long_term",
                    "category": "system",
                    "metrics_affected": [],
                    "estimated_benefit": "N/A"
                }
            ]
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

async def example_usage():
    """Example usage of the EnhancedAIService with the analyze_data method."""
    # Sample API data - in a real scenario, this would come from your API
    sample_data = {
        "data_points": [
            {"id": 1, "text": "Positive review about our product", "sentiment": 0.8},
            {"id": 2, "text": "Competitor A launched a new feature", "sentiment": -0.2},
            {"id": 3, "text": "Market trends show growth in our sector", "sentiment": 0.6}
        ],
        "company": {
            "name": "Example Corp",
            "industry": "Technology",
            "competitors": ["Competitor A", "Competitor B"]
        }
    }
    
    try:
        # Initialize the service (API key would typically come from environment variables)
        async with EnhancedAIService() as ai_service:
            # Analyze the data
            print("Starting analysis...")
            result = await ai_service.analyze_data(sample_data)
            
            # Print the results
            print("\nAnalysis Results:")
            print(json.dumps(result, indent=2, default=str))
            
            # Example of checking the status
            if result["status"] == "success":
                print("\nAnalysis completed successfully!")
                print(f"Analyzed {result['data']['metadata']['data_points_analyzed']} data points.")
            else:
                print(f"\nError during analysis: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(example_usage())
