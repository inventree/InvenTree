"""Gunicorn configuration for InvenTree."""

import logging
import multiprocessing
import os

data_dir = os.environ.get('INVENTREE_DATA_DIR', None)

# By default, log to stdout
log_file = '-'
error_log_file = '-'

if data_dir:
    log_dir = os.path.join(data_dir, 'gunicorn')
    log_dir = os.path.abspath(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    if os.path.exists(log_dir) and os.path.isdir(log_dir):
        log_file = os.path.join(log_dir, 'gunicorn.log')
        error_log_file = os.path.join(log_dir, 'gunicorn.error.log')

# Logger configuration
logger = logging.getLogger('inventree')
accesslog = log_file
errorlog = error_log_file
loglevel = os.environ.get('INVENTREE_LOG_LEVEL', 'warning').lower()
capture_output = True

# Worker configuration
#  TODO: Implement support for gevent
# worker_class = 'gevent'  # Allow multi-threading support
worker_tmp_dir = '/dev/shm'  # Write temp file to RAM (faster)
threads = 4


# Worker timeout (default = 90 seconds)
timeout = os.environ.get('INVENTREE_GUNICORN_TIMEOUT', 90)

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
