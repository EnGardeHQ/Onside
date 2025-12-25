"""API tests for En Garde integration endpoints.

Tests all /api/v1/engarde/* endpoints including authentication,
validation, error handling, and response formats.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus
)
from tests.fixtures.brand_analysis_fixtures import (
    SAMPLE_QUESTIONNAIRE_COMPLETE,
    SAMPLE_KEYWORDS,
    SAMPLE_COMPETITORS,
    SAMPLE_CONTENT_OPPORTUNITIES
)


@pytest.mark.api
@pytest.mark.asyncio
class TestBrandAnalysisInitiateEndpoint:
    """Test /engarde/brand-analysis/initiate endpoint."""

    @pytest.mark.asyncio
    async def test_initiate_success(self, test_client, test_token):
        """Test successful brand analysis initiation."""
        headers = {'Authorization': f'Bearer {test_token}'}

        response = await test_client.post(
            '/api/v1/engarde/brand-analysis/initiate',
            json=SAMPLE_QUESTIONNAIRE_COMPLETE,
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()

        assert 'job_id' in data
        assert 'status' in data
        assert 'message' in data
        assert data['status'] == 'initiated'
        assert uuid.UUID(data['job_id'])  # Valid UUID

    @pytest.mark.asyncio
    async def test_initiate_requires_auth(self, test_client):
        """Test that initiate requires authentication."""
        response = await test_client.post(
            '/api/v1/engarde/brand-analysis/initiate',
            json=SAMPLE_QUESTIONNAIRE_COMPLETE
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_initiate_validation_error(self, test_client, test_token):
        """Test validation error with invalid questionnaire."""
        headers = {'Authorization': f'Bearer {test_token}'}

        invalid_data = {
            'brand_name': '',  # Empty brand name
            'primary_website': 'not-a-url',  # Invalid URL
            'industry': 'Tech'
        }

        response = await test_client.post(
            '/api/v1/engarde/brand-analysis/initiate',
            json=invalid_data,
            headers=headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_initiate_missing_required_fields(self, test_client, test_token):
        """Test error when required fields are missing."""
        headers = {'Authorization': f'Bearer {test_token}'}

        incomplete_data = {
            'brand_name': 'Test Brand'
            # Missing required fields
        }

        response = await test_client.post(
            '/api/v1/engarde/brand-analysis/initiate',
            json=incomplete_data,
            headers=headers
        )

        assert response.status_code == 422


@pytest.mark.api
@pytest.mark.asyncio
class TestBrandAnalysisStatusEndpoint:
    """Test /engarde/brand-analysis/{job_id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_status_success(self, test_client, test_token, test_db, test_user):
        """Test successful status retrieval."""
        # Create job
        job_id = uuid.uuid4()
        job = BrandAnalysisJob(
            id=job_id,
            user_id=test_user.id,
            questionnaire=SAMPLE_QUESTIONNAIRE_COMPLETE,
            status=AnalysisStatus.ANALYZING,
            progress=50
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        headers = {'Authorization': f'Bearer {test_token}'}

        response = await test_client.get(
            f'/api/v1/engarde/brand-analysis/{job_id}/status',
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['job_id'] == str(job_id)
        assert data['status'] == 'analyzing'
        assert data['progress'] == 50
        assert 'created_at' in data
        assert 'updated_at' in data

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, test_client, test_token):
        """Test status for non-existent job."""
        headers = {'Authorization': f'Bearer {test_token}'}
        fake_job_id = uuid.uuid4()

        response = await test_client.get(
            f'/api/v1/engarde/brand-analysis/{fake_job_id}/status',
            headers=headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_status_invalid_uuid(self, test_client, test_token):
        """Test status with invalid UUID format."""
        headers = {'Authorization': f'Bearer {test_token}'}

        response = await test_client.get(
            '/api/v1/engarde/brand-analysis/invalid-uuid/status',
            headers=headers
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_status_requires_auth(self, test_client, test_db, test_user):
        """Test that status endpoint requires authentication."""
        job_id = uuid.uuid4()
        job = BrandAnalysisJob(
            id=job_id,
            user_id=test_user.id,
            questionnaire=SAMPLE_QUESTIONNAIRE_COMPLETE,
            status=AnalysisStatus.INITIATED,
            progress=0
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        response = await test_client.get(
            f'/api/v1/engarde/brand-analysis/{job_id}/status'
        )

        assert response.status_code == 401


@pytest.mark.api
@pytest.mark.asyncio
class TestBrandAnalysisResultsEndpoint:
    """Test /engarde/brand-analysis/{job_id}/results endpoint."""

    @pytest.mark.asyncio
    async def test_get_results_success(self, test_client, test_token, test_db, test_user):
        """Test successful results retrieval."""
        # Create completed job
        job_id = uuid.uuid4()
        job = BrandAnalysisJob(
            id=job_id,
            user_id=test_user.id,
            questionnaire=SAMPLE_QUESTIONNAIRE_COMPLETE,
            status=AnalysisStatus.COMPLETED,
            progress=100,
            results={'keywords_found': 10, 'competitors_identified': 5},
            completed_at=datetime.utcnow()
        )
        await test_db.execute(test_db.add(job))

        # Add some keywords
        for kw_data in SAMPLE_KEYWORDS[:3]:
            keyword = DiscoveredKeyword(
                job_id=job_id,
                **kw_data
            )
            await test_db.execute(test_db.add(keyword))

        # Add some competitors
        for comp_data in SAMPLE_COMPETITORS[:2]:
            competitor = IdentifiedCompetitor(
                job_id=job_id,
                **comp_data
            )
            await test_db.execute(test_db.add(competitor))

        await test_db.commit()

        headers = {'Authorization': f'Bearer {test_token}'}

        response = await test_client.get(
            f'/api/v1/engarde/brand-analysis/{job_id}/results',
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['job_id'] == str(job_id)
        assert data['status'] == 'completed'
        assert 'keywords' in data
        assert 'competitors' in data
        assert 'opportunities' in data
        assert len(data['keywords']) == 3
        assert len(data['competitors']) == 2

    @pytest.mark.asyncio
    async def test_get_results_job_not_complete(self, test_client, test_token, test_db, test_user):
        """Test results retrieval for incomplete job."""
        job_id = uuid.uuid4()
        job = BrandAnalysisJob(
            id=job_id,
            user_id=test_user.id,
            questionnaire=SAMPLE_QUESTIONNAIRE_COMPLETE,
            status=AnalysisStatus.ANALYZING,
            progress=50
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        headers = {'Authorization': f'Bearer {test_token}'}

        response = await test_client.get(
            f'/api/v1/engarde/brand-analysis/{job_id}/results',
            headers=headers
        )

        assert response.status_code == 400
        assert 'not complete' in response.json()['detail'].lower()

    @pytest.mark.asyncio
    async def test_get_results_not_found(self, test_client, test_token):
        """Test results for non-existent job."""
        headers = {'Authorization': f'Bearer {test_token}'}
        fake_job_id = uuid.uuid4()

        response = await test_client.get(
            f'/api/v1/engarde/brand-analysis/{fake_job_id}/results',
            headers=headers
        )

        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.asyncio
class TestBrandAnalysisConfirmEndpoint:
    """Test /engarde/brand-analysis/{job_id}/confirm endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_success(self, test_client, test_token, test_db, test_user):
        """Test successful confirmation."""
        job_id = uuid.uuid4()
        job = BrandAnalysisJob(
            id=job_id,
            user_id=test_user.id,
            questionnaire=SAMPLE_QUESTIONNAIRE_COMPLETE,
            status=AnalysisStatus.COMPLETED,
            progress=100
        )
        await test_db.execute(test_db.add(job))

        # Add keywords
        keyword_ids = []
        for i in range(3):
            kw = DiscoveredKeyword(
                job_id=job_id,
                keyword=f'keyword{i}',
                source='nlp_extraction',
                relevance_score=0.5,
                confirmed=False
            )
            await test_db.execute(test_db.add(kw))
            await test_db.flush()
            keyword_ids.append(kw.id)

        # Add competitors
        competitor_ids = []
        for i in range(2):
            comp = IdentifiedCompetitor(
                job_id=job_id,
                domain=f'competitor{i}.com',
                relevance_score=0.5,
                category='secondary',
                confirmed=False
            )
            await test_db.execute(test_db.add(comp))
            await test_db.flush()
            competitor_ids.append(comp.id)

        await test_db.commit()

        headers = {'Authorization': f'Bearer {test_token}'}

        confirmation_data = {
            'selected_keywords': keyword_ids,
            'selected_competitors': competitor_ids
        }

        response = await test_client.post(
            f'/api/v1/engarde/brand-analysis/{job_id}/confirm',
            json=confirmation_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data['imported'] is True
        assert data['keywords_count'] == 3
        assert data['competitors_count'] == 2

    @pytest.mark.asyncio
    async def test_confirm_empty_selection(self, test_client, test_token, test_db, test_user):
        """Test confirmation with empty selection."""
        job_id = uuid.uuid4()
        job = BrandAnalysisJob(
            id=job_id,
            user_id=test_user.id,
            questionnaire=SAMPLE_QUESTIONNAIRE_COMPLETE,
            status=AnalysisStatus.COMPLETED,
            progress=100
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        headers = {'Authorization': f'Bearer {test_token}'}

        confirmation_data = {
            'selected_keywords': [],
            'selected_competitors': []
        }

        response = await test_client.post(
            f'/api/v1/engarde/brand-analysis/{job_id}/confirm',
            json=confirmation_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['keywords_count'] == 0
        assert data['competitors_count'] == 0


@pytest.mark.api
@pytest.mark.asyncio
class TestBrandAnalysisDeleteEndpoint:
    """Test /engarde/brand-analysis/{job_id} DELETE endpoint."""

    @pytest.mark.asyncio
    async def test_delete_success(self, test_client, test_token, test_db, test_user):
        """Test successful job deletion."""
        job_id = uuid.uuid4()
        job = BrandAnalysisJob(
            id=job_id,
            user_id=test_user.id,
            questionnaire=SAMPLE_QUESTIONNAIRE_COMPLETE,
            status=AnalysisStatus.COMPLETED,
            progress=100
        )
        await test_db.execute(test_db.add(job))
        await test_db.commit()

        headers = {'Authorization': f'Bearer {test_token}'}

        response = await test_client.delete(
            f'/api/v1/engarde/brand-analysis/{job_id}',
            headers=headers
        )

        assert response.status_code == 200

        # Verify job was deleted
        from sqlalchemy import select
        result = await test_db.execute(
            select(BrandAnalysisJob).where(BrandAnalysisJob.id == job_id)
        )
        deleted_job = result.scalar_one_or_none()
        assert deleted_job is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, test_client, test_token):
        """Test delete for non-existent job."""
        headers = {'Authorization': f'Bearer {test_token}'}
        fake_job_id = uuid.uuid4()

        response = await test_client.delete(
            f'/api/v1/engarde/brand-analysis/{fake_job_id}',
            headers=headers
        )

        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.asyncio
class TestAPIRateLimiting:
    """Test rate limiting (if implemented)."""

    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client, test_token):
        """Test API rate limiting."""
        # Would test rate limiting if implemented
        pass


@pytest.mark.api
@pytest.mark.asyncio
class TestAPIErrorResponses:
    """Test API error response formats."""

    @pytest.mark.asyncio
    async def test_404_response_format(self, test_client, test_token):
        """Test 404 error response format."""
        headers = {'Authorization': f'Bearer {test_token}'}
        fake_id = uuid.uuid4()

        response = await test_client.get(
            f'/api/v1/engarde/brand-analysis/{fake_id}/status',
            headers=headers
        )

        assert response.status_code == 404
        assert 'detail' in response.json()

    @pytest.mark.asyncio
    async def test_422_validation_error_format(self, test_client, test_token):
        """Test 422 validation error format."""
        headers = {'Authorization': f'Bearer {test_token}'}

        invalid_data = {
            'brand_name': '',
            'primary_website': 'invalid',
            'industry': 'Tech'
        }

        response = await test_client.post(
            '/api/v1/engarde/brand-analysis/initiate',
            json=invalid_data,
            headers=headers
        )

        assert response.status_code == 422
        error_data = response.json()
        assert 'detail' in error_data

    @pytest.mark.asyncio
    async def test_401_unauthorized_format(self, test_client):
        """Test 401 unauthorized response format."""
        response = await test_client.get(
            '/api/v1/engarde/brand-analysis/test/status'
        )

        assert response.status_code == 401
        assert 'detail' in response.json()
