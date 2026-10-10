"""Industry data models which extend, but do not replace, InvenTree records."""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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
