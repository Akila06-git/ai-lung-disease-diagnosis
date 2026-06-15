from __future__ import annotations

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration for the API app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "Lung Disease Detection API"

