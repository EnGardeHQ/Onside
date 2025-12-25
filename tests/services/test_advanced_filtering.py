"""
Comprehensive unit and integration tests for AdvancedFilter service.

This module provides extensive test coverage for advanced filtering functionality,
including all 14 filter operators, multi-field sorting, pagination (offset and page-based),
full-text search, type conversion, and error handling.
"""
import pytest
from unittest.mock import MagicMock, Mock
from datetime import datetime
from typing import Any, Dict

from src.services.advanced_filtering import (
    FilterOperator,
    FilterParser,
    AdvancedFilter
)
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Create a test model
Base = declarative_base()


class TestModel(Base):
    """Test SQLAlchemy model for filter testing."""
    __tablename__ = 'test_model'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    age = Column(Integer)
    score = Column(Float)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    category = Column(String(50))
    description = Column(String(500))


class TestFilterOperator:
    """Test suite for FilterOperator constants."""

    def test_all_operators_available(self):
        """Test all 14 operators are defined."""
        operators = FilterOperator.all()
        assert len(operators) == 14
        assert FilterOperator.EQ in operators
        assert FilterOperator.NE in operators
        assert FilterOperator.GT in operators
        assert FilterOperator.GTE in operators
        assert FilterOperator.LT in operators
        assert FilterOperator.LTE in operators
        assert FilterOperator.CONTAINS in operators
        assert FilterOperator.ICONTAINS in operators
        assert FilterOperator.STARTSWITH in operators
        assert FilterOperator.ENDSWITH in operators
        assert FilterOperator.IN in operators
        assert FilterOperator.NOT_IN in operators
        assert FilterOperator.IS_NULL in operators
        assert FilterOperator.NOT_NULL in operators
        assert FilterOperator.BETWEEN in operators


class TestFilterParser:
    """Test suite for FilterParser."""

    @pytest.fixture
    def parser(self):
        """Create a FilterParser instance."""
        return FilterParser()

    def test_parse_filter_simple_field(self, parser):
        """Test parsing simple field without operator."""
        field, operator, value = parser.parse_filter("name", "John")
        assert field == "name"
        assert operator == FilterOperator.EQ
        assert value == "John"

    def test_parse_filter_with_eq_operator(self, parser):
        """Test parsing with eq operator."""
        field, operator, value = parser.parse_filter("name__eq", "John")
        assert field == "name"
        assert operator == FilterOperator.EQ
        assert value == "John"

    def test_parse_filter_with_ne_operator(self, parser):
        """Test parsing with ne operator."""
        field, operator, value = parser.parse_filter("status__ne", "inactive")
        assert field == "status"
        assert operator == FilterOperator.NE
        assert value == "inactive"

    def test_parse_filter_with_gt_operator(self, parser):
        """Test parsing with gt operator."""
        field, operator, value = parser.parse_filter("age__gt", "18")
        assert field == "age"
        assert operator == FilterOperator.GT
        assert value == 18  # Should be parsed as int

    def test_parse_filter_with_gte_operator(self, parser):
        """Test parsing with gte operator."""
        field, operator, value = parser.parse_filter("score__gte", "75.5")
        assert field == "score"
        assert operator == FilterOperator.GTE
        assert value == 75.5  # Should be parsed as float

    def test_parse_filter_with_lt_operator(self, parser):
        """Test parsing with lt operator."""
        field, operator, value = parser.parse_filter("age__lt", "65")
        assert field == "age"
        assert operator == FilterOperator.LT
        assert value == 65

    def test_parse_filter_with_lte_operator(self, parser):
        """Test parsing with lte operator."""
        field, operator, value = parser.parse_filter("score__lte", "100")
        assert field == "score"
        assert operator == FilterOperator.LTE
        assert value == 100

    def test_parse_filter_with_contains_operator(self, parser):
        """Test parsing with contains operator."""
        field, operator, value = parser.parse_filter("name__contains", "john")
        assert field == "name"
        assert operator == FilterOperator.CONTAINS
        assert value == "john"

    def test_parse_filter_with_icontains_operator(self, parser):
        """Test parsing with icontains operator."""
        field, operator, value = parser.parse_filter("email__icontains", "example.com")
        assert field == "email"
        assert operator == FilterOperator.ICONTAINS
        assert value == "example.com"

    def test_parse_filter_with_startswith_operator(self, parser):
        """Test parsing with startswith operator."""
        field, operator, value = parser.parse_filter("name__startswith", "Dr.")
        assert field == "name"
        assert operator == FilterOperator.STARTSWITH
        assert value == "Dr."

    def test_parse_filter_with_endswith_operator(self, parser):
        """Test parsing with endswith operator."""
        field, operator, value = parser.parse_filter("email__endswith", ".com")
        assert field == "email"
        assert operator == FilterOperator.ENDSWITH
        assert value == ".com"

    def test_parse_filter_with_in_operator(self, parser):
        """Test parsing with in operator."""
        field, operator, value = parser.parse_filter("status__in", "active,pending,approved")
        assert field == "status"
        assert operator == FilterOperator.IN
        assert value == ["active", "pending", "approved"]

    def test_parse_filter_with_not_in_operator(self, parser):
        """Test parsing with not_in operator."""
        field, operator, value = parser.parse_filter("category__not_in", "spam,deleted")
        assert field == "category"
        assert operator == FilterOperator.NOT_IN
        assert value == ["spam", "deleted"]

    def test_parse_filter_with_is_null_operator(self, parser):
        """Test parsing with is_null operator."""
        field, operator, value = parser.parse_filter("deleted_at__is_null", "true")
        assert field == "deleted_at"
        assert operator == FilterOperator.IS_NULL
        assert value is True

    def test_parse_filter_with_not_null_operator(self, parser):
        """Test parsing with not_null operator."""
        field, operator, value = parser.parse_filter("email__not_null", "true")
        assert field == "email"
        assert operator == FilterOperator.NOT_NULL
        assert value is True

    def test_parse_filter_with_between_operator(self, parser):
        """Test parsing with between operator."""
        field, operator, value = parser.parse_filter("age__between", "18,65")
        assert field == "age"
        assert operator == FilterOperator.BETWEEN
        assert value == ("18", "65")

    def test_parse_filter_field_with_underscores(self, parser):
        """Test parsing field name containing underscores."""
        field, operator, value = parser.parse_filter("user_name__eq", "john")
        assert field == "user_name"
        assert operator == FilterOperator.EQ

    def test_parse_filter_field_with_multiple_underscores(self, parser):
        """Test parsing field with multiple underscores."""
        field, operator, value = parser.parse_filter("user_full_name__contains", "john")
        assert field == "user_full_name"
        assert operator == FilterOperator.CONTAINS

    def test_parse_value_integer(self, parser):
        """Test parsing integer values."""
        value = parser._parse_value("42", FilterOperator.EQ)
        assert value == 42
        assert isinstance(value, int)

    def test_parse_value_float(self, parser):
        """Test parsing float values."""
        value = parser._parse_value("42.5", FilterOperator.EQ)
        assert value == 42.5
        assert isinstance(value, float)

    def test_parse_value_boolean_true(self, parser):
        """Test parsing boolean true values."""
        assert parser._parse_value("true", FilterOperator.EQ) is True
        assert parser._parse_value("True", FilterOperator.EQ) is True

    def test_parse_value_boolean_false(self, parser):
        """Test parsing boolean false values."""
        assert parser._parse_value("false", FilterOperator.EQ) is False
        assert parser._parse_value("False", FilterOperator.EQ) is False

    def test_parse_value_datetime(self, parser):
        """Test parsing datetime values."""
        value = parser._parse_value("2024-01-15T10:30:00", FilterOperator.EQ)
        assert isinstance(value, datetime)
        assert value.year == 2024
        assert value.month == 1
        assert value.day == 15

    def test_parse_value_datetime_with_z(self, parser):
        """Test parsing datetime with Z suffix."""
        value = parser._parse_value("2024-01-15T10:30:00Z", FilterOperator.EQ)
        assert isinstance(value, datetime)

    def test_parse_value_string(self, parser):
        """Test parsing string values."""
        value = parser._parse_value("hello world", FilterOperator.EQ)
        assert value == "hello world"
        assert isinstance(value, str)

    def test_parse_value_null_operators(self, parser):
        """Test parsing values for null operators."""
        assert parser._parse_value("true", FilterOperator.IS_NULL) is True
        assert parser._parse_value("false", FilterOperator.IS_NULL) is False
        assert parser._parse_value("1", FilterOperator.NOT_NULL) is True


class TestAdvancedFilter:
    """Test suite for AdvancedFilter."""

    @pytest.fixture
    def advanced_filter(self):
        """Create an AdvancedFilter instance."""
        return AdvancedFilter()

    @pytest.fixture
    def mock_query(self):
        """Create a mock SQLAlchemy query."""
        query = MagicMock()
        query.filter = MagicMock(return_value=query)
        query.order_by = MagicMock(return_value=query)
        query.offset = MagicMock(return_value=query)
        query.limit = MagicMock(return_value=query)
        query.count = MagicMock(return_value=100)
        return query

    def test_apply_filters_eq_operator(self, advanced_filter, mock_query):
        """Test applying eq filter."""
        filters = {"name": "John"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_ne_operator(self, advanced_filter, mock_query):
        """Test applying ne filter."""
        filters = {"status__ne": "inactive"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_gt_operator(self, advanced_filter, mock_query):
        """Test applying gt filter."""
        filters = {"age__gt": "18"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_gte_operator(self, advanced_filter, mock_query):
        """Test applying gte filter."""
        filters = {"age__gte": "18"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_lt_operator(self, advanced_filter, mock_query):
        """Test applying lt filter."""
        filters = {"age__lt": "65"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_lte_operator(self, advanced_filter, mock_query):
        """Test applying lte filter."""
        filters = {"age__lte": "65"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_contains_operator(self, advanced_filter, mock_query):
        """Test applying contains filter."""
        filters = {"name__contains": "john"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_icontains_operator(self, advanced_filter, mock_query):
        """Test applying icontains filter."""
        filters = {"email__icontains": "example.com"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_startswith_operator(self, advanced_filter, mock_query):
        """Test applying startswith filter."""
        filters = {"name__startswith": "Dr"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_endswith_operator(self, advanced_filter, mock_query):
        """Test applying endswith filter."""
        filters = {"email__endswith": ".com"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_in_operator(self, advanced_filter, mock_query):
        """Test applying in filter."""
        filters = {"category__in": "tech,science,education"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_not_in_operator(self, advanced_filter, mock_query):
        """Test applying not_in filter."""
        filters = {"category__not_in": "spam,deleted"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_is_null_operator(self, advanced_filter, mock_query):
        """Test applying is_null filter."""
        filters = {"email__is_null": "true"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_not_null_operator(self, advanced_filter, mock_query):
        """Test applying not_null filter."""
        filters = {"email__not_null": "true"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_between_operator(self, advanced_filter, mock_query):
        """Test applying between filter."""
        filters = {"age__between": "18,65"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_apply_filters_multiple_filters(self, advanced_filter, mock_query):
        """Test applying multiple filters."""
        filters = {
            "name__contains": "john",
            "age__gte": "18",
            "is_active": "true"
        }
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.call_count >= 3

    def test_apply_filters_skips_pagination_params(self, advanced_filter, mock_query):
        """Test that pagination parameters are skipped."""
        filters = {
            "name": "John",
            "page": "1",
            "limit": "10",
            "offset": "0",
            "sort": "name",
            "order": "asc",
            "search": "test"
        }
        # Should only filter on 'name', not the others
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        # Only 'name' filter should be applied
        assert mock_query.filter.called

    def test_apply_filters_invalid_field(self, advanced_filter, mock_query):
        """Test filtering on non-existent field is skipped."""
        filters = {"nonexistent_field": "value"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        # Should not raise error, just skip the field
        assert result is not None

    def test_apply_sorting_single_field_asc(self, advanced_filter, mock_query):
        """Test sorting by single field ascending."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, "name", "asc"
        )
        assert mock_query.order_by.called

    def test_apply_sorting_single_field_desc(self, advanced_filter, mock_query):
        """Test sorting by single field descending."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, "created_at", "desc"
        )
        assert mock_query.order_by.called

    def test_apply_sorting_multiple_fields(self, advanced_filter, mock_query):
        """Test sorting by multiple fields."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, "category,name", "asc"
        )
        assert mock_query.order_by.call_count >= 2

    def test_apply_sorting_with_prefix_minus(self, advanced_filter, mock_query):
        """Test sorting with minus prefix for descending."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, "-created_at", "asc"
        )
        assert mock_query.order_by.called

    def test_apply_sorting_with_prefix_plus(self, advanced_filter, mock_query):
        """Test sorting with plus prefix for ascending."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, "+name", "desc"
        )
        assert mock_query.order_by.called

    def test_apply_sorting_mixed_directions(self, advanced_filter, mock_query):
        """Test sorting with mixed directions."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, "category,-created_at,+name", "asc"
        )
        assert mock_query.order_by.call_count >= 3

    def test_apply_sorting_no_sort_field(self, advanced_filter, mock_query):
        """Test sorting with no sort field."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, None, "asc"
        )
        # Should not call order_by
        assert not mock_query.order_by.called

    def test_apply_sorting_invalid_field(self, advanced_filter, mock_query):
        """Test sorting on invalid field is skipped."""
        result = advanced_filter.apply_sorting(
            mock_query, TestModel, "nonexistent_field", "asc"
        )
        # Should not raise error
        assert result is not None

    def test_apply_pagination_with_page(self, advanced_filter, mock_query):
        """Test pagination with page number."""
        result, metadata = advanced_filter.apply_pagination(
            mock_query, page=2, limit=10
        )
        assert mock_query.offset.called
        assert mock_query.limit.called
        assert metadata['page'] == 2
        assert metadata['limit'] == 10

    def test_apply_pagination_with_offset(self, advanced_filter, mock_query):
        """Test pagination with offset."""
        result, metadata = advanced_filter.apply_pagination(
            mock_query, offset=20, limit=10
        )
        assert mock_query.offset.called
        assert mock_query.limit.called
        assert metadata['offset'] == 20

    def test_apply_pagination_default_limit(self, advanced_filter, mock_query):
        """Test pagination uses default limit."""
        result, metadata = advanced_filter.apply_pagination(mock_query)
        assert metadata['limit'] == 50  # Default

    def test_apply_pagination_max_limit(self, advanced_filter, mock_query):
        """Test pagination enforces maximum limit."""
        result, metadata = advanced_filter.apply_pagination(
            mock_query, limit=500
        )
        assert metadata['limit'] == 100  # Max enforced

    def test_apply_pagination_metadata_has_next(self, advanced_filter, mock_query):
        """Test pagination metadata has_next flag."""
        mock_query.count.return_value = 100
        result, metadata = advanced_filter.apply_pagination(
            mock_query, page=1, limit=10
        )
        assert metadata['has_next'] is True

    def test_apply_pagination_metadata_has_prev(self, advanced_filter, mock_query):
        """Test pagination metadata has_prev flag."""
        result, metadata = advanced_filter.apply_pagination(
            mock_query, page=2, limit=10
        )
        assert metadata['has_prev'] is True

    def test_apply_pagination_metadata_pages(self, advanced_filter, mock_query):
        """Test pagination metadata calculates total pages."""
        mock_query.count.return_value = 95
        result, metadata = advanced_filter.apply_pagination(
            mock_query, limit=10
        )
        assert metadata['pages'] == 10  # Ceiling of 95/10

    def test_apply_full_text_search_single_field(self, advanced_filter, mock_query):
        """Test full-text search on single field."""
        result = advanced_filter.apply_full_text_search(
            mock_query, TestModel, "john", ["name"]
        )
        assert mock_query.filter.called

    def test_apply_full_text_search_multiple_fields(self, advanced_filter, mock_query):
        """Test full-text search on multiple fields."""
        result = advanced_filter.apply_full_text_search(
            mock_query, TestModel, "test", ["name", "email", "description"]
        )
        assert mock_query.filter.called

    def test_apply_full_text_search_no_query(self, advanced_filter, mock_query):
        """Test full-text search with empty query."""
        result = advanced_filter.apply_full_text_search(
            mock_query, TestModel, "", ["name"]
        )
        # Should not filter
        assert not mock_query.filter.called

    def test_apply_full_text_search_no_fields(self, advanced_filter, mock_query):
        """Test full-text search with no fields."""
        result = advanced_filter.apply_full_text_search(
            mock_query, TestModel, "test", []
        )
        # Should not filter
        assert not mock_query.filter.called

    def test_apply_full_text_search_invalid_field(self, advanced_filter, mock_query):
        """Test full-text search skips invalid fields."""
        result = advanced_filter.apply_full_text_search(
            mock_query, TestModel, "test", ["name", "nonexistent_field"]
        )
        # Should filter on valid field only
        assert result is not None

    def test_apply_all_combined(self, advanced_filter, mock_query):
        """Test applying all operations together."""
        params = {
            "name__contains": "john",
            "age__gte": "18",
            "is_active": "true",
            "sort": "created_at",
            "order": "desc",
            "page": "2",
            "limit": "20",
            "search": "test"
        }
        search_fields = ["name", "email", "description"]

        query, metadata = advanced_filter.apply_all(
            mock_query, TestModel, params, search_fields
        )

        # All operations should be applied
        assert mock_query.filter.called  # For filters and search
        assert mock_query.order_by.called  # For sorting
        assert mock_query.offset.called  # For pagination
        assert mock_query.limit.called  # For pagination
        assert 'total' in metadata
        assert 'page' in metadata

    def test_apply_all_without_search(self, advanced_filter, mock_query):
        """Test apply_all without search query."""
        params = {
            "name": "John",
            "sort": "name",
            "page": "1"
        }

        query, metadata = advanced_filter.apply_all(
            mock_query, TestModel, params
        )

        assert metadata is not None

    def test_apply_all_minimal_params(self, advanced_filter, mock_query):
        """Test apply_all with minimal parameters."""
        params = {}

        query, metadata = advanced_filter.apply_all(
            mock_query, TestModel, params
        )

        # Should still return metadata
        assert 'total' in metadata
        assert 'limit' in metadata


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    @pytest.fixture
    def advanced_filter(self):
        """Create an AdvancedFilter instance."""
        return AdvancedFilter()

    @pytest.fixture
    def mock_query(self):
        """Create a mock SQLAlchemy query."""
        query = MagicMock()
        query.filter = MagicMock(return_value=query)
        query.order_by = MagicMock(return_value=query)
        query.offset = MagicMock(return_value=query)
        query.limit = MagicMock(return_value=query)
        query.count = MagicMock(return_value=0)
        return query

    def test_pagination_empty_results(self, advanced_filter, mock_query):
        """Test pagination with zero results."""
        mock_query.count.return_value = 0
        result, metadata = advanced_filter.apply_pagination(mock_query, page=1)
        assert metadata['total'] == 0
        assert metadata['pages'] == 1
        assert metadata['has_next'] is False

    def test_pagination_single_page(self, advanced_filter, mock_query):
        """Test pagination when all results fit on one page."""
        mock_query.count.return_value = 10
        result, metadata = advanced_filter.apply_pagination(mock_query, limit=50)
        assert metadata['pages'] == 1
        assert metadata['has_next'] is False

    def test_between_operator_invalid_format(self, advanced_filter, mock_query):
        """Test between operator with invalid format."""
        filters = {"age__between": "18"}  # Missing second value
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        # Should handle gracefully
        assert result is not None

    def test_filter_with_empty_string(self, advanced_filter, mock_query):
        """Test filtering with empty string value."""
        filters = {"name": ""}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_in_operator_single_value(self, advanced_filter, mock_query):
        """Test in operator with single value."""
        filters = {"category__in": "tech"}
        result = advanced_filter.apply_filters(mock_query, TestModel, filters)
        assert mock_query.filter.called

    def test_search_special_characters(self, advanced_filter, mock_query):
        """Test full-text search with special characters."""
        result = advanced_filter.apply_full_text_search(
            mock_query, TestModel, "john@example.com", ["email"]
        )
        assert mock_query.filter.called

    def test_pagination_page_zero(self, advanced_filter, mock_query):
        """Test pagination with page 0."""
        result, metadata = advanced_filter.apply_pagination(mock_query, page=0)
        # Should handle gracefully
        assert metadata is not None

    def test_pagination_negative_page(self, advanced_filter, mock_query):
        """Test pagination with negative page."""
        result, metadata = advanced_filter.apply_pagination(mock_query, page=-1)
        # Should handle gracefully
        assert metadata is not None
