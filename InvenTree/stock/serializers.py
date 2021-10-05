"""
JSON serializers for Stock app
"""

from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _

from .models import StockItem, StockLocation
from .models import StockItemTracking
from .models import StockItemAttachment
from .models import StockItemTestResult

from django.db.models.functions import Coalesce

from django.db.models import Case, When, Value
from django.db.models import BooleanField
from django.db.models import Q

from sql_util.utils import SubquerySum, SubqueryCount

from decimal import Decimal

from datetime import datetime, timedelta

import common.models
from common.settings import currency_code_default, currency_code_mappings

from company.serializers import SupplierPartSerializer
from part.serializers import PartBriefSerializer
from InvenTree.serializers import UserSerializerBrief, InvenTreeModelSerializer, InvenTreeMoneySerializer
from InvenTree.serializers import InvenTreeAttachmentSerializer, InvenTreeAttachmentSerializerField


class LocationBriefSerializer(InvenTreeModelSerializer):
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


class StockItemSerializerBrief(InvenTreeModelSerializer):
    """ Brief serializers for a StockItem """

    location_name = serializers.CharField(source='location', read_only=True)
    part_name = serializers.CharField(source='part.full_name', read_only=True)
    quantity = serializers.FloatField()

    class Meta:
        model = StockItem
        fields = [
            'pk',
            'uid',
            'part',
            'part_name',
            'supplier_part',
            'location',
            'location_name',
            'quantity',
            'serial',
        ]


class StockItemSerializer(InvenTreeModelSerializer):
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

    quantity = serializers.FloatField()

    allocated = serializers.FloatField(source='allocation_count', required=False)

    expired = serializers.BooleanField(required=False, read_only=True)

    stale = serializers.BooleanField(required=False, read_only=True)

    serial = serializers.CharField(required=False)

    required_tests = serializers.IntegerField(source='required_test_count', read_only=True, required=False)

    purchase_price = InvenTreeMoneySerializer(
        label=_('Purchase Price'),
        max_digits=19, decimal_places=4,
        allow_null=True
    )

    purchase_price_currency = serializers.ChoiceField(
        choices=currency_code_mappings(),
        default=currency_code_default,
        label=_('Currency'),
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
            'expired',
            'expiry_date',
            'in_stock',
            'is_building',
            'link',
            'location',
            'location_detail',
            'notes',
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


class StockQuantitySerializer(InvenTreeModelSerializer):

    class Meta:
        model = StockItem
        fields = ('quantity',)


class LocationSerializer(InvenTreeModelSerializer):
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


class StockItemAttachmentSerializer(InvenTreeAttachmentSerializer):
    """ Serializer for StockItemAttachment model """

    def __init__(self, *args, **kwargs):
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if user_detail is not True:
            self.fields.pop('user_detail')

    user_detail = UserSerializerBrief(source='user', read_only=True)

    attachment = InvenTreeAttachmentSerializerField(required=True)

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


class StockItemTestResultSerializer(InvenTreeModelSerializer):
    """ Serializer for the StockItemTestResult model """

    user_detail = UserSerializerBrief(source='user', read_only=True)

    key = serializers.CharField(read_only=True)

    attachment = InvenTreeAttachmentSerializerField(required=False)

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


class StockTrackingSerializer(InvenTreeModelSerializer):
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

    user_detail = UserSerializerBrief(source='user', many=False, read_only=True)

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
