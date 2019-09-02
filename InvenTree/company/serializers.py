"""
JSON serializers for Company app
"""

from rest_framework import serializers

from .models import Company
from .models import SupplierPart, SupplierPriceBreak

from InvenTree.serializers import InvenTreeModelSerializer

from part.serializers import PartBriefSerializer


class CompanyBriefSerializer(InvenTreeModelSerializer):
    """ Serializer for Company object (limited detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Company
        fields = [
            'pk',
            'url',
            'name'
        ]


class CompanySerializer(InvenTreeModelSerializer):
    """ Serializer for Company object (full detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    part_count = serializers.CharField(read_only=True)

    image = serializers.CharField(source='get_image_url', read_only=True)

    class Meta:
        model = Company
        fields = [
            'pk',
            'url',
            'name',
            'description',
            'website',
            'name',
            'phone',
            'address',
            'email',
            'contact',
            'URL',
            'image',
            'notes',
            'is_customer',
            'is_supplier',
            'part_count'
        ]


class SupplierPartSerializer(InvenTreeModelSerializer):
    """ Serializer for SupplierPart object """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_logo = serializers.CharField(source='supplier.get_image_url', read_only=True)

    pricing = serializers.CharField(source='unit_pricing', read_only=True)

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)

        super(SupplierPartSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

    class Meta:
        model = SupplierPart
        fields = [
            'pk',
            'url',
            'part',
            'part_detail',
            'supplier',
            'supplier_name',
            'supplier_logo',
            'SKU',
            'manufacturer',
            'description',
            'MPN',
            'URL',
            'pricing',
        ]


class SupplierPriceBreakSerializer(InvenTreeModelSerializer):
    """ Serializer for SupplierPriceBreak object """

    class Meta:
        model = SupplierPriceBreak
        fields = [
            'pk',
            'part',
            'quantity',
            'cost'
        ]
