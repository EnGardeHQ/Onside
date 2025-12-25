"""
Celery Application Configuration

This module configures Celery for handling background tasks including:
- Report generation
- Web scraping batch jobs
- Data ingestion from external APIs
- Email delivery
- Scheduled analytics calculations
"""
import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
from src.core.config import settings

# Create Celery application
celery_app = Celery(
    "onside",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.tasks.report_tasks",
        "src.tasks.scraping_tasks",
        "src.tasks.analytics_tasks",
        "src.tasks.email_tasks",
        "src.tasks.data_ingestion_tasks",
    ]
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,

    # Result backend settings
    result_expires=3600 * 24,  # Results expire after 24 hours
    result_persistent=True,

    # Task execution settings
    task_acks_late=True,  # Task acknowledgement after execution
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # Prevent worker from prefetching too many tasks

    # Retry settings
    task_default_retry_delay=60,  # Retry after 60 seconds
    task_max_retries=3,

    # Task routes - route tasks to specific queues
    task_routes={
        "src.tasks.report_tasks.*": {"queue": "reports"},
        "src.tasks.scraping_tasks.*": {"queue": "scraping"},
        "src.tasks.analytics_tasks.*": {"queue": "analytics"},
        "src.tasks.email_tasks.*": {"queue": "emails"},
        "src.tasks.data_ingestion_tasks.*": {"queue": "data_ingestion"},
    },

    # Queue definitions with priorities
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default", priority=5),
        Queue("reports", Exchange("reports"), routing_key="reports", priority=7),
        Queue("scraping", Exchange("scraping"), routing_key="scraping", priority=6),
        Queue("analytics", Exchange("analytics"), routing_key="analytics", priority=8),
        Queue("emails", Exchange("emails"), routing_key="emails", priority=4),
        Queue("data_ingestion", Exchange("data_ingestion"), routing_key="data_ingestion", priority=6),
    ),

    # Default queue
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",

    # Worker settings
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks to prevent memory leaks
    worker_disable_rate_limits=False,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Celery Beat Schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Daily analytics calculation at 2 AM UTC
    "calculate-daily-analytics": {
        "task": "src.tasks.analytics_tasks.calculate_daily_analytics",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "analytics"},
    },

    # Hourly competitive intelligence scraping
    "scrape-competitor-updates": {
        "task": "src.tasks.scraping_tasks.scrape_competitor_updates",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"queue": "scraping"},
    },

    # Weekly report generation on Mondays at 8 AM UTC
    "generate-weekly-reports": {
        "task": "src.tasks.report_tasks.generate_weekly_reports",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
        "options": {"queue": "reports"},
    },

    # Daily data ingestion from external APIs at 3 AM UTC
    "ingest-external-data": {
        "task": "src.tasks.data_ingestion_tasks.ingest_all_external_data",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "data_ingestion"},
    },

    # Clean up old task results every day at 4 AM UTC
    "cleanup-old-results": {
        "task": "src.tasks.maintenance_tasks.cleanup_old_results",
        "schedule": crontab(hour=4, minute=0),
        "options": {"queue": "default"},
    },
}

# Task annotations for fine-grained control
celery_app.conf.task_annotations = {
    "src.tasks.report_tasks.generate_report_task": {
        "rate_limit": "10/m",  # Max 10 report generations per minute
        "time_limit": 600,  # 10 minutes max
    },
    "src.tasks.scraping_tasks.scrape_domain_task": {
        "rate_limit": "30/m",  # Max 30 scrapes per minute
        "time_limit": 300,  # 5 minutes max
    },
    "src.tasks.email_tasks.send_email_task": {
        "rate_limit": "100/m",  # Max 100 emails per minute
        "max_retries": 5,
    },
}

if __name__ == "__main__":
    celery_app.start()
