import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import pandas as pd
import json
import aiohttp
from src.services.data_ingestion import DataIngestionService
from src.models.content import Content
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@pytest.fixture
def data_service():
    return DataIngestionService()

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_ingest_csv_data(data_service, mock_db_session):
    """Test CSV data ingestion"""
    test_data = pd.DataFrame({
        'title': ['Test Article'],
        'content': ['Test content with more than 10 characters'],
        'type': ['article'],
        'published_date': ['2024-01-01']
    })

    mock_content = MagicMock()
    mock_content.title = "Test Article"
    mock_content.content_text = "Test content"
    mock_content.id = 1

    with patch('pandas.read_csv', return_value=test_data):
        with patch('src.models.content.Content', return_value=mock_content) as mock_content_class:
            result = await data_service.ingest_csv_data(
                'test.csv',
                user_id=1,
                db=mock_db_session
            )

            assert len(result) == 1
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_ingest_json_data(data_service, mock_db_session):
    """Test JSON data ingestion"""
    test_data = [{
        'title': 'Test Article',
        'content': 'Test content with more than 10 characters',
        'type': 'article',
        'published_date': '2024-01-01'
    }]

    mock_content = MagicMock()
    mock_content.title = "Test Article"
    mock_content.content_text = "Test content"
    mock_content.id = 1

    with patch('builtins.open', create=True) as mock_file:
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(test_data)
        with patch('src.models.content.Content', return_value=mock_content) as mock_content_class:
            result = await data_service.ingest_json_data(
                'test.json',
                user_id=1,
                db=mock_db_session
            )

            assert len(result) == 1
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_ingest_api_data(data_service, mock_db_session):
    """Test API data ingestion"""
    test_data = [{
        'title': 'Test Article',
        'content': 'Test content with more than 10 characters',
        'type': 'article',
        'published_date': '2024-01-01'
    }]

    mock_content = MagicMock()
    mock_content.title = "Test Article"
    mock_content.content_text = "Test content"
    mock_content.id = 1

    mock_response = AsyncMock()
    mock_response.json.return_value = test_data

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

    with patch('aiohttp.ClientSession', return_value=mock_session):
        with patch('src.models.content.Content', return_value=mock_content) as mock_content_class:
            result = await data_service.ingest_api_data(
                'http://test.api/data',
                user_id=1,
                db=mock_db_session
            )

            assert len(result) == 1
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_validate_data(data_service):
    """Test data validation"""
    valid_data = {
        'title': 'Test Article',
        'content_text': 'This is a valid content with more than 10 characters'
    }
    assert data_service.validate_data(valid_data) is True

    invalid_data = {
        'title': '',
        'content_text': 'Short'
    }
    assert data_service.validate_data(invalid_data) is False

@pytest.mark.asyncio
async def test_transform_data(data_service):
    """Test data transformation"""
    input_data = {
        'title': 'Test Article',
        'content': 'Test content',
        'type': 'article',
        'published_date': '2024-01-01'
    }
    user_id = 1

    result = data_service.transform_data(input_data, user_id)

    assert result['user_id'] == user_id
    assert result['title'] == input_data['title']
    assert result['content_text'] == input_data['content']
    assert result['content_metadata']['type'] == input_data['type']
    assert result['content_metadata']['published_date'] == input_data['published_date']
    assert 'created_at' in result
    assert 'updated_at' in result

@pytest.mark.asyncio
async def test_handle_duplicates(data_service, mock_db_session):
    """Test duplicate content handling"""
    mock_content = MagicMock()
    mock_content.title = "Test Article"
    mock_content.content_text = "Test content"
    mock_content.id = 1

    # Setup mock response for execute
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=mock_content)
    mock_db_session.execute.return_value = mock_result

    # Test skip strategy
    result = await data_service.handle_duplicates(mock_content, mock_db_session, 'skip')
    assert result is None

    # Test update strategy
    result = await data_service.handle_duplicates(mock_content, mock_db_session, 'update')
    assert result == mock_content

    # Test version strategy
    result = await data_service.handle_duplicates(mock_content, mock_db_session, 'version')
    assert 'Test Article (v' in result.title

@pytest.mark.asyncio
async def test_error_handling(data_service, mock_db_session):
    """Test error handling during data ingestion"""
    # Test database error
    mock_db_session.commit.side_effect = Exception("Database error")

    with pytest.raises(HTTPException) as exc_info:
        await data_service.ingest_csv_data(
            'test.csv',
            user_id=1,
            db=mock_db_session
        )
    assert exc_info.value.status_code == 500
    assert mock_db_session.rollback.called

    # Test file not found error
    with pytest.raises(HTTPException) as exc_info:
        await data_service.ingest_json_data(
            'nonexistent.json',
            user_id=1,
            db=mock_db_session
        )
    assert exc_info.value.status_code == 500
    assert "No such file or directory" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_batch_processing(data_service, mock_db_session):
    """Test batch processing of data"""
    large_df = pd.DataFrame({
        'title': [f'Article {i}' for i in range(100)],
        'content': [f'Content {i} with more than 10 characters' for i in range(100)],
        'type': ['article'] * 100,
        'published_date': ['2024-01-01'] * 100
    })

    mock_content = MagicMock()
    mock_content.title = "Test Article"
    mock_content.content_text = "Test content"
    mock_content.id = 1

    with patch('pandas.read_csv', return_value=large_df):
        with patch('src.models.content.Content', return_value=mock_content) as mock_content_class:
            result = await data_service.ingest_csv_data(
                'test.csv',
                user_id=1,
                db=mock_db_session,
                batch_size=10
            )

            assert len(result) == 100
            assert mock_db_session.commit.call_count == 10  # Called once per batch
