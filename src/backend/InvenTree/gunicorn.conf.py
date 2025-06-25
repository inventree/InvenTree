"""Gunicorn configuration script for InvenTree web server."""

import multiprocessing

bind = '0.0.0.0:8000'

workers = multiprocessing.cpu_count() * 2 + 1

max_requests = 1000
max_requests_jitter = 50

# preload app so that the ready functions are only executed once
preload_app = True


def post_fork(server, worker):
    """Post-fork hook to set up logging for each worker."""
    from django.conf import settings

    if not settings.TRACING_ENABLED:
        return

    # Instrument gunicorm
    from InvenTree.tracing import setup_instruments, setup_tracing

    # Run tracing/logging instrumentation
    setup_tracing(**settings.TRACING_DETAILS)
    setup_instruments()
