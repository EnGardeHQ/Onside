#!/usr/bin/env python
"""
Enhanced AI Analysis Service for OnSide Report Generation

This module provides the analyze_data method implementation for the EnhancedAIService class.
It serves as the core method for the OnSide report generator.
"""

import os
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("enhanced_ai_service")

async def analyze_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Primary entry point for analyzing API data and generating a comprehensive OnSide report.
    Coordinates all specialized analysis methods to produce a KPMG-style report integrating
    various data sources.
    
    Args:
        api_data: Data from various API sources including competitor data, market data,
                search data, and company information
                
    Returns:
        Comprehensive report with all analysis components, reasoning chains, and confidence metrics
    """
    logger.info("Starting comprehensive OnSide report generation")
    
    try:
        # Extract necessary data components
        company_data = api_data.get("company_data", {})
        competitor_data = api_data.get("competitor_data", [])
        market_data = api_data.get("market_data", {})
        search_data = api_data.get("search_data", {})
        industry_data = api_data.get("industry_data", {})
        
        # Initialize result structure
        result = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "report_type": "comprehensive",
                "company_name": company_data.get("company", "Unknown"),
                "data_completeness": self._calculate_data_completeness(api_data)
            },
            "analyses": {}
        }
        
        # Perform competitor analysis with fallback support
        try:
            competitor_analysis = await self.generate_competitor_analysis_with_cot(company_data)
            result["analyses"]["competitor_analysis"] = competitor_analysis
        except Exception as e:
            logger.error(f"Error in competitor analysis: {str(e)}")
            logger.error(traceback.format_exc())
            # Use fallback for this component
            result["analyses"]["competitor_analysis"] = self._generate_fallback_analysis(company_data.get("company", "Unknown"))
            result["metadata"]["fallbacks_triggered"] = True
        
        # Perform content pillars analysis
        try:
            content_analysis = await self.generate_content_pillars_analysis(company_data, market_data)
            result["analyses"]["content_pillars"] = content_analysis
        except Exception as e:
            logger.error(f"Error in content pillars analysis: {str(e)}")
            logger.error(traceback.format_exc())
            # Use fallback for this component
            result["analyses"]["content_pillars"] = self._get_fallback_content_pillars()
            result["metadata"]["fallbacks_triggered"] = True
            
        # Perform engagement index analysis
        try:
            engagement_analysis = await self.generate_engagement_index_analysis(company_data, competitor_data)
            result["analyses"]["engagement_index"] = engagement_analysis
        except Exception as e:
            logger.error(f"Error in engagement analysis: {str(e)}")
            logger.error(traceback.format_exc())
            # Use fallback for this component
            result["analyses"]["engagement_index"] = self._get_fallback_engagement_index()
            result["metadata"]["fallbacks_triggered"] = True
            
        # Perform opportunity index analysis
        try:
            opportunity_analysis = await self.generate_opportunity_index(company_data, search_data)
            result["analyses"]["opportunity_index"] = opportunity_analysis
        except Exception as e:
            logger.error(f"Error in opportunity analysis: {str(e)}")
            logger.error(traceback.format_exc())
            # Use fallback for this component
            result["analyses"]["opportunity_index"] = self._get_fallback_opportunity_index()
            result["metadata"]["fallbacks_triggered"] = True
            
        # Perform audience segmentation
        try:
            audience_analysis = await self.generate_audience_segmentation(company_data, industry_data)
            result["analyses"]["audience_segmentation"] = audience_analysis
        except Exception as e:
            logger.error(f"Error in audience analysis: {str(e)}")
            logger.error(traceback.format_exc())
            # Use fallback for this component
            result["analyses"]["audience_segmentation"] = self._get_fallback_audience_segmentation()
            result["metadata"]["fallbacks_triggered"] = True
            
        # Generate strategic recommendations based on all previous analyses
        try:
            # Combine all analyses for strategic recommendations
            integrated_data = {
                "company_data": company_data,
                "analyses": result["analyses"]
            }
            strategic_recommendations = await self.generate_strategic_recommendations(integrated_data)
            result["analyses"]["strategic_recommendations"] = strategic_recommendations
        except Exception as e:
            logger.error(f"Error in strategic recommendations: {str(e)}")
            logger.error(traceback.format_exc())
            # Use fallback for this component
            result["analyses"]["strategic_recommendations"] = self._get_fallback_strategic_recommendations()
            result["metadata"]["fallbacks_triggered"] = True
            
        # Calculate overall quality metrics
        result["metadata"]["quality_metrics"] = self._calculate_quality_metrics(result)
        
        logger.info("Comprehensive OnSide report generation completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating comprehensive OnSide report: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a minimal fallback result if the entire process fails
        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "report_type": "fallback",
                "company_name": api_data.get("company_data", {}).get("company", "Unknown"),
                "error": str(e),
                "fallbacks_triggered": True
            },
            "analyses": {
                "note": "Error occurred during report generation. Using fallback data.",
                "competitor_analysis": self._generate_fallback_analysis("Unknown")
            }
        }

def _calculate_data_completeness(self, api_data: Dict[str, Any]) -> float:
    """
    Calculate the completeness of input data for quality assessment.
    
    Args:
        api_data: Input API data for analysis
        
    Returns:
        Data completeness score between 0-1
    """
    # Define expected data keys and their importance weights
    expected_keys = {
        "company_data": 0.4,
        "competitor_data": 0.2,
        "market_data": 0.15,
        "search_data": 0.15,
        "industry_data": 0.1
    }
    
    completeness_score = 0.0
    
    # Check presence and basic quality of each key
    for key, weight in expected_keys.items():
        if key in api_data and api_data[key]:
            # Check if data has meaningful content
            if isinstance(api_data[key], dict) and api_data[key]:
                completeness_score += weight
            elif isinstance(api_data[key], list) and api_data[key]:
                completeness_score += weight
            else:
                # Partial credit for present but potentially limited data
                completeness_score += weight * 0.5
                
    return min(completeness_score, 1.0)  # Cap at 1.0

def _calculate_quality_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate quality metrics for the overall report.
    
    Args:
        result: Generated report data
        
    Returns:
        Quality metrics including confidence scores, data quality, and coverage
    """
    metrics = {
        "confidence": {},
        "overall_confidence": 0.0,
        "data_quality": 0.0,
        "coverage": 0.0,
        "reasoning_chain_completeness": 0.0
    }
    
    # Get confidence scores from each analysis component
    analyses = result.get("analyses", {})
    confidence_scores = []
    
    # Extract confidence metrics from each analysis
    for analysis_type, analysis_data in analyses.items():
        # Different analyses may store confidence in different structures
        if isinstance(analysis_data, dict):
            # Try different possible paths to confidence data
            confidence = (
                analysis_data.get("confidence") or
                analysis_data.get("metadata", {}).get("confidence") or
                analysis_data.get("overall_confidence") or
                analysis_data.get("content", {}).get("confidence") or
                0.7  # Default fallback confidence if not found
            )
            
            metrics["confidence"][analysis_type] = float(confidence)
            confidence_scores.append(float(confidence))
            
    # Calculate overall confidence (weighted average)
    if confidence_scores:
        metrics["overall_confidence"] = sum(confidence_scores) / len(confidence_scores)
        
    # Calculate data quality based on input data completeness
    metrics["data_quality"] = result.get("metadata", {}).get("data_completeness", 0.7)
    
    # Calculate coverage based on how many analysis types are present
    expected_analyses = 6  # Total number of analyses we expect
    actual_analyses = len(analyses)
    metrics["coverage"] = min(actual_analyses / expected_analyses, 1.0)
    
    # Calculate reasoning chain completeness
    reasoning_chains = 0
    for analysis_type, analysis_data in analyses.items():
        # Check if reasoning chains exist in different possible structures
        if isinstance(analysis_data, dict) and (
            "reasoning" in analysis_data or
            "reasoning_chain" in analysis_data or
            "reasoning_chains" in analysis_data or
            ("content" in analysis_data and isinstance(analysis_data["content"], dict) and
             ("reasoning" in analysis_data["content"] or "reasoning_chains" in analysis_data["content"]))
        ):
            reasoning_chains += 1
            
    metrics["reasoning_chain_completeness"] = min(reasoning_chains / actual_analyses, 1.0) if actual_analyses > 0 else 0.0
    
    return metrics
