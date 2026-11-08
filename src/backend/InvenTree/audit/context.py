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
_audit_batch_cid = ContextVar('inventree_audit_batch_cid', default=None)
_audit_events = ContextVar('inventree_audit_events', default=None)
_audit_flush_event = ContextVar('inventree_audit_flush_event', default=None)


@contextlib.contextmanager
def audit_batch():
    """Collect (unsaved) audit entries created within this context, rather than saving each one.

    Nested contexts share the outermost list.

    The correlation ID is resolved once for the batch (see get_cid),
    as resolving it for every entry is expensive for large batches.

    Yields:
        The list of collected entries, which the caller is responsible for writing
        (or None for a nested context, as there is nothing to write).
    """
    if _audit_batch.get() is not None:
        yield None
        return

    entries = []
    token = _audit_batch.set(entries)
    cid_token = _audit_batch_cid.set(resolve_cid())

    try:
        yield entries
    finally:
        _audit_batch_cid.reset(cid_token)
        _audit_batch.reset(token)


def get_batch() -> Optional[list]:
    """Return the list of audit entries being collected, or None if not batching."""
    return _audit_batch.get()


class PendingEvent:
    """A named event which is waiting to be attached to an audit entry (see audit.helpers.audit_event)."""

    def __init__(self, instance, event_type: int, notes=None, deltas=None, actor=None):
        """Initialize the pending event."""
        self.instance = instance
        self.event_type = event_type
        self.notes = notes
        self.deltas = deltas
        self.actor = actor
        self.consumed = False


def instance_key(instance) -> Optional[tuple]:
    """Return a key which identifies the database row of an instance (or None if unsaved)."""
    if instance.pk is None:
        return None

    return (type(instance), instance.pk)


class EventRegistry:
    """The pending events within an audit_event() context.

    Events are indexed by instance (identity), and by database row (model and primary key),
    so that matching events can be found efficiently for large numbers of events.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self.counter = 0
        self.by_id: dict[int, list] = {}
        self.by_key: dict[tuple, list] = {}

    def add(self, event: PendingEvent) -> None:
        """Add an event to the registry."""
        self.counter += 1
        event.order = self.counter

        self.by_id.setdefault(id(event.instance), []).append(event)

        if key := instance_key(event.instance):
            self.by_key.setdefault(key, []).append(event)

    def remove(self, event: PendingEvent) -> None:
        """Remove an event from the registry."""
        for index, key in [
            (self.by_id, id(event.instance)),
            (self.by_key, instance_key(event.instance)),
        ]:
            if key is not None and event in (events := index.get(key, [])):
                events.remove(event)

                if not events:
                    del index[key]

    def find(self, instance) -> Optional[PendingEvent]:
        """Return the first (unconsumed) pending event for the provided instance.

        Instances are matched by identity, or by model and primary key
        (e.g. if the same database row is saved via a different instance).
        """
        candidates = list(self.by_id.get(id(instance), []))

        if key := instance_key(instance):
            candidates += self.by_key.get(key, [])

        candidates = [event for event in candidates if not event.consumed]

        return min(candidates, key=lambda event: event.order, default=None)


@contextlib.contextmanager
def pending_events(events: list):
    """Register the provided events as pending for the duration of the context."""
    registry = _audit_events.get()
    token = None

    if registry is None:
        registry = EventRegistry()
        token = _audit_events.set(registry)

    for event in events:
        registry.add(event)

    try:
        yield
    finally:
        for event in events:
            registry.remove(event)

        if token is not None:
            _audit_events.reset(token)


def has_pending_event(instance) -> bool:
    """Return True if there is a pending (unconsumed) event for the provided instance."""
    registry = _audit_events.get()
    return registry is not None and registry.find(instance) is not None


@contextlib.contextmanager
def flushing_event(event: PendingEvent):
    """Consume the provided event for any entry recorded for its instance within this context.

    Used when writing an entry for a specific event (see audit.helpers.write_event_entry),
    which may not be the first pending event for the instance.
    """
    token = _audit_flush_event.set(event)

    try:
        yield
    finally:
        _audit_flush_event.reset(token)


def consume_event(instance) -> Optional[PendingEvent]:
    """Return (and consume) the first pending event for the provided instance, if any."""
    event = _audit_flush_event.get()

    if (
        event is not None
        and not event.consumed
        and (
            event.instance is instance
            or (
                (key := instance_key(instance)) is not None
                and key == instance_key(event.instance)
            )
        )
    ):
        event.consumed = True
        return event

    registry = _audit_events.get()

    if registry is None:
        return None

    if event := registry.find(instance):
        event.consumed = True

    return event


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


def task_name(func) -> str:
    """Return the dotted name of a task function (which may be provided as a string)."""
    if isinstance(func, str):
        return func

    module = getattr(func, '__module__', None)
    name = getattr(func, '__qualname__', None) or getattr(func, '__name__', None)

    if module and name:
        return f'{module}.{name}'

    return repr(func)


@contextlib.contextmanager
def audit_task(func):
    """Mark audit entries created within this context as originating from a background task.

    If a request is active (e.g. a task run synchronously as part of a request),
    the changes are attributed to the request instead.
    """
    if _audit_request.get() is not None:
        yield
        return

    with audit_source(f'task:{task_name(func)}'):
        yield


# Context managers for tasks which are executed by the background worker
_worker_tasks: list = []


def begin_worker_task(func) -> None:
    """Enter the audit_task context for a task executed by the background worker.

    The worker provides separate signals before and after a task is executed,
    so the context is entered (and exited) manually.
    """
    context = audit_task(func)
    context.__enter__()
    _worker_tasks.append(context)


def end_worker_task() -> None:
    """Exit the audit_task context for the most recent worker task."""
    if _worker_tasks:
        _worker_tasks.pop().__exit__(None, None, None)


def get_cid() -> Optional[str]:
    """Return the current correlation ID (used as AUDITLOG_CID_GETTER).

    Within an audit_batch() context, the ID resolved when the batch was entered is returned.
    """
    if cid := _audit_batch_cid.get():
        return cid

    return resolve_cid()


def resolve_cid() -> Optional[str]:
    """Resolve the current correlation ID.

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
