"""Progress Tracking Service Tests (S5-04)

BDD-style tests for the progress tracking service following
Semantic Seed Venture Studio Coding Standards V2.0.

Features tested:
1. Progress tracker creation and management
2. WebSocket connection handling
3. Real-time progress updates
4. Integration with AI/ML services from Sprint 4
5. Error handling and recovery

Database: Uses actual PostgreSQL database (not mocks)
- Host: localhost:5432
- Database: onside
- User: tobymorning
"""
import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.progress import ProgressTracker, ProgressStatus, ProgressStage
from src.services.progress.progress_service import ProgressService
from src.services.ai import (
    CompetitorAnalysisService,
    MarketAnalysisService,
    AudienceAnalysisService
)

# Test Data
TEST_REPORT_ID = 1
TEST_USER_ID = 1

@pytest.fixture
async def progress_service(db_session: AsyncSession) -> ProgressService:
    """Create a progress service instance for testing.
    
    Args:
        db_session: Database session
        
    Returns:
        Configured progress service
    """
    return ProgressService(
        db_session=db_session,
        competitor_service=CompetitorAnalysisService(),
        market_service=MarketAnalysisService(),
        audience_service=AudienceAnalysisService()
    )

@pytest.fixture
async def websocket_manager(progress_service: ProgressService) -> AsyncGenerator:
    """Create a WebSocket manager for testing.
    
    Args:
        progress_service: Progress service instance
        
    Yields:
        WebSocket manager instance
    """
    manager = progress_service.websocket_manager
    yield manager
    # Cleanup connections
    for connection in manager.active_connections:
        await manager.disconnect(connection)

async def test_create_progress_tracker(
    progress_service: ProgressService,
    db_session: AsyncSession
):
    """Test creating a new progress tracker.
    
    Given a report generation request
    When creating a new progress tracker
    Then the tracker should be initialized with correct status
    """
    # When
    tracker = await progress_service.create_tracker(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # Then
    assert tracker.report_id == TEST_REPORT_ID
    assert tracker.user_id == TEST_USER_ID
    assert tracker.status == ProgressStatus.QUEUED
    assert tracker.progress_percent == 0.0
    
    # Verify in database
    result = await db_session.execute(
        select(ProgressTracker).where(
            ProgressTracker.report_id == TEST_REPORT_ID
        )
    )
    db_tracker = result.scalar_one()
    assert db_tracker.id == tracker.id

async def test_update_progress(
    progress_service: ProgressService,
    db_session: AsyncSession
):
    """Test updating progress for a stage.
    
    Given an active progress tracker
    When updating progress for a stage
    Then the overall progress should be calculated correctly
    """
    # Given
    tracker = await progress_service.create_tracker(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # When
    await progress_service.update_progress(
        report_id=TEST_REPORT_ID,
        stage=ProgressStage.DATA_COLLECTION,
        progress=0.5
    )
    
    # Then
    result = await db_session.execute(
        select(ProgressTracker).where(
            ProgressTracker.report_id == TEST_REPORT_ID
        )
    )
    tracker = result.scalar_one()
    assert tracker.current_stage == ProgressStage.DATA_COLLECTION
    assert tracker.status == ProgressStatus.IN_PROGRESS
    # Progress should be weighted (0.5 * 0.15 for DATA_COLLECTION)
    assert pytest.approx(tracker.progress_percent, 0.01) == 0.075

async def test_websocket_connection(
    progress_service: ProgressService,
    websocket_manager,
    db_session: AsyncSession
):
    """Test WebSocket connection management.
    
    Given a WebSocket connection request
    When connecting to the progress service
    Then updates should be broadcast to connected clients
    """
    # Given
    tracker = await progress_service.create_tracker(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # Mock WebSocket
    class MockWebSocket:
        async def send_json(self, data: Dict):
            self.last_message = data
            
        async def receive_json(self):
            return {"type": "ping"}
    
    socket = MockWebSocket()
    
    # When
    await websocket_manager.connect(socket, TEST_REPORT_ID)
    await progress_service.update_progress(
        report_id=TEST_REPORT_ID,
        stage=ProgressStage.COMPETITOR_ANALYSIS,
        progress=0.75
    )
    
    # Then
    assert hasattr(socket, 'last_message')
    message = socket.last_message
    assert message["report_id"] == TEST_REPORT_ID
    assert message["stage"] == ProgressStage.COMPETITOR_ANALYSIS.value
    # Progress should be weighted (0.75 * 0.25 for COMPETITOR_ANALYSIS)
    assert pytest.approx(message["progress"], 0.01) == 0.1875

async def test_error_handling(
    progress_service: ProgressService,
    db_session: AsyncSession
):
    """Test error handling during progress tracking.
    
    Given a progress tracker
    When an error occurs during processing
    Then it should be properly recorded and handled
    """
    # Given
    tracker = await progress_service.create_tracker(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # When - Simulate error in competitor analysis
    error_msg = "API rate limit exceeded"
    await progress_service.record_error(
        report_id=TEST_REPORT_ID,
        error_message=error_msg,
        error_details={"stage": "competitor_analysis", "retry_count": 1}
    )
    
    # Then
    result = await db_session.execute(
        select(ProgressTracker).where(
            ProgressTracker.report_id == TEST_REPORT_ID
        )
    )
    tracker = result.scalar_one()
    assert tracker.status == ProgressStatus.FAILED
    assert tracker.error_message == error_msg
    assert tracker.error_details["stage"] == "competitor_analysis"

async def test_integration_with_ai_services(
    progress_service: ProgressService,
    db_session: AsyncSession
):
    """Test integration with AI services from Sprint 4.
    
    Given a progress tracker
    When running analysis with AI services
    Then progress should be tracked for each service
    """
    # Given
    tracker = await progress_service.create_tracker(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # When - Simulate AI service processing
    stages = [
        (ProgressStage.COMPETITOR_ANALYSIS, 1.0),
        (ProgressStage.MARKET_ANALYSIS, 1.0),
        (ProgressStage.AUDIENCE_ANALYSIS, 1.0)
    ]
    
    for stage, progress in stages:
        await progress_service.update_progress(
            report_id=TEST_REPORT_ID,
            stage=stage,
            progress=progress
        )
    
    # Then
    result = await db_session.execute(
        select(ProgressTracker).where(
            ProgressTracker.report_id == TEST_REPORT_ID
        )
    )
    tracker = result.scalar_one()
    # Total progress should be sum of weighted stages
    # (0.25 + 0.20 + 0.20 = 0.65 for these stages)
    assert pytest.approx(tracker.progress_percent, 0.01) == 0.65
    assert tracker.status == ProgressStatus.IN_PROGRESS

async def test_timeout_handling(
    progress_service: ProgressService,
    db_session: AsyncSession
):
    """Test handling of stage timeouts.
    
    Given a progress tracker
    When a stage exceeds its timeout
    Then it should be properly handled
    """
    # Given
    tracker = await progress_service.create_tracker(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # When - Simulate timeout in market analysis
    await progress_service.start_stage(
        report_id=TEST_REPORT_ID,
        stage=ProgressStage.MARKET_ANALYSIS
    )
    
    # Simulate time passage
    tracker.started_at = datetime.now() - timedelta(minutes=15)  # Exceeds 10 minute timeout
    await db_session.commit()
    
    # Then
    await progress_service.check_timeout(TEST_REPORT_ID)
    result = await db_session.execute(
        select(ProgressTracker).where(
            ProgressTracker.report_id == TEST_REPORT_ID
        )
    )
    tracker = result.scalar_one()
    assert tracker.status == ProgressStatus.FAILED
    assert "timeout" in tracker.error_message.lower()

async def test_cancellation(
    progress_service: ProgressService,
    db_session: AsyncSession
):
    """Test report generation cancellation.
    
    Given an active progress tracker
    When cancelling the report generation
    Then it should be properly stopped
    """
    # Given
    tracker = await progress_service.create_tracker(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # When
    await progress_service.cancel_report(
        report_id=TEST_REPORT_ID,
        user_id=TEST_USER_ID
    )
    
    # Then
    result = await db_session.execute(
        select(ProgressTracker).where(
            ProgressTracker.report_id == TEST_REPORT_ID
        )
    )
    tracker = result.scalar_one()
    assert tracker.status == ProgressStatus.CANCELLED
    assert tracker.completed_at is not None
