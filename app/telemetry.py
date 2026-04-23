import logging
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter
from sqlalchemy.ext.asyncio import AsyncEngine

from app.conf import OpenTelemetryExporter, Settings

logger = logging.getLogger(__name__)

SpanFilter = Callable[[ReadableSpan], bool]


def slow_sqlalchemy_queries(*, min_duration_ms: int) -> SpanFilter:  # pragma: no cover
    def filter(span: ReadableSpan) -> bool:
        scope = span.instrumentation_scope
        if not scope or scope.name != "opentelemetry.instrumentation.sqlalchemy":
            return True

        if not span.status.is_ok:
            # Always include failed queries
            return True

        if span.end_time is None or span.start_time is None:
            # execution time is unknown, always include it
            return True

        span_duration_ms = (span.end_time - span.start_time) / 1_000_000

        return span_duration_ms >= min_duration_ms

    return filter


class FilteredSpanProcessor(SpanProcessor):  # pragma: no cover
    def __init__(self, delegate_processor: SpanProcessor, filter_func: SpanFilter) -> None:
        self.delegate_processor = delegate_processor
        self.filter_func = filter_func

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        self.delegate_processor.on_start(span, parent_context)

    def on_end(self, span: ReadableSpan) -> None:
        if not self.filter_func(span):
            # If the span does not pass the filter, we drop it
            return

        self.delegate_processor.on_end(span)

    def shutdown(self) -> None:
        self.delegate_processor.shutdown()

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return self.delegate_processor.force_flush(timeout_millis)


def setup_telemetry(settings: Settings) -> None:  # pragma: no cover
    if settings.opentelemetry_exporter is None:
        return

    resource = Resource(
        attributes={"service.name": "ffc-extension"},
    )
    trace_provider = TracerProvider(resource=resource)

    exporter: SpanExporter

    if settings.opentelemetry_exporter == OpenTelemetryExporter.AZURE_APP_INSIGHTS:
        exporter = AzureMonitorTraceExporter(
            connection_string=settings.opentelemetry_connection_string
        )
    elif settings.opentelemetry_exporter == OpenTelemetryExporter.JAEGER:
        exporter = OTLPSpanExporter(endpoint=settings.opentelemetry_connection_string)  # type: ignore[arg-type]
    elif settings.opentelemetry_exporter == OpenTelemetryExporter.CONSOLE:
        exporter = ConsoleSpanExporter()
    else:
        raise ValueError(f"Unsupported OpenTelemetry exporter: {settings.opentelemetry_exporter}")

    span_processor: SpanProcessor = BatchSpanProcessor(exporter)

    if settings.opentelemetry_sqlalchemy_min_query_duration_ms is not None:
        span_processor = FilteredSpanProcessor(
            span_processor,
            slow_sqlalchemy_queries(
                min_duration_ms=settings.opentelemetry_sqlalchemy_min_query_duration_ms
            ),
        )
    trace_provider.add_span_processor(span_processor)

    trace.set_tracer_provider(trace_provider)

    HTTPXClientInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=True)


def setup_fastapi_instrumentor(settings: Settings, app: FastAPI) -> None:  # pragma: no cover
    """
    Setup FastAPI instrumentation for the application.
    """
    if settings.opentelemetry_exporter is None:
        return

    FastAPIInstrumentor.instrument_app(app)


def setup_sqlalchemy_instrumentor(
    settings: Settings, dbengine: AsyncEngine
) -> None:  # pragma: no cover
    if settings.opentelemetry_exporter is None:
        return

    SQLAlchemyInstrumentor().instrument(engine=dbengine.sync_engine, enable_commenter=True)


def capture_telemetry_cli_command[**P, R](
    tracer_name: str, span_name: str
) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
    def decorator(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            tracer = trace.get_tracer(tracer_name)

            with tracer.start_as_current_span(
                span_name,
                kind=trace.SpanKind.CLIENT,
                attributes={
                    "az.namespace": "CLI Command",
                },
            ):
                return await func(*args, **kwargs)

        return _wrapper

    return decorator
