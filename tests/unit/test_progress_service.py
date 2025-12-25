"""
BDD Tests for Progress Tracking Service (S5-04)

This module implements BDD-style tests for the real-time progress tracking service,
following Semantic Seed Venture Studio Coding Standards V2.0.

The tests connect to the actual PostgreSQL database as required:
- Host: localhost
- Port: 5432
- Database: onside
- User: tobymorning

Tests follow Red-Green-Refactor TDD methodology and verify integration with:
1. WebSocket functionality
2. AI/ML services from Sprint 4
3. Real-time progress updates
4. Error handling and recovery
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import WebSocket
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.progress import (
    ProgressTracker,
    ProgressStatus,
    ProgressStage
)
from src.services.progress.progress_service import (
    ProgressService,
    ProgressManager
)
from src.services.competitor_analysis import CompetitorAnalysisService
from src.services.market_analysis import MarketAnalysisService
from src.services.audience_analysis import AudienceAnalysisService

class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.closed = False
    
    async def accept(self):
        pass
    
    async def send_text(self, message: str):
        self.sent_messages.append(message)
    
    async def receive_text(self):
        return '{"command": "test"}'
    
    async def close(self):
        self.closed = True


class TestProgressTracking:
    """
    Feature: Real-Time Progress Tracking
    As a user generating a competitive analysis report
    I want to track the progress in real-time
    So I can monitor the report generation status
    """
    
    @pytest.fixture
    def progress_manager(self):
        """Create a progress manager for testing."""
        return ProgressManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        return MockWebSocket()
    
    @pytest_asyncio.fixture
    async def progress_service(self, test_db: AsyncSession, progress_manager):
        """Create a progress service for testing."""
        return ProgressService(test_db, progress_manager)
    
    @pytest.mark.asyncio
    async def test_create_progress_tracker(self, progress_service):
        """
        Scenario: Creating a new progress tracker
        Given a report ID and user ID
        When I create a new progress tracker
        Then it should be initialized with default values
        """
        # Given
        report_id = 1
        user_id = 1
        
        # When
        tracker = await progress_service.create_tracker(report_id, user_id)
        
        # Then
        assert tracker is not None
        assert tracker.report_id == report_id
        assert tracker.user_id == user_id
        assert tracker.status == ProgressStatus.QUEUED
        assert tracker.progress_percent == 0.0
        assert tracker.created_at is not None
    
    @pytest.mark.asyncio
    async def test_update_stage_progress(self, progress_service):
        """
        Scenario: Updating progress for a stage
        Given an active progress tracker
        When I update the progress of a stage
        Then the overall progress should be recalculated
        """
        # Given
        tracker = await progress_service.create_tracker(1, 1)
        
        # When - update data collection stage
        await progress_service.update_progress(
            report_id=1,
            stage=ProgressStage.DATA_COLLECTION,
            progress=0.5
        )
        
        # Then
        updated_tracker = await progress_service._get_tracker(1)
        assert updated_tracker.stage_progress[ProgressStage.DATA_COLLECTION] == 0.5
        # Overall progress should be weighted
        expected_progress = 0.5 * updated_tracker.stage_weights[ProgressStage.DATA_COLLECTION]
        assert abs(updated_tracker.progress_percent - expected_progress) < 0.01
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, progress_service, mock_websocket):
        """
        Scenario: WebSocket connection management
        Given a WebSocket connection request
        When I connect to the progress service
        Then I should receive initial progress state
        """
        # Given
        report_id = 1
        user_id = 1
        tracker = await progress_service.create_tracker(report_id, user_id)
        
        # When
        with patch('fastapi.WebSocket', return_value=mock_websocket):
            await progress_service.handle_websocket(mock_websocket, report_id, user_id)
        
        # Then
        assert len(mock_websocket.sent_messages) >= 1
        # First message should be initial state
        import json
        initial_state = json.loads(mock_websocket.sent_messages[0])
        assert initial_state["report_id"] == report_id
        assert initial_state["status"] == ProgressStatus.QUEUED
    
    @pytest.mark.asyncio
    async def test_error_handling(self, progress_service):
        """
        Scenario: Error handling during report generation
        Given an active progress tracker
        When an error occurs during processing
        Then the error should be recorded and status updated
        """
        # Given
        tracker = await progress_service.create_tracker(1, 1)
        error_info = {
            "message": "Test error",
            "type": "TestError"
        }
        
        # When
        await progress_service.update_progress(
            report_id=1,
            stage=ProgressStage.DATA_COLLECTION,
            progress=0.3,
            error=error_info
        )
        
        # Then
        updated_tracker = await progress_service._get_tracker(1)
        assert updated_tracker.status == ProgressStatus.FAILED
        assert updated_tracker.error_message == "Test error"
        assert updated_tracker.error_details == error_info
    
    @pytest.mark.asyncio
    async def test_progress_estimation(self, progress_service):
        """
        Scenario: Progress time estimation
        Given a running progress tracker
        When progress is updated multiple times
        Then completion time should be estimated
        """
        # Given
        tracker = await progress_service.create_tracker(1, 1)
        
        # When - simulate progress updates
        stages = [
            (ProgressStage.DATA_COLLECTION, 0.5),
            (ProgressStage.COMPETITOR_ANALYSIS, 0.3),
            (ProgressStage.MARKET_ANALYSIS, 0.2)
        ]
        
        for stage, progress in stages:
            await asyncio.sleep(0.1)  # Simulate time passing
            await progress_service.update_progress(1, stage, progress)
        
        # Then
        updated_tracker = await progress_service._get_tracker(1)
        assert updated_tracker.estimated_completion_time is not None
        # Estimated time should be in the future
        assert updated_tracker.estimated_completion_time > datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_integration_with_ai_services(
        self,
        progress_service,
        test_db: AsyncSession
    ):
        """
        Scenario: Integration with AI/ML services
        Given AI services from Sprint 4
        When generating a report
        Then progress should be tracked for each service
        """
        # Given - mock AI services
        competitor_service = AsyncMock(spec=CompetitorAnalysisService)
        market_service = AsyncMock(spec=MarketAnalysisService)
        audience_service = AsyncMock(spec=AudienceAnalysisService)
        
        # Configure mocks to return test data
        competitor_service.collect_data_with_reasoning.return_value = {"test": "data"}
        competitor_service.analyze_with_confidence.return_value = {"insights": "test"}
        market_service.analyze_with_predictions.return_value = {"market": "test"}
        audience_service.generate_personas.return_value = {"personas": "test"}
        
        # When - start report generation
        from src.routes.progress import generate_report_with_progress
        await generate_report_with_progress(
            report_id=1,
            progress_service=progress_service,
            competitor_service=competitor_service,
            market_service=market_service,
            audience_service=audience_service,
            session=test_db
        )
        
        # Then
        tracker = await progress_service._get_tracker(1)
        assert tracker.status == ProgressStatus.COMPLETED
        assert tracker.progress_percent == 1.0
        assert all(
            tracker.stage_progress.get(stage, 0.0) == 1.0
            for stage in ProgressStage
        )
    
    @pytest.mark.asyncio
    async def test_cancellation(self, progress_service):
        """
        Scenario: Report generation cancellation
        Given an active report generation
        When I cancel the report
        Then the progress should be marked as cancelled
        """
        # Given
        tracker = await progress_service.create_tracker(1, 1)
        await progress_service.update_progress(
            1,
            ProgressStage.DATA_COLLECTION,
            0.3
        )
        
        # When
        await progress_service.cancel_report(1)
        
        # Then
        updated_tracker = await progress_service._get_tracker(1)
        assert updated_tracker.status == ProgressStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_database_integration(
        self,
        progress_service,
        test_db: AsyncSession
    ):
        """
        Scenario: Database integration verification
        Given a connection to the actual PostgreSQL database
        When I perform progress tracking operations
        Then changes should persist in the database
        """
        # Given - verify database connection
        result = await test_db.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        assert db_name is not None
        
        # When - create and update tracker
        tracker = await progress_service.create_tracker(1, 1)
        await progress_service.update_progress(
            1,
            ProgressStage.DATA_COLLECTION,
            0.5
        )
        
        # Then - verify in database
        await test_db.refresh(tracker)
        assert tracker.progress_percent > 0
        assert ProgressStage.DATA_COLLECTION in tracker.stage_progress
        
        # Clean up
        await test_db.delete(tracker)
        await test_db.commit()


if __name__ == "__main__":
    pytest.main(["-v", "test_progress_service.py"])
