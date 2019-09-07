"""
JSON serializers for Part app
"""

from rest_framework import serializers

from .models import Part, PartStar

from .models import PartCategory
from .models import BomItem
from .models import PartParameter, PartParameterTemplate

from InvenTree.serializers import InvenTreeModelSerializer


class CategorySerializer(InvenTreeModelSerializer):
    """ Serializer for PartCategory """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = PartCategory
        fields = [
            'pk',
            'name',
            'description',
            'pathstring',
            'url',
            'parent',
        ]


class PartBriefSerializer(InvenTreeModelSerializer):
    """ Serializer for Part (brief detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)

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
            'image_url',
            'active',
        ]


class PartSerializer(InvenTreeModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    category_name = serializers.CharField(source='category_path', read_only=True)

    allocated_stock = serializers.IntegerField(source='allocation_count', read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('category')
        queryset = queryset.prefetch_related('stock_items')
        queryset = queryset.prefetch_related('bom_items')
        queryset = queryset.prefetch_related('builds')
        return queryset

    class Meta:
        model = Part
        partial = True
        fields = [
            'pk',
            'url',  # Link to the part detail page
            'category',
            'category_name',
            'image_url',
            'full_name',
            'name',
            'IPN',
            'is_template',
            'variant_of',
            'description',
            'keywords',
            'URL',
            'total_stock',
            'allocated_stock',
            'on_order',
            'units',
            'trackable',
            'assembly',
            'component',
            'trackable',
            'purchaseable',
            'salable',
            'active',
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
