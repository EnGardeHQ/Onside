from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from fastapi import HTTPException
from src.models.seo import ContentAsset
from src.services.ai.semantic_service import SemanticService

logger = logging.getLogger(__name__)

class PersonaAnalysisService:
    def __init__(self):
        self.semantic_service = SemanticService()
        self._initialize_persona_models()

    def _initialize_persona_models(self):
        """Initialize persona-specific ML models"""
        self.persona_models = {
            "intent_classifier": self._load_model("intent_classifier"),
            "behavior_predictor": self._load_model("behavior_predictor"),
            "preference_analyzer": self._load_model("preference_analyzer")
        }

    async def analyze_persona_alignment(self, content: ContentAsset, 
                                     persona: Dict) -> Dict:
        """Analyze how well content aligns with target persona"""
        try:
            # Demographic alignment
            demographic_score = await self._analyze_demographic_fit(content, persona)
            
            # Behavioral alignment
            behavioral_score = await self._analyze_behavioral_fit(content, persona)
            
            # Professional context
            professional_score = await self._analyze_professional_context(content, persona)
            
            # Content preferences
            preference_score = await self._analyze_content_preferences(content, persona)
            
            # Purchase journey stage
            journey_alignment = await self._analyze_journey_stage(content, persona)
            
            # Decision-making factors
            decision_factors = await self._analyze_decision_factors(content, persona)

            return {
                "overall_alignment": self._calculate_overall_alignment([
                    demographic_score,
                    behavioral_score,
                    professional_score,
                    preference_score
                ]),
                "component_scores": {
                    "demographic_alignment": demographic_score,
                    "behavioral_alignment": behavioral_score,
                    "professional_context": professional_score,
                    "preference_alignment": preference_score
                },
                "journey_stage": journey_alignment,
                "decision_factors": decision_factors,
                "recommendations": await self._generate_persona_recommendations(
                    content, 
                    persona,
                    demographic_score,
                    behavioral_score,
                    professional_score,
                    preference_score
                )
            }
        except Exception as e:
            logger.error(f"Error in persona analysis: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in persona analysis: {str(e)}"
            )

    async def _analyze_demographic_fit(self, content: ContentAsset, 
                                    persona: Dict) -> float:
        """Analyze demographic alignment"""
        try:
            demographic_factors = {
                "age_group": self._analyze_age_group_fit(content, persona),
                "education_level": self._analyze_education_fit(content, persona),
                "income_bracket": self._analyze_income_fit(content, persona),
                "location": self._analyze_location_relevance(content, persona),
                "language": self._analyze_language_fit(content, persona)
            }
            
            weights = {
                "age_group": 0.2,
                "education_level": 0.2,
                "income_bracket": 0.2,
                "location": 0.2,
                "language": 0.2
            }
            
            return sum(score * weights[factor] 
                      for factor, score in demographic_factors.items())
        except Exception as e:
            logger.error(f"Error in demographic analysis: {str(e)}")
            return 0.0

    async def _analyze_behavioral_fit(self, content: ContentAsset, 
                                   persona: Dict) -> float:
        """Analyze behavioral alignment"""
        try:
            behavioral_factors = {
                "content_consumption": self._analyze_consumption_patterns(content, persona),
                "device_usage": self._analyze_device_preferences(content, persona),
                "time_patterns": self._analyze_timing_preferences(content, persona),
                "interaction_style": self._analyze_interaction_preferences(content, persona)
            }
            
            weights = {
                "content_consumption": 0.3,
                "device_usage": 0.2,
                "time_patterns": 0.2,
                "interaction_style": 0.3
            }
            
            return sum(score * weights[factor] 
                      for factor, score in behavioral_factors.items())
        except Exception as e:
            logger.error(f"Error in behavioral analysis: {str(e)}")
            return 0.0

    async def _analyze_professional_context(self, content: ContentAsset, 
                                        persona: Dict) -> float:
        """Analyze professional context alignment"""
        try:
            professional_factors = {
                "industry_relevance": self._analyze_industry_fit(content, persona),
                "role_relevance": self._analyze_role_fit(content, persona),
                "company_size_fit": self._analyze_company_size_fit(content, persona),
                "decision_making_level": self._analyze_decision_level_fit(content, persona)
            }
            
            weights = {
                "industry_relevance": 0.3,
                "role_relevance": 0.3,
                "company_size_fit": 0.2,
                "decision_making_level": 0.2
            }
            
            return sum(score * weights[factor] 
                      for factor, score in professional_factors.items())
        except Exception as e:
            logger.error(f"Error in professional context analysis: {str(e)}")
            return 0.0

    async def _analyze_content_preferences(self, content: ContentAsset, 
                                       persona: Dict) -> float:
        """Analyze content preference alignment"""
        try:
            preference_factors = {
                "format_preference": self._analyze_format_fit(content, persona),
                "style_preference": self._analyze_style_fit(content, persona),
                "depth_preference": self._analyze_depth_fit(content, persona),
                "tone_preference": self._analyze_tone_fit(content, persona)
            }
            
            weights = {
                "format_preference": 0.25,
                "style_preference": 0.25,
                "depth_preference": 0.25,
                "tone_preference": 0.25
            }
            
            return sum(score * weights[factor] 
                      for factor, score in preference_factors.items())
        except Exception as e:
            logger.error(f"Error in preference analysis: {str(e)}")
            return 0.0

    async def _analyze_journey_stage(self, content: ContentAsset, 
                                  persona: Dict) -> Dict:
        """Analyze content alignment with purchase journey stage"""
        try:
            stages = {
                "awareness": self._calculate_awareness_fit(content, persona),
                "consideration": self._calculate_consideration_fit(content, persona),
                "decision": self._calculate_decision_fit(content, persona),
                "retention": self._calculate_retention_fit(content, persona)
            }
            
            best_stage = max(stages.items(), key=lambda x: x[1])
            
            return {
                "best_fit_stage": best_stage[0],
                "stage_scores": stages,
                "confidence": best_stage[1]
            }
        except Exception as e:
            logger.error(f"Error in journey stage analysis: {str(e)}")
            return {}

    async def _analyze_decision_factors(self, content: ContentAsset, 
                                    persona: Dict) -> Dict:
        """Analyze alignment with decision-making factors"""
        try:
            return {
                "primary_motivators": self._identify_motivators(content, persona),
                "pain_points": self._identify_pain_points(content, persona),
                "value_propositions": self._identify_value_props(content, persona),
                "objection_handling": self._analyze_objection_handling(content, persona)
            }
        except Exception as e:
            logger.error(f"Error in decision factors analysis: {str(e)}")
            return {}

    async def _generate_persona_recommendations(self, content: ContentAsset,
                                            persona: Dict,
                                            demographic_score: float,
                                            behavioral_score: float,
                                            professional_score: float,
                                            preference_score: float) -> List[Dict]:
        """Generate persona-specific content recommendations"""
        try:
            recommendations = []
            
            # Analyze areas for improvement
            if demographic_score < 0.7:
                recommendations.extend(
                    self._get_demographic_recommendations(content, persona)
                )
            
            if behavioral_score < 0.7:
                recommendations.extend(
                    self._get_behavioral_recommendations(content, persona)
                )
            
            if professional_score < 0.7:
                recommendations.extend(
                    self._get_professional_recommendations(content, persona)
                )
            
            if preference_score < 0.7:
                recommendations.extend(
                    self._get_preference_recommendations(content, persona)
                )
            
            return sorted(recommendations, 
                         key=lambda x: x.get('impact_score', 0), 
                         reverse=True)
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
