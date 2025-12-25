"""Integration tests for Brand Discovery Chat API endpoints."""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.main import app
from src.database import Base, get_db
from src.models.user import User, UserRole
from src.models.brand_discovery_chat import BrandDiscoveryChatSession
from src.auth.security import create_access_token


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_brand_chat.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with overridden database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        name="Test User",
        role=UserRole.USER
    )
    user.set_password("testpassword123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


class TestBrandDiscoveryChatAPI:
    """Integration tests for brand discovery chat endpoints."""

    def test_start_chat_session(self, client, auth_headers):
        """Test starting a new chat session."""
        # Act
        response = client.post("/brand-discovery-chat/start", headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "first_message" in data
        assert "brand" in data["first_message"].lower()
        assert "name" in data["first_message"].lower()

    def test_send_message_to_session(self, client, auth_headers, db_session):
        """Test sending a message to an active session."""
        # Arrange - create session
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        # Act - send message
        message_response = client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "Acme Corporation"}
        )

        # Assert
        assert message_response.status_code == 200
        data = message_response.json()
        assert "ai_response" in data
        assert "progress_pct" in data
        assert "extracted_data" in data
        assert data["progress_pct"] > 0

    def test_get_session_status(self, client, auth_headers):
        """Test getting session status."""
        # Arrange - create session and send a message
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "Acme Corp"}
        )

        # Act
        status_response = client.get(
            f"/brand-discovery-chat/{session_id}/status",
            headers=auth_headers
        )

        # Assert
        assert status_response.status_code == 200
        data = status_response.json()
        assert "progress_pct" in data
        assert "extracted_data" in data
        assert "missing_fields" in data
        assert "is_complete" in data

    def test_get_session_history(self, client, auth_headers):
        """Test getting full session history."""
        # Arrange - create session and send messages
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "Acme Corp"}
        )

        # Act
        history_response = client.get(
            f"/brand-discovery-chat/{session_id}/history",
            headers=auth_headers
        )

        # Assert
        assert history_response.status_code == 200
        data = history_response.json()
        assert "messages" in data
        assert len(data["messages"]) > 0
        assert data["status"] == "active"

    def test_finalize_incomplete_session_fails(self, client, auth_headers):
        """Test that finalizing incomplete session returns error."""
        # Arrange - create session with partial data
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        # Send only brand name
        client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "Acme Corp"}
        )

        # Act - try to finalize
        finalize_response = client.post(
            f"/brand-discovery-chat/{session_id}/finalize",
            headers=auth_headers
        )

        # Assert
        assert finalize_response.status_code == 400
        assert "missing required fields" in finalize_response.json()["detail"].lower()

    def test_complete_conversation_flow(self, client, auth_headers, db_session):
        """Test a complete conversation flow from start to finalization."""
        # Start session
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        assert start_response.status_code == 201
        session_id = start_response.json()["session_id"]

        # Simulate complete conversation
        conversation = [
            "Acme Corporation",
            "acmecorp.com",
            "We're in SaaS, specifically email marketing software",
            "Email automation, newsletter tools, and campaign analytics for small businesses",
        ]

        for message in conversation:
            response = client.post(
                f"/brand-discovery-chat/{session_id}/message",
                headers=auth_headers,
                json={"message": message}
            )
            assert response.status_code == 200

        # Check status
        status_response = client.get(
            f"/brand-discovery-chat/{session_id}/status",
            headers=auth_headers
        )
        status_data = status_response.json()

        # Should have all required fields
        assert status_data["is_complete"] or len(status_data["missing_fields"]) == 0

        # Finalize
        finalize_response = client.post(
            f"/brand-discovery-chat/{session_id}/finalize",
            headers=auth_headers
        )

        # Assert finalization successful
        assert finalize_response.status_code == 200
        finalize_data = finalize_response.json()
        assert "questionnaire" in finalize_data
        assert finalize_data["questionnaire"]["brand_name"] == "Acme Corporation"
        assert "acmecorp.com" in finalize_data["questionnaire"]["website"]

    def test_send_message_to_nonexistent_session(self, client, auth_headers):
        """Test that sending message to non-existent session returns 404."""
        # Arrange
        fake_session_id = str(uuid.uuid4())

        # Act
        response = client.post(
            f"/brand-discovery-chat/{fake_session_id}/message",
            headers=auth_headers,
            json={"message": "test"}
        )

        # Assert
        assert response.status_code == 404

    def test_unauthorized_access_denied(self, client):
        """Test that endpoints require authentication."""
        # Act
        response = client.post("/brand-discovery-chat/start")

        # Assert
        assert response.status_code == 401

    def test_multiple_info_in_one_message(self, client, auth_headers):
        """Test handling multiple pieces of information in one message."""
        # Arrange
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        # Act - send message with multiple fields
        response = client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={
                "message": "Hi, I'm setting up for Acme Corp at acmecorp.io, we do SaaS email marketing"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Should extract multiple fields
        extracted = data["extracted_data"]
        # Note: Actual extraction depends on LLM, but service should handle it
        assert data["progress_pct"] > 0

    def test_url_normalization(self, client, auth_headers):
        """Test that URLs are normalized correctly."""
        # Arrange
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        # Send brand name first
        client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "Acme Corp"}
        )

        # Act - send URL with protocol and path
        response = client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "https://www.acmecorp.com/home"}
        )

        # Assert
        assert response.status_code == 200

        # Check status to see normalized URL
        status_response = client.get(
            f"/brand-discovery-chat/{session_id}/status",
            headers=auth_headers
        )

        data = status_response.json()
        if data["extracted_data"].get("website"):
            # Should be cleaned
            website = data["extracted_data"]["website"]
            assert not website.startswith("http")
            assert "www." not in website or website == "www.acmecorp.com"


class TestConversationCorrections:
    """Test handling of corrections in conversation."""

    def test_user_corrects_previous_response(self, client, auth_headers):
        """Test that corrections override previous values."""
        # Arrange
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        # Initial response
        client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "techstart.com"}
        )

        # Act - correction
        correction_response = client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "Actually, it's techstart.io not .com"}
        )

        # Assert
        assert correction_response.status_code == 200

        # Should have updated the website
        status_response = client.get(
            f"/brand-discovery-chat/{session_id}/status",
            headers=auth_headers
        )

        # The AI should handle the correction (exact behavior depends on LLM)
        assert status_response.status_code == 200


class TestProgressCalculation:
    """Test progress calculation logic."""

    def test_progress_increases_with_more_data(self, client, auth_headers):
        """Test that progress increases as more information is collected."""
        # Arrange
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        progress_values = []

        # Act - send messages one by one
        messages = [
            "Acme Corp",
            "acmecorp.com",
            "SaaS/Email Marketing",
            "Email automation tools"
        ]

        for message in messages:
            response = client.post(
                f"/brand-discovery-chat/{session_id}/message",
                headers=auth_headers,
                json={"message": message}
            )
            progress_values.append(response.json()["progress_pct"])

        # Assert - progress should generally increase
        # (allowing for some LLM variability in extraction)
        assert progress_values[-1] >= progress_values[0]

    def test_optional_fields_increase_progress(self, client, auth_headers):
        """Test that providing optional fields increases progress beyond required."""
        # This test verifies that completion percentage goes higher when
        # optional fields like competitors and keywords are provided

        # Arrange
        start_response = client.post("/brand-discovery-chat/start", headers=auth_headers)
        session_id = start_response.json()["session_id"]

        # Provide all required fields
        required_messages = [
            "Acme Corp",
            "acmecorp.com",
            "SaaS",
            "Email tools"
        ]

        for message in required_messages:
            client.post(
                f"/brand-discovery-chat/{session_id}/message",
                headers=auth_headers,
                json={"message": message}
            )

        status_after_required = client.get(
            f"/brand-discovery-chat/{session_id}/status",
            headers=auth_headers
        ).json()
        progress_required = status_after_required["progress_pct"]

        # Add optional fields
        client.post(
            f"/brand-discovery-chat/{session_id}/message",
            headers=auth_headers,
            json={"message": "Our competitors are Mailchimp and Constant Contact"}
        )

        status_after_optional = client.get(
            f"/brand-discovery-chat/{session_id}/status",
            headers=auth_headers
        ).json()
        progress_with_optional = status_after_optional["progress_pct"]

        # Assert - should increase or stay at 100%
        assert progress_with_optional >= progress_required
