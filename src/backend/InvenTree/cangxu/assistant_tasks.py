"""Durable receipt dispatch, ordered transport leases and bounded reconciliation."""

import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from InvenTree.config import get_setting

from .assistant_delivery_models import AssistantDutySlot, AssistantGatewayDelivery
from .assistant_gateway import (
    AssistantRuntimeNotConfiguredError,
    RuntimeProtocolError,
    RuntimeRejectedError,
    RuntimeUnavailableError,
    acknowledge_delivery,
    active_duty_query,
    duty_applies_to_event,
    duty_slot_key,
    epoch_ms,
    event_delivery_key,
    get_runtime_transport,
    record_delivery_failure,
    submit_delivery,
)
from .assistant_models import AssistantDuty, AssistantOutboxEvent, PartnerBinding
from .assistant_services import canonical_request_hash

PERIODIC_DISPATCH_FUNC = 'cangxu.assistant_tasks.assistant_periodic_dispatch'
DELIVER_ONE_FUNC = 'cangxu.assistant_tasks.deliver_gateway_delivery'
TASK_GROUP = 'cangxu-assistant'
LAST_DISPATCH_SETTING = '_ASSISTANT_LAST_DISPATCH'


def ensure_schedules(**kwargs):
    """Install one durable Django-Q2 schedule after migrations, never at import."""
    from django_q.models import Schedule

    from InvenTree.tasks import schedule_task

    minutes = get_setting(
        'ASSISTANT_DISPATCH_INTERVAL_MINUTES',
        'assistant_dispatch_interval_minutes',
        1,
        typecast=int,
    )
    schedule_task(
        PERIODIC_DISPATCH_FUNC, schedule_type=Schedule.MINUTES, minutes=max(minutes, 1)
    )


def _scan_limit():
    """Bound dispatch cycles while duties retain their persisted next-check cursor."""
    return min(
        max(
            get_setting(
                'ASSISTANT_SCAN_BATCH_SIZE',
                'assistant_scan_batch_size',
                100,
                typecast=int,
            ),
            1,
        ),
        1000,
    )


def _work(duty, receipt_id):
    """Pin authority and objects when enqueuing; retries cannot retarget a task."""
    grant = duty.grant
    attachments = duty.trigger_filter.get('attachments', [])
    if not duty.binding.write_enabled or 'receipt.link_archive' not in grant.actions:
        attachments = []
    return {
        'grant_id': grant.pk,
        'grant_version': grant.version,
        'receipt_id': str(receipt_id),
        'attachments': attachments,
    }


def _delivery(*, duty, kind, key, payload, event=None):
    """Deduplicate a stable immutable delivery intent within the caller's lock."""
    digest = canonical_request_hash({'kind': kind, 'payload': payload})
    existing = AssistantGatewayDelivery.objects.filter(
        binding=duty.binding, request_key=key
    ).first()
    if existing:
        return existing, False
    return AssistantGatewayDelivery.objects.create(
        binding=duty.binding,
        duty=duty,
        kind=kind,
        request_key=key,
        request_hash=digest,
        payload=payload,
        outbox_event=event,
    ), True


def enqueue_due_duties(*, now=None, limit=None):
    """Collapse missed intervals and claim a unique slot for each scoped receipt."""
    now = now or timezone.now()
    enqueued = 0
    candidates = (
        active_duty_query()
        .filter(next_run_at__lte=now)
        .order_by('next_run_at', 'pk')
        .values_list('pk', flat=True)[: limit or _scan_limit()]
    )
    for duty_id in list(candidates):
        with transaction.atomic():
            duty = (
                AssistantDuty.objects
                .select_for_update()
                .select_related('grant', 'binding', 'grant__subject')
                .get(pk=duty_id)
            )
            if (
                duty.paused
                or not duty.grant.is_active()
                or not duty.next_run_at
                or duty.next_run_at > now
            ):
                continue
            if duty.grant.object_type != 'purchase_receipt':
                continue
            scheduled_at = duty.next_run_at
            for receipt_id in duty.grant.object_ids:
                key = f'{duty_slot_key(duty, scheduled_at, duty.version)}:receipt:{receipt_id}'
                slot, _ = AssistantDutySlot.objects.get_or_create(
                    slot_key=key,
                    defaults={
                        'duty': duty,
                        'duty_revision': duty.version,
                        'scheduled_at': scheduled_at,
                    },
                )
                payload = {
                    'due_at_ms': epoch_ms(scheduled_at),
                    'work': _work(duty, receipt_id),
                }
                delivery, created = _delivery(
                    duty=duty,
                    kind=AssistantGatewayDelivery.Kind.DUTY_CHECK,
                    key=key,
                    payload=payload,
                )
                if slot.delivery_id is None:
                    slot.delivery = delivery
                    slot.save(update_fields=['delivery'])
                enqueued += int(created)
            duty.next_run_at = (
                now + timedelta(seconds=duty.interval_seconds)
                if duty.interval_seconds
                else None
            )
            duty.save(update_fields=['next_run_at'])
    return enqueued


def mark_event_delivered_if_complete(event_id, *, now=None):
    """Only mark an event after all its persisted subscriber deliveries acknowledge."""
    now = now or timezone.now()
    with transaction.atomic():
        event = AssistantOutboxEvent.objects.select_for_update().get(pk=event_id)
        if event.fanout_deliveries.exclude(
            status=AssistantGatewayDelivery.Status.ACKNOWLEDGED
        ).exists():
            return False
        if event.delivered_at is None:
            event.delivered_at = now
            event.save(update_fields=['delivered_at'])
    return True


def enqueue_undelivered_events(*, now=None, limit=None):
    """Atomically publish complete fan-out sets; periodic checks cover missed writes."""
    now = now or timezone.now()
    enqueued = 0
    candidates = (
        AssistantOutboxEvent.objects
        .filter(delivered_at__isnull=True)
        .order_by('pk')
        .values_list('pk', flat=True)[: limit or _scan_limit()]
    )
    for event_id in list(candidates):
        with transaction.atomic():
            event = AssistantOutboxEvent.objects.select_for_update().get(pk=event_id)
            if event.delivered_at is not None:
                continue
            for duty in (
                active_duty_query()
                .filter(grant__object_type=event.object_type)
                .select_related('grant', 'binding', 'grant__subject')
            ):
                if not duty_applies_to_event(duty, event):
                    continue
                payload = {
                    'due_at_ms': epoch_ms(event.created_at),
                    'work': _work(duty, event.object_id),
                }
                _, created = _delivery(
                    duty=duty,
                    kind=AssistantGatewayDelivery.Kind.BUSINESS_EVENT,
                    key=event_delivery_key(event, duty),
                    payload=payload,
                    event=event,
                )
                enqueued += int(created)
            mark_event_delivered_if_complete(event.pk, now=now)
    return enqueued


def _acquire_binding(binding_id, now):
    """Acquire a short transport lease without keeping a transaction over HTTP."""
    with transaction.atomic():
        binding = PartnerBinding.objects.select_for_update().get(pk=binding_id)
        if binding.dispatch_until and binding.dispatch_until > now:
            return None
        owner = uuid.uuid4()
        binding.dispatch_owner = owner
        # Each request timeout is <=60s; renew before each request and leave margin.
        binding.dispatch_until = now + timedelta(seconds=90)
        binding.save(update_fields=['dispatch_owner', 'dispatch_until'])
        return owner


def _still_allowed(delivery):
    """Revalidate current scope before admission; tools recheck again on execution."""
    binding = PartnerBinding.objects.get(pk=delivery.binding_id)
    if delivery.kind == AssistantGatewayDelivery.Kind.CONTROL:
        return True
    if (
        not binding.enabled
        or not get_user_model().objects.get(pk=binding.user_id).is_active
    ):
        return False
    if delivery.duty_id:
        duty = AssistantDuty.objects.select_related(
            'grant', 'binding', 'grant__subject'
        ).get(pk=delivery.duty_id)
        work = delivery.payload.get('work', {})
        return (
            not duty.paused
            and duty.grant.is_active()
            and duty.grant.version == work.get('grant_version')
        )
    return True


def attempt_pending_deliveries(
    *, now=None, limit=None, transport=None, binding_id=None
):
    """Serialize each partner's queue across workers, preserving deferred input order."""
    now = now or timezone.now()
    if transport is None:
        try:
            transport = get_runtime_transport()
        except AssistantRuntimeNotConfiguredError:
            return 0
    pending = AssistantGatewayDelivery.objects.filter(
        status=AssistantGatewayDelivery.Status.PENDING
    )
    if binding_id is not None:
        pending = pending.filter(binding_id=binding_id)
    bindings = list(
        pending
        .order_by('binding_id')
        .values_list('binding_id', flat=True)
        .distinct()[: limit or _scan_limit()]
    )
    acknowledged = 0
    for partner in bindings:
        owner = _acquire_binding(partner, now)
        if owner is None:
            continue
        try:
            queue = (
                AssistantGatewayDelivery.objects
                .filter(
                    binding_id=partner, status=AssistantGatewayDelivery.Status.PENDING
                )
                .select_related('binding')
                .annotate(
                    control_priority=Case(
                        When(kind=AssistantGatewayDelivery.Kind.CONTROL, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )
                .order_by('control_priority', 'pk')[: limit or _scan_limit()]
            )
            for delivery in list(queue):
                if delivery.available_at > now:
                    break
                if not _still_allowed(delivery):
                    record_delivery_failure(
                        delivery, 'authority_changed', retryable=False, now=now
                    )
                    continue
                # Never let a delayed old worker advance a queue after losing ownership.
                renewed = PartnerBinding.objects.filter(
                    pk=partner, dispatch_owner=owner
                ).update(dispatch_until=timezone.now() + timedelta(seconds=90))
                if not renewed:
                    break
                try:
                    result = submit_delivery(transport, delivery)
                except (RuntimeUnavailableError, RuntimeProtocolError) as exc:
                    record_delivery_failure(delivery, exc.code, retryable=True, now=now)
                    break
                except RuntimeRejectedError as exc:
                    record_delivery_failure(
                        delivery, exc.code, retryable=False, now=now
                    )
                    continue
                with transaction.atomic():
                    fresh = AssistantGatewayDelivery.objects.select_for_update().get(
                        pk=delivery.pk
                    )
                    if fresh.status == AssistantGatewayDelivery.Status.PENDING:
                        acknowledge_delivery(fresh, result['response_id'], now=now)
                        acknowledged += 1
                        if fresh.outbox_event_id:
                            mark_event_delivered_if_complete(
                                fresh.outbox_event_id, now=now
                            )
        finally:
            PartnerBinding.objects.filter(pk=partner, dispatch_owner=owner).update(
                dispatch_until=None, dispatch_owner=None
            )
    return acknowledged


def deliver_gateway_delivery(delivery_id):
    """Drain the owning partner in order rather than letting fresh inputs overtake."""
    delivery = AssistantGatewayDelivery.objects.filter(pk=delivery_id).first()
    if delivery is None:
        return False
    return bool(attempt_pending_deliveries(binding_id=delivery.binding_id))


def redrive_failed_delivery(delivery_id):
    """Operations retries the original key and intent after fixing an external cause."""
    return bool(
        AssistantGatewayDelivery.objects.filter(
            pk=delivery_id, status=AssistantGatewayDelivery.Status.FAILED
        ).update(
            status=AssistantGatewayDelivery.Status.PENDING,
            available_at=timezone.now(),
            attempts=0,
        )
    )


def assistant_periodic_dispatch():
    """Run independently of browser traffic using the durable Django-Q2 schedule."""
    summary = {
        'duties': enqueue_due_duties(),
        'events': enqueue_undelivered_events(),
        'acknowledged': attempt_pending_deliveries(),
    }
    from common.settings import set_global_setting

    set_global_setting(LAST_DISPATCH_SETTING, timezone.now().isoformat(), None)
    return summary
