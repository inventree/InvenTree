"""
JSON serializers for Company app
"""

from rest_framework import serializers

from django.db.models import Count

from .models import Company
from .models import SupplierPart, SupplierPriceBreak

from InvenTree.serializers import InvenTreeModelSerializer

from part.serializers import PartBriefSerializer


class CompanyBriefSerializer(InvenTreeModelSerializer):
    """ Serializer for Company object (limited detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    image = serializers.CharField(source='get_thumbnail_url', read_only=True)

    class Meta:
        model = Company
        fields = [
            'pk',
            'url',
            'name',
            'description',
            'image',
        ]


class CompanySerializer(InvenTreeModelSerializer):
    """ Serializer for Company object (full detail) """

    @staticmethod
    def annotate_queryset(queryset):

        return queryset.annotate(
            parts_supplied=Count('supplied_parts'),
            parts_manufactured=Count('manufactured_parts')
        )

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    
    image = serializers.CharField(source='get_thumbnail_url', read_only=True)

    parts_supplied = serializers.IntegerField(read_only=True)
    parts_manufactured = serializers.IntegerField(read_only=True)

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
            'link',
            'image',
            'is_customer',
            'is_manufacturer',
            'is_supplier',
            'notes',
            'parts_supplied',
            'parts_manufactured',
        ]


class SupplierPartSerializer(InvenTreeModelSerializer):
    """ Serializer for SupplierPart object """

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    supplier_detail = CompanyBriefSerializer(source='supplier', many=False, read_only=True)

    manufacturer_detail = CompanyBriefSerializer(source='manufacturer', many=False, read_only=True)

    pretty_name = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)
        supplier_detail = kwargs.pop('supplier_detail', False)
        manufacturer_detail = kwargs.pop('manufacturer_detail', False)
        prettify = kwargs.pop('pretty', False)

        super(SupplierPartSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if supplier_detail is not True:
            self.fields.pop('supplier_detail')

        if manufacturer_detail is not True:
            self.fields.pop('manufacturer_detail')

        if prettify is not True:
            self.fields.pop('pretty_name')

    supplier = serializers.PrimaryKeyRelatedField(queryset=Company.objects.filter(is_supplier=True))

    manufacturer = serializers.PrimaryKeyRelatedField(queryset=Company.objects.filter(is_manufacturer=True))

    class Meta:
        model = SupplierPart
        fields = [
            'pk',
            'part',
            'part_detail',
            'pretty_name',
            'supplier',
            'supplier_detail',
            'SKU',
            'manufacturer',
            'manufacturer_detail',
            'description',
            'MPN',
            'link',
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
