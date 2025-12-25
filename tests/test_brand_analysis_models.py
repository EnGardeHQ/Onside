"""Unit tests for brand analysis models.

Tests model creation, relationships, enum validations, and data serialization
for all brand analysis related models.
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus,
    KeywordSource,
    CompetitorCategory,
    GapType,
    ContentPriority
)
from src.models.user import User, UserRole


@pytest.mark.unit
class TestEnumValidations:
    """Test enum value validations."""

    def test_analysis_status_enum_values(self):
        """Test AnalysisStatus enum has all expected values."""
        assert AnalysisStatus.INITIATED.value == "initiated"
        assert AnalysisStatus.CRAWLING.value == "crawling"
        assert AnalysisStatus.ANALYZING.value == "analyzing"
        assert AnalysisStatus.PROCESSING.value == "processing"
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"

    def test_keyword_source_enum_values(self):
        """Test KeywordSource enum has all expected values."""
        assert KeywordSource.WEBSITE_CONTENT.value == "website_content"
        assert KeywordSource.SERP_ANALYSIS.value == "serp_analysis"
        assert KeywordSource.NLP_EXTRACTION.value == "nlp_extraction"

    def test_competitor_category_enum_values(self):
        """Test CompetitorCategory enum has all expected values."""
        assert CompetitorCategory.PRIMARY.value == "primary"
        assert CompetitorCategory.SECONDARY.value == "secondary"
        assert CompetitorCategory.EMERGING.value == "emerging"
        assert CompetitorCategory.NICHE.value == "niche"

    def test_gap_type_enum_values(self):
        """Test GapType enum has all expected values."""
        assert GapType.MISSING_CONTENT.value == "missing_content"
        assert GapType.WEAK_CONTENT.value == "weak_content"
        assert GapType.COMPETITOR_STRENGTH.value == "competitor_strength"

    def test_content_priority_enum_values(self):
        """Test ContentPriority enum has all expected values."""
        assert ContentPriority.HIGH.value == "high"
        assert ContentPriority.MEDIUM.value == "medium"
        assert ContentPriority.LOW.value == "low"


@pytest.mark.unit
class TestBrandAnalysisJob:
    """Test BrandAnalysisJob model."""

    def test_create_brand_analysis_job(self, test_db: Session, test_user: User):
        """Test creating a brand analysis job with valid data."""
        questionnaire = {
            "brand_name": "Test Brand",
            "primary_website": "https://testbrand.com",
            "industry": "Technology",
            "target_markets": ["USA", "Canada"],
            "products_services": ["Software", "Consulting"],
            "known_competitors": ["competitor1.com"],
            "target_keywords": ["keyword1", "keyword2"]
        }

        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire=questionnaire,
            status=AnalysisStatus.INITIATED,
            progress=0
        )

        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        assert job.id is not None
        assert isinstance(job.id, uuid.UUID)
        assert job.user_id == test_user.id
        assert job.questionnaire == questionnaire
        assert job.status == AnalysisStatus.INITIATED
        assert job.progress == 0
        assert job.results is None
        assert job.error_message is None
        assert job.created_at is not None
        assert job.updated_at is not None
        assert job.completed_at is None

    def test_brand_analysis_job_default_values(self, test_db: Session, test_user: User):
        """Test default values for brand analysis job."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )

        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        assert job.status == AnalysisStatus.INITIATED
        assert job.progress == 0

    def test_brand_analysis_job_requires_user(self, test_db: Session):
        """Test that brand analysis job requires a user."""
        job = BrandAnalysisJob(
            user_id=999999,  # Non-existent user
            questionnaire={"brand_name": "Test"}
        )

        test_db.add(job)
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()

    def test_brand_analysis_job_requires_questionnaire(self, test_db: Session, test_user: User):
        """Test that brand analysis job requires questionnaire data."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire=None
        )

        test_db.add(job)
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()

    def test_update_job_progress(self, test_db: Session, test_user: User):
        """Test updating job progress and status."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )

        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        # Update progress
        job.status = AnalysisStatus.CRAWLING
        job.progress = 30
        test_db.commit()
        test_db.refresh(job)

        assert job.status == AnalysisStatus.CRAWLING
        assert job.progress == 30

    def test_complete_job_with_results(self, test_db: Session, test_user: User):
        """Test completing a job with results."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )

        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        # Complete job
        results = {
            "keywords_found": 50,
            "competitors_identified": 10,
            "content_opportunities": 5
        }
        job.status = AnalysisStatus.COMPLETED
        job.progress = 100
        job.results = results
        job.completed_at = datetime.utcnow()

        test_db.commit()
        test_db.refresh(job)

        assert job.status == AnalysisStatus.COMPLETED
        assert job.progress == 100
        assert job.results == results
        assert job.completed_at is not None

    def test_fail_job_with_error_message(self, test_db: Session, test_user: User):
        """Test failing a job with error message."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )

        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        # Fail job
        error_msg = "Failed to crawl website: Connection timeout"
        job.status = AnalysisStatus.FAILED
        job.error_message = error_msg

        test_db.commit()
        test_db.refresh(job)

        assert job.status == AnalysisStatus.FAILED
        assert job.error_message == error_msg


@pytest.mark.unit
class TestDiscoveredKeyword:
    """Test DiscoveredKeyword model."""

    def test_create_discovered_keyword(self, test_db: Session, test_user: User):
        """Test creating a discovered keyword."""
        # Create job first
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)

        # Create keyword
        keyword = DiscoveredKeyword(
            job_id=job.id,
            keyword="test keyword",
            source=KeywordSource.WEBSITE_CONTENT,
            search_volume=1000,
            difficulty=45.5,
            relevance_score=0.85,
            current_ranking=5,
            serp_features={"featured_snippet": True}
        )

        test_db.add(keyword)
        test_db.commit()
        test_db.refresh(keyword)

        assert keyword.id is not None
        assert keyword.job_id == job.id
        assert keyword.keyword == "test keyword"
        assert keyword.source == KeywordSource.WEBSITE_CONTENT
        assert keyword.search_volume == 1000
        assert keyword.difficulty == 45.5
        assert keyword.relevance_score == 0.85
        assert keyword.current_ranking == 5
        assert keyword.serp_features == {"featured_snippet": True}
        assert keyword.confirmed is False
        assert keyword.created_at is not None

    def test_discovered_keyword_default_values(self, test_db: Session, test_user: User):
        """Test default values for discovered keyword."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        keyword = DiscoveredKeyword(
            job_id=job.id,
            keyword="test",
            source=KeywordSource.NLP_EXTRACTION
        )

        test_db.add(keyword)
        test_db.commit()
        test_db.refresh(keyword)

        assert keyword.relevance_score == 0.0
        assert keyword.confirmed is False

    def test_discovered_keyword_relationship(self, test_db: Session, test_user: User):
        """Test relationship between keyword and job."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        keyword = DiscoveredKeyword(
            job_id=job.id,
            keyword="test",
            source=KeywordSource.WEBSITE_CONTENT,
            relevance_score=0.5
        )

        test_db.add(keyword)
        test_db.commit()
        test_db.refresh(job)

        assert len(job.discovered_keywords) == 1
        assert job.discovered_keywords[0].keyword == "test"

    def test_confirm_keyword(self, test_db: Session, test_user: User):
        """Test confirming a keyword."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        keyword = DiscoveredKeyword(
            job_id=job.id,
            keyword="test",
            source=KeywordSource.WEBSITE_CONTENT,
            relevance_score=0.8
        )
        test_db.add(keyword)
        test_db.commit()
        test_db.refresh(keyword)

        # Confirm keyword
        keyword.confirmed = True
        test_db.commit()
        test_db.refresh(keyword)

        assert keyword.confirmed is True


@pytest.mark.unit
class TestIdentifiedCompetitor:
    """Test IdentifiedCompetitor model."""

    def test_create_identified_competitor(self, test_db: Session, test_user: User):
        """Test creating an identified competitor."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        competitor = IdentifiedCompetitor(
            job_id=job.id,
            domain="competitor.com",
            name="Competitor Inc",
            relevance_score=0.75,
            category=CompetitorCategory.PRIMARY,
            overlap_percentage=65.5,
            keyword_overlap=["keyword1", "keyword2"],
            content_similarity=0.82
        )

        test_db.add(competitor)
        test_db.commit()
        test_db.refresh(competitor)

        assert competitor.id is not None
        assert competitor.job_id == job.id
        assert competitor.domain == "competitor.com"
        assert competitor.name == "Competitor Inc"
        assert competitor.relevance_score == 0.75
        assert competitor.category == CompetitorCategory.PRIMARY
        assert competitor.overlap_percentage == 65.5
        assert competitor.keyword_overlap == ["keyword1", "keyword2"]
        assert competitor.content_similarity == 0.82
        assert competitor.confirmed is False

    def test_identified_competitor_default_values(self, test_db: Session, test_user: User):
        """Test default values for identified competitor."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        competitor = IdentifiedCompetitor(
            job_id=job.id,
            domain="competitor.com",
            relevance_score=0.5
        )

        test_db.add(competitor)
        test_db.commit()
        test_db.refresh(competitor)

        assert competitor.category == CompetitorCategory.SECONDARY
        assert competitor.confirmed is False
        assert competitor.relevance_score == 0.5

    def test_identified_competitor_relationship(self, test_db: Session, test_user: User):
        """Test relationship between competitor and job."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        competitor = IdentifiedCompetitor(
            job_id=job.id,
            domain="competitor.com",
            relevance_score=0.7,
            category=CompetitorCategory.PRIMARY
        )

        test_db.add(competitor)
        test_db.commit()
        test_db.refresh(job)

        assert len(job.identified_competitors) == 1
        assert job.identified_competitors[0].domain == "competitor.com"


@pytest.mark.unit
class TestContentOpportunity:
    """Test ContentOpportunity model."""

    def test_create_content_opportunity(self, test_db: Session, test_user: User):
        """Test creating a content opportunity."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        opportunity = ContentOpportunity(
            job_id=job.id,
            topic="Guide to Test Automation",
            gap_type=GapType.MISSING_CONTENT,
            traffic_potential=5000,
            difficulty=55.0,
            priority=ContentPriority.HIGH,
            recommended_format="blog"
        )

        test_db.add(opportunity)
        test_db.commit()
        test_db.refresh(opportunity)

        assert opportunity.id is not None
        assert opportunity.job_id == job.id
        assert opportunity.topic == "Guide to Test Automation"
        assert opportunity.gap_type == GapType.MISSING_CONTENT
        assert opportunity.traffic_potential == 5000
        assert opportunity.difficulty == 55.0
        assert opportunity.priority == ContentPriority.HIGH
        assert opportunity.recommended_format == "blog"

    def test_content_opportunity_default_priority(self, test_db: Session, test_user: User):
        """Test default priority for content opportunity."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        opportunity = ContentOpportunity(
            job_id=job.id,
            topic="Test Topic",
            gap_type=GapType.WEAK_CONTENT
        )

        test_db.add(opportunity)
        test_db.commit()
        test_db.refresh(opportunity)

        assert opportunity.priority == ContentPriority.MEDIUM

    def test_content_opportunity_relationship(self, test_db: Session, test_user: User):
        """Test relationship between opportunity and job."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        opportunity = ContentOpportunity(
            job_id=job.id,
            topic="Test Topic",
            gap_type=GapType.MISSING_CONTENT,
            priority=ContentPriority.HIGH
        )

        test_db.add(opportunity)
        test_db.commit()
        test_db.refresh(job)

        assert len(job.content_opportunities) == 1
        assert job.content_opportunities[0].topic == "Test Topic"


@pytest.mark.unit
class TestCascadeDeletes:
    """Test cascade delete behavior."""

    def test_delete_job_cascades_to_keywords(self, test_db: Session, test_user: User):
        """Test deleting a job cascades to keywords."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        # Add keywords
        for i in range(3):
            keyword = DiscoveredKeyword(
                job_id=job.id,
                keyword=f"keyword{i}",
                source=KeywordSource.WEBSITE_CONTENT,
                relevance_score=0.5
            )
            test_db.add(keyword)
        test_db.commit()

        job_id = job.id

        # Delete job
        test_db.delete(job)
        test_db.commit()

        # Check keywords are deleted
        keywords = test_db.query(DiscoveredKeyword).filter(
            DiscoveredKeyword.job_id == job_id
        ).all()
        assert len(keywords) == 0

    def test_delete_job_cascades_to_competitors(self, test_db: Session, test_user: User):
        """Test deleting a job cascades to competitors."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        # Add competitors
        for i in range(3):
            competitor = IdentifiedCompetitor(
                job_id=job.id,
                domain=f"competitor{i}.com",
                relevance_score=0.5,
                category=CompetitorCategory.SECONDARY
            )
            test_db.add(competitor)
        test_db.commit()

        job_id = job.id

        # Delete job
        test_db.delete(job)
        test_db.commit()

        # Check competitors are deleted
        competitors = test_db.query(IdentifiedCompetitor).filter(
            IdentifiedCompetitor.job_id == job_id
        ).all()
        assert len(competitors) == 0

    def test_delete_job_cascades_to_opportunities(self, test_db: Session, test_user: User):
        """Test deleting a job cascades to opportunities."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        test_db.commit()

        # Add opportunities
        for i in range(3):
            opportunity = ContentOpportunity(
                job_id=job.id,
                topic=f"Topic {i}",
                gap_type=GapType.MISSING_CONTENT,
                priority=ContentPriority.MEDIUM
            )
            test_db.add(opportunity)
        test_db.commit()

        job_id = job.id

        # Delete job
        test_db.delete(job)
        test_db.commit()

        # Check opportunities are deleted
        opportunities = test_db.query(ContentOpportunity).filter(
            ContentOpportunity.job_id == job_id
        ).all()
        assert len(opportunities) == 0
