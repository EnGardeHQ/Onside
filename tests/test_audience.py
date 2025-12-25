import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.services.ai.audience_intelligence import AudienceIntelligenceService

def test_get_audience_insights_success(auth_client, db_session, mock_user, mock_token):
    # Create test content and engagement data
    content = Content(
        user_id=mock_user.id,
        content_type="article",
        title="Test Article",
        content_metadata={"content": "Test content"},
        created_at=datetime.now(timezone.utc) - timedelta(days=15)
    )
    db_session.add(content)
    db_session.commit()

    metrics = [
        EngagementMetrics(
            content_id=content.id,
            metric_type="likes",
            value=100,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        ),
        EngagementMetrics(
            content_id=content.id,
            metric_type="shares",
            value=50,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=13)
        )
    ]
    db_session.add_all(metrics)
    db_session.commit()

    response = auth_client.get(
        "/api/audience/insights",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"Error response: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check response structure
    assert "insights" in data
    assert "metadata" in data
    assert "time_period" in data
    
    # Check insights content
    insights = data["insights"]
    assert "engagement_patterns" in insights
    assert "content_performance" in insights
    assert "audience_segments" in insights
    
    # Check metadata
    metadata = data["metadata"]
    assert metadata["content_count"] == 1
    assert metadata["platforms_analyzed"] == ["twitter"]
    assert metadata["total_engagements"] == 150.0

def test_get_audience_insights_with_filters(auth_client, db_session, mock_user, mock_token):
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

    # Add metrics for both content items
    metrics = [
        # Metrics for article
        EngagementMetrics(
            content_id=contents[0].id,
            metric_type="likes",
            value=100,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        ),
        EngagementMetrics(
            content_id=contents[0].id,
            metric_type="shares",
            value=50,
            source="twitter",
            timestamp=datetime.now(timezone.utc) - timedelta(days=13)
        ),
        # Metrics for video
        EngagementMetrics(
            content_id=contents[1].id,
            metric_type="views",
            value=200,
            source="youtube",
            timestamp=datetime.now(timezone.utc) - timedelta(days=9)
        ),
        EngagementMetrics(
            content_id=contents[1].id,
            metric_type="likes",
            value=75,
            source="youtube",
            timestamp=datetime.now(timezone.utc) - timedelta(days=8)
        )
    ]
    db_session.add_all(metrics)
    db_session.commit()

    # Test with content type filter
    response = auth_client.get(
        "/api/audience/insights?content_type=article",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"Error response: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "insights" in data
    assert "metadata" in data
    assert "time_period" in data
    
    # Check insights content
    insights = data["insights"]
    assert "engagement_patterns" in insights
    assert "content_performance" in insights
    assert "audience_segments" in insights
    
    # Check metadata
    metadata = data["metadata"]
    assert metadata["content_count"] == 1
    assert metadata["platforms_analyzed"] == ["twitter"]
    assert metadata["total_engagements"] == 150.0  # 100 likes + 50 shares

def test_get_audience_insights_date_range(auth_client, db_session, mock_user, mock_token):
    # Create test content with different dates
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    mid_date = datetime.now(timezone.utc) - timedelta(days=20)
    end_date = datetime.now(timezone.utc) - timedelta(days=15)

    # Create test content within the date range
    content = Content(
        user_id=mock_user.id,
        content_type="article",
        title="Test Article",
        content_metadata={"content": "Test content"},
        created_at=mid_date
    )
    db_session.add(content)
    db_session.commit()

    # Add engagement metrics
    metrics = [
        EngagementMetrics(
            content_id=content.id,
            metric_type="likes",
            value=100,
            source="twitter",
            timestamp=mid_date + timedelta(days=1)
        ),
        EngagementMetrics(
            content_id=content.id,
            metric_type="shares",
            value=50,
            source="twitter",
            timestamp=mid_date + timedelta(days=2)
        )
    ]
    db_session.add_all(metrics)
    db_session.commit()

    # Format dates in ISO format with Z timezone indicator
    start_date_str = start_date.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date_str = end_date.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")

    response = auth_client.get(
        f"/api/audience/insights?start_date={start_date_str}&end_date={end_date_str}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"Error response: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "insights" in data
    assert "metadata" in data
    assert "time_period" in data

    # Check insights content
    insights = data["insights"]
    assert "engagement_patterns" in insights
    assert "content_performance" in insights
    assert "audience_segments" in insights

    # Check metadata
    metadata = data["metadata"]
    assert metadata["content_count"] == 1
    assert metadata["platforms_analyzed"] == ["twitter"]
    assert metadata["total_engagements"] == 150.0  # 100 likes + 50 shares

def test_get_audience_trends_success(auth_client, db_session, mock_user, mock_token):
    # Create test content and metrics over time
    lookback_days = 30
    now = datetime.now(timezone.utc)
    content_created_at = now - timedelta(days=lookback_days - 1)  # Within the lookback period
    
    content = Content(
        user_id=mock_user.id,
        content_type="article",
        title="Test Article",
        content_metadata={"content": "Test content"},
        created_at=content_created_at
    )
    db_session.add(content)
    db_session.commit()

    # Add metrics for different days
    metrics = []
    for days_ago in range(lookback_days - 1, 0, -1):
        metric_time = now - timedelta(days=days_ago)
        metrics.append(
            EngagementMetrics(
                content_id=content.id,
                metric_type="likes",
                value=100 + days_ago,
                source="twitter",
                timestamp=metric_time
            )
        )
    db_session.add_all(metrics)
    db_session.commit()

    response = auth_client.get(
        f"/api/audience/trends?lookback_days={lookback_days}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"Error response: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "trends" in data
    assert "time_period" in data
    assert "metadata" in data

    # Check trends data
    trends = data["trends"]
    assert "trend_patterns" in trends
    assert "emerging_trends" in trends
    assert "confidence" in trends
    assert "recommendations" in trends

    # Check metadata
    metadata = data["metadata"]
    assert metadata["content_analyzed"] == 1
    assert metadata["platforms"] == ["twitter"]
    assert "trend_confidence" in metadata

def test_get_audience_trends_no_data(auth_client, mock_token):
    response = auth_client.get(
        "/api/audience/trends",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    if response.status_code != status.HTTP_404_NOT_FOUND:
        print(f"Error response: {response.json()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "No audience data found" in data["detail"]

def test_get_audience_trends_invalid_lookback(auth_client, mock_token):
    response = auth_client.get(
        "/api/audience/trends?lookback_days=0",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    if response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY:
        print(f"Error response: {response.json()}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert len(data["detail"]) > 0
    error = data["detail"][0]
    assert error["loc"] == ["query", "lookback_days"]
    assert "ensure this value is greater than or equal to 1" in error["msg"]

def test_get_audience_insights_unauthorized(client):
    response = client.get("/api/audience/insights")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_audience_trends_unauthorized(client):
    response = client.get("/api/audience/trends")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
