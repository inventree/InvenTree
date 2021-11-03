"""
JSON serializers for Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.functions import Coalesce
from django.db.models import Case, When, Value
from django.db.models import BooleanField
from django.db.models import Q

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from sql_util.utils import SubquerySum, SubqueryCount

from .models import StockItem, StockLocation
from .models import StockItemTracking
from .models import StockItemAttachment
from .models import StockItemTestResult

import common.models
from common.settings import currency_code_default, currency_code_mappings
from company.serializers import SupplierPartSerializer

import InvenTree.helpers
import InvenTree.serializers

from part.serializers import PartBriefSerializer


class LocationBriefSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """
    Provides a brief serializer for a StockLocation object
    """

    class Meta:
        model = StockLocation
        fields = [
            'pk',
            'name',
            'pathstring',
        ]


class StockItemSerializerBrief(InvenTree.serializers.InvenTreeModelSerializer):
    """ Brief serializers for a StockItem """

    location_name = serializers.CharField(source='location', read_only=True)
    part_name = serializers.CharField(source='part.full_name', read_only=True)
    quantity = serializers.FloatField()

    class Meta:
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


class StockItemSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """ Serializer for a StockItem:

    - Includes serialization for the linked part
    - Includes serialization for the item location
    """

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add some extra annotations to the queryset,
        performing database queries as efficiently as possible.
        """

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

    # quantity = serializers.FloatField()

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

        return str(obj.purchase_price) if obj.purchase_price else '-'

    purchase_order_reference = serializers.CharField(source='purchase_order.reference', read_only=True)

    sales_order_reference = serializers.CharField(source='sales_order.reference', read_only=True)

    def __init__(self, *args, **kwargs):

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
    """
    A DRF serializer for "serializing" a StockItem.

    (Sorry for the confusing naming...)

    Here, "serializing" means splitting out a single StockItem,
    into multiple single-quantity items with an assigned serial number

    Note: The base StockItem object is provided to the serializer context
    """

    class Meta:
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
        """
        Validate that the quantity value is correct
        """

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
        """
        Check that the supplied serial numbers are valid
        """

        data = super().validate(data)

        item = self.context['item']

        if not item.part.trackable:
            raise ValidationError(_("Serial numbers cannot be assigned to this part"))

        # Ensure the serial numbers are valid!
        quantity = data['quantity']
        serial_numbers = data['serial_numbers']

        try:
            serials = InvenTree.helpers.extract_serial_numbers(serial_numbers, quantity)
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

        item = self.context['item']
        request = self.context['request']
        user = request.user

        data = self.validated_data

        serials = InvenTree.helpers.extract_serial_numbers(
            data['serial_numbers'],
            data['quantity'],
        )

        item.serializeStock(
            data['quantity'],
            serials,
            user,
            notes=data.get('notes', ''),
            location=data['destination'],
        )


class LocationSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """ Detailed information about a stock location
    """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    items = serializers.IntegerField(source='item_count', read_only=True)

    level = serializers.IntegerField(read_only=True)

    class Meta:
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
        ]


class StockItemAttachmentSerializer(InvenTree.serializers.InvenTreeAttachmentSerializer):
    """ Serializer for StockItemAttachment model """

    def __init__(self, *args, **kwargs):
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if user_detail is not True:
            self.fields.pop('user_detail')

    user_detail = InvenTree.serializers.UserSerializerBrief(source='user', read_only=True)

    attachment = InvenTree.serializers.InvenTreeAttachmentSerializerField(required=True)

    # TODO: Record the uploading user when creating or updating an attachment!

    class Meta:
        model = StockItemAttachment

        fields = [
            'pk',
            'stock_item',
            'attachment',
            'filename',
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
    """ Serializer for the StockItemTestResult model """

    user_detail = InvenTree.serializers.UserSerializerBrief(source='user', read_only=True)

    key = serializers.CharField(read_only=True)

    attachment = InvenTree.serializers.InvenTreeAttachmentSerializerField(required=False)

    def __init__(self, *args, **kwargs):
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if user_detail is not True:
            self.fields.pop('user_detail')

    class Meta:
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
    """ Serializer for StockItemTracking model """

    def __init__(self, *args, **kwargs):

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


class StockAdjustmentItemSerializer(serializers.Serializer):
    """
    Serializer for a single StockItem within a stock adjument request.

    Fields:
        - item: StockItem object
        - quantity: Numerical quantity
    """

    class Meta:
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
    """
    Base class for managing stock adjustment actions via the API
    """

    class Meta:
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

        super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_("A list of stock items must be provided"))

        return data


class StockCountSerializer(StockAdjustmentSerializer):
    """
    Serializer for counting stock items
    """

    def save(self):

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
    """
    Serializer for adding stock to stock item(s)
    """

    def save(self):

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
    """
    Serializer for removing stock from stock item(s)
    """

    def save(self):
        
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
    """
    Serializer for transferring (moving) stock item(s)
    """

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Location'),
        help_text=_('Destination stock location'),
    )

    class Meta:
        fields = [
            'items',
            'notes',
            'location',
        ]

    def validate(self, data):

        super().validate(data)

        # TODO: Any specific validation of location field?

        return data

    def save(self):

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
