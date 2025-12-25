import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone as tz, UTC
from src.models.content import Content
from src.models.engagement import EngagementMetrics
from src.services.ai.content_recommendations import ContentRecommendationService

def test_generate_recommendations_success(auth_client, db_session, mock_user, mock_token):
    # Create historical content data
    contents = []
    for i in range(5):
        content = Content(
            user_id=mock_user.id,
            content_type="article",
            title=f"Test Article {i}",
            content_metadata={"content": "Test content"},
            created_at=datetime.now(UTC) - timedelta(days=30-i)
        )
        contents.append(content)
    
    db_session.add_all(contents)
    db_session.commit()
    
    # Add engagement metrics
    metrics = []
    for content in contents:
        metrics.extend([
            EngagementMetrics(
                content_id=content.id,
                metric_type="likes",
                value=100,
                source="twitter",
                timestamp=content.created_at + timedelta(days=1)
            ),
            EngagementMetrics(
                content_id=content.id,
                metric_type="shares",
                value=50,
                source="twitter",
                timestamp=content.created_at + timedelta(days=1)
            )
        ])
    
    db_session.add_all(metrics)
    db_session.commit()
    
    response = auth_client.post(
        "/api/recommendations/generate",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert all("score" in rec and "content" in rec for rec in data["recommendations"])

def test_generate_recommendations_with_filters(auth_client, db_session, mock_user, mock_token):
    # Create content of different types
    contents = [
        Content(
            user_id=mock_user.id,
            content_type="article",
            title="Test Article",
            content_metadata={"content": "Test content"},
            created_at=datetime.now(UTC) - timedelta(days=15)
        ),
        Content(
            user_id=mock_user.id,
            content_type="video",
            title="Test Video",
            content_metadata={"content": "Test content"},
            created_at=datetime.now(UTC) - timedelta(days=10)
        )
    ]
    db_session.add_all(contents)
    db_session.commit()
    
    # Add metrics for different platforms
    metrics = [
        EngagementMetrics(
            content_id=contents[0].id,
            metric_type="likes",
            value=100,
            source="twitter",
            timestamp=datetime.now(UTC) - timedelta(days=14)
        ),
        EngagementMetrics(
            content_id=contents[1].id,
            metric_type="views",
            value=200,
            source="youtube",
            timestamp=datetime.now(UTC) - timedelta(days=9)
        )
    ]
    db_session.add_all(metrics)
    db_session.commit()
    
    # Test with content type and platform filters
    response = auth_client.post(
        "/api/recommendations/generate?content_type=video&target_platform=youtube",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert all(rec["content"]["content_type"] == "video" for rec in data["recommendations"])

def test_generate_recommendations_custom_count(auth_client, db_session, mock_user, mock_token):
    response = auth_client.post(
        "/api/recommendations/generate?count=3",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 3

def test_generate_recommendations_invalid_count(auth_client, mock_token):
    response = auth_client.post(
        "/api/recommendations/generate?count=25",  # More than maximum allowed
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data

def test_generate_recommendations_no_historical_data(auth_client, mock_token):
    response = auth_client.post(
        "/api/recommendations/generate",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) == 0

def test_generate_recommendations_with_target_audience(auth_client, db_session, mock_user, mock_token):
    response = auth_client.post(
        "/api/recommendations/generate?target_audience=tech_professionals",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "recommendations" in data

def test_generate_recommendations_unauthorized(client):
    response = client.post("/api/recommendations/generate")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
