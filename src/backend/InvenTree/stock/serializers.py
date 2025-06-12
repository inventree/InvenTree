"""JSON serializers for Stock app."""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import BooleanField, Case, Count, Prefetch, Q, Value, When
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

import structlog
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from sql_util.utils import SubqueryCount, SubquerySum
from taggit.serializers import TagListSerializerField

import build.models
import company.models
import company.serializers as company_serializers
import InvenTree.helpers
import InvenTree.serializers
import order.models
import part.filters as part_filters
import part.models as part_models
import part.serializers as part_serializers
import stock.filters
import stock.status_codes
from common.settings import get_global_setting
from generic.states.fields import InvenTreeCustomStatusSerializerMixin
from importer.registry import register_importer
from InvenTree.mixins import DataImportExportSerializerMixin
from InvenTree.ready import isGeneratingSchema
from InvenTree.serializers import (
    InvenTreeCurrencySerializer,
    InvenTreeDecimalField,
    InvenTreeModelSerializer,
)
from users.serializers import UserSerializer

from .models import (
    StockItem,
    StockItemTestResult,
    StockItemTracking,
    StockLocation,
    StockLocationType,
)

logger = structlog.get_logger('inventree')


class GenerateBatchCodeSerializer(serializers.Serializer):
    """Serializer for generating a batch code.

    Any of the provided write-only fields can be used for additional context.
    """

    class Meta:
        """Metaclass options."""

        fields = [
            'batch_code',
            'build_order',
            'item',
            'location',
            'part',
            'purchase_order',
            'quantity',
        ]

        read_only_fields = ['batch_code']

        write_only_fields = [
            'build_order',
            'item',
            'location',
            'part',
            'purchase_order',
            'quantity',
        ]

    batch_code = serializers.CharField(
        read_only=True, help_text=_('Generated batch code'), label=_('Batch Code')
    )

    build_order = serializers.PrimaryKeyRelatedField(
        queryset=build.models.Build.objects.all(),
        many=False,
        required=False,
        allow_null=True,
        label=_('Build Order'),
        help_text=_('Select build order'),
    )

    item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        required=False,
        allow_null=True,
        label=_('Stock Item'),
        help_text=_('Select stock item to generate batch code for'),
    )

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=False,
        allow_null=True,
        label=_('Location'),
        help_text=_('Select location to generate batch code for'),
    )

    part = serializers.PrimaryKeyRelatedField(
        queryset=part_models.Part.objects.all(),
        many=False,
        required=False,
        allow_null=True,
        label=_('Part'),
        help_text=_('Select part to generate batch code for'),
    )

    purchase_order = serializers.PrimaryKeyRelatedField(
        queryset=order.models.PurchaseOrder.objects.all(),
        many=False,
        required=False,
        allow_null=True,
        label=_('Purchase Order'),
        help_text=_('Select purchase order'),
    )

    quantity = serializers.FloatField(
        required=False,
        allow_null=True,
        label=_('Quantity'),
        help_text=_('Enter quantity for batch code'),
    )


class GenerateSerialNumberSerializer(serializers.Serializer):
    """Serializer for generating one or multiple serial numbers.

    Any of the provided write-only fields can be used for additional context.

    Note that in the case where multiple serial numbers are required,
    the "serial_number" field will return a string with multiple serial numbers
    separated by a comma.
    """

    class Meta:
        """Metaclass options."""

        fields = ['serial_number', 'part', 'quantity']

        read_only_fields = ['serial_number']

        write_only_fields = ['part', 'quantity']

    serial_number = serializers.CharField(
        read_only=True,
        allow_null=True,
        help_text=_('Generated serial number'),
        label=_('Serial Number'),
    )

    part = serializers.PrimaryKeyRelatedField(
        queryset=part_models.Part.objects.all(),
        many=False,
        required=False,
        allow_null=True,
        label=_('Part'),
        help_text=_('Select part to generate serial number for'),
    )

    quantity = serializers.IntegerField(
        required=False,
        allow_null=False,
        default=1,
        label=_('Quantity'),
        help_text=_('Quantity of serial numbers to generate'),
    )


class LocationBriefSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Provides a brief serializer for a StockLocation object."""

    class Meta:
        """Metaclass options."""

        model = StockLocation
        fields = ['pk', 'name', 'pathstring']


@register_importer()
class StockItemTestResultSerializer(
    DataImportExportSerializerMixin, InvenTree.serializers.InvenTreeModelSerializer
):
    """Serializer for the StockItemTestResult model."""

    class Meta:
        """Metaclass options."""

        model = StockItemTestResult

        fields = [
            'pk',
            'stock_item',
            'result',
            'value',
            'attachment',
            'notes',
            'test_station',
            'started_datetime',
            'finished_datetime',
            'user',
            'user_detail',
            'date',
            'template',
            'template_detail',
        ]

        read_only_fields = ['pk', 'user', 'date']

    def __init__(self, *args, **kwargs):
        """Add detail fields."""
        user_detail = kwargs.pop('user_detail', False)
        template_detail = kwargs.pop('template_detail', False)

        super().__init__(*args, **kwargs)

        if isGeneratingSchema():
            return

        if user_detail is not True:
            self.fields.pop('user_detail', None)

        if template_detail is not True:
            self.fields.pop('template_detail', None)

    user_detail = UserSerializer(source='user', read_only=True, allow_null=True)

    template = serializers.PrimaryKeyRelatedField(
        queryset=part_models.PartTestTemplate.objects.all(),
        many=False,
        required=False,
        allow_null=True,
        help_text=_('Template'),
        label=_('Test template for this result'),
    )

    template_detail = part_serializers.PartTestTemplateSerializer(
        source='template', read_only=True, allow_null=True
    )

    attachment = InvenTree.serializers.InvenTreeAttachmentSerializerField(
        required=False,
        allow_null=True,
        label=_('Attachment'),
        help_text=_('Test result attachment'),
    )

    def validate(self, data):
        """Validate the test result data."""
        stock_item = data['stock_item']
        template = data.get('template', None)

        # To support legacy API, we can accept a test name instead of a template
        # In such a case, we use the test name to lookup the appropriate template
        test_name = self.context['request'].data.get('test', None)

        if not template and not test_name:
            raise ValidationError(_('Template ID or test name must be provided'))

        if not template:
            test_key = InvenTree.helpers.generateTestKey(test_name)

            ancestors = stock_item.part.get_ancestors(include_self=True)

            # Find a template based on name
            if template := part_models.PartTestTemplate.objects.filter(
                part__tree_id=stock_item.part.tree_id, part__in=ancestors, key=test_key
            ).first():
                data['template'] = template

            elif get_global_setting('TEST_UPLOAD_CREATE_TEMPLATE', False):
                logger.debug(
                    "No matching test template found for '%s' - creating a new template",
                    test_name,
                )

                # Create a new test template based on the provided data
                data['template'] = part_models.PartTestTemplate.objects.create(
                    part=stock_item.part, test_name=test_name
                )

        data = super().validate(data)

        started = data.get('started_datetime')
        finished = data.get('finished_datetime')

        if started is not None and finished is not None and started > finished:
            raise ValidationError({
                'finished_datetime': _(
                    'The test finished time cannot be earlier than the test started time'
                )
            })
        return data


class StockItemSerializerBrief(
    InvenTree.serializers.NotesFieldMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Brief serializers for a StockItem."""

    class Meta:
        """Metaclass options."""

        model = StockItem
        fields = [
            'part',
            'part_name',
            'pk',
            'location',
            'quantity',
            'serial',
            'batch',
            'supplier_part',
            'barcode_hash',
        ]

        read_only_fields = ['barcode_hash']

    part_name = serializers.CharField(source='part.full_name', read_only=True)

    quantity = InvenTreeDecimalField()

    def validate_serial(self, value):
        """Make sure serial is not to big."""
        if abs(InvenTree.helpers.extract_int(value)) > 0x7FFFFFFF:
            raise serializers.ValidationError(_('Serial number is too large'))
        return value


@register_importer()
class StockItemSerializer(
    DataImportExportSerializerMixin,
    InvenTreeCustomStatusSerializerMixin,
    InvenTree.serializers.InvenTreeTagModelSerializer,
):
    """Serializer for a StockItem.

    - Includes serialization for the linked part
    - Includes serialization for the item location
    """

    export_exclude_fields = ['tags', 'tracking_items']

    export_child_fields = [
        'part_detail.name',
        'part_detail.description',
        'part_detail.IPN',
        'part_detail.revision',
        'part_detail.pricing_min',
        'part_detail.pricing_max',
        'location_detail.name',
        'location_detail.pathstring',
        'supplier_part_detail.SKU',
        'supplier_part_detail.MPN',
    ]

    import_exclude_fields = ['use_pack_size', 'location_path']

    class Meta:
        """Metaclass options."""

        model = StockItem
        fields = [
            'pk',
            'part',
            'quantity',
            'serial',
            'batch',
            'location',
            'belongs_to',
            'build',
            'consumed_by',
            'customer',
            'delete_on_deplete',
            'expiry_date',
            'in_stock',
            'is_building',
            'link',
            'notes',
            'owner',
            'packaging',
            'parent',
            'purchase_order',
            'purchase_order_reference',
            'sales_order',
            'sales_order_reference',
            'status',
            'status_text',
            'status_custom_key',
            'supplier_part',
            'SKU',
            'MPN',
            'barcode_hash',
            'updated',
            'stocktake_date',
            'purchase_price',
            'purchase_price_currency',
            'use_pack_size',
            'tests',
            # Annotated fields
            'allocated',
            'expired',
            'installed_items',
            'child_items',
            'location_path',
            'stale',
            'tracking_items',
            'tags',
            # Detail fields (FK relationships)
            'supplier_part_detail',
            'part_detail',
            'location_detail',
        ]

        """
        These fields are read-only in this context.
        They can be updated by accessing the appropriate API endpoints
        """
        read_only_fields = [
            'allocated',
            'barcode_hash',
            'stocktake_date',
            'stocktake_user',
            'updated',
        ]

        """
        Fields used when creating a stock item
        """
        extra_kwargs = {'use_pack_size': {'write_only': True}}

    def __init__(self, *args, **kwargs):
        """Add detail fields."""
        part_detail = kwargs.pop('part_detail', True)
        location_detail = kwargs.pop('location_detail', True)
        supplier_part_detail = kwargs.pop('supplier_part_detail', True)
        path_detail = kwargs.pop('path_detail', False)

        tests = kwargs.pop('tests', False)

        super().__init__(*args, **kwargs)

        if isGeneratingSchema():
            return

        if not part_detail:
            self.fields.pop('part_detail', None)

        if not location_detail:
            self.fields.pop('location_detail', None)

        if not supplier_part_detail:
            self.fields.pop('supplier_part_detail', None)

        if not tests:
            self.fields.pop('tests', None)

        if not path_detail:
            self.fields.pop('location_path', None)

    part = serializers.PrimaryKeyRelatedField(
        queryset=part_models.Part.objects.all(),
        many=False,
        allow_null=False,
        help_text=_('Base Part'),
        label=_('Part'),
    )

    parent = serializers.PrimaryKeyRelatedField(
        many=False,
        read_only=True,
        label=_('Parent Item'),
        help_text=_('Parent stock item'),
    )

    location_path = serializers.ListField(
        child=serializers.DictField(),
        source='location.get_path',
        read_only=True,
        allow_null=True,
    )

    in_stock = serializers.BooleanField(read_only=True, label=_('In Stock'))

    """
    Field used when creating a stock item
    """
    use_pack_size = serializers.BooleanField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text=_(
            'Use pack size when adding: the quantity defined is the number of packs'
        ),
        label=('Use pack size'),
    )

    def validate_part(self, part):
        """Ensure the provided Part instance is valid."""
        if part.virtual:
            raise ValidationError(_('Stock item cannot be created for virtual parts'))

        return part

    def update(self, instance, validated_data):
        """Custom update method to pass the user information through to the instance."""
        instance._user = self.context['user']

        return super().update(instance, validated_data)

    @staticmethod
    def annotate_queryset(queryset):
        """Add some extra annotations to the queryset, performing database queries as efficiently as possible."""
        queryset = queryset.prefetch_related(
            'location',
            'allocations',
            'sales_order',
            'sales_order_allocations',
            'purchase_order',
            Prefetch(
                'part',
                queryset=part_models.Part.objects.annotate(
                    category_default_location=part_filters.annotate_default_location(
                        'category__'
                    )
                ).prefetch_related(None),
            ),
            'parent',
            'part__category',
            'part__supplier_parts',
            'part__supplier_parts__purchase_order_line_items',
            'part__pricing_data',
            'part__tags',
            'supplier_part',
            'supplier_part__part',
            'supplier_part__supplier',
            'supplier_part__manufacturer_part',
            'supplier_part__manufacturer_part__manufacturer',
            'supplier_part__manufacturer_part__tags',
            'supplier_part__purchase_order_line_items',
            'supplier_part__tags',
            'test_results',
            'customer',
            'belongs_to',
            'sales_order',
            'consumed_by',
            'tags',
        )

        # Annotate the queryset with the total allocated to sales orders
        queryset = queryset.annotate(
            allocated=Coalesce(
                SubquerySum('sales_order_allocations__quantity'), Decimal(0)
            )
            + Coalesce(SubquerySum('allocations__quantity'), Decimal(0))
        )

        # Annotate the queryset with the number of tracking items
        queryset = queryset.annotate(tracking_items=SubqueryCount('tracking_info'))

        # Add flag to indicate if the StockItem has expired
        queryset = queryset.annotate(
            expired=Case(
                When(
                    StockItem.EXPIRED_FILTER,
                    then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        # Add flag to indicate if the StockItem is stale
        stale_days = get_global_setting('STOCK_STALE_DAYS')
        stale_date = InvenTree.helpers.current_date() + timedelta(days=stale_days)
        stale_filter = (
            StockItem.IN_STOCK_FILTER
            & ~Q(expiry_date=None)
            & Q(expiry_date__lt=stale_date)
        )

        queryset = queryset.annotate(
            stale=Case(
                When(stale_filter, then=Value(True, output_field=BooleanField())),
                default=Value(False, output_field=BooleanField()),
            )
        )

        # Annotate with the total number of "installed items"
        queryset = queryset.annotate(installed_items=SubqueryCount('installed_parts'))

        # Annotate with the total number of "child items" (split stock items)
        queryset = queryset.annotate(child_items=stock.filters.annotate_child_items())

        return queryset

    status_text = serializers.CharField(
        source='get_status_display', read_only=True, label=_('Status')
    )

    SKU = serializers.CharField(
        source='supplier_part.SKU',
        read_only=True,
        label=_('Supplier Part Number'),
        allow_null=True,
    )

    MPN = serializers.CharField(
        source='supplier_part.manufacturer_part.MPN',
        read_only=True,
        label=_('Manufacturer Part Number'),
        allow_null=True,
    )

    # Optional detail fields, which can be appended via query parameters
    supplier_part_detail = company_serializers.SupplierPartSerializer(
        label=_('Supplier Part'),
        source='supplier_part',
        brief=True,
        supplier_detail=False,
        manufacturer_detail=False,
        part_detail=False,
        many=False,
        read_only=True,
        allow_null=True,
    )

    part_detail = part_serializers.PartBriefSerializer(
        label=_('Part'), source='part', many=False, read_only=True, allow_null=True
    )

    location_detail = LocationBriefSerializer(
        label=_('Location'),
        source='location',
        many=False,
        read_only=True,
        allow_null=True,
    )

    tests = StockItemTestResultSerializer(
        source='test_results', many=True, read_only=True, allow_null=True
    )

    quantity = InvenTreeDecimalField()

    # Annotated fields
    allocated = serializers.FloatField(
        read_only=True, allow_null=True, label=_('Allocated Quantity')
    )
    expired = serializers.BooleanField(
        read_only=True, allow_null=True, label=_('Expired')
    )
    installed_items = serializers.IntegerField(
        read_only=True, allow_null=True, label=_('Installed Items')
    )
    child_items = serializers.IntegerField(
        read_only=True, allow_null=True, label=_('Child Items')
    )
    stale = serializers.BooleanField(read_only=True, allow_null=True, label=_('Stale'))
    tracking_items = serializers.IntegerField(
        read_only=True, allow_null=True, label=_('Tracking Items')
    )

    purchase_price = InvenTree.serializers.InvenTreeMoneySerializer(
        label=_('Purchase Price'),
        allow_null=True,
        help_text=_('Purchase price of this stock item, per unit or pack'),
    )

    purchase_price_currency = InvenTreeCurrencySerializer(
        help_text=_('Purchase currency of this stock item')
    )

    purchase_order_reference = serializers.CharField(
        source='purchase_order.reference', read_only=True, allow_null=True
    )

    sales_order_reference = serializers.CharField(
        source='sales_order.reference', read_only=True, allow_null=True
    )

    tags = TagListSerializerField(required=False)


class SerializeStockItemSerializer(serializers.Serializer):
    """A DRF serializer for "serializing" a StockItem.

    (Sorry for the confusing naming...)

    Here, "serializing" means splitting out a single StockItem,
    into multiple single-quantity items with an assigned serial number

    Note: The base StockItem object is provided to the serializer context
    """

    class Meta:
        """Metaclass options."""

        fields = ['quantity', 'serial_numbers', 'destination', 'notes']

    quantity = serializers.IntegerField(
        min_value=0,
        required=True,
        label=_('Quantity'),
        help_text=_('Enter number of stock items to serialize'),
    )

    def validate_quantity(self, quantity):
        """Validate that the quantity value is correct."""
        item = self.context['item']

        if quantity < 0:
            raise ValidationError(_('Quantity must be greater than zero'))

        if quantity > item.quantity:
            q = item.quantity
            raise ValidationError(
                _(f'Quantity must not exceed available stock quantity ({q})')
            )

        return quantity

    serial_numbers = serializers.CharField(
        label=_('Serial Numbers'),
        help_text=_('Enter serial numbers for new items'),
        allow_blank=False,
        required=True,
    )

    destination = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Location'),
        help_text=_('Destination stock location'),
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Notes'),
        help_text=_('Optional note field'),
    )

    def validate(self, data):
        """Check that the supplied serial numbers are valid."""
        data = super().validate(data)

        item = self.context['item']

        if not item.part.trackable:
            raise ValidationError(_('Serial numbers cannot be assigned to this part'))

        # Ensure the serial numbers are valid!
        quantity = data['quantity']
        serial_numbers = data['serial_numbers']

        try:
            serials = InvenTree.helpers.extract_serial_numbers(
                serial_numbers,
                quantity,
                item.part.get_latest_serial_number(),
                part=item.part,
            )
        except DjangoValidationError as e:
            raise ValidationError({'serial_numbers': e.messages})

        existing = item.part.find_conflicting_serial_numbers(serials)

        if len(existing) > 0:
            exists = ','.join([str(x) for x in existing])
            error = _('Serial numbers already exist') + ': ' + exists

            raise ValidationError({'serial_numbers': error})

        return data

    def save(self):
        """Serialize stock item."""
        item = self.context['item']
        request = self.context.get('request')
        user = request.user if request else None

        data = self.validated_data

        serials = InvenTree.helpers.extract_serial_numbers(
            data['serial_numbers'],
            data['quantity'],
            item.part.get_latest_serial_number(),
            part=item.part,
        )

        item.serializeStock(
            data['quantity'],
            serials,
            user,
            notes=data.get('notes', ''),
            location=data['destination'],
        )


class InstallStockItemSerializer(serializers.Serializer):
    """Serializer for installing a stock item into a given part."""

    stock_item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Stock Item'),
        help_text=_('Select stock item to install'),
    )

    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
        required=False,
        label=_('Quantity to Install'),
        help_text=_('Enter the quantity of items to install'),
    )

    note = serializers.CharField(
        label=_('Note'),
        help_text=_('Add transaction note (optional)'),
        required=False,
        allow_blank=True,
    )

    def validate_quantity(self, quantity):
        """Validate the quantity value."""
        if quantity < 1:
            raise ValidationError(_('Quantity to install must be at least 1'))

        return quantity

    def validate_stock_item(self, stock_item):
        """Validate the selected stock item."""
        if not stock_item.in_stock:
            # StockItem must be in stock to be "installed"
            raise ValidationError(_('Stock item is unavailable'))

        parent_item = self.context['item']
        parent_part = parent_item.part

        if get_global_setting(
            'STOCK_ENFORCE_BOM_INSTALLATION', backup_value=True, cache=False
        ):
            # Check if the selected part is in the Bill of Materials of the parent item
            if not parent_part.check_if_part_in_bom(stock_item.part):
                raise ValidationError(
                    _('Selected part is not in the Bill of Materials')
                )

        return stock_item

    def validate(self, data):
        """Ensure that the provided dataset is valid."""
        stock_item = data['stock_item']

        quantity = data.get('quantity', stock_item.quantity)

        if quantity > stock_item.quantity:
            raise ValidationError({
                'quantity': _('Quantity to install must not exceed available quantity')
            })

        return data

    def save(self):
        """Install the selected stock item into this one."""
        data = self.validated_data

        stock_item = data['stock_item']
        quantity_to_install = data.get('quantity', stock_item.quantity)
        note = data.get('note', '')

        parent_item = self.context['item']
        request = self.context['request']

        parent_item.installStockItem(
            stock_item, quantity_to_install, request.user, note
        )


class UninstallStockItemSerializer(serializers.Serializer):
    """API serializers for uninstalling an installed item from a stock item."""

    class Meta:
        """Metaclass options."""

        fields = ['location', 'note']

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Location'),
        help_text=_('Destination location for uninstalled item'),
    )

    note = serializers.CharField(
        label=_('Notes'),
        help_text=_('Add transaction note (optional)'),
        required=False,
        allow_blank=True,
    )

    def save(self):
        """Uninstall stock item."""
        item = self.context['item']

        data = self.validated_data
        request = self.context['request']

        location = data['location']

        note = data.get('note', '')

        item.uninstall_into_location(location, request.user, note)


class ConvertStockItemSerializer(serializers.Serializer):
    """DRF serializer class for converting a StockItem to a valid variant part."""

    class Meta:
        """Metaclass options."""

        fields = ['part']

    part = serializers.PrimaryKeyRelatedField(
        queryset=part_models.Part.objects.all(),
        label=_('Part'),
        help_text=_('Select part to convert stock item into'),
        many=False,
        required=True,
        allow_null=False,
    )

    def validate_part(self, part):
        """Ensure that the provided part is a valid option for the stock item."""
        stock_item = self.context['item']
        valid_options = stock_item.part.get_conversion_options()

        if part not in valid_options:
            raise ValidationError(
                _('Selected part is not a valid option for conversion')
            )

        return part

    def validate(self, data):
        """Ensure that the stock item is valid for conversion.

        Rules:
        - If a SupplierPart is assigned, we cannot convert!
        """
        data = super().validate(data)

        stock_item = self.context['item']

        if stock_item.supplier_part is not None:
            raise ValidationError(
                _('Cannot convert stock item with assigned SupplierPart')
            )

        return data

    def save(self):
        """Save the serializer to convert the StockItem to the selected Part."""
        data = self.validated_data

        part = data['part']

        stock_item = self.context['item']
        request = self.context['request']

        stock_item.convert_to_variant(part, request.user)


@extend_schema_field(
    serializers.IntegerField(
        help_text='Status key, chosen from the list of StockStatus keys'
    )
)
class StockStatusCustomSerializer(serializers.ChoiceField):
    """Serializer to allow annotating the schema to use int where custom values may be entered."""

    def __init__(self, *args, **kwargs):
        """Initialize the status selector."""
        if 'choices' not in kwargs:
            kwargs['choices'] = stock.status_codes.StockStatus.items(custom=True)

        if 'label' not in kwargs:
            kwargs['label'] = _('Status')

        if 'help_text' not in kwargs:
            kwargs['help_text'] = _('Stock item status code')

        if InvenTree.ready.isGeneratingSchema():
            kwargs['help_text'] = (
                kwargs['help_text']
                + '\n\n'
                + '\n'.join(
                    f'* `{value}` - {label}' for value, label in kwargs['choices']
                )
                + "\n\nAdditional custom status keys may be retrieved from the 'stock_status_retrieve' call."
            )

        super().__init__(*args, **kwargs)


class ReturnStockItemSerializer(serializers.Serializer):
    """DRF serializer for returning a stock item from a customer."""

    class Meta:
        """Metaclass options."""

        fields = ['location', 'status', 'notes']

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Location'),
        help_text=_('Destination location for returned item'),
    )

    status = StockStatusCustomSerializer(default=None, required=False, allow_blank=True)

    notes = serializers.CharField(
        label=_('Notes'),
        help_text=_('Add transaction note (optional)'),
        required=False,
        allow_blank=True,
    )

    def save(self):
        """Save the serializer to return the item into stock."""
        item = self.context['item']
        request = self.context['request']

        data = self.validated_data

        location = data['location']

        item.return_from_customer(
            location,
            user=request.user,
            notes=data.get('notes', ''),
            status=data.get('status', None),
        )


class StockChangeStatusSerializer(serializers.Serializer):
    """Serializer for changing status of multiple StockItem objects."""

    class Meta:
        """Metaclass options."""

        fields = ['items', 'status', 'note']

    items = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=True,
        required=True,
        allow_null=False,
        label=_('Stock Items'),
        help_text=_('Select stock items to change status'),
    )

    def validate_items(self, items):
        """Validate the selected stock items."""
        if len(items) == 0:
            raise ValidationError(_('No stock items selected'))

        return items

    status = StockStatusCustomSerializer(
        default=stock.status_codes.StockStatus.OK.value
    )

    note = serializers.CharField(
        label=_('Notes'),
        help_text=_('Add transaction note (optional)'),
        required=False,
        allow_blank=True,
    )

    @transaction.atomic
    def save(self):
        """Save the serializer to change the status of the selected stock items."""
        data = self.validated_data

        items = data['items']
        status = data['status']

        request = self.context['request']
        user = getattr(request, 'user', None)

        note = data.get('note', '')

        items_to_update = []
        transaction_notes = []

        deltas = {'status': status}

        now = InvenTree.helpers.current_time()

        # Instead of performing database updates for each item,
        # perform bulk database updates (much more efficient)

        for item in items:
            # Ignore items which are already in the desired status
            if item.status == status:
                continue

            item.updated = now
            item.status = status
            items_to_update.append(item)

            # Create a new transaction note for each item
            transaction_notes.append(
                StockItemTracking(
                    item=item,
                    tracking_type=stock.status_codes.StockHistoryCode.EDITED.value,
                    date=now,
                    deltas=deltas,
                    user=user,
                    notes=note,
                )
            )

        # Update status
        StockItem.objects.bulk_update(items_to_update, ['status', 'updated'])

        # Create entries
        StockItemTracking.objects.bulk_create(transaction_notes)


class StockLocationTypeSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for StockLocationType model."""

    class Meta:
        """Serializer metaclass."""

        model = StockLocationType
        fields = ['pk', 'name', 'description', 'icon', 'location_count']

        read_only_fields = ['location_count']

    location_count = serializers.IntegerField(read_only=True, allow_null=True)

    @staticmethod
    def annotate_queryset(queryset):
        """Add location count to each location type."""
        return queryset.annotate(location_count=Count('stock_locations'))


class LocationTreeSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for a simple tree view."""

    class Meta:
        """Metaclass options."""

        model = StockLocation
        fields = ['pk', 'name', 'parent', 'icon', 'structural', 'sublocations']

    sublocations = serializers.IntegerField(label=_('Sublocations'), read_only=True)

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the queryset with the number of sublocations."""
        return queryset.annotate(sublocations=stock.filters.annotate_sub_locations())


@register_importer()
class LocationSerializer(
    DataImportExportSerializerMixin, InvenTree.serializers.InvenTreeTagModelSerializer
):
    """Detailed information about a stock location."""

    import_exclude_fields = []

    class Meta:
        """Metaclass options."""

        model = StockLocation
        fields = [
            'pk',
            'barcode_hash',
            'name',
            'level',
            'description',
            'parent',
            'pathstring',
            'path',
            'items',
            'sublocations',
            'owner',
            'icon',
            'custom_icon',
            'structural',
            'external',
            'location_type',
            'location_type_detail',
            'tags',
        ]

        read_only_fields = ['barcode_hash', 'icon', 'level', 'pathstring']

    def __init__(self, *args, **kwargs):
        """Optionally add or remove extra fields."""
        path_detail = kwargs.pop('path_detail', False)

        super().__init__(*args, **kwargs)

        if not path_detail and not isGeneratingSchema():
            self.fields.pop('path', None)

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate extra information to the queryset."""
        # Annotate the number of stock items which exist in this category (including subcategories)

        queryset = queryset.prefetch_related('tags')

        queryset = queryset.annotate(
            items=stock.filters.annotate_location_items(),
            sublocations=stock.filters.annotate_sub_locations(),
        )

        return queryset

    parent = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        allow_null=True,
        required=False,
        label=_('Parent Location'),
        help_text=_('Parent stock location'),
    )

    items = serializers.IntegerField(read_only=True, label=_('Stock Items'))

    sublocations = serializers.IntegerField(read_only=True, label=_('Sublocations'))

    level = serializers.IntegerField(read_only=True)

    tags = TagListSerializerField(required=False)

    path = serializers.ListField(
        child=serializers.DictField(),
        source='get_path',
        read_only=True,
        allow_null=True,
    )

    # explicitly set this field, so it gets included for AutoSchema
    icon = serializers.CharField(read_only=True)

    # Detail for location type
    location_type_detail = StockLocationTypeSerializer(
        source='location_type', read_only=True, allow_null=True, many=False
    )


@register_importer()
class StockTrackingSerializer(
    DataImportExportSerializerMixin, InvenTree.serializers.InvenTreeModelSerializer
):
    """Serializer for StockItemTracking model."""

    class Meta:
        """Metaclass options."""

        model = StockItemTracking
        fields = [
            'pk',
            'item',
            'item_detail',
            'date',
            'deltas',
            'label',
            'notes',
            'tracking_type',
            'user',
            'user_detail',
        ]

        read_only_fields = ['date', 'user', 'label', 'tracking_type']

    def __init__(self, *args, **kwargs):
        """Add detail fields."""
        item_detail = kwargs.pop('item_detail', False)
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if isGeneratingSchema():
            return

        if item_detail is not True:
            self.fields.pop('item_detail', None)

        if user_detail is not True:
            self.fields.pop('user_detail', None)

    label = serializers.CharField(read_only=True)

    item_detail = StockItemSerializerBrief(
        source='item', many=False, read_only=True, allow_null=True
    )

    user_detail = UserSerializer(
        source='user', many=False, read_only=True, allow_null=True
    )

    deltas = serializers.JSONField(read_only=True)


class StockAssignmentItemSerializer(serializers.Serializer):
    """Serializer for a single StockItem with in StockAssignment request.

    Here, the particular StockItem is being assigned (manually) to a customer

    Fields:
        - item: StockItem object
    """

    class Meta:
        """Metaclass options."""

        fields = ['item']

    item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    def validate_item(self, item):
        """Validate item.

        Ensures:
        - is in stock
        - Is salable
        - Is not allocated
        """
        # The item must currently be "in stock"
        if not item.in_stock:
            raise ValidationError(_('Item must be in stock'))

        # The base part must be "salable"
        if not item.part.salable:
            raise ValidationError(_('Part must be salable'))

        # The item must not be allocated to a sales order
        if item.sales_order_allocations.count() > 0:
            raise ValidationError(_('Item is allocated to a sales order'))

        # The item must not be allocated to a build order
        if item.allocations.count() > 0:
            raise ValidationError(_('Item is allocated to a build order'))

        return item


class StockAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning one (or more) stock items to a customer.

    This is a manual assignment process, separate for (for example) a Sales Order
    """

    class Meta:
        """Metaclass options."""

        fields = ['items', 'customer', 'notes']

    items = StockAssignmentItemSerializer(many=True, required=True)

    customer = serializers.PrimaryKeyRelatedField(
        queryset=company.models.Company.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Customer'),
        help_text=_('Customer to assign stock items'),
    )

    def validate_customer(self, customer):
        """Make sure provided company is customer."""
        if customer and not customer.is_customer:
            raise ValidationError(_('Selected company is not a customer'))

        return customer

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Notes'),
        help_text=_('Stock assignment notes'),
    )

    def validate(self, data):
        """Make sure items were provided."""
        data = super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('A list of stock items must be provided'))

        return data

    def save(self):
        """Assign stock."""
        request = self.context['request']

        user = getattr(request, 'user', None)

        data = self.validated_data

        items = data['items']
        customer = data['customer']
        notes = data.get('notes', '')

        with transaction.atomic():
            for item in items:
                stock_item = item['item']

                stock_item.allocateToCustomer(customer, user=user, notes=notes)


class StockMergeItemSerializer(serializers.Serializer):
    """Serializer for a single StockItem within the StockMergeSerializer class.

    Here, the individual StockItem is being checked for merge compatibility.
    """

    class Meta:
        """Metaclass options."""

        fields = ['item']

    item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    def validate_item(self, item):
        """Make sure item can be merged."""
        # Check that the stock item is able to be merged
        item.can_merge(raise_error=True)

        return item


class StockMergeSerializer(serializers.Serializer):
    """Serializer for merging two (or more) stock items together."""

    class Meta:
        """Metaclass options."""

        fields = [
            'items',
            'location',
            'notes',
            'allow_mismatched_suppliers',
            'allow_mismatched_status',
        ]

    items = StockMergeItemSerializer(many=True, required=True)

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Location'),
        help_text=_('Destination stock location'),
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Notes'),
        help_text=_('Stock merging notes'),
    )

    allow_mismatched_suppliers = serializers.BooleanField(
        required=False,
        label=_('Allow mismatched suppliers'),
        help_text=_('Allow stock items with different supplier parts to be merged'),
    )

    allow_mismatched_status = serializers.BooleanField(
        required=False,
        label=_('Allow mismatched status'),
        help_text=_('Allow stock items with different status codes to be merged'),
    )

    def validate(self, data):
        """Make sure all needed values are provided and that the items can be merged."""
        data = super().validate(data)

        items = data['items']

        if len(items) < 2:
            raise ValidationError(_('At least two stock items must be provided'))

        unique_items = set()

        # The "base item" is the first item
        base_item = items[0]['item']

        data['base_item'] = base_item

        # Ensure stock items are unique!
        for element in items:
            item = element['item']

            if item.pk in unique_items:
                raise ValidationError(_('Duplicate stock items'))

            unique_items.add(item.pk)

            # Checks from here refer to the "base_item"
            if item == base_item:
                continue

            # Check that this item can be merged with the base_item
            item.can_merge(
                raise_error=True,
                other=base_item,
                allow_mismatched_suppliers=data.get(
                    'allow_mismatched_suppliers', False
                ),
                allow_mismatched_status=data.get('allow_mismatched_status', False),
            )

        return data

    def save(self):
        """Actually perform the stock merging action.

        At this point we are confident that the merge can take place
        """
        data = self.validated_data

        base_item = data['base_item']
        items = data['items'][1:]

        request = self.context['request']
        user = getattr(request, 'user', None)

        items = []

        for item in data['items'][1:]:
            items.append(item['item'])

        base_item.merge_stock_items(
            items,
            allow_mismatched_suppliers=data.get('allow_mismatched_suppliers', False),
            allow_mismatched_status=data.get('allow_mismatched_status', False),
            user=user,
            location=data['location'],
            notes=data.get('notes', None),
        )


def stock_item_adjust_status_options():
    """Return a custom set of options for the StockItem status adjustment field.

    In particular, include a Null option for the status field.
    """
    return [(None, _('No Change')), *stock.status_codes.StockStatus.items(custom=True)]


class StockAdjustmentItemSerializer(serializers.Serializer):
    """Serializer for a single StockItem within a stock adjustment request.

    Required Fields:
        - item: StockItem object
        - quantity: Numerical quantity

    Optional Fields (may be used by external tools)
        - status: Change StockItem status code
        - packaging: Change StockItem packaging
        - batch: Change StockItem batch code

    The optional fields can be used to adjust values for individual stock items
    """

    class Meta:
        """Metaclass options."""

        fields = ['pk', 'quantity', 'batch', 'status', 'packaging']

    pk = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label='stock_item',
        help_text=_('StockItem primary key value'),
    )

    def validate_pk(self, stock_item: StockItem) -> StockItem:
        """Ensure the stock item is valid."""
        allow_out_of_stock_transfer = get_global_setting(
            'STOCK_ALLOW_OUT_OF_STOCK_TRANSFER', backup_value=False, cache=False
        )

        if not allow_out_of_stock_transfer and not stock_item.is_in_stock(
            check_status=False, check_quantity=False
        ):
            raise ValidationError(_('Stock item is not in stock'))

        return stock_item

    quantity = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal(0), required=True
    )

    batch = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        label=_('Batch Code'),
        help_text=_('Batch code for this stock item'),
    )

    status = StockStatusCustomSerializer(
        choices=stock_item_adjust_status_options(),
        default=None,
        required=False,
        allow_blank=True,
    )

    packaging = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        label=_('Packaging'),
        help_text=_('Packaging this stock item is stored in'),
    )


class StockAdjustmentSerializer(serializers.Serializer):
    """Base class for managing stock adjustment actions via the API."""

    class Meta:
        """Metaclass options."""

        fields = ['items', 'notes']

    items = StockAdjustmentItemSerializer(many=True)

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Notes'),
        help_text=_('Stock transaction notes'),
    )

    def validate(self, data):
        """Make sure items are provided."""
        super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('A list of stock items must be provided'))

        return data


class StockCountSerializer(StockAdjustmentSerializer):
    """Serializer for counting stock items."""

    def save(self):
        """Count stock."""
        request = self.context['request']

        data = self.validated_data
        items = data['items']
        notes = data.get('notes', '')

        with transaction.atomic():
            for item in items:
                stock_item = item['pk']
                quantity = item['quantity']

                # Optional fields
                extra = {}

                for field_name in StockItem.optional_transfer_fields():
                    if field_value := item.get(field_name, None):
                        extra[field_name] = field_value

                stock_item.stocktake(quantity, request.user, notes=notes, **extra)


class StockAddSerializer(StockAdjustmentSerializer):
    """Serializer for adding stock to stock item(s)."""

    def save(self):
        """Add stock."""
        request = self.context['request']

        data = self.validated_data
        notes = data.get('notes', '')

        with transaction.atomic():
            for item in data['items']:
                stock_item = item['pk']
                quantity = item['quantity']

                # Optional fields
                extra = {}

                for field_name in StockItem.optional_transfer_fields():
                    if field_value := item.get(field_name, None):
                        extra[field_name] = field_value

                stock_item.add_stock(quantity, request.user, notes=notes, **extra)


class StockRemoveSerializer(StockAdjustmentSerializer):
    """Serializer for removing stock from stock item(s)."""

    def save(self):
        """Remove stock."""
        request = self.context['request']

        data = self.validated_data
        notes = data.get('notes', '')

        with transaction.atomic():
            for item in data['items']:
                stock_item = item['pk']
                quantity = item['quantity']

                # Optional fields
                extra = {}

                for field_name in StockItem.optional_transfer_fields():
                    if field_value := item.get(field_name, None):
                        extra[field_name] = field_value

                stock_item.take_stock(quantity, request.user, notes=notes, **extra)


class StockTransferSerializer(StockAdjustmentSerializer):
    """Serializer for transferring (moving) stock item(s)."""

    class Meta:
        """Metaclass options."""

        fields = ['items', 'notes', 'location']

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Location'),
        help_text=_('Destination stock location'),
    )

    def save(self):
        """Transfer stock."""
        request = self.context['request']

        data = self.validated_data

        items = data['items']
        notes = data.get('notes', '')
        location = data['location']

        with transaction.atomic():
            for item in items:
                # Required fields
                stock_item = item['pk']
                quantity = item['quantity']

                # Optional fields
                kwargs = {}

                for field_name in StockItem.optional_transfer_fields():
                    if field_value := item.get(field_name, None):
                        kwargs[field_name] = field_value

                stock_item.move(
                    location, notes, request.user, quantity=quantity, **kwargs
                )


class StockItemSerialNumbersSerializer(InvenTreeModelSerializer):
    """Serializer for extra serial number information about a stock item."""

    class Meta:
        """Metaclass options."""

        model = StockItem
        fields = ['next', 'previous']

    next = StockItemSerializer(
        read_only=True, source='get_next_stock_item', label=_('Next Serial Number')
    )

    previous = StockItemSerializer(
        read_only=True,
        source='get_previous_stock_item',
        label=_('Previous Serial Number'),
    )
