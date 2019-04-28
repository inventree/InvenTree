"""
JSON serializers for Part app
"""

from rest_framework import serializers

from .models import Part, PartCategory, BomItem
from .models import SupplierPart, SupplierPriceBreak

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

    class Meta:
        model = Part
        fields = [
            'pk',
            'url',
            'name',
            'description',
            'available_stock',
        ]


class PartSerializer(serializers.ModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    category_name = serializers.CharField(source='category_path', read_only=True)

    class Meta:
        model = Part
        fields = [
            'pk',
            'url',  # Link to the part detail page
            'name',
            'IPN',
            'URL',  # Link to an external URL (optional)
            'description',
            'category',
            'category_name',
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


class BomItemSerializer(InvenTreeModelSerializer):
    """ Serializer for BomItem object """

    # url = serializers.CharField(source='get_absolute_url', read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    sub_part_detail = PartBriefSerializer(source='sub_part', many=False, read_only=True)

    class Meta:
        model = BomItem
        fields = [
            'pk',
            # 'url',
            'part',
            'part_detail',
            'sub_part',
            'sub_part_detail',
            'quantity',
            'note',
        ]


class SupplierPartSerializer(serializers.ModelSerializer):
    """ Serializer for SupplierPart object """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    part_name = serializers.CharField(source='part.name', read_only=True)

    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = SupplierPart
        fields = [
            'pk',
            'url',
            'part',
            'part_name',
            'supplier',
            'supplier_name',
            'SKU',
            'manufacturer',
            'MPN',
        ]


class SupplierPriceBreakSerializer(serializers.ModelSerializer):
    """ Serializer for SupplierPriceBreak object """

    class Meta:
        model = SupplierPriceBreak
        fields = [
            'pk',
            'part',
            'quantity',
            'cost'
        ]
