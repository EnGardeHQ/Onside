"""Advanced filtering service for API endpoints.

This module provides comprehensive filtering, sorting, and pagination
capabilities for all API endpoints, supporting complex query operations.
"""
import re
from typing import Any, Dict, List, Optional, Tuple, Type
from sqlalchemy import or_, and_, desc, asc, func
from sqlalchemy.orm import Query
from sqlalchemy.inspection import inspect
from datetime import datetime


class FilterOperator:
    """Supported filter operators."""
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    CONTAINS = "contains"  # String contains
    ICONTAINS = "icontains"  # Case-insensitive contains
    STARTSWITH = "startswith"  # String starts with
    ENDSWITH = "endswith"  # String ends with
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list
    IS_NULL = "is_null"  # Is NULL
    NOT_NULL = "not_null"  # Is NOT NULL
    BETWEEN = "between"  # Between two values

    @classmethod
    def all(cls) -> List[str]:
        """Get all supported operators."""
        return [
            cls.EQ, cls.NE, cls.GT, cls.GTE, cls.LT, cls.LTE,
            cls.CONTAINS, cls.ICONTAINS, cls.STARTSWITH, cls.ENDSWITH,
            cls.IN, cls.NOT_IN, cls.IS_NULL, cls.NOT_NULL, cls.BETWEEN
        ]


class FilterParser:
    """Parser for filter query parameters.

    Supports filter syntax like: field__operator=value
    Example: name__contains=test, age__gte=18, status__in=active,pending
    """

    def __init__(self):
        """Initialize the filter parser."""
        self.operators = FilterOperator.all()

    def parse_filter(self, key: str, value: str) -> Tuple[str, str, Any]:
        """Parse a filter expression.

        Args:
            key: Filter key (e.g., 'name__contains')
            value: Filter value

        Returns:
            Tuple of (field_name, operator, parsed_value)
        """
        # Split by double underscore to get field and operator
        parts = key.split('__')

        if len(parts) == 1:
            # No operator specified, default to 'eq'
            field_name = parts[0]
            operator = FilterOperator.EQ
        elif len(parts) == 2:
            field_name = parts[0]
            operator = parts[1]
            if operator not in self.operators:
                # Treat as part of field name and default to 'eq'
                field_name = key
                operator = FilterOperator.EQ
        else:
            # Multiple underscores - join all but last as field name
            field_name = '__'.join(parts[:-1])
            operator = parts[-1]
            if operator not in self.operators:
                field_name = key
                operator = FilterOperator.EQ

        # Parse the value based on operator
        parsed_value = self._parse_value(value, operator)

        return field_name, operator, parsed_value

    def _parse_value(self, value: str, operator: str) -> Any:
        """Parse filter value based on operator.

        Args:
            value: Raw value string
            operator: Filter operator

        Returns:
            Parsed value
        """
        if operator in [FilterOperator.IS_NULL, FilterOperator.NOT_NULL]:
            # Boolean value for null checks
            return value.lower() in ('true', '1', 'yes')

        if operator == FilterOperator.IN or operator == FilterOperator.NOT_IN:
            # Split comma-separated list
            return [v.strip() for v in value.split(',')]

        if operator == FilterOperator.BETWEEN:
            # Split comma-separated range
            parts = [v.strip() for v in value.split(',')]
            if len(parts) == 2:
                return tuple(parts)
            return value

        # Try to parse as integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try to parse as float
        try:
            return float(value)
        except ValueError:
            pass

        # Try to parse as boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Try to parse as datetime
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

        # Return as string
        return value


class AdvancedFilter:
    """Advanced filtering service for SQLAlchemy queries.

    Provides filtering, sorting, pagination, and full-text search capabilities.
    """

    def __init__(self):
        """Initialize the advanced filter service."""
        self.parser = FilterParser()

    def apply_filters(
        self,
        query: Query,
        model: Type,
        filters: Dict[str, Any]
    ) -> Query:
        """Apply filters to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            model: SQLAlchemy model class
            filters: Dictionary of filter expressions

        Returns:
            Filtered query
        """
        for key, value in filters.items():
            # Skip pagination and sorting parameters
            if key in ['page', 'limit', 'offset', 'sort', 'order', 'search']:
                continue

            # Parse filter expression
            field_name, operator, parsed_value = self.parser.parse_filter(key, str(value))

            # Get model attribute
            try:
                attr = getattr(model, field_name)
            except AttributeError:
                # Field doesn't exist, skip it
                continue

            # Apply operator
            query = self._apply_operator(query, attr, operator, parsed_value)

        return query

    def _apply_operator(
        self,
        query: Query,
        attr: Any,
        operator: str,
        value: Any
    ) -> Query:
        """Apply a filter operator to the query.

        Args:
            query: SQLAlchemy query
            attr: Model attribute
            operator: Filter operator
            value: Filter value

        Returns:
            Modified query
        """
        if operator == FilterOperator.EQ:
            query = query.filter(attr == value)
        elif operator == FilterOperator.NE:
            query = query.filter(attr != value)
        elif operator == FilterOperator.GT:
            query = query.filter(attr > value)
        elif operator == FilterOperator.GTE:
            query = query.filter(attr >= value)
        elif operator == FilterOperator.LT:
            query = query.filter(attr < value)
        elif operator == FilterOperator.LTE:
            query = query.filter(attr <= value)
        elif operator == FilterOperator.CONTAINS:
            query = query.filter(attr.contains(value))
        elif operator == FilterOperator.ICONTAINS:
            query = query.filter(attr.ilike(f'%{value}%'))
        elif operator == FilterOperator.STARTSWITH:
            query = query.filter(attr.startswith(value))
        elif operator == FilterOperator.ENDSWITH:
            query = query.filter(attr.endswith(value))
        elif operator == FilterOperator.IN:
            query = query.filter(attr.in_(value))
        elif operator == FilterOperator.NOT_IN:
            query = query.filter(~attr.in_(value))
        elif operator == FilterOperator.IS_NULL:
            if value:
                query = query.filter(attr.is_(None))
            else:
                query = query.filter(attr.isnot(None))
        elif operator == FilterOperator.NOT_NULL:
            if value:
                query = query.filter(attr.isnot(None))
            else:
                query = query.filter(attr.is_(None))
        elif operator == FilterOperator.BETWEEN:
            if isinstance(value, tuple) and len(value) == 2:
                query = query.filter(and_(attr >= value[0], attr <= value[1]))

        return query

    def apply_sorting(
        self,
        query: Query,
        model: Type,
        sort_by: Optional[str] = None,
        order: str = 'asc'
    ) -> Query:
        """Apply sorting to a query.

        Args:
            query: SQLAlchemy query
            model: SQLAlchemy model class
            sort_by: Field(s) to sort by (comma-separated for multiple)
            order: Sort order ('asc' or 'desc')

        Returns:
            Sorted query
        """
        if not sort_by:
            return query

        # Support multiple sort fields
        sort_fields = [f.strip() for f in sort_by.split(',')]

        for field in sort_fields:
            # Check if field has explicit order
            if field.startswith('-'):
                field = field[1:]
                field_order = 'desc'
            elif field.startswith('+'):
                field = field[1:]
                field_order = 'asc'
            else:
                field_order = order

            # Get model attribute
            try:
                attr = getattr(model, field)
            except AttributeError:
                continue

            # Apply sorting
            if field_order == 'desc':
                query = query.order_by(desc(attr))
            else:
                query = query.order_by(asc(attr))

        return query

    def apply_pagination(
        self,
        query: Query,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Tuple[Query, Dict[str, Any]]:
        """Apply pagination to a query.

        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            limit: Items per page
            offset: Number of items to skip

        Returns:
            Tuple of (paginated query, pagination metadata)
        """
        # Default limit
        if limit is None:
            limit = 50
        limit = min(limit, 100)  # Max 100 items per page

        # Calculate total count
        total = query.count()

        # Calculate offset
        if offset is None and page is not None:
            offset = (page - 1) * limit
        elif offset is None:
            offset = 0

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Calculate pagination metadata
        metadata = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'pages': (total + limit - 1) // limit if limit > 0 else 1,
            'has_next': offset + limit < total,
            'has_prev': offset > 0
        }

        return query, metadata

    def apply_full_text_search(
        self,
        query: Query,
        model: Type,
        search_query: str,
        search_fields: List[str]
    ) -> Query:
        """Apply full-text search to specified fields.

        Args:
            query: SQLAlchemy query
            model: SQLAlchemy model class
            search_query: Search string
            search_fields: List of field names to search in

        Returns:
            Filtered query
        """
        if not search_query or not search_fields:
            return query

        # Build OR conditions for all search fields
        conditions = []
        for field_name in search_fields:
            try:
                attr = getattr(model, field_name)
                conditions.append(attr.ilike(f'%{search_query}%'))
            except AttributeError:
                continue

        if conditions:
            query = query.filter(or_(*conditions))

        return query

    def apply_all(
        self,
        query: Query,
        model: Type,
        params: Dict[str, Any],
        search_fields: Optional[List[str]] = None
    ) -> Tuple[Query, Dict[str, Any]]:
        """Apply all filtering, sorting, and pagination operations.

        Args:
            query: SQLAlchemy query
            model: SQLAlchemy model class
            params: Query parameters dictionary
            search_fields: List of fields for full-text search

        Returns:
            Tuple of (filtered/sorted/paginated query, pagination metadata)
        """
        # Apply full-text search
        if 'search' in params and search_fields:
            query = self.apply_full_text_search(
                query, model, params['search'], search_fields
            )

        # Apply filters
        query = self.apply_filters(query, model, params)

        # Apply sorting
        query = self.apply_sorting(
            query, model,
            params.get('sort'),
            params.get('order', 'asc')
        )

        # Apply pagination
        query, metadata = self.apply_pagination(
            query,
            params.get('page'),
            params.get('limit'),
            params.get('offset')
        )

        return query, metadata
