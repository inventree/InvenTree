"""Archive references reuse native attachments without duplicating stored files."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class ReceiptArchiveEvidence(models.Model):
    """Associate an explicitly identified existing attachment with one receipt."""

    class Kind(models.TextChoices):
        """Distinguish evidence without interpreting filenames as inspection facts."""

        PHOTO = 'photo', 'Photo'
        REPORT = 'report', 'Inspection report'

    receipt = models.ForeignKey(
        'cangxu.PurchaseReceipt',
        on_delete=models.PROTECT,
        related_name='archive_evidence',
    )
    attachment = models.ForeignKey(
        'common.Attachment',
        on_delete=models.PROTECT,
        related_name='cangxu_receipt_evidence',
    )
    kind = models.CharField(max_length=12, choices=Kind.choices)
    file_name = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64)
    linked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    linked_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """One source attachment has one interpretation within a receipt."""

        constraints = [
            models.UniqueConstraint(
                fields=['receipt', 'attachment'], name='cx_receipt_evidence_unique'
            )
        ]

    def clean(self):
        """Keep source records within the same purchase or explicit receipt."""
        super().clean()
        if not self.receipt_id or not self.attachment_id:
            return
        source = self.attachment
        receipt = self.receipt
        if not (
            (source.model_type == 'purchasereceipt' and source.model_id == receipt.pk)
            or (
                source.model_type == 'purchaseorder'
                and source.model_id == receipt.purchase_order_line.order_id
            )
        ):
            raise ValidationError(
                'Archive evidence must belong to the receipt or its purchase order'
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Validate business association before ordinary ORM writes."""
        self.full_clean()
        return super().save(*args, **kwargs)


class AssistantRunStop(models.Model):
    """Freeze one Pi task before cancellation without revoking its whole duty."""

    binding = models.ForeignKey('cangxu.PartnerBinding', on_delete=models.PROTECT)
    run_id = models.CharField(max_length=200)
    stopped_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Task identity is scoped to one partner's persistent storage."""

        constraints = [
            models.UniqueConstraint(
                fields=['binding', 'run_id'], name='cx_run_stop_unique'
            )
        ]
