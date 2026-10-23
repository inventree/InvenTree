"""Context tracking for audit log entries.

django-auditlog resolves the "actor" eagerly in its middleware, which misses users
authenticated later by DRF (e.g. HTTP Basic auth). Instead, the current request is
stored here, and the actor is resolved lazily when a log entry is written.
DRF writes the authenticated user back to the underlying HttpRequest, so
request.user is correct by the time any model is saved.
"""

import contextlib
import uuid
from contextvars import ContextVar
from typing import Optional

import structlog

_audit_request = ContextVar('inventree_audit_request', default=None)
_audit_cid = ContextVar('inventree_audit_cid', default=None)
_audit_source = ContextVar('inventree_audit_source', default=None)
_audit_batch = ContextVar('inventree_audit_batch', default=None)


@contextlib.contextmanager
def audit_batch():
    """Collect (unsaved) audit entries created within this context, rather than saving each one.

    Nested contexts share the outermost list.

    Yields:
        The list of collected entries, which the caller is responsible for writing
        (or None for a nested context, as there is nothing to write).
    """
    if _audit_batch.get() is not None:
        yield None
        return

    entries = []
    token = _audit_batch.set(entries)

    try:
        yield entries
    finally:
        _audit_batch.reset(token)


def get_batch() -> Optional[list]:
    """Return the list of audit entries being collected, or None if not batching."""
    return _audit_batch.get()


@contextlib.contextmanager
def audit_request(request):
    """Track the provided request (and a new correlation ID) for the duration of the context."""
    request_token = _audit_request.set(request)
    cid_token = _audit_cid.set(uuid.uuid4().hex)

    try:
        yield
    finally:
        _audit_request.reset(request_token)
        _audit_cid.reset(cid_token)


@contextlib.contextmanager
def audit_source(source: str):
    """Mark audit entries created within this context as originating from 'source'.

    Intended for changes made outside of a request (e.g. 'task:<name>', 'command:<name>').
    A new correlation ID is generated if one is not already active.
    """
    source_token = _audit_source.set(source)
    cid_token = _audit_cid.set(_audit_cid.get() or uuid.uuid4().hex)

    try:
        yield
    finally:
        _audit_source.reset(source_token)
        _audit_cid.reset(cid_token)


def get_cid() -> Optional[str]:
    """Return the current correlation ID (used as AUDITLOG_CID_GETTER).

    - Within a request: the request ID bound by django-structlog, so that audit entries
      can be matched against log entries (and the X-Request-ID header) for the request.
      Note: django-structlog uses the incoming 'X-Request-ID' header if provided
      (e.g. by a reverse proxy), otherwise generates a new UUID.
    - Otherwise (e.g. background tasks, or if the structlog middleware is not installed):
      a server-generated ID (see audit_request / audit_source).
    """
    if _audit_source.get() is None and _audit_request.get() is not None:
        if request_id := structlog.contextvars.get_contextvars().get('request_id'):
            return str(request_id)

    return _audit_cid.get()


def get_source() -> Optional[str]:
    """Return the current audit source, if set."""
    return _audit_source.get()


def get_request_actor():
    """Return the authenticated user for the current request, or None."""
    request = _audit_request.get()

    if request is None:
        return None

    user = getattr(request, 'user', None)

    if user is not None and user.is_authenticated:
        return user

    return None
