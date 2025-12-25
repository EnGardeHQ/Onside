"""
Report Generator Service.

This module provides functionality for generating reports asynchronously,
with job status tracking and handling of both content and sentiment reports.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.models.report import Report, ReportStatus, ReportType
from src.models.content import Content
from src.models.user import User
from src.services.ai.llm_with_chain_of_thought import LLMWithChainOfThought
from src.services.ai.competitor_analysis import CompetitorAnalysisService
from src.services.ai.market_analysis import MarketAnalysisService
from src.services.ai.audience_analysis import AudienceAnalysisService
# These services are not implemented yet
# from src.services.ai.sentiment_analysis import SentimentAnalysisService
# from src.services.ai.temporal_analysis import TemporalAnalysisService
# from src.services.ai.seo_analysis import SEOAnalysisService
from src.services.analytics import AnalyticsService
from src.services.llm_provider import LLMProvider, FallbackManager
from src.models.llm_fallback import FallbackReason, LLMProvider as LLMProviderEnum

logger = logging.getLogger("report_generator")


class ReportGeneratorService:
    """
    Service for generating different types of reports asynchronously.
    
    Provides functionality to:
    - Create report generation jobs
    - Track report status
    - Process reports in the background
    - Handle both content and sentiment report types
    """
    
    def __init__(self, db: AsyncSession, competitor_data_service=None, market_data_service=None, 
                 audience_data_service=None, engagement_metrics_service=None, metrics_service=None, 
                 predictive_model_service=None, competitor_analysis_service=None, market_analysis_service=None, 
                 audience_analysis_service=None, llm_manager=None):
        """
        Initialize the report generator service with LLM capabilities.
        
        Args:
            db: Database session
            competitor_data_service: Service for fetching competitor data
            market_data_service: Service for fetching market data
            audience_data_service: Service for fetching audience data
            engagement_metrics_service: Service for processing engagement metrics
            metrics_service: Service for processing metrics
            predictive_model_service: Service for predictive analytics
            competitor_analysis_service: Service for competitor analysis
            market_analysis_service: Service for market analysis
            audience_analysis_service: Service for audience analysis
            llm_manager: LLM provider manager for AI capabilities
        """
        self.db = db
        
        # Initialize LLM manager with OpenAI as primary provider and Anthropic as fallback
        self.llm_manager = llm_manager or FallbackManager(
            primary_provider=LLMProvider.OPENAI,
            fallback_providers=[LLMProvider.ANTHROPIC]
        )
        
        # Initialize AI services with LLM capabilities
        self.competitor_analysis = competitor_analysis_service or CompetitorAnalysisService(
            llm_manager=self.llm_manager,
            competitor_data_service=competitor_data_service,
            metrics_service=metrics_service
        )
        
        self.market_analysis = market_analysis_service or MarketAnalysisService(
            llm_manager=self.llm_manager,
            market_data_service=market_data_service,
            predictive_model_service=predictive_model_service
        )
        
        self.audience_analysis = audience_analysis_service or AudienceAnalysisService(
            llm_manager=self.llm_manager,
            audience_data_service=audience_data_service,
            engagement_metrics_service=engagement_metrics_service
        )
        self.analytics_service = AnalyticsService()
        
        # Use provided services or initialize defaults
        self.llm_manager = llm_manager or FallbackManager()
        self.competitor_service = competitor_analysis_service
        self.market_service = market_analysis_service
        self.audience_service = audience_analysis_service
        
        # These services may not be implemented yet
        self.sentiment_service = None
        self.temporal_service = None
        self.seo_service = None
        
        self._background_tasks = set()
    
    async def create_report(
        self, 
        user_id: str, 
        report_type: ReportType, 
        parameters: Dict[str, Any],
        company_id: int = None
    ) -> Report:
        """
        Create a new report generation job.
        
        Args:
            user_id: ID of the user creating the report
            report_type: Type of report to generate
            parameters: Parameters for report generation
            
        Returns:
            Newly created report record
        """
        # Get company_id from parameters if not explicitly provided
        if company_id is None:
            company_id = parameters.get('company_id')
            if company_id is None and report_type in [ReportType.MARKET, ReportType.AUDIENCE]:
                raise ValueError(f"company_id is required for {report_type.value} reports")
        
        # Create a new report record
        report = Report(
            user_id=user_id,
            company_id=company_id,
            type=report_type,
            status=ReportStatus.QUEUED,
            parameters=parameters,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add report to database
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        
        # Start background task for report generation
        task = asyncio.create_task(self._process_report(report.id))
        
        # Add done callback to remove task when complete
        task.add_done_callback(self._background_tasks.discard)
        self._background_tasks.add(task)
        
        return report
    
    async def get_report(self, report_id: int) -> Optional[Report]:
        """
        Get a report by ID.
        
        Args:
            report_id: ID of the report to retrieve
            
        Returns:
            Report if found, None otherwise
        """
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_reports(
        self, 
        user_id: str, 
        report_type: Optional[ReportType] = None,
        status: Optional[ReportStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Report], int]:
        """
        Get reports for a specific user.
        
        Args:
            user_id: ID of the user
            report_type: Optional filter by report type
            status: Optional filter by report status
            page: Page number for pagination
            page_size: Number of items per page
            
        Returns:
            Tuple of (list of reports, total count)
        """
        query = select(Report).where(Report.user_id == user_id)
        
        # Apply filters if provided
        if report_type:
            query = query.where(Report.type == report_type)
        
        if status:
            query = query.where(Report.status == status)
        
        # Get total count
        count_result = await self.db.execute(
            select(Report).where(Report.user_id == user_id)
            .with_only_columns(Report.id)
        )
        total = len(count_result.scalars().all())
        
        # Apply pagination
        query = query.order_by(Report.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        reports = result.scalars().all()
        
        return reports, total
    
    async def _process_report(self, report_id: int) -> None:
        """
        Process a report generation job in the background.
        
        Args:
            report_id: ID of the report to process
        """
        # Update report status to PROCESSING
        await self._update_report_status(report_id, ReportStatus.PROCESSING)
        
        try:
            # Get report details
            report = await self.get_report(report_id)
            if not report:
                logger.error(f"Report {report_id} not found for processing")
                return
            
            # Process based on report type with AI/ML capabilities
            start_time = datetime.utcnow()
            
            try:
                result = await self._generate_report_by_type(report)
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update report with results and metrics
                await self._update_report_status(
                    report_id,
                    ReportStatus.COMPLETED,
                    result=result,
                    processing_time=processing_time
                )
                
            except Exception as e:
                error_msg = f"Error generating {report.type.value} report: {str(e)}"
                logger.exception(error_msg)
                await self._update_report_status(
                    report_id,
                    ReportStatus.FAILED,
                    error_message=error_msg
                )
            
            # Update report with results
            await self._update_report_status(
                report_id, 
                ReportStatus.COMPLETED, 
                result=result
            )
            
        except Exception as e:
            error_msg = f"Error processing report {report_id}: {str(e)}"
            logger.exception(error_msg)
            await self._update_report_status(
                report_id, 
                ReportStatus.FAILED, 
                error_message=error_msg
            )
    
    async def _generate_report_by_type(self, report: Report) -> Dict[str, Any]:
        """Generate a report based on its type using appropriate AI service.
        
        This method implements the Sprint 4 requirement for AI/ML-enhanced report
        generation with chain-of-thought reasoning and fallback mechanisms.
        
        Args:
            report: Report instance to generate
            
        Returns:
            Dict containing the report results
        """
        handlers = {
            ReportType.CONTENT: self._generate_content_report,
            ReportType.SENTIMENT: self._generate_sentiment_report,
            ReportType.COMPETITOR: self._generate_competitor_report,
            ReportType.MARKET: self._generate_market_report,
            ReportType.AUDIENCE: self._generate_audience_report,
            ReportType.TEMPORAL: self._generate_temporal_report,
            ReportType.SEO: self._generate_seo_report
        }
        
        if report.type not in handlers:
            raise ValueError(f"Unsupported report type: {report.type}")
            
        return await handlers[report.type](report)
    
    async def _generate_competitor_report(self, report: Report) -> Dict[str, Any]:
        """Generate a competitor intelligence report with AI analysis using OpenAI.
        
        Implements Sprint 4 requirements for enhanced competitor analysis using:
        - Chain-of-thought reasoning for competitor insights
        - Data quality and confidence scoring
        - LLM fallback support with OpenAI as primary provider
        - Structured insights for trends, opportunities, threats
        - Comprehensive error handling and logging
        
        Args:
            report: Report instance containing parameters and metadata
            
        Returns:
            Dict containing analysis results, insights, and metadata
            
        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If analysis fails critically
        """
        try:
            # Step 1: Fetch and validate competitor data
            data, data_quality = await self.competitor_analysis._fetch_competitor_data(
                competitor_ids=report.parameters["competitor_ids"],
                metrics=report.parameters["metrics"],
                timeframe=report.parameters["timeframe"]
            )
            
            # Step 2: Analyze metrics and identify trends
            analysis_results, metric_confidence = await self.competitor_analysis._analyze_metrics(
                data=data,
                metrics=report.parameters["metrics"]
            )
            
            # Step 3: Generate strategic insights using LLM with chain-of-thought
            insights, insight_confidence = await self.competitor_analysis._generate_insights(
                analysis_results=analysis_results,
                report=report
            )
            
            # Step 4: Analyze competitive positioning
            positioning, positioning_confidence = await self.competitor_analysis._analyze_positioning(
                competitor_data=data,
                analysis_results=analysis_results,
                insights=insights
            )
            
            # Calculate overall confidence score with weighted components
            confidence_score = (
                data_quality * 0.25 +            # Weight for data quality
                metric_confidence * 0.25 +       # Weight for metric analysis
                insight_confidence * 0.25 +      # Weight for LLM insights
                positioning_confidence * 0.25    # Weight for competitive positioning
            )
            
            # Get chain of thought reasoning
            chain_of_thought = self.competitor_analysis.get_reasoning_chain()
            
            # Update report with reasoning and confidence metrics
            report.chain_of_thought = chain_of_thought
            report.confidence_score = confidence_score
            report.confidence_metrics = {
                "data_quality": data_quality,
                "metric_confidence": metric_confidence,
                "insight_confidence": insight_confidence,
                "positioning_confidence": positioning_confidence
            }
            
            # Structure insights based on type
            structured_insights = {
                "trends": [],
                "opportunities": [],
                "threats": [],
                "recommendations": []
            }
            
            # Distribute insights to appropriate categories
            for insight_type, insight_list in insights.items():
                if insight_type in structured_insights:
                    structured_insights[insight_type].extend([
                        insight for insight in insight_list
                        if isinstance(insight, dict) and
                        insight.get("confidence", 0.0) >= 0.7  # Only include high-confidence insights
                    ])
            
            return {
                "analysis": {
                    "metrics": analysis_results,
                    "trends": structured_insights["trends"],
                    "opportunities": structured_insights["opportunities"],
                    "threats": structured_insights["threats"],
                    "competitive_positioning": positioning,
                    "recommendations": structured_insights["recommendations"]
                },
                "metadata": {
                    "model": "gpt-4",
                    "provider": "openai",
                    "processing_time": self.competitor_analysis.get_processing_time(),
                    "confidence_score": confidence_score,
                    "chain_of_thought": chain_of_thought,
                    "data_coverage": data.get("coverage_metrics", {})
                }
            }
            
        except ValueError as e:
            error_msg = f"Invalid parameters in competitor analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,  # Now using Anthropic as the fallback
                reason=FallbackReason.INVALID_RESPONSE,
                prompt=error_msg
            )
            raise ValueError(error_msg) from e
            
        except RuntimeError as e:
            error_msg = f"Runtime error in competitor analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,  # Now using Anthropic as the fallback
                reason=FallbackReason.ERROR,
                prompt=error_msg
            )
            raise RuntimeError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error in competitor analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,  # Now using Anthropic as the fallback
                reason=FallbackReason.ERROR,
                prompt=error_msg
            )
            # Log detailed error information for debugging
            logger.exception("Detailed error information:")
            raise RuntimeError(error_msg) from e
    
    async def _generate_market_report(self, report: Report) -> Dict[str, Any]:
        """Generate a market analysis report with predictive insights.
        
        Implements Sprint 4 requirements for enhanced market analysis using:
        - Predictive analytics with ML model integration
        - Enhanced LLM insights for market predictions
        - Sector-specific trend analysis
        - Confidence-weighted analysis
        - Chain-of-thought reasoning
        - Fallback mechanisms for robustness
        
        Args:
            report: Report instance containing parameters and metadata
            
        Returns:
            Dict containing analysis results, predictions, and metadata
            
        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If analysis fails critically
        """
        try:
            # Step 1: Validate and fetch market data
            market_data, data_quality = await self.market_analysis._fetch_market_data(
                company_id=report.parameters["company_id"],
                sectors=report.parameters["sectors"],
                timeframe=report.parameters["timeframe"]
            )
            
            # Step 2: Generate market predictions
            predictions, prediction_confidence = await self.market_analysis._generate_predictions(
                data=market_data,
                sectors=report.parameters["sectors"],
                timeframe=report.parameters["timeframe"]
            )
            
            # Step 3: Analyze sector-specific trends
            trends, trend_confidence = await self.market_analysis._analyze_sector_trends(
                market_data=market_data,
                predictions=predictions
            )
            
            # Step 4: Generate strategic insights using LLM with chain-of-thought
            insights, insight_confidence = await self.market_analysis._generate_insights(
                market_data=market_data,
                predictions=predictions,
                trends=trends,
                report=report
            )
            
            # Calculate overall confidence score with weighted components
            confidence_score = (
                data_quality * 0.25 +           # Weight for data quality
                prediction_confidence * 0.25 +   # Weight for predictive analytics
                trend_confidence * 0.25 +        # Weight for trend analysis
                insight_confidence * 0.25        # Weight for LLM insights
            )
            
            # Get chain of thought reasoning
            chain_of_thought = self.market_analysis.get_reasoning_chain()
            
            # Update report with reasoning and confidence metrics
            report.chain_of_thought = chain_of_thought
            report.confidence_score = confidence_score
            report.confidence_metrics = {
                "data_quality": data_quality,
                "prediction_confidence": prediction_confidence,
                "trend_confidence": trend_confidence,
                "insight_confidence": insight_confidence
            }
            
            return {
                "analysis": {
                    "market_predictions": predictions,
                    "sector_trends": trends,
                    "market_insights": insights.get("market", {}),
                    "sector_insights": insights.get("sectors", {}),
                    "recommendations": [
                        insight for insight in insights.get("recommendations", [])
                        if insight["confidence"] >= 0.7  # Only include high-confidence recommendations
                    ]
                },
                "metadata": {
                    "model": "gpt-4",
                    "provider": "openai",
                    "processing_time": self.market_analysis.get_processing_time(),
                    "confidence_score": confidence_score,
                    "chain_of_thought": chain_of_thought,
                    "data_coverage": market_data.get("coverage_metrics", {})
                }
            }
            
        except ValueError as e:
            error_msg = f"Invalid parameters in market analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,
                reason=FallbackReason.INVALID_RESPONSE,
                prompt=error_msg
            )
            raise ValueError(error_msg) from e
            
        except RuntimeError as e:
            error_msg = f"Runtime error in market analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,  # Now using Anthropic as the fallback
                reason=FallbackReason.ERROR,
                prompt=error_msg
            )
            raise RuntimeError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error in market analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,  # Now using Anthropic as the fallback
                reason=FallbackReason.ERROR,
                prompt=error_msg
            )
            # Log detailed error information for debugging
            logger.exception("Detailed error information:")
            raise RuntimeError(error_msg) from e
    
    async def _generate_audience_report(self, report: Report) -> Dict[str, Any]:
        """Generate an audience analysis report with AI-driven insights.
        
        Implements Sprint 4 requirements for enhanced audience analysis using:
        - Chain-of-thought reasoning
        - Confidence scoring with weighted metrics
        - Data quality validation
        - Engagement pattern analysis
        - AI-driven persona generation
        - Fallback mechanisms for robustness
        
        Args:
            report: Report instance containing parameters and metadata
            
        Returns:
            Dict containing analysis results, insights, and metadata
        
        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If analysis fails critically
        """
        try:
            # Step 1: Validate and fetch audience data
            audience_data, data_quality = await self.audience_analysis._fetch_audience_data(
                company_id=report.parameters["company_id"],
                segments=report.parameters.get("segments", []),
                timeframe=report.parameters["timeframe"],
                demographic_filters=report.parameters.get("demographic_filters", {})
            )
            
            # Step 2: Analyze engagement patterns
            engagement_analysis, engagement_confidence = await self.audience_analysis._analyze_engagement(
                data=audience_data,
                metrics=report.parameters.get("metrics", ["views", "likes", "shares", "comments"])
            )
            
            # Step 3: Generate AI-driven personas
            personas, persona_confidence = await self.audience_analysis._generate_personas(
                engagement_data=engagement_analysis,
                demographic_data=audience_data.get("demographics", {})
            )
            
            # Step 4: Generate strategic insights using LLM with chain-of-thought
            insights, insight_confidence = await self.audience_analysis._generate_insights(
                personas=personas,
                engagement_analysis=engagement_analysis,
                report=report
            )
            
            # Calculate overall confidence score with weighted components
            confidence_score = (
                data_quality * 0.25 +          # Weight for data quality
                engagement_confidence * 0.25 +  # Weight for engagement analysis
                persona_confidence * 0.25 +     # Weight for persona generation
                insight_confidence * 0.25       # Weight for LLM insights
            )
            
            # Get chain of thought reasoning
            chain_of_thought = self.audience_analysis.get_reasoning_chain()
            
            # Update report with reasoning and confidence metrics
            report.chain_of_thought = chain_of_thought
            report.confidence_score = confidence_score
            report.confidence_metrics = {
                "data_quality": data_quality,
                "engagement_confidence": engagement_confidence,
                "persona_confidence": persona_confidence,
                "insight_confidence": insight_confidence
            }
            
            return {
                "analysis": {
                    "engagement_patterns": engagement_analysis,
                    "audience_personas": personas,
                    "demographic_insights": insights.get("demographics", {}),
                    "behavioral_insights": insights.get("behavior", {}),
                    "recommendations": [
                        insight for insight in insights.get("recommendations", [])
                        if insight["confidence"] >= 0.7  # Only include high-confidence recommendations
                    ]
                },
                "metadata": {
                    "model": "gpt-4",
                    "provider": "openai",
                    "processing_time": self.audience_analysis.get_processing_time(),
                    "confidence_score": confidence_score,
                    "chain_of_thought": chain_of_thought,
                    "data_coverage": audience_data.get("coverage_metrics", {})
                }
            }
            
        except ValueError as e:
            error_msg = f"Invalid parameters in audience analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,
                reason=FallbackReason.INVALID_RESPONSE,
                prompt=error_msg
            )
            raise ValueError(error_msg) from e
            
        except RuntimeError as e:
            error_msg = f"Runtime error in audience analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,  # Now using Anthropic as the fallback
                reason=FallbackReason.ERROR,
                prompt=error_msg
            )
            raise RuntimeError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error in audience analysis: {str(e)}"
            logger.error(error_msg)
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,  # Now using Anthropic as the fallback
                reason=FallbackReason.ERROR,
                prompt=error_msg
            )
            # Log detailed error information for debugging
            logger.exception("Detailed error information:")
            raise RuntimeError(error_msg) from e
    
    async def _generate_temporal_report(self, report: Report) -> Dict[str, Any]:
        """Generate a temporal analysis report with trend detection."""
        try:
            result = await self.temporal_service.analyze(
                content_id=report.parameters["content_id"],
                interval=report.parameters["interval"],
                timeframe=report.parameters["timeframe"],
                trend_detection=report.parameters["trend_detection"],
                with_chain_of_thought=report.parameters["with_chain_of_thought"]
            )
            
            if report.parameters["with_chain_of_thought"]:
                report.record_chain_of_thought(result["reasoning"])
            
            report.update_confidence(
                score=result["confidence_score"],
                metrics=result["confidence_metrics"]
            )
            
            return result["analysis"]
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {str(e)}")
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,
                reason=FallbackReason.ERROR,
                prompt=str(e)
            )
            raise
    
    async def _generate_seo_report(self, report: Report) -> Dict[str, Any]:
        """Generate an SEO analysis report with competitor benchmarking."""
        try:
            result = await self.seo_service.analyze(
                content_id=report.parameters["content_id"],
                enhanced=report.parameters["enhanced"],
                competitors_count=report.parameters["competitors_count"],
                with_chain_of_thought=report.parameters["with_chain_of_thought"]
            )
            
            if report.parameters["with_chain_of_thought"]:
                report.record_chain_of_thought(result["reasoning"])
            
            report.update_confidence(
                score=result["confidence_score"],
                metrics=result["confidence_metrics"]
            )
            
            return result["analysis"]
            
        except Exception as e:
            logger.error(f"Error in SEO analysis: {str(e)}")
            report.track_llm_fallback(
                original_provider=LLMProviderEnum.OPENAI,
                fallback_provider=LLMProviderEnum.ANTHROPIC,
                reason=FallbackReason.ERROR,
                prompt=str(e)
            )
            raise
    
    async def _update_report_status(
        self, 
        report_id: int, 
        status: ReportStatus,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update the status of a report.
        
        Args:
            report_id: ID of the report to update
            status: New status
            result: Optional result data
            error_message: Optional error message (for failed reports)
        """
        update_values = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if result is not None:
            update_values["result"] = result
        
        if error_message is not None:
            update_values["error_message"] = error_message
        
        await self.db.execute(
            update(Report)
            .where(Report.id == report_id)
            .values(**update_values)
        )
        await self.db.commit()
    
    async def _generate_content_report(self, report: Report) -> Dict[str, Any]:
        """
        Generate a content report.
        
        Args:
            report: Report record
            
        Returns:
            Report result data
        """
        # Initialize chain of thought reasoning
        reasoning = ChainOfThoughtReasoning()
        
        # Extract parameters
        parameters = report.parameters
        start_date = parameters.get("start_date")
        end_date = parameters.get("end_date")
        content_types = parameters.get("content_types", [])
        platforms = parameters.get("platforms", [])
        
        # Log reasoning step
        reasoning.add_step(
            "Extracting report parameters",
            {
                "report_id": report.id,
                "parameters": parameters
            },
            {
                "start_date": start_date,
                "end_date": end_date,
                "content_types": content_types,
                "platforms": platforms
            }
        )
        
        # Query content data
        query = select(Content).where(Content.user_id == report.user_id)
        
        # Apply filters
        if start_date:
            query = query.where(Content.created_at >= start_date)
        
        if end_date:
            query = query.where(Content.created_at <= end_date)
        
        if content_types:
            query = query.where(Content.content_type.in_(content_types))
        
        # Execute query
        result = await self.db.execute(query)
        content_items = result.scalars().all()
        
        # Log reasoning step
        reasoning.add_step(
            "Querying content data",
            {
                "query_filters": {
                    "user_id": report.user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "content_types": content_types
                }
            },
            {
                "content_count": len(content_items),
                "content_sample": [c.id for c in content_items[:5]] if content_items else []
            }
        )
        
        # Filter by platform if needed
        if platforms:
            filtered_content = []
            for content in content_items:
                if content.content_metadata and content.content_metadata.get("platform") in platforms:
                    filtered_content.append(content)
            content_items = filtered_content
        
        # Process content items
        content_stats = self.analytics_service.process_content_stats(content_items)
        
        # Log reasoning step
        reasoning.add_step(
            "Generating content statistics",
            {
                "content_count": len(content_items)
            },
            {
                "stats_generated": True,
                "stat_categories": list(content_stats.keys())
            }
        )
        
        # Prepare report result
        report_result = {
            "content_count": len(content_items),
            "content_stats": content_stats,
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "platforms": platforms,
            "content_types": content_types,
            "reasoning_chain": reasoning.get_reasoning_chain()
        }
        
        return report_result
    
    async def _generate_sentiment_report(self, report: Report) -> Dict[str, Any]:
        """
        Generate a sentiment report.
        
        Args:
            report: Report record
            
        Returns:
            Report result data
        """
        # Initialize chain of thought reasoning
        reasoning = ChainOfThoughtReasoning()
        
        # Extract parameters
        parameters = report.parameters
        content_ids = parameters.get("content_ids", [])
        subject_ids = parameters.get("subject_ids", [])
        
        # Log reasoning step
        reasoning.add_step(
            "Extracting report parameters",
            {
                "report_id": report.id,
                "parameters": parameters
            },
            {
                "content_ids": content_ids,
                "subject_ids": subject_ids
            }
        )
        
        # Query content data
        query = select(Content).where(Content.user_id == report.user_id)
        
        # Apply filters
        if content_ids:
            query = query.where(Content.id.in_(content_ids))
        
        if subject_ids:
            query = query.where(Content.subject_id.in_(subject_ids))
        
        # Execute query
        result = await self.db.execute(query)
        content_items = result.scalars().all()
        
        # Log reasoning step
        reasoning.add_step(
            "Querying content data",
            {
                "query_filters": {
                    "user_id": report.user_id,
                    "content_ids": content_ids,
                    "subject_ids": subject_ids
                }
            },
            {
                "content_count": len(content_items),
                "content_sample": [c.id for c in content_items[:5]] if content_items else []
            }
        )
        
        # Process sentiment analysis
        sentiment_results = []
        for content in content_items:
            sentiment = await self.sentiment_service.analyze_content_sentiment(
                content, with_reasoning=True
            )
            sentiment_results.append({
                "content_id": content.id,
                "title": content.title,
                "sentiment": sentiment
            })
        
        # Log reasoning step
        reasoning.add_step(
            "Analyzing sentiment for content",
            {
                "content_count": len(content_items)
            },
            {
                "sentiment_results_count": len(sentiment_results)
            }
        )
        
        # Prepare report result
        report_result = {
            "content_count": len(content_items),
            "sentiment_results": sentiment_results,
            "overall_sentiment": self._calculate_overall_sentiment(sentiment_results),
            "reasoning_chain": reasoning.get_reasoning_chain()
        }
        
        return report_result
    
    def _calculate_overall_sentiment(self, sentiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall sentiment from individual content sentiments.
        
        Args:
            sentiment_results: List of sentiment results
            
        Returns:
            Overall sentiment statistics
        """
        if not sentiment_results:
            return {
                "average_score": 0,
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                }
            }
        
        # Calculate average sentiment score
        total_score = sum(r["sentiment"].get("score", 0) for r in sentiment_results)
        average_score = total_score / len(sentiment_results)
        
        # Calculate sentiment distribution
        positive_count = sum(1 for r in sentiment_results if r["sentiment"].get("score", 0) > 0.5)
        negative_count = sum(1 for r in sentiment_results if r["sentiment"].get("score", 0) < -0.5)
        neutral_count = len(sentiment_results) - positive_count - negative_count
        
        return {
            "average_score": average_score,
            "sentiment_distribution": {
                "positive": positive_count,
                "neutral": neutral_count,
                "negative": negative_count
            }
        }
