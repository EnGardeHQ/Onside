"""Unit tests for Brand Discovery Chat Service."""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from src.services.ai.brand_discovery_chat import BrandDiscoveryChatService
from src.models.brand_discovery_chat import BrandDiscoveryChatSession
from src.schemas.brand_discovery_chat import (
    ChatStartResponse,
    ChatMessageResponse,
    ConversationState,
    ExtractedData,
    BrandAnalysisQuestionnaire,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock(spec=Session)
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    with patch('src.services.ai.brand_discovery_chat.LLMService') as mock:
        yield mock


@pytest.fixture
def service(mock_db):
    """Create service instance with mocked dependencies."""
    return BrandDiscoveryChatService(mock_db)


class TestStartConversation:
    """Test suite for starting conversations."""

    def test_start_conversation_creates_session(self, service, mock_db):
        """Test that starting a conversation creates a new session."""
        # Arrange
        user_id = "test_user_123"

        # Mock the session creation
        def add_side_effect(obj):
            obj.session_id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()

        mock_db.add.side_effect = add_side_effect

        # Act
        response = service.start_conversation(user_id)

        # Assert
        assert isinstance(response, ChatStartResponse)
        assert response.session_id is not None
        assert "brand or company name" in response.first_message.lower()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_start_conversation_initial_message(self, service, mock_db):
        """Test that the initial message is appropriate."""
        # Arrange
        user_id = "test_user_123"

        # Mock the session creation
        def add_side_effect(obj):
            obj.session_id = uuid.uuid4()

        mock_db.add.side_effect = add_side_effect

        # Act
        response = service.start_conversation(user_id)

        # Assert
        assert "Hi!" in response.first_message or "Hello" in response.first_message
        assert "brand" in response.first_message.lower()
        assert "name" in response.first_message.lower()


class TestSendMessage:
    """Test suite for sending messages."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session object."""
        session = BrandDiscoveryChatSession(
            session_id=uuid.uuid4(),
            user_id="test_user_123",
            messages=[],
            extracted_data={},
            status='active'
        )
        return session

    @pytest.mark.asyncio
    async def test_send_message_extracts_brand_name(self, service, mock_db, mock_session):
        """Test that sending a message extracts brand name."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Mock LLM response
        with patch.object(service, '_generate_response', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = (
                "Great! What's your primary website?",
                {"brand_name": "Acme Corp"}
            )

            # Act
            response = await service.send_message(mock_session.session_id, "Acme Corp")

            # Assert
            assert isinstance(response, ChatMessageResponse)
            assert response.extracted_data.brand_name == "Acme Corp"
            assert response.progress_pct > 0

    @pytest.mark.asyncio
    async def test_send_message_updates_progress(self, service, mock_db, mock_session):
        """Test that progress is calculated correctly."""
        # Arrange
        mock_session.extracted_data = {
            "brand_name": "Acme Corp",
            "website": "acmecorp.com"
        }
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Mock LLM response
        with patch.object(service, '_generate_response', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = (
                "What industry are you in?",
                {"industry": "SaaS"}
            )

            # Act
            response = await service.send_message(mock_session.session_id, "We're in SaaS")

            # Assert
            assert response.progress_pct > 0
            assert response.progress_pct <= 100

    @pytest.mark.asyncio
    async def test_send_message_marks_complete_when_done(self, service, mock_db, mock_session):
        """Test that session is marked complete when all required fields collected."""
        # Arrange
        mock_session.extracted_data = {
            "brand_name": "Acme Corp",
            "website": "acmecorp.com",
            "industry": "SaaS",
        }
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Mock LLM response with final required field
        with patch.object(service, '_generate_response', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = (
                "Perfect! I have everything I need.",
                {"products_services": "Email marketing software"}
            )

            # Act
            response = await service.send_message(
                mock_session.session_id,
                "Email marketing software"
            )

            # Assert
            assert response.is_complete is True
            assert mock_session.status == 'completed'

    @pytest.mark.asyncio
    async def test_send_message_inactive_session_raises_error(self, service, mock_db, mock_session):
        """Test that sending message to inactive session raises error."""
        # Arrange
        mock_session.status = 'completed'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Act & Assert
        with pytest.raises(ValueError, match="not active"):
            await service.send_message(mock_session.session_id, "test message")


class TestConversationState:
    """Test suite for getting conversation state."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session with partial data."""
        return BrandDiscoveryChatSession(
            session_id=uuid.uuid4(),
            user_id="test_user_123",
            messages=[],
            extracted_data={
                "brand_name": "Acme Corp",
                "website": "acmecorp.com"
            },
            status='active'
        )

    def test_get_conversation_state_returns_progress(self, service, mock_db, mock_session):
        """Test that conversation state includes progress."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Act
        state = service.get_conversation_state(mock_session.session_id)

        # Assert
        assert isinstance(state, ConversationState)
        assert state.progress_pct > 0
        assert state.progress_pct < 100  # Not complete yet

    def test_get_conversation_state_shows_missing_fields(self, service, mock_db, mock_session):
        """Test that missing required fields are listed."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Act
        state = service.get_conversation_state(mock_session.session_id)

        # Assert
        assert 'industry' in state.missing_fields
        assert 'products_services' in state.missing_fields
        assert 'brand_name' not in state.missing_fields  # Already collected


class TestFinalizeConversation:
    """Test suite for finalizing conversations."""

    @pytest.fixture
    def complete_session(self):
        """Create a session with all required data."""
        return BrandDiscoveryChatSession(
            session_id=uuid.uuid4(),
            user_id="test_user_123",
            messages=[],
            extracted_data={
                "brand_name": "Acme Corp",
                "website": "acmecorp.com",
                "industry": "SaaS/Email Marketing",
                "products_services": "Email automation and analytics",
                "competitors": ["Mailchimp", "Constant Contact"],
                "keywords": ["email marketing", "marketing automation"]
            },
            status='active'
        )

    def test_finalize_complete_session_succeeds(self, service, mock_db, complete_session):
        """Test that finalization succeeds with complete data."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = complete_session

        # Act
        response = service.finalize_conversation(complete_session.session_id)

        # Assert
        assert isinstance(response.questionnaire, BrandAnalysisQuestionnaire)
        assert response.questionnaire.brand_name == "Acme Corp"
        assert response.questionnaire.website.startswith("https://")
        assert complete_session.status == 'completed'

    def test_finalize_incomplete_session_raises_error(self, service, mock_db):
        """Test that finalization fails with missing required fields."""
        # Arrange
        incomplete_session = BrandDiscoveryChatSession(
            session_id=uuid.uuid4(),
            user_id="test_user_123",
            messages=[],
            extracted_data={
                "brand_name": "Acme Corp",
                "website": "acmecorp.com"
                # Missing industry and products_services
            },
            status='active'
        )
        mock_db.query.return_value.filter.return_value.first.return_value = incomplete_session

        # Act & Assert
        with pytest.raises(ValueError, match="missing required fields"):
            service.finalize_conversation(incomplete_session.session_id)


class TestDataExtraction:
    """Test suite for data extraction and cleaning."""

    def test_clean_url_removes_protocol(self, service):
        """Test that URLs are cleaned properly."""
        # Test cases
        test_cases = [
            ("https://example.com", "example.com"),
            ("http://www.example.com", "example.com"),
            ("example.com/", "example.com"),
            ("example.com/path", "example.com"),
            ("EXAMPLE.COM", "example.com"),
        ]

        for input_url, expected in test_cases:
            result = service._clean_url(input_url)
            assert result == expected, f"Failed for {input_url}: expected {expected}, got {result}"

    def test_clean_extracted_data_handles_lists(self, service):
        """Test that list fields are properly handled."""
        # Arrange
        data = {
            "competitors": "Mailchimp, Constant Contact and SendGrid",
            "keywords": "email marketing, automation",
            "brand_name": "Acme Corp"
        }

        # Act
        cleaned = service._clean_extracted_data(data)

        # Assert
        assert isinstance(cleaned['competitors'], list)
        assert len(cleaned['competitors']) == 3
        assert 'Mailchimp' in cleaned['competitors']
        assert 'SendGrid' in cleaned['competitors']

        assert isinstance(cleaned['keywords'], list)
        assert len(cleaned['keywords']) == 2

    def test_clean_extracted_data_removes_empty_values(self, service):
        """Test that empty values are filtered out."""
        # Arrange
        data = {
            "brand_name": "Acme Corp",
            "website": "",
            "industry": None,
            "keywords": []
        }

        # Act
        cleaned = service._clean_extracted_data(data)

        # Assert
        assert 'brand_name' in cleaned
        assert 'website' not in cleaned
        assert 'industry' not in cleaned
        assert 'keywords' not in cleaned

    def test_calculate_progress_weights_fields_correctly(self, service):
        """Test that progress calculation uses proper weights."""
        # Only required fields
        data_required_only = {
            "brand_name": "Acme Corp",
            "website": "acme.com",
            "industry": "SaaS",
            "products_services": "Email tools"
        }

        # With optional fields
        data_with_optional = {
            **data_required_only,
            "competitors": ["Mailchimp"],
            "keywords": ["email marketing"],
            "target_markets": ["US"],
            "marketing_goals": "Increase organic traffic"
        }

        progress_required = service._calculate_progress(data_required_only)
        progress_with_optional = service._calculate_progress(data_with_optional)

        # Required fields should give substantial progress
        assert progress_required >= 50

        # Adding optional fields should increase progress
        assert progress_with_optional > progress_required

    def test_get_missing_required_fields(self, service):
        """Test identification of missing required fields."""
        # Arrange
        data = {
            "brand_name": "Acme Corp",
            "website": "acme.com"
            # Missing: industry, products_services
        }

        # Act
        missing = service._get_missing_required_fields(data)

        # Assert
        assert 'industry' in missing
        assert 'products_services' in missing
        assert 'brand_name' not in missing
        assert 'website' not in missing


class TestFallbackExtraction:
    """Test suite for rule-based fallback extraction."""

    def test_fallback_extraction_detects_url(self, service):
        """Test that fallback can extract URLs."""
        # Arrange
        current_data = {}
        messages = [
            "Our website is techstartup.io",
            "https://example.com is our site",
            "Find us at www.company.co.uk"
        ]

        for message in messages:
            # Act
            response, extracted = service._fallback_extraction(current_data, message)

            # Assert
            assert 'website' in extracted
            assert isinstance(extracted['website'], str)
            assert len(extracted['website']) > 0

    def test_fallback_extraction_brand_name_from_short_message(self, service):
        """Test that short messages are treated as brand names."""
        # Arrange
        current_data = {}
        message = "Acme Corp"

        # Act
        response, extracted = service._fallback_extraction(current_data, message)

        # Assert
        assert 'brand_name' in extracted
        assert extracted['brand_name'] == "Acme Corp"

    def test_fallback_asks_appropriate_next_question(self, service):
        """Test that fallback generates appropriate follow-up questions."""
        # Test progression through required fields
        test_cases = [
            ({}, "What's your brand or company name?"),
            ({"brand_name": "Acme"}, "What's your primary website URL?"),
            ({"brand_name": "Acme", "website": "acme.com"}, "What industry are you in?"),
            ({"brand_name": "Acme", "website": "acme.com", "industry": "SaaS"}, "What products or services do you offer?"),
        ]

        for current_data, expected_keyword in test_cases:
            response, _ = service._fallback_extraction(current_data, "test message")
            assert any(keyword in response.lower() for keyword in expected_keyword.lower().split())


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_session_not_found_raises_error(self, service, mock_db):
        """Test that accessing non-existent session raises error."""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        fake_session_id = uuid.uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            service.get_conversation_state(fake_session_id)

    def test_handles_correction_in_conversation(self, service, mock_db):
        """Test that corrections to previously provided info are handled."""
        # This would test scenarios like:
        # User: "acme.com"
        # AI: "Got it!"
        # User: "Actually, it's acme.co not .com"
        # AI: "Updated to acme.co"

        # Implementation would involve testing _generate_response with
        # correction-indicating patterns
        pass  # Placeholder for integration test

    @pytest.mark.asyncio
    async def test_handles_llm_failure_gracefully(self, service, mock_db):
        """Test that LLM failures fall back to rule-based extraction."""
        # Arrange
        mock_session = BrandDiscoveryChatSession(
            session_id=uuid.uuid4(),
            user_id="test_user_123",
            messages=[],
            extracted_data={},
            status='active'
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        # Mock LLM to fail
        with patch.object(service, '_generate_response', new_callable=AsyncMock) as mock_gen:
            mock_gen.side_effect = Exception("LLM service unavailable")

            # Mock fallback extraction
            with patch.object(service, '_fallback_extraction') as mock_fallback:
                mock_fallback.return_value = ("What's your website?", {"brand_name": "Acme"})

                # Act
                response = await service.send_message(mock_session.session_id, "Acme Corp")

                # Assert - should still work via fallback
                mock_fallback.assert_called_once()
