"""Durable gateway delivery queue and duty schedule slots for the work partner.

Every runtime submission is persisted before any network attempt. Message text
lives here only while the delivery is pending; once the runtime acknowledges
receipt the payload is cleared because the runtime owns the transcript.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from .assistant_models import (
    AssistantDuty,
    AssistantOutboxEvent,
    PartnerBinding,
    ValidatedAssistantModel,
)


class AssistantGatewayDelivery(ValidatedAssistantModel):
    """Hold one runtime submission per binding and stable request key."""

    class Kind(models.TextChoices):
        """Describe which runtime endpoint consumes this delivery."""

        MESSAGE = 'message', 'Message'
        CONTROL = 'control', 'Control'
        DUTY_CHECK = 'duty_check', 'Duty check'
        BUSINESS_EVENT = 'business_event', 'Business event'

    class Status(models.TextChoices):
        """Describe durable acknowledgement state, not runtime progress."""

        PENDING = 'pending', 'Pending'
        ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
        FAILED = 'failed', 'Failed'

    binding = models.ForeignKey(
        PartnerBinding, on_delete=models.PROTECT, related_name='gateway_deliveries'
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    request_key = models.CharField(max_length=200)
    request_hash = models.CharField(
        max_length=64,
        validators=[
            RegexValidator(r'\A[0-9a-f]{64}\Z', 'Provide a canonical SHA-256 digest.')
        ],
    )
    payload = models.JSONField(default=dict, blank=True)
    outbox_event = models.ForeignKey(
        AssistantOutboxEvent,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='fanout_deliveries',
    )
    duty = models.ForeignKey(
        AssistantDuty,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='check_deliveries',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    attempts = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    response_id = models.CharField(max_length=200, blank=True, default='')
    last_error = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Deduplicate by binding and request key; scan due attempts cheaply."""

        ordering = ['pk']
        indexes = [
            models.Index(fields=['status', 'available_at'], name='cx_delivery_due_idx'),
            models.Index(fields=['binding', 'status'], name='cx_delivery_binding_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['binding', 'request_key'], name='cx_delivery_request_unique'
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=('pending', 'acknowledged', 'failed')),
                name='cx_delivery_status',
            ),
        ]

    def clean(self):
        """Reject ambiguous keys or payloads before persisting."""
        super().clean()
        errors = {}
        if not isinstance(self.request_key, str) or not self.request_key.strip():
            errors['request_key'] = 'Provide a stable request key.'
        elif '*' in self.request_key:
            errors['request_key'] = 'Wildcard request keys are not stable identifiers.'
        if not isinstance(self.payload, dict):
            errors['payload'] = 'Payload must be a JSON object.'
        if self.duty_id and self.binding_id != self.duty.binding_id:
            errors['duty'] = 'The delivery and duty must belong to the same partner.'
        if self.outbox_event_id and self.kind != self.Kind.BUSINESS_EVENT:
            errors['outbox_event'] = 'Only business events reference an outbox row.'
        if errors:
            raise ValidationError(errors)


class AssistantDutySlot(ValidatedAssistantModel):
    """Persist one claimed duty time slot so schedulers cannot double dispatch."""

    duty = models.ForeignKey(
        AssistantDuty, on_delete=models.PROTECT, related_name='slots'
    )
    slot_key = models.CharField(max_length=200, unique=True)
    duty_revision = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    scheduled_at = models.DateTimeField()
    delivery = models.OneToOneField(
        AssistantGatewayDelivery,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='duty_slot',
    )
    claimed_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """The unique slot key is the portable atomic claim."""

        ordering = ['pk']
        indexes = [
            models.Index(fields=['duty', 'scheduled_at'], name='cx_slot_due_idx')
        ]

    def clean(self):
        """Keep slot identity explicit and revision aligned."""
        super().clean()
        errors = {}
        if not isinstance(self.slot_key, str) or not self.slot_key.strip():
            errors['slot_key'] = 'Provide a stable slot key.'
        if self.scheduled_at and timezone.is_naive(self.scheduled_at):
            errors['scheduled_at'] = 'Use a timezone-aware slot time.'
        if self.delivery_id and self.delivery.duty_id != self.duty_id:
            errors['delivery'] = 'The slot delivery must belong to the same duty.'
        if errors:
            raise ValidationError(errors)
