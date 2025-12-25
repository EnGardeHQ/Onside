"""
Database Query Optimizer Service (S5-03)

This module implements database query optimization utilities as specified in 
Sprint 5 story S5-03. Following Semantic Seed Venture Studio Coding Standards V2.0,
it connects to the actual PostgreSQL database and implements:

1. Query performance analysis
2. Index recommendation
3. Query caching mechanism with TTL support
4. Query execution statistics collection

All optimizations are tested against the real schema to ensure compatibility and performance.
"""
import time
import asyncio
import logging
import hashlib
import json
import datetime
from typing import Dict, Any, Optional, List, Tuple, Callable, Union
from functools import wraps
from sqlalchemy import text, Table, MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import CursorResult
from sqlalchemy.sql import Select, Insert, Update, Delete
from sqlalchemy.exc import SQLAlchemyError

from src.utilities.error_reporting import ErrorReporter, ErrorSeverity, with_error_reporting

# Configure logger
logger = logging.getLogger(__name__)

# Global cache for query results
_query_cache: Dict[str, Dict[str, Any]] = {}

class QueryStats:
    """Statistics for query execution."""
    
    def __init__(self, query_hash: str, query_text: str):
        """Initialize query statistics.
        
        Args:
            query_hash: Hash identifier of the query
            query_text: Original query text/statement
        """
        self.query_hash = query_hash
        self.query_text = query_text
        self.execution_count = 0
        self.total_duration = 0.0
        self.min_duration = float('inf')
        self.max_duration = 0.0
        self.avg_duration = 0.0
        self.last_executed = None
        self.row_count = 0
    
    def record_execution(self, duration: float, row_count: int):
        """Record a query execution.
        
        Args:
            duration: Execution time in seconds
            row_count: Number of rows returned/affected
        """
        self.execution_count += 1
        self.total_duration += duration
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        self.avg_duration = self.total_duration / self.execution_count
        self.last_executed = datetime.datetime.now()
        self.row_count = row_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "query_hash": self.query_hash,
            "query_text": self.query_text,
            "execution_count": self.execution_count,
            "total_duration": self.total_duration,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "avg_duration": self.avg_duration,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "row_count": self.row_count
        }


class QueryOptimizer:
    """Service for optimizing database queries."""
    
    # Store query statistics for analysis
    _query_stats: Dict[str, QueryStats] = {}
    
    # Slow query threshold in seconds
    _slow_query_threshold = 0.5
    
    @classmethod
    def hash_query(cls, query_obj: Union[str, Select, Insert, Update, Delete]) -> str:
        """Create a hash for a query to use as a cache key.
        
        Args:
            query_obj: SQL query as string or SQLAlchemy statement
            
        Returns:
            String hash of the query
        """
        if isinstance(query_obj, str):
            query_str = query_obj
        else:
            # Convert SQLAlchemy statement to string
            query_str = str(query_obj)
        
        # Create MD5 hash of the query string
        return hashlib.md5(query_str.encode('utf-8')).hexdigest()
    
    @classmethod
    async def analyze_query(cls, session: AsyncSession, query: str) -> Dict[str, Any]:
        """Analyze a query for performance insights.
        
        Args:
            session: Database session
            query: SQL query to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Use PostgreSQL EXPLAIN ANALYZE to get query plan
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            result = await session.execute(text(explain_query))
            plan_json = result.scalar()
            
            # Extract key metrics from the query plan
            if isinstance(plan_json, str):
                plan_data = json.loads(plan_json)
            else:
                plan_data = plan_json
                
            # Analyze the plan and identify bottlenecks
            analysis = cls._analyze_query_plan(plan_data[0])
            
            return {
                "query": query,
                "query_hash": cls.hash_query(query),
                "plan": plan_data,
                "analysis": analysis
            }
        except Exception as e:
            ErrorReporter.report(
                message=f"Failed to analyze query: {str(e)}",
                severity=ErrorSeverity.ERROR,
                exception=e,
                context={"query": query}
            )
            return {
                "query": query,
                "query_hash": cls.hash_query(query),
                "error": str(e)
            }
    
    @classmethod
    def _analyze_query_plan(cls, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a query execution plan for optimization opportunities.
        
        Args:
            plan_data: Query plan data from EXPLAIN ANALYZE
            
        Returns:
            Dictionary with analysis and recommendations
        """
        analysis = {
            "execution_time": plan_data.get("Execution Time", 0) / 1000,  # Convert to seconds
            "planning_time": plan_data.get("Planning Time", 0) / 1000,    # Convert to seconds
            "is_slow": False,
            "sequential_scans": [],
            "missing_indexes": [],
            "recommendations": []
        }
        
        # Check if query is considered slow
        if analysis["execution_time"] > cls._slow_query_threshold:
            analysis["is_slow"] = True
            analysis["recommendations"].append(
                f"Query is slow ({analysis['execution_time']:.4f}s). Consider optimization."
            )
        
        # Recursively analyze the plan tree
        cls._analyze_plan_node(plan_data["Plan"], analysis)
        
        return analysis
    
    @classmethod
    def _analyze_plan_node(cls, node: Dict[str, Any], analysis: Dict[str, Any], path: str = ""):
        """Recursively analyze a node in the query plan.
        
        Args:
            node: Plan node
            analysis: Analysis result to update
            path: Path to this node in the plan tree
        """
        node_type = node.get("Node Type", "")
        node_path = f"{path}/{node_type}" if path else node_type
        
        # Check for sequential scans (often indicate missing indexes)
        if node_type == "Seq Scan":
            table_name = node.get("Relation Name", "unknown")
            rows = node.get("Plan Rows", 0)
            cost = node.get("Total Cost", 0)
            
            analysis["sequential_scans"].append({
                "table": table_name,
                "rows": rows,
                "cost": cost
            })
            
            # Only recommend indexes for larger tables
            if rows > 1000:
                filter_cond = node.get("Filter", "")
                if filter_cond:
                    # Extract potential columns for indexing from filter
                    columns = cls._extract_columns_from_filter(filter_cond)
                    if columns:
                        analysis["missing_indexes"].append({
                            "table": table_name,
                            "columns": columns
                        })
                        analysis["recommendations"].append(
                            f"Consider adding an index on {table_name}({', '.join(columns)})"
                        )
        
        # Check for nested loops with many iterations
        elif node_type == "Nested Loop" and node.get("Plan Rows", 0) > 1000:
            analysis["recommendations"].append(
                f"Large nested loop detected. Consider optimizing joins or adding indexes."
            )
        
        # Recursively analyze child nodes
        for child_key in ["Plans", "Subplans"]:
            if child_key in node and isinstance(node[child_key], list):
                for i, child in enumerate(node[child_key]):
                    cls._analyze_plan_node(child, analysis, f"{node_path}/{i}")
    
    @classmethod
    def _extract_columns_from_filter(cls, filter_str: str) -> List[str]:
        """Extract potential column names from a filter condition.
        
        Args:
            filter_str: Filter condition string from query plan
            
        Returns:
            List of potential column names
        """
        # Simple extraction based on common patterns
        # This is a simplified version; a real implementation would use SQL parsing
        columns = []
        
        # Look for patterns like "column_name = constant"
        parts = filter_str.split(" AND ")
        for part in parts:
            for op in ["=", ">", "<", ">=", "<=", "LIKE"]:
                if op in part:
                    col_part = part.split(op)[0].strip()
                    # Remove table aliases and quotes
                    if "." in col_part:
                        col_part = col_part.split(".")[-1]
                    col_part = col_part.strip('"\'')
                    if col_part:
                        columns.append(col_part)
        
        return columns
    
    @classmethod
    def suggest_indexes(cls, session: AsyncSession, table_name: str) -> List[Dict[str, Any]]:
        """Suggest potential indexes for a table based on query patterns.
        
        Args:
            session: Database session
            table_name: Name of the table to analyze
            
        Returns:
            List of suggested indexes
        """
        # Get queries targeting this table
        table_queries = {}
        for query_hash, stats in cls._query_stats.items():
            if table_name.lower() in stats.query_text.lower():
                table_queries[query_hash] = stats
        
        # Analyze frequently executed and slow queries
        suggestions = []
        for query_hash, stats in table_queries.items():
            if (stats.avg_duration > cls._slow_query_threshold or 
                stats.execution_count > 10):
                suggestions.append({
                    "query_hash": query_hash,
                    "avg_duration": stats.avg_duration,
                    "execution_count": stats.execution_count,
                    "query": stats.query_text
                })
        
        return suggestions
    
    @classmethod
    def record_query_stats(cls, query_obj: Union[str, Select, Insert, Update, Delete], 
                          duration: float, row_count: int):
        """Record statistics for a query execution.
        
        Args:
            query_obj: SQL query as string or SQLAlchemy statement
            duration: Execution time in seconds
            row_count: Number of rows returned/affected
        """
        query_hash = cls.hash_query(query_obj)
        
        if isinstance(query_obj, str):
            query_text = query_obj
        else:
            query_text = str(query_obj)
        
        # Create or update stats
        if query_hash not in cls._query_stats:
            cls._query_stats[query_hash] = QueryStats(query_hash, query_text)
        
        stats = cls._query_stats[query_hash]
        stats.record_execution(duration, row_count)
        
        # Log slow queries
        if duration > cls._slow_query_threshold:
            logger.warning(
                f"Slow query detected ({duration:.4f}s): {query_text[:100]}..."
            )
    
    @classmethod
    def get_query_stats(cls, limit: int = 100) -> List[Dict[str, Any]]:
        """Get statistics for all tracked queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query statistics
        """
        # Sort by average duration (slowest first)
        sorted_stats = sorted(
            cls._query_stats.values(),
            key=lambda s: s.avg_duration,
            reverse=True
        )
        
        return [stats.to_dict() for stats in sorted_stats[:limit]]
    
    @classmethod
    def clear_query_stats(cls):
        """Clear all tracked query statistics."""
        cls._query_stats.clear()
    
    @classmethod
    def set_slow_query_threshold(cls, threshold_seconds: float):
        """Set the threshold for identifying slow queries.
        
        Args:
            threshold_seconds: Threshold in seconds
        """
        cls._slow_query_threshold = threshold_seconds


class QueryCache:
    """Cache for database query results with TTL support."""
    
    @staticmethod
    def cache_key(query_obj: Union[str, Select, Insert, Update, Delete], 
                params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a cache key for a query.
        
        Args:
            query_obj: SQL query as string or SQLAlchemy statement
            params: Query parameters
            
        Returns:
            Cache key string
        """
        query_hash = QueryOptimizer.hash_query(query_obj)
        
        if params:
            # Include parameters in the cache key
            params_str = json.dumps(params, sort_keys=True)
            return f"{query_hash}:{hashlib.md5(params_str.encode('utf-8')).hexdigest()}"
        
        return query_hash
    
    @staticmethod
    def get(key: str) -> Optional[Dict[str, Any]]:
        """Get a cached query result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None if not found or expired
        """
        if key not in _query_cache:
            return None
        
        cached = _query_cache[key]
        
        # Check if expired
        if "expires_at" in cached and cached["expires_at"] <= time.time():
            # Remove expired entry
            del _query_cache[key]
            return None
        
        return cached
    
    @staticmethod
    def set(key: str, value: Any, ttl: Optional[int] = None):
        """Store a query result in the cache.
        
        Args:
            key: Cache key
            value: Result to cache
            ttl: Time-to-live in seconds, or None for no expiration
        """
        cached = {
            "data": value,
            "cached_at": time.time()
        }
        
        if ttl is not None:
            cached["expires_at"] = time.time() + ttl
        
        _query_cache[key] = cached
    
    @staticmethod
    def invalidate(key: str):
        """Remove a specific item from the cache.
        
        Args:
            key: Cache key to invalidate
        """
        if key in _query_cache:
            del _query_cache[key]
    
    @staticmethod
    def invalidate_by_table(table_name: str):
        """Invalidate all cache entries related to a specific table.
        
        Args:
            table_name: Name of the table
        """
        keys_to_remove = []
        
        for key, cached in _query_cache.items():
            # Check if the query text contains the table name
            query_text = cached.get("query_text", "")
            if table_name.lower() in query_text.lower():
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del _query_cache[key]
    
    @staticmethod
    def clear():
        """Clear the entire query cache."""
        _query_cache.clear()


def optimized_query(ttl: Optional[int] = None):
    """Decorator for optimizing SQLAlchemy queries with caching and stats.
    
    Args:
        ttl: Cache time-to-live in seconds, or None to disable caching
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Only optimize if the first argument is a session
            if not args or not isinstance(args[0], AsyncSession):
                return await func(*args, **kwargs)
            
            try:
                # Execute the original function to get the query
                query_obj = await func(*args, **kwargs)
                
                if query_obj is None:
                    return None
                
                # Get session from args
                session = args[0]
                
                # Generate cache key if caching is enabled
                cache_key = None
                if ttl is not None:
                    cache_key = QueryCache.cache_key(query_obj, kwargs)
                    cached = QueryCache.get(cache_key)
                    if cached:
                        return cached["data"]
                
                # Execute the query with timing
                start_time = time.time()
                result = await session.execute(query_obj)
                duration = time.time() - start_time
                
                # Check result type and process accordingly
                if hasattr(result, "scalars"):
                    # Handle multiple rows
                    rows = list(result.scalars().all())
                    row_count = len(rows)
                    final_result = rows
                elif hasattr(result, "scalar"):
                    # Handle single value
                    value = result.scalar()
                    row_count = 1 if value is not None else 0
                    final_result = value
                else:
                    # Default handling
                    rows = list(result)
                    row_count = len(rows)
                    final_result = rows
                
                # Record query statistics
                QueryOptimizer.record_query_stats(query_obj, duration, row_count)
                
                # Cache if enabled
                if ttl is not None and cache_key:
                    QueryCache.set(
                        cache_key, 
                        final_result, 
                        ttl=ttl
                    )
                
                return final_result
            except Exception as e:
                ErrorReporter.report(
                    message=f"Query optimization error: {str(e)}",
                    severity=ErrorSeverity.ERROR,
                    exception=e,
                    context={"function": func.__name__}
                )
                # Fall back to original function
                return await func(*args, **kwargs)
        return wrapper
    return decorator
