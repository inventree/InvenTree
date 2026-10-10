"""REST serializers for the Cangxu industry models."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from InvenTree.serializers import InvenTreeModelSerializer
from stock.models import StockItem, StockLocation

from .models import (
    ComponentReplacement,
    ConfigurationItem,
    ConfigurationTestEvidence,
    CountLine,
    CountSession,
    DataImportBatch,
    DataImportRecord,
    ManufacturingLot,
    ManufacturingLotPartner,
    ManufacturingLotStockItem,
    PartCodeAlias,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseEvent,
    ServiceCaseLine,
    ShipmentManifest,
    ShipmentManifestLine,
    UnitConfiguration,
)


class PartCodeAliasSerializer(InvenTreeModelSerializer):
    """Resolve alternate company and system codes to one canonical Part."""

    class Meta:
        """Configure the fields and write policy for this serializer."""

        model = PartCodeAlias
        fields = '__all__'
        read_only_fields = ['normalized_code', 'company_scope', 'created']


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
        read_only_fields = ['created_by']

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
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    reviewed_by = serializers.PrimaryKeyRelatedField(read_only=True)
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
