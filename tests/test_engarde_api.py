"""Unit tests for En Garde API endpoints.

Tests all API endpoints, authentication, validation errors,
and background task triggering.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import status
from httpx import AsyncClient

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
from src.models.user import User


@pytest.mark.unit
class TestInitiateBrandAnalysis:
    """Test POST /engarde/brand-analysis/initiate endpoint."""

    @pytest.mark.asyncio
    async def test_initiate_brand_analysis_success(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test successfully initiating brand analysis."""
        questionnaire_data = {
            "brand_name": "Test Brand",
            "primary_website": "https://testbrand.com",
            "industry": "Technology",
            "target_markets": ["USA", "Canada"],
            "products_services": ["Software", "Consulting"],
            "known_competitors": ["competitor.com"],
            "target_keywords": ["keyword1", "keyword2"]
        }

        response = await test_client.post(
            "/api/v1/engarde/brand-analysis/initiate",
            json=questionnaire_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] == "initiated"
        assert uuid.UUID(data["job_id"])  # Valid UUID

    @pytest.mark.asyncio
    async def test_initiate_requires_authentication(self, test_client: AsyncClient):
        """Test that initiate endpoint requires authentication."""
        questionnaire_data = {
            "brand_name": "Test Brand",
            "primary_website": "https://testbrand.com",
            "industry": "Technology"
        }

        response = await test_client.post(
            "/api/v1/engarde/brand-analysis/initiate",
            json=questionnaire_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_initiate_validates_brand_name(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test brand name validation."""
        questionnaire_data = {
            "brand_name": "",  # Empty brand name
            "primary_website": "https://testbrand.com",
            "industry": "Technology"
        }

        response = await test_client.post(
            "/api/v1/engarde/brand-analysis/initiate",
            json=questionnaire_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_initiate_validates_website_url(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test website URL validation."""
        questionnaire_data = {
            "brand_name": "Test Brand",
            "primary_website": "not-a-url",  # Invalid URL
            "industry": "Technology"
        }

        response = await test_client.post(
            "/api/v1/engarde/brand-analysis/initiate",
            json=questionnaire_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_initiate_validates_industry(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test industry field validation."""
        questionnaire_data = {
            "brand_name": "Test Brand",
            "primary_website": "https://testbrand.com",
            "industry": ""  # Empty industry
        }

        response = await test_client.post(
            "/api/v1/engarde/brand-analysis/initiate",
            json=questionnaire_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_initiate_accepts_optional_fields(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test that optional fields are accepted but not required."""
        questionnaire_data = {
            "brand_name": "Test Brand",
            "primary_website": "https://testbrand.com",
            "industry": "Technology"
            # No optional fields provided
        }

        response = await test_client.post(
            "/api/v1/engarde/brand-analysis/initiate",
            json=questionnaire_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
class TestGetBrandAnalysisStatus:
    """Test GET /engarde/brand-analysis/{job_id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_status_success(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test successfully getting analysis status."""
        # Create a job
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.CRAWLING,
            progress=30
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        response = await test_client.get(
            f"/api/v1/engarde/brand-analysis/{job.id}/status",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["job_id"] == str(job.id)
        assert data["status"] == "crawling"
        assert data["progress"] == 30
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_status_not_found(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test getting status for non-existent job."""
        fake_job_id = str(uuid.uuid4())

        response = await test_client.get(
            f"/api/v1/engarde/brand-analysis/{fake_job_id}/status",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_status_invalid_job_id(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test getting status with invalid job ID format."""
        response = await test_client.get(
            "/api/v1/engarde/brand-analysis/not-a-uuid/status",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_status_requires_authentication(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User
    ):
        """Test that status endpoint requires authentication."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        response = await test_client.get(
            f"/api/v1/engarde/brand-analysis/{job.id}/status"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_status_with_error_message(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test getting status when job has failed with error."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.FAILED,
            error_message="Connection timeout"
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        response = await test_client.get(
            f"/api/v1/engarde/brand-analysis/{job.id}/status",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Connection timeout"


@pytest.mark.unit
class TestGetBrandAnalysisResults:
    """Test GET /engarde/brand-analysis/{job_id}/results endpoint."""

    @pytest.mark.asyncio
    async def test_get_results_success(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test successfully getting analysis results."""
        # Create completed job
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.COMPLETED,
            progress=100,
            results={"keywords_found": 50}
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Add some keywords
        keyword = DiscoveredKeyword(
            job_id=job.id,
            keyword="test keyword",
            source=KeywordSource.WEBSITE_CONTENT,
            relevance_score=0.8
        )
        test_db.add(keyword)

        # Add competitor
        competitor = IdentifiedCompetitor(
            job_id=job.id,
            domain="competitor.com",
            relevance_score=0.7,
            category=CompetitorCategory.PRIMARY
        )
        test_db.add(competitor)

        # Add opportunity
        opportunity = ContentOpportunity(
            job_id=job.id,
            topic="Test Topic",
            gap_type=GapType.MISSING_CONTENT,
            priority=ContentPriority.HIGH
        )
        test_db.add(opportunity)

        await test_db.commit()

        response = await test_client.get(
            f"/api/v1/engarde/brand-analysis/{job.id}/results",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["job_id"] == str(job.id)
        assert data["status"] == "completed"
        assert len(data["keywords"]) == 1
        assert len(data["competitors"]) == 1
        assert len(data["opportunities"]) == 1
        assert data["results"]["keywords_found"] == 50

    @pytest.mark.asyncio
    async def test_get_results_incomplete_job(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test getting results for incomplete job."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.CRAWLING,
            progress=30
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        response = await test_client.get(
            f"/api/v1/engarde/brand-analysis/{job.id}/results",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not complete" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_results_not_found(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test getting results for non-existent job."""
        fake_job_id = str(uuid.uuid4())

        response = await test_client.get(
            f"/api/v1/engarde/brand-analysis/{fake_job_id}/results",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestConfirmBrandAnalysis:
    """Test POST /engarde/brand-analysis/{job_id}/confirm endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_analysis_success(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test successfully confirming analysis selections."""
        # Create completed job
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.COMPLETED,
            progress=100
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Add keywords
        keyword1 = DiscoveredKeyword(
            job_id=job.id,
            keyword="keyword1",
            source=KeywordSource.WEBSITE_CONTENT,
            relevance_score=0.8
        )
        keyword2 = DiscoveredKeyword(
            job_id=job.id,
            keyword="keyword2",
            source=KeywordSource.NLP_EXTRACTION,
            relevance_score=0.7
        )
        test_db.add(keyword1)
        test_db.add(keyword2)
        await test_db.commit()
        await test_db.refresh(keyword1)
        await test_db.refresh(keyword2)

        # Add competitor
        competitor = IdentifiedCompetitor(
            job_id=job.id,
            domain="competitor.com",
            relevance_score=0.7,
            category=CompetitorCategory.PRIMARY
        )
        test_db.add(competitor)
        await test_db.commit()
        await test_db.refresh(competitor)

        # Confirm selections
        confirmation_data = {
            "selected_keywords": [keyword1.id, keyword2.id],
            "selected_competitors": [competitor.id]
        }

        response = await test_client.post(
            f"/api/v1/engarde/brand-analysis/{job.id}/confirm",
            json=confirmation_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["imported"] is True
        assert data["keywords_count"] == 2
        assert data["competitors_count"] == 1

        # Verify keywords are marked as confirmed
        await test_db.refresh(keyword1)
        await test_db.refresh(keyword2)
        await test_db.refresh(competitor)
        assert keyword1.confirmed is True
        assert keyword2.confirmed is True
        assert competitor.confirmed is True

    @pytest.mark.asyncio
    async def test_confirm_analysis_empty_selections(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test confirming with no selections."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.COMPLETED
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        confirmation_data = {
            "selected_keywords": [],
            "selected_competitors": []
        }

        response = await test_client.post(
            f"/api/v1/engarde/brand-analysis/{job.id}/confirm",
            json=confirmation_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["keywords_count"] == 0
        assert data["competitors_count"] == 0

    @pytest.mark.asyncio
    async def test_confirm_analysis_not_found(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test confirming non-existent job."""
        fake_job_id = str(uuid.uuid4())
        confirmation_data = {
            "selected_keywords": [1, 2],
            "selected_competitors": [1]
        }

        response = await test_client.post(
            f"/api/v1/engarde/brand-analysis/{fake_job_id}/confirm",
            json=confirmation_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestDeleteBrandAnalysis:
    """Test DELETE /engarde/brand-analysis/{job_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_analysis_success(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test successfully deleting analysis job."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        job_id = job.id

        response = await test_client.delete(
            f"/api/v1/engarde/brand-analysis/{job_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"]

        # Verify job is deleted
        deleted_job = await test_db.query(BrandAnalysisJob).filter(
            BrandAnalysisJob.id == job_id
        ).first()
        assert deleted_job is None

    @pytest.mark.asyncio
    async def test_delete_analysis_cascades(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User,
        test_token: str
    ):
        """Test deleting analysis cascades to related data."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        # Add related data
        keyword = DiscoveredKeyword(
            job_id=job.id,
            keyword="test",
            source=KeywordSource.WEBSITE_CONTENT,
            relevance_score=0.5
        )
        test_db.add(keyword)
        await test_db.commit()

        job_id = job.id

        response = await test_client.delete(
            f"/api/v1/engarde/brand-analysis/{job_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify cascade delete
        keywords = await test_db.query(DiscoveredKeyword).filter(
            DiscoveredKeyword.job_id == job_id
        ).all()
        assert len(keywords) == 0

    @pytest.mark.asyncio
    async def test_delete_analysis_not_found(
        self,
        test_client: AsyncClient,
        test_token: str
    ):
        """Test deleting non-existent job."""
        fake_job_id = str(uuid.uuid4())

        response = await test_client.delete(
            f"/api/v1/engarde/brand-analysis/{fake_job_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_analysis_requires_authentication(
        self,
        test_client: AsyncClient,
        test_db,
        test_user: User
    ):
        """Test that delete endpoint requires authentication."""
        job = BrandAnalysisJob(
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"}
        )
        test_db.add(job)
        await test_db.commit()
        await test_db.refresh(job)

        response = await test_client.delete(
            f"/api/v1/engarde/brand-analysis/{job.id}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
class TestPydanticSchemas:
    """Test Pydantic schema validation."""

    def test_questionnaire_schema_validation(self):
        """Test BrandAnalysisQuestionnaireSchema validation."""
        from src.api.v1.engarde import BrandAnalysisQuestionnaireSchema

        # Valid data
        valid_data = {
            "brand_name": "Test Brand",
            "primary_website": "https://test.com",
            "industry": "Technology"
        }
        schema = BrandAnalysisQuestionnaireSchema(**valid_data)
        assert schema.brand_name == "Test Brand"
        assert schema.target_markets == []  # Default

        # Invalid URL
        with pytest.raises(Exception):
            BrandAnalysisQuestionnaireSchema(
                brand_name="Test",
                primary_website="not-a-url",
                industry="Tech"
            )

    def test_discovered_keyword_schema(self):
        """Test DiscoveredKeywordSchema serialization."""
        from src.api.v1.engarde import DiscoveredKeywordSchema

        keyword_data = {
            "id": 1,
            "keyword": "test",
            "source": "website_content",
            "search_volume": 1000,
            "difficulty": 50.0,
            "relevance_score": 0.8,
            "current_ranking": 5,
            "confirmed": False
        }

        schema = DiscoveredKeywordSchema(**keyword_data)
        assert schema.keyword == "test"
        assert schema.search_volume == 1000

    def test_competitor_schema(self):
        """Test IdentifiedCompetitorSchema serialization."""
        from src.api.v1.engarde import IdentifiedCompetitorSchema

        competitor_data = {
            "id": 1,
            "domain": "competitor.com",
            "name": "Competitor Inc",
            "relevance_score": 0.75,
            "category": "primary",
            "overlap_percentage": 65.0,
            "confirmed": False
        }

        schema = IdentifiedCompetitorSchema(**competitor_data)
        assert schema.domain == "competitor.com"
        assert schema.category == "primary"
