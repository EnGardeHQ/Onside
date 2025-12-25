from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import logging
from typing import List, Dict, Any, Optional, Union
from src.models.content import Content
from src.models.ai import AIInsight, InsightType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import torch

from src.services.ai.llm_service import LLMService, LLMProvider
from src.services.ai.chain_of_thought import ChainOfThoughtReasoning

logger = logging.getLogger(__name__)

class ContentAffinityService:
    def __init__(self):
        # Initialize sentence transformer model for embedding-based similarity
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize LLM service for enhanced semantic comparisons and fallback
        self.llm_service = LLMService()
        
    async def calculate_content_affinity(
        self,
        target_content: Content,
        comparison_contents: List[Content],
        db: AsyncSession,
        with_reasoning: bool = False
    ) -> List[AIInsight]:
        """Calculate content affinity scores between target and comparison contents with LLM enhancement
        
        This method uses a hybrid approach with embedding-based similarity as the primary method,
        LLM-based semantic comparison as an enhancement, and fallback mechanisms if either fails.
        """
        # Initialize reasoning tracking if requested
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Initializing content affinity calculation",
                {"target_id": target_content.id, "comparison_count": len(comparison_contents)},
                {"status": "initialized"}
            )
            
        try:
            if not target_content:
                raise ValueError("Target content cannot be None")
                
            if not comparison_contents:
                raise ValueError("Comparison contents cannot be empty")
            
            if reasoning:
                reasoning.add_step(
                    "Validated content inputs",
                    {"target_id": target_content.id, "comparison_ids": [c.id for c in comparison_contents]},
                    {"status": "validated"}
                )
                
            # Get content from database to ensure it exists
            result = await db.execute(
                select(Content)
                .options(selectinload(Content.insights))
                .where(Content.id == target_content.id)
            )
            db_content = result.scalar_one_or_none()
            
            if not db_content:
                raise ValueError(f"Content with id {target_content.id} not found")

            # Primary approach: Use embedding-based similarity
            try:
                # Extract text from all contents
                target_text = self._extract_text(target_content)
                comparison_texts = [self._extract_text(c) for c in comparison_contents]
                
                if reasoning:
                    reasoning.add_step(
                        "Extracted text from content",
                        {"target_text_length": len(target_text)},
                        {"status": "text_extracted", "sample": target_text[:100] + "..." if len(target_text) > 100 else target_text}
                    )
                
                # Generate embeddings
                with torch.no_grad():
                    target_embedding = self.model.encode([target_text])[0]
                    comparison_embeddings = self.model.encode(comparison_texts)
                
                if reasoning:
                    reasoning.add_step(
                        "Generated embeddings",
                        {"method": "sentence_transformer"},
                        {"status": "embeddings_generated", "embedding_dimensions": len(target_embedding)}
                    )
                
                # Calculate similarities
                similarities = cosine_similarity(
                    [target_embedding],
                    comparison_embeddings
                )[0]
                
                if reasoning:
                    reasoning.add_step(
                        "Calculated cosine similarities",
                        {"method": "cosine_similarity"},
                        {"status": "similarities_calculated"}
                    )
                
                # Try to enhance with LLM-based semantic insights
                try:
                    # Only use LLM for the top matches to save API usage
                    # Sort the indices by similarity scores
                    top_indices = similarities.argsort()[-3:][::-1]  # Top 3 matches
                    
                    if reasoning:
                        reasoning.add_step(
                            "Selected top matches for LLM enhancement",
                            {"top_indices": top_indices.tolist()},
                            {"status": "top_matches_selected"}
                        )
                    
                    # Enhanced scores for top matches
                    enhanced_scores = await self._generate_enhanced_scores(
                        target_content, 
                        [comparison_contents[i] for i in top_indices],
                        with_reasoning
                    )
                    
                    # Update similarities for top matches
                    for idx, enhanced_score in zip(top_indices, enhanced_scores):
                        # Blend embedding similarity and LLM-based score (60% LLM, 40% embedding)
                        similarities[idx] = 0.4 * similarities[idx] + 0.6 * enhanced_score
                    
                    if reasoning:
                        reasoning.add_step(
                            "Enhanced top match scores with LLM",
                            {"method": "llm_enhancement"},
                            {"status": "llm_enhancement_complete"}
                        )
                except Exception as e:
                    # Log error but continue with embedding-based similarities
                    logger.warning(f"LLM enhancement failed, using embedding-only similarities: {str(e)}")
                    
                    if reasoning:
                        reasoning.add_step(
                            "LLM enhancement failed",
                            {"error": str(e)},
                            {"status": "llm_failed_using_embeddings_only"}
                        )
            
            except Exception as e:
                # If embedding-based approach fails, fallback to LLM-only
                logger.warning(f"Embedding-based similarity failed, using LLM-only approach: {str(e)}")
                
                if reasoning:
                    reasoning.add_step(
                        "Embedding-based similarity failed",
                        {"error": str(e)},
                        {"status": "embeddings_failed_using_llm"}
                    )
                
                # Calculate similarities using LLM
                similarities = await self._calculate_llm_similarities(
                    target_content, 
                    comparison_contents,
                    with_reasoning
                )
            
            # Create insights with reasoning if available
            insights = []
            for i, score in enumerate(similarities):
                # Prepare metadata
                metadata = {
                    "target_content_id": target_content.id,
                    "similarity_method": "hybrid" if "llm" in locals() else "cosine",
                    "comparison_title": comparison_contents[i].title
                }
                
                # Add reasoning chain if requested
                if reasoning:
                    metadata["reasoning_chain"] = reasoning.get_reasoning_chain()
                
                # Create insight with explanation
                explanation = self._generate_affinity_explanation(
                    target_content, 
                    comparison_contents[i], 
                    float(score)
                )
                
                insight = AIInsight(
                    content_id=comparison_contents[i].id,
                    user_id=comparison_contents[i].user_id, 
                    type=InsightType.TOPIC,  # Using TOPIC type for affinity
                    score=float(score),
                    confidence=0.9 if "enhanced_scores" in locals() else 0.8,  # Higher confidence with LLM enhancement
                    explanation=explanation,
                    insight_metadata=metadata
                )
                insights.append(insight)
            
            if reasoning:
                reasoning.add_step(
                    "Created AIInsight objects",
                    {"insight_count": len(insights)},
                    {"status": "insights_created"}
                )
            
            # Save to database
            db.add_all(insights)
            await db.commit()
            
            if reasoning:
                reasoning.add_step(
                    "Saved insights to database",
                    {"insight_count": len(insights)},
                    {"status": "insights_saved"}
                )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error in content affinity calculation: {str(e)}")
            
            if reasoning:
                reasoning.add_step(
                    "Error in affinity calculation",
                    {"error": str(e)},
                    {"status": "calculation_failed"}
                )
                
            await db.rollback()
            raise e
            
    def _extract_text(self, content: Content) -> str:
        """Extract text from content based on its type"""
        if not content:
            return ""
            
        text_parts = []
        
        # Add title if present
        if content.title:
            text_parts.append(content.title)
            
        # Add content text if present
        if content.content_text:
            text_parts.append(content.content_text)
            
        # Add any additional metadata text if present
        if content.content_metadata and isinstance(content.content_metadata, dict):
            metadata_text = " ".join(str(v) for v in content.content_metadata.values())
            text_parts.append(metadata_text)
            
        return " ".join(text_parts)
        
    async def _generate_enhanced_scores(self, 
                                      target_content: Content, 
                                      comparison_contents: List[Content],
                                      with_reasoning: bool = False) -> List[float]:
        """Generate enhanced similarity scores using LLM"""
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        scores = []
        
        # Prepare target content data
        target_data = {
            "id": target_content.id,
            "title": target_content.title,
            "text": self._extract_text(target_content)[:1000]  # Limit length for API
        }
        
        if reasoning:
            reasoning.add_step(
                "Preparing LLM request for enhanced scores",
                {"target_id": target_content.id, "comparison_count": len(comparison_contents)},
                {"status": "llm_request_preparation"}
            )
        
        for content in comparison_contents:
            # Prepare comparison content data
            comparison_data = {
                "id": content.id,
                "title": content.title,
                "text": self._extract_text(content)[:1000]  # Limit length for API
            }
            
            # Construct prompt for LLM
            prompt = (
                f"Task: Evaluate the semantic similarity between two content pieces. \n\n"
                f"Content A: {target_data['title']}\n\n"
                f"Content A Text: {target_data['text'][:500]}...\n\n"
                f"Content B: {comparison_data['title']}\n\n"
                f"Content B Text: {comparison_data['text'][:500]}...\n\n"
                f"Output a similarity score between 0.0 (completely dissimilar) and 1.0 (identical) based on semantic meaning. "
                f"Format your response as a single number value between 0.0 and 1.0 to five decimal places."
            )
            
            try:
                # Call LLM service to get similarity score
                llm_response = await self.llm_service.generate_response(
                    prompt=prompt,
                    temperature=0.1,  # Low temperature for more deterministic results
                    max_tokens=20  # Only need a small response
                )
                
                # Extract score from response (expecting just a float number)
                try:
                    score = float(llm_response.strip())
                    # Ensure score is within bounds
                    score = max(0.0, min(1.0, score))
                except ValueError:
                    # If LLM didn't return a valid float, use a fallback value
                    logger.warning(f"LLM didn't return a valid score, using fallback value: {llm_response}")
                    score = 0.5  # Neutral fallback
                
                scores.append(score)
                
                if reasoning:
                    reasoning.add_step(
                        f"Generated LLM similarity score for content {content.id}",
                        {"content_id": content.id, "llm_score": score},
                        {"status": "llm_score_generated"}
                    )
                
            except Exception as e:
                logger.warning(f"Failed to get LLM similarity score: {str(e)}")
                # Use a fallback value
                scores.append(0.5)  # Neutral fallback
                
                if reasoning:
                    reasoning.add_step(
                        f"Failed to generate LLM similarity score for content {content.id}",
                        {"content_id": content.id, "error": str(e)},
                        {"status": "llm_score_failed"}
                    )
        
        return scores
    
    async def _calculate_llm_similarities(self, 
                                        target_content: Content, 
                                        comparison_contents: List[Content],
                                        with_reasoning: bool = False) -> np.ndarray:
        """Fallback method to calculate similarities using only LLM when embeddings fail"""
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Using LLM-only fallback for similarities",
                {"target_id": target_content.id, "comparison_count": len(comparison_contents)},
                {"status": "llm_only_fallback_initiated"}
            )
        
        try:
            # Use _generate_enhanced_scores as the implementation
            scores = await self._generate_enhanced_scores(
                target_content, 
                comparison_contents,
                with_reasoning
            )
            
            if reasoning:
                reasoning.add_step(
                    "Generated LLM-only similarities",
                    {"score_count": len(scores)},
                    {"status": "llm_only_similarities_generated"}
                )
            
            return np.array(scores)
            
        except Exception as e:
            # If even LLM fails, return random similarities as a last resort
            logger.error(f"LLM fallback also failed, using random similarities: {str(e)}")
            
            if reasoning:
                reasoning.add_step(
                    "LLM fallback failed, using random scores",
                    {"error": str(e)},
                    {"status": "llm_fallback_failed"}
                )
            
            # Generate random scores between 0.4 and 0.6 as a last resort
            return np.random.uniform(0.4, 0.6, len(comparison_contents))
    
    def _generate_affinity_explanation(self, target_content: Content, comparison_content: Content, score: float) -> str:
        """Generate a human-readable explanation of content affinity"""
        score_tier = "high" if score > 0.7 else "moderate" if score > 0.5 else "low"
        
        if score_tier == "high":
            return f"There is a strong content affinity between '{target_content.title}' and '{comparison_content.title}' with highly related topics and themes."
        elif score_tier == "moderate":
            return f"There is a moderate content affinity between '{target_content.title}' and '{comparison_content.title}' with some overlapping topics."
        else:
            return f"There is minimal content affinity between '{target_content.title}' and '{comparison_content.title}' with few common themes."
