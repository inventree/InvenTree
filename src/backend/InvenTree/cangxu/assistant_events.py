"""Transactional receipt event references with scoped periodic reconciliation fallback."""

from django.db import transaction
from django.db.models import Max
from django.db.models.signals import post_delete, post_save

from .assistant_models import AssistantOutboxEvent


def emit_receipt_change(receipt_id, *, using='default'):
    """Allocate a monotonically increasing event revision under the receipt lock."""
    from .models import PurchaseReceipt

    with transaction.atomic(using=using):
        if (
            not PurchaseReceipt.objects
            .using(using)
            .select_for_update()
            .filter(pk=receipt_id)
            .first()
        ):
            return
        previous = (
            AssistantOutboxEvent.objects
            .using(using)
            .filter(object_type='purchase_receipt', object_id=str(receipt_id))
            .aggregate(version=Max('object_version'))['version']
            or 0
        )
        AssistantOutboxEvent.objects.using(using).create(
            object_type='purchase_receipt',
            object_id=str(receipt_id),
            object_version=previous + 1,
            event_type='receipt.changed',
        )


def receipt_changed(sender, instance, using='default', raw=False, **kwargs):
    """Persist a reference only, never inspection text or attachment content."""
    if raw:
        return
    from .models import (
        PurchaseReceipt,
        PurchaseReceiptDisposition,
        PurchaseReceiptFeedback,
    )

    if sender is PurchaseReceipt:
        receipt_id = instance.pk
    elif sender in {PurchaseReceiptDisposition, PurchaseReceiptFeedback}:
        receipt_id = instance.inspection.receipt_id
    else:
        receipt_id = instance.receipt_id
    emit_receipt_change(receipt_id, using=using)


def attachment_changed(sender, instance, using='default', raw=False, **kwargs):
    """Discover native purchase attachments as well as the industry archive path.

    The native Attachment.save is atomic. Bulk updates, source reassignment and
    orders with more than 500 receipts are covered by scoped duty reconciliation.
    """
    if raw:
        return
    from .models import PurchaseReceipt

    if instance.model_type == 'purchasereceipt':
        emit_receipt_change(instance.model_id, using=using)
    elif instance.model_type == 'purchaseorder':
        receipt_ids = (
            PurchaseReceipt.objects
            .using(using)
            .filter(purchase_order_line__order_id=instance.model_id)
            .order_by('pk')
            .values_list('pk', flat=True)[:500]
        )
        for receipt_id in receipt_ids:
            emit_receipt_change(receipt_id, using=using)


def register_receipt_events():
    """Register stable receivers once when the application is ready."""
    from common.models import Attachment

    from .assistant_business_models import ReceiptArchiveEvidence
    from .models import (
        PurchaseReceipt,
        PurchaseReceiptDisposition,
        PurchaseReceiptFeedback,
        PurchaseReceiptInspection,
    )

    for model in (
        PurchaseReceipt,
        PurchaseReceiptInspection,
        PurchaseReceiptFeedback,
        PurchaseReceiptDisposition,
        ReceiptArchiveEvidence,
    ):
        for signal, label in ((post_save, 'save'), (post_delete, 'delete')):
            signal.connect(
                receipt_changed,
                sender=model,
                weak=False,
                dispatch_uid=f'cangxu.receipt.{model.__name__}.{label}',
            )
    for signal, label in ((post_save, 'save'), (post_delete, 'delete')):
        signal.connect(
            attachment_changed,
            sender=Attachment,
            weak=False,
            dispatch_uid=f'cangxu.receipt.attachment.{label}',
        )
