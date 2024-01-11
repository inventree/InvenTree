#!/usr/bin/env python
"""InvenTree / django management commands."""

import os
import sys

from InvenTree.config import get_boolean_setting
from tracing import setup_instruments, setup_tracing

TRACING_ENABLED = get_boolean_setting(
    'INVENTREE_TRACING_ENABLED', 'tracing_enabled', False
)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')

    # Run tracing/logging instrumentation
    if TRACING_ENABLED:
        setup_instruments()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            'available on your PYTHONPATH environment variable? Did you '
            'forget to activate a virtual environment?'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    if TRACING_ENABLED:
        setup_tracing()
    main()
