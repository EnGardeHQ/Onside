"""
BDD Tests for Query Optimizer (S5-03)

This module implements BDD-style tests for the database query optimization service
following the Semantic Seed Venture Studio Coding Standards V2.0.

The tests connect to the actual PostgreSQL database as required by project standards:
- Host: localhost
- Port: 5432
- Database: onside
- User: tobymorning

Tests follow Red-Green-Refactor TDD methodology:
1. Write failing tests (Red)
2. Implement functionality to make tests pass (Green)
3. Refactor while maintaining passing tests
"""
import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import patch, MagicMock
import json
from sqlalchemy import text, Table, MetaData, Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
import os

from src.utilities.query_optimizer import (
    QueryOptimizer,
    QueryCache,
    QueryStats,
    optimized_query
)
from src.utilities.error_reporting import ErrorReporter

# BDD-style test scenarios
class TestQueryOptimizer:
    """
    Feature: Database Query Optimization
    As a system admin
    I want optimized database queries with proper indexes
    So the system remains responsive under load
    """
    
    def setup_method(self):
        """Set up test environment before each test."""
        QueryOptimizer.clear_query_stats()
        QueryCache.clear()
    
    @pytest.mark.asyncio
    async def test_query_hash_generation(self):
        """
        Scenario: Query hash generation
        Given a SQL query
        When I generate a hash for the query
        Then it should return a consistent hash value
        """
        # Given
        query = "SELECT * FROM users WHERE id = 1"
        
        # When
        hash1 = QueryOptimizer.hash_query(query)
        hash2 = QueryOptimizer.hash_query(query)
        
        # Then
        assert isinstance(hash1, str)
        assert len(hash1) > 0
        assert hash1 == hash2  # Hash should be consistent
        
        # When - different query
        different_query = "SELECT * FROM users WHERE id = 2"
        different_hash = QueryOptimizer.hash_query(different_query)
        
        # Then
        assert hash1 != different_hash  # Different queries have different hashes
    
    @pytest.mark.asyncio
    async def test_record_query_stats(self):
        """
        Scenario: Recording query statistics
        Given a SQL query
        When I record execution statistics for the query
        Then the statistics should be stored correctly
        """
        # Given
        query = "SELECT * FROM users WHERE active = true"
        duration = 0.25  # seconds
        row_count = 10
        
        # When
        QueryOptimizer.record_query_stats(query, duration, row_count)
        
        # Then
        stats = QueryOptimizer.get_query_stats()
        assert len(stats) == 1
        assert stats[0]["query_text"] == query
        assert stats[0]["execution_count"] == 1
        assert stats[0]["avg_duration"] == duration
        assert stats[0]["row_count"] == row_count
        
        # When - record another execution
        QueryOptimizer.record_query_stats(query, 0.35, 15)
        
        # Then - stats should be updated
        stats = QueryOptimizer.get_query_stats()
        assert len(stats) == 1
        assert stats[0]["execution_count"] == 2
        assert stats[0]["avg_duration"] == (0.25 + 0.35) / 2
        assert stats[0]["min_duration"] == 0.25
        assert stats[0]["max_duration"] == 0.35
        assert stats[0]["row_count"] == 15  # Most recent count
    
    @pytest.mark.asyncio
    async def test_query_caching(self):
        """
        Scenario: Query result caching
        Given a SQL query and parameters
        When I cache the query result
        Then I should be able to retrieve it from the cache
        """
        # Given
        query = "SELECT * FROM companies WHERE sector = :sector"
        params = {"sector": "technology"}
        result = [{"id": 1, "name": "TechCorp"}]
        
        # When
        cache_key = QueryCache.cache_key(query, params)
        QueryCache.set(cache_key, result, ttl=60)
        
        # Then
        cached = QueryCache.get(cache_key)
        assert cached is not None
        assert cached["data"] == result
        
        # When - cache with different params
        different_params = {"sector": "healthcare"}
        different_key = QueryCache.cache_key(query, different_params)
        assert different_key != cache_key
        
        # Then - should not be in cache
        assert QueryCache.get(different_key) is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """
        Scenario: Cache entry expiration
        Given a cached query result with a short TTL
        When the TTL expires
        Then the cached result should no longer be available
        """
        # Given
        query = "SELECT * FROM test_cache_expiration"
        result = [{"test": "data"}]
        cache_key = QueryCache.cache_key(query)
        
        # When - cache with 1 second TTL
        QueryCache.set(cache_key, result, ttl=1)
        
        # Then - initially in cache
        assert QueryCache.get(cache_key) is not None
        
        # When - wait for expiration
        await asyncio.sleep(1.1)
        
        # Then - should be expired
        assert QueryCache.get(cache_key) is None
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """
        Scenario: Cache invalidation by table name
        Given cached query results for different tables
        When I invalidate cache for a specific table
        Then only entries for that table should be removed
        """
        # Given
        query1 = "SELECT * FROM users WHERE id = 1"
        query2 = "SELECT * FROM companies WHERE id = 1"
        
        # Cache both queries
        key1 = QueryCache.cache_key(query1)
        key2 = QueryCache.cache_key(query2)
        QueryCache.set(key1, ["user1"], ttl=60)
        QueryCache.set(key2, ["company1"], ttl=60)
        
        # Add query text to cached entries for table detection
        _query_cache = QueryCache._QueryCache__dict__["_query_cache"]
        _query_cache[key1]["query_text"] = query1
        _query_cache[key2]["query_text"] = query2
        
        # When - invalidate users table cache
        QueryCache.invalidate_by_table("users")
        
        # Then - users query should be gone, companies still there
        assert QueryCache.get(key1) is None
        assert QueryCache.get(key2) is not None
    
    @pytest.mark.asyncio
    async def test_optimized_query_decorator(self, test_db: AsyncSession):
        """
        Scenario: Query optimization with decorator
        Given a function that returns a query
        When I decorate it with optimized_query
        Then the query should be executed with timing and caching
        """
        # Define a test query function
        @optimized_query(ttl=60)
        async def test_query(session):
            return text("SELECT 1 as test_value")
        
        # When - execute the query
        with patch.object(QueryOptimizer, 'record_query_stats') as mock_record:
            with patch.object(QueryCache, 'set') as mock_cache:
                result = await test_query(test_db)
                
                # Then - should return correct result
                assert result == 1
                
                # Then - should record stats and cache
                mock_record.assert_called_once()
                mock_cache.assert_called_once()


class TestQueryAnalysis:
    """
    Feature: Query Analysis and Index Recommendations
    As a database administrator
    I want to identify slow queries and optimize them
    So our database performance improves
    """
    
    @pytest.mark.asyncio
    async def test_analyze_query_plan(self):
        """
        Scenario: Query plan analysis
        Given a query execution plan
        When I analyze the plan
        Then it should identify optimization opportunities
        """
        # Given - mock query plan
        mock_plan = {
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": "large_table",
                "Plan Rows": 2000,
                "Total Cost": 100,
                "Filter": "column1 = 'value'"
            },
            "Planning Time": 0.5,
            "Execution Time": 600.0  # Deliberately slow for testing
        }
        
        # When
        analysis = QueryOptimizer._analyze_query_plan(mock_plan)
        
        # Then
        assert analysis["is_slow"] == True
        assert len(analysis["sequential_scans"]) == 1
        assert analysis["sequential_scans"][0]["table"] == "large_table"
        assert len(analysis["missing_indexes"]) == 1
        assert "column1" in analysis["missing_indexes"][0]["columns"]
        assert len(analysis["recommendations"]) >= 2  # Should have at least 2 recommendations
    
    @pytest.mark.asyncio
    async def test_real_db_connection(self, test_db: AsyncSession):
        """
        Scenario: Connecting to real PostgreSQL database
        Given a database session
        When I execute a simple query
        Then it should connect to the real database successfully
        """
        # This test verifies we're connecting to the actual PostgreSQL database
        # per Semantic Seed Venture Studio Coding Standards
        
        # When - execute simple query
        result = await test_db.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        
        # Then - should connect to the actual database
        # Note: In test environment, this might be a test schema but still uses real PostgreSQL
        assert db_name is not None
        assert isinstance(db_name, str)


if __name__ == "__main__":
    pytest.main(["-v", "test_query_optimizer.py"])
