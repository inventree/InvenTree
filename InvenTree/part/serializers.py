"""
JSON serializers for Part app
"""

from rest_framework import serializers

from .models import Part, PartStar

from .models import PartCategory
from .models import BomItem
from .models import PartParameter, PartParameterTemplate

from decimal import Decimal

from django.db.models import Q, F, Sum, Count
from django.db.models.functions import Coalesce

from InvenTree.status_codes import StockStatus, OrderStatus, BuildStatus
from InvenTree.serializers import InvenTreeModelSerializer


class CategorySerializer(InvenTreeModelSerializer):
    """ Serializer for PartCategory """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    parts = serializers.IntegerField(source='item_count', read_only=True)

    class Meta:
        model = PartCategory
        fields = [
            'pk',
            'name',
            'description',
            'pathstring',
            'url',
            'parent',
            'parts',
        ]


class PartThumbSerializer(serializers.Serializer):
    """
    Serializer for the 'image' field of the Part model.
    Used to serve and display existing Part images.
    """

    image = serializers.URLField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class PartBriefSerializer(InvenTreeModelSerializer):
    """ Serializer for Part (brief detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('category')
        queryset = queryset.prefetch_related('stock_items')
        queryset = queryset.prefetch_related('bom_items')
        queryset = queryset.prefetch_related('builds')
        return queryset
    
    class Meta:
        model = Part
        fields = [
            'pk',
            'url',
            'full_name',
            'description',
            'total_stock',
            'available_stock',
            'thumbnail',
            'active',
            'assembly',
            'virtual',
        ]


class PartSerializer(InvenTreeModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    @staticmethod
    def prefetch_queryset(queryset):
        return queryset.prefetch_related(
            'category',
            'stock_items',
            'bom_items',
            'builds',
            'supplier_parts',
            'supplier_parts__purchase_order_line_items',
            'supplier_parts__purcahes_order_line_items__order'
        )

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add some extra annotations to the queryset, 
        performing database queries as efficiently as possible,
        to reduce database trips.
        """

        # Filter to limit stock items to "available"
        stock_filter = Q(stock_items__status__in=StockStatus.AVAILABLE_CODES)

        # Filter to limit orders to "open"
        order_filter = Q(supplier_parts__purchase_order_line_items__order__status__in=OrderStatus.OPEN)

        # Filter to limit builds to "active"
        build_filter = Q(builds__status__in=BuildStatus.ACTIVE_CODES)

        # Annotate the number total stock count
        queryset = queryset.annotate(
            in_stock=Coalesce(Sum('stock_items__quantity', filter=stock_filter, distinct=True), Decimal(0))
        )

        # Annotate the number of parts "on order"
        # Total "on order" parts = "Quantity" - "Received" for each active purchase order
        queryset = queryset.annotate(
            ordering=Coalesce(Sum(
                'supplier_parts__purchase_order_line_items__quantity',
                filter=order_filter,
                distinct=True
            ), Decimal(0)) - Coalesce(Sum(
                'supplier_parts__purchase_order_line_items__received',
                filter=order_filter,
                distinct=True
            ), Decimal(0))
        )

        # Annotate number of parts being build
        queryset = queryset.annotate(
            building=Coalesce(
                Sum('builds__quantity', filter=build_filter, distinct=True), Decimal(0)
            )
        )
        
        return queryset

    in_stock = serializers.FloatField(read_only=True)
    ordering = serializers.FloatField(read_only=True)
    building = serializers.FloatField(read_only=True)

    #allocated_stock = serializers.FloatField(source='allocation_count', read_only=True)
    #bom_items = serializers.IntegerField(source='bom_count', read_only=True)
    #building = serializers.FloatField(source='quantity_being_built', read_only=False)
    #category_name = serializers.CharField(source='category_path', read_only=True)
    image = serializers.CharField(source='get_image_url', read_only=True)
    #on_order = serializers.FloatField(read_only=True)
    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)
    url = serializers.CharField(source='get_absolute_url', read_only=True)
    #used_in = serializers.IntegerField(source='used_in_count', read_only=True)

    # TODO - Include a 'category_detail' field which serializers the category object

    class Meta:
        model = Part
        partial = True
        fields = [
            'active',
            #'allocated_stock',
            'assembly',
            #'bom_items',
            #'building',
            'category',
            #'category_name',
            'component',
            'description',
            'full_name',
            'image',
            'in_stock',
            'ordering',
            'building',
            'IPN',
            'is_template',
            'keywords',
            'link',
            'name',
            'notes',
            #'on_order',
            'pk',
            'purchaseable',
            'salable',
            'thumbnail',
            'trackable',
            #'total_stock',
            'units',
            #'used_in',
            'url',  # Link to the part detail page
            'variant_of',
            'virtual',
        ]


class PartStarSerializer(InvenTreeModelSerializer):
    """ Serializer for a PartStar object """

    partname = serializers.CharField(source='part.full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = PartStar
        fields = [
            'pk',
            'part',
            'partname',
            'user',
            'username',
        ]


class BomItemSerializer(InvenTreeModelSerializer):
    """ Serializer for BomItem object """

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    sub_part_detail = PartBriefSerializer(source='sub_part', many=False, read_only=True)
    price_range = serializers.CharField(read_only=True)
    validated = serializers.BooleanField(read_only=True, source='is_line_valid')

    def __init__(self, *args, **kwargs):
        # part_detail and sub_part_detail serializers are only included if requested.
        # This saves a bunch of database requests

        part_detail = kwargs.pop('part_detail', False)
        sub_part_detail = kwargs.pop('sub_part_detail', False)

        super(BomItemSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if sub_part_detail is not True:
            self.fields.pop('sub_part_detail')

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('part')
        queryset = queryset.prefetch_related('part__category')
        queryset = queryset.prefetch_related('part__stock_items')
        queryset = queryset.prefetch_related('sub_part')
        queryset = queryset.prefetch_related('sub_part__category')
        queryset = queryset.prefetch_related('sub_part__stock_items')
        queryset = queryset.prefetch_related('sub_part__supplier_parts__pricebreaks')
        return queryset

    class Meta:
        model = BomItem
        fields = [
            'pk',
            'part',
            'part_detail',
            'sub_part',
            'sub_part_detail',
            'quantity',
            'reference',
            'price_range',
            'overage',
            'note',
            'validated',
        ]


class PartParameterSerializer(InvenTreeModelSerializer):
    """ JSON serializers for the PartParameter model """

    class Meta:
        model = PartParameter
        fields = [
            'pk',
            'part',
            'template',
            'data'
        ]


class PartParameterTemplateSerializer(InvenTreeModelSerializer):
    """ JSON serializer for the PartParameterTemplate model """

    class Meta:
        model = PartParameterTemplate
        fields = [
            'pk',
            'name',
            'units',
        ]
