"""
Tests for Import Service

Comprehensive test suite for the En Garde Integration Import Service.
Tests cover data transformation, duplicate detection, import strategies,
validation, and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from decimal import Decimal
import uuid

from src.services.engarde_integration.import_service import (
    ImportService,
    ImportStrategy,
    ImportStatus,
    ImportStatistics,
    DuplicateMatch
)
from src.services.engarde_integration.data_transformer import (
    EnGardeDataTransformer,
    EnGardeKeywordSchema,
    EnGardeCompetitorSchema
)
from src.models.brand_analysis import (
    BrandAnalysisJob,
    DiscoveredKeyword,
    IdentifiedCompetitor,
    ContentOpportunity,
    AnalysisStatus,
    KeywordSource,
    CompetitorCategory
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_onside_db():
    """Mock Onside database session."""
    db = Mock()
    db.query = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def mock_engarde_db():
    """Mock En Garde database session."""
    db = Mock()
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.flush = Mock()
    return db


@pytest.fixture
def sample_job():
    """Sample brand analysis job."""
    return BrandAnalysisJob(
        id=uuid.uuid4(),
        user_id=1,
        questionnaire={"brand_name": "Test Brand"},
        status=AnalysisStatus.COMPLETED,
        progress=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )


@pytest.fixture
def sample_discovered_keywords():
    """Sample discovered keywords from Onside."""
    return [
        DiscoveredKeyword(
            id=1,
            job_id=uuid.uuid4(),
            keyword="email marketing",
            source=KeywordSource.NLP_EXTRACTION,
            search_volume=12000,
            difficulty=65.5,
            relevance_score=0.87,
            current_ranking=15,
            confirmed=False
        ),
        DiscoveredKeyword(
            id=2,
            job_id=uuid.uuid4(),
            keyword="marketing automation",
            source=KeywordSource.SERP_ANALYSIS,
            search_volume=8500,
            difficulty=72.0,
            relevance_score=0.92,
            current_ranking=None,
            confirmed=False
        ),
        DiscoveredKeyword(
            id=3,
            job_id=uuid.uuid4(),
            keyword="crm software",
            source=KeywordSource.WEBSITE_CONTENT,
            search_volume=15000,
            difficulty=78.3,
            relevance_score=0.76,
            current_ranking=22,
            confirmed=False
        )
    ]


@pytest.fixture
def sample_identified_competitors():
    """Sample identified competitors from Onside."""
    return [
        IdentifiedCompetitor(
            id=1,
            job_id=uuid.uuid4(),
            domain="mailchimp.com",
            name="Mailchimp",
            relevance_score=0.92,
            category=CompetitorCategory.PRIMARY,
            overlap_percentage=78.5,
            content_similarity=0.85,
            confirmed=False
        ),
        IdentifiedCompetitor(
            id=2,
            job_id=uuid.uuid4(),
            domain="hubspot.com",
            name="HubSpot",
            relevance_score=0.88,
            category=CompetitorCategory.PRIMARY,
            overlap_percentage=65.2,
            content_similarity=0.72,
            confirmed=False
        )
    ]


@pytest.fixture
def import_service(mock_onside_db):
    """Initialize import service for testing."""
    return ImportService(
        onside_db=mock_onside_db,
        engarde_db=None,
        use_api_import=True,
        engarde_api_client=Mock()
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_import_service_initialization_with_db():
    """Test service initialization with database connection."""
    onside_db = Mock()
    engarde_db = Mock()

    service = ImportService(
        onside_db=onside_db,
        engarde_db=engarde_db,
        use_api_import=False
    )

    assert service.onside_db == onside_db
    assert service.engarde_db == engarde_db
    assert service.use_api_import is False
    assert isinstance(service.transformer, EnGardeDataTransformer)


def test_import_service_initialization_with_api():
    """Test service initialization with API client."""
    onside_db = Mock()
    api_client = Mock()

    service = ImportService(
        onside_db=onside_db,
        use_api_import=True,
        engarde_api_client=api_client
    )

    assert service.onside_db == onside_db
    assert service.engarde_db is None
    assert service.use_api_import is True
    assert service.engarde_api_client == api_client


def test_import_service_initialization_fails_without_engarde_connection():
    """Test that initialization fails when no En Garde connection provided."""
    with pytest.raises(ValueError, match="Either engarde_db must be provided"):
        ImportService(
            onside_db=Mock(),
            use_api_import=False
        )


def test_import_service_initialization_fails_without_api_client():
    """Test that initialization fails when API mode but no client provided."""
    with pytest.raises(ValueError, match="engarde_api_client is required"):
        ImportService(
            onside_db=Mock(),
            use_api_import=True
        )


# ============================================================================
# DATA VALIDATION TESTS
# ============================================================================

def test_validate_job_success(import_service, mock_onside_db, sample_job):
    """Test successful job validation."""
    mock_onside_db.query.return_value.filter.return_value.first.return_value = sample_job

    job = import_service._validate_job(str(sample_job.id))

    assert job == sample_job
    mock_onside_db.query.assert_called_once()


def test_validate_job_invalid_uuid(import_service):
    """Test job validation with invalid UUID."""
    with pytest.raises(ValueError, match="Invalid job_id format"):
        import_service._validate_job("not-a-uuid")


def test_validate_job_not_found(import_service, mock_onside_db):
    """Test job validation when job doesn't exist."""
    mock_onside_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Brand analysis job not found"):
        import_service._validate_job(str(uuid.uuid4()))


def test_validate_import_data_success(import_service):
    """Test successful import data validation."""
    keywords = [
        EnGardeKeywordSchema(
            keyword_text="test keyword",
            search_volume=1000,
            competition_score=50.0,
            priority_level="medium",
            source="onside_analysis"
        )
    ]

    data = {"keywords": keywords, "competitors": [], "opportunities": []}
    tenant_uuid = str(uuid.uuid4())

    result = import_service.validate_import_data(data, tenant_uuid)

    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    assert result["quality_score"] > 0


def test_validate_import_data_invalid_structure(import_service):
    """Test validation with invalid data structure."""
    result = import_service.validate_import_data("not a dict")

    assert result["is_valid"] is False
    assert "Data must be a dictionary" in result["errors"]
    assert result["quality_score"] == 0


def test_validate_import_data_invalid_tenant_uuid(import_service):
    """Test validation with invalid tenant UUID."""
    data = {"keywords": [], "competitors": [], "opportunities": []}

    result = import_service.validate_import_data(data, "invalid-uuid")

    assert result["is_valid"] is False
    assert any("Invalid tenant_uuid format" in err for err in result["errors"])


# ============================================================================
# DATA RETRIEVAL TESTS
# ============================================================================

def test_retrieve_selected_items_keywords_only(
    import_service,
    mock_onside_db,
    sample_discovered_keywords
):
    """Test retrieving only selected keywords."""
    job_id = str(uuid.uuid4())
    user_selections = {
        "selected_keywords": [1, 2],
        "selected_competitors": []
    }

    # Mock query for keywords
    mock_query = Mock()
    mock_onside_db.query.return_value = mock_query
    mock_query.filter.return_value.all.return_value = sample_discovered_keywords[:2]

    result = import_service._retrieve_selected_items(job_id, user_selections)

    assert len(result["keywords"]) == 2
    assert len(result["competitors"]) == 0
    assert len(result["opportunities"]) == 0


def test_retrieve_selected_items_mixed(
    import_service,
    mock_onside_db,
    sample_discovered_keywords,
    sample_identified_competitors
):
    """Test retrieving both keywords and competitors."""
    job_id = str(uuid.uuid4())
    user_selections = {
        "selected_keywords": [1, 2, 3],
        "selected_competitors": [1, 2]
    }

    # Mock queries
    def query_side_effect(model):
        mock_query = Mock()
        if model == DiscoveredKeyword:
            mock_query.filter.return_value.all.return_value = sample_discovered_keywords
        elif model == IdentifiedCompetitor:
            mock_query.filter.return_value.all.return_value = sample_identified_competitors
        return mock_query

    mock_onside_db.query.side_effect = query_side_effect

    result = import_service._retrieve_selected_items(job_id, user_selections)

    assert len(result["keywords"]) == 3
    assert len(result["competitors"]) == 2


# ============================================================================
# DATA TRANSFORMATION TESTS
# ============================================================================

def test_transform_data_keywords(import_service, sample_discovered_keywords):
    """Test transformation of keywords to En Garde format."""
    selected_items = {
        "keywords": sample_discovered_keywords,
        "competitors": [],
        "opportunities": []
    }

    result = import_service._transform_data(selected_items)

    assert len(result["keywords"]) == 3
    assert all(isinstance(kw, EnGardeKeywordSchema) for kw in result["keywords"])
    assert result["keywords"][0].keyword_text == "email marketing"
    assert result["keywords"][0].search_volume == 12000


def test_transform_data_competitors(import_service, sample_identified_competitors):
    """Test transformation of competitors to En Garde format."""
    selected_items = {
        "keywords": [],
        "competitors": sample_identified_competitors,
        "opportunities": []
    }

    result = import_service._transform_data(selected_items)

    assert len(result["competitors"]) == 2
    assert all(isinstance(comp, EnGardeCompetitorSchema) for comp in result["competitors"])
    assert result["competitors"][0].competitor_name == "Mailchimp"
    assert result["competitors"][0].domain == "mailchimp.com"


# ============================================================================
# DUPLICATE DETECTION TESTS
# ============================================================================

def test_check_duplicates_no_duplicates(import_service):
    """Test duplicate check when no duplicates exist."""
    keywords = [
        EnGardeKeywordSchema(
            keyword_text="unique keyword",
            priority_level="medium",
            source="onside_analysis"
        )
    ]
    competitors = [
        EnGardeCompetitorSchema(
            competitor_name="Unique Competitor",
            domain="unique.com",
            source="onside_analysis"
        )
    ]

    result = import_service.check_duplicates(keywords, competitors, str(uuid.uuid4()))

    assert len(result["duplicates"]) == 0
    assert result["summary"]["duplicates_found"] == 0
    assert result["recommended_strategy"] == ImportStrategy.CREATE_NEW


def test_check_duplicates_summary_statistics(import_service):
    """Test duplicate detection summary statistics."""
    keywords = [
        EnGardeKeywordSchema(
            keyword_text=f"keyword {i}",
            priority_level="medium",
            source="onside_analysis"
        )
        for i in range(5)
    ]

    result = import_service.check_duplicates(keywords, [], str(uuid.uuid4()))

    assert result["summary"]["total_checked"] == 5
    assert "duplicate_rate" in result["summary"]
    assert "keyword_duplicates" in result["summary"]
    assert "competitor_duplicates" in result["summary"]


# ============================================================================
# IMPORT STRATEGY TESTS
# ============================================================================

def test_import_strategy_skip(import_service):
    """Test SKIP import strategy."""
    assert ImportStrategy.SKIP.value == "skip"
    assert ImportStrategy.SKIP in ImportStrategy


def test_import_strategy_merge(import_service):
    """Test MERGE import strategy."""
    assert ImportStrategy.MERGE.value == "merge"
    assert ImportStrategy.MERGE in ImportStrategy


def test_import_strategy_replace(import_service):
    """Test REPLACE import strategy."""
    assert ImportStrategy.REPLACE.value == "replace"
    assert ImportStrategy.REPLACE in ImportStrategy


def test_import_strategy_create_new(import_service):
    """Test CREATE_NEW import strategy."""
    assert ImportStrategy.CREATE_NEW.value == "create_new"
    assert ImportStrategy.CREATE_NEW in ImportStrategy


# ============================================================================
# IMPORT EXECUTION TESTS
# ============================================================================

@patch.object(ImportService, '_import_keyword')
@patch.object(ImportService, '_import_competitor')
def test_execute_import_with_skip_strategy(
    mock_import_competitor,
    mock_import_keyword,
    import_service
):
    """Test import execution with SKIP strategy for duplicates."""
    keywords = [
        EnGardeKeywordSchema(
            keyword_text="test keyword",
            metadata={"onside_id": 1},
            priority_level="medium",
            source="onside_analysis"
        )
    ]
    competitors = []

    duplicate_report = {
        "duplicates": [
            DuplicateMatch(
                item_id=1,
                item_type="keyword",
                onside_value="test keyword",
                existing_value="test keyword",
                similarity_score=1.0,
                recommended_action=ImportStrategy.SKIP
            )
        ],
        "summary": {"duplicates_found": 1}
    }

    transformed_data = {"keywords": keywords, "competitors": competitors, "opportunities": []}

    result = import_service._execute_import(
        transformed_data=transformed_data,
        duplicate_report=duplicate_report,
        import_strategy=ImportStrategy.SKIP,
        tenant_uuid=str(uuid.uuid4()),
        batch_id=str(uuid.uuid4())
    )

    # Should skip the duplicate keyword
    assert result["keywords_imported"] == 0
    assert result["duplicates_skipped"] == 1
    mock_import_keyword.assert_not_called()


@patch.object(ImportService, '_import_keyword')
def test_execute_import_no_duplicates(mock_import_keyword, import_service):
    """Test import execution when no duplicates exist."""
    keywords = [
        EnGardeKeywordSchema(
            keyword_text=f"keyword {i}",
            metadata={"onside_id": i},
            priority_level="medium",
            source="onside_analysis"
        )
        for i in range(3)
    ]

    duplicate_report = {"duplicates": [], "summary": {"duplicates_found": 0}}
    transformed_data = {"keywords": keywords, "competitors": [], "opportunities": []}

    result = import_service._execute_import(
        transformed_data=transformed_data,
        duplicate_report=duplicate_report,
        import_strategy=ImportStrategy.SKIP,
        tenant_uuid=str(uuid.uuid4()),
        batch_id=str(uuid.uuid4())
    )

    assert result["keywords_imported"] == 3
    assert result["duplicates_skipped"] == 0
    assert mock_import_keyword.call_count == 3


# ============================================================================
# ROLLBACK TESTS
# ============================================================================

def test_rollback_import(import_service):
    """Test rollback functionality."""
    batch_id = str(uuid.uuid4())

    result = import_service.rollback_import(batch_id)

    assert result["batch_id"] == batch_id
    assert result["status"] == "success"
    assert "message" in result


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_import_with_transformation_errors(import_service, mock_onside_db):
    """Test import handles transformation errors gracefully."""
    # This test would verify error handling during transformation
    # For now, it's a placeholder for future implementation
    pass


def test_import_with_database_errors(import_service, mock_onside_db):
    """Test import handles database errors gracefully."""
    mock_onside_db.commit.side_effect = Exception("Database error")

    # Test that errors are caught and handled appropriately
    # This is a placeholder for actual implementation
    pass


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_mark_items_confirmed(import_service, mock_onside_db):
    """Test marking items as confirmed in Onside staging tables."""
    job_id = str(uuid.uuid4())
    user_selections = {
        "selected_keywords": [1, 2, 3],
        "selected_competitors": [4, 5]
    }

    mock_query = Mock()
    mock_onside_db.query.return_value = mock_query
    mock_query.filter.return_value.update.return_value = None

    import_service._mark_items_confirmed(job_id, user_selections)

    # Verify update was called for both keywords and competitors
    assert mock_query.filter.return_value.update.call_count == 2


# ============================================================================
# EDGE CASES
# ============================================================================

def test_import_with_empty_selections(import_service):
    """Test import with no items selected."""
    # This would test behavior when user_selections is empty
    pass


def test_import_with_partial_failures(import_service):
    """Test import when some items fail but others succeed."""
    # This would test resilience to partial failures
    pass


def test_import_with_invalid_tenant_uuid(import_service):
    """Test import with invalid tenant UUID."""
    # This would test tenant validation
    pass


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

def test_import_large_batch(import_service):
    """Test import performance with large batches."""
    # This would test performance with 1000+ items
    pass


def test_import_concurrent_batches(import_service):
    """Test handling of concurrent import batches."""
    # This would test thread safety and concurrent operations
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
