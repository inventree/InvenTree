"""
JSON serializers for Part app
"""
import imghdr

from rest_framework import serializers

from .models import Part, PartStar

from .models import PartCategory
from .models import BomItem
from .models import PartParameter, PartParameterTemplate
from .models import PartAttachment
from .models import PartTestTemplate
from .models import PartSellPriceBreak

from stock.models import StockItem

from decimal import Decimal

from sql_util.utils import SubquerySum, SubqueryCount

from django.db.models import Q
from django.db.models.functions import Coalesce

from InvenTree.status_codes import PurchaseOrderStatus, BuildStatus
from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField


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


class PartAttachmentSerializer(InvenTreeModelSerializer):
    """
    Serializer for the PartAttachment class
    """

    attachment = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = PartAttachment

        fields = [
            'pk',
            'part',
            'attachment',
            'comment'
        ]


class PartTestTemplateSerializer(InvenTreeModelSerializer):
    """
    Serializer for the PartTestTemplate class
    """

    key = serializers.CharField(read_only=True)

    class Meta:
        model = PartTestTemplate

        fields = [
            'pk',
            'key',
            'part',
            'test_name',
            'description',
            'required',
            'requires_value',
            'requires_attachment',
        ]


class PartSalePriceSerializer(InvenTreeModelSerializer):
    """
    Serializer for sale prices for Part model.
    """

    symbol = serializers.CharField(read_only=True)

    suffix = serializers.CharField(read_only=True)

    quantity = serializers.FloatField()

    cost = serializers.FloatField()

    class Meta:
        model = PartSellPriceBreak
        fields = [
            'pk',
            'part',
            'quantity',
            'cost',
            'currency',
            'symbol',
            'suffix',
        ]


class PartThumbSerializer(serializers.Serializer):
    """
    Serializer for the 'image' field of the Part model.
    Used to serve and display existing Part images.
    """

    image = serializers.URLField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class PartThumbSerializerUpdate(InvenTreeModelSerializer):
    """ Serializer for updating Part thumbnail """

    def validate_image(self, value):
        """
        Check that file is an image.
        """
        validate = imghdr.what(value)
        if not validate:
            raise serializers.ValidationError("File is not an image")
        return value

    image = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = Part
        fields = [
            'image',
        ]


class PartBriefSerializer(InvenTreeModelSerializer):
    """ Serializer for Part (brief detail) """

    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)
    
    stock = serializers.FloatField(source='total_stock')

    class Meta:
        model = Part
        fields = [
            'pk',
            'IPN',
            'name',
            'revision',
            'full_name',
            'description',
            'thumbnail',
            'active',
            'assembly',
            'is_template',
            'purchaseable',
            'salable',
            'stock',
            'trackable',
            'virtual',
        ]


class PartSerializer(InvenTreeModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    def __init__(self, *args, **kwargs):
        """
        Custom initialization method for PartSerializer,
        so that we can optionally pass extra fields based on the query.
        """

        self.starred_parts = kwargs.pop('starred_parts', [])

        category_detail = kwargs.pop('category_detail', False)

        super().__init__(*args, **kwargs)

        if category_detail is not True:
            self.fields.pop('category_detail')

    @staticmethod
    def prefetch_queryset(queryset):
        """
        Prefetch related database tables,
        to reduce database hits.
        """

        return queryset.prefetch_related(
            'category',
            'category__parts',
            'category__parent',
            'stock_items',
            'bom_items',
            'builds',
            'supplier_parts',
            'supplier_parts__purchase_order_line_items',
            'supplier_parts__purchase_order_line_items__order',
        )

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add some extra annotations to the queryset,
        performing database queries as efficiently as possible,
        to reduce database trips.
        """

        # Annotate with the total 'in stock' quantity
        queryset = queryset.annotate(
            in_stock=Coalesce(
                SubquerySum('stock_items__quantity', filter=StockItem.IN_STOCK_FILTER),
                Decimal(0)
            ),
        )

        # Annotate with the total number of stock items
        queryset = queryset.annotate(
            stock_item_count=SubqueryCount('stock_items')
        )

        # Filter to limit builds to "active"
        build_filter = Q(
            status__in=BuildStatus.ACTIVE_CODES
        )

        # Annotate with the total 'building' quantity
        queryset = queryset.annotate(
            building=Coalesce(
                SubquerySum('builds__quantity', filter=build_filter),
                Decimal(0),
            )
        )
        
        # Filter to limit orders to "open"
        order_filter = Q(
            order__status__in=PurchaseOrderStatus.OPEN
        )

        # Annotate with the total 'on order' quantity
        queryset = queryset.annotate(
            ordering=Coalesce(
                SubquerySum('supplier_parts__purchase_order_line_items__quantity', filter=order_filter),
                Decimal(0),
            ) - Coalesce(
                SubquerySum('supplier_parts__purchase_order_line_items__received', filter=order_filter),
                Decimal(0),
            )
        )
        
        return queryset

    def get_starred(self, part):
        """
        Return "true" if the part is starred by the current user.
        """

        return part in self.starred_parts

    # Extra detail for the category
    category_detail = CategorySerializer(source='category', many=False, read_only=True)

    # Calculated fields
    in_stock = serializers.FloatField(read_only=True)
    ordering = serializers.FloatField(read_only=True)
    building = serializers.FloatField(read_only=True)
    stock_item_count = serializers.IntegerField(read_only=True)

    image = serializers.CharField(source='get_image_url', read_only=True)
    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)
    starred = serializers.SerializerMethodField()

    # PrimaryKeyRelated fields (Note: enforcing field type here results in much faster queries, somehow...)
    category = serializers.PrimaryKeyRelatedField(queryset=PartCategory.objects.all())

    # TODO - Include annotation for the following fields:
    # allocated_stock = serializers.FloatField(source='allocation_count', read_only=True)
    # bom_items = serializers.IntegerField(source='bom_count', read_only=True)
    # used_in = serializers.IntegerField(source='used_in_count', read_only=True)

    class Meta:
        model = Part
        partial = True
        fields = [
            'active',
            # 'allocated_stock',
            'assembly',
            # 'bom_items',
            'category',
            'category_detail',
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
            'minimum_stock',
            'name',
            'notes',
            'pk',
            'purchaseable',
            'revision',
            'salable',
            'starred',
            'stock_item_count',
            'thumbnail',
            'trackable',
            'units',
            # 'used_in',
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

    price_range = serializers.CharField(read_only=True)

    quantity = serializers.FloatField()

    part = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(assembly=True))
    
    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    sub_part = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(component=True))

    sub_part_detail = PartBriefSerializer(source='sub_part', many=False, read_only=True)

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
