"""Gunicorn configuration script for InvenTree web server"""

import multiprocessing

bind = '0.0.0.0:8000'

workers = multiprocessing.cpu_count() * 2 + 1

max_requests = 1000
max_requests_jitter = 50

# preload app so that the ready functions are only executed once
preload_app = True
