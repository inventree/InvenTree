"""JSON serializers for Company app."""

import io

from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from sql_util.utils import SubqueryCount
from taggit.serializers import TagListSerializerField

import company.filters
import part.filters
import part.serializers as part_serializers
from importer.mixins import DataImportExportSerializerMixin
from importer.registry import register_importer
from InvenTree.serializers import (
    InvenTreeCurrencySerializer,
    InvenTreeDecimalField,
    InvenTreeImageSerializerField,
    InvenTreeModelSerializer,
    InvenTreeMoneySerializer,
    InvenTreeTagModelSerializer,
    NotesFieldMixin,
    RemoteImageMixin,
)

from .models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    ManufacturerPartParameter,
    SupplierPart,
    SupplierPriceBreak,
)


class CompanyBriefSerializer(InvenTreeModelSerializer):
    """Serializer for Company object (limited detail)."""

    class Meta:
        """Metaclass options."""

        model = Company
        fields = [
            'pk',
            'active',
            'name',
            'description',
            'image',
            'thumbnail',
            'currency',
        ]
        read_only_fields = ['currency']

    image = InvenTreeImageSerializerField(read_only=True)

    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)


@register_importer()
class AddressSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializer for the Address Model."""

    class Meta:
        """Metaclass options."""

        model = Address
        fields = [
            'pk',
            'company',
            'title',
            'primary',
            'line1',
            'line2',
            'postal_code',
            'postal_city',
            'province',
            'country',
            'shipping_notes',
            'internal_shipping_notes',
            'link',
        ]


class AddressBriefSerializer(InvenTreeModelSerializer):
    """Serializer for Address Model (limited)."""

    class Meta:
        """Metaclass options."""

        model = Address
        fields = [
            'pk',
            'line1',
            'line2',
            'postal_code',
            'postal_city',
            'province',
            'country',
            'shipping_notes',
            'internal_shipping_notes',
        ]


@register_importer()
class CompanySerializer(
    DataImportExportSerializerMixin,
    NotesFieldMixin,
    RemoteImageMixin,
    InvenTreeModelSerializer,
):
    """Serializer for Company object (full detail)."""

    export_exclude_fields = ['primary_address']

    import_exclude_fields = ['image']

    class Meta:
        """Metaclass options."""

        model = Company
        fields = [
            'pk',
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
            'active',
            'is_customer',
            'is_manufacturer',
            'is_supplier',
            'notes',
            'parts_supplied',
            'parts_manufactured',
            'remote_image',
            'address_count',
            'primary_address',
        ]

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the supplied queryset with aggregated information."""
        # Add count of parts manufactured
        queryset = queryset.annotate(
            parts_manufactured=SubqueryCount('manufactured_parts')
        )

        queryset = queryset.annotate(parts_supplied=SubqueryCount('supplied_parts'))

        queryset = queryset.annotate(address_count=SubqueryCount('addresses'))

        return queryset

    address = serializers.CharField(
        label=_(
            'Return the string representation for the primary address. This property exists for backwards compatibility.'
        ),
        allow_null=True,
        read_only=True,
    )

    primary_address = AddressSerializer(required=False, allow_null=True, read_only=True)

    image = InvenTreeImageSerializerField(required=False, allow_null=True)

    email = serializers.EmailField(
        required=False, default='', allow_blank=True, allow_null=True
    )

    parts_supplied = serializers.IntegerField(read_only=True)
    parts_manufactured = serializers.IntegerField(read_only=True)
    address_count = serializers.IntegerField(read_only=True)

    currency = InvenTreeCurrencySerializer(
        help_text=_('Default currency used for this supplier'), required=True
    )

    def save(self):
        """Save the Company instance."""
        super().save()

        company = self.instance

        # Check if an image was downloaded from a remote URL
        remote_img = getattr(self, 'remote_image_file', None)

        if remote_img and company:
            fmt = remote_img.format or 'PNG'
            buffer = io.BytesIO()
            remote_img.save(buffer, format=fmt)

            # Construct a simplified name for the image
            filename = f'company_{company.pk}_image.{fmt.lower()}'

            company.image.save(filename, ContentFile(buffer.getvalue()))

        return self.instance


@register_importer()
class ContactSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializer class for the Contact model."""

    class Meta:
        """Metaclass options."""

        model = Contact
        fields = ['pk', 'company', 'company_name', 'name', 'phone', 'email', 'role']

    company_name = serializers.CharField(
        label=_('Company Name'), source='company.name', read_only=True
    )


@register_importer()
class ManufacturerPartSerializer(
    DataImportExportSerializerMixin, InvenTreeTagModelSerializer, NotesFieldMixin
):
    """Serializer for ManufacturerPart object."""

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
            'barcode_hash',
            'notes',
            'tags',
        ]

    tags = TagListSerializerField(required=False)

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra detail fields as required."""
        part_detail = kwargs.pop('part_detail', True)
        manufacturer_detail = kwargs.pop('manufacturer_detail', True)
        prettify = kwargs.pop('pretty', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail', None)

        if manufacturer_detail is not True:
            self.fields.pop('manufacturer_detail', None)

        if prettify is not True:
            self.fields.pop('pretty_name', None)

    part_detail = part_serializers.PartBriefSerializer(
        source='part', many=False, read_only=True
    )

    manufacturer_detail = CompanyBriefSerializer(
        source='manufacturer', many=False, read_only=True
    )

    pretty_name = serializers.CharField(read_only=True)

    manufacturer = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_manufacturer=True)
    )


@register_importer()
class ManufacturerPartParameterSerializer(
    DataImportExportSerializerMixin, InvenTreeModelSerializer
):
    """Serializer for the ManufacturerPartParameter model."""

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

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra detail fields as required."""
        man_detail = kwargs.pop('manufacturer_part_detail', False)

        super().__init__(*args, **kwargs)

        if not man_detail:
            self.fields.pop('manufacturer_part_detail', None)

    manufacturer_part_detail = ManufacturerPartSerializer(
        source='manufacturer_part', many=False, read_only=True
    )


@register_importer()
class SupplierPartSerializer(
    DataImportExportSerializerMixin, InvenTreeTagModelSerializer, NotesFieldMixin
):
    """Serializer for SupplierPart object."""

    export_exclude_fields = ['tags']

    export_child_fields = [
        'part_detail.name',
        'part_detail.description',
        'part_detail.IPN',
        'supplier_detail.name',
        'manufacturer_detail.name',
    ]

    class Meta:
        """Metaclass options."""

        model = SupplierPart
        fields = [
            'available',
            'availability_updated',
            'description',
            'in_stock',
            'on_order',
            'link',
            'active',
            'manufacturer_detail',
            'manufacturer_part',
            'manufacturer_part_detail',
            'MPN',
            'note',
            'pk',
            'barcode_hash',
            'packaging',
            'pack_quantity',
            'pack_quantity_native',
            'part',
            'part_detail',
            'pretty_name',
            'SKU',
            'supplier',
            'supplier_detail',
            'updated',
            'notes',
            'tags',
        ]

        read_only_fields = [
            'availability_updated',
            'barcode_hash',
            'pack_quantity_native',
        ]

    tags = TagListSerializerField(required=False)

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra detail fields as required."""
        # Check if 'available' quantity was supplied

        self.has_available_quantity = 'available' in kwargs.get('data', {})

        brief = kwargs.pop('brief', False)

        detail_default = not brief

        part_detail = kwargs.pop('part_detail', detail_default)
        supplier_detail = kwargs.pop('supplier_detail', detail_default)
        manufacturer_detail = kwargs.pop('manufacturer_detail', detail_default)

        prettify = kwargs.pop('pretty', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail', None)

        if supplier_detail is not True:
            self.fields.pop('supplier_detail', None)

        if manufacturer_detail is not True:
            self.fields.pop('manufacturer_detail', None)
            self.fields.pop('manufacturer_part_detail', None)

        if brief or prettify is not True:
            self.fields.pop('pretty_name', None)

        if brief:
            self.fields.pop('tags')
            self.fields.pop('available')
            self.fields.pop('on_order')
            self.fields.pop('availability_updated')

    # Annotated field showing total in-stock quantity
    in_stock = serializers.FloatField(read_only=True, label=_('In Stock'))

    on_order = serializers.FloatField(read_only=True, label=_('On Order'))

    available = serializers.FloatField(required=False, label=_('Available'))

    pack_quantity_native = serializers.FloatField(read_only=True)

    part_detail = part_serializers.PartBriefSerializer(
        label=_('Part'), source='part', many=False, read_only=True
    )

    supplier_detail = CompanyBriefSerializer(
        label=_('Supplier'), source='supplier', many=False, read_only=True
    )

    manufacturer_detail = CompanyBriefSerializer(
        label=_('Manufacturer'),
        source='manufacturer_part.manufacturer',
        many=False,
        read_only=True,
    )

    pretty_name = serializers.CharField(read_only=True)

    supplier = serializers.PrimaryKeyRelatedField(
        label=_('Supplier'), queryset=Company.objects.filter(is_supplier=True)
    )

    manufacturer_part_detail = ManufacturerPartSerializer(
        label=_('Manufacturer Part'),
        source='manufacturer_part',
        part_detail=False,
        read_only=True,
    )

    MPN = serializers.CharField(
        source='manufacturer_part.MPN', read_only=True, label=_('MPN')
    )

    # Date fields
    updated = serializers.DateTimeField(allow_null=True, read_only=True)

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the SupplierPart queryset with extra fields.

        Fields:
            in_stock: Current stock quantity for each SupplierPart
        """
        queryset = queryset.annotate(in_stock=part.filters.annotate_total_stock())

        queryset = queryset.annotate(
            on_order=company.filters.annotate_on_order_quantity()
        )

        return queryset

    def update(self, supplier_part, data):
        """Custom update functionality for the serializer."""
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
            kwargs = {'manufacturer': manufacturer, 'MPN': MPN}
            supplier_part.save(**kwargs)

        return supplier_part


@register_importer()
class SupplierPriceBreakSerializer(
    DataImportExportSerializerMixin, InvenTreeModelSerializer
):
    """Serializer for SupplierPriceBreak object."""

    class Meta:
        """Metaclass options."""

        model = SupplierPriceBreak
        fields = [
            'pk',
            'part',
            'part_detail',
            'quantity',
            'price',
            'price_currency',
            'supplier',
            'supplier_detail',
            'updated',
        ]

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra fields as required."""
        supplier_detail = kwargs.pop('supplier_detail', False)
        part_detail = kwargs.pop('part_detail', False)

        super().__init__(*args, **kwargs)

        if not supplier_detail:
            self.fields.pop('supplier_detail', None)

        if not part_detail:
            self.fields.pop('part_detail', None)

    @staticmethod
    def annotate_queryset(queryset):
        """Prefetch related fields for the queryset."""
        queryset = queryset.select_related('part', 'part__supplier', 'part__part')

        return queryset

    quantity = InvenTreeDecimalField()

    price = InvenTreeMoneySerializer(allow_null=True, required=True, label=_('Price'))

    price_currency = InvenTreeCurrencySerializer()

    supplier = serializers.PrimaryKeyRelatedField(
        source='part.supplier', many=False, read_only=True
    )

    supplier_detail = CompanyBriefSerializer(
        source='part.supplier', many=False, read_only=True
    )

    # Detail serializer for SupplierPart
    part_detail = SupplierPartSerializer(
        source='part', brief=True, many=False, read_only=True
    )
