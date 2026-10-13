"""Industry data models which extend, but do not replace, InvenTree records."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from InvenTree.models import InvenTreeAttachmentMixin
from stock.status_codes import StockStatus


class PartCodeAlias(models.Model):
    """Map an ERP, supplier, or OEM code to an existing InvenTree part."""

    class Namespace(models.TextChoices):
        """Identify the source namespace for an alternate part code."""

        ERP = 'erp', _('ERP')
        OEM = 'oem', _('OEM / customer')
        SUPPLIER = 'supplier', _('Supplier')
        LEGACY = 'legacy', _('Legacy system')

    part = models.ForeignKey(
        'part.Part', on_delete=models.PROTECT, related_name='cangxu_code_aliases'
    )
    namespace = models.CharField(max_length=20, choices=Namespace.choices)
    code = models.CharField(max_length=100)
    normalized_code = models.CharField(max_length=100, editable=False)
    source_system = models.CharField(max_length=100, blank=True)
    company_scope = models.CharField(max_length=20, default='*', editable=False)
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_part_code_aliases',
    )
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['namespace', 'normalized_code']
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'namespace',
                    'normalized_code',
                    'source_system',
                    'company_scope',
                ],
                name='cangxu_part_alias_uniq',
            )
        ]
        indexes = [models.Index(fields=['normalized_code', 'namespace'])]
        verbose_name = _('Part code alias')
        verbose_name_plural = _('Part code aliases')

    def save(self, *args, **kwargs):
        """Normalize whitespace and case while preserving significant zeroes."""
        self.code = self.code.strip()
        self.normalized_code = self.code.upper()
        self.company_scope = str(self.company_id) if self.company_id else '*'
        super().save(*args, **kwargs)

    def __str__(self):
        """Return a concise human-readable label for this record."""
        return f'{self.namespace}: {self.code}'


class HardwareProfileRevision(models.Model):
    """Versioned, approved technical specification for an existing InvenTree Part."""

    class Kind(models.TextChoices):
        """Classify hardware without assuming a vendor or physical form."""

        GPU = 'gpu', _('GPU / accelerator')
        ACCELERATOR_BASEBOARD = 'accelerator_baseboard', _('Accelerator baseboard')
        PCIE_SWITCH = 'pcie_switch', _('PCIe switch')
        NVLINK_SWITCH = 'nvlink_switch', _('NVLink / NVSwitch component')
        ETHERNET_SWITCH = 'ethernet_switch', _('Ethernet switch')
        INFINIBAND_SWITCH = 'infiniband_switch', _('InfiniBand switch')
        NIC_HCA_DPU = 'nic_hca_dpu', _('NIC / HCA / DPU')
        RISER = 'riser', _('Riser / adapter board')
        RETIMER = 'retimer', _('Retimer')
        CABLE = 'cable', _('Data / interconnect cable')
        POWER_HARNESS = 'power_harness', _('Power harness')
        OPTICAL_MODULE = 'optical_module', _('Optical module')
        OTHER = 'other', _('Other hardware')

    class Protocol(models.TextChoices):
        """Represent the primary interface or medium for this hardware profile."""

        UNSPECIFIED = 'unspecified', _('Unspecified')
        PCIE = 'pcie', _('PCI Express')
        NVLINK = 'nvlink', _('NVLink')
        ETHERNET = 'ethernet', _('Ethernet')
        INFINIBAND = 'infiniband', _('InfiniBand')
        MCIO = 'mcio', _('MCIO / internal high-speed')
        GPU_POWER = 'gpu_power', _('GPU power')
        OPTICAL = 'optical', _('Optical fiber')
        MANAGEMENT = 'management', _('Management')
        LIQUID_COOLING = 'liquid_cooling', _('Liquid cooling')

    class FormFactor(models.TextChoices):
        """Describe the physical form independently from protocol and function."""

        UNSPECIFIED = 'unspecified', _('Unspecified')
        PCIE_CARD = 'pcie_card', _('PCIe card')
        MODULE = 'module', _('Module / tray')
        BASEBOARD = 'baseboard', _('Baseboard')
        SWITCH_BOARD = 'switch_board', _('Switch board')
        CHIP = 'chip', _('Board-mounted chip')
        CABLE = 'cable', _('Cable assembly')
        EMBEDDED = 'embedded', _('Embedded component')
        RACKMOUNT = 'rackmount', _('Rack-mount device')

    class State(models.TextChoices):
        """Separate editable drafts from signed, immutable engineering revisions."""

        DRAFT = 'draft', _('Draft')
        APPROVED = 'approved', _('Approved')
        SUPERSEDED = 'superseded', _('Superseded')

    part = models.ForeignKey(
        'part.Part', on_delete=models.PROTECT, related_name='cangxu_hardware_profiles'
    )
    revision = models.CharField(max_length=40)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    protocol = models.CharField(
        max_length=24, choices=Protocol.choices, default=Protocol.UNSPECIFIED
    )
    form_factor = models.CharField(
        max_length=24, choices=FormFactor.choices, default=FormFactor.UNSPECIFIED
    )
    chip_vendor = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_chip_profiles',
    )
    board_manufacturer = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_board_profiles',
    )
    specifications = models.JSONField(default=dict, blank=True)
    source_reference = models.CharField(max_length=255)
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    supersedes = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='revisions',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_hardware_profiles_created',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_hardware_profiles_approved',
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Keep revision identity stable and only one engineering revision current."""

        ordering = ['part', '-created_at', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['part', 'revision'], name='cangxu_hwprofile_part_rev_uniq'
            ),
            models.UniqueConstraint(
                fields=['part'],
                condition=models.Q(state='approved'),
                name='cangxu_hwprofile_one_approved',
            ),
        ]
        indexes = [models.Index(fields=['kind', 'protocol', 'state'])]
        verbose_name = _('Hardware profile revision')
        verbose_name_plural = _('Hardware profile revisions')

    def clean(self):
        """Keep switch type and primary protocol consistent."""
        super().clean()
        required_protocols = {
            self.Kind.PCIE_SWITCH: self.Protocol.PCIE,
            self.Kind.NVLINK_SWITCH: self.Protocol.NVLINK,
            self.Kind.ETHERNET_SWITCH: self.Protocol.ETHERNET,
            self.Kind.INFINIBAND_SWITCH: self.Protocol.INFINIBAND,
            self.Kind.POWER_HARNESS: self.Protocol.GPU_POWER,
        }
        expected = required_protocols.get(self.kind)
        if expected and self.protocol != expected:
            raise ValidationError({
                'protocol': _('This hardware kind requires protocol %(protocol)s.')
                % {'protocol': expected}
            })
        if self.kind == self.Kind.CABLE and self.protocol == self.Protocol.UNSPECIFIED:
            raise ValidationError({
                'protocol': _('Select a cable protocol or medium before saving.')
            })

    def __str__(self):
        """Return a concise part and revision label."""
        return f'{self.part} / {self.revision}'


class HardwarePortDefinition(models.Model):
    """Describe a port on a specific hardware revision."""

    profile = models.ForeignKey(
        HardwareProfileRevision, on_delete=models.PROTECT, related_name='ports'
    )
    path = models.CharField(max_length=100)
    protocol = models.CharField(
        max_length=24, choices=HardwareProfileRevision.Protocol.choices
    )
    connector = models.CharField(max_length=80)
    lane_count = models.PositiveSmallIntegerField(null=True, blank=True)
    max_rate = models.CharField(max_length=40, blank=True)
    supported_modes = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        """Make port paths unique within a profile revision."""

        ordering = ['profile', 'path']
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'path'], name='cangxu_hwport_profile_path_uniq'
            )
        ]
        verbose_name = _('Hardware port definition')
        verbose_name_plural = _('Hardware port definitions')

    def clean(self):
        """Keep port definitions on non-cable hardware with matching protocols."""
        super().clean()
        if self.profile_id and self.profile.kind in {
            HardwareProfileRevision.Kind.CABLE,
            HardwareProfileRevision.Kind.POWER_HARNESS,
        }:
            raise ValidationError({
                'profile': _('Use cable ends for cable assemblies.')
            })


class CableEndDefinition(models.Model):
    """Define one end or branch of a cable assembly; breakouts may have many ends."""

    profile = models.ForeignKey(
        HardwareProfileRevision, on_delete=models.PROTECT, related_name='cable_ends'
    )
    label = models.CharField(max_length=40)
    connector = models.CharField(max_length=80)
    protocol = models.CharField(
        max_length=24, choices=HardwareProfileRevision.Protocol.choices
    )
    branch_group = models.CharField(max_length=40, blank=True)
    lane_map = models.JSONField(default=dict, blank=True)
    pinout_reference = models.CharField(max_length=255, blank=True)

    class Meta:
        """Keep branch labels distinct within a cable profile revision."""

        ordering = ['profile', 'label']
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'label'], name='cangxu_cableend_profile_label_uniq'
            )
        ]
        verbose_name = _('Cable end definition')
        verbose_name_plural = _('Cable end definitions')

    def clean(self):
        """Keep each end consistent with its parent cable profile."""
        super().clean()
        if self.profile_id:
            if self.profile.kind not in {
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Kind.POWER_HARNESS,
            }:
                raise ValidationError({
                    'profile': _('Cable ends require a cable profile.')
                })
            if self.protocol != self.profile.protocol:
                raise ValidationError({
                    'protocol': _('Cable end protocol must match its profile.')
                })


class ManufacturingLot(models.Model):
    """A traceable production or supplier lot linked to an existing part."""

    part = models.ForeignKey(
        'part.Part', on_delete=models.PROTECT, related_name='cangxu_lots'
    )
    purchase_order_line = models.ForeignKey(
        'order.PurchaseOrderLineItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_manufacturing_lots',
        help_text=_('Native purchase order line associated with this received lot.'),
    )
    stock_items = models.ManyToManyField(
        'stock.StockItem',
        through='ManufacturingLotStockItem',
        related_name='cangxu_manufacturing_lots',
        blank=True,
    )
    code = models.CharField(max_length=100)
    production_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['part', 'code'], name='cangxu_lot_part_code_uniq'
            )
        ]
        verbose_name = _('Manufacturing lot')
        verbose_name_plural = _('Manufacturing lots')

    def __str__(self):
        """Return a concise human-readable label for this record."""
        return f'{self.part}: {self.code}'

    def clean(self):
        """Ensure a linked purchase line orders the lot's canonical part."""
        super().clean()
        if (
            self.purchase_order_line_id
            and self.part_id
            and self.purchase_order_line.part.part_id != self.part_id
        ):
            raise ValidationError({
                'purchase_order_line': _(
                    'The purchase order line part must match the manufacturing lot part.'
                )
            })


class ManufacturingLotStockItem(models.Model):
    """Link received or produced InvenTree stock items to their manufacturing lot."""

    lot = models.ForeignKey(
        ManufacturingLot, on_delete=models.PROTECT, related_name='stock_item_links'
    )
    stock_item = models.ForeignKey(
        'stock.StockItem', on_delete=models.PROTECT, related_name='lot_links'
    )
    linked_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        constraints = [
            models.UniqueConstraint(
                fields=['lot', 'stock_item'], name='cangxu_lot_stock_uniq'
            )
        ]
        verbose_name = _('Lot stock item')


class PurchaseReceipt(InvenTreeAttachmentMixin, models.Model):
    """Make native purchase receipt submissions safe to retry after timeouts."""

    idempotency_key = models.UUIDField(unique=True)
    request_hash = models.CharField(max_length=64)
    purchase_order_line = models.ForeignKey(
        'order.PurchaseOrderLineItem',
        on_delete=models.PROTECT,
        related_name='cangxu_receipt_requests',
    )
    location = models.ForeignKey(
        'stock.StockLocation', on_delete=models.PROTECT, related_name='cangxu_receipts'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(Decimal('0.00001'))],
    )
    status = models.PositiveSmallIntegerField(default=StockStatus.OK.value)
    batch_code = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    serial_numbers = models.JSONField(default=list, blank=True)
    packaging = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=500, blank=True)
    note = models.TextField(blank=True)
    stock_items = models.ManyToManyField(
        'stock.StockItem', related_name='cangxu_receipt_requests', blank=True
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_purchase_receipts',
    )
    received_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Order receipt attempts for an easy audit trail."""

        ordering = ['-received_at', '-pk']
        verbose_name = _('Purchase receipt request')
        verbose_name_plural = _('Purchase receipt requests')

    @classmethod
    def check_related_permission(cls, permission, user):
        """Authorize receipt archives with the linked purchase-order role."""
        from users.permissions import check_user_role

        if permission not in {'view', 'add', 'change', 'delete'}:
            return False
        required_permission = 'view' if permission == 'view' else 'change'
        return check_user_role(user, 'purchase_order', required_permission)

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Commit the business record and its assistant event together."""
        return super().save(*args, **kwargs)


class PurchaseReceiptInspection(models.Model):
    """Store the signed inspection checklist for one native purchase receipt."""

    class SamplingMethod(models.TextChoices):
        """Record whether the receipt received a full or sampled inspection."""

        FULL = 'full', _('Full inspection')
        SAMPLE = 'sample', _('Sample inspection')

    class MatchResult(models.TextChoices):
        """Describe the part/model comparison against the purchase paperwork."""

        MATCH = 'match', _('Matches')
        WRONG = 'wrong', _('Wrong model')
        OTHER_MISSING = 'other_missing', _('Other model missing')

    class QuantityResult(models.TextChoices):
        """Describe the received quantity comparison."""

        MATCH = 'match', _('Matches')
        SHORT = 'short', _('Shortage')
        EXCESS = 'excess', _('Excess')

    class PackagingCondition(models.TextChoices):
        """Record visible incoming packaging condition."""

        INTACT = 'intact', _('Intact')
        DAMAGED = 'damaged', _('Damaged')
        WET = 'wet', _('Wet')
        DEFORMED = 'deformed', _('Deformed')

    class State(models.TextChoices):
        """Track checklist completion independently from stock availability."""

        DRAFT = 'draft', _('Draft')
        SUBMITTED = 'submitted', _('Submitted')
        PASS = 'pass', _('Passed inspection')
        EXCEPTION = 'exception', _('Exception found')

    class AppearanceIssue(models.TextChoices):
        """Known visual or component anomalies from the paper checklist."""

        SCRATCH = 'scratch', _('Surface scratch')
        STRUCTURE_DEFORMED = 'structure_deformed', _('Structure deformed')
        GOLD_FINGER_SCRATCH = 'gold_finger_scratch', _('Gold finger scratched')
        PART_MISSING = 'part_missing', _('Part missing')
        LABEL_ABNORMAL = 'label_abnormal', _('Label abnormal')
        PORT_DAMAGED = 'port_damaged', _('Port damaged')
        STAIN = 'stain', _('Stain')
        PIN_BENT = 'pin_bent', _('Bent pin')
        COMPONENT_ABNORMAL = 'component_abnormal', _('Electronic component abnormal')
        OTHER = 'other', _('Other appearance issue')

    receipt = models.OneToOneField(
        PurchaseReceipt, on_delete=models.PROTECT, related_name='inspection'
    )
    report_number = models.CharField(max_length=64, unique=True, blank=True)
    sampling_method = models.CharField(
        max_length=12, choices=SamplingMethod.choices, blank=True
    )
    sampled_quantity = models.DecimalField(
        max_digits=15, decimal_places=5, null=True, blank=True
    )
    model_result = models.CharField(
        max_length=20, choices=MatchResult.choices, blank=True
    )
    quantity_result = models.CharField(
        max_length=12, choices=QuantityResult.choices, blank=True
    )
    packaging_condition = models.CharField(
        max_length=12, choices=PackagingCondition.choices, blank=True
    )
    appearance_issues = models.JSONField(default=list, blank=True)
    other_notes = models.TextField(blank=True)
    state = models.CharField(max_length=16, choices=State.choices, default=State.DRAFT)
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_receipt_inspections',
    )
    inspected_at = models.DateTimeField(null=True, blank=True)
    warehouse_signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_receipt_warehouse_signatures',
    )
    warehouse_signed_at = models.DateTimeField(null=True, blank=True)
    purchaser_signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_receipt_purchaser_signatures',
    )
    purchaser_signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Make inspection reports stable and easy to retrieve."""

        ordering = ['-created_at', '-pk']
        indexes = [models.Index(fields=['state', 'created_at'])]
        verbose_name = _('Purchase receipt inspection')
        verbose_name_plural = _('Purchase receipt inspections')

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Assign a stable, human-readable report number from the receipt key."""
        if not self.report_number and self.receipt_id:
            self.report_number = f'IN-{self.receipt_id:08d}'
        super().save(*args, **kwargs)


class PurchaseReceiptFeedback(models.Model):
    """Append technical and purchasing responses to an inspection exception."""

    class Department(models.TextChoices):
        """Identify the receiving team's requested feedback destination."""

        TECHNICAL = 'technical', _('Technical support')
        PURCHASING = 'purchasing', _('Purchasing')

    inspection = models.ForeignKey(
        PurchaseReceiptInspection,
        on_delete=models.PROTECT,
        related_name='feedback_entries',
    )
    department = models.CharField(max_length=16, choices=Department.choices)
    message = models.TextField()
    response = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cangxu_receipt_feedback_created',
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_receipt_feedback_responses',
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Keep feedback in chronological order for the exception audit."""

        ordering = ['created_at', 'pk']
        indexes = [models.Index(fields=['inspection', 'department', 'created_at'])]
        verbose_name = _('Purchase receipt feedback')
        verbose_name_plural = _('Purchase receipt feedback')

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Commit the business record and its assistant event together."""
        return super().save(*args, **kwargs)


class PurchaseReceiptDisposition(models.Model):
    """Record and approve the outcome selected for an inspection exception."""

    class Outcome(models.TextChoices):
        """Represent the three receipt branches in the supplied workflow."""

        NORMAL = 'normal', _('Normal receipt')
        CONCESSION = 'concession', _('Concession receipt')
        RETURN = 'return', _('Return to supplier')

    class State(models.TextChoices):
        """Track the approval boundary before changing stock availability."""

        PENDING = 'pending', _('Pending approval')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        COMPLETED = 'completed', _('Completed')

    inspection = models.OneToOneField(
        PurchaseReceiptInspection, on_delete=models.PROTECT, related_name='disposition'
    )
    outcome = models.CharField(max_length=16, choices=Outcome.choices)
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.PENDING
    )
    request_notes = models.TextField()
    return_location = models.ForeignKey(
        'stock.StockLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_purchase_receipt_returns',
    )
    return_shipment_reference = models.CharField(max_length=100, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cangxu_receipt_dispositions_requested',
    )
    requested_at = models.DateTimeField(default=timezone.now, editable=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_receipt_dispositions_approved',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Expose pending dispositions for approval queues."""

        ordering = ['state', 'requested_at', 'pk']
        indexes = [models.Index(fields=['state', 'requested_at'])]
        verbose_name = _('Purchase receipt disposition')
        verbose_name_plural = _('Purchase receipt dispositions')

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Commit the business record and its assistant event together."""
        return super().save(*args, **kwargs)


class ManufacturingLotPartner(models.Model):
    """Record distinct manufacturing and supply roles for a lot."""

    class Role(models.TextChoices):
        """Identify the business role of this partner."""

        BOARD_MANUFACTURER = 'board', _('Board manufacturer')
        BOARD_BRAND = 'board_brand', _('Board brand')
        CHIP_VENDOR = 'chip_vendor', _('Chip vendor')
        PCB = 'pcb', _('PCB manufacturer')
        SMT = 'smt', _('SMT provider')
        SUPPLIER = 'supplier', _('Supplier')
        OEM = 'oem', _('OEM')

    lot = models.ForeignKey(
        ManufacturingLot, on_delete=models.CASCADE, related_name='partners'
    )
    company = models.ForeignKey(
        'company.Company', on_delete=models.PROTECT, related_name='cangxu_lot_roles'
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        constraints = [
            models.UniqueConstraint(
                fields=['lot', 'company', 'role'], name='cangxu_lot_partner_uniq'
            )
        ]
        verbose_name = _('Lot partner')


class UnitConfiguration(models.Model):
    """An immutable-in-practice revision of an assembled server configuration."""

    class State(models.TextChoices):
        """Enumerate valid states for this workflow."""

        DRAFT = 'draft', _('Draft')
        RELEASED = 'released', _('Released')
        SUPERSEDED = 'superseded', _('Superseded')

    class Kind(models.TextChoices):
        """Classify the type of this record."""

        PLANNED = 'planned', _('Planned configuration')
        ACTUAL = 'actual', _('Actual configuration')
        DELIVERY = 'delivery', _('Delivery configuration')

    unit = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        related_name='cangxu_configurations',
    )
    revision = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.ACTUAL)
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    change_summary = models.TextField(blank=True)
    firmware = models.JSONField(default=dict, blank=True)
    bom_snapshot = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_configurations_created',
    )
    created = models.DateTimeField(default=timezone.now, editable=False)
    released_at = models.DateTimeField(null=True, blank=True)
    supersedes = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='superseded_by',
    )

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['unit', '-revision']
        constraints = [
            models.UniqueConstraint(
                fields=['unit', 'revision'], name='cangxu_config_unit_rev_uniq'
            )
        ]
        verbose_name = _('Unit configuration')
        verbose_name_plural = _('Unit configurations')

    def __str__(self):
        """Return a concise human-readable label for this record."""
        return f'{self.unit} / R{self.revision}'


class ConfigurationItem(models.Model):
    """Record a component and position in one configuration revision."""

    class RemovalKind(models.TextChoices):
        """Distinguish production return, failure take-down, and rework removal."""

        SURPLUS_RETURN = 'surplus_return', _('Surplus return')
        FAILURE_DISASSEMBLY = 'failure_disassembly', _('Failure disassembly')
        REWORK_DISASSEMBLY = 'rework_disassembly', _('Rework disassembly')
        OTHER = 'other', _('Other removal')

    configuration = models.ForeignKey(
        UnitConfiguration, on_delete=models.PROTECT, related_name='items'
    )
    component = models.ForeignKey(
        'stock.StockItem', on_delete=models.PROTECT, related_name='cangxu_config_items'
    )
    position = models.CharField(max_length=100)
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=1,
        validators=[MinValueValidator(Decimal('0.00001'))],
    )
    installed_at = models.DateTimeField(default=timezone.now)
    removed_at = models.DateTimeField(null=True, blank=True)
    installed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_items_installed',
    )
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_items_removed',
    )
    removal_reason = models.TextField(blank=True)
    removal_kind = models.CharField(
        max_length=24, choices=RemovalKind.choices, blank=True, default=''
    )
    source_build_line = models.ForeignKey(
        'build.BuildLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_configuration_items',
    )
    rework_task = models.ForeignKey(
        'cangxu.ReworkTask',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='configuration_items',
    )
    source_build_item = models.ForeignKey(
        'build.BuildItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_configuration_items',
    )

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['position', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['configuration', 'position'],
                condition=Q(removed_at__isnull=True),
                name='cangxu_config_active_position_uniq',
            )
        ]
        indexes = [models.Index(fields=['component', 'removed_at'])]
        verbose_name = _('Configuration item')
        verbose_name_plural = _('Configuration items')

    def __str__(self):
        """Return a concise human-readable label for this record."""
        return f'{self.position}: {self.component}'


class ConfigurationTestEvidence(models.Model):
    """Bind a native test result to the exact configuration it validates."""

    configuration = models.ForeignKey(
        UnitConfiguration, on_delete=models.PROTECT, related_name='test_evidence'
    )
    test_result = models.ForeignKey(
        'stock.StockItemTestResult',
        on_delete=models.PROTECT,
        related_name='cangxu_configuration_evidence',
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_test_evidence_recorded',
    )
    recorded_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        constraints = [
            models.UniqueConstraint(
                fields=['configuration', 'test_result'], name='cangxu_config_test_uniq'
            )
        ]
        verbose_name = _('Configuration test evidence')
        verbose_name_plural = _('Configuration test evidence')


class ComponentReplacement(models.Model):
    """Link a removed item to its replacement in the successor configuration."""

    unit = models.ForeignKey(
        'stock.StockItem', on_delete=models.PROTECT, related_name='cangxu_replacements'
    )
    configuration = models.ForeignKey(
        UnitConfiguration, on_delete=models.PROTECT, related_name='replacements'
    )
    previous_configuration = models.ForeignKey(
        UnitConfiguration,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='replacements_from',
    )
    previous_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        related_name='cangxu_replaced_items',
    )
    replacement_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        related_name='cangxu_replacements_received',
    )
    rework_task = models.ForeignKey(
        'cangxu.ReworkTask',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='component_replacements',
    )
    position = models.CharField(max_length=100)
    reason = models.TextField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_replacements_changed',
    )
    changed_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        constraints = [
            models.UniqueConstraint(
                fields=['configuration', 'previous_item'],
                name='cangxu_replace_item_uniq',
            )
        ]
        verbose_name = _('Component replacement')
        verbose_name_plural = _('Component replacements')


class QualityIssue(models.Model):
    """Track a quality issue against a unit or a specific component."""

    class Severity(models.TextChoices):
        """Rank the impact of this quality issue."""

        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        BLOCKER = 'blocker', _('Blocking')

    class State(models.TextChoices):
        """Enumerate valid states for this workflow."""

        OPEN = 'open', _('Open')
        INVESTIGATING = 'investigating', _('Investigating')
        REWORK = 'rework', _('Rework')
        VERIFY = 'verify', _('Awaiting verification')
        CLOSED = 'closed', _('Closed')

    reference = models.CharField(max_length=40, unique=True)
    unit = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        related_name='cangxu_quality_issues',
    )
    component = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_component_issues',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.MEDIUM
    )
    state = models.CharField(max_length=20, choices=State.choices, default=State.OPEN)
    containment = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    verification_notes = models.TextField(blank=True)
    detected_at = models.DateTimeField(default=timezone.now)
    detected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_issues_detected',
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_issues_closed',
    )
    created = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['-detected_at']
        indexes = [models.Index(fields=['unit', 'state'])]
        verbose_name = _('Quality issue')
        verbose_name_plural = _('Quality issues')

    def __str__(self):
        """Return a concise human-readable label for this record."""
        return f'{self.reference}: {self.title}'


class ReworkTask(models.Model):
    """Track corrective manufacturing work and its verification."""

    class State(models.TextChoices):
        """Enumerate valid states for this workflow."""

        OPEN = 'open', _('Open')
        IN_PROGRESS = 'in_progress', _('In progress')
        VERIFY = 'verify', _('Awaiting verification')
        COMPLETE = 'complete', _('Complete')
        CANCELLED = 'cancelled', _('Cancelled')

    issue = models.ForeignKey(
        QualityIssue, on_delete=models.PROTECT, related_name='rework_tasks'
    )
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.OPEN)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_rework_assigned',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_rework_verified',
    )
    verification_notes = models.TextField(blank=True)
    created = models.DateTimeField(default=timezone.now, editable=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['state', '-created']
        verbose_name = _('Rework task')
        verbose_name_plural = _('Rework tasks')


class ServiceCase(models.Model):
    """Represent customer returns, supplier repairs, and internal failures."""

    class Kind(models.TextChoices):
        """Classify the type of this record."""

        CUSTOMER_RETURN = 'customer_return', _('Customer return')
        SUPPLIER_REPAIR = 'supplier_repair', _('Supplier repair')
        INTERNAL_FAILURE = 'internal_failure', _('Internal failure')

    class State(models.TextChoices):
        """Enumerate valid states for this workflow."""

        OPEN = 'open', _('Open')
        IN_PROGRESS = 'in_progress', _('In progress')
        WAITING = 'waiting', _('Waiting for external party')
        INSPECTION = 'inspection', _('Awaiting inspection')
        CLOSED = 'closed', _('Closed')

    reference = models.CharField(max_length=40, unique=True)
    kind = models.CharField(max_length=30, choices=Kind.choices)
    state = models.CharField(max_length=20, choices=State.choices, default=State.OPEN)
    customer = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_customer_cases',
    )
    supplier = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_supplier_cases',
    )
    source_shipment = models.ForeignKey(
        'order.SalesOrderShipment',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_service_cases',
        help_text=_('Original InvenTree shipment associated with a customer return.'),
    )
    unit = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_service_cases',
    )
    external_reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    opened_at = models.DateTimeField(default=timezone.now)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_cases_opened',
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_cases_closed',
    )

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['-opened_at']
        indexes = [models.Index(fields=['kind', 'state'])]
        verbose_name = _('Service case')
        verbose_name_plural = _('Service cases')

    def __str__(self):
        """Return a concise human-readable label for this record."""
        return self.reference


class ServiceCaseLine(models.Model):
    """Track each repaired, replaced, or returned item independently."""

    class Outcome(models.TextChoices):
        """Record the result for this service line."""

        PENDING = 'pending', _('Pending')
        REPAIRED = 'repaired', _('Repaired')
        REPLACED = 'replaced', _('Replaced')
        SCRAPPED = 'scrapped', _('Scrapped')
        NOT_RETURNED = 'not_returned', _('Not returned')
        NO_FAULT = 'no_fault', _('No fault found')

    case = models.ForeignKey(
        ServiceCase, on_delete=models.PROTECT, related_name='lines'
    )
    stock_item = models.ForeignKey(
        'stock.StockItem', on_delete=models.PROTECT, related_name='cangxu_service_lines'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=1,
        validators=[MinValueValidator(Decimal('0.00001'))],
    )
    fault_description = models.TextField(blank=True)
    outcome = models.CharField(
        max_length=20, choices=Outcome.choices, default=Outcome.PENDING
    )
    replacement_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_replacement_for',
    )
    notes = models.TextField(blank=True)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['id']
        verbose_name = _('Service case line')
        verbose_name_plural = _('Service case lines')


class ServiceCaseEvent(models.Model):
    """Record custody hand-offs and quantities against a service line."""

    class EventType(models.TextChoices):
        """Enumerate custody and inspection events."""

        RECEIVED = 'received', _('Received')
        SENT = 'sent', _('Sent to external party')
        EXTERNAL_RECEIVED = 'external_received', _('Received by external party')
        RETURNED = 'returned', _('Returned by external party')
        INSPECTED = 'inspected', _('Inspected')
        REINSTALLED = 'reinstalled', _('Reinstalled')
        DISPOSED = 'disposed', _('Disposed')
        SCRAPPED = 'scrapped', _('Scrapped')
        NOTE = 'note', _('Note')

    line = models.ForeignKey(
        ServiceCaseLine, on_delete=models.PROTECT, related_name='events'
    )
    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_service_events',
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    company = models.ForeignKey(
        'company.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_service_events',
    )
    from_location = models.ForeignKey(
        'stock.StockLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_service_events_from',
    )
    to_location = models.ForeignKey(
        'stock.StockLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_service_events_to',
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00001'))],
    )
    inspection_passed = models.BooleanField(null=True, blank=True)
    idempotency_key = models.UUIDField(null=True, blank=True, unique=True)
    request_hash = models.CharField(max_length=64, blank=True, default='')
    tracking_reference = models.CharField(max_length=100, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_service_events',
    )
    notes = models.TextField(blank=True)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['occurred_at', 'id']
        verbose_name = _('Service case event')
        verbose_name_plural = _('Service case events')


class MaterialIssue(models.Model):
    """Record a native-stock issue for an untracked consumable BOM line."""

    build_line = models.ForeignKey(
        'build.BuildLine',
        on_delete=models.PROTECT,
        related_name='cangxu_material_issues',
    )
    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        related_name='cangxu_material_issues',
    )
    consumed_stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        related_name='cangxu_consumed_material_issues',
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    idempotency_key = models.UUIDField(unique=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Keep issues newest-first for build traceability."""

        ordering = ['-created_at', '-pk']


class MaterialReturn(models.Model):
    """Record a partial or full return against a previous material issue."""

    issue = models.ForeignKey(
        MaterialIssue, on_delete=models.PROTECT, related_name='returns'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    location = models.ForeignKey(
        'stock.StockLocation',
        on_delete=models.PROTECT,
        related_name='cangxu_material_returns',
    )
    idempotency_key = models.UUIDField(unique=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Keep returns newest-first for audit history."""

        ordering = ['-created_at', '-pk']


class CountSession(models.Model):
    """A reviewable physical stock count anchored to a warehouse location."""

    class State(models.TextChoices):
        """Enumerate valid states for this workflow."""

        OPEN = 'open', _('Open')
        REVIEW = 'review', _('Awaiting review')
        CLOSED = 'closed', _('Closed')

    reference = models.CharField(max_length=40, unique=True)
    location = models.ForeignKey(
        'stock.StockLocation', on_delete=models.PROTECT, related_name='cangxu_counts'
    )
    baseline_at = models.DateTimeField(default=timezone.now)
    state = models.CharField(max_length=20, choices=State.choices, default=State.OPEN)
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_counts_started',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_counts_reviewed',
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['-baseline_at']
        verbose_name = _('Stock count session')
        verbose_name_plural = _('Stock count sessions')


class CountLine(models.Model):
    """Capture expected and counted quantities before an approved adjustment."""

    session = models.ForeignKey(
        CountSession, on_delete=models.PROTECT, related_name='lines'
    )
    part = models.ForeignKey('part.Part', on_delete=models.PROTECT)
    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_count_lines',
    )
    expected_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(Decimal('0.00001'))],
    )
    counted_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_count_lines',
    )
    counted_at = models.DateTimeField(null=True, blank=True)
    discrepancy_reason = models.TextField(blank=True)
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_count_lines_reviewed',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'stock_item'], name='cangxu_count_stock_uniq'
            )
        ]
        verbose_name = _('Stock count line')
        verbose_name_plural = _('Stock count lines')


class ShipmentManifest(models.Model):
    """Freeze the checked contents of one physical package."""

    shipment = models.ForeignKey(
        'order.SalesOrderShipment',
        on_delete=models.PROTECT,
        related_name='cangxu_manifests',
    )
    package_code = models.CharField(max_length=100)
    configuration = models.ForeignKey(
        UnitConfiguration,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='shipment_manifests',
    )
    contents_snapshot = models.JSONField(default=dict, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_manifests_checked',
    )
    checked_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_manifests_signed',
    )
    receipt_notes = models.TextField(blank=True)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        ordering = ['shipment', 'package_code']
        constraints = [
            models.UniqueConstraint(
                fields=['shipment', 'package_code'], name='cangxu_manifest_pkg_uniq'
            )
        ]
        verbose_name = _('Shipment manifest')
        verbose_name_plural = _('Shipment manifests')


class ShipmentManifestLine(models.Model):
    """Record the expected physical items checked into a package."""

    manifest = models.ForeignKey(
        ShipmentManifest, on_delete=models.PROTECT, related_name='lines'
    )
    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.PROTECT,
        related_name='cangxu_manifest_lines',
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=1,
        validators=[MinValueValidator(Decimal('0.00001'))],
    )
    item_role = models.CharField(max_length=40, blank=True)
    scanned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        """Define model metadata, ordering, and database constraints."""

        constraints = [
            models.UniqueConstraint(
                fields=['manifest', 'stock_item'], name='cangxu_manifest_item_uniq'
            )
        ]
        verbose_name = _('Shipment manifest line')
        verbose_name_plural = _('Shipment manifest lines')


class ShipmentReceipt(models.Model):
    """Record one partial or final consignee receipt for a shipped package."""

    manifest = models.ForeignKey(
        ShipmentManifest, on_delete=models.PROTECT, related_name='receipts'
    )
    idempotency_key = models.UUIDField(unique=True)
    request_hash = models.CharField(max_length=64)
    recipient_name = models.CharField(max_length=150, blank=True)
    is_final = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_receipts_recorded',
    )
    received_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Order receipt events and allow a package to close only once."""

        ordering = ['received_at', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['manifest'],
                condition=Q(is_final=True),
                name='cangxu_receipt_manifest_final_uniq',
            )
        ]


class ShipmentReceiptLine(models.Model):
    """Record the received quantity and condition for one expected package item."""

    class Condition(models.TextChoices):
        """Describe whether the expected item arrived in usable condition."""

        OK = 'ok', _('Received as expected')
        SHORT = 'short', _('Not received in full')
        DAMAGED = 'damaged', _('Damaged on arrival')
        WRONG_ITEM = 'wrong_item', _('Unexpected item')

    receipt = models.ForeignKey(
        ShipmentReceipt, on_delete=models.PROTECT, related_name='lines'
    )
    manifest_line = models.ForeignKey(
        ShipmentManifestLine, on_delete=models.PROTECT, related_name='receipt_lines'
    )
    quantity_received = models.DecimalField(
        max_digits=15, decimal_places=5, validators=[MinValueValidator(Decimal('0'))]
    )
    condition = models.CharField(
        max_length=20, choices=Condition.choices, default=Condition.OK
    )
    notes = models.TextField(blank=True)

    class Meta:
        """Prevent duplicate reports for one expected item in a receipt event."""

        ordering = ['manifest_line_id', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['receipt', 'manifest_line'],
                name='cangxu_receipt_line_item_uniq',
            )
        ]


class ShipmentReceiptException(models.Model):
    """Create a follow-up task when final package receipt has a discrepancy."""

    class Kind(models.TextChoices):
        """Classify the unresolved delivery discrepancy."""

        SHORT = 'short', _('Short received')
        DAMAGED = 'damaged', _('Damaged on arrival')
        WRONG_ITEM = 'wrong_item', _('Unexpected item received')

    class State(models.TextChoices):
        """Track follow-up work for the delivery discrepancy."""

        OPEN = 'open', _('Open')
        RESOLVED = 'resolved', _('Resolved')

    receipt_line = models.OneToOneField(
        ShipmentReceiptLine, on_delete=models.PROTECT, related_name='exception'
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    expected_quantity = models.DecimalField(max_digits=15, decimal_places=5)
    received_quantity = models.DecimalField(max_digits=15, decimal_places=5)
    state = models.CharField(max_length=20, choices=State.choices, default=State.OPEN)
    notes = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_receipt_exceptions_resolved',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Keep open delivery follow-ups easy to find."""

        ordering = ['state', 'created_at', 'pk']


class DataImportBatch(models.Model):
    """Track a source file through staging, review, and native ledger posting."""

    class Kind(models.TextChoices):
        """Classify the historical source represented by a batch."""

        OPENING_STOCK = 'opening_stock', _('Opening stock')
        PURCHASE_HISTORY = 'purchase_history', _('Purchase history')
        SHIPMENT_HISTORY = 'shipment_history', _('Shipment history')
        SERVICE_HISTORY = 'service_history', _('Service history')
        PART_CATALOG = 'part_catalog', _('Part catalog')

    class State(models.TextChoices):
        """Track review and apply progress without implying stock changes."""

        DRAFT = 'draft', _('Draft')
        REVIEW = 'review', _('Awaiting review')
        APPROVED = 'approved', _('Approved')
        PARTIAL = 'partial', _('Partially applied')
        APPLIED = 'applied', _('Applied')
        REJECTED = 'rejected', _('Rejected')

    source_system = models.CharField(max_length=100)
    source_kind = models.CharField(max_length=30, choices=Kind.choices)
    source_file_name = models.CharField(max_length=255, blank=True)
    source_file_digest = models.CharField(max_length=64)
    inventory_as_of = models.DateField(null=True, blank=True)
    physical_count_confirmed = models.BooleanField(default=False)
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_import_batches_created',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cangxu_import_batches_reviewed',
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Enforce repeat-upload idempotence and useful review ordering."""

        ordering = ['-created_at', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['source_system', 'source_kind', 'source_file_digest'],
                name='cangxu_import_source_digest_uniq',
            )
        ]
        indexes = [models.Index(fields=['source_kind', 'state'])]
        verbose_name = _('Data import batch')
        verbose_name_plural = _('Data import batches')


class DataImportRecord(models.Model):
    """Keep one source row, its mapping, validation, and native stock result."""

    class State(models.TextChoices):
        """Represent each row's auditable import lifecycle."""

        STAGED = 'staged', _('Staged')
        VALID = 'valid', _('Valid')
        INVALID = 'invalid', _('Needs correction')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        APPLIED = 'applied', _('Applied')
        FAILED = 'failed', _('Apply failed')

    batch = models.ForeignKey(
        DataImportBatch, on_delete=models.PROTECT, related_name='records'
    )
    source_sheet = models.CharField(max_length=100)
    source_row = models.PositiveIntegerField()
    source_range = models.CharField(max_length=100, blank=True)
    source_values = models.JSONField(default=dict)
    normalized_values = models.JSONField(default=dict, blank=True)
    mapped_part = models.ForeignKey(
        'part.Part',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_import_records',
    )
    location = models.ForeignKey(
        'stock.StockLocation',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_import_records',
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00001'))],
    )
    serial = models.CharField(max_length=100, blank=True)
    batch_code = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=20, choices=State.choices, default=State.STAGED)
    validation_errors = models.JSONField(default=list, blank=True)
    apply_error = models.TextField(blank=True)
    stock_item = models.OneToOneField(
        'stock.StockItem',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cangxu_import_record',
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Prevent duplicate source rows within the same import batch."""

        ordering = ['source_sheet', 'source_row', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['batch', 'source_sheet', 'source_row'],
                name='cangxu_import_batch_row_uniq',
            )
        ]
        indexes = [models.Index(fields=['batch', 'state'])]
        verbose_name = _('Data import record')
        verbose_name_plural = _('Data import records')


# Register assistant models with Django without mixing their persistence ownership.
from .assistant_attachment_models import AssistantChatAttachment  # noqa: F401
from .assistant_business_models import (  # noqa: F401
    AssistantRunStop,
    ReceiptArchiveEvidence,
)
from .assistant_delivery_models import (  # noqa: F401
    AssistantDutySlot,
    AssistantGatewayDelivery,
)
from .assistant_models import (  # noqa: F401
    AssistantCommand,
    AssistantDuty,
    AssistantGrant,
    AssistantOutboxEvent,
    PartnerBinding,
)
