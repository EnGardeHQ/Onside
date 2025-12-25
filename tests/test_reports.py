import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from dateutil import tz as dtz
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.services.analytics import AnalyticsService
from src.services.competitive_analysis import CompetitiveAnalysisService

def test_generate_kpi_report_success(auth_client, db_session, mock_user, mock_token):
    # Create test content
    content = Content(
        user_id=mock_user.id,
        content_type="article",
        title="Test Article",
        content_metadata={"content": "Test content"},
        created_at=datetime.now(timezone.utc) - timedelta(days=15)
    )
    db_session.add(content)
    db_session.commit()
    
    # Add various types of metrics
    metrics = [
        EngagementMetrics(
            content_id=content.id,
            metric_type="engagement",
            value=100,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        ),
        EngagementMetrics(
            content_id=content.id,
            metric_type="reach",
            value=1000,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        ),
        EngagementMetrics(
            content_id=content.id,
            metric_type="conversion",
            value=10,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        )
    ]
    db_session.add_all(metrics)
    db_session.commit()
    
    response = auth_client.get(
        "/api/reports/kpi",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "metrics" in data
    assert "engagement" in data["metrics"]
    assert "reach" in data["metrics"]
    assert "conversion" in data["metrics"]

def test_generate_kpi_report_with_filters(auth_client, db_session, mock_user, mock_token):
    # Create test content with different types
    contents = [
        Content(
            user_id=mock_user.id,
            content_type="article",
            title="Test Article",
            content_metadata={"content": "Test content"},
            created_at=datetime.now(timezone.utc) - timedelta(days=15)
        ),
        Content(
            user_id=mock_user.id,
            content_type="video",
            title="Test Video",
            content_metadata={"content": "Test content"},
            created_at=datetime.now(timezone.utc) - timedelta(days=10)
        )
    ]
    db_session.add_all(contents)
    db_session.commit()
    
    # Add metrics for both contents
    metrics = []
    for content in contents:
        metrics.extend([
            EngagementMetrics(
                content_id=content.id,
                metric_type="engagement",
                value=100,
                source="twitter",
                timestamp=datetime.now(timezone.utc) - timedelta(days=9)
            ),
            EngagementMetrics(
                content_id=content.id,
                metric_type="reach",
                value=1000,
                source="twitter",
                timestamp=datetime.now(timezone.utc) - timedelta(days=9)
            )
        ])
    db_session.add_all(metrics)
    db_session.commit()
    
    # Test with content type filter
    response = auth_client.get(
        "/api/reports/kpi?content_type=article",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "metrics" in data
    assert data["metrics"]["engagement"]["total"] == 100
    assert data["metrics"]["reach"]["total"] == 1000

def test_generate_kpi_report_date_range(auth_client, db_session, mock_user, mock_token):
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    end_date = datetime.now(timezone.utc)
    
    from urllib.parse import quote
    start_date_str = quote(start_date.isoformat())
    end_date_str = quote(end_date.isoformat())
    
    print(f"\nStart date: {start_date_str}")
    print(f"End date: {end_date_str}")
    
    response = auth_client.get(
        f"/api/reports/kpi?start_date={start_date_str}&end_date={end_date_str}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    print(f"Response content: {response.content}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "metrics" in data
    assert "date_range" in data

def test_generate_competitive_report_success(auth_client, db_session, mock_user, mock_token, mock_competitor):
    # Create content for both user and competitor
    user_content = Content(
        user_id=mock_user.id,
        content_type="article",
        title="User Article",
        content_metadata={"content": "Test content"},
        created_at=datetime.now(timezone.utc) - timedelta(days=15)
    )
    competitor_content = Content(
        user_id=mock_competitor.id,
        content_type="article",
        title="Competitor Article",
        content_metadata={"content": "Test content"},
        created_at=datetime.now(timezone.utc) - timedelta(days=15)
    )
    db_session.add_all([user_content, competitor_content])
    db_session.commit()
    
    # Add metrics for both contents
    metrics = [
        EngagementMetrics(
            content_id=user_content.id,
            metric_type="engagement",
            value=100,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        ),
        EngagementMetrics(
            content_id=competitor_content.id,
            metric_type="engagement",
            value=150,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        )
    ]
    db_session.add_all(metrics)
    db_session.commit()
    
    response = auth_client.get(
        f"/api/reports/competitive?competitor_ids={mock_competitor.id}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "competitor_metrics" in data
    assert str(mock_competitor.id) in data["competitor_metrics"]
    assert data["competitor_metrics"][str(mock_competitor.id)]["engagement"]["total"] == 150

def test_generate_competitive_report_timeframe(auth_client, mock_token, mock_competitor):
    response = auth_client.get(
        f"/api/reports/competitive?competitor_ids={mock_competitor.id}&timeframe=90d",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "competitor_metrics" in data
    assert "timeframe" in data

def test_generate_competitive_report_invalid_timeframe(auth_client, mock_token, mock_competitor):
    response = auth_client.get(
        f"/api/reports/competitive?competitor_ids={mock_competitor.id}&timeframe=invalid",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data

def test_generate_kpi_report_unauthorized(client):
    response = client.get("/api/reports/kpi")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_generate_competitive_report_unauthorized(client):
    response = client.get("/api/reports/competitive?competitor_ids=1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
