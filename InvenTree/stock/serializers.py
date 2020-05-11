"""
JSON serializers for Stock app
"""

from rest_framework import serializers

from .models import StockItem, StockLocation
from .models import StockItemTracking
from .models import StockItemAttachment

from django.db.models import Sum, Count
from django.db.models.functions import Coalesce

from company.serializers import SupplierPartSerializer
from part.serializers import PartBriefSerializer
from InvenTree.serializers import UserSerializerBrief, InvenTreeModelSerializer


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
        ]


class StockItemSerializer(InvenTreeModelSerializer):
    """ Serializer for a StockItem:

    - Includes serialization for the linked part
    - Includes serialization for the item location
    """

    @staticmethod
    def prefetch_queryset(queryset):
        """
        Prefetch related database tables,
        to reduce database hits.
        """

        return queryset.prefetch_related(
            'belongs_to',
            'build',
            'build_order',
            'sales_order',
            'supplier_part',
            'supplier_part__supplier',
            'supplier_part__manufacturer',
            'allocations',
            'sales_order_allocations',
            'location',
            'part',
            'tracking_info',
        )

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add some extra annotations to the queryset,
        performing database queries as efficiently as possible.
        """

        queryset = queryset.annotate(
            allocated=Coalesce(
                Sum('sales_order_allocations__quantity', distinct=True), 0) + Coalesce(
                Sum('allocations__quantity', distinct=True), 0),
            tracking_items=Count('tracking_info'),
        )

        return queryset

    status_text = serializers.CharField(source='get_status_display', read_only=True)
    
    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    location_detail = LocationBriefSerializer(source='location', many=False, read_only=True)
    supplier_part_detail = SupplierPartSerializer(source='supplier_part', many=False, read_only=True)

    tracking_items = serializers.IntegerField()

    quantity = serializers.FloatField()
    allocated = serializers.FloatField()

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)
        location_detail = kwargs.pop('location_detail', False)
        supplier_part_detail = kwargs.pop('supplier_part_detail', False)

        super(StockItemSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if location_detail is not True:
            self.fields.pop('location_detail')

        if supplier_part_detail is not True:
            self.fields.pop('supplier_part_detail')

    class Meta:
        model = StockItem
        fields = [
            'allocated',
            'batch',
            'build_order',
            'belongs_to',
            'in_stock',
            'link',
            'location',
            'location_detail',
            'notes',
            'part',
            'part_detail',
            'pk',
            'quantity',
            'sales_order',
            'serial',
            'supplier_part',
            'supplier_part_detail',
            'status',
            'status_text',
            'tracking_items',
            'uid',
        ]

        """ These fields are read-only in this context.
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

    class Meta:
        model = StockLocation
        fields = [
            'pk',
            'url',
            'name',
            'description',
            'parent',
            'pathstring',
            'items',
        ]


class StockItemAttachmentSerializer(InvenTreeModelSerializer):
    """ Serializer for StockItemAttachment model """

    class Meta:
        model = StockItemAttachment

        fields = [
            'pk',
            'stock_item',
            'attachment',
            'comment'
        ]


class StockTrackingSerializer(InvenTreeModelSerializer):
    """ Serializer for StockItemTracking model """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    user = UserSerializerBrief(many=False, read_only=True)

    item = StockItemSerializerBrief(many=False, read_only=True)

    class Meta:
        model = StockItemTracking
        fields = [
            'pk',
            'url',
            'item',
            'date',
            'title',
            'notes',
            'link',
            'quantity',
            'user',
            'system',
        ]

        read_only_fields = [
            'date',
            'user',
            'system',
            'quantity',
        ]
