"""Small typed receipt tools; inspection, signatures and approval stay human-owned."""

import hashlib

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from common.models import Attachment

from .assistant_business_models import ReceiptArchiveEvidence
from .assistant_models import AssistantGrant, AssistantOutboxEvent, PartnerBinding
from .assistant_services import ToolDefinition, _check_role, execute_command
from .models import (
    PurchaseReceipt,
    PurchaseReceiptDisposition,
    PurchaseReceiptInspection,
)


def _file_digest(source):
    """Read an existing bounded file, with no file writes inside the transaction."""
    if not source.attachment or not source.attachment.storage.exists(
        source.attachment.name
    ):
        raise ValidationError(
            'The archived file is missing; external links are not archive evidence'
        )
    if source.attachment.size > 20 * 1024 * 1024:
        raise ValidationError(
            'Archive evidence larger than 20 MiB needs the existing manual archive flow'
        )
    digest = hashlib.sha256()
    with source.attachment.open('rb') as stream:
        for chunk in stream.chunks():
            digest.update(chunk)
    return digest.hexdigest()


def _validate_archive_limits(limits, arguments):
    """Enforce the only supported scope cap; never silently accept other caps."""
    return (
        set(limits) <= {'attachment_ids'}
        and isinstance(limits.get('attachment_ids', []), list)
        and arguments.get('attachment_id') in limits.get('attachment_ids', [])
    )


def _link_archive(user, object_id, arguments):
    """Link existing evidence in the command transaction without file side effects."""
    if set(arguments) != {'attachment_id', 'kind'}:
        raise ValidationError('Provide only attachment_id and evidence kind')
    if arguments['kind'] not in ReceiptArchiveEvidence.Kind.values:
        raise ValidationError('Evidence kind must be photo or report')
    receipt = PurchaseReceipt.objects.select_for_update().get(pk=object_id)
    source = Attachment.objects.select_for_update().get(pk=arguments['attachment_id'])
    # Source ACL is the same purchase-order role as the receipt; no arbitrary
    # uploaded file or cross-order attachment may be linked by this adapter.
    evidence = ReceiptArchiveEvidence(
        receipt=receipt, attachment=source, kind=arguments['kind'], linked_by=user
    )
    evidence.clean()
    checksum = _file_digest(source)
    evidence.file_name = source.attachment.name
    evidence.sha256 = checksum
    if (
        evidence.kind == ReceiptArchiveEvidence.Kind.PHOTO
        and not source.check_is_image()
    ):
        raise ValidationError('Photo evidence must be a valid stored image')
    existing = ReceiptArchiveEvidence.objects.filter(
        receipt=receipt, attachment=source
    ).first()
    if existing:
        if existing.kind != evidence.kind or existing.sha256 != checksum:
            raise ValidationError(
                'This attachment already has different archived evidence'
            )
        evidence = existing
    else:
        evidence.save()
    return {
        'status': 'linked',
        'evidence_id': evidence.pk,
        'receipt_id': receipt.pk,
        'attachment_id': source.pk,
        'kind': evidence.kind,
        'record_url': f'/api/cangxu/purchase-receipts/{receipt.pk}/',
    }, (
        AssistantOutboxEvent.objects.filter(
            object_type='purchase_receipt', object_id=str(receipt.pk)
        ).aggregate(version=Max('object_version'))['version']
        or 1
    )


LINK_ARCHIVE = ToolDefinition(
    action='receipt.link_archive',
    object_type='purchase_receipt',
    permission_role='purchase_order',
    permission='change',
    execute=_link_archive,
    event_type='receipt.archive_linked',
    validate_limits=_validate_archive_limits,
)
READ_RECEIPT = ToolDefinition(
    action='receipt.read',
    object_type='purchase_receipt',
    permission_role='purchase_order',
    permission='view',
    execute=lambda *_: None,
    event_type='receipt.read',
)


def _read_authority(binding_id, grant_id, grant_version, receipt_id):
    """Reload identity and scope for each query, independently of browser cookies."""
    binding = PartnerBinding.objects.get(pk=binding_id)
    user = get_user_model().objects.get(pk=binding.user_id)
    grant = AssistantGrant.objects.get(pk=grant_id)
    if (
        not binding.enabled
        or not user.is_active
        or grant.binding_id != binding.pk
        or grant.subject_id != user.pk
        or grant.version != grant_version
        or grant.revoked_at is not None
        or (grant.expires_at and grant.expires_at <= timezone.now())
        or (not grant.continuous and not grant.expires_at)
        or grant.object_type != 'purchase_receipt'
        or str(receipt_id) not in grant.object_ids
        or 'receipt.read' not in grant.actions
        or not _check_role(user, READ_RECEIPT)
    ):
        raise PermissionDenied('Current authority does not permit this receipt query')
    return user


def receipt_status(*, binding_id, grant_id, grant_version, receipt_id):
    """Return deterministic completeness facts; never infer inspection or signatures."""
    _read_authority(binding_id, grant_id, grant_version, receipt_id)
    receipt = PurchaseReceipt.objects.select_related('purchase_order_line__order').get(
        pk=receipt_id
    )
    inspection = PurchaseReceiptInspection.objects.filter(receipt=receipt).first()
    missing = []
    if not inspection:
        missing.append('inspection')
    else:
        if inspection.state not in {
            PurchaseReceiptInspection.State.PASS,
            PurchaseReceiptInspection.State.EXCEPTION,
        }:
            missing.append('inspection_conclusion')
        if not inspection.inspector_id or not inspection.inspected_at:
            missing.append('inspector')
        if not inspection.warehouse_signer_id or not inspection.warehouse_signed_at:
            missing.append('warehouse_signature')
        if not inspection.purchaser_signer_id or not inspection.purchaser_signed_at:
            missing.append('purchaser_signature')
        if inspection.state == PurchaseReceiptInspection.State.EXCEPTION:
            disposition = PurchaseReceiptDisposition.objects.filter(
                inspection=inspection
            ).first()
            if (
                not disposition
                or disposition.state != PurchaseReceiptDisposition.State.COMPLETED
            ):
                missing.append('exception_disposition')
    evidence = []
    for link in receipt.archive_evidence.select_related('attachment').order_by('pk'):
        source = link.attachment
        # Revalidate current source location/ACL and file existence on every read.
        try:
            link.clean()
        except ValidationError:
            continue
        try:
            if (
                source.attachment.name != link.file_name
                or _file_digest(source) != link.sha256
            ):
                continue
        except (ValidationError, OSError):
            continue
        evidence.append({
            'id': link.pk,
            'attachment_id': source.pk,
            'kind': link.kind,
            'attachment_url': f'/api/attachment/{source.pk}/',
        })
    for kind in ReceiptArchiveEvidence.Kind.values:
        if not any(entry['kind'] == kind for entry in evidence):
            missing.append(kind)
    return {
        'receipt_id': receipt.pk,
        'purchase_order_id': receipt.purchase_order_line.order_id,
        'quantity': str(receipt.quantity),
        'stock_status': receipt.status,
        'inspection_state': inspection.state if inspection else None,
        'missing': missing,
        'archive_ready': not missing,
        'status': 'ready' if not missing else 'waiting',
        'evidence': evidence,
        'queried_at': timezone.now().isoformat(),
        'record_url': f'/api/cangxu/purchase-receipts/{receipt.pk}/',
    }


@transaction.atomic
def run_receipt_tool(*, binding, payload):
    """Dispatch only registered tools; no arbitrary model field or URL access."""
    if payload['tool'] == 'receipt_status':
        return receipt_status(
            binding_id=binding.pk,
            grant_id=payload['grant_id'],
            grant_version=payload['grant_version'],
            receipt_id=payload['object_id'],
        )
    if payload['tool'] != 'link_receipt_archive':
        raise ValidationError('Unknown assistant business tool')
    command = execute_command(
        binding_id=binding.pk,
        grant_id=payload['grant_id'],
        grant_version=payload['grant_version'],
        key=payload['command_id'],
        object_id=payload['object_id'],
        run_id=payload['run_id'],
        step_id=payload['step_id'],
        arguments=payload['args'],
        tool=LINK_ARCHIVE,
    )
    return {
        **command.result_reference,
        'command_id': command.key,
        'command_receipt_id': command.pk,
    }
