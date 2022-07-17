"""JSON serializers for Company app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from sql_util.utils import SubqueryCount

import part.filters
from common.settings import currency_code_default, currency_code_mappings
from InvenTree.serializers import (InvenTreeAttachmentSerializer,
                                   InvenTreeDecimalField,
                                   InvenTreeImageSerializerField,
                                   InvenTreeModelSerializer,
                                   InvenTreeMoneySerializer)
from part.serializers import PartBriefSerializer

from .models import (Company, ManufacturerPart, ManufacturerPartAttachment,
                     ManufacturerPartParameter, SupplierPart,
                     SupplierPriceBreak)


class CompanyBriefSerializer(InvenTreeModelSerializer):
    """Serializer for Company object (limited detail)"""

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    image = serializers.CharField(source='get_thumbnail_url', read_only=True)

    class Meta:
        """Metaclass options."""

        model = Company
        fields = [
            'pk',
            'url',
            'name',
            'description',
            'image',
        ]


class CompanySerializer(InvenTreeModelSerializer):
    """Serializer for Company object (full detail)"""

    @staticmethod
    def annotate_queryset(queryset):
        """Annoate the supplied queryset with aggregated information"""
        # Add count of parts manufactured
        queryset = queryset.annotate(
            parts_manufactured=SubqueryCount('manufactured_parts')
        )

        queryset = queryset.annotate(
            parts_supplied=SubqueryCount('supplied_parts')
        )

        return queryset

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    image = InvenTreeImageSerializerField(required=False, allow_null=True)

    parts_supplied = serializers.IntegerField(read_only=True)
    parts_manufactured = serializers.IntegerField(read_only=True)

    currency = serializers.ChoiceField(
        choices=currency_code_mappings(),
        initial=currency_code_default,
        help_text=_('Default currency used for this supplier'),
        label=_('Currency Code'),
        required=True,
    )

    class Meta:
        """Metaclass options."""

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
            'currency',
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


class ManufacturerPartSerializer(InvenTreeModelSerializer):
    """Serializer for ManufacturerPart object."""

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    manufacturer_detail = CompanyBriefSerializer(source='manufacturer', many=False, read_only=True)

    pretty_name = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra detail fields as required"""
        part_detail = kwargs.pop('part_detail', True)
        manufacturer_detail = kwargs.pop('manufacturer_detail', True)
        prettify = kwargs.pop('pretty', False)

        super(ManufacturerPartSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if manufacturer_detail is not True:
            self.fields.pop('manufacturer_detail')

        if prettify is not True:
            self.fields.pop('pretty_name')

    manufacturer = serializers.PrimaryKeyRelatedField(queryset=Company.objects.filter(is_manufacturer=True))

    class Meta:
        """Metaclass options."""

        model = ManufacturerPart
        fields = [
            'pk',
            'part',
            'part_detail',
            'pretty_name',
            'manufacturer',
            'manufacturer_detail',
            'description',
            'MPN',
            'link',
        ]


class ManufacturerPartAttachmentSerializer(InvenTreeAttachmentSerializer):
    """Serializer for the ManufacturerPartAttachment class."""

    class Meta:
        """Metaclass options."""

        model = ManufacturerPartAttachment

        fields = [
            'pk',
            'manufacturer_part',
            'attachment',
            'filename',
            'link',
            'comment',
            'upload_date',
            'user',
            'user_detail',
        ]

        read_only_fields = [
            'upload_date',
        ]


class ManufacturerPartParameterSerializer(InvenTreeModelSerializer):
    """Serializer for the ManufacturerPartParameter model."""

    manufacturer_part_detail = ManufacturerPartSerializer(source='manufacturer_part', many=False, read_only=True)

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra detail fields as required"""
        man_detail = kwargs.pop('manufacturer_part_detail', False)

        super(ManufacturerPartParameterSerializer, self).__init__(*args, **kwargs)

        if not man_detail:
            self.fields.pop('manufacturer_part_detail')

    class Meta:
        """Metaclass options."""

        model = ManufacturerPartParameter

        fields = [
            'pk',
            'manufacturer_part',
            'manufacturer_part_detail',
            'name',
            'value',
            'units',
        ]


class SupplierPartSerializer(InvenTreeModelSerializer):
    """Serializer for SupplierPart object."""

    # Annotated field showing total in-stock quantity
    in_stock = serializers.FloatField(read_only=True)

    # Annotated field showing the last update time
    last_updated = serializers.DateTimeField(read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    supplier_detail = CompanyBriefSerializer(source='supplier', many=False, read_only=True)

    manufacturer_detail = CompanyBriefSerializer(source='manufacturer_part.manufacturer', many=False, read_only=True)

    pretty_name = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra detail fields as required"""

        # Check if 'available' quantity was supplied
        self.has_available_quantity = 'available' in kwargs.get('data', {})

        part_detail = kwargs.pop('part_detail', True)
        supplier_detail = kwargs.pop('supplier_detail', True)
        manufacturer_detail = kwargs.pop('manufacturer_detail', True)

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

    manufacturer = serializers.CharField(read_only=True)

    MPN = serializers.CharField(read_only=True)

    manufacturer_part_detail = ManufacturerPartSerializer(source='manufacturer_part', read_only=True)

    class Meta:
        """Metaclass options."""

        model = SupplierPart
        fields = [
            'availability_updated',
            'available',
            'description',
            'in_stock',
            'last_updated',
            'link',
            'manufacturer_detail',
            'manufacturer_part_detail',
            'manufacturer_part',
            'manufacturer',
            'MPN',
            'note',
            'packaging',
            'part_detail',
            'part',
            'pk',
            'pretty_name',
            'SKU',
            'supplier_detail',
            'supplier',
        ]

        read_only_fields = [
            'availability_updated',
            'last_updated',
        ]

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the SupplierPart queryset with extra fields:

        Fields:
            in_stock: Current stock quantity for each SupplierPart
        """

        queryset = queryset.annotate(
            in_stock=part.filters.annotate_total_stock(),
            last_updated=part.filters.annotate_last_updated(),
        )

        return queryset

    def update(self, supplier_part, data):
        """Custom update functionality for the serializer"""

        available = data.pop('available', None)

        response = super().update(supplier_part, data)

        if available is not None and self.has_available_quantity:
            supplier_part.update_available_quantity(available)

        return response

    def create(self, validated_data):
        """Extract manufacturer data and process ManufacturerPart."""

        # Extract 'available' quantity from the serializer
        available = validated_data.pop('available', None)

        # Create SupplierPart
        supplier_part = super().create(validated_data)

        if available is not None and self.has_available_quantity:
            supplier_part.update_available_quantity(available)

        # Get ManufacturerPart raw data (unvalidated)
        manufacturer = self.initial_data.get('manufacturer', None)
        MPN = self.initial_data.get('MPN', None)

        if manufacturer and MPN:
            kwargs = {
                'manufacturer': manufacturer,
                'MPN': MPN,
            }
            supplier_part.save(**kwargs)

        return supplier_part


class SupplierPriceBreakSerializer(InvenTreeModelSerializer):
    """Serializer for SupplierPriceBreak object."""

    quantity = InvenTreeDecimalField()

    price = InvenTreeMoneySerializer(
        allow_null=True,
        required=True,
        label=_('Price'),
    )

    price_currency = serializers.ChoiceField(
        choices=currency_code_mappings(),
        default=currency_code_default,
        label=_('Currency'),
    )

    class Meta:
        """Metaclass options."""

        model = SupplierPriceBreak
        fields = [
            'pk',
            'part',
            'quantity',
            'price',
            'price_currency',
            'updated',
        ]
