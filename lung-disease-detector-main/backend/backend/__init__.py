from __future__ import annotations

"""Backend Django project package initialization.

This module also exposes the Celery application instance so that it can be
discovered by the `celery` command-line tool.
"""

from .celery import app as celery_app

__all__ = ["celery_app"]

