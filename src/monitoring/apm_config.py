"""
Application Performance Monitoring (APM) Configuration
Supports New Relic, DataDog, and other APM providers
"""

import os
import time
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import asynccontextmanager
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

logger = logging.getLogger(__name__)

class APMMetrics:
    """Custom metrics collector for APM integration"""
    
    def __init__(self):
        self.metrics = {}
        self.custom_metrics = {}
        
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        if tags is None:
            tags = {}
        
        metric_key = f"{name}:{','.join([f'{k}:{v}' for k, v in sorted(tags.items())])}"
        if metric_key not in self.metrics:
            self.metrics[metric_key] = 0
        self.metrics[metric_key] += value
        
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram metric (response times, etc.)"""
        if tags is None:
            tags = {}
            
        metric_data = {
            'name': name,
            'value': value,
            'tags': tags,
            'timestamp': time.time()
        }
        
        if name not in self.custom_metrics:
            self.custom_metrics[name] = []
        self.custom_metrics[name].append(metric_data)
        
    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a gauge metric (memory usage, active connections, etc.)"""
        if tags is None:
            tags = {}
            
        metric_key = f"gauge:{name}"
        self.metrics[metric_key] = {
            'value': value,
            'tags': tags,
            'timestamp': time.time()
        }

# Global APM metrics instance
apm_metrics = APMMetrics()

class NewRelicConfig:
    """New Relic APM configuration"""
    
    def __init__(self):
        self.app_name = os.getenv("NEW_RELIC_APP_NAME", "OnSide-API")
        self.license_key = os.getenv("NEW_RELIC_LICENSE_KEY", "")
        self.enabled = os.getenv("NEW_RELIC_ENABLED", "false").lower() == "true"
        
    def initialize(self):
        """Initialize New Relic agent"""
        if not self.enabled or not self.license_key:
            logger.warning("New Relic APM not enabled or license key missing")
            return
            
        try:
            import newrelic.agent
            newrelic.agent.initialize()
            logger.info("New Relic APM initialized successfully")
        except ImportError:
            logger.warning("New Relic agent not installed. Run: pip install newrelic")
        except Exception as e:
            logger.error(f"Failed to initialize New Relic: {e}")

class DataDogConfig:
    """DataDog APM configuration"""
    
    def __init__(self):
        self.api_key = os.getenv("DATADOG_API_KEY", "")
        self.app_key = os.getenv("DATADOG_APP_KEY", "")
        self.service_name = os.getenv("DATADOG_SERVICE_NAME", "onside-api")
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.enabled = os.getenv("DATADOG_ENABLED", "false").lower() == "true"
        
    def initialize(self):
        """Initialize DataDog tracing"""
        if not self.enabled or not self.api_key:
            logger.warning("DataDog APM not enabled or API key missing")
            return
            
        try:
            from ddtrace import patch_all, config
            patch_all()
            
            config.service = self.service_name
            config.env = self.environment
            
            logger.info("DataDog APM initialized successfully")
        except ImportError:
            logger.warning("DataDog tracing not installed. Run: pip install ddtrace")
        except Exception as e:
            logger.error(f"Failed to initialize DataDog: {e}")

def track_api_performance(func: Callable) -> Callable:
    """Decorator to track API endpoint performance"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            status = "success"
            
            # Record success metrics
            apm_metrics.increment_counter(
                "api.requests.total",
                tags={"endpoint": endpoint_name, "status": status}
            )
            
            return result
            
        except Exception as e:
            status = "error"
            error_type = type(e).__name__
            
            # Record error metrics
            apm_metrics.increment_counter(
                "api.requests.total",
                tags={"endpoint": endpoint_name, "status": status}
            )
            apm_metrics.increment_counter(
                "api.errors.total",
                tags={"endpoint": endpoint_name, "error_type": error_type}
            )
            
            logger.error(f"API error in {endpoint_name}: {e}", exc_info=True)
            raise
            
        finally:
            # Record response time
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            apm_metrics.record_histogram(
                "api.response_time",
                duration,
                tags={"endpoint": endpoint_name, "status": status}
            )
            
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint_name = func.__name__
        
        try:
            result = func(*args, **kwargs)
            status = "success"
            
            # Record success metrics
            apm_metrics.increment_counter(
                "api.requests.total",
                tags={"endpoint": endpoint_name, "status": status}
            )
            
            return result
            
        except Exception as e:
            status = "error"
            error_type = type(e).__name__
            
            # Record error metrics
            apm_metrics.increment_counter(
                "api.requests.total",
                tags={"endpoint": endpoint_name, "status": status}
            )
            apm_metrics.increment_counter(
                "api.errors.total",
                tags={"endpoint": endpoint_name, "error_type": error_type}
            )
            
            logger.error(f"API error in {endpoint_name}: {e}", exc_info=True)
            raise
            
        finally:
            # Record response time
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            apm_metrics.record_histogram(
                "api.response_time",
                duration,
                tags={"endpoint": endpoint_name, "status": status}
            )
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def track_database_performance(func: Callable) -> Callable:
    """Decorator to track database query performance"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            status = "success"
            
            # Record success metrics
            apm_metrics.increment_counter(
                "database.queries.total",
                tags={"operation": operation_name, "status": status}
            )
            
            return result
            
        except Exception as e:
            status = "error"
            error_type = type(e).__name__
            
            # Record error metrics
            apm_metrics.increment_counter(
                "database.queries.total",
                tags={"operation": operation_name, "status": status}
            )
            apm_metrics.increment_counter(
                "database.errors.total",
                tags={"operation": operation_name, "error_type": error_type}
            )
            
            logger.error(f"Database error in {operation_name}: {e}", exc_info=True)
            raise
            
        finally:
            # Record query time
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            apm_metrics.record_histogram(
                "database.query_time",
                duration,
                tags={"operation": operation_name, "status": status}
            )
            
    return async_wrapper

def track_external_api_performance(api_name: str):
    """Decorator to track external API call performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = "success"
                
                # Record success metrics
                apm_metrics.increment_counter(
                    "external_api.requests.total",
                    tags={"api": api_name, "status": status}
                )
                
                return result
                
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                
                # Record error metrics
                apm_metrics.increment_counter(
                    "external_api.requests.total",
                    tags={"api": api_name, "status": status}
                )
                apm_metrics.increment_counter(
                    "external_api.errors.total",
                    tags={"api": api_name, "error_type": error_type}
                )
                
                logger.error(f"External API error for {api_name}: {e}", exc_info=True)
                raise
                
            finally:
                # Record response time
                duration = (time.time() - start_time) * 1000
                apm_metrics.record_histogram(
                    "external_api.response_time",
                    duration,
                    tags={"api": api_name, "status": status}
                )
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                status = "success"
                
                # Record success metrics
                apm_metrics.increment_counter(
                    "external_api.requests.total",
                    tags={"api": api_name, "status": status}
                )
                
                return result
                
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                
                # Record error metrics
                apm_metrics.increment_counter(
                    "external_api.requests.total",
                    tags={"api": api_name, "status": status}
                )
                apm_metrics.increment_counter(
                    "external_api.errors.total",
                    tags={"api": api_name, "error_type": error_type}
                )
                
                logger.error(f"External API error for {api_name}: {e}", exc_info=True)
                raise
                
            finally:
                # Record response time
                duration = (time.time() - start_time) * 1000
                apm_metrics.record_histogram(
                    "external_api.response_time",
                    duration,
                    tags={"api": api_name, "status": status}
                )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

class BusinessMetrics:
    """Track business-specific metrics"""
    
    @staticmethod
    def track_report_generation(company_name: str, report_type: str, success: bool, duration_ms: float):
        """Track report generation metrics"""
        status = "success" if success else "failure"
        
        apm_metrics.increment_counter(
            "business.reports.generated",
            tags={"report_type": report_type, "status": status}
        )
        
        apm_metrics.record_histogram(
            "business.report.generation_time",
            duration_ms,
            tags={"report_type": report_type, "status": status}
        )
        
    @staticmethod
    def track_user_activity(user_id: str, action: str):
        """Track user activity metrics"""
        apm_metrics.increment_counter(
            "business.user.actions",
            tags={"action": action}
        )
        
    @staticmethod
    def track_pdf_export(success: bool, size_bytes: int = None):
        """Track PDF export metrics"""
        status = "success" if success else "failure"
        
        apm_metrics.increment_counter(
            "business.pdf.exports",
            tags={"status": status}
        )
        
        if success and size_bytes:
            apm_metrics.record_histogram(
                "business.pdf.size_bytes",
                size_bytes,
                tags={"status": status}
            )

def initialize_apm():
    """Initialize all APM providers"""
    # Initialize New Relic
    newrelic_config = NewRelicConfig()
    newrelic_config.initialize()
    
    # Initialize DataDog
    datadog_config = DataDogConfig()
    datadog_config.initialize()
    
    logger.info("APM initialization completed")

async def apm_middleware(request: Request, call_next):
    """FastAPI middleware for APM tracking"""
    start_time = time.time()
    
    # Generate correlation ID for request tracking
    correlation_id = f"req_{int(time.time() * 1000000)}"
    request.state.correlation_id = correlation_id
    
    # Track request
    method = request.method
    path = request.url.path
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        status = "success" if status_code < 400 else "error"
        
        # Record metrics
        apm_metrics.increment_counter(
            "http.requests.total",
            tags={"method": method, "path": path, "status_code": str(status_code)}
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
        
    except Exception as e:
        # Record error
        apm_metrics.increment_counter(
            "http.requests.total",
            tags={"method": method, "path": path, "status_code": "500"}
        )
        apm_metrics.increment_counter(
            "http.errors.total",
            tags={"method": method, "path": path, "error_type": type(e).__name__}
        )
        
        logger.error(f"Request error: {e}", extra={"correlation_id": correlation_id}, exc_info=True)
        raise
        
    finally:
        # Record response time
        duration = (time.time() - start_time) * 1000
        apm_metrics.record_histogram(
            "http.response_time",
            duration,
            tags={"method": method, "path": path}
        )