"""
JSON serializers for Stock app
"""

from rest_framework import serializers

from .models import StockItem, StockLocation
from .models import StockItemTracking

from part.serializers import PartBriefSerializer
from InvenTree.serializers import UserSerializerBrief, InvenTreeModelSerializer


class LocationBriefSerializer(InvenTreeModelSerializer):
    """
    Provides a brief serializer for a StockLocation object
    """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = StockLocation
        fields = [
            'pk',
            'name',
            'pathstring',
            'url',
        ]


class StockItemSerializerBrief(InvenTreeModelSerializer):
    """ Brief serializers for a StockItem """

    location_name = serializers.CharField(source='location', read_only=True)
    part_name = serializers.CharField(source='part.full_name', read_only=True)

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
            'supplier_part',
            'supplier_part__supplier',
            'supplier_part__manufacturer',
            'location',
            'part'
        )

    status_text = serializers.CharField(source='get_status_display', read_only=True)
    
    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    location_detail = LocationBriefSerializer(source='location', many=False, read_only=True)

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)
        location_detail = kwargs.pop('location_detail', False)

        super(StockItemSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if location_detail is not True:
            self.fields.pop('location_detail')

    class Meta:
        model = StockItem
        fields = [
            'batch',
            'in_stock',
            'link',
            'location',
            'location_detail',
            'notes',
            'part',
            'part_detail',
            'pk',
            'quantity',
            'serial',
            'supplier_part',
            'status',
            'status_text',
            'uid',
        ]

        """ These fields are read-only in this context.
        They can be updated by accessing the appropriate API endpoints
        """
        read_only_fields = [
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
