"""
JSON serializers for Part app
"""

from rest_framework import serializers

from .models import Part, PartStar

from .models import PartCategory
from .models import BomItem

from InvenTree.serializers import InvenTreeModelSerializer


class CategorySerializer(serializers.ModelSerializer):
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


class PartBriefSerializer(serializers.ModelSerializer):
    """ Serializer for Part (brief detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    single_price_info = serializers.CharField(read_only=True)
    
    class Meta:
        model = Part
        fields = [
            'pk',
            'url',
            'full_name',
            'description',
            'available_stock',
            'single_price_info',
            'image_url',
        ]


class PartSerializer(serializers.ModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    category_name = serializers.CharField(source='category_path', read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('category')
        queryset = queryset.prefetch_related('locations')
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
            'variant',
            'description',
            'keywords',
            'URL',
            'total_stock',
            'available_stock',
            'units',
            'trackable',
            'buildable',
            'consumable',
            'trackable',
            'salable',
            'active',
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
    price_info = serializers.CharField(read_only=True)

    class Meta:
        model = BomItem
        fields = [
            'pk',
            'part',
            'part_detail',
            'sub_part',
            'sub_part_detail',
            'quantity',
            'price_info',
            'overage',
            'note',
        ]
