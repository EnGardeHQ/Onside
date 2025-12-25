"""
BDD Tests for Error Reporting Service (S5-02)

This module implements BDD-style tests for the standardized error reporting service
following the Semantic Seed Venture Studio Coding Standards V2.0.

The tests follow the Red-Green-Refactor TDD methodology:
1. Write failing tests (Red)
2. Implement functionality to make tests pass (Green)
3. Refactor while maintaining passing tests
"""
import pytest
import asyncio
import logging
from unittest.mock import MagicMock, patch
import json

from src.utilities.error_reporting import (
    ErrorReporter, 
    ErrorSeverity, 
    ErrorReport,
    with_error_reporting
)

# BDD-style test scenarios
class TestErrorReporting:
    """
    Feature: Standardized Error Reporting
    As a developer
    I want standardized error reporting across all services
    So we can quickly identify and fix issues
    """
    
    def setup_method(self):
        """Set up test environment before each test."""
        ErrorReporter.clear_recent_errors()
    
    def test_error_report_creation(self):
        """
        Scenario: Creating a basic error report
        Given an error message
        When I create an error report
        Then it should have the correct properties and default severity
        """
        # Given
        message = "Test error message"
        
        # When
        report = ErrorReport(message=message)
        
        # Then
        assert report.message == message
        assert report.severity == ErrorSeverity.ERROR
        assert report.error_id is not None
        assert report.timestamp is not None
        assert report.context == {}
        assert report.exception_type is None
        assert report.exception_message is None
        assert report.stack_trace is None
    
    def test_error_report_with_exception(self):
        """
        Scenario: Creating an error report with an exception
        Given an error message and an exception
        When I create an error report with the exception
        Then it should contain the exception details
        """
        # Given
        message = "Test error with exception"
        exception = ValueError("Test value error")
        
        # When
        try:
            raise exception
        except ValueError as e:
            report = ErrorReport(message=message, exception=e)
        
        # Then
        assert report.message == message
        assert report.exception_type == "ValueError"
        assert report.exception_message == "Test value error"
        assert report.stack_trace is not None
        assert "Traceback" in report.stack_trace
    
    def test_error_report_with_context(self):
        """
        Scenario: Creating an error report with context
        Given an error message and contextual information
        When I create an error report with context
        Then it should include the contextual information
        """
        # Given
        message = "Test error with context"
        context = {"service": "TestService", "operation": "data_processing"}
        
        # When
        report = ErrorReport(message=message, context=context)
        
        # Then
        assert report.message == message
        assert report.context == context
        
        # Verify context in JSON serialization
        json_data = json.loads(report.to_json())
        assert json_data["context"] == context
    
    def test_error_reporter_reporting(self):
        """
        Scenario: Reporting an error through the reporter
        Given an error message
        When I report it through the ErrorReporter
        Then it should be logged and stored in recent errors
        """
        # Given
        message = "Test reported error"
        
        # When
        with patch("logging.Logger.log") as mock_log:
            report = ErrorReporter.report(message=message)
        
        # Then
        assert len(ErrorReporter.get_recent_errors()) == 1
        assert ErrorReporter.get_recent_errors()[0].message == message
        mock_log.assert_called_once()
    
    def test_error_reporter_with_custom_severity(self):
        """
        Scenario: Reporting an error with custom severity
        Given an error message and a warning severity
        When I report it through the ErrorReporter
        Then it should have the specified severity
        """
        # Given
        message = "Test warning error"
        severity = ErrorSeverity.WARNING
        
        # When
        with patch("logging.Logger.log") as mock_log:
            report = ErrorReporter.report(message=message, severity=severity)
        
        # Then
        assert report.severity == ErrorSeverity.WARNING
        assert ErrorReporter.get_recent_errors()[0].severity == ErrorSeverity.WARNING
        mock_log.assert_called_once()
    
    def test_error_reporter_handling(self):
        """
        Scenario: Handling errors with registered handlers
        Given a registered error handler for critical errors
        When I report a critical error
        Then the handler should be called with the error report
        """
        # Given
        mock_handler = MagicMock()
        ErrorReporter.register_handler(ErrorSeverity.CRITICAL, mock_handler)
        
        # When
        report = ErrorReporter.report(
            message="Critical test error",
            severity=ErrorSeverity.CRITICAL
        )
        
        # Then
        mock_handler.assert_called_once()
        args, _ = mock_handler.call_args
        assert args[0] == report

    @pytest.mark.asyncio
    async def test_with_error_reporting_decorator_async(self):
        """
        Scenario: Using error reporting decorator with async function
        Given an async function decorated with error reporting
        When the function raises an exception
        Then the exception should be reported with the correct context
        """
        # Given
        @with_error_reporting(severity=ErrorSeverity.WARNING)
        async def failing_async_function():
            raise ValueError("Async test error")
        
        # When
        with pytest.raises(ValueError):
            with patch.object(ErrorReporter, "report") as mock_report:
                await failing_async_function()
        
        # Then
        mock_report.assert_called_once()
        args, kwargs = mock_report.call_args
        assert "Async test error" in kwargs["message"]
        assert kwargs["severity"] == ErrorSeverity.WARNING
        assert isinstance(kwargs["exception"], ValueError)
        assert "failing_async_function" in kwargs["context"]["function"]

    def test_with_error_reporting_decorator_sync(self):
        """
        Scenario: Using error reporting decorator with sync function
        Given a sync function decorated with error reporting
        When the function raises an exception
        Then the exception should be reported with the correct context
        """
        # Given
        @with_error_reporting(severity=ErrorSeverity.ERROR)
        def failing_sync_function():
            raise RuntimeError("Sync test error")
        
        # When
        with pytest.raises(RuntimeError):
            with patch.object(ErrorReporter, "report") as mock_report:
                failing_sync_function()
        
        # Then
        mock_report.assert_called_once()
        args, kwargs = mock_report.call_args
        assert "Sync test error" in kwargs["message"]
        assert kwargs["severity"] == ErrorSeverity.ERROR
        assert isinstance(kwargs["exception"], RuntimeError)
        assert "failing_sync_function" in kwargs["context"]["function"]


class TestErrorLogging:
    """
    Feature: Error Logging and Monitoring
    As a system admin
    I want detailed error logs and monitoring
    So I can identify and resolve issues quickly
    """
    
    def setup_method(self):
        """Set up test environment before each test."""
        ErrorReporter.clear_recent_errors()
    
    def test_error_report_logging(self):
        """
        Scenario: Logging an error report
        Given an error report
        When I call the log method
        Then it should log with the appropriate level and format
        """
        # Given
        report = ErrorReport(
            message="Test log error",
            severity=ErrorSeverity.ERROR,
            context={"source": "test_logging"}
        )
        
        # When
        with patch("logging.Logger.log") as mock_log:
            report.log()
        
        # Then
        mock_log.assert_called_once()
        args, _ = mock_log.call_args
        assert args[0] == logging.ERROR  # Check log level
        assert report.error_id in args[1]  # Check error ID in message
        assert "Test log error" in args[1]  # Check error message
        assert "source=test_logging" in args[1]  # Check context
    
    def test_critical_error_stack_trace_logging(self):
        """
        Scenario: Logging a critical error with stack trace
        Given a critical error with an exception
        When I call the log method
        Then it should log both the error and the stack trace
        """
        # Given
        try:
            raise ValueError("Critical test error")
        except ValueError as e:
            report = ErrorReport(
                message="Critical logging test",
                severity=ErrorSeverity.CRITICAL,
                exception=e
            )
        
        # When
        with patch("logging.Logger.log") as mock_log, \
             patch("logging.Logger.critical") as mock_critical:
            report.log()
        
        # Then
        mock_log.assert_called_once()
        mock_critical.assert_called_once()
        args, _ = mock_critical.call_args
        assert "Stack trace" in args[0]
        assert report.error_id in args[0]


if __name__ == "__main__":
    pytest.main(["-v", "test_error_reporting.py"])
