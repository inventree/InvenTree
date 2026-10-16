"""REST serializers for the Cangxu industry models."""

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from build.models import BuildLine
from InvenTree.helpers import extract_serial_numbers
from InvenTree.serializers import InvenTreeModelSerializer
from order.models import PurchaseOrderLineItem
from stock.models import StockItem, StockLocation
from stock.status_codes import StockStatus

from .models import (
    CableEndDefinition,
    ComponentReplacement,
    ConfigurationItem,
    ConfigurationTestEvidence,
    CountLine,
    CountSession,
    DataImportBatch,
    DataImportRecord,
    HardwarePortDefinition,
    HardwareProfileRevision,
    ManufacturingLot,
    ManufacturingLotPartner,
    ManufacturingLotStockItem,
    MaterialIssue,
    PartCodeAlias,
    PurchaseReceipt,
    PurchaseReceiptDisposition,
    PurchaseReceiptFeedback,
    PurchaseReceiptInspection,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseEvent,
    ServiceCaseLine,
    ShipmentManifest,
    ShipmentManifestLine,
    ShipmentReceipt,
    ShipmentReceiptException,
    ShipmentReceiptLine,
    UnitConfiguration,
)


class PartCodeAliasSerializer(InvenTreeModelSerializer):
    """Resolve alternate company and system codes to one canonical Part."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = PartCodeAlias
        fields = '__all__'
        read_only_fields = ['normalized_code', 'company_scope', 'created']


class HardwareProfileRevisionSerializer(InvenTreeModelSerializer):
    """Expose versioned hardware kind, protocol, and sourced specifications."""

    class Meta:
        """Configure profile revision fields and server-controlled approval state."""

        model = HardwareProfileRevision
        fields = '__all__'
        read_only_fields = [
            'state',
            'created_by',
            'approved_by',
            'supersedes',
            'created_at',
            'approved_at',
        ]

    def validate_specifications(self, value):
        """Require a JSON object so parameters can include explicit units."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                _('Specifications must be an object with values and units.')
            )
        return value


class HardwarePortDefinitionSerializer(InvenTreeModelSerializer):
    """Expose typed connector and lane definitions for a hardware revision."""

    class Meta:
        """Configure port definition fields."""

        model = HardwarePortDefinition
        fields = '__all__'

    def validate(self, attrs):
        """Apply model-level profile and protocol invariants to API writes."""
        attrs = super().validate(attrs)
        instance = self.instance or HardwarePortDefinition()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            ) from exc
        return attrs


class CableEndDefinitionSerializer(InvenTreeModelSerializer):
    """Expose arbitrary cable ends, including breakout branches."""

    class Meta:
        """Configure cable end definition fields."""

        model = CableEndDefinition
        fields = '__all__'

    def validate(self, attrs):
        """Apply model-level cable-kind and protocol invariants to API writes."""
        attrs = super().validate(attrs)
        instance = self.instance or CableEndDefinition()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            ) from exc
        return attrs


class ManufacturingLotSerializer(InvenTreeModelSerializer):
    """Expose traceable production batches."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ManufacturingLot
        fields = '__all__'
        read_only_fields = ['created', 'stock_items']

    def validate(self, attrs):
        """Keep the lot's canonical part aligned with its native PO line."""
        attrs = super().validate(attrs)
        part = attrs.get('part', getattr(self.instance, 'part', None))
        purchase_order_line = attrs.get(
            'purchase_order_line', getattr(self.instance, 'purchase_order_line', None)
        )

        if part and purchase_order_line and part.pk != purchase_order_line.part.part_id:
            raise serializers.ValidationError({
                'purchase_order_line': _(
                    'The purchase order line part must match the manufacturing lot part.'
                )
            })

        return attrs


class ManufacturingLotPartnerSerializer(InvenTreeModelSerializer):
    """Expose supplier, board maker, PCB and SMT roles independently."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ManufacturingLotPartner
        fields = '__all__'


class PurchaseReceiptSerializer(InvenTreeModelSerializer):
    """Expose the immutable idempotency key and stock created by a receipt."""

    stock_items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    purchase_order_number = serializers.CharField(
        source='purchase_order_line.order.reference', read_only=True
    )
    part_name = serializers.CharField(
        source='purchase_order_line.part.part.name', read_only=True
    )
    part_code = serializers.CharField(
        source='purchase_order_line.part.part.IPN', read_only=True
    )
    inspection_id = serializers.SerializerMethodField()
    archive_evidence = serializers.SerializerMethodField()

    def get_archive_evidence(self, obj) -> list[dict]:
        """Expose archive associations only while the original source is viewable."""
        request = self.context.get('request')
        if request is None:
            return []
        result = []
        for evidence in obj.archive_evidence.select_related('attachment'):
            try:
                evidence.clean()
                source = evidence.attachment
                if not source.check_permission('view', request.user):
                    continue
            except DjangoValidationError:
                continue
            result.append({
                'id': evidence.pk,
                'attachment_id': source.pk,
                'kind': evidence.kind,
                'sha256': evidence.sha256,
                'linked_by': evidence.linked_by_id,
                'linked_at': evidence.linked_at,
                'integrity': 'not_rechecked',
            })
        return result

    def get_inspection_id(self, obj) -> int | None:
        """Return the linked checklist ID without failing on uninspected receipts."""
        try:
            return obj.inspection.pk
        except PurchaseReceiptInspection.DoesNotExist:
            return None

    class Meta:
        """Keep receipt submissions read-only after native stock is posted."""

        model = PurchaseReceipt
        fields = '__all__'
        read_only_fields = [
            'id',
            'idempotency_key',
            'request_hash',
            'purchase_order_line',
            'location',
            'quantity',
            'status',
            'batch_code',
            'expiry_date',
            'serial_numbers',
            'packaging',
            'barcode',
            'note',
            'stock_items',
            'received_by',
            'received_at',
        ]


class PurchaseReceiptInspectionSerializer(InvenTreeModelSerializer):
    """Capture the paper incoming-inspection checklist and signatures."""

    appearance_issues = serializers.ListField(
        child=serializers.ChoiceField(
            choices=PurchaseReceiptInspection.AppearanceIssue.choices
        ),
        allow_empty=True,
        required=False,
    )

    class Meta:
        """Keep report identity, workflow state, and signatures server controlled."""

        model = PurchaseReceiptInspection
        fields = '__all__'
        read_only_fields = [
            'report_number',
            'state',
            'inspector',
            'inspected_at',
            'warehouse_signer',
            'warehouse_signed_at',
            'purchaser_signer',
            'purchaser_signed_at',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        """Keep sample quantity within the linked native receipt quantity."""
        attrs = super().validate(attrs)
        instance = self.instance or PurchaseReceiptInspection()
        for field, value in attrs.items():
            setattr(instance, field, value)
        receipt = attrs.get('receipt') or (
            self.instance.receipt if self.instance else None
        )
        method = attrs.get('sampling_method', instance.sampling_method)
        quantity = attrs.get('sampled_quantity', instance.sampled_quantity)
        if receipt and method == PurchaseReceiptInspection.SamplingMethod.FULL:
            if quantity is not None and quantity != receipt.quantity:
                raise serializers.ValidationError({
                    'sampled_quantity': _(
                        'Full inspection quantity must equal the receipt quantity.'
                    )
                })
        elif receipt and method == PurchaseReceiptInspection.SamplingMethod.SAMPLE:
            if quantity is None or quantity <= 0 or quantity > receipt.quantity:
                raise serializers.ValidationError({
                    'sampled_quantity': _(
                        'Sample quantity must be positive and no greater than the receipt quantity.'
                    )
                })
        return attrs


class PurchaseReceiptFeedbackSerializer(InvenTreeModelSerializer):
    """Record a routed technical-support or purchasing feedback request."""

    class Meta:
        """Keep response identity and timestamps server controlled."""

        model = PurchaseReceiptFeedback
        fields = '__all__'
        read_only_fields = [
            'response',
            'created_by',
            'created_at',
            'responded_by',
            'responded_at',
        ]

    def validate(self, attrs):
        """Supply the actor before InvenTree performs model-level validation."""
        if self.instance is None:
            attrs['created_by'] = self.context['request'].user
        return super().validate(attrs)


class PurchaseReceiptDispositionSerializer(InvenTreeModelSerializer):
    """Request normal, concession, or supplier-return disposition."""

    class Meta:
        """Keep approval state and actors controlled by workflow actions."""

        model = PurchaseReceiptDisposition
        fields = '__all__'
        read_only_fields = [
            'state',
            'requested_by',
            'requested_at',
            'approved_by',
            'approved_at',
            'approval_notes',
            'completed_at',
        ]

    def validate(self, attrs):
        """Supply the requester before InvenTree performs model validation."""
        if self.instance is None:
            attrs['requested_by'] = self.context['request'].user
        return super().validate(attrs)


class PurchaseReceiptApprovalSerializer(serializers.Serializer):
    """Validate approval or rejection notes for an incoming exception."""

    approved = serializers.BooleanField()
    notes = serializers.CharField(
        allow_blank=True, required=False, default='', max_length=4000
    )


class PurchaseReceiptFeedbackResponseSerializer(serializers.Serializer):
    """Validate a one-time response from the routed department."""

    response = serializers.CharField(allow_blank=False, max_length=4000)


class PurchaseReceiptRequestSerializer(serializers.Serializer):
    """Validate one idempotent, possibly serialized purchase receipt."""

    idempotency_key = serializers.UUIDField()
    purchase_order_line = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrderLineItem.objects.select_related('part__part', 'order')
    )
    quantity = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal('0.00001')
    )
    location = serializers.PrimaryKeyRelatedField(queryset=StockLocation.objects.all())
    status = serializers.ChoiceField(
        choices=[
            (StockStatus.OK.value, _('Available')),
            (StockStatus.QUARANTINED.value, _('Quarantined')),
        ],
        default=StockStatus.OK.value,
    )
    batch_code = serializers.CharField(max_length=100, required=False, allow_blank=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    serial_numbers = serializers.JSONField(required=False, default=list)
    packaging = serializers.CharField(max_length=50, required=False, allow_blank=True)
    barcode = serializers.CharField(max_length=500, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Require exact serial coverage for serialized supplier quantities."""
        attrs = super().validate(attrs)
        line = attrs['purchase_order_line']
        serial_numbers = attrs['serial_numbers']
        if isinstance(serial_numbers, str):
            serial_text = serial_numbers.strip()
            if serial_text:
                part = line.part.part if line.part else None
                try:
                    serial_numbers = extract_serial_numbers(
                        serial_text,
                        line.part.base_quantity(attrs['quantity']),
                        part.get_latest_serial_number() if part else None,
                        part=part,
                    )
                except (DjangoValidationError, AttributeError) as exc:
                    raise serializers.ValidationError({
                        'serial_numbers': getattr(exc, 'messages', [str(exc)])
                    }) from exc
            else:
                serial_numbers = []
            attrs['serial_numbers'] = serial_numbers
        if not isinstance(serial_numbers, list) or not all(
            isinstance(serial, str) for serial in serial_numbers
        ):
            raise serializers.ValidationError({
                'serial_numbers': _('Provide serial numbers as a list or range string.')
            })
        if len(serial_numbers) != len(set(serial_numbers)):
            raise serializers.ValidationError({
                'serial_numbers': _('Serial numbers must be unique in a receipt.')
            })

        if serial_numbers:
            supplier_part = line.part
            if not supplier_part or not supplier_part.part:
                raise serializers.ValidationError({
                    'purchase_order_line': _('The order line has no linked part.')
                })
            base_quantity = supplier_part.base_quantity(attrs['quantity'])
            if base_quantity != base_quantity.to_integral_value():
                raise serializers.ValidationError({
                    'quantity': _('Serialized stock quantity must be a whole number.')
                })
            if len(serial_numbers) != int(base_quantity):
                raise serializers.ValidationError({
                    'serial_numbers': _(
                        'Provide one serial number for each received stock item.'
                    )
                })
            if any(len(serial) > 100 for serial in serial_numbers):
                raise serializers.ValidationError({
                    'serial_numbers': _('Serial numbers cannot exceed 100 characters.')
                })
            # InvenTree's native receive validates serial uniqueness and part
            # rules when posting new stock. Keep this serializer structural so
            # a legitimate idempotent replay can return already-created serials.
        elif line.part and line.part.part and line.part.part.trackable:
            raise serializers.ValidationError({
                'serial_numbers': _(
                    'Serial numbers are required for this trackable part.'
                )
            })

        return attrs


class PurchaseReceiptBulkRequestSerializer(serializers.Serializer):
    """Validate an all-or-nothing submission of independent PO receipts."""

    receipts = PurchaseReceiptRequestSerializer(many=True, allow_empty=False)

    def validate_receipts(self, receipts):
        """Require each order line and idempotency key to appear only once."""
        line_ids = [row['purchase_order_line'].pk for row in receipts]
        keys = [row['idempotency_key'] for row in receipts]
        if len(line_ids) != len(set(line_ids)):
            raise serializers.ValidationError(
                'Each purchase order line may appear once.'
            )
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError(
                'Each receipt must use a unique idempotency key.'
            )
        return receipts


class ManufacturingLotStockItemSerializer(InvenTreeModelSerializer):
    """Link an existing stock record to a manufacturing lot."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ManufacturingLotStockItem
        fields = '__all__'
        read_only_fields = ['linked_at']

    def validate(self, attrs):
        """Validate related records and enforce workflow constraints."""
        attrs = super().validate(attrs)
        lot = attrs.get('lot', getattr(self.instance, 'lot', None))
        stock_item = attrs.get('stock_item', getattr(self.instance, 'stock_item', None))

        if lot and stock_item and lot.part_id != stock_item.part_id:
            raise serializers.ValidationError({
                'stock_item': _('The stock item must match the lot part.')
            })

        if lot and stock_item and stock_item.batch and stock_item.batch != lot.code:
            raise serializers.ValidationError({
                'stock_item': _('The stock item batch must match the lot code.')
            })

        return attrs


class UnitConfigurationSerializer(InvenTreeModelSerializer):
    """Expose versioned configuration revisions without client-assigned numbers."""

    revision = serializers.IntegerField(read_only=True, default=1)

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = UnitConfiguration
        fields = '__all__'
        read_only_fields = [
            'revision',
            'state',
            'bom_snapshot',
            'supersedes',
            'created_by',
            'created',
            'released_at',
        ]

    def get_fields(self):
        """Apply the field write policy for this serializer instance."""
        fields = super().get_fields()
        if self.instance:
            fields['unit'].read_only = True
        return fields

    def validate(self, attrs):
        """Validate related records and enforce workflow constraints."""
        attrs = super().validate(attrs)
        if self.instance and self.instance.state != UnitConfiguration.State.DRAFT:
            raise serializers.ValidationError(
                _('Only draft configurations can be changed.')
            )
        if self.instance and self.instance.test_evidence.exists():
            raise serializers.ValidationError(
                _('Create a new configuration revision after recording test evidence.')
            )
        return attrs


class ConfigurationItemSerializer(InvenTreeModelSerializer):
    """Validate component assignment to a configuration position."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ConfigurationItem
        fields = '__all__'
        read_only_fields = [
            'installed_at',
            'removed_at',
            'installed_by',
            'removed_by',
            'removal_reason',
            'removal_kind',
            'source_build_item',
        ]

    def validate(self, attrs):
        """Validate related records and enforce workflow constraints."""
        attrs = super().validate(attrs)
        if self.instance:
            raise serializers.ValidationError(
                _(
                    'Configuration items are changed through install or remove operations.'
                )
            )
        config = attrs.get('configuration')
        component = attrs.get('component')
        quantity = attrs.get('quantity', 1)

        if config and config.state != UnitConfiguration.State.DRAFT:
            raise serializers.ValidationError({
                'configuration': _('Only draft configurations can be changed.')
            })
        if config and config.test_evidence.exists():
            raise serializers.ValidationError(
                _('Create a new configuration revision after recording test evidence.')
            )

        if config and component:
            if config.unit_id == component.pk:
                raise serializers.ValidationError({
                    'component': _('A unit cannot be installed into itself.')
                })

            position = attrs.get('position')
            if (
                position
                and config.items.filter(
                    position=position, removed_at__isnull=True
                ).exists()
            ):
                raise serializers.ValidationError({
                    'position': _(
                        'The position is already occupied in this configuration.'
                    )
                })

            if component.serialized and quantity != 1:
                raise serializers.ValidationError({
                    'quantity': _('Serialized components must have quantity one.')
                })

            source_build_line = attrs.get('source_build_line')
            if source_build_line and (
                config.unit.build_id != source_build_line.build_id
                or source_build_line.bom_item.sub_part_id != component.part_id
            ):
                raise serializers.ValidationError({
                    'source_build_line': _(
                        'The work order line must belong to this unit and match the component part.'
                    )
                })

        return attrs


class ConfigurationTestEvidenceSerializer(InvenTreeModelSerializer):
    """Bind native stock test results to a specific configuration revision."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ConfigurationTestEvidence
        fields = '__all__'
        read_only_fields = ['recorded_by', 'recorded_at']


class ComponentReplacementSerializer(InvenTreeModelSerializer):
    """Expose the immutable relation between the removed and replacement items."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ComponentReplacement
        fields = '__all__'

    def get_fields(self):
        """Apply the field write policy for this serializer instance."""
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields


class QualityIssueSerializer(InvenTreeModelSerializer):
    """Track a quality issue against a unit and, optionally, a component."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = QualityIssue
        fields = '__all__'
        read_only_fields = [
            'state',
            'detected_by',
            'verification_notes',
            'closed_at',
            'closed_by',
            'created',
        ]


class ReworkTaskSerializer(InvenTreeModelSerializer):
    """Record corrective work and its independent verification."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ReworkTask
        fields = '__all__'
        read_only_fields = [
            'state',
            'verified_by',
            'verification_notes',
            'created',
            'completed_at',
        ]


class ServiceCaseSerializer(InvenTreeModelSerializer):
    """Distinguish customer returns from supplier repairs."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ServiceCase
        fields = '__all__'
        read_only_fields = ['state', 'opened_by', 'closed_at', 'closed_by']

    def validate(self, attrs):
        """Validate related records and enforce workflow constraints."""
        attrs = super().validate(attrs)
        kind = attrs.get('kind', getattr(self.instance, 'kind', None))
        customer = attrs.get('customer', getattr(self.instance, 'customer', None))
        supplier = attrs.get('supplier', getattr(self.instance, 'supplier', None))
        source_shipment = attrs.get(
            'source_shipment', getattr(self.instance, 'source_shipment', None)
        )
        unit = attrs.get('unit', getattr(self.instance, 'unit', None))

        if kind == ServiceCase.Kind.CUSTOMER_RETURN and not customer:
            raise serializers.ValidationError({
                'customer': _('A customer is required for a customer return.')
            })

        if kind == ServiceCase.Kind.SUPPLIER_REPAIR and not supplier:
            raise serializers.ValidationError({
                'supplier': _('A supplier is required for a supplier repair.')
            })

        if customer and supplier:
            raise serializers.ValidationError(
                _('A service case cannot be owned by both a customer and supplier.')
            )

        if source_shipment and customer:
            if source_shipment.order.customer_id != customer.pk:
                raise serializers.ValidationError({
                    'source_shipment': _(
                        'The source shipment must belong to the service case customer.'
                    )
                })

        if source_shipment and not source_shipment.shipment_date:
            raise serializers.ValidationError({
                'source_shipment': _(
                    'A customer return must reference a completed shipment.'
                )
            })

        if source_shipment and unit:
            if not source_shipment.allocations.filter(item=unit).exists():
                raise serializers.ValidationError({
                    'unit': _('The source shipment must contain the service case unit.')
                })

        if self.instance and self.instance.lines.exists():
            immutable = {
                'kind': self.instance.kind,
                'customer': self.instance.customer_id,
                'supplier': self.instance.supplier_id,
                'source_shipment': self.instance.source_shipment_id,
                'unit': self.instance.unit_id,
            }
            if any(
                attrs.get(name, current) != current
                for name, current in immutable.items()
            ):
                raise serializers.ValidationError(
                    _(
                        'Service case identity cannot change after lines have been added.'
                    )
                )

        return attrs


class ServiceCaseLineSerializer(InvenTreeModelSerializer):
    """Track each returned stock item and its replacement independently."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ServiceCaseLine
        fields = '__all__'
        read_only_fields = ['outcome']

    def validate(self, attrs):
        """Validate related records and enforce workflow constraints."""
        attrs = super().validate(attrs)
        case = attrs.get('case', getattr(self.instance, 'case', None))
        stock_item = attrs.get('stock_item', getattr(self.instance, 'stock_item', None))
        quantity = attrs.get('quantity', getattr(self.instance, 'quantity', 1))

        if case and case.state == ServiceCase.State.CLOSED:
            raise serializers.ValidationError({
                'case': _('The service case is closed.')
            })

        if self.instance and self.instance.events.exists():
            immutable = {
                'case': self.instance.case_id,
                'stock_item': self.instance.stock_item_id,
                'quantity': self.instance.quantity,
            }
            if any(
                attrs.get(name, current) != current
                for name, current in immutable.items()
            ):
                raise serializers.ValidationError(
                    _(
                        'Case, stock identity, and quantity cannot change after custody events.'
                    )
                )

        if stock_item and stock_item.serialized and quantity != 1:
            raise serializers.ValidationError({
                'quantity': _('Serialized service items must have quantity one.')
            })
        if stock_item and quantity > stock_item.quantity:
            raise serializers.ValidationError({
                'quantity': _('Service line quantity exceeds the stock item quantity.')
            })

        return attrs


class ServiceCaseEventSerializer(InvenTreeModelSerializer):
    """Append traceable custody and handling events to a service case line."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ServiceCaseEvent
        fields = '__all__'
        read_only_fields = ['created_by', 'request_hash']

    idempotency_key = serializers.UUIDField(required=True, validators=[])

    def validate(self, attrs):
        """Validate related records and enforce workflow constraints."""
        attrs = super().validate(attrs)
        line = attrs.get('line', getattr(self.instance, 'line', None))
        stock_item = attrs.get('stock_item', getattr(self.instance, 'stock_item', None))
        event_type = attrs.get('event_type', getattr(self.instance, 'event_type', None))
        inspection_passed = attrs.get(
            'inspection_passed', getattr(self.instance, 'inspection_passed', None)
        )

        if line and stock_item and stock_item.pk != line.stock_item_id:
            if (
                stock_item.pk != line.replacement_item_id
                and not line.events.filter(stock_item=stock_item).exists()
            ):
                raise serializers.ValidationError({
                    'stock_item': _(
                        'The item must be part of this service line history.'
                    )
                })

        if (
            event_type == ServiceCaseEvent.EventType.INSPECTED
            and inspection_passed is None
        ):
            raise serializers.ValidationError({
                'inspection_passed': _('Record whether the inspection passed.')
            })
        if (
            event_type != ServiceCaseEvent.EventType.INSPECTED
            and inspection_passed is not None
        ):
            raise serializers.ValidationError({
                'inspection_passed': _(
                    'Inspection results are only valid for inspection events.'
                )
            })

        return attrs


class CountSessionSerializer(InvenTreeModelSerializer):
    """Start a physical count at a warehouse location."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = CountSession
        fields = '__all__'
        read_only_fields = [
            'baseline_at',
            'state',
            'started_by',
            'reviewed_by',
            'closed_at',
        ]

    def get_fields(self):
        """Make the count scope immutable after its stock snapshot is created."""
        fields = super().get_fields()
        if self.instance:
            fields['reference'].read_only = True
            fields['location'].read_only = True
        return fields


class CountLineSerializer(InvenTreeModelSerializer):
    """Capture one expected and counted stock quantity."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = CountLine
        fields = '__all__'
        read_only_fields = [
            'session',
            'part',
            'stock_item',
            'expected_quantity',
            'counted_by',
            'counted_at',
            'reviewed',
            'reviewed_by',
            'reviewed_at',
        ]

    def validate(self, attrs):
        """Validate related records and enforce workflow constraints."""
        attrs = super().validate(attrs)
        session = attrs.get('session', getattr(self.instance, 'session', None))
        part = attrs.get('part', getattr(self.instance, 'part', None))
        stock_item = attrs.get('stock_item', getattr(self.instance, 'stock_item', None))

        if session and session.state != CountSession.State.OPEN:
            raise serializers.ValidationError({
                'session': _('Only open count sessions can be changed.')
            })

        if stock_item and part and stock_item.part_id != part.pk:
            raise serializers.ValidationError({
                'part': _('The part must match the stock item.')
            })

        if stock_item and stock_item.serialized:
            quantity = attrs.get('counted_quantity')
            if quantity is not None and quantity not in (0, 1):
                raise serializers.ValidationError({
                    'counted_quantity': _(
                        'Serialized stock must be counted as zero or one.'
                    )
                })

        return attrs


class ShipmentManifestSerializer(InvenTreeModelSerializer):
    """Freeze package contents against one InvenTree shipment."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ShipmentManifest
        fields = '__all__'
        read_only_fields = [
            'contents_snapshot',
            'content_hash',
            'checked_by',
            'checked_at',
            'signed_at',
            'signed_by',
            'receipt_notes',
        ]

    def validate(self, attrs):
        """Freeze shipment/package identity after scans or shipment."""
        attrs = super().validate(attrs)
        if self.instance and (
            self.instance.checked_at
            or self.instance.shipment.shipment_date
            or self.instance.lines.exists()
        ):
            immutable = {
                'shipment': self.instance.shipment_id,
                'package_code': self.instance.package_code,
                'configuration': self.instance.configuration_id,
            }
            if any(
                attrs.get(name, current) != current
                for name, current in immutable.items()
            ):
                raise serializers.ValidationError(
                    _(
                        'Shipment/package identity cannot change after scans or shipping.'
                    )
                )
        return attrs


class ShipmentManifestLineSerializer(InvenTreeModelSerializer):
    """Record actual scanned stock items in a package."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = ShipmentManifestLine
        fields = '__all__'
        read_only_fields = ['scanned_at']


class ShipmentReceiptExceptionSerializer(InvenTreeModelSerializer):
    """Expose a discrepancy follow-up and its resolution record."""

    class Meta:
        """Keep exception evidence read-only outside the resolve action."""

        model = ShipmentReceiptException
        fields = [
            'id',
            'receipt_line',
            'kind',
            'expected_quantity',
            'received_quantity',
            'state',
            'notes',
            'resolution',
            'created_at',
            'resolved_by',
            'resolved_at',
        ]
        read_only_fields = fields


class ShipmentReceiptLineSerializer(InvenTreeModelSerializer):
    """Expose the immutable quantity and condition recorded at receipt."""

    exception = ShipmentReceiptExceptionSerializer(read_only=True)

    class Meta:
        """Keep receipt lines immutable after the receipt event is recorded."""

        model = ShipmentReceiptLine
        fields = [
            'id',
            'receipt',
            'manifest_line',
            'quantity_received',
            'condition',
            'notes',
            'exception',
        ]
        read_only_fields = fields


class ShipmentReceiptSerializer(InvenTreeModelSerializer):
    """Expose partial and final receipt events with line-level evidence."""

    lines = ShipmentReceiptLineSerializer(many=True, read_only=True)

    class Meta:
        """Expose receipt events as immutable audit records."""

        model = ShipmentReceipt
        fields = [
            'id',
            'manifest',
            'idempotency_key',
            'recipient_name',
            'is_final',
            'notes',
            'received_by',
            'received_at',
            'lines',
        ]
        read_only_fields = fields


class ShipmentReceiptLineRequestSerializer(serializers.Serializer):
    """Validate one received quantity against an expected manifest line."""

    manifest_line = serializers.PrimaryKeyRelatedField(
        queryset=ShipmentManifestLine.objects.all()
    )
    quantity_received = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal('0')
    )
    condition = serializers.ChoiceField(
        choices=ShipmentReceiptLine.Condition.choices,
        default=ShipmentReceiptLine.Condition.OK,
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class ShipmentReceiptRequestSerializer(serializers.Serializer):
    """Validate an idempotent partial or final consignee receipt."""

    manifest = serializers.PrimaryKeyRelatedField(
        queryset=ShipmentManifest.objects.all()
    )
    idempotency_key = serializers.UUIDField()
    recipient_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )
    is_final = serializers.BooleanField(default=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = ShipmentReceiptLineRequestSerializer(many=True, required=False)


class ShipmentReceiptExceptionResolveSerializer(serializers.Serializer):
    """Require a human explanation when closing a delivery follow-up."""

    resolution = serializers.CharField(trim_whitespace=True, allow_blank=False)


class ManifestVerificationSerializer(serializers.Serializer):
    """Accept a package verification request."""

    confirm = serializers.BooleanField(default=True)


class CountReviewSerializer(serializers.Serializer):
    """Accept an explicit review for a count discrepancy."""

    note = serializers.CharField(required=False, allow_blank=True)


class DataImportBatchSerializer(serializers.Serializer):
    """Expose source identity and review metadata for import batches."""

    id = serializers.IntegerField(read_only=True)
    source_system = serializers.CharField(max_length=100)
    source_kind = serializers.ChoiceField(choices=DataImportBatch.Kind.choices)
    source_file_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    source_file_digest = serializers.RegexField(regex=r'^[0-9a-fA-F]{64}$')
    inventory_as_of = serializers.DateField(required=False, allow_null=True)
    physical_count_confirmed = serializers.BooleanField(required=False, default=False)
    state = serializers.CharField(read_only=True)
    created_by = serializers.IntegerField(
        read_only=True, allow_null=True, source='created_by_id'
    )
    reviewed_by = serializers.IntegerField(
        read_only=True, allow_null=True, source='reviewed_by_id'
    )
    created_at = serializers.DateTimeField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)
    applied_at = serializers.DateTimeField(read_only=True)

    def validate_source_file_digest(self, value):
        """Normalize digest casing so exact-file retries find the same batch."""
        return value.lower()

    def validate(self, attrs):
        """Keep source identity and review prerequisites fixed after staging."""
        attrs = super().validate(attrs)
        if (
            self.instance
            and attrs
            and self.instance.state != DataImportBatch.State.DRAFT
        ):
            raise serializers.ValidationError(
                _('Batch metadata cannot change after source rows are staged.')
            )
        return attrs

    def create(self, validated_data):
        """Create a batch when used outside the idempotent viewset action."""
        return DataImportBatch.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update editable metadata while the batch remains in draft."""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class DataImportRecordSerializer(InvenTreeModelSerializer):
    """Keep original source cells separate from editable normalized mappings."""

    class Meta:
        """Configure row provenance, mapping, and server-owned result fields."""

        model = DataImportRecord
        fields = '__all__'
        read_only_fields = [
            'state',
            'validation_errors',
            'apply_error',
            'stock_item',
            'created_at',
            'applied_at',
        ]

    def get_fields(self):
        """Keep source-row provenance immutable after its first save."""
        fields = super().get_fields()
        if self.instance:
            for name in [
                'batch',
                'source_sheet',
                'source_row',
                'source_range',
                'source_values',
            ]:
                fields[name].read_only = True
        return fields

    def validate(self, attrs):
        """Allow corrections only before approval or application."""
        attrs = super().validate(attrs)
        batch = attrs.get('batch', getattr(self.instance, 'batch', None))
        if self.instance and batch.state in [
            DataImportBatch.State.APPROVED,
            DataImportBatch.State.APPLIED,
            DataImportBatch.State.REJECTED,
        ]:
            raise serializers.ValidationError(
                _('Rows cannot be changed after batch approval.')
            )
        if 'source_values' in attrs and not isinstance(attrs['source_values'], dict):
            raise serializers.ValidationError({
                'source_values': _('Source values must be a JSON object.')
            })
        if 'normalized_values' in attrs and not isinstance(
            attrs['normalized_values'], dict
        ):
            raise serializers.ValidationError({
                'normalized_values': _('Normalized values must be a JSON object.')
            })
        return attrs


class DataImportStageRowSerializer(serializers.Serializer):
    """Accept source-only rows in one bounded staging request."""

    source_sheet = serializers.CharField(max_length=100)
    source_row = serializers.IntegerField(min_value=1)
    source_range = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    source_values = serializers.DictField()
    normalized_values = serializers.DictField(required=False, default=dict)

    def validate_source_values(self, value):
        """Reject empty rows while preserving original spreadsheet cell values."""
        if not value:
            raise serializers.ValidationError(
                _('A source row must contain at least one value.')
            )
        return value


class OpeningStockMappingSerializer(serializers.Serializer):
    """Require an explicit internal location for staged opening stock."""

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.filter(external=False)
    )


class StateTransitionSerializer(serializers.Serializer):
    """Accept an explicit workflow transition and optional explanation."""

    state = serializers.CharField(max_length=30)
    note = serializers.CharField(required=False, allow_blank=True)


class ServiceResolutionSerializer(serializers.Serializer):
    """Resolve one service line and optionally link a replacement item."""

    outcome = serializers.ChoiceField(
        choices=[
            (value, label)
            for value, label in ServiceCaseLine.Outcome.choices
            if value != ServiceCaseLine.Outcome.PENDING
        ]
    )
    replacement_item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(), required=False, allow_null=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class ComponentReplacementRequestSerializer(serializers.Serializer):
    """Accept the physical replacement of one configured component."""

    replacement_item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all()
    )
    destination_location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all()
    )
    reason = serializers.CharField()
    rework_task = serializers.PrimaryKeyRelatedField(
        queryset=ReworkTask.objects.all(), required=False, allow_null=True
    )


class ComponentRemovalRequestSerializer(serializers.Serializer):
    """Capture the destination, removal class, and operator reason."""

    location = serializers.PrimaryKeyRelatedField(queryset=StockLocation.objects.all())
    reason = serializers.CharField(trim_whitespace=True, allow_blank=False)
    removal_kind = serializers.ChoiceField(
        choices=ConfigurationItem.RemovalKind.choices
    )


class MaterialIssueRequestSerializer(serializers.Serializer):
    """Validate an idempotent issue from stock against a consumable BOM line."""

    build_line = serializers.PrimaryKeyRelatedField(queryset=BuildLine.objects.all())
    stock_item = serializers.PrimaryKeyRelatedField(queryset=StockItem.objects.all())
    quantity = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal('0.00001')
    )
    idempotency_key = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)


class MaterialReturnRequestSerializer(serializers.Serializer):
    """Validate a partial return to an explicitly selected internal location."""

    quantity = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal('0.00001')
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.filter(external=False, structural=False)
    )
    idempotency_key = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)


class MaterialIssueSerializer(serializers.ModelSerializer):
    """Expose issue and cumulative return quantities without duplicating stock."""

    returned_quantity = serializers.SerializerMethodField()
    remaining_quantity = serializers.SerializerMethodField()
    build_reference = serializers.CharField(
        source='build_line.build.reference', read_only=True
    )
    part_name = serializers.CharField(
        source='build_line.bom_item.sub_part.name', read_only=True
    )
    part_code = serializers.CharField(
        source='build_line.bom_item.sub_part.IPN', read_only=True, allow_null=True
    )

    class Meta:
        """Expose immutable issue facts and the cumulative returned quantity."""

        model = MaterialIssue
        fields = [
            'id',
            'build_line',
            'build_reference',
            'part_name',
            'part_code',
            'stock_item',
            'consumed_stock_item',
            'quantity',
            'returned_quantity',
            'remaining_quantity',
            'idempotency_key',
            'notes',
            'created_by',
            'created_at',
        ]
        read_only_fields = fields

    def get_returned_quantity(self, obj) -> Decimal:
        """Sum native return events associated with this material issue."""
        return self._returned_quantity(obj)

    def get_remaining_quantity(self, obj) -> Decimal:
        """Return the issue quantity that has not yet been put back into stock."""
        return max(Decimal('0'), obj.quantity - self._returned_quantity(obj))

    @staticmethod
    def _returned_quantity(obj):
        if 'returns' in getattr(obj, '_prefetched_objects_cache', {}):
            return sum((event.quantity for event in obj.returns.all()), Decimal('0'))
        return obj.returns.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
