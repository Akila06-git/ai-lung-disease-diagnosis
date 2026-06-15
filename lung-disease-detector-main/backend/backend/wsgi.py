from __future__ import annotations

"""WSGI config for backend project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_wsgi_application()


# ---------------------------------------------------------------------------
# OpenTelemetry Instrumentation (Tracing -> Tempo)
# ---------------------------------------------------------------------------

def _setup_otel():
    """Initialize OpenTelemetry tracing if the SDK is installed."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.instrumentation.django import DjangoInstrumentor

        resource = Resource(attributes={SERVICE_NAME: "lung-disease-detector"})
        provider = TracerProvider(resource=resource)

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        DjangoInstrumentor().instrument()

        # Optional: instrument psycopg2 and redis
        try:
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
            Psycopg2Instrumentor().instrument()
        except Exception:
            pass

        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            RedisInstrumentor().instrument()
        except Exception:
            pass

    except ImportError:
        pass  # OTel not installed; skip silently


if os.environ.get("ENABLE_OTEL", "False").lower() == "true":
    _setup_otel()
