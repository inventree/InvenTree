"""Gunicorn configuration for InvenTree."""

import logging
import multiprocessing
import os

# Logger configuration
logger = logging.getLogger('inventree')
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('INVENTREE_LOG_LEVEL', 'warning').lower()
capture_output = True

# Worker configuration
#  TODO: Implement support for gevent
# worker_class = 'gevent'  # Allow multi-threading support
worker_tmp_dir = '/dev/shm'  # Write temp file to RAM (faster)
threads = 4


# Worker timeout (default = 90 seconds)
timeout = os.environ.get('INVENTREE_GUNICORN_TIMEOUT', '90')

# Number of worker processes
workers = os.environ.get('INVENTREE_GUNICORN_WORKERS', None)

if workers is not None:
    try:
        workers = int(workers)
    except ValueError:
        workers = None

if workers is None:
    workers = multiprocessing.cpu_count() * 2 + 1

logger.info('Starting gunicorn server with %s workers', workers)

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
    setup_instruments(settings.DB_ENGINE)
