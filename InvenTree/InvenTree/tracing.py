"""OpenTelemetry setup functions."""

import base64
import logging
from typing import Optional

from opentelemetry import metrics, trace
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

import InvenTree.ready
from InvenTree.version import inventreeVersion

# Logger configuration
logger = logging.getLogger('inventree')


def setup_tracing(
    endpoint: str,
    headers: dict,
    resources_input: Optional[dict] = None,
    console: bool = False,
    auth: Optional[dict] = None,
    is_http: bool = False,
    append_http: bool = True,
):
    """Set up tracing for the application in the current context.

    Args:
        endpoint: The endpoint to send the traces to.
        headers: The headers to send with the traces.
        resources_input: The resources to send with the traces.
        console: Whether to output the traces to the console.
    """
    if not InvenTree.ready.isInMainThread():
        # Don't setup tracing in the worker thread
        return

    if resources_input is None:
        resources_input = {}
    if auth is None:
        auth = {}

    # Setup the auth headers
    if 'basic' in auth:
        basic_auth = auth['basic']
        if 'username' in basic_auth and 'password' in basic_auth:
            auth_raw = f'{basic_auth["username"]}:{basic_auth["password"]}'
            auth_token = base64.b64encode(auth_raw.encode('utf-8')).decode('utf-8')
            headers['Authorization'] = f'Basic {auth_token}'
        else:
            logger.warning('Basic auth is missing username or password')

    # Clean up headers
    headers = {k: v for k, v in headers.items() if v is not None}

    # Initialize the OTLP Resource
    resource = resources.Resource(
        attributes={
            resources.SERVICE_NAME: 'BACKEND',
            resources.SERVICE_NAMESPACE: 'INVENTREE',
            resources.SERVICE_VERSION: inventreeVersion(),
            **resources_input,
        }
    )

    # Import the OTLP exporters
    if is_http:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
    else:
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

    # Spans / Tracs
    span_exporter = OTLPSpanExporter(
        headers=headers,
        endpoint=endpoint if not (is_http and append_http) else f'{endpoint}/v1/traces',
    )
    trace_processor = BatchSpanProcessor(span_exporter)
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    trace_provider.add_span_processor(trace_processor)
    # For debugging purposes, export the traces to the console
    if console:
        trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Metrics
    metric_perodic_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            headers=headers,
            endpoint=endpoint
            if not (is_http and append_http)
            else f'{endpoint}/v1/metrics',
        )
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
    log_exporter = OTLPLogExporter(
        headers=headers,
        endpoint=endpoint if not (is_http and append_http) else f'{endpoint}/v1/logs',
    )
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
