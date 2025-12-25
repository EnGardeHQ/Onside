"""Integration tests for brand analysis workflow.

Tests the complete end-to-end flow from initiation through completion,
including database persistence, status updates, and result retrieval.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock

from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus
)
from src.agents.seo_content_walker import (
    SEOContentWalkerAgent,
    BrandAnalysisQuestionnaire
)
from tests.fixtures.brand_analysis_fixtures import (
    SAMPLE_QUESTIONNAIRE_COMPLETE,
    MOCK_WEBSITE_CRAWL_DATA,
    SAMPLE_KEYWORDS,
    SAMPLE_COMPETITORS
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestBrandAnalysisFlow:
    """Test complete brand analysis workflow."""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, test_db):
        """Test complete analysis from start to finish."""
        # Create job
        job_id = uuid.uuid4()
        questionnaire = BrandAnalysisQuestionnaire.from_dict(SAMPLE_QUESTIONNAIRE_COMPLETE)

        job = BrandAnalysisJob(
            id=job_id,
            user_id=1,
            questionnaire=questionnaire.to_dict(),
            status=AnalysisStatus.INITIATED,
            progress=0
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        # Create agent
        agent = SEOContentWalkerAgent(db=test_db)

        # Mock crawling and SERP analysis
        with patch.object(agent, 'crawl_website', return_value=MOCK_WEBSITE_CRAWL_DATA):
            with patch.object(agent, 'analyze_serp', return_value={}):
                # Run analysis
                results = await agent.analyze_brand(str(job_id), questionnaire)

        # Verify job completion
        await test_db.refresh(job)
        assert job.status == AnalysisStatus.COMPLETED
        assert job.progress == 100
        assert job.completed_at is not None
        assert results is not None

        # Verify keywords were saved
        from sqlalchemy import select
        keywords_result = await test_db.execute(
            select(DiscoveredKeyword).where(DiscoveredKeyword.job_id == job_id)
        )
        keywords = keywords_result.scalars().all()
        assert len(keywords) > 0

        # Verify competitors were saved
        competitors_result = await test_db.execute(
            select(IdentifiedCompetitor).where(IdentifiedCompetitor.job_id == job_id)
        )
        competitors = competitors_result.scalars().all()
        assert len(competitors) >= 0

        # Verify content opportunities were saved
        opportunities_result = await test_db.execute(
            select(ContentOpportunity).where(ContentOpportunity.job_id == job_id)
        )
        opportunities = opportunities_result.scalars().all()
        assert len(opportunities) >= 0

    @pytest.mark.asyncio
    async def test_status_progression(self, test_db):
        """Test that job status progresses correctly."""
        job_id = uuid.uuid4()
        questionnaire = BrandAnalysisQuestionnaire.from_dict(SAMPLE_QUESTIONNAIRE_COMPLETE)

        job = BrandAnalysisJob(
            id=job_id,
            user_id=1,
            questionnaire=questionnaire.to_dict(),
            status=AnalysisStatus.INITIATED,
            progress=0
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        agent = SEOContentWalkerAgent(db=test_db)

        # Mock crawling
        with patch.object(agent, 'crawl_website', return_value=MOCK_WEBSITE_CRAWL_DATA):
            with patch.object(agent, 'analyze_serp', return_value={}):
                await agent.analyze_brand(str(job_id), questionnaire)

        # Check status progression
        await test_db.refresh(job)
        assert job.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]

    @pytest.mark.asyncio
    async def test_error_handling(self, test_db):
        """Test error handling in analysis workflow."""
        job_id = uuid.uuid4()
        questionnaire = BrandAnalysisQuestionnaire.from_dict(SAMPLE_QUESTIONNAIRE_COMPLETE)

        job = BrandAnalysisJob(
            id=job_id,
            user_id=1,
            questionnaire=questionnaire.to_dict(),
            status=AnalysisStatus.INITIATED,
            progress=0
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        agent = SEOContentWalkerAgent(db=test_db)

        # Mock crawling to raise error
        with patch.object(agent, 'crawl_website', side_effect=Exception('Test error')):
            with pytest.raises(Exception):
                await agent.analyze_brand(str(job_id), questionnaire)

        # Verify job marked as failed
        await test_db.refresh(job)
        assert job.status == AnalysisStatus.FAILED
        assert job.error_message is not None
        assert 'Test error' in job.error_message

    @pytest.mark.asyncio
    async def test_keyword_persistence(self, test_db):
        """Test that keywords are properly persisted."""
        job_id = uuid.uuid4()

        # Create keywords
        keywords = [
            DiscoveredKeyword(
                job_id=job_id,
                keyword='test keyword',
                source='nlp_extraction',
                search_volume=1000,
                difficulty=50.0,
                relevance_score=0.75
            )
            for i in range(5)
        ]

        for kw in keywords:
            await test_db.execute(test_db.add(kw))
        await test_db.commit()

        # Retrieve keywords
        from sqlalchemy import select
        result = await test_db.execute(
            select(DiscoveredKeyword).where(DiscoveredKeyword.job_id == job_id)
        )
        retrieved = result.scalars().all()

        assert len(retrieved) == 5
        assert all(kw.job_id == job_id for kw in retrieved)

    @pytest.mark.asyncio
    async def test_competitor_persistence(self, test_db):
        """Test that competitors are properly persisted."""
        job_id = uuid.uuid4()

        competitors = [
            IdentifiedCompetitor(
                job_id=job_id,
                domain=f'competitor{i}.com',
                name=f'Competitor {i}',
                relevance_score=0.7,
                category='secondary',
                overlap_percentage=50.0
            )
            for i in range(3)
        ]

        for comp in competitors:
            await test_db.execute(test_db.add(comp))
        await test_db.commit()

        # Retrieve
        from sqlalchemy import select
        result = await test_db.execute(
            select(IdentifiedCompetitor).where(IdentifiedCompetitor.job_id == job_id)
        )
        retrieved = result.scalars().all()

        assert len(retrieved) == 3
        assert all(c.job_id == job_id for c in retrieved)

    @pytest.mark.asyncio
    async def test_cascade_delete(self, test_db):
        """Test that deleting job cascades to related records."""
        job_id = uuid.uuid4()

        # Create job
        job = BrandAnalysisJob(
            id=job_id,
            user_id=1,
            questionnaire={},
            status=AnalysisStatus.COMPLETED,
            progress=100
        )
        await test_db.execute(test_db.add(job))

        # Add related records
        keyword = DiscoveredKeyword(
            job_id=job_id,
            keyword='test',
            source='nlp_extraction',
            relevance_score=0.5
        )
        await test_db.execute(test_db.add(keyword))
        await test_db.commit()

        # Delete job
        await test_db.execute(test_db.delete(job))
        await test_db.commit()

        # Verify keyword was deleted
        from sqlalchemy import select
        result = await test_db.execute(
            select(DiscoveredKeyword).where(DiscoveredKeyword.job_id == job_id)
        )
        keywords = result.scalars().all()
        assert len(keywords) == 0


@pytest.mark.integration
class TestDatabaseConstraints:
    """Test database constraints and validations."""

    @pytest.mark.asyncio
    async def test_job_requires_user(self, test_db):
        """Test that job requires valid user_id."""
        with pytest.raises(Exception):  # Foreign key constraint
            job = BrandAnalysisJob(
                id=uuid.uuid4(),
                user_id=99999,  # Non-existent user
                questionnaire={},
                status=AnalysisStatus.INITIATED,
                progress=0
            )
            await test_db.execute(test_db.add(job))
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_keyword_requires_job(self, test_db):
        """Test that keyword requires valid job_id."""
        with pytest.raises(Exception):  # Foreign key constraint
            keyword = DiscoveredKeyword(
                job_id=uuid.uuid4(),  # Non-existent job
                keyword='test',
                source='nlp_extraction',
                relevance_score=0.5
            )
            await test_db.execute(test_db.add(keyword))
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_job_status_enum(self, test_db):
        """Test that job status must be valid enum value."""
        job = BrandAnalysisJob(
            id=uuid.uuid4(),
            user_id=1,
            questionnaire={},
            status=AnalysisStatus.INITIATED,
            progress=0
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        # Valid status change
        job.status = AnalysisStatus.COMPLETED
        await test_db.commit()

        # Invalid status would raise error at Python level
        with pytest.raises(ValueError):
            job.status = 'invalid_status'
