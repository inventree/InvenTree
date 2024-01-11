#!/usr/bin/env python
"""InvenTree / django management commands."""

import os
import sys

from tracing import setup_instruments, setup_tracing


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')

    # Run tracing/logging instrumentation
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
    setup_tracing()
    main()
