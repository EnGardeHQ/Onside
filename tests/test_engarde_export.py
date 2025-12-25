"""
Integration tests for En Garde export endpoints.

Tests the CSV and campaign format export functionality that allows
Onside brand analysis results to be exported into En Garde's campaign system.
"""

import pytest
import uuid
import json
import csv
import io
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus
)
from src.models.user import User


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """Create test user."""
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password_here",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def completed_analysis_job(db_session: Session, test_user: User):
    """Create a completed brand analysis job with sample data."""
    job_id = uuid.uuid4()

    # Create job
    job = BrandAnalysisJob(
        id=job_id,
        user_id=test_user.id,
        questionnaire={
            "brand_name": "Test Marketing Tools",
            "primary_website": "https://www.testmarketing.com",
            "industry": "SaaS Marketing",
            "target_markets": ["United States", "Canada"],
            "products_services": ["Email Marketing", "Analytics"],
            "known_competitors": ["mailchimp.com"],
            "target_keywords": ["email marketing"]
        },
        status=AnalysisStatus.COMPLETED,
        progress=100,
        completed_at=datetime.utcnow(),
        results={
            "keywords_found": 3,
            "competitors_identified": 2,
            "content_opportunities": 2
        }
    )
    db_session.add(job)

    # Create keywords
    keywords = [
        DiscoveredKeyword(
            job_id=job_id,
            keyword="email marketing automation",
            source="nlp_extraction",
            search_volume=12000,
            difficulty=65.5,
            relevance_score=0.87,
            current_ranking=None,
            confirmed=True
        ),
        DiscoveredKeyword(
            job_id=job_id,
            keyword="marketing automation software",
            source="website_content",
            search_volume=8500,
            difficulty=72.3,
            relevance_score=0.82,
            current_ranking=15,
            confirmed=True
        ),
        DiscoveredKeyword(
            job_id=job_id,
            keyword="crm email marketing",
            source="serp_analysis",
            search_volume=5200,
            difficulty=58.1,
            relevance_score=0.75,
            current_ranking=None,
            confirmed=False
        )
    ]
    for kw in keywords:
        db_session.add(kw)

    # Create competitors
    competitors = [
        IdentifiedCompetitor(
            job_id=job_id,
            domain="mailchimp.com",
            name="Mailchimp",
            relevance_score=0.92,
            category="primary",
            overlap_percentage=78.5,
            confirmed=True
        ),
        IdentifiedCompetitor(
            job_id=job_id,
            domain="hubspot.com",
            name="HubSpot",
            relevance_score=0.88,
            category="primary",
            overlap_percentage=65.2,
            confirmed=False
        )
    ]
    for comp in competitors:
        db_session.add(comp)

    # Create opportunities
    opportunities = [
        ContentOpportunity(
            job_id=job_id,
            topic="Email segmentation best practices",
            gap_type="missing_content",
            traffic_potential=5000,
            difficulty=45.0,
            priority="high",
            recommended_format="guide"
        ),
        ContentOpportunity(
            job_id=job_id,
            topic="Marketing automation ROI calculator",
            gap_type="missing_content",
            traffic_potential=3200,
            difficulty=38.5,
            priority="high",
            recommended_format="blog"
        )
    ]
    for opp in opportunities:
        db_session.add(opp)

    db_session.commit()
    db_session.refresh(job)

    return job


class TestCSVExport:
    """Test CSV export endpoint."""

    def test_export_csv_success(self, test_client, completed_analysis_job, auth_headers):
        """Test successful CSV export."""
        job_id = str(completed_analysis_job.id)

        response = test_client.get(
            f"/engarde/brand-analysis/{job_id}/export/csv",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        # Parse CSV content
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        rows = list(csv_reader)
        assert len(rows) > 0

        # Verify headers
        expected_headers = [
            "type", "keyword", "domain", "topic", "source",
            "search_volume", "difficulty", "relevance_score", "priority",
            "current_ranking", "category", "traffic_potential",
            "gap_type", "recommended_format", "overlap_percentage", "metadata"
        ]
        assert list(csv_reader.fieldnames) == expected_headers

        # Verify keyword rows
        keyword_rows = [r for r in rows if r["type"] == "keyword"]
        assert len(keyword_rows) == 3

        # Check first keyword
        kw1 = keyword_rows[0]
        assert kw1["keyword"] == "email marketing automation"
        assert kw1["search_volume"] == "12000"
        assert kw1["difficulty"] == "65.5"
        assert kw1["priority"] == "high"

        # Verify competitor rows
        competitor_rows = [r for r in rows if r["type"] == "competitor"]
        assert len(competitor_rows) == 2

        comp1 = competitor_rows[0]
        assert comp1["domain"] == "mailchimp.com"
        assert "Mailchimp" in comp1["metadata"]

        # Verify opportunity rows
        opp_rows = [r for r in rows if r["type"] == "content_opportunity"]
        assert len(opp_rows) == 2

        opp1 = opp_rows[0]
        assert "Email segmentation" in opp1["topic"]
        assert opp1["gap_type"] == "missing_content"
        assert opp1["recommended_format"] == "guide"

    def test_export_csv_invalid_job_id(self, test_client, auth_headers):
        """Test CSV export with invalid job ID."""
        response = test_client.get(
            "/engarde/brand-analysis/invalid-uuid/export/csv",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "Invalid job ID format" in response.json()["detail"]

    def test_export_csv_job_not_found(self, test_client, auth_headers):
        """Test CSV export with non-existent job."""
        fake_job_id = str(uuid.uuid4())

        response = test_client.get(
            f"/engarde/brand-analysis/{fake_job_id}/export/csv",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Analysis job not found" in response.json()["detail"]

    def test_export_csv_incomplete_analysis(self, test_client, db_session, test_user, auth_headers):
        """Test CSV export with incomplete analysis."""
        # Create incomplete job
        job = BrandAnalysisJob(
            id=uuid.uuid4(),
            user_id=test_user.id,
            questionnaire={"brand_name": "Test"},
            status=AnalysisStatus.ANALYZING,
            progress=50
        )
        db_session.add(job)
        db_session.commit()

        response = test_client.get(
            f"/engarde/brand-analysis/{job.id}/export/csv",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "Analysis is not complete" in response.json()["detail"]

    def test_export_csv_filename_format(self, test_client, completed_analysis_job, auth_headers):
        """Test CSV export filename format."""
        job_id = str(completed_analysis_job.id)

        response = test_client.get(
            f"/engarde/brand-analysis/{job_id}/export/csv",
            headers=auth_headers
        )

        disposition = response.headers["content-disposition"]
        assert "onside_analysis_" in disposition
        assert "test_marketing_tools" in disposition
        assert job_id[:8] in disposition
        assert ".csv" in disposition


class TestCampaignExport:
    """Test campaign format export endpoint."""

    def test_export_campaign_success(self, test_client, completed_analysis_job, auth_headers):
        """Test successful campaign format export."""
        job_id = str(completed_analysis_job.id)

        response = test_client.get(
            f"/engarde/brand-analysis/{job_id}/export/campaign",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify campaign structure
        assert data["campaign_name"] == "Brand Analysis - Test Marketing Tools"
        assert data["platform"] == "onside_analysis"
        assert data["import_source"] == "onside_brand_analysis"
        assert "Automated brand digital footprint" in data["description"]
        assert data["campaign_objective"] == "Brand digital footprint analysis and SEO strategy"
        assert data["is_active"] is False
        assert data["currency"] == "USD"
        assert data["budget"] is None

        # Verify tags
        assert "onside_analysis" in data["tags"]
        assert "brand_audit" in data["tags"]
        assert "seo_research" in data["tags"]

        # Verify metadata
        metadata = data["import_metadata"]
        assert metadata["onside_job_id"] == job_id
        assert metadata["brand_name"] == "Test Marketing Tools"
        assert metadata["brand_website"] == "https://www.testmarketing.com"
        assert metadata["industry"] == "SaaS Marketing"
        assert metadata["total_keywords"] == 3
        assert metadata["total_competitors"] == 2
        assert metadata["total_opportunities"] == 2

        # Verify keywords array
        assert len(data["keywords"]) == 3
        kw1 = data["keywords"][0]
        assert kw1["keyword_text"] == "email marketing automation"
        assert kw1["search_volume"] == 12000
        assert kw1["competition_score"] == 65.5
        assert kw1["priority_level"] in ["high", "medium", "low"]
        assert kw1["source"] == "onside_analysis"
        assert "metadata" in kw1
        assert kw1["metadata"]["onside_id"] is not None

        # Verify competitors array
        assert len(data["competitors"]) == 2
        comp1 = data["competitors"][0]
        assert comp1["domain"] == "mailchimp.com"
        assert comp1["competitor_name"] == "Mailchimp"
        assert comp1["competitor_type"] == "direct"  # mapped from "primary"
        assert comp1["source"] == "onside_analysis"

        # Verify opportunities array
        assert len(data["content_opportunities"]) == 2
        opp1 = data["content_opportunities"][0]
        assert opp1["title"] == "Email segmentation best practices"
        assert opp1["content_type"] == "guide"
        assert opp1["priority"] == "high"
        assert opp1["estimated_traffic"] == 5000
        assert opp1["difficulty_score"] == 45.0

    def test_export_campaign_data_transformation(self, test_client, completed_analysis_job, auth_headers):
        """Test that data transformation is applied correctly."""
        job_id = str(completed_analysis_job.id)

        response = test_client.get(
            f"/engarde/brand-analysis/{job_id}/export/campaign",
            headers=auth_headers
        )

        data = response.json()

        # Test keyword enrichments
        kw = data["keywords"][0]
        assert "cpc_estimate" in kw  # Should be enriched
        assert "intent_type" in kw  # Should be inferred
        assert "target_position" in kw  # Should be calculated

        # Test competitor category mapping
        comp = data["competitors"][0]
        assert comp["competitor_type"] in ["direct", "indirect", "emerging", "aspirational"]
        assert comp["strength_score"] is not None  # Converted from relevance_score

        # Test opportunity format mapping
        opp = data["content_opportunities"][0]
        assert opp["content_type"] in [
            "blog_post", "guide", "video", "infographic", "case_study", "whitepaper"
        ]

    def test_export_campaign_invalid_job_id(self, test_client, auth_headers):
        """Test campaign export with invalid job ID."""
        response = test_client.get(
            "/engarde/brand-analysis/invalid-uuid/export/campaign",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "Invalid job ID format" in response.json()["detail"]

    def test_export_campaign_json_serializable(self, test_client, completed_analysis_job, auth_headers):
        """Test that campaign export is fully JSON serializable."""
        job_id = str(completed_analysis_job.id)

        response = test_client.get(
            f"/engarde/brand-analysis/{job_id}/export/campaign",
            headers=auth_headers
        )

        # Should not raise exception
        json_str = json.dumps(response.json())
        assert len(json_str) > 0

        # Should be re-parseable
        reparsed = json.loads(json_str)
        assert reparsed["campaign_name"] == "Brand Analysis - Test Marketing Tools"


class TestConfirmWithExport:
    """Test enhanced confirm endpoint with export functionality."""

    def test_confirm_with_csv_export(self, test_client, completed_analysis_job, auth_headers):
        """Test confirm endpoint with CSV export format."""
        job_id = str(completed_analysis_job.id)

        response = test_client.post(
            f"/engarde/brand-analysis/{job_id}/confirm",
            headers=auth_headers,
            json={
                "selected_keywords": [1, 2],
                "selected_competitors": [1],
                "export_format": "csv"
            }
        )

        # Should return CSV file
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_confirm_with_campaign_export(self, test_client, completed_analysis_job, auth_headers):
        """Test confirm endpoint with campaign JSON export format."""
        job_id = str(completed_analysis_job.id)

        response = test_client.post(
            f"/engarde/brand-analysis/{job_id}/confirm",
            headers=auth_headers,
            json={
                "selected_keywords": [1, 2],
                "selected_competitors": [1],
                "export_format": "campaign_json"
            }
        )

        # Should return campaign JSON
        assert response.status_code == 200
        data = response.json()
        assert "campaign_name" in data
        assert "keywords" in data

    def test_confirm_without_export(self, test_client, completed_analysis_job, auth_headers):
        """Test confirm endpoint without export (normal import)."""
        job_id = str(completed_analysis_job.id)

        response = test_client.post(
            f"/engarde/brand-analysis/{job_id}/confirm",
            headers=auth_headers,
            json={
                "selected_keywords": [1, 2],
                "selected_competitors": [1],
                "tenant_uuid": str(uuid.uuid4()),
                "import_strategy": "skip"
            }
        )

        # Should perform import
        assert response.status_code == 200
        data = response.json()
        assert "imported" in data
        assert "batch_id" in data


class TestIntegrationFlow:
    """Test complete integration flow."""

    def test_full_export_to_engarde_flow(
        self,
        test_client,
        completed_analysis_job,
        auth_headers
    ):
        """Test complete flow from analysis to En Garde campaign creation."""
        job_id = str(completed_analysis_job.id)

        # Step 1: Get campaign export
        export_response = test_client.get(
            f"/engarde/brand-analysis/{job_id}/export/campaign",
            headers=auth_headers
        )
        assert export_response.status_code == 200
        campaign_data = export_response.json()

        # Step 2: Verify campaign data is ready for En Garde
        assert campaign_data["campaign_name"]
        assert campaign_data["platform"] == "onside_analysis"
        assert len(campaign_data["keywords"]) > 0

        # Step 3: Simulate POST to En Garde (would be actual API call in production)
        # This is what the frontend would do:
        # POST /campaign-spaces with campaign_data
        assert "import_metadata" in campaign_data
        assert campaign_data["import_metadata"]["onside_job_id"] == job_id

    def test_csv_download_flow(self, test_client, completed_analysis_job, auth_headers):
        """Test CSV download flow for manual import."""
        job_id = str(completed_analysis_job.id)

        # Step 1: Download CSV
        response = test_client.get(
            f"/engarde/brand-analysis/{job_id}/export/csv",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Step 2: Verify CSV can be parsed
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        assert len(rows) > 0

        # Step 3: User would upload this CSV to En Garde CSV import page
        # CSV format is compatible with En Garde's expected schema


# Pytest configuration
@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    # In real tests, generate actual JWT token
    return {"Authorization": f"Bearer test_token_{test_user.id}"}


@pytest.fixture
def db_session():
    """Create database session for tests."""
    # This would use your test database configuration
    # For now, this is a placeholder
    pass
