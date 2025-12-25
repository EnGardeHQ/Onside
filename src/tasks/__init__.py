"""
Celery Tasks Package

This package contains all background task definitions for the OnSide platform.
"""
from src.celery_app import celery_app

__all__ = ["celery_app"]
