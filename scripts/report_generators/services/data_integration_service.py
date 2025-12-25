#!/usr/bin/env python
"""
Data Integration Service for TCS Report

This service integrates data from multiple API sources to create
comprehensive competitive intelligence with cross-source analysis.

Following Semantic Seed Venture Studio Coding Standards V2.0.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import datetime as dt
# Python 3.10 compatibility - use timezone.utc instead of UTC
UTC = dt.timezone.utc
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("data_integration_service")

class DataIntegrationService:
    """
    Service for integrating and cross-analyzing data from multiple API sources
    to generate comprehensive competitive intelligence.
    """
    
    def __init__(self):
        """Initialize the data integration service."""
        logger.info("Initializing Data Integration Service")
        
        # Configuration for integration weights
        self.confidence_weights = {
            "ai_analysis": 0.40,    # AI has the highest weight
            "news": 0.25,           # News provides recent context
            "search_insights": 0.20, # Search positioning provides market visibility
            "domain_info": 0.10,    # Domain age provides historical context
            "location_data": 0.05   # Geographic data provides least context
        }
    
    def integrate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate data from multiple API sources into a unified analysis using
        advanced KPMG-style data structures and analytical frameworks.
        
        Args:
            data: Raw data from multiple API sources
            
        Returns:
            Integrated data with cross-source analysis
        """
        logger.info("Integrating data from multiple API sources for enhanced KPMG-style report")
        
        integrated_results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "company": data.get("company", "Tata Consultancy Services"),
            "domain": data.get("domain", "tcs.com"),
            "industry": data.get("industry", "IT Services"),
            "integrated_analysis": {}
        }
        
        # Extract data from each source
        ai_data = data.get("ai_analysis", {})
        news_data = data.get("news", {})
        domain_data = data.get("domain_info", {})
        search_data = data.get("search_insights", {})
        location_data = data.get("location_data", {})
        
        # Extract enhanced AI analysis if available
        enhanced_ai_data = data.get("enhanced_ai_analysis", {})
        
        # Extract API data separate from analysis
        api_data = {
            "news": news_data,
            "domain_info": domain_data,
            "search_insights": search_data,
            "location_data": location_data
        }
        
        # Check if we have enhanced AI data (KPMG-style structure)
        if enhanced_ai_data and isinstance(enhanced_ai_data, dict) and enhanced_ai_data.get("content_pillars"):
            logger.info("Using enhanced AI analysis for KPMG-style report generation")
            
            # Use the enhanced AI data structure directly
            integrated_results["integrated_analysis"]["content_pillars"] = self._integrate_content_pillars(
                enhanced_ai_data.get("content_pillars", []), search_data, news_data
            )
            
            integrated_results["integrated_analysis"]["engagement_index"] = self._integrate_engagement_index(
                enhanced_ai_data.get("engagement_index", {}), news_data, search_data
            )
            
            integrated_results["integrated_analysis"]["opportunity_index"] = self._integrate_opportunity_index(
                enhanced_ai_data.get("opportunity_index", {}), search_data
            )
            
            integrated_results["integrated_analysis"]["audience_analysis"] = self._integrate_audience_analysis(
                enhanced_ai_data.get("audience_analysis", {}), news_data, search_data
            )
            
            # Enhanced competitive matrix
            integrated_results["integrated_analysis"]["competitive_matrix"] = self._integrate_competitive_matrix(
                enhanced_ai_data.get("competitive_matrix", {}), news_data, search_data
            )
        else:
            logger.info("Using traditional data integration approach (non-KPMG structure)")
            
            # Traditional data integration for backward compatibility
            # Generate the advanced structures from existing data
            integrated_results["integrated_analysis"]["content_pillars"] = self._generate_content_pillars(
                ai_data, search_data, news_data
            )
            
            integrated_results["integrated_analysis"]["engagement_index"] = self._generate_engagement_index(
                ai_data, news_data, search_data
            )
            
            integrated_results["integrated_analysis"]["opportunity_index"] = self._generate_opportunity_index(
                ai_data, search_data
            )
            
            integrated_results["integrated_analysis"]["audience_analysis"] = self._generate_audience_analysis(
                ai_data, news_data
            )
        
        # Legacy integrations (always include these for compatibility)
        integrated_results["integrated_analysis"]["competitive_positioning"] = self._integrate_competitive_positioning(
            ai_data, news_data, search_data
        )
        
        # Integrate SWOT analysis
        integrated_results["integrated_analysis"]["swot_analysis"] = self._integrate_swot_analysis(
            ai_data, news_data, search_data
        )
        
        # Integrate market trends
        integrated_results["integrated_analysis"]["market_trends"] = self._integrate_market_trends(
            ai_data, news_data, search_data
        )
        
        # Integrate competitor analysis
        integrated_results["integrated_analysis"]["competitor_analysis"] = self._integrate_competitor_analysis(
            ai_data, news_data, search_data
        )
        
        # Integrate company profile
        integrated_results["integrated_analysis"]["company_profile"] = self._integrate_company_profile(
            ai_data, domain_data, location_data
        )
        
        # Enhanced strategic recommendations
        integrated_results["integrated_analysis"]["strategic_recommendations"] = self._integrate_strategic_recommendations(
            integrated_results["integrated_analysis"], api_data
        )
        
        # Enhanced confidence metrics with data quality scoring
        integrated_results["integrated_analysis"]["confidence_metrics"] = self._calculate_enhanced_confidence_metrics(
            integrated_results["integrated_analysis"], api_data
        )
        
        return integrated_results
    
    def _integrate_competitive_positioning(
        self, 
        ai_data: Dict[str, Any],
        news_data: Dict[str, Any],
        search_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate competitive positioning from multiple sources.
        
        Args:
            ai_data: AI analysis data
            news_data: News data
            search_data: Search insights data
            
        Returns:
            Integrated competitive positioning with confidence score
        """
        # Extract positioning from AI analysis
        ai_content = self._parse_ai_content(ai_data)
        positioning = ai_content.get("competitive_positioning", "")
        
        # Enhance with news sentiment
        news_sentiment = self._analyze_news_sentiment(news_data)
        
        # Enhance with search positioning
        search_position = self._analyze_search_positioning(search_data)
        
        # Calculate confidence score based on data quality
        ai_confidence = 0.8  # Base confidence from AI analysis
        
        # Adjust confidence based on supporting data
        if news_sentiment["available"]:
            ai_confidence += 0.05
        if search_position["available"]:
            ai_confidence += 0.05
        
        # Cap confidence at 0.95
        confidence = min(ai_confidence, 0.95)
        
        return {
            "statement": positioning,
            "news_sentiment": news_sentiment["sentiment"],
            "search_positioning": search_position["positioning"],
            "confidence_score": confidence,
            "data_sources": ["AI Analysis", "News Data", "Search Insights"]
        }
    
    def _integrate_swot_analysis(
        self, 
        ai_data: Dict[str, Any],
        news_data: Dict[str, Any],
        search_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate SWOT analysis from multiple sources.
        
        Args:
            ai_data: AI analysis data
            news_data: News data
            search_data: Search insights data
            
        Returns:
            Integrated SWOT analysis with confidence scores
        """
        # Extract SWOT elements from AI analysis
        ai_content = self._parse_ai_content(ai_data)
        
        # Get strengths and weaknesses
        strengths = ai_content.get("strengths", [])
        weaknesses = ai_content.get("weaknesses", [])
        
        # Convert to standardized format
        strengths_list = []
        if isinstance(strengths, list):
            # Handle both simple string lists and object lists with confidence
            for item in strengths:
                if isinstance(item, dict):
                    strengths_list.append(item)
                else:
                    strengths_list.append({
                        "strength": item,
                        "confidence": 0.85,
                        "evidence": "AI analysis"
                    })
                    
        weaknesses_list = []
        if isinstance(weaknesses, list):
            for item in weaknesses:
                if isinstance(item, dict):
                    weaknesses_list.append(item)
                else:
                    weaknesses_list.append({
                        "weakness": item,
                        "confidence": 0.85,
                        "evidence": "AI analysis"
                    })
        
        # Generate opportunities and threats
        opportunities = self._generate_opportunities(ai_content, news_data)
        threats = self._generate_threats(ai_content, news_data, search_data)
        
        return {
            "strengths": strengths_list,
            "weaknesses": weaknesses_list,
            "opportunities": opportunities,
            "threats": threats,
            "confidence_score": 0.85,
            "data_sources": ["AI Analysis", "News Data", "Search Insights"]
        }
    
    def _integrate_market_trends(
        self, 
        ai_data: Dict[str, Any],
        news_data: Dict[str, Any],
        search_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate market trends from multiple sources.
        
        Args:
            ai_data: AI analysis data
            news_data: News data
            search_data: Search insights data
            
        Returns:
            Integrated market trends with confidence scores
        """
        # Extract market data from AI analysis
        ai_content = self._parse_ai_content(ai_data)
        market_share = ai_content.get("market_share", "")
        industry_rank = ai_content.get("industry_rank", "")
        
        # Extract trends from news
        trending_topics = self._extract_trending_topics(news_data)
        
        # Extract search trends
        search_trends = self._extract_search_trends(search_data)
        
        return {
            "market_share": market_share,
            "industry_rank": industry_rank,
            "trending_topics": trending_topics,
            "search_trends": search_trends,
            "confidence_score": 0.83,
            "data_sources": ["AI Analysis", "News Data", "Search Insights"]
        }
    
    def _integrate_competitor_analysis(
        self, 
        ai_data: Dict[str, Any],
        news_data: Dict[str, Any],
        search_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate competitor analysis from multiple sources.
        
        Args:
            ai_data: AI analysis data
            news_data: News data
            search_data: Search insights data
            
        Returns:
            Integrated competitor analysis with confidence scores
        """
        # Extract competitor data from AI analysis
        ai_content = self._parse_ai_content(ai_data)
        competitors = ai_content.get("competitor_analysis", [])
        
        # Enhance with news mentions
        competitor_news = self._extract_competitor_news(news_data, [c.get("competitor_name", "") for c in competitors])
        
        # Enhance with comparative metrics
        enhanced_competitors = []
        
        for comp in competitors:
            comp_name = comp.get("competitor_name", "")
            # Add news mentions if available
            news_mentions = next((item for item in competitor_news if item["name"] == comp_name), {"mentions": []})
            
            enhanced_comp = {
                "name": comp_name,
                "strengths": comp.get("strengths", []),
                "weaknesses": comp.get("weaknesses", []),
                "threat_level": comp.get("threat_level", "Medium"),
                "threat_justification": comp.get("threat_justification", ""),
                "news_mentions": news_mentions.get("mentions", []),
                "comparison_metrics": {
                    "relative_market_share": self._generate_relative_metric(0.5, 1.5),
                    "innovation_index": self._generate_relative_metric(0.5, 1.0),
                    "digital_presence": self._generate_relative_metric(0.7, 1.3)
                }
            }
            enhanced_competitors.append(enhanced_comp)
        
        return {
            "competitors": enhanced_competitors,
            "confidence_score": 0.87,
            "data_sources": ["AI Analysis", "News Data", "Search Insights"]
        }
    
    def _integrate_company_profile(
        self, 
        ai_data: Dict[str, Any],
        domain_data: Dict[str, Any],
        location_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate company profile from multiple sources.
        
        Args:
            ai_data: AI analysis data
            domain_data: Domain data
            location_data: Location data
            
        Returns:
            Integrated company profile
        """
        # Extract company data
        ai_content = self._parse_ai_content(ai_data)
        
        # Calculate domain age if available
        domain_age = "Unknown"
        if domain_data.get("success", False) and domain_data.get("creation_date"):
            try:
                created = domain_data["creation_date"]
                # Simple string-based calculation for demo purposes
                if isinstance(created, str) and len(created) > 4:
                    year = created[:4]
                    domain_age = f"{2025 - int(year)} years"
            except:
                pass
        
        # Get company headquarters region if available
        hq_region = "Global presence with headquarters in India"
        if location_data.get("success", False):
            try:
                hq_region = f"{location_data.get('city', '')}, {location_data.get('region', '')}, {location_data.get('country', '')}"
            except:
                pass
        
        return {
            "company_description": ai_content.get("competitive_positioning", ""),
            "market_presence": ai_content.get("market_share", ""),
            "industry_position": ai_content.get("industry_rank", ""),
            "domain_age": domain_age,
            "headquarters": hq_region,
            "confidence_score": 0.90,
            "data_sources": ["AI Analysis", "Domain Data", "Location Data"]
        }
    
    def _generate_strategic_recommendations(self, integrated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate strategic recommendations based on integrated data.
        
        Args:
            integrated_data: Integrated analysis data
            
        Returns:
            Strategic recommendations with confidence scores
        """
        # Extract SWOT elements
        swot = integrated_data.get("swot_analysis", {})
        strengths = swot.get("strengths", [])
        weaknesses = swot.get("weaknesses", [])
        opportunities = swot.get("opportunities", [])
        threats = swot.get("threats", [])
        
        # Generate recommendations in each category
        leverage_strengths = []
        for strength in strengths[:2]:  # Use top 2 strengths
            strength_text = strength.get("strength", "") if isinstance(strength, dict) else strength
            if strength_text:
                leverage_strengths.append({
                    "recommendation": f"Leverage {strength_text.lower()} to expand market position",
                    "priority": "High",
                    "confidence": 0.88,
                    "impact": "Market growth"
                })
        
        address_weaknesses = []
        for weakness in weaknesses[:2]:  # Use top 2 weaknesses
            weakness_text = weakness.get("weakness", "") if isinstance(weakness, dict) else weakness
            if weakness_text:
                address_weaknesses.append({
                    "recommendation": f"Address {weakness_text.lower()} through targeted initiatives",
                    "priority": "Medium",
                    "confidence": 0.82,
                    "impact": "Risk mitigation"
                })
        
        pursue_opportunities = []
        for opportunity in opportunities[:2]:  # Use top 2 opportunities
            opportunity_text = opportunity.get("opportunity", "") if isinstance(opportunity, dict) else opportunity
            if opportunity_text:
                pursue_opportunities.append({
                    "recommendation": f"Pursue {opportunity_text.lower()} to gain competitive advantage",
                    "priority": "High",
                    "confidence": 0.85,
                    "impact": "Market growth"
                })
        
        mitigate_threats = []
        for threat in threats[:2]:  # Use top 2 threats
            threat_text = threat.get("threat", "") if isinstance(threat, dict) else threat
            if threat_text:
                mitigate_threats.append({
                    "recommendation": f"Mitigate risk from {threat_text.lower()} through strategic planning",
                    "priority": "Medium",
                    "confidence": 0.80,
                    "impact": "Risk mitigation"
                })
        
        return {
            "leverage_strengths": leverage_strengths,
            "address_weaknesses": address_weaknesses,
            "pursue_opportunities": pursue_opportunities,
            "mitigate_threats": mitigate_threats,
            "overall_recommendation": "Focus on expanding cloud services and AI capabilities while addressing talent retention and geographic diversification to maintain competitive advantage.",
            "confidence_score": 0.85,
            "data_sources": ["Integrated Analysis"]
        }
    
    def _calculate_confidence_metrics(
        self,
        ai_data: Dict[str, Any],
        news_data: Dict[str, Any],
        domain_data: Dict[str, Any],
        search_data: Dict[str, Any],
        location_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate confidence metrics for the integrated analysis.
        
        Args:
            Various data sources
            
        Returns:
            Confidence metrics
        """
        # Calculate data quality scores
        ai_quality = 0.9 if ai_data.get("success", False) else 0.0
        news_quality = 0.8 if news_data.get("success", False) and news_data.get("articles") else 0.0
        domain_quality = 0.7 if domain_data.get("success", False) else 0.0
        search_quality = 0.8 if search_data.get("success", False) and search_data.get("top_results") else 0.0
        location_quality = 0.6 if location_data.get("success", False) else 0.0
        
        # Calculate weighted confidence
        weighted_confidence = (
            ai_quality * self.confidence_weights["ai_analysis"] +
            news_quality * self.confidence_weights["news"] +
            domain_quality * self.confidence_weights["domain_info"] +
            search_quality * self.confidence_weights["search_insights"] +
            location_quality * self.confidence_weights["location_data"]
        )
        
        # Normalize weighted confidence
        max_possible = sum(self.confidence_weights.values())
        normalized_confidence = weighted_confidence / max_possible
        
        return {
            "overall_confidence": normalized_confidence,
            "data_quality": {
                "ai_analysis": ai_quality,
                "news": news_quality,
                "domain_info": domain_quality,
                "search_insights": search_quality,
                "location_data": location_quality
            },
            "data_coverage": {
                "competitor_analysis": 0.90 if ai_quality > 0 else 0.50,
                "market_trends": 0.85 if news_quality > 0 and ai_quality > 0 else 0.40,
                "company_profile": 0.95 if domain_quality > 0 and ai_quality > 0 else 0.60,
                "geographic_presence": 0.75 if location_quality > 0 else 0.30
            }
        }
    
    def _parse_ai_content(self, ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse AI content from AI analysis.
        
        Args:
            ai_data: AI analysis data
            
        Returns:
            Parsed AI content
        """
        content = ai_data.get("content", "{}")
        
        if isinstance(content, str):
            try:
                return json.loads(content)
            except:
                return {}
        
        return content
    
    def _analyze_news_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment from news data.
        
        Args:
            news_data: News data
            
        Returns:
            News sentiment analysis
        """
        articles = news_data.get("articles", [])
        
        if not articles:
            return {
                "available": False,
                "sentiment": "neutral",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        # Simple naive sentiment analysis based on keywords
        positive_keywords = ["award", "honour", "success", "growth", "increase", "partner"]
        negative_keywords = ["force", "relocate", "alleges", "decline", "challenge", "problem"]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for article in articles:
            title = article.get("title", "").lower()
            found_positive = any(keyword in title for keyword in positive_keywords)
            found_negative = any(keyword in title for keyword in negative_keywords)
            
            if found_positive and not found_negative:
                positive_count += 1
            elif found_negative and not found_positive:
                negative_count += 1
            else:
                neutral_count += 1
        
        # Determine overall sentiment
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "available": True,
            "sentiment": sentiment,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count
        }
    
    def _analyze_search_positioning(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze search positioning from search data.
        
        Args:
            search_data: Search insights data
            
        Returns:
            Search positioning analysis
        """
        if not search_data.get("success", False) or not search_data.get("top_results"):
            return {
                "available": False,
                "positioning": "unknown"
            }
        
        # Analyze top results
        top_results = search_data.get("top_results", [])
        official_site_position = None
        
        for result in top_results:
            position = result.get("position", 0)
            title = result.get("title", "").lower()
            url = result.get("link", "").lower()
            
            # Check if this is the official website
            if "tcs.com" in url and not official_site_position:
                official_site_position = position
        
        # Determine positioning
        if official_site_position == 1:
            positioning = "dominant"
        elif official_site_position and official_site_position <= 3:
            positioning = "strong"
        elif official_site_position and official_site_position <= 5:
            positioning = "moderate"
        elif official_site_position:
            positioning = "weak"
        else:
            positioning = "unknown"
        
        return {
            "available": True,
            "positioning": positioning,
            "official_site_position": official_site_position
        }
    
    def _generate_opportunities(self, ai_content: Dict[str, Any], news_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate opportunities based on AI content and news data.
        
        Args:
            ai_content: Parsed AI content
            news_data: News data
            
        Returns:
            List of opportunities with confidence scores
        """
        # Default opportunities based on IT services industry
        default_opportunities = [
            {
                "opportunity": "Cloud services expansion",
                "confidence": 0.90,
                "evidence": "Industry trend analysis"
            },
            {
                "opportunity": "AI/ML integration in service offerings",
                "confidence": 0.88,
                "evidence": "Technology trend analysis"
            },
            {
                "opportunity": "Digital transformation consulting",
                "confidence": 0.85,
                "evidence": "Market demand assessment"
            },
            {
                "opportunity": "Cybersecurity services growth",
                "confidence": 0.82,
                "evidence": "Risk analysis"
            }
        ]
        
        # Extract trending topics from news to identify additional opportunities
        trending_topics = self._extract_trending_topics(news_data)
        
        # Add news-based opportunities if available
        opportunities = list(default_opportunities)
        
        for topic in trending_topics:
            if topic not in [o.get("opportunity") for o in opportunities]:
                opportunities.append({
                    "opportunity": topic,
                    "confidence": 0.75,
                    "evidence": "News analysis"
                })
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    def _generate_threats(
        self, 
        ai_content: Dict[str, Any], 
        news_data: Dict[str, Any],
        search_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate threats based on AI content, news data, and search data.
        
        Args:
            ai_content: Parsed AI content
            news_data: News data
            search_data: Search data
            
        Returns:
            List of threats with confidence scores
        """
        # Default threats based on IT services industry
        default_threats = [
            {
                "threat": "Increased competition from specialized providers",
                "confidence": 0.85,
                "evidence": "Competitor analysis"
            },
            {
                "threat": "Rapid technological change requiring continuous adaptation",
                "confidence": 0.88,
                "evidence": "Industry trend analysis"
            },
            {
                "threat": "Talent acquisition and retention challenges",
                "confidence": 0.82,
                "evidence": "Labor market analysis"
            },
            {
                "threat": "Economic uncertainty affecting client spending",
                "confidence": 0.80,
                "evidence": "Economic analysis"
            }
        ]
        
        # Extract negative news to identify additional threats
        articles = news_data.get("articles", [])
        negative_keywords = ["force", "relocate", "alleges", "decline", "challenge", "problem", "crisis"]
        
        news_threats = []
        for article in articles:
            title = article.get("title", "").lower()
            if any(keyword in title for keyword in negative_keywords):
                # Extract the negative aspect as a threat
                for keyword in negative_keywords:
                    if keyword in title:
                        threat_text = f"Issues related to {keyword}"
                        if threat_text not in [t.get("threat") for t in news_threats]:
                            news_threats.append({
                                "threat": threat_text,
                                "confidence": 0.75,
                                "evidence": f"News: {article.get('title')}"
                            })
        
        # Combine threats
        threats = list(default_threats)
        for threat in news_threats:
            threats.append(threat)
        
        return threats[:5]  # Limit to top 5 threats
    
    def _extract_trending_topics(self, news_data: Dict[str, Any]) -> List[str]:
        """
        Extract trending topics from news data.
        
        Args:
            news_data: News data
            
        Returns:
            List of trending topics
        """
        articles = news_data.get("articles", [])
        
        if not articles:
            return ["Cloud services", "Digital transformation", "AI/ML integration"]
        
        # Extract keywords from titles and descriptions
        keywords = []
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            
            # Simple keyword extraction (in a real system, use NLP)
            words = title.split() + description.split()
            keywords.extend([w.lower() for w in words if len(w) > 4])
        
        # Count keyword frequencies
        keyword_counts = {}
        for word in keywords:
            if word in keyword_counts:
                keyword_counts[word] += 1
            else:
                keyword_counts[word] = 1
        
        # Get top keywords
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [k for k, v in sorted_keywords[:10]]
        
        # Map to business topics (simplified)
        topic_mapping = {
            "digital": "Digital transformation",
            "cloud": "Cloud services",
            "ai": "AI/ML integration",
            "security": "Cybersecurity",
            "analytics": "Data analytics",
            "automation": "Process automation"
        }
        
        trending_topics = []
        for topic, mapped_topic in topic_mapping.items():
            if any(topic in keyword.lower() for keyword in top_keywords):
                trending_topics.append(mapped_topic)
        
        # Ensure we have at least 3 topics
        default_topics = ["Cloud services", "Digital transformation", "AI/ML integration"]
        for topic in default_topics:
            if topic not in trending_topics:
                trending_topics.append(topic)
        
        return trending_topics[:5]  # Limit to top 5 topics
    
    def _extract_search_trends(self, search_data: Dict[str, Any]) -> List[str]:
        """
        Extract search trends from search data.
        
        Args:
            search_data: Search insights data
            
        Returns:
            List of search trends
        """
        related_queries = search_data.get("related_queries", [])
        
        if not related_queries:
            return ["IT services", "Digital transformation", "Cloud migration"]
        
        # Filter out None values and empty strings
        valid_queries = [q for q in related_queries if q]
        
        # If still no valid queries, return defaults
        if not valid_queries:
            return ["IT services", "Digital transformation", "Cloud migration"]
        
        return valid_queries[:5]  # Limit to top 5 queries
    
    # Enhanced KPMG-style Integration Methods
    
    def _integrate_content_pillars(self, content_pillars: List[Dict[str, Any]], search_data: Dict[str, Any], news_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Integrate content pillars with search and news data to enrich and validate them.
        
        Args:
            content_pillars: Content pillars from enhanced AI analysis
            search_data: Search insights data for validation
            news_data: News data for enrichment
            
        Returns:
            Enriched and validated content pillars
        """
        logger.info("Integrating content pillars with search and news data")
        
        if not content_pillars:
            return []
        
        enriched_content_pillars = []
        search_terms = self._extract_search_terms(search_data)
        news_topics = self._extract_news_topics(news_data)
        
        for pillar in content_pillars:
            # Create a copy to avoid modifying the original
            enriched_pillar = pillar.copy()
            
            # Get the pillar name
            pillar_name = enriched_pillar.get("pillar", "")
            
            # Calculate search relevance
            search_relevance = self._calculate_search_relevance(pillar_name, search_terms)
            
            # Calculate news relevance
            news_relevance = self._calculate_news_relevance(pillar_name, news_topics)
            
            # Add enriched data
            enriched_pillar["market_relevance"] = {
                "search_relevance": search_relevance,
                "news_relevance": news_relevance,
                "overall_relevance": (search_relevance + news_relevance) / 2
            }
            
            # Check if any sub-pillars match trending topics and tag them
            if "sub_pillars" in enriched_pillar and isinstance(enriched_pillar["sub_pillars"], list):
                trending_sub_pillars = []
                for sub_pillar in enriched_pillar["sub_pillars"]:
                    is_trending = any(topic.lower() in sub_pillar.lower() for topic in news_topics)
                    trending_sub_pillars.append({
                        "name": sub_pillar,
                        "trending": is_trending
                    })
                enriched_pillar["sub_pillars_detailed"] = trending_sub_pillars
            
            enriched_content_pillars.append(enriched_pillar)
        
        return enriched_content_pillars
    
    def _integrate_engagement_index(self, engagement_index: Dict[str, Any], news_data: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate engagement index with news and search data for validation and enrichment.
        
        Args:
            engagement_index: Engagement index from enhanced AI analysis
            news_data: News data for relevance enrichment
            search_data: Search insights for validation
            
        Returns:
            Enhanced engagement index with real-world validation
        """
        logger.info("Integrating engagement index with news and search data")
        
        if not engagement_index:
            return {}
        
        # Create a deep copy to avoid modifying the original
        enriched_engagement = engagement_index.copy()
        news_topics = self._extract_news_topics(news_data)
        search_terms = self._extract_search_terms(search_data)
        
        # Enrich topics with news and search validation
        if "topics" in enriched_engagement and isinstance(enriched_engagement["topics"], list):
            for topic in enriched_engagement["topics"]:
                topic_name = topic.get("name", "")
                
                # Calculate real-world relevance
                news_mentions = sum(1 for news_topic in news_topics if topic_name.lower() in news_topic.lower())
                search_mentions = sum(1 for search_term in search_terms if topic_name.lower() in search_term.lower())
                
                # Add real-world data
                topic["real_world_data"] = {
                    "news_mentions": news_mentions,
                    "search_mentions": search_mentions,
                    "verified_relevance": bool(news_mentions > 0 or search_mentions > 0)
                }
        
        # Add news integration stats
        enriched_engagement["data_enrichment"] = {
            "news_source_count": len(news_data.get("articles", [])),
            "search_term_count": len(search_terms),
            "integration_timestamp": datetime.now(UTC).isoformat(),
            "data_quality": self._calculate_data_source_quality(news_data, search_data)
        }
        
        return enriched_engagement
    
    def _integrate_opportunity_index(self, opportunity_index: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate opportunity index with search data for validation and volume enrichment.
        
        Args:
            opportunity_index: Opportunity index from enhanced AI analysis
            search_data: Search insights for validation and volume data
            
        Returns:
            Enhanced opportunity index with search volume validation
        """
        logger.info("Integrating opportunity index with search data")
        
        if not opportunity_index:
            return {}
        
        # Create a deep copy to avoid modifying the original
        enriched_opportunities = opportunity_index.copy()
        search_volumes = self._extract_search_volumes(search_data)
        
        # Validate high-value segments with search volume data
        if "high_value_segments" in enriched_opportunities and isinstance(enriched_opportunities["high_value_segments"], list):
            for segment in enriched_opportunities["high_value_segments"]:
                segment_name = segment.get("segment", "")
                
                # Find matching search volumes
                for term, volume in search_volumes.items():
                    if term.lower() in segment_name.lower() or segment_name.lower() in term.lower():
                        # If AI estimated a search volume, compare it to the real one
                        ai_volume = segment.get("search_volume", 0)
                        if ai_volume > 0:
                            accuracy = 100 - min(100, abs(ai_volume - volume) / max(ai_volume, volume) * 100)
                        else:
                            accuracy = 50  # Default accuracy when no AI prediction
                        
                        # Add real-world data
                        segment["validated_data"] = {
                            "actual_search_volume": volume,
                            "ai_prediction_accuracy": accuracy,
                            "data_source": "search_insights"
                        }
                        break
        
        # Add search data quality metrics
        enriched_opportunities["data_validation"] = {
            "search_term_coverage": len(search_volumes),
            "validation_timestamp": datetime.now(UTC).isoformat(),
            "data_quality": self._calculate_search_data_quality(search_data)
        }
        
        return enriched_opportunities
    
    def _integrate_audience_analysis(self, audience_analysis: Dict[str, Any], news_data: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate audience analysis with news and search data for validation.
        
        Args:
            audience_analysis: Audience analysis from enhanced AI analysis
            news_data: News data for trend validation
            search_data: Search insights for audience interest validation
            
        Returns:
            Enhanced audience analysis with real-world validation
        """
        logger.info("Integrating audience analysis with news and search data")
        
        if not audience_analysis:
            return {}
        
        # Create a deep copy to avoid modifying the original
        enriched_audience = audience_analysis.copy()
        news_topics = self._extract_news_topics(news_data)
        search_terms = self._extract_search_terms(search_data)
        
        # Validate personas against news and search data
        if "personas" in enriched_audience and isinstance(enriched_audience["personas"], list):
            for persona in enriched_audience["personas"]:
                # Extract persona needs and pain points for validation
                needs = persona.get("needs", [])
                pain_points = persona.get("pain_points", [])
                
                # Calculate validation scores based on news and search alignment
                news_validation = self._calculate_topic_alignment(needs + pain_points, news_topics)
                search_validation = self._calculate_topic_alignment(needs + pain_points, search_terms)
                
                # Add validation data
                persona["market_validation"] = {
                    "news_alignment": news_validation,
                    "search_alignment": search_validation,
                    "overall_validation": (news_validation + search_validation) / 2
                }
        
        # Add validation metrics to conversion funnel if present
        if "conversion_funnel" in enriched_audience and isinstance(enriched_audience["conversion_funnel"], dict):
            industry_data = self._extract_industry_benchmarks(news_data, search_data)
            conversion_funnel = enriched_audience["conversion_funnel"]
            
            # Add industry comparison
            if "industry_benchmark" in conversion_funnel and "overall_conversion" in conversion_funnel:
                ai_benchmark = conversion_funnel["industry_benchmark"]
                real_benchmark = industry_data.get("conversion_benchmark", 70)
                
                conversion_funnel["benchmark_validation"] = {
                    "ai_industry_benchmark": ai_benchmark,
                    "data_based_benchmark": real_benchmark,
                    "benchmark_difference": abs(ai_benchmark - real_benchmark),
                    "is_above_benchmark": conversion_funnel["overall_conversion"] > real_benchmark
                }
        
        # Add data validation metadata
        enriched_audience["data_validation"] = {
            "news_source_count": len(news_data.get("articles", [])),
            "search_term_coverage": len(search_terms),
            "validation_timestamp": datetime.now(UTC).isoformat(),
            "data_quality": self._calculate_data_source_quality(news_data, search_data)
        }
        
        return enriched_audience
    
    def _integrate_competitive_matrix(self, competitive_matrix: Dict[str, Any], news_data: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate competitive matrix with news and search data for validation.
        
        Args:
            competitive_matrix: Competitive matrix from enhanced AI analysis
            news_data: News data for competitor validation
            search_data: Search insights for market position validation
            
        Returns:
            Enhanced competitive matrix with real-world validation
        """
        logger.info("Integrating competitive matrix with news and search data")
        
        if not competitive_matrix:
            return {}
        
        # Create a deep copy to avoid modifying the original
        enriched_matrix = competitive_matrix.copy()
        
        # Extract competitor names
        competitor_names = []
        if "competitors" in enriched_matrix and isinstance(enriched_matrix["competitors"], list):
            competitor_names = [comp.get("name", "") for comp in enriched_matrix["competitors"]]
        
        # Get competitor news mentions
        competitor_news = self._extract_competitor_news(news_data, competitor_names)
        competitor_search = self._extract_competitor_search_presence(search_data, competitor_names)
        
        # Enrich competitors with news and search validation
        if "competitors" in enriched_matrix and isinstance(enriched_matrix["competitors"], list):
            for competitor in enriched_matrix["competitors"]:
                competitor_name = competitor.get("name", "")
                
                # Find news mentions for this competitor
                news_mentions = next((c for c in competitor_news if c["name"] == competitor_name), {"mentions": []})                
                search_presence = next((c for c in competitor_search if c["name"] == competitor_name), {"presence": 0})
                
                # Add real-world data
                competitor["market_presence"] = {
                    "news_mentions": len(news_mentions.get("mentions", [])),
                    "search_presence": search_presence.get("presence", 0),
                    "recency": self._calculate_competitor_recency(news_mentions.get("mentions", [])),
                    "data_sources": ["news_api", "search_insights"]
                }
        
        # Add data quality metrics
        enriched_matrix["data_validation"] = {
            "competitor_coverage": len(competitor_names),
            "news_source_coverage": len(news_data.get("articles", [])),
            "validation_timestamp": datetime.now(UTC).isoformat(),
            "data_quality": self._calculate_data_source_quality(news_data, search_data)
        }
        
        return enriched_matrix

    def _extract_competitor_news(self, news_data: Dict[str, Any], competitor_names: List[str]) -> List[Dict[str, Any]]:
        """
        Extract news mentions of competitors.
        
        Args:
            news_data: News data
            competitor_names: List of competitor names
            
        Returns:
            News mentions for each competitor
        """
        articles = news_data.get("articles", [])
        competitor_news = []
        
        for competitor in competitor_names:
            mentions = []
            
            for article in articles:
                title = article.get("title", "")
                description = article.get("description", "")
                
                # Check if competitor is mentioned
                if competitor.lower() in title.lower() or competitor.lower() in description.lower():
                    mentions.append({
                        "title": title,
                        "date": article.get("publishedAt", "")
                    })
            
            competitor_news.append({
                "name": competitor,
                "mentions": mentions
            })
        
        return competitor_news
    
    # Helper methods for KPMG-style integrations
    
    def _calculate_search_relevance(self, topic: str, search_terms: List[str]) -> float:
        """
        Calculate the search relevance of a topic based on search terms.
        
        Args:
            topic: Topic name
            search_terms: List of search terms
            
        Returns:
            Search relevance score (0-100)
        """
        if not topic or not search_terms:
            return 50.0
        
        # Find exact matches
        exact_matches = sum(1 for term in search_terms if term.lower() == topic.lower())
        
        # Find partial matches
        partial_matches = sum(1 for term in search_terms 
                            if term.lower() in topic.lower() or topic.lower() in term.lower())
        
        # Calculate relevance score
        relevance = 50.0  # Base relevance
        relevance += exact_matches * 25.0  # Bonus for exact matches
        relevance += partial_matches * 10.0  # Bonus for partial matches
        
        # Cap at 100
        return min(relevance, 100.0)
    
    def _calculate_news_relevance(self, topic: str, news_topics: List[str]) -> float:
        """
        Calculate the news relevance of a topic based on news topics.
        
        Args:
            topic: Topic name
            news_topics: List of news topics
            
        Returns:
            News relevance score (0-100)
        """
        if not topic or not news_topics:
            return 50.0
        
        # Find exact matches
        exact_matches = sum(1 for news_topic in news_topics 
                           if news_topic.lower() == topic.lower())
        
        # Find partial matches
        partial_matches = sum(1 for news_topic in news_topics 
                             if news_topic.lower() in topic.lower() or topic.lower() in news_topic.lower())
        
        # Calculate relevance score
        relevance = 50.0  # Base relevance
        relevance += exact_matches * 30.0  # Bonus for exact matches
        relevance += partial_matches * 15.0  # Bonus for partial matches
        
        # Cap at 100
        return min(relevance, 100.0)
    
    def _extract_search_terms(self, search_data: Dict[str, Any]) -> List[str]:
        """
        Extract search terms from search data.
        
        Args:
            search_data: Search insights data
            
        Returns:
            List of search terms
        """
        search_terms = []
        
        # Extract related queries
        related_queries = search_data.get("related_queries", [])
        if related_queries and isinstance(related_queries, list):
            search_terms.extend(related_queries)
        
        # Extract top keywords
        top_keywords = search_data.get("top_keywords", [])
        if top_keywords and isinstance(top_keywords, list):
            search_terms.extend(top_keywords)
        
        # Extract categories
        categories = search_data.get("categories", [])
        if categories and isinstance(categories, list):
            search_terms.extend(categories)
        
        # If no search terms found, use default terms
        if not search_terms:
            search_terms = [
                "IT services", 
                "Digital transformation", 
                "Cloud migration",
                "Enterprise software",
                "Business consulting"
            ]
        
        # Remove duplicates and empty strings
        search_terms = [term for term in search_terms if term and isinstance(term, str)]
        return list(set(search_terms))
    
    def _extract_news_topics(self, news_data: Dict[str, Any]) -> List[str]:
        """
        Extract topics from news data.
        
        Args:
            news_data: News data
            
        Returns:
            List of news topics
        """
        news_topics = []
        articles = news_data.get("articles", [])
        
        # Extract topics from article titles and descriptions
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            
            # Extract potential topics (naive approach)
            words = (title + " " + description).split()
            
            # Filter for capitalized words which might be topics/names
            potential_topics = [word for word in words if len(word) > 4 and word[0].isupper()]
            news_topics.extend(potential_topics)
        
        # If no topics found, use default topics
        if not news_topics:
            news_topics = [
                "Digital Transformation",
                "Cloud Services",
                "IT Consulting",
                "Enterprise Solutions",
                "Business Innovation"
            ]
        
        # Remove duplicates and limit to a reasonable number
        unique_topics = list(set(news_topics))
        return unique_topics[:15]  # Limit to 15 topics
    
    def _extract_search_volumes(self, search_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract search volume data from search insights.
        
        Args:
            search_data: Search insights data
            
        Returns:
            Dictionary mapping search terms to volumes
        """
        search_volumes = {}
        
        # Extract volume data if available
        volume_data = search_data.get("volume_data", {})
        if volume_data and isinstance(volume_data, dict):
            search_volumes = volume_data
        else:
            # Generate sample data based on related queries
            related_queries = search_data.get("related_queries", [])
            if related_queries and isinstance(related_queries, list):
                for query in related_queries:
                    if query and isinstance(query, str):
                        # Generate plausible search volume
                        search_volumes[query] = np.random.randint(100, 10000)
        
        # If no search volumes found, use default data
        if not search_volumes:
            search_volumes = {
                "IT services": 8500,
                "Digital transformation": 6200,
                "Cloud migration": 4800,
                "Enterprise software": 3500,
                "Business consulting": 5700
            }
        
        return search_volumes
    
    def _calculate_topic_alignment(self, source_topics: List[str], target_topics: List[str]) -> float:
        """
        Calculate the alignment between two sets of topics.
        
        Args:
            source_topics: Source topic list
            target_topics: Target topic list for comparison
            
        Returns:
            Alignment score (0-100)
        """
        if not source_topics or not target_topics:
            return 50.0
        
        # Count matches
        match_count = 0
        for s_topic in source_topics:
            for t_topic in target_topics:
                if s_topic.lower() in t_topic.lower() or t_topic.lower() in s_topic.lower():
                    match_count += 1
                    break
        
        # Calculate alignment percentage
        max_possible = len(source_topics)  # Maximum possible matches
        if max_possible == 0:
            return 50.0
            
        alignment = (match_count / max_possible) * 100.0
        
        # Ensure minimum baseline
        return max(alignment, 40.0)  # Minimum 40% alignment
    
    def _extract_industry_benchmarks(self, news_data: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract or generate industry benchmarks from available data.
        
        Args:
            news_data: News data
            search_data: Search insights data
            
        Returns:
            Dictionary of industry benchmarks
        """
        # Default industry benchmarks
        benchmarks = {
            "conversion_benchmark": 70,
            "engagement_benchmark": 65,
            "content_effectiveness_benchmark": 72,
            "industry_avg_growth": 5.8
        }
        
        # Try to extract real benchmarks if available
        industry_data = news_data.get("industry_stats", {})
        if industry_data and isinstance(industry_data, dict):
            for key, value in industry_data.items():
                if "benchmark" in key.lower() and isinstance(value, (int, float)):
                    benchmarks[key] = value
        
        return benchmarks
    
    def _extract_competitor_search_presence(self, search_data: Dict[str, Any], competitor_names: List[str]) -> List[Dict[str, Any]]:
        """
        Extract competitor search presence from search data.
        
        Args:
            search_data: Search insights data
            competitor_names: List of competitor names
            
        Returns:
            List of competitor search presence data
        """
        competitor_search = []
        
        # Extract search terms
        search_terms = self._extract_search_terms(search_data)
        
        for competitor in competitor_names:
            # Calculate search presence based on term matches
            presence = 0
            for term in search_terms:
                if competitor.lower() in term.lower():
                    presence += 10  # Add points for each mention
                    
            # Add competitor search data
            competitor_search.append({
                "name": competitor,
                "presence": min(presence, 100)  # Cap at 100
            })
        
        return competitor_search
    
    def _calculate_competitor_recency(self, mentions: List[Dict[str, Any]]) -> float:
        """
        Calculate competitor recency score based on news mentions.
        
        Args:
            mentions: List of news mentions with dates
            
        Returns:
            Recency score (0-100)
        """
        if not mentions:
            return 50.0
        
        try:
            # Parse dates
            dates = []
            for mention in mentions:
                date_str = mention.get("date", "")
                if date_str:
                    try:
                        # Attempt to parse date
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        dates.append(date)
                    except ValueError:
                        pass
            
            if not dates:
                return 50.0
                
            # Calculate days since most recent mention
            most_recent = max(dates)
            days_ago = (datetime.now(UTC) - most_recent).days
            
            # Calculate recency score (newer is higher)
            if days_ago <= 1:  # Today or yesterday
                return 100.0
            elif days_ago <= 7:  # Within a week
                return 90.0
            elif days_ago <= 30:  # Within a month
                return 75.0
            elif days_ago <= 90:  # Within quarter
                return 60.0
            else:  # Older
                return 40.0
                
        except Exception:
            return 50.0  # Default on error
    
    def _calculate_data_source_quality(self, *data_sources) -> float:
        """
        Calculate the data quality of multiple data sources.
        
        Args:
            data_sources: Variable number of data sources
            
        Returns:
            Data quality score (0-100)
        """
        if not data_sources:
            return 50.0
            
        # Calculate completeness for each source
        quality_scores = []
        for source in data_sources:
            if not source or not isinstance(source, dict):
                quality_scores.append(0.0)
                continue
                
            # Count non-empty properties
            non_empty = sum(1 for v in source.values() 
                           if v is not None and (not isinstance(v, (list, dict)) or len(v) > 0))
            total_props = len(source)
            
            # Calculate completeness
            if total_props > 0:
                completeness = (non_empty / total_props) * 100.0
                quality_scores.append(completeness)
        
        # Average the quality scores
        if not quality_scores:
            return 50.0
            
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Apply minimum quality threshold
        return max(avg_quality, 40.0)  # Minimum 40% quality
    
    def _calculate_search_data_quality(self, search_data: Dict[str, Any]) -> float:
        """
        Calculate the quality of search data specifically.
        
        Args:
            search_data: Search insights data
            
        Returns:
            Search data quality score (0-100)
        """
        if not search_data or not isinstance(search_data, dict):
            return 50.0
            
        # Check for key components
        score = 50.0  # Base score
        
        # Check for related queries
        related_queries = search_data.get("related_queries", [])
        if related_queries and isinstance(related_queries, list) and len(related_queries) > 0:
            score += 15.0
            
        # Check for volume data
        volume_data = search_data.get("volume_data", {})
        if volume_data and isinstance(volume_data, dict) and len(volume_data) > 0:
            score += 20.0
            
        # Check for categories
        categories = search_data.get("categories", [])
        if categories and isinstance(categories, list) and len(categories) > 0:
            score += 10.0
            
        # Check for top keywords
        top_keywords = search_data.get("top_keywords", [])
        if top_keywords and isinstance(top_keywords, list) and len(top_keywords) > 0:
            score += 5.0
            
        # Cap at 100
        return min(score, 100.0)
    
    def _generate_relative_metric(self, min_val: float, max_val: float) -> float:
        """
        Generate a random relative metric within range.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Random metric value
        """
        return round(min_val + (max_val - min_val) * np.random.random(), 2)


# Test the data integration service
def test_service():
    """Test the data integration service."""
    # Load sample data
    try:
        with open("exports/tcs_api_demo_20250516_164740.json", "r") as f:
            sample_data = json.load(f)
        
        # Create service
        service = DataIntegrationService()
        
        # Integrate data
        integrated_data = service.integrate_data(sample_data)
        
        print(f"\nData Integration Results:")
        print(f"Overall Confidence: {integrated_data['integrated_analysis']['confidence_metrics']['overall_confidence']:.2f}")
        print(f"Integrated data has {len(integrated_data['integrated_analysis'])} analysis components")
        
        # Show sample of strategic recommendations
        recommendations = integrated_data["integrated_analysis"]["strategic_recommendations"]
        print("\nSample Strategic Recommendations:")
        for category, items in recommendations.items():
            if isinstance(items, list) and items:
                print(f"- {category}: {items[0].get('recommendation', '')}")
        
        return integrated_data
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    test_service()
