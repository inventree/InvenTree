"""A short-lived, cross-process lease built on top of InvenTreeSetting.

Used to serialize an potentially long-running operation,
without holding a database transaction open for the duration.
"""

import time
from datetime import datetime, timedelta
from typing import Optional

from django.db import transaction
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.utils import timezone

import structlog

logger = structlog.get_logger('inventree')

# How long a lease is honored for, before it is treated as abandoned
CLAIM_LEASE = timedelta(minutes=5)


def _parse_claim(value: str) -> Optional[datetime]:
    """Parse a claim timestamp (as written by `try_acquire_lease`), if any."""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def try_acquire_lease(key: str) -> bool:
    """Attempt to acquire a short-lived, cross-process lease for the given key.

    The lease is recorded as a separate '<key>_CLAIMED_AT' setting, checked and
    written under a row lock - but the lock is only held for this brief read/write,
    never for the (potentially slow) work the lease protects against running twice.
    A lease older than CLAIM_LEASE is treated as abandoned and may be re-acquired,
    so a crashed holder does not block progress forever.
    """
    from common.models import InvenTreeSetting

    claim_key = f'{key.upper()}_CLAIMED_AT'
    now = timezone.now()

    try:
        with transaction.atomic():
            InvenTreeSetting.objects.get_or_create(
                key=claim_key, defaults={'value': ''}
            )
            setting = InvenTreeSetting.objects.select_for_update().get(
                key__iexact=claim_key
            )

            claimed_at = _parse_claim(setting.value)

            if claimed_at is not None and (now - claimed_at) < CLAIM_LEASE:
                return False

            setting.value = now.isoformat()
            setting.save()
            return True
    except (IntegrityError, OperationalError, ProgrammingError):
        logger.debug("Could not acquire lease for '%s' - database not ready", key)
        return False


def acquire_lease_blocking(
    key: str, timeout: float = 60, poll_interval: float = 0.5
) -> bool:
    """Repeatedly attempt `try_acquire_lease` until it succeeds or `timeout` elapses.

    Callers of this are not latency-sensitive (only ever triggered by an admin
    action, or a startup/reload event) - so it is preferable to wait briefly for
    a concurrent holder to finish, rather than silently skipping the guarded work
    the first time the lease happens to be held.

    Returns True if the lease was acquired, or False if `timeout` elapsed first.
    """
    deadline = time.monotonic() + timeout

    while True:
        if try_acquire_lease(key):
            return True

        if time.monotonic() >= deadline:
            return False

        time.sleep(poll_interval)


def release_lease(key: str):
    """Release a lease previously acquired via `try_acquire_lease`."""
    from common.models import InvenTreeSetting

    claim_key = f'{key.upper()}_CLAIMED_AT'

    try:
        with transaction.atomic():
            setting = InvenTreeSetting.objects.select_for_update().get(
                key__iexact=claim_key
            )
            setting.value = ''
            setting.save()
    except (
        IntegrityError,
        OperationalError,
        ProgrammingError,
        InvenTreeSetting.DoesNotExist,
    ):
        logger.debug("Could not release lease for '%s' - database not ready", key)
