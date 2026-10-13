"""Bounded retries for transient SQLite writer contention, without replaying transactions."""

import sqlite3
import time

from django.db import OperationalError, connection

from rest_framework.exceptions import APIException


class AssistantDatabaseBusy(APIException):
    """The caller can retry the same stable request key after contention clears."""

    status_code = 503
    default_detail = 'Assistant storage is busy. Retry the same request shortly.'
    default_code = 'assistant_storage_busy'


def sqlite_busy_retry(operation):
    """Retry only rolled-back SQLite operations, never a live outer transaction."""
    for attempt in range(5):
        try:
            return operation()
        except OperationalError as exc:
            cause = exc.__cause__
            code = getattr(cause, 'sqlite_errorcode', None)
            busy = (
                code is not None
                and code & 0xFF in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}
            ) or str(exc).lower() in {'database is locked', 'database table is locked'}
            if connection.vendor != 'sqlite' or not busy:
                raise
            if connection.in_atomic_block or attempt == 4:
                raise AssistantDatabaseBusy() from None
            time.sleep(0.05 * 2**attempt)
