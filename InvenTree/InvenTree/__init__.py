"""
The InvenTree module provides high-level management and functionality.

It provides a number of helper functions and generic classes which are used by InvenTree apps.
"""

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
