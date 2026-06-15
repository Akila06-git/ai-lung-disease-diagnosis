from __future__ import annotations

"""Celery application configuration for the Django project."""

import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self) -> str:
    """Simple debug task to verify Celery is working."""
    return f"Request: {self.request!r}"

