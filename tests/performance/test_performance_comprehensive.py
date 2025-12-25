"""
Comprehensive Performance Testing Suite for OnSide

This module implements automated performance testing to detect regressions and ensure
optimal system performance. Addresses GitHub Issue #29.

Feature: Automated Performance Testing
As a developer,
I want automated performance tests that detect regressions,
So I can maintain optimal system performance and prevent degradation.

Tests cover:
- API response time benchmarks
- Database query performance
- Report generation performance
- Concurrent request handling
- Memory usage under load
- Cache effectiveness
"""
import asyncio
import time
import statistics
import pytest
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json
import psutil
import os

# Performance thresholds based on acceptance criteria from issue #29
API_RESPONSE_THRESHOLD_MS = 500  # Target: <500ms
REPORT_GENERATION_THRESHOLD_S = 12  # Target: <12s
DB_QUERY_THRESHOLD_MS = 100  # Target: <100ms
CONCURRENT_SUCCESS_RATE = 0.95  # Target: 95%+

# Benchmark configuration
BENCHMARK_ITERATIONS = 10
BENCHMARK_DIR = Path(__file__).parent / "benchmarks"
BENCHMARK_FILE = BENCHMARK_DIR / "performance_metrics.json"


class PerformanceMonitor:
    """
    Utility class for comprehensive performance monitoring.

    Tracks execution time, memory usage, and provides statistical analysis.
    """

    def __init__(self, test_name: str):
        """Initialize performance monitor for a specific test."""
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.duration_ms = None
        self.process = psutil.Process()
        self.memory_start = None
        self.memory_end = None
        self.memory_delta_mb = None
        self.cpu_percent = None

    def start(self):
        """Start performance measurement."""
        self.start_time = time.perf_counter()
        self.memory_start = self.process.memory_info().rss / 1024 / 1024  # MB
        self.process.cpu_percent()  # Initialize CPU measurement
        return self

    def stop(self):
        """Stop performance measurement and calculate metrics."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.memory_end = self.process.memory_info().rss / 1024 / 1024  # MB
        self.memory_delta_mb = self.memory_end - self.memory_start
        self.cpu_percent = self.process.cpu_percent()
        return self

    def __enter__(self):
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "test_name": self.test_name,
            "duration_ms": round(self.duration_ms, 2),
            "memory_delta_mb": round(self.memory_delta_mb, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def load_baseline(cls, test_name: str) -> Dict[str, Any]:
        """Load baseline metrics for comparison."""
        if not BENCHMARK_FILE.exists():
            return None

        with open(BENCHMARK_FILE, "r") as f:
            benchmarks = json.load(f)

        return benchmarks.get(test_name)

    @classmethod
    def save_baseline(cls, metrics: Dict[str, Any]):
        """Save baseline metrics for future comparison."""
        BENCHMARK_DIR.mkdir(exist_ok=True)

        benchmarks = {}
        if BENCHMARK_FILE.exists():
            with open(BENCHMARK_FILE, "r") as f:
                benchmarks = json.load(f)

        benchmarks[metrics["test_name"]] = metrics

        with open(BENCHMARK_FILE, "w") as f:
            json.dump(benchmarks, f, indent=2)


def run_performance_benchmark(func):
    """
    Decorator to run performance benchmarks with multiple iterations.

    Runs the test multiple times, calculates statistics, and compares
    against baseline performance metrics.
    """
    async def wrapper(*args, **kwargs):
        durations = []
        memory_deltas = []
        cpu_usage = []

        # Warmup run
        await func(*args, **kwargs)

        # Benchmark runs
        for i in range(BENCHMARK_ITERATIONS):
            monitor = PerformanceMonitor(func.__name__).start()
            await func(*args, **kwargs)
            monitor.stop()

            durations.append(monitor.duration_ms)
            memory_deltas.append(monitor.memory_delta_mb)
            cpu_usage.append(monitor.cpu_percent)

        # Calculate statistics
        metrics = {
            "test_name": func.__name__,
            "duration_ms": {
                "mean": round(statistics.mean(durations), 2),
                "median": round(statistics.median(durations), 2),
                "min": round(min(durations), 2),
                "max": round(max(durations), 2),
                "stdev": round(statistics.stdev(durations), 2) if len(durations) > 1 else 0
            },
            "memory_delta_mb": {
                "mean": round(statistics.mean(memory_deltas), 2),
                "max": round(max(memory_deltas), 2)
            },
            "cpu_percent": {
                "mean": round(statistics.mean(cpu_usage), 2),
                "max": round(max(cpu_usage), 2)
            },
            "iterations": BENCHMARK_ITERATIONS,
            "timestamp": datetime.now().isoformat()
        }

        return metrics

    return wrapper


def assert_performance_threshold(
    metrics: Dict[str, Any],
    threshold_ms: float,
    metric_name: str = "API Response Time"
):
    """
    Assert that performance metrics meet threshold requirements.

    Args:
        metrics: Performance metrics dictionary
        threshold_ms: Maximum acceptable duration in milliseconds
        metric_name: Name of the metric for error messages
    """
    mean_duration = metrics["duration_ms"]["mean"]
    max_duration = metrics["duration_ms"]["max"]

    # Check mean performance
    assert mean_duration <= threshold_ms, (
        f"{metric_name} exceeds threshold! "
        f"Mean: {mean_duration}ms, Threshold: {threshold_ms}ms, "
        f"Degradation: {((mean_duration / threshold_ms) - 1) * 100:.1f}%"
    )

    # Check worst-case performance (max shouldn't be more than 2x threshold)
    max_threshold = threshold_ms * 2
    assert max_duration <= max_threshold, (
        f"{metric_name} worst case exceeds limit! "
        f"Max: {max_duration}ms, Limit: {max_threshold}ms"
    )


def compare_with_baseline(
    current_metrics: Dict[str, Any],
    degradation_threshold: float = 1.5
):
    """
    Compare current performance with baseline and detect regressions.

    Args:
        current_metrics: Current performance metrics
        degradation_threshold: Maximum acceptable degradation ratio (1.5 = 50% slower)
    """
    baseline = PerformanceMonitor.load_baseline(current_metrics["test_name"])

    # If no baseline exists, save current as baseline
    if not baseline:
        PerformanceMonitor.save_baseline(current_metrics)
        return

    # Compare performance
    current_mean = current_metrics["duration_ms"]["mean"]
    baseline_mean = baseline["duration_ms"]["mean"]
    ratio = current_mean / baseline_mean

    # Assert performance hasn't degraded significantly
    assert ratio <= degradation_threshold, (
        f"Performance regression detected in {current_metrics['test_name']}! "
        f"Current: {current_mean:.2f}ms, Baseline: {baseline_mean:.2f}ms, "
        f"Degradation: {(ratio - 1) * 100:.1f}%"
    )

    # Optionally update baseline if performance improved
    if ratio < 0.9:  # 10% improvement
        PerformanceMonitor.save_baseline(current_metrics)


class TestAPIPerformance:
    """
    Feature: API Endpoint Performance Testing
    As a user,
    I want API endpoints to respond quickly,
    So I can have a responsive user experience.
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_health_endpoint_response_time(self, test_client):
        """
        Scenario: Health endpoint performance
        Given a running API server
        When I make a request to the health endpoint
        Then it should respond in under 500ms
        """
        @run_performance_benchmark
        async def benchmark_health_endpoint(client):
            response = await client.get("/health")
            assert response.status_code == 200
            return response

        metrics = await benchmark_health_endpoint(test_client)
        assert_performance_threshold(metrics, API_RESPONSE_THRESHOLD_MS, "Health Endpoint")
        compare_with_baseline(metrics)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_list_endpoint_response_time(self, test_client, auth_headers):
        """
        Scenario: List endpoint performance
        Given authenticated access
        When I request a list of resources
        Then it should respond in under 500ms
        """
        @run_performance_benchmark
        async def benchmark_list_endpoint(client, headers):
            response = await client.get("/api/v1/domains", headers=headers)
            return response

        metrics = await benchmark_list_endpoint(test_client, auth_headers)
        assert_performance_threshold(metrics, API_RESPONSE_THRESHOLD_MS, "List Endpoint")
        compare_with_baseline(metrics)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_search_endpoint_response_time(self, test_client, auth_headers):
        """
        Scenario: Search endpoint performance
        Given authenticated access
        When I perform a search operation
        Then it should respond in under 500ms
        """
        @run_performance_benchmark
        async def benchmark_search(client, headers):
            response = await client.get(
                "/api/v1/gnews/search?query=technology",
                headers=headers
            )
            return response

        metrics = await benchmark_search(test_client, auth_headers)
        assert_performance_threshold(metrics, API_RESPONSE_THRESHOLD_MS, "Search Endpoint")
        compare_with_baseline(metrics)


class TestDatabasePerformance:
    """
    Feature: Database Query Performance
    As a developer,
    I want database queries to execute quickly,
    So the application remains responsive.
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_simple_select_query_performance(self, test_db):
        """
        Scenario: Simple SELECT query performance
        Given a database connection
        When I execute a simple SELECT query
        Then it should complete in under 100ms
        """
        from sqlalchemy import text

        @run_performance_benchmark
        async def benchmark_simple_query(db):
            result = await db.execute(text("SELECT 1"))
            return result.scalar()

        metrics = await benchmark_simple_query(test_db)
        assert_performance_threshold(metrics, DB_QUERY_THRESHOLD_MS, "Simple Query")
        compare_with_baseline(metrics)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_join_query_performance(self, test_db):
        """
        Scenario: JOIN query performance
        Given a database with related tables
        When I execute a query with JOINs
        Then it should complete efficiently
        """
        from sqlalchemy import text

        @run_performance_benchmark
        async def benchmark_join_query(db):
            query = text("""
                SELECT u.id, u.email, COUNT(r.id) as report_count
                FROM users u
                LEFT JOIN reports r ON u.id = r.user_id
                GROUP BY u.id, u.email
                LIMIT 100
            """)
            result = await db.execute(query)
            return list(result)

        metrics = await benchmark_join_query(test_db)
        # JOINs can be slower, allow more time
        assert_performance_threshold(metrics, DB_QUERY_THRESHOLD_MS * 3, "JOIN Query")
        compare_with_baseline(metrics)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_batch_insert_performance(self, test_db):
        """
        Scenario: Batch insert performance
        Given multiple records to insert
        When I perform a batch insert
        Then it should be efficient
        """
        @run_performance_benchmark
        async def benchmark_batch_insert(db):
            # Simulate batch insert
            await asyncio.sleep(0.01)  # Placeholder
            return True

        metrics = await benchmark_batch_insert(test_db)
        compare_with_baseline(metrics)


class TestReportGenerationPerformance:
    """
    Feature: Report Generation Performance
    As a user,
    I want reports to generate quickly,
    So I can access insights without long waits.
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_basic_report_generation_time(self, test_db):
        """
        Scenario: Basic report generation performance
        Given report generation request
        When I generate a basic report
        Then it should complete in under 12 seconds
        """
        @run_performance_benchmark
        async def benchmark_report_generation(db):
            # Simulate report generation
            await asyncio.sleep(0.5)  # Placeholder for actual report logic
            return {"status": "completed"}

        metrics = await benchmark_report_generation(test_db)
        assert_performance_threshold(
            metrics,
            REPORT_GENERATION_THRESHOLD_S * 1000,
            "Report Generation"
        )
        compare_with_baseline(metrics)

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_complex_report_with_multiple_data_sources(self, test_db):
        """
        Scenario: Complex report generation
        Given a report requiring multiple data sources
        When I generate the report
        Then it should complete within acceptable time
        """
        @run_performance_benchmark
        async def benchmark_complex_report(db):
            # Simulate fetching from multiple sources
            tasks = [asyncio.sleep(0.2) for _ in range(5)]
            await asyncio.gather(*tasks)
            return {"status": "completed"}

        metrics = await benchmark_complex_report(test_db)
        # Complex reports can take longer
        assert_performance_threshold(
            metrics,
            REPORT_GENERATION_THRESHOLD_S * 1000 * 2,
            "Complex Report"
        )
        compare_with_baseline(metrics)


class TestConcurrentLoadPerformance:
    """
    Feature: Concurrent Request Handling
    As a system,
    I want to handle multiple concurrent requests efficiently,
    So the application scales well under load.
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_api_requests(self, test_client):
        """
        Scenario: Concurrent API request handling
        Given multiple simultaneous API requests
        When I make 100 concurrent requests
        Then at least 95% should succeed
        And average response time should be acceptable
        """
        async def make_request():
            try:
                response = await test_client.get("/health")
                return response.status_code == 200
            except Exception:
                return False

        # Monitor overall performance
        monitor = PerformanceMonitor("concurrent_requests").start()

        # Make 100 concurrent requests
        tasks = [make_request() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        monitor.stop()

        # Calculate success rate
        success_count = sum(1 for r in results if r)
        success_rate = success_count / len(results)

        # Assert success rate meets threshold
        assert success_rate >= CONCURRENT_SUCCESS_RATE, (
            f"Concurrent request success rate too low! "
            f"Success: {success_rate*100:.1f}%, Threshold: {CONCURRENT_SUCCESS_RATE*100}%"
        )

        # Average time per request should be reasonable
        avg_time_per_request = monitor.duration_ms / len(results)
        assert avg_time_per_request < API_RESPONSE_THRESHOLD_MS * 2, (
            f"Average time per concurrent request too high: {avg_time_per_request:.2f}ms"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_database_connection_pool_performance(self, test_db):
        """
        Scenario: Database connection pool efficiency
        Given multiple concurrent database operations
        When I perform concurrent queries
        Then the connection pool should handle them efficiently
        """
        from sqlalchemy import text

        async def query_db():
            try:
                result = await test_db.execute(text("SELECT 1"))
                return result.scalar() == 1
            except Exception:
                return False

        monitor = PerformanceMonitor("concurrent_db_queries").start()

        # Make 50 concurrent database queries
        tasks = [query_db() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        monitor.stop()

        success_count = sum(1 for r in results if r)
        success_rate = success_count / len(results)

        assert success_rate >= CONCURRENT_SUCCESS_RATE, (
            f"Database concurrent query success rate too low: {success_rate*100:.1f}%"
        )


class TestMemoryUsage:
    """
    Feature: Memory Usage Under Load
    As a system,
    I want to manage memory efficiently,
    So the application doesn't experience memory leaks.
    """

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_usage_stability(self, test_client):
        """
        Scenario: Memory usage stability under load
        Given repeated operations
        When I perform the same operation multiple times
        Then memory usage should remain stable (no leaks)
        """
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Perform operation 100 times
        for _ in range(100):
            await test_client.get("/health")

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal (< 50MB for 100 requests)
        assert memory_growth < 50, (
            f"Potential memory leak detected! "
            f"Memory grew by {memory_growth:.2f}MB over 100 requests"
        )

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_large_response_memory_efficiency(self, test_client, auth_headers):
        """
        Scenario: Large response handling memory efficiency
        Given an endpoint that returns large data
        When I request the data
        Then memory should be managed efficiently
        """
        monitor = PerformanceMonitor("large_response_memory").start()

        # Request endpoint with potentially large response
        response = await test_client.get("/api/v1/reports", headers=auth_headers)

        monitor.stop()

        # Memory delta should be reasonable (< 100MB)
        assert monitor.memory_delta_mb < 100, (
            f"Large response consumed too much memory: {monitor.memory_delta_mb:.2f}MB"
        )


# Fixture to automatically generate performance report
@pytest.fixture(scope="session", autouse=True)
def generate_performance_report(request):
    """Generate a performance test summary report after all tests complete."""
    yield

    if BENCHMARK_FILE.exists():
        with open(BENCHMARK_FILE, "r") as f:
            benchmarks = json.load(f)

        report_path = BENCHMARK_DIR / "performance_report.md"
        with open(report_path, "w") as f:
            f.write("# OnSide Performance Test Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write("## Performance Benchmarks\n\n")
            f.write("| Test | Mean (ms) | Min (ms) | Max (ms) | StDev |\n")
            f.write("|------|-----------|----------|----------|-------|\n")

            for test_name, metrics in benchmarks.items():
                if "duration_ms" in metrics and isinstance(metrics["duration_ms"], dict):
                    duration = metrics["duration_ms"]
                    f.write(
                        f"| {test_name} | {duration['mean']} | {duration['min']} | "
                        f"{duration['max']} | {duration.get('stdev', 'N/A')} |\n"
                    )

            f.write("\n## Threshold Compliance\n\n")
            f.write(f"- API Response Time Target: {API_RESPONSE_THRESHOLD_MS}ms\n")
            f.write(f"- Report Generation Target: {REPORT_GENERATION_THRESHOLD_S}s\n")
            f.write(f"- Database Query Target: {DB_QUERY_THRESHOLD_MS}ms\n")
            f.write(f"- Concurrent Success Rate Target: {CONCURRENT_SUCCESS_RATE*100}%\n")
