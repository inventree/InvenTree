"""Internal transactional command boundary; no model-selected code or API routes.

Only trusted application adapters may construct ToolDefinition. Each adapter must
lock its domain objects and enforce domain preconditions inside the transaction.
File/network effects must not be performed here: they cannot share this commit.
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .assistant_models import (
    AssistantCommand,
    AssistantGrant,
    AssistantOutboxEvent,
    PartnerBinding,
)


class CommandConflictError(ValidationError):
    """Reject a reused command key with a different intent or unknown outcome."""


@dataclass(frozen=True)
class ToolDefinition:
    """Server-owned adapter, permission and event contract, never model arguments."""

    action: str
    object_type: str
    permission_role: str
    permission: str
    execute: Callable
    event_type: str
    validate_limits: Callable | None = None


def canonical_request_hash(request):
    """Hash JSON intent deterministically; reject ambiguous non-JSON values."""
    encoded = json.dumps(
        request,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _check_role(user, tool):
    """Read current role assignments without long-lived worker permission caches."""
    if tool.permission not in {'view', 'add', 'change', 'delete'}:
        raise ValueError('Invalid server tool permission')
    return (
        user.is_superuser
        or user.groups.filter(
            rule_sets__name=tool.permission_role,
            **{f'rule_sets__can_{tool.permission}': True},
        ).exists()
    )


@transaction.atomic
def execute_command(
    *,
    binding_id,
    grant_id,
    grant_version,
    key,
    object_id,
    run_id,
    step_id,
    arguments,
    tool,
):
    """Atomically execute a registered domain adapter and save its durable receipt.

    Lock ordering is binding, user, grant, receipt, then adapter's domain objects.
    Current authority is checked even on replay; a receipt is not new authority.
    SQLite callers must retry lock errors using the SAME command key. This helper
    does not claim cross-system atomicity or expose arbitrary writes to a model.
    """
    if not isinstance(arguments, dict):
        raise ValidationError('Command arguments must be a JSON object')
    object_id = str(object_id)
    intent = {
        'grant_id': grant_id,
        'grant_version': grant_version,
        'object_type': tool.object_type,
        'object_id': object_id,
        'action': tool.action,
        'arguments': arguments,
    }
    digest = canonical_request_hash(intent)
    binding = PartnerBinding.objects.select_for_update().get(pk=binding_id)
    user = get_user_model().objects.select_for_update().get(pk=binding.user_id)
    grant = AssistantGrant.objects.select_for_update().get(pk=grant_id)
    if (
        not binding.enabled
        or not user.is_active
        or grant.binding_id != binding.pk
        or grant.subject_id != user.pk
        or grant.version != grant_version
        or grant.revoked_at is not None
        or (grant.expires_at is not None and grant.expires_at <= timezone.now())
        or (not grant.continuous and grant.expires_at is None)
        or grant.object_type != tool.object_type
        or object_id not in grant.object_ids
        or tool.action not in grant.actions
        or not _check_role(user, tool)
    ):
        raise PermissionDenied('Current authority does not permit this command')
    from .assistant_business_models import AssistantRunStop

    # Limit-aware tools are introduced independently; never silently ignore a cap.
    if grant.limits and (
        tool.validate_limits is None
        or not tool.validate_limits(grant.limits, arguments)
    ):
        raise PermissionDenied('This adapter does not support these grant limits')
    existing = (
        AssistantCommand.objects
        .select_for_update()
        .filter(binding=binding, key=key)
        .first()
    )
    if existing:
        if existing.request_hash != digest:
            raise CommandConflictError(
                'Command key already identifies a different request'
            )
        if existing.status != AssistantCommand.Status.SUCCEEDED:
            raise CommandConflictError('Reconcile the existing command before retrying')
        return existing
    if (
        not binding.write_enabled
        or AssistantRunStop.objects.filter(binding=binding, run_id=run_id).exists()
    ):
        raise PermissionDenied(
            'Autonomous writes for this task are persistently stopped'
        )
    command = AssistantCommand.objects.create(
        binding=binding,
        grant=grant,
        grant_version=grant_version,
        key=key,
        request_hash=digest,
        object_type=tool.object_type,
        object_id=object_id,
        action=tool.action,
        run_id=run_id,
        step_id=step_id,
    )
    # The adapter returns only serializable receipt references plus actual version.
    result, object_version = tool.execute(user, object_id, arguments)
    if not isinstance(result, dict):
        raise ValidationError('Tool result must contain business receipt references')
    canonical_request_hash(result)
    command.status = AssistantCommand.Status.SUCCEEDED
    command.result_reference = result
    command.completed_at = timezone.now()
    command.save()
    AssistantOutboxEvent.objects.create(
        object_type=tool.object_type,
        object_id=object_id,
        object_version=object_version,
        event_type=tool.event_type,
        command=command,
        correlation_id=run_id,
        causation_id=key,
    )
    return command
