"""Authorization and delivery records for the resident work partner.

Pi owns conversation text and task checkpoints. These records only hold the
application's identity, explicit authority, schedules and business receipts.
"""

import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ValidatedAssistantModel(models.Model):
    """Validate authority metadata on ordinary ORM writes."""

    class Meta:
        """Do not create a separate table for the validation base."""

        abstract = True

    def save(self, *args, **kwargs):
        """Reject incomplete or inconsistent metadata before persisting."""
        self.full_clean()
        return super().save(*args, **kwargs)


class PartnerBinding(ValidatedAssistantModel):
    """Bind one user's partner and primary conversation within a deployment."""

    deployment_id = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    partner_id = models.UUIDField(default=uuid.uuid4, editable=False)
    conversation_id = models.UUIDField(default=uuid.uuid4, editable=False)
    dispatch_owner = models.UUIDField(null=True, blank=True, editable=False)
    dispatch_until = models.DateTimeField(null=True, blank=True, editable=False)
    enabled = models.BooleanField(default=False)
    write_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Prevent duplicate user, partner and conversation bindings."""

        constraints = [
            models.UniqueConstraint(
                fields=['deployment_id', 'user'], name='cx_partner_user_unique'
            ),
            models.UniqueConstraint(
                fields=['deployment_id', 'partner_id'], name='cx_partner_id_unique'
            ),
            models.UniqueConstraint(
                fields=['deployment_id', 'conversation_id'],
                name='cx_partner_chat_unique',
            ),
        ]


class AssistantGrant(ValidatedAssistantModel):
    """Record explicit authority; an empty or expired grant authorizes nothing."""

    binding = models.ForeignKey(
        PartnerBinding, on_delete=models.PROTECT, related_name='grants'
    )
    subject = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    object_type = models.CharField(max_length=100)
    object_ids = models.JSONField(default=list)
    actions = models.JSONField(default=list)
    limits = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    expires_at = models.DateTimeField(null=True, blank=True)
    continuous = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    authorization_reference = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Require a deliberate lifetime and a positive revision."""

        constraints = [
            models.CheckConstraint(
                condition=Q(continuous=True) | Q(expires_at__isnull=False),
                name='cx_grant_lifetime',
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1), name='cx_grant_version'
            ),
        ]

    def clean(self):
        """Reject wildcard authority and cross-user grants."""
        super().clean()
        errors = {}
        if self.binding_id and self.subject_id != self.binding.user_id:
            errors['subject'] = 'The grant subject must own the partner binding.'
        for field in ('object_ids', 'actions'):
            values = getattr(self, field)
            if (
                not isinstance(values, list)
                or not values
                or any(
                    not isinstance(value, str) or not value.strip() or '*' in value
                    for value in values
                )
                or len(values) != len(set(values))
            ):
                errors[field] = (
                    'Provide unique, explicit nonempty strings without wildcards.'
                )
        if '*' in self.object_type:
            errors['object_type'] = 'An explicit object type is required.'
        if not isinstance(self.limits, dict):
            errors['limits'] = 'Limits must be an object.'
        if not self.continuous and self.expires_at is None:
            errors['expires_at'] = (
                'Provide an expiry or explicitly authorize continuous work.'
            )
        if self.expires_at and timezone.is_naive(self.expires_at):
            errors['expires_at'] = 'Use a timezone-aware expiry.'
        if errors:
            raise ValidationError(errors)

    def is_active(self, at=None):
        """Check this metadata snapshot; execution must reload current authority."""
        at = at or timezone.now()
        return bool(
            self.binding.enabled
            and self.subject.is_active
            and self.revoked_at is None
            and (self.continuous or self.expires_at is not None)
            and (self.expires_at is None or self.expires_at > at)
        )


class AssistantDuty(ValidatedAssistantModel):
    """Persist a paused-by-default business responsibility and its next check."""

    binding = models.ForeignKey(
        PartnerBinding, on_delete=models.PROTECT, related_name='duties'
    )
    grant = models.ForeignKey(
        AssistantGrant, on_delete=models.PROTECT, related_name='duties'
    )
    name = models.CharField(max_length=200)
    goal = models.TextField()
    trigger_filter = models.JSONField(default=dict, blank=True)
    interval_seconds = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )
    time_zone = models.CharField(max_length=100, default='Asia/Shanghai')
    next_run_at = models.DateTimeField(null=True, blank=True)
    cursor = models.JSONField(default=dict, blank=True)
    paused = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Index due duties and forbid nonpositive schedules or revisions."""

        indexes = [models.Index(fields=['paused', 'next_run_at'])]
        constraints = [
            models.CheckConstraint(
                condition=Q(interval_seconds__isnull=True) | Q(interval_seconds__gte=1),
                name='cx_duty_interval',
            ),
            models.CheckConstraint(condition=Q(version__gte=1), name='cx_duty_version'),
        ]

    def clean(self):
        """Require consistent ownership, a real timezone and durable schedule."""
        super().clean()
        errors = {}
        if self.grant_id and self.binding_id != self.grant.binding_id:
            errors['grant'] = 'The duty and grant must belong to the same partner.'
        try:
            ZoneInfo(self.time_zone)
        except (ZoneInfoNotFoundError, ValueError):
            errors['time_zone'] = 'Provide a valid IANA timezone.'
        if self.interval_seconds and not self.next_run_at:
            errors['next_run_at'] = 'Scheduled duties require a persisted next check.'
        if self.next_run_at and timezone.is_naive(self.next_run_at):
            errors['next_run_at'] = 'Use a timezone-aware next check.'
        for field in ('trigger_filter', 'cursor'):
            if not isinstance(getattr(self, field), dict):
                errors[field] = 'Provide an object.'
        if errors:
            raise ValidationError(errors)


class AssistantCommand(ValidatedAssistantModel):
    """Keep a scoped idempotency key and receipt, never a stock balance."""

    class Status(models.TextChoices):
        """Describe the persisted execution outcome."""

        PENDING = 'pending', 'Pending'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'

    binding = models.ForeignKey(
        PartnerBinding, on_delete=models.PROTECT, related_name='commands'
    )
    grant = models.ForeignKey(
        AssistantGrant,
        on_delete=models.PROTECT,
        related_name='commands',
        null=True,
        blank=True,
    )
    grant_version = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    key = models.CharField(max_length=200)
    request_hash = models.CharField(
        max_length=64,
        validators=[
            RegexValidator(r'\A[0-9a-f]{64}\Z', 'Provide a canonical SHA-256 digest.')
        ],
    )
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    run_id = models.CharField(max_length=200)
    step_id = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    result_reference = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Scope deduplication to the partner rather than a transient run."""

        constraints = [
            models.UniqueConstraint(
                fields=['binding', 'key'], name='cx_command_key_unique'
            ),
            models.CheckConstraint(
                condition=Q(grant_version__gte=1), name='cx_command_grant_version'
            ),
        ]

    def clean(self):
        """Prevent a receipt from crossing partner boundaries."""
        super().clean()
        if self.grant_id and self.binding_id != self.grant.binding_id:
            raise ValidationError({
                'grant': 'The command and grant must belong to the same partner.'
            })
        if not isinstance(self.result_reference, dict):
            raise ValidationError({'result_reference': 'Provide an object reference.'})


class AssistantOutboxEvent(ValidatedAssistantModel):
    """Hold minimal business references until durable downstream acknowledgement."""

    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_version = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    event_type = models.CharField(max_length=100)
    command = models.ForeignKey(
        AssistantCommand,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='events',
    )
    correlation_id = models.CharField(max_length=200, blank=True)
    causation_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    available_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        """Support retry scans without embedding business snapshots."""

        indexes = [models.Index(fields=['delivered_at', 'available_at'])]
        constraints = [
            models.CheckConstraint(
                condition=Q(object_version__gte=1), name='cx_event_version'
            )
        ]
