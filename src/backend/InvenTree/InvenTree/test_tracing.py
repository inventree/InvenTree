"""Tests for OpenTelemetry tracing setup."""

import logging
from unittest import mock

from django.test import SimpleTestCase

import InvenTree.tracing as tracing

GRPC_EXPORTER_PATCHES = [
    'opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter',
    'opentelemetry.exporter.otlp.proto.grpc.metric_exporter.OTLPMetricExporter',
    'opentelemetry.exporter.otlp.proto.grpc._log_exporter.OTLPLogExporter',
]

# Names of the SDK objects that setup_tracing() would otherwise construct for real -
# doing so spins up background export threads and (without a reachable collector)
# logs connection errors, so these are stubbed out for the tests below.
SDK_PATCHES = [
    'InvenTree.tracing.TracerProvider',
    'InvenTree.tracing.BatchSpanProcessor',
    'InvenTree.tracing.MeterProvider',
    'InvenTree.tracing.PeriodicExportingMetricReader',
    'InvenTree.tracing.logs.LoggerProvider',
    'InvenTree.tracing.logs.LoggingHandler',
    'InvenTree.tracing.logs_export.BatchLogRecordProcessor',
    'InvenTree.tracing.trace.set_tracer_provider',
    'InvenTree.tracing.metrics.set_meter_provider',
]


class TracingSetupTest(SimpleTestCase):
    """Tests for InvenTree.tracing.setup_tracing.

    setup_tracing() keeps its "already configured" state in the module-level
    TRACE_PROV global, so it is reset before/after every test to keep tests isolated.
    """

    def setUp(self):
        """Reset global tracing state before each test."""
        super().setUp()
        tracing.TRACE_PROC = None
        tracing.TRACE_PROV = None
        tracing.TRACE_PID = None

        self.logger = logging.getLogger('inventree')
        self.handlers_before = list(self.logger.handlers)

    def tearDown(self):
        """Reset global tracing state, and remove any handlers added by setup_tracing."""
        tracing.TRACE_PROC = None
        tracing.TRACE_PROV = None
        tracing.TRACE_PID = None

        for handler in list(self.logger.handlers):
            if handler not in self.handlers_before:
                self.logger.removeHandler(handler)

        super().tearDown()

    def call_setup(self, pid=None, **kwargs):
        """Call setup_tracing with all SDK/exporter classes mocked out.

        Args:
            pid: If given, os.getpid() is mocked to return this value for the
                duration of the call - used to simulate a forked worker process.

        Returns the mock.patch context's mocked TracerProvider class, so callers can
        assert on whether tracing was actually (re)configured.
        """
        targets = SDK_PATCHES + GRPC_EXPORTER_PATCHES
        if pid is not None:
            targets = [*targets, 'InvenTree.tracing.os.getpid']

        patches = [mock.patch(target) for target in targets]
        mocks = [patcher.start() for patcher in patches]
        self.addCleanup(lambda: [patcher.stop() for patcher in patches])

        if pid is not None:
            mocks[-1].return_value = pid

        kwargs.setdefault('endpoint', 'http://localhost:4317')
        kwargs.setdefault('headers', {'x-test': 'value'})
        kwargs.setdefault('is_http', False)
        tracing.setup_tracing(**kwargs)

        return mocks[0]  # TracerProvider mock

    def test_first_call_configures_tracing(self):
        """The first call to setup_tracing must actually configure tracing.

        Regression test for a bug where the "already configured" guard checked
        `trace.get_tracer_provider() is not None`. OpenTelemetry's API never returns
        None here - before anything is configured it returns a ProxyTracerProvider -
        so that check was always true, and setup_tracing returned immediately without
        ever installing an exporter, even on the very first call.
        """
        self.assertIsNone(tracing.TRACE_PROV)

        mock_tracer_provider = self.call_setup()

        mock_tracer_provider.assert_called_once()
        self.assertIsNotNone(tracing.TRACE_PROV)

    def test_second_call_is_skipped(self):
        """A second call to setup_tracing should not reconfigure tracing."""
        self.call_setup()
        self.assertIsNotNone(tracing.TRACE_PROV)

        mock_tracer_provider = self.call_setup()
        mock_tracer_provider.assert_not_called()

    def test_reconfigures_after_simulated_fork(self):
        """setup_tracing must reconfigure in a forked child process, even though it inherits TRACE_PROV from the parent.

        Regression test for gunicorn's `preload_app = True`: settings (and so
        setup_tracing) are imported once in the master process before workers are
        forked. Each forked worker inherits TRACE_PROV via copy-on-write memory, but
        the parent's BatchSpanProcessor background thread does not survive fork()
        (only the forking thread continues in the child), so post_fork's explicit
        setup_tracing() call must still be able to reconfigure a real exporter in
        each worker rather than being skipped as "already configured".
        """
        # First call, simulating the pre-fork master process (pid 100)
        master_tracer_provider = self.call_setup(pid=100)
        master_tracer_provider.assert_called_once()
        self.assertEqual(tracing.TRACE_PID, 100)

        # Second call with the SAME pid must still be skipped (same-process guard)
        same_pid_tracer_provider = self.call_setup(pid=100)
        same_pid_tracer_provider.assert_not_called()

        # Second call from a DIFFERENT pid, simulating a forked worker, must reconfigure
        worker_tracer_provider = self.call_setup(pid=200)
        worker_tracer_provider.assert_called_once()
        self.assertEqual(tracing.TRACE_PID, 200)

    def test_missing_endpoint_or_headers_skips_setup(self):
        """setup_tracing should skip setup if endpoint or headers are not provided."""
        tracing.setup_tracing(endpoint=None, headers={'a': 'b'})
        self.assertIsNone(tracing.TRACE_PROV)

        tracing.setup_tracing(endpoint='http://localhost:4317', headers=None)
        self.assertIsNone(tracing.TRACE_PROV)
