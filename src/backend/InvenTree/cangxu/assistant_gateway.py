"""Identity gateway and durable runtime transport for the work partner.

Configuration comes from server settings only: a runtime URL, a shared bearer
token and the deployment UUID. Model keys never reach this module and message
bodies or credentials are never logged.
"""

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

import requests

from InvenTree.config import get_setting

from .assistant_delivery_models import AssistantGatewayDelivery
from .assistant_models import AssistantDuty, AssistantGrant, PartnerBinding
from .assistant_services import canonical_request_hash

CONTROL_SCOPE_RUNTIME_MAP = {
    'reply': 'reply',
    'task': 'task',
    'all-writes': 'all-writes',
    'all-background': 'all-background',
}


class AssistantRuntimeError(Exception):
    """Base marker so callers never leak raw transport exceptions."""


class AssistantRuntimeNotConfiguredError(AssistantRuntimeError):
    """The server has no complete runtime URL, token or deployment identity."""


class RuntimeUnavailableError(AssistantRuntimeError):
    """A retryable transport failure; the delivery stays pending with backoff."""

    def __init__(self, code):
        """Keep only a stable machine code, never a body or secret."""
        self.code = code
        super().__init__(code)


class RuntimeRejectedError(AssistantRuntimeError):
    """The runtime durably refused the request; retrying will not fix it."""

    def __init__(self, code):
        """Keep only a stable machine code for diagnosis."""
        self.code = code
        super().__init__(code)


class RuntimeProtocolError(AssistantRuntimeError):
    """The runtime answered with a shape this gateway cannot validate."""

    def __init__(self, code='protocol_invalid_response'):
        """Name the validation failure without echoing any content."""
        self.code = code
        super().__init__(code)


class DeliveryConflictError(AssistantRuntimeError):
    """A stable request key was reused with different content."""


@dataclass(frozen=True)
class RuntimeConfig:
    """Resolved server-side runtime settings; no browser supplied values."""

    url: str
    token: str
    deployment_id: str
    timeout: float


def _text_setting(env_var, config_key, default=''):
    """Read a text setting through the shared InvenTree config precedence."""
    return get_setting(env_var, config_key, default, typecast=str)


def runtime_config():
    """Resolve the runtime endpoint; incomplete settings mean not configured."""
    token = _text_setting('ASSISTANT_RUNTIME_TOKEN', 'assistant_runtime_token')
    if not token:
        token = _text_setting('ASSISTANT_INTERNAL_TOKEN', 'assistant_internal_token')
    url = _text_setting('ASSISTANT_RUNTIME_URL', 'assistant_runtime_url').rstrip('/')
    deployment = (
        _text_setting('ASSISTANT_DEPLOYMENT_ID', 'assistant_deployment_id')
        .strip()
        .lower()
    )
    try:
        deployment = str(uuid.UUID(deployment))
    except (ValueError, AttributeError):
        deployment = ''
    timeout = get_setting(
        'ASSISTANT_RUNTIME_TIMEOUT_SECONDS',
        'assistant_runtime_timeout_seconds',
        5.0,
        typecast=float,
    )
    timeout = min(max(timeout, 0.1), 60.0)
    if not url or not token or not deployment or len(token) < 32:
        return None
    return RuntimeConfig(
        url=url, token=token, deployment_id=deployment, timeout=timeout
    )


def get_runtime_transport():
    """Build a transport from current settings, or raise if unconfigured."""
    config = runtime_config()
    if config is None:
        raise AssistantRuntimeNotConfiguredError(
            'The assistant runtime endpoint is not configured'
        )
    return RuntimeTransport(config)


def _require(condition, code='protocol_invalid_response'):
    """Validate a runtime response field without embedding its content."""
    if not condition:
        raise RuntimeProtocolError(code)


class RuntimeTransport:
    """Small HTTP client for the local runtime protocol v1.

    Requests carry the shared bearer token and deployment header. Errors are
    reduced to stable codes; response bodies are validated and then dropped.
    """

    def __init__(self, config, session=None):
        """Allow tests to inject a fake session; never log the config."""
        self._config = config
        self._session = session or requests.Session()
        if session is None:
            # This configured service connection is direct. Apart from routing
            # bearer credentials through an unintended proxy, macOS system
            # proxy discovery invokes CoreFoundation in Django-Q fork workers.
            self._session.trust_env = False

    def _request(self, method, path, body=None, params=None):
        """Perform one bounded request and normalize failures to codes."""
        url = f'{self._config.url}{path}'
        headers = {
            'Authorization': f'Bearer {self._config.token}',
            'X-Assistant-Deployment': self._config.deployment_id,
        }
        try:
            response = self._session.request(
                method,
                url,
                json=body,
                params=params,
                headers=headers,
                timeout=self._config.timeout,
            )
        except (requests.Timeout, requests.ConnectionError):
            raise RuntimeUnavailableError('network_unreachable') from None
        except requests.RequestException:
            raise RuntimeUnavailableError('network_error') from None
        if response.status_code >= 500 or response.status_code == 503:
            raise RuntimeUnavailableError(f'http_{response.status_code}')
        if response.status_code >= 400:
            raise RuntimeRejectedError(
                self._error_code(response, f'http_{response.status_code}')
            )
        try:
            data = response.json()
        except ValueError:
            raise RuntimeProtocolError('protocol_non_json') from None
        _require(isinstance(data, dict), 'protocol_non_object')
        return data

    @staticmethod
    def _error_code(response, fallback):
        """Extract only the structured error code, never its message."""
        try:
            code = response.json().get('error', {}).get('code')
        except ValueError:
            return fallback
        return code if isinstance(code, str) and code else fallback

    def submit_message(
        self, partner_id, request_id, text, references, attachments=None
    ):
        """Persist one conversation submission; the runtime owns the text."""
        body = {
            'request_id': str(request_id),
            'text': text,
            'references': list(references or []),
            'attachments': list(attachments or []),
        }
        data = self._request('POST', f'/v1/partners/{partner_id}/messages', body=body)
        _require(
            isinstance(data.get('submission_id'), int)
            and data.get('status') == 'accepted',
            'protocol_message_ack',
        )
        return {'response_id': str(data['submission_id'])}

    def list_messages(self, partner_id, before=None, limit=50):
        """Read bounded transcript history for one partner."""
        params = {'limit': int(limit)}
        if before is not None:
            params['before'] = int(before)
        data = self._request(
            'GET', f'/v1/partners/{partner_id}/messages', params=params
        )
        items = data.get('items')
        _require(isinstance(items, list), 'protocol_history_items')
        for item in items:
            _require(
                isinstance(item, dict)
                and isinstance(item.get('id'), int)
                and isinstance(item.get('text'), str),
                'protocol_history_item',
            )
        return {
            'items': items,
            'next_before': data.get('next_before'),
            'has_more': bool(data.get('has_more')),
        }

    def partner_status(self, partner_id):
        """Read persisted runtime state for one partner."""
        data = self._request('GET', f'/v1/partners/{partner_id}/status')
        _require(
            data.get('status') in {'available', 'processing'}, 'protocol_status_value'
        )
        return data

    def submit_control(self, partner_id, request_id, scope, task_id=None):
        """Forward one durable control command."""
        body = {'request_id': str(request_id), 'scope': scope}
        if task_id is not None:
            body['task_id'] = int(task_id)
        data = self._request('POST', f'/v1/partners/{partner_id}/controls', body=body)
        _require(data.get('status') == 'controlled', 'protocol_control_ack')
        return {'response_id': ''}

    def submit_event(self, partner_id, key, source, due_at_ms, work=None):
        """Enqueue one persistent runtime check from a timer or event."""
        body = {'key': str(key), 'source': source, 'dueAt': int(due_at_ms)}
        if work is not None:
            body['work'] = work
        data = self._request('POST', f'/v1/partners/{partner_id}/events', body=body)
        _require(
            isinstance(data.get('task_id'), int) and data.get('status') == 'accepted',
            'protocol_event_ack',
        )
        return {'response_id': str(data['task_id'])}


def _event_work(grant, object_id):
    """Build the bounded work contract from explicit grant scope."""
    if grant is None or not object_id:
        return None
    work = {
        'grant_id': grant.pk,
        'grant_version': grant.version,
        'object_id': str(object_id),
        'attachments': [],
    }
    if grant.object_type == 'purchase_receipt':
        work['receipt_id'] = str(object_id)
    return work


def submit_delivery(transport, delivery):
    """Map one durable delivery onto the runtime protocol; return response id.

    This runs outside any database transaction; callers persist the outcome.
    """
    partner_id = delivery.binding.partner_id
    if delivery.kind == AssistantGatewayDelivery.Kind.MESSAGE:
        from .assistant_attachments import message_attachments
        from .assistant_references import validate_references

        try:
            references = delivery.payload.get('references') or []
            validate_references(delivery.binding.user, references)
            attachments = message_attachments(
                delivery.binding,
                [item['id'] for item in delivery.payload.get('attachments', [])],
            )
        except Exception as exc:
            raise RuntimeRejectedError('message_context_unavailable') from exc
        arguments = [
            partner_id,
            delivery.request_key,
            delivery.payload.get('text', ''),
            references,
        ]
        return (
            transport.submit_message(*arguments, attachments=attachments)
            if attachments
            else transport.submit_message(*arguments)
        )
    if delivery.kind == AssistantGatewayDelivery.Kind.CONTROL:
        return transport.submit_control(
            partner_id,
            delivery.request_key,
            delivery.payload['scope'],
            delivery.payload.get('task_id'),
        )
    if delivery.kind in {
        AssistantGatewayDelivery.Kind.DUTY_CHECK,
        AssistantGatewayDelivery.Kind.BUSINESS_EVENT,
    }:
        work = delivery.payload.get('work')
        if not isinstance(work, dict) or not work.get('receipt_id'):
            raise RuntimeRejectedError('missing_pinned_receipt_work')
        return transport.submit_event(
            partner_id,
            delivery.request_key,
            'timer'
            if delivery.kind == AssistantGatewayDelivery.Kind.DUTY_CHECK
            else 'event',
            delivery.payload['due_at_ms'],
            work=work,
        )
    raise RuntimeProtocolError('unknown_delivery_kind')


def ensure_partner_binding(user, partner_id=None):
    """Provision a binding with bounded SQLite contention retries."""
    from .assistant_database import sqlite_busy_retry

    return sqlite_busy_retry(lambda: _ensure_partner_binding(user, partner_id))


def _ensure_partner_binding(user, partner_id=None):
    """Return the user's binding for the configured deployment.

    An explicit message provisions the default partner with the enabled service
    default. A caller-chosen partner identifier only selects an existing binding
    owned by the same user and deployment; it never provisions one.
    """
    config = runtime_config()
    if config is None:
        raise AssistantRuntimeNotConfiguredError(
            'The assistant runtime endpoint is not configured'
        )
    if partner_id is not None:
        return PartnerBinding.objects.get(
            deployment_id=config.deployment_id, user=user, partner_id=partner_id
        )
    try:
        binding, _ = PartnerBinding.objects.get_or_create(
            deployment_id=config.deployment_id,
            user=user,
            is_default=True,
            defaults={'enabled': True, 'write_enabled': True},
        )
    except ValidationError:
        # Model.full_clean can observe a competing first-open insert before
        # save(), so get_or_create's IntegrityError recovery is not sufficient.
        binding = PartnerBinding.objects.filter(
            deployment_id=config.deployment_id, user=user, is_default=True
        ).first()
        if binding is None:
            raise
    return binding


def queue_message_delivery(
    *, binding, client_request_id, text, references, attachments=None
):
    """Persist one message durably; identical retries return the same record."""
    intent = {
        'kind': AssistantGatewayDelivery.Kind.MESSAGE,
        'text': text,
        'references': list(references or []),
        'attachments': list(attachments or []),
    }
    return _queue_delivery(
        binding=binding,
        kind=AssistantGatewayDelivery.Kind.MESSAGE,
        request_key=client_request_id,
        intent=intent,
        payload={
            'text': text,
            'references': list(references or []),
            'attachments': list(attachments or []),
        },
    )


def queue_control_delivery(*, binding, client_request_id, scope, task_id=None):
    """Persist one control command; all-writes freezes writes immediately."""
    runtime_scope = CONTROL_SCOPE_RUNTIME_MAP[scope]
    intent = {
        'kind': AssistantGatewayDelivery.Kind.CONTROL,
        'scope': scope,
        'task_id': task_id,
    }
    return _queue_delivery(
        binding=binding,
        kind=AssistantGatewayDelivery.Kind.CONTROL,
        request_key=client_request_id,
        intent=intent,
        payload={'scope': runtime_scope, 'task_id': task_id},
    )


def _queue_delivery(*, binding, kind, request_key, intent, payload):
    """Create or replay one delivery under its stable key."""
    digest = canonical_request_hash(intent)
    existing = AssistantGatewayDelivery.objects.filter(
        binding=binding, request_key=request_key
    ).first()
    if existing:
        if existing.request_hash != digest:
            raise DeliveryConflictError(
                'Request key already identifies different content'
            )
        return existing, False
    try:
        with transaction.atomic():
            delivery = AssistantGatewayDelivery.objects.create(
                binding=binding,
                kind=kind,
                request_key=request_key,
                request_hash=digest,
                payload=payload,
            )
    except IntegrityError:
        # A concurrent request inserted the key first; replay its record.
        delivery = AssistantGatewayDelivery.objects.get(
            binding=binding, request_key=request_key
        )
        if delivery.request_hash != digest:
            raise DeliveryConflictError(
                'Request key already identifies different content'
            ) from None
        return delivery, False
    return delivery, True


def acknowledge_delivery(delivery, response_id, *, now=None):
    """Record the runtime ack and clear pending text from this database."""
    now = now or timezone.now()
    delivery.attempts += 1
    delivery.status = AssistantGatewayDelivery.Status.ACKNOWLEDGED
    delivery.acknowledged_at = now
    delivery.response_id = response_id or ''
    delivery.payload = {'cleared': True}
    delivery.last_error = ''
    delivery.save(
        update_fields=[
            'attempts',
            'status',
            'acknowledged_at',
            'response_id',
            'payload',
            'last_error',
            'updated_at',
        ]
    )
    return delivery


def delivery_backoff_seconds(attempts, *, now=None):
    """Return capped exponential backoff for the given attempt count."""
    base = get_setting(
        'ASSISTANT_DELIVERY_BACKOFF_SECONDS',
        'assistant_delivery_backoff_seconds',
        30,
        typecast=float,
    )
    cap = get_setting(
        'ASSISTANT_DELIVERY_BACKOFF_MAX_SECONDS',
        'assistant_delivery_backoff_max_seconds',
        3600,
        typecast=float,
    )
    return min(max(base, 0) * 2 ** max(attempts - 1, 0), max(cap, base))


def record_delivery_failure(delivery, code, *, retryable, now=None):
    """Count one attempt and keep retrying with backoff until the cap."""
    now = now or timezone.now()
    delivery.attempts += 1
    delivery.last_error = code[:200]
    attempts_limit = get_setting(
        'ASSISTANT_DELIVERY_MAX_ATTEMPTS',
        'assistant_delivery_max_attempts',
        8,
        typecast=int,
    )
    if not retryable or delivery.attempts >= max(attempts_limit, 1):
        # Rejections and exhausted retries stay diagnosable, never silent.
        delivery.status = AssistantGatewayDelivery.Status.FAILED
    else:
        delivery.available_at = now + timedelta(
            seconds=delivery_backoff_seconds(delivery.attempts)
        )
    delivery.save(
        update_fields=['attempts', 'last_error', 'available_at', 'status', 'updated_at']
    )
    return delivery


def duty_slot_key(duty, scheduled_at, revision):
    """Build the stable per-slot key required by the schedule contract."""
    stamp = scheduled_at.astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')
    return f'duty:{duty.pk}:{stamp}:{revision}'


def event_delivery_key(event, duty):
    """Build the stable fan-out key for one outbox event and duty."""
    return f'event:{event.event_id}:duty:{duty.pk}'


def active_duty_query():
    """Return duties whose binding, user and grant currently allow checks."""
    now = timezone.now()
    return AssistantDuty.objects.filter(
        paused=False,
        binding__enabled=True,
        binding__user__is_active=True,
        grant__revoked_at__isnull=True,
    ).filter(Q(grant__expires_at__isnull=True) | Q(grant__expires_at__gt=now))


def duty_applies_to_event(duty, event):
    """Check explicit grant containment; there is no all-warehouse default."""
    grant = duty.grant
    if grant is None or not grant.is_active():
        return False
    if grant.object_type != event.object_type:
        return False
    if str(event.object_id) not in [str(item) for item in grant.object_ids or []]:
        return False
    trigger_filter = duty.trigger_filter or {}
    if not isinstance(trigger_filter, dict):
        return False
    event_types = trigger_filter.get('event_types')
    if isinstance(event_types, list) and event_types:
        if event.event_type not in event_types:
            return False
    object_ids = trigger_filter.get('object_ids')
    if isinstance(object_ids, list) and object_ids:
        if str(event.object_id) not in [str(item) for item in object_ids]:
            return False
    return True


def register_command_duty(
    *,
    user=None,
    binding=None,
    object_ids,
    actions,
    authorization_reference,
    name,
    goal,
    object_type='purchase_receipt',
    interval_seconds=None,
    next_run_at=None,
    time_zone='Asia/Shanghai',
    trigger_filter=None,
    expires_at=None,
    continuous=True,
    limits=None,
    paused=False,
):
    """Trusted internal registration of an explicit command scope and duty.

    Only server code may call this: the natural command itself is the recorded
    authorization evidence, so no per-tool prompts or client identity claims
    are accepted here. A previous stop-all-writes control remains in force.
    """
    if (user is None) == (binding is None):
        raise ValidationError('Provide exactly one of user or binding')
    with transaction.atomic():
        if binding is None:
            binding = ensure_partner_binding(user)
        if object_type != 'purchase_receipt' or not object_ids or len(object_ids) > 100:
            raise ValidationError(
                'This dispatcher supports 1 to 100 explicit receipts only'
            )
        if (
            set(actions) - {'receipt.read', 'receipt.link_archive'}
            or 'receipt.read' not in actions
        ):
            raise ValidationError('Unsupported receipt duty actions')
        grant = AssistantGrant.objects.create(
            binding=binding,
            subject_id=binding.user_id,
            object_type=object_type,
            object_ids=[str(item) for item in object_ids],
            actions=list(actions),
            limits=limits or {},
            continuous=continuous,
            expires_at=expires_at,
            authorization_reference=authorization_reference,
        )
        if interval_seconds and next_run_at is None:
            next_run_at = timezone.now()
        duty = AssistantDuty.objects.create(
            binding=binding,
            grant=grant,
            name=name,
            goal=goal,
            trigger_filter=trigger_filter or {},
            interval_seconds=interval_seconds,
            time_zone=time_zone,
            next_run_at=next_run_at,
            paused=paused,
        )
    return duty


def epoch_ms(moment):
    """Convert an aware datetime to the protocol's epoch milliseconds."""
    return math.floor(moment.timestamp() * 1000)
