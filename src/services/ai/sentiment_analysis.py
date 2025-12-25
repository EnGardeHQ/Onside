"""Sentiment analysis service module with LLM-based analysis and fallback mechanisms"""
from typing import List, Optional, Dict, Union, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.database.config import get_db
from src.models.content import Content
from src.models.ai import AIInsight, InsightType
from textblob import TextBlob
from fastapi import HTTPException
import json
import logging

from src.services.ai.llm_service import LLMService, LLMProvider
from src.services.ai.chain_of_thought import ChainOfThoughtReasoning

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    """Service for analyzing sentiment in content with LLM integration and fallback mechanisms"""
    
    def __init__(self):
        """Initialize the sentiment analysis service with LLM client"""
        self.llm_service = LLMService()

    async def analyze_content(self, content_id: int, db: AsyncSession, with_reasoning: bool = False) -> Optional[AIInsight]:
        """Analyze sentiment for a specific content item with LLM fallback"""
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Initializing sentiment analysis",
                {"content_id": content_id},
                {"status": "initialized"}
            )
            
        # Get content from database
        result = await db.execute(
            select(Content)
            .options(selectinload(Content.insights))
            .where(Content.id == content_id)
        )
        content = result.scalar_one_or_none()
        
        if not content:
            if reasoning:
                reasoning.add_step(
                    "Content retrieval failed",
                    {"content_id": content_id},
                    {"status": "content_not_found"}
                )
            return None
        
        if reasoning:
            reasoning.add_step(
                "Content retrieved successfully",
                {"content_id": content_id},
                {
                    "status": "content_found",
                    "title": content.title,
                    "text_length": len(content.content_text) if content.content_text else 0
                }
            )
        
        try:
            # Try advanced LLM-based sentiment analysis
            sentiment_data = await self._analyze_with_llm(content, with_reasoning)
            sentiment_score = sentiment_data.get("score", 0.0)
            confidence = sentiment_data.get("confidence", 0.0)
            explanation = sentiment_data.get("explanation", "")
            
            if reasoning:
                reasoning.add_step(
                    "LLM-based sentiment analysis successful",
                    {"content_id": content_id},
                    {
                        "status": "llm_success",
                        "score": sentiment_score,
                        "confidence": confidence
                    }
                )
        except Exception as e:
            # Fallback to TextBlob if LLM analysis fails
            logger.warning(f"LLM sentiment analysis failed, falling back to TextBlob: {str(e)}")
            
            if reasoning:
                reasoning.add_step(
                    "LLM-based sentiment analysis failed, falling back to TextBlob",
                    {"content_id": content_id, "error": str(e)},
                    {"status": "llm_failed_fallback_textblob"}
                )
            
            text = f"{content.title} {content.content_text}" if content.content_text else content.title
            blob = TextBlob(text)
            sentiment = blob.sentiment
            sentiment_score = sentiment.polarity
            confidence = abs(sentiment.polarity)
            explanation = "Content appears to have a positive tone" if sentiment_score > 0 else "Content appears to have a negative tone"
            
            if reasoning:
                reasoning.add_step(
                    "TextBlob sentiment analysis completed",
                    {"content_id": content_id},
                    {
                        "status": "textblob_success",
                        "score": sentiment_score,
                        "confidence": confidence
                    }
                )
        
        # Create or update sentiment insight
        insight = AIInsight(
            content_id=content_id,
            type=InsightType.SENTIMENT,
            score=sentiment_score,
            confidence=confidence,
            explanation=explanation,
            metadata={"reasoning_chain": reasoning.get_reasoning_chain() if reasoning else None}
        )
        
        db.add(insight)
        await db.commit()
        await db.refresh(insight)
        
        return insight
        
    async def _analyze_with_llm(self, content: Content, with_reasoning: bool = False) -> Dict[str, Any]:
        """Analyze content sentiment using an LLM with fallback mechanisms"""
        # Prepare the content for analysis
        title = content.title or ""
        text = content.content_text or ""
        
        # Truncate text if it's too long
        max_text_length = 4000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."
        
        # Prepare the prompt for the LLM
        messages = [
            {"role": "system", "content": "You are a sentiment analysis expert. Analyze the sentiment of the provided content and respond with a JSON structure containing 'score' (float between -1 and 1), 'confidence' (float between 0 and 1), and 'explanation' (string describing the sentiment). Score of -1 is extremely negative, 0 is neutral, and 1 is extremely positive."},
            {"role": "user", "content": f"Title: {title}\n\nContent: {text}\n\nAnalyze the sentiment of this content and provide the results in the specified JSON format."}
        ]
        
        try:
            # Call the LLM service with fallback capabilities
            response = await self.llm_service.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more deterministic results
                with_reasoning=with_reasoning
            )
            
            # Parse the JSON response
            content = response.get("content", "")
            # Extract the JSON portion if it's embedded in text
            json_start = content.find("{")
            json_end = content.rfind("}")
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end+1]
                try:
                    result = json.loads(json_str)
                    # Ensure the required fields are present
                    if not all(k in result for k in ["score", "confidence", "explanation"]):
                        raise ValueError("Missing required fields in LLM response")
                    return result
                except json.JSONDecodeError:
                    raise ValueError("Failed to parse LLM response as JSON")
            else:
                raise ValueError("No JSON found in LLM response")
                
        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {str(e)}")
            raise
        
    async def get_content_sentiment(self, content_id: int, db: AsyncSession) -> Optional[AIInsight]:
        """Get existing sentiment analysis for content"""
        result = await db.execute(
            select(AIInsight)
            .where(
                AIInsight.content_id == content_id,
                AIInsight.type == InsightType.SENTIMENT
            )
        )
        return result.scalar_one_or_none()
        
    async def batch_analyze_content(self, content_ids: List[int], db: AsyncSession) -> List[AIInsight]:
        """Analyze sentiment for multiple content items"""
        insights = []
        for content_id in content_ids:
            insight = await self.analyze_content(content_id, db)
            if insight:
                insights.append(insight)
        return insights

    async def analyze_content_sentiment(
        self,
        content: Union[Content, int],
        context: Optional[Dict] = None,
        session: Optional[AsyncSession] = None,
        with_reasoning: bool = False
    ) -> Dict:
        """Analyze sentiment for a single content item with LLM and fallback"""
        reasoning = ChainOfThoughtReasoning() if with_reasoning else None
        
        if reasoning:
            reasoning.add_step(
                "Starting content sentiment analysis",
                {"content": content.id if isinstance(content, Content) else content},
                {"status": "initialized"}
            )
        
        # Handle content as ID or Content object
        content_id = content.id if isinstance(content, Content) else content
        content_obj = content if isinstance(content, Content) else None
        
        if not content_id:
            raise ValueError("Invalid content ID")

        if not content_obj and not session:
            raise ValueError("Database session is required when content object is not provided")

        # Fetch content if needed
        if not content_obj:
            if reasoning:
                reasoning.add_step(
                    "Fetching content from database",
                    {"content_id": content_id},
                    {"status": "fetching"}
                )
                
            stmt = select(Content).where(Content.id == content_id)
            result = await session.execute(stmt)
            content_obj = result.scalar_one_or_none()

            if not content_obj:
                if reasoning:
                    reasoning.add_step(
                        "Content not found",
                        {"content_id": content_id},
                        {"status": "error_not_found"}
                    )
                raise ValueError("Content not found")
        
        if reasoning:
            reasoning.add_step(
                "Content retrieved successfully",
                {"content_id": content_id},
                {
                    "status": "content_ready",
                    "content_length": len(content_obj.content_text) if content_obj.content_text else 0
                }
            )
        
        # Analyze sentiment with LLM and fallback
        try:
            sentiment_data = await self.get_content_sentiment_text(
                content_obj.content_text,
                with_reasoning=with_reasoning
            )
            
            if reasoning:
                reasoning.add_step(
                    "Sentiment analysis completed",
                    {"method": sentiment_data.get("method", "llm")},
                    {
                        "status": "completed",
                        "score": sentiment_data.get("score", 0),
                        "confidence": sentiment_data.get("confidence", 0)
                    }
                )
            
            if context and "score" in sentiment_data:
                adjusted_score = self._adjust_sentiment_with_context(sentiment_data["score"], context)
                sentiment_data["score"] = adjusted_score
                sentiment_data["context_adjusted"] = True
                
                if reasoning:
                    reasoning.add_step(
                        "Applied context adjustments",
                        {"context": context},
                        {
                            "status": "context_applied",
                            "original_score": sentiment_data.get("score", 0),
                            "adjusted_score": adjusted_score
                        }
                    )
            
            # Add content ID and reasoning chain to response
            result = {
                "content_id": content_id,
                "sentiment": sentiment_data
            }
            
            if reasoning:
                result["reasoning_chain"] = reasoning.get_reasoning_chain()
                
            return result
                
        except Exception as e:
            if reasoning:
                reasoning.add_step(
                    "Sentiment analysis failed",
                    {"error": str(e)},
                    {"status": "error"}
                )
                
            logger.error(f"Failed to analyze sentiment: {str(e)}")
            raise ValueError(f"Sentiment analysis failed: {str(e)}")

    async def analyze_batch_sentiment(
        self,
        content_ids: List[int],
        session: AsyncSession,
        with_reasoning: bool = False
    ) -> List[Dict]:
        """Analyze sentiment for multiple content items"""
        results = []
        for content_id in content_ids:
            try:
                sentiment = await self.analyze_content_sentiment(
                    content_id, 
                    session=session,
                    with_reasoning=with_reasoning
                )
                results.append(sentiment)
            except ValueError as e:
                results.append({
                    "content_id": content_id,
                    "error": str(e)
                })
        return results

    async def get_content_sentiment_text(self, text: str, with_reasoning: bool = False) -> Dict[str, Any]:
        """Get sentiment score for text content using LLM with fallback"""
        try:
            # Truncate text if needed
            max_text_length = 4000
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": "You are a sentiment analysis expert. Analyze the sentiment of the provided text and respond with a JSON structure containing 'score' (float between -1 and 1), 'confidence' (float between 0 and 1), and 'explanation' (string describing the sentiment)."},
                {"role": "user", "content": f"Content: {text}\n\nAnalyze the sentiment of this text and provide the results in the specified JSON format."}
            ]
            
            # Call LLM with fallback
            response = await self.llm_service.chat_completion(
                messages=messages,
                temperature=0.3,
                with_reasoning=with_reasoning
            )
            
            # Parse response
            content = response.get("content", "")
            json_start = content.find("{")
            json_end = content.rfind("}")
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end+1]
                result = json.loads(json_str)
                
                # Add reasoning chain if available
                if with_reasoning and "reasoning_chain" in response:
                    result["reasoning_chain"] = response["reasoning_chain"]
                    
                return result
            else:
                raise ValueError("No JSON found in LLM response")
                
        except Exception as e:
            logger.warning(f"LLM sentiment analysis failed, falling back to TextBlob: {str(e)}")
            
            # Fallback to TextBlob
            blob = TextBlob(text)
            sentiment = blob.sentiment
            
            return {
                "score": sentiment.polarity,
                "confidence": abs(sentiment.polarity),
                "explanation": "Content appears to have a positive tone" if sentiment.polarity > 0 else "Content appears to have a negative tone",
                "method": "textblob_fallback"
            }

    def _adjust_sentiment_with_context(
        self,
        sentiment_score: float,
        context: Dict
    ) -> float:
        """Adjust sentiment score based on context"""
        # Apply industry-specific adjustments
        if context.get("industry") == "tech":
            sentiment_score *= 1.1
        
        # Apply audience-specific adjustments
        if context.get("audience") == "developers":
            sentiment_score *= 0.9

        # Ensure score stays between -1 and 1
        return max(min(sentiment_score, 1.0), -1.0)
