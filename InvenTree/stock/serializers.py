"""JSON serializers for Stock app."""

from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import BooleanField, Case, Q, Value, When
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from sql_util.utils import SubqueryCount, SubquerySum

import common.models
import company.models
import InvenTree.helpers
import InvenTree.serializers
from common.settings import currency_code_default, currency_code_mappings
from company.serializers import SupplierPartSerializer
from InvenTree.serializers import InvenTreeDecimalField, extract_int
from part.serializers import PartBriefSerializer

from .models import (StockItem, StockItemAttachment, StockItemTestResult,
                     StockItemTracking, StockLocation)


class LocationBriefSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Provides a brief serializer for a StockLocation object."""

    class Meta:
        """Metaclass options."""

        model = StockLocation
        fields = [
            'pk',
            'name',
            'pathstring',
        ]


class StockItemSerializerBrief(InvenTree.serializers.InvenTreeModelSerializer):
    """Brief serializers for a StockItem."""

    location_name = serializers.CharField(source='location', read_only=True)
    part_name = serializers.CharField(source='part.full_name', read_only=True)

    quantity = InvenTreeDecimalField()

    class Meta:
        """Metaclass options."""

        model = StockItem
        fields = [
            'part',
            'part_name',
            'pk',
            'location',
            'location_name',
            'quantity',
            'serial',
            'supplier_part',
            'uid',
        ]

    def validate_serial(self, value):
        """Make sure serial is not to big."""
        if extract_int(value) > 2147483647:
            raise serializers.ValidationError('serial is to to big')
        return value


class StockItemSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for a StockItem.

    - Includes serialization for the linked part
    - Includes serialization for the item location
    """

    def update(self, instance, validated_data):
        """Custom update method to pass the user information through to the instance."""
        instance._user = self.context['user']

        return super().update(instance, validated_data)

    @staticmethod
    def annotate_queryset(queryset):
        """Add some extra annotations to the queryset, performing database queries as efficiently as possible."""
        # Annotate the queryset with the total allocated to sales orders
        queryset = queryset.annotate(
            allocated=Coalesce(
                SubquerySum('sales_order_allocations__quantity'), Decimal(0)
            ) + Coalesce(
                SubquerySum('allocations__quantity'), Decimal(0)
            )
        )

        # Annotate the queryset with the number of tracking items
        queryset = queryset.annotate(
            tracking_items=SubqueryCount('tracking_info')
        )

        # Add flag to indicate if the StockItem has expired
        queryset = queryset.annotate(
            expired=Case(
                When(
                    StockItem.EXPIRED_FILTER, then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField())
            )
        )

        # Add flag to indicate if the StockItem is stale
        stale_days = common.models.InvenTreeSetting.get_setting('STOCK_STALE_DAYS')
        stale_date = datetime.now().date() + timedelta(days=stale_days)
        stale_filter = StockItem.IN_STOCK_FILTER & ~Q(expiry_date=None) & Q(expiry_date__lt=stale_date)

        queryset = queryset.annotate(
            stale=Case(
                When(
                    stale_filter, then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        return queryset

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    supplier_part_detail = SupplierPartSerializer(source='supplier_part', many=False, read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    location_detail = LocationBriefSerializer(source='location', many=False, read_only=True)

    tracking_items = serializers.IntegerField(source='tracking_info_count', read_only=True, required=False)

    quantity = InvenTreeDecimalField()

    allocated = serializers.FloatField(source='allocation_count', required=False)

    expired = serializers.BooleanField(required=False, read_only=True)

    stale = serializers.BooleanField(required=False, read_only=True)

    # serial = serializers.CharField(required=False)

    required_tests = serializers.IntegerField(source='required_test_count', read_only=True, required=False)

    purchase_price = InvenTree.serializers.InvenTreeMoneySerializer(
        label=_('Purchase Price'),
        max_digits=19, decimal_places=4,
        allow_null=True,
        help_text=_('Purchase price of this stock item'),
    )

    purchase_price_currency = serializers.ChoiceField(
        choices=currency_code_mappings(),
        default=currency_code_default,
        label=_('Currency'),
        help_text=_('Purchase currency of this stock item'),
    )

    purchase_price_string = serializers.SerializerMethodField()

    def get_purchase_price_string(self, obj):
        """Return purchase price as string."""
        return str(obj.purchase_price) if obj.purchase_price else '-'

    purchase_order_reference = serializers.CharField(source='purchase_order.reference', read_only=True)

    sales_order_reference = serializers.CharField(source='sales_order.reference', read_only=True)

    def __init__(self, *args, **kwargs):
        """Add detail fields."""
        part_detail = kwargs.pop('part_detail', False)
        location_detail = kwargs.pop('location_detail', False)
        supplier_part_detail = kwargs.pop('supplier_part_detail', False)
        test_detail = kwargs.pop('test_detail', False)

        super(StockItemSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if location_detail is not True:
            self.fields.pop('location_detail')

        if supplier_part_detail is not True:
            self.fields.pop('supplier_part_detail')

        if test_detail is not True:
            self.fields.pop('required_tests')

    class Meta:
        """Metaclass options."""

        model = StockItem
        fields = [
            'allocated',
            'batch',
            'belongs_to',
            'build',
            'customer',
            'delete_on_deplete',
            'expired',
            'expiry_date',
            'in_stock',
            'is_building',
            'link',
            'location',
            'location_detail',
            'notes',
            'owner',
            'packaging',
            'part',
            'part_detail',
            'purchase_order',
            'purchase_order_reference',
            'pk',
            'quantity',
            'required_tests',
            'sales_order',
            'sales_order_reference',
            'serial',
            'stale',
            'status',
            'status_text',
            'stocktake_date',
            'supplier_part',
            'supplier_part_detail',
            'tracking_items',
            'uid',
            'updated',
            'purchase_price',
            'purchase_price_currency',
            'purchase_price_string',
        ]

        """
        These fields are read-only in this context.
        They can be updated by accessing the appropriate API endpoints
        """
        read_only_fields = [
            'allocated',
            'stocktake_date',
            'stocktake_user',
            'updated',
            'in_stock'
        ]


class SerializeStockItemSerializer(serializers.Serializer):
    """A DRF serializer for "serializing" a StockItem.

    (Sorry for the confusing naming...)

    Here, "serializing" means splitting out a single StockItem,
    into multiple single-quantity items with an assigned serial number

    Note: The base StockItem object is provided to the serializer context
    """

    class Meta:
        """Metaclass options."""

        fields = [
            'quantity',
            'serial_numbers',
            'destination',
            'notes',
        ]

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
            raise ValidationError(_("Quantity must be greater than zero"))

        if quantity > item.quantity:
            q = item.quantity
            raise ValidationError(_(f"Quantity must not exceed available stock quantity ({q})"))

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
        label=_("Notes"),
        help_text=_("Optional note field")
    )

    def validate(self, data):
        """Check that the supplied serial numbers are valid."""
        data = super().validate(data)

        item = self.context['item']

        if not item.part.trackable:
            raise ValidationError(_("Serial numbers cannot be assigned to this part"))

        # Ensure the serial numbers are valid!
        quantity = data['quantity']
        serial_numbers = data['serial_numbers']

        try:
            serials = InvenTree.helpers.extract_serial_numbers(serial_numbers, quantity, item.part.getLatestSerialNumberInt())
        except DjangoValidationError as e:
            raise ValidationError({
                'serial_numbers': e.messages,
            })

        existing = item.part.find_conflicting_serial_numbers(serials)

        if len(existing) > 0:
            exists = ','.join([str(x) for x in existing])
            error = _('Serial numbers already exist') + ": " + exists

            raise ValidationError({
                'serial_numbers': error,
            })

        return data

    def save(self):
        """Serialize stock item."""
        item = self.context['item']
        request = self.context['request']
        user = request.user

        data = self.validated_data

        serials = InvenTree.helpers.extract_serial_numbers(
            data['serial_numbers'],
            data['quantity'],
            item.part.getLatestSerialNumberInt()
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

    note = serializers.CharField(
        label=_('Note'),
        required=False,
        allow_blank=True,
    )

    def validate_stock_item(self, stock_item):
        """Validate the selected stock item."""
        if not stock_item.in_stock:
            # StockItem must be in stock to be "installed"
            raise ValidationError(_("Stock item is unavailable"))

        # Extract the "parent" item - the item into which the stock item will be installed
        parent_item = self.context['item']
        parent_part = parent_item.part

        if not parent_part.check_if_part_in_bom(stock_item.part):
            raise ValidationError(_("Selected part is not in the Bill of Materials"))

        return stock_item

    def save(self):
        """Install the selected stock item into this one."""
        data = self.validated_data

        stock_item = data['stock_item']
        note = data.get('note', '')

        parent_item = self.context['item']
        request = self.context['request']

        parent_item.installStockItem(
            stock_item,
            stock_item.quantity,
            request.user,
            note,
        )


class UninstallStockItemSerializer(serializers.Serializer):
    """API serializers for uninstalling an installed item from a stock item."""

    class Meta:
        """Metaclass options."""

        fields = [
            'location',
            'note',
        ]

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False, required=True, allow_null=False,
        label=_('Location'),
        help_text=_('Destination location for uninstalled item')
    )

    note = serializers.CharField(
        label=_('Notes'),
        help_text=_('Add transaction note (optional)'),
        required=False, allow_blank=True,
    )

    def save(self):
        """Uninstall stock item."""
        item = self.context['item']

        data = self.validated_data
        request = self.context['request']

        location = data['location']

        note = data.get('note', '')

        item.uninstall_into_location(
            location,
            request.user,
            note
        )


class LocationTreeSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for a simple tree view."""

    class Meta:
        """Metaclass options."""

        model = StockLocation
        fields = [
            'pk',
            'name',
            'parent',
        ]


class LocationSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Detailed information about a stock location."""

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    items = serializers.IntegerField(source='item_count', read_only=True)

    level = serializers.IntegerField(read_only=True)

    class Meta:
        """Metaclass options."""

        model = StockLocation
        fields = [
            'pk',
            'url',
            'name',
            'level',
            'description',
            'parent',
            'pathstring',
            'items',
            'owner',
        ]


class StockItemAttachmentSerializer(InvenTree.serializers.InvenTreeAttachmentSerializer):
    """Serializer for StockItemAttachment model."""

    def __init__(self, *args, **kwargs):
        """Add detail fields."""
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if user_detail is not True:
            self.fields.pop('user_detail')

    user_detail = InvenTree.serializers.UserSerializerBrief(source='user', read_only=True)

    # TODO: Record the uploading user when creating or updating an attachment!

    class Meta:
        """Metaclass options."""

        model = StockItemAttachment

        fields = [
            'pk',
            'stock_item',
            'attachment',
            'filename',
            'link',
            'comment',
            'upload_date',
            'user',
            'user_detail',
        ]

        read_only_fields = [
            'upload_date',
            'user',
            'user_detail'
        ]


class StockItemTestResultSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for the StockItemTestResult model."""

    user_detail = InvenTree.serializers.UserSerializerBrief(source='user', read_only=True)

    key = serializers.CharField(read_only=True)

    attachment = InvenTree.serializers.InvenTreeAttachmentSerializerField(required=False)

    def __init__(self, *args, **kwargs):
        """Add detail fields."""
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if user_detail is not True:
            self.fields.pop('user_detail')

    class Meta:
        """Metaclass options."""

        model = StockItemTestResult

        fields = [
            'pk',
            'stock_item',
            'key',
            'test',
            'result',
            'value',
            'attachment',
            'notes',
            'user',
            'user_detail',
            'date'
        ]

        read_only_fields = [
            'pk',
            'user',
            'date',
        ]


class StockTrackingSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for StockItemTracking model."""

    def __init__(self, *args, **kwargs):
        """Add detail fields."""
        item_detail = kwargs.pop('item_detail', False)
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if item_detail is not True:
            self.fields.pop('item_detail')

        if user_detail is not True:
            self.fields.pop('user_detail')

    label = serializers.CharField(read_only=True)

    item_detail = StockItemSerializerBrief(source='item', many=False, read_only=True)

    user_detail = InvenTree.serializers.UserSerializerBrief(source='user', many=False, read_only=True)

    deltas = serializers.JSONField(read_only=True)

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

        read_only_fields = [
            'date',
            'user',
            'label',
            'tracking_type',
        ]


class StockAssignmentItemSerializer(serializers.Serializer):
    """Serializer for a single StockItem with in StockAssignment request.

    Here, the particular StockItem is being assigned (manually) to a customer

    Fields:
        - item: StockItem object
    """

    class Meta:
        """Metaclass options."""

        fields = [
            'item',
        ]

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
            raise ValidationError(_("Item must be in stock"))

        # The base part must be "salable"
        if not item.part.salable:
            raise ValidationError(_("Part must be salable"))

        # The item must not be allocated to a sales order
        if item.sales_order_allocations.count() > 0:
            raise ValidationError(_("Item is allocated to a sales order"))

        # The item must not be allocated to a build order
        if item.allocations.count() > 0:
            raise ValidationError(_("Item is allocated to a build order"))

        return item


class StockAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning one (or more) stock items to a customer.

    This is a manual assignment process, separate for (for example) a Sales Order
    """

    class Meta:
        """Metaclass options."""

        fields = [
            'items',
            'customer',
            'notes',
        ]

    items = StockAssignmentItemSerializer(
        many=True,
        required=True,
    )

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
            raise ValidationError(_("A list of stock items must be provided"))

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

                stock_item.allocateToCustomer(
                    customer,
                    user=user,
                    notes=notes,
                )


class StockMergeItemSerializer(serializers.Serializer):
    """Serializer for a single StockItem within the StockMergeSerializer class.

    Here, the individual StockItem is being checked for merge compatibility.
    """

    class Meta:
        """Metaclass options."""

        fields = [
            'item',
        ]

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

    items = StockMergeItemSerializer(
        many=True,
        required=True,
    )

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
                allow_mismatched_suppliers=data.get('allow_mismatched_suppliers', False),
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
            notes=data.get('notes', None)
        )


class StockAdjustmentItemSerializer(serializers.Serializer):
    """Serializer for a single StockItem within a stock adjument request.

    Fields:
        - item: StockItem object
        - quantity: Numerical quantity
    """

    class Meta:
        """Metaclass options."""

        fields = [
            'item',
            'quantity'
        ]

    pk = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label='stock_item',
        help_text=_('StockItem primary key value')
    )

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=0,
        required=True
    )


class StockAdjustmentSerializer(serializers.Serializer):
    """Base class for managing stock adjustment actions via the API."""

    class Meta:
        """Metaclass options."""

        fields = [
            'items',
            'notes',
        ]

    items = StockAdjustmentItemSerializer(many=True)

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_("Notes"),
        help_text=_("Stock transaction notes"),
    )

    def validate(self, data):
        """Make sure items are provided."""
        super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_("A list of stock items must be provided"))

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

                stock_item.stocktake(
                    quantity,
                    request.user,
                    notes=notes
                )


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

                stock_item.add_stock(
                    quantity,
                    request.user,
                    notes=notes
                )


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

                stock_item.take_stock(
                    quantity,
                    request.user,
                    notes=notes
                )


class StockTransferSerializer(StockAdjustmentSerializer):
    """Serializer for transferring (moving) stock item(s)."""

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Location'),
        help_text=_('Destination stock location'),
    )

    class Meta:
        """Metaclass options."""

        fields = [
            'items',
            'notes',
            'location',
        ]

    def save(self):
        """Transfer stock."""
        request = self.context['request']

        data = self.validated_data

        items = data['items']
        notes = data.get('notes', '')
        location = data['location']

        with transaction.atomic():
            for item in items:

                stock_item = item['pk']
                quantity = item['quantity']

                stock_item.move(
                    location,
                    notes,
                    request.user,
                    quantity=quantity
                )
