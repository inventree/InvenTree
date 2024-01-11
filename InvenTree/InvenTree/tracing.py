"""OpenTelemetry setup functions."""

import logging

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk import _logs as logs
from opentelemetry.sdk import resources
from opentelemetry.sdk._logs import export as logs_export
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from InvenTree.version import inventreeVersion


def setup_tracing(
    endpoint: str,
    headers: dict,
    resources_input: dict | None = None,
    console: bool = False,
):
    """Set up tracing for the application in the current context.

    Args:
        endpoint: The endpoint to send the traces to.
        headers: The headers to send with the traces.
        resources_input: The resources to send with the traces.
        console: Whether to output the traces to the console.
    """
    if resources_input is None:
        resources_input = {}

    # Initialize the OTLP Resource
    resource = resources.Resource(
        attributes={
            resources.SERVICE_NAME: 'BACKEND',
            resources.SERVICE_NAMESPACE: 'INVENTREE',
            resources.SERVICE_VERSION: inventreeVersion(),
            **resources_input,
        }
    )

    # Spans / Tracs
    span_exporter = OTLPSpanExporter(headers=headers, endpoint=endpoint)
    trace_processor = BatchSpanProcessor(span_exporter)
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    trace_provider.add_span_processor(trace_processor)
    # For debugging purposes, export the traces to the console
    if console:
        trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Metrics
    metric_perodic_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(headers=headers, endpoint=endpoint)
    )
    metric_readers = [metric_perodic_reader]

    # For debugging purposes, export the metrics to the console
    if console:
        console_metric_exporter = ConsoleMetricExporter()
        console_metric_reader = PeriodicExportingMetricReader(console_metric_exporter)
        metric_readers.append(console_metric_reader)

    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)

    # Logs
    log_exporter = OTLPLogExporter(headers=headers, endpoint=endpoint)
    log_provider = logs.LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(
        logs_export.BatchLogRecordProcessor(log_exporter)
    )
    handler = logs.LoggingHandler(level=logging.INFO, logger_provider=log_provider)
    logger = logging.getLogger('inventree')
    logger.addHandler(handler)


def setup_instruments():
    """Run auto-insturmentation for OpenTelemetry tracing."""
    DjangoInstrumentor().instrument()
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()
