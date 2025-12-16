"""DRF data serializers for Part app."""

import io
import os
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import ExpressionWrapper, F, Q
from django.db.models.functions import Greatest
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

import structlog
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from sql_util.utils import SubqueryCount

import common.currency
import common.filters
import common.serializers
import company.models
import InvenTree.helpers
import InvenTree.serializers
import part.filters as part_filters
import part.helpers as part_helpers
import stock.models
import users.models
from importer.registry import register_importer
from InvenTree.mixins import DataImportExportSerializerMixin
from InvenTree.ready import isGeneratingSchema
from InvenTree.serializers import (
    FilterableDateTimeField,
    FilterableFloatField,
    FilterableListField,
    FilterableListSerializer,
    enable_filter,
)
from users.serializers import UserSerializer

from .models import (
    BomItem,
    BomItemSubstitute,
    Part,
    PartCategory,
    PartCategoryParameterTemplate,
    PartInternalPriceBreak,
    PartPricing,
    PartRelated,
    PartSellPriceBreak,
    PartStar,
    PartStocktake,
    PartTestTemplate,
)

logger = structlog.get_logger('inventree')


@register_importer()
class CategorySerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    DataImportExportSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for PartCategory."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartCategory
        fields = [
            'pk',
            'name',
            'description',
            'default_location',
            'default_keywords',
            'level',
            'parent',
            'part_count',
            'subcategories',
            'pathstring',
            'path',
            'starred',
            'structural',
            'icon',
            'parent_default_location',
        ]
        read_only_fields = ['level', 'pathstring']

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate extra information to the queryset."""
        # Annotate the number of 'parts' which exist in each category (including subcategories!)
        queryset = queryset.annotate(
            part_count=part_filters.annotate_category_parts(),
            subcategories=part_filters.annotate_sub_categories(),
        )

        queryset = queryset.annotate(
            parent_default_location=part_filters.annotate_default_location('parent__')
        )

        return queryset

    parent = serializers.PrimaryKeyRelatedField(
        queryset=PartCategory.objects.all(),
        required=False,
        allow_null=True,
        label=_('Parent Category'),
        help_text=_('Parent part category'),
    )

    part_count = serializers.IntegerField(
        read_only=True, allow_null=True, label=_('Parts')
    )

    subcategories = serializers.IntegerField(
        read_only=True, allow_null=True, label=_('Subcategories')
    )

    level = serializers.IntegerField(read_only=True)

    starred = serializers.SerializerMethodField()

    def get_starred(self, category) -> bool:
        """Return True if the category is directly "starred" by the current user."""
        return category in self.context.get('starred_categories', [])

    path = enable_filter(
        FilterableListField(
            child=serializers.DictField(),
            source='get_path',
            read_only=True,
            allow_null=True,
        ),
        filter_name='path_detail',
    )

    icon = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text=_('Icon (optional)'),
        max_length=100,
    )

    parent_default_location = serializers.IntegerField(read_only=True, allow_null=True)


class CategoryTree(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for PartCategory tree."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartCategory
        fields = ['pk', 'name', 'parent', 'icon', 'structural', 'subcategories']

    subcategories = serializers.IntegerField(label=_('Subcategories'), read_only=True)

    icon = serializers.CharField(
        required=False, allow_blank=True, help_text=_('Icon (optional)'), max_length=100
    )

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the queryset with the number of subcategories."""
        return queryset.annotate(subcategories=part_filters.annotate_sub_categories())


@register_importer()
class PartTestTemplateSerializer(
    DataImportExportSerializerMixin, InvenTree.serializers.InvenTreeModelSerializer
):
    """Serializer for the PartTestTemplate class."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartTestTemplate

        fields = [
            'pk',
            'key',
            'part',
            'test_name',
            'description',
            'enabled',
            'required',
            'requires_value',
            'requires_attachment',
            'results',
            'choices',
        ]

    key = serializers.CharField(read_only=True)
    results = serializers.IntegerField(
        label=_('Results'),
        help_text=_('Number of results recorded against this template'),
        read_only=True,
    )

    @staticmethod
    def annotate_queryset(queryset):
        """Custom query annotations for the PartTestTemplate serializer."""
        return queryset.annotate(results=SubqueryCount('test_results'))


@register_importer()
class PartSalePriceSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    DataImportExportSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for sale prices for Part model."""

    no_filters = True

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartSellPriceBreak
        fields = ['pk', 'part', 'quantity', 'price', 'price_currency']

    quantity = InvenTree.serializers.InvenTreeDecimalField()

    price = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)

    price_currency = InvenTree.serializers.InvenTreeCurrencySerializer(
        help_text=_('Purchase currency of this stock item')
    )


class PartInternalPriceSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for internal prices for Part model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartInternalPriceBreak
        fields = ['pk', 'part', 'quantity', 'price', 'price_currency']

    quantity = InvenTree.serializers.InvenTreeDecimalField()

    price = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)

    price_currency = InvenTree.serializers.InvenTreeCurrencySerializer(
        help_text=_('Purchase currency of this stock item')
    )


class PartThumbSerializer(serializers.Serializer):
    """Serializer for the 'image' field of the Part model.

    Used to serve and display existing Part images.
    """

    image = InvenTree.serializers.InvenTreeImageSerializerField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class PartThumbSerializerUpdate(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for updating Part thumbnail."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = Part
        fields = ['image']

    def validate_image(self, value):
        """Check that file is an image."""
        validate = InvenTree.helpers.TestIfImage(value)
        if not validate:
            raise serializers.ValidationError(_('File is not an image'))
        return value

    image = InvenTree.serializers.InvenTreeAttachmentSerializerField(required=True)


class PartBriefSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for Part (brief detail)."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = Part
        fields = [
            'pk',
            'IPN',
            'barcode_hash',
            'category_default_location',
            'default_location',
            'default_expiry',
            'name',
            'revision',
            'full_name',
            'description',
            'image',
            'thumbnail',
            'active',
            'locked',
            'assembly',
            'component',
            'minimum_stock',
            'is_template',
            'purchaseable',
            'salable',
            'testable',
            'trackable',
            'virtual',
            'units',
            'pricing_min',
            'pricing_max',
        ]
        read_only_fields = ['barcode_hash']

    category_default_location = serializers.IntegerField(
        read_only=True, allow_null=True
    )

    image = InvenTree.serializers.InvenTreeImageSerializerField(
        read_only=True, allow_null=True
    )
    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)

    IPN = serializers.CharField(
        required=False,
        allow_null=True,
        help_text=_('Internal Part Number'),
        max_length=100,
    )

    revision = serializers.CharField(
        required=False, default='', allow_blank=True, allow_null=True, max_length=100
    )

    # Pricing fields
    pricing_min = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(
            source='pricing_data.overall_min', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )
    pricing_max = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(
            source='pricing_data.overall_max', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )


class DuplicatePartSerializer(serializers.Serializer):
    """Serializer for specifying options when duplicating a Part.

    The fields in this serializer control how the Part is duplicated.
    """

    class Meta:
        """Metaclass options."""

        fields = [
            'part',
            'copy_image',
            'copy_bom',
            'copy_parameters',
            'copy_notes',
            'copy_tests',
        ]

    part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.all(),
        label=_('Original Part'),
        help_text=_('Select original part to duplicate'),
        required=True,
    )

    copy_image = serializers.BooleanField(
        label=_('Copy Image'),
        help_text=_('Copy image from original part'),
        required=False,
        default=False,
    )

    copy_bom = serializers.BooleanField(
        label=_('Copy BOM'),
        help_text=_('Copy bill of materials from original part'),
        required=False,
        default=False,
    )

    copy_parameters = serializers.BooleanField(
        label=_('Copy Parameters'),
        help_text=_('Copy parameter data from original part'),
        required=False,
        default=False,
    )

    copy_notes = serializers.BooleanField(
        label=_('Copy Notes'),
        help_text=_('Copy notes from original part'),
        required=False,
        default=True,
    )

    copy_tests = serializers.BooleanField(
        label=_('Copy Tests'),
        help_text=_('Copy test templates from original part'),
        required=False,
        default=False,
    )


class InitialStockSerializer(serializers.Serializer):
    """Serializer for creating initial stock quantity."""

    class Meta:
        """Metaclass options."""

        fields = ['quantity', 'location']

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        label=_('Initial Stock Quantity'),
        help_text=_(
            'Specify initial stock quantity for this Part. If quantity is zero, no stock is added.'
        ),
        required=True,
    )

    location = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockLocation.objects.all(),
        label=_('Initial Stock Location'),
        help_text=_('Specify initial stock location for this Part'),
        allow_null=True,
        required=False,
    )


class InitialSupplierSerializer(serializers.Serializer):
    """Serializer for adding initial supplier / manufacturer information."""

    class Meta:
        """Metaclass options."""

        fields = ['supplier', 'sku', 'manufacturer', 'mpn']

    supplier = serializers.PrimaryKeyRelatedField(
        queryset=company.models.Company.objects.all(),
        label=_('Supplier'),
        help_text=_('Select supplier (or leave blank to skip)'),
        allow_null=True,
        required=False,
    )

    sku = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        label=_('SKU'),
        help_text=_('Supplier stock keeping unit'),
    )

    manufacturer = serializers.PrimaryKeyRelatedField(
        queryset=company.models.Company.objects.all(),
        label=_('Manufacturer'),
        help_text=_('Select manufacturer (or leave blank to skip)'),
        allow_null=True,
        required=False,
    )

    mpn = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        label=_('MPN'),
        help_text=_('Manufacturer part number'),
    )

    def validate_supplier(self, company):
        """Validation for the provided Supplier."""
        if company and not company.is_supplier:
            raise serializers.ValidationError(
                _('Selected company is not a valid supplier')
            )

        return company

    def validate_manufacturer(self, company):
        """Validation for the provided Manufacturer."""
        if company and not company.is_manufacturer:
            raise serializers.ValidationError(
                _('Selected company is not a valid manufacturer')
            )

        return company

    def validate(self, data):
        """Extra validation for this serializer."""
        if company.models.ManufacturerPart.objects.filter(
            manufacturer=data.get('manufacturer', None), MPN=data.get('mpn', '')
        ).exists():
            raise serializers.ValidationError({
                'mpn': _('Manufacturer part matching this MPN already exists')
            })

        if company.models.SupplierPart.objects.filter(
            supplier=data.get('supplier', None), SKU=data.get('sku', '')
        ).exists():
            raise serializers.ValidationError({
                'sku': _('Supplier part matching this SKU already exists')
            })

        return data


class DefaultLocationSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Brief serializer for a StockLocation object.

    Defined here, rather than stock.serializers, to negotiate circular imports.
    """

    class Meta:
        """Metaclass options."""

        import stock.models as stock_models

        model = stock_models.StockLocation
        fields = ['pk', 'name', 'pathstring']


@register_importer()
class PartSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    DataImportExportSerializerMixin,
    InvenTree.serializers.NotesFieldMixin,
    InvenTree.serializers.RemoteImageMixin,
    InvenTree.serializers.InvenTreeTaggitSerializer,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for complete detail information of a part.

    Used when displaying all details of a single component.
    """

    import_exclude_fields = ['creation_date', 'creation_user', 'duplicate']

    class Meta:
        """Metaclass defining serializer fields."""

        model = Part
        partial = True
        fields = [
            'active',
            'assembly',
            'barcode_hash',
            'category',
            'category_detail',
            'category_path',
            'category_name',
            'component',
            'creation_date',
            'creation_user',
            'default_expiry',
            'default_location',
            'default_location_detail',
            'default_supplier',
            'description',
            'full_name',
            'image',
            'remote_image',
            'existing_image',
            'IPN',
            'is_template',
            'keywords',
            'link',
            'locked',
            'minimum_stock',
            'name',
            'notes',
            'parameters',
            'pk',
            'purchaseable',
            'revision',
            'revision_of',
            'revision_count',
            'salable',
            'starred',
            'thumbnail',
            'testable',
            'trackable',
            'units',
            'variant_of',
            'virtual',
            'pricing_min',
            'pricing_max',
            'pricing_updated',
            'responsible',
            'price_breaks',
            # Annotated fields
            'allocated_to_build_orders',
            'allocated_to_sales_orders',
            'building',
            'scheduled_to_build',
            'category_default_location',
            'in_stock',
            'ordering',
            'required_for_build_orders',
            'required_for_sales_orders',
            'stock_item_count',
            'total_in_stock',
            'external_stock',
            'unallocated_stock',
            'variant_stock',
            # Fields only used for Part creation
            'duplicate',
            'initial_stock',
            'initial_supplier',
            'copy_category_parameters',
            'tags',
        ]
        read_only_fields = ['barcode_hash', 'creation_date', 'creation_user']

    def __init__(self, *args, **kwargs):
        """Custom initialization method for PartSerializer.

        - Allows us to optionally pass extra fields based on the query.
        """
        self.starred_parts = kwargs.pop('starred_parts', [])
        create = kwargs.pop('create', False)

        super().__init__(*args, **kwargs)

        if isGeneratingSchema():
            return

        if not create:
            # These fields are only used for the LIST API endpoint
            for f in self.skip_create_fields():
                # Fields required for certain operations, but are not part of the model
                if f in ['remote_image', 'existing_image']:
                    continue
                self.fields.pop(f, None)

    def get_api_url(self):
        """Return the API url associated with this serializer."""
        return reverse_lazy('api-part-list')

    def skip_create_fields(self):
        """Skip these fields when instantiating a new Part instance."""
        fields = super().skip_create_fields()

        fields += [
            'duplicate',
            'initial_stock',
            'initial_supplier',
            'copy_category_parameters',
            'existing_image',
        ]

        return fields

    @staticmethod
    def annotate_queryset(queryset):
        """Add some extra annotations to the queryset.

        Performing database queries as efficiently as possible, to reduce database trips.
        """
        # Annotate with the total number of revisions
        queryset = queryset.annotate(revision_count=SubqueryCount('revisions'))

        # Annotate with the total number of stock items
        queryset = queryset.annotate(stock_item_count=SubqueryCount('stock_items'))

        # Annotate with the total variant stock quantity
        variant_query = part_filters.variant_stock_query()

        queryset = queryset.annotate(
            variant_stock=part_filters.annotate_variant_quantity(
                variant_query, reference='quantity'
            )
        )

        # Annotate with the total 'building' quantity
        queryset = queryset.annotate(
            building=part_filters.annotate_in_production_quantity()
        )

        queryset = queryset.annotate(
            scheduled_to_build=part_filters.annotate_scheduled_to_build_quantity()
        )

        queryset = queryset.annotate(
            ordering=part_filters.annotate_on_order_quantity(),
            in_stock=part_filters.annotate_total_stock(),
            allocated_to_sales_orders=part_filters.annotate_sales_order_allocations(),
            allocated_to_build_orders=part_filters.annotate_build_order_allocations(),
        )

        # Annotate the queryset with the 'total_in_stock' quantity
        # This is the 'in_stock' quantity summed with the 'variant_stock' quantity
        queryset = queryset.annotate(
            total_in_stock=ExpressionWrapper(
                F('in_stock') + F('variant_stock'), output_field=models.DecimalField()
            )
        )

        queryset = queryset.annotate(
            external_stock=part_filters.annotate_total_stock(
                filter=Q(location__external=True)
            )
        )

        # Annotate with the total 'available stock' quantity
        # This is the current stock, minus any allocations
        queryset = queryset.annotate(
            unallocated_stock=Greatest(
                ExpressionWrapper(
                    F('total_in_stock')
                    - F('allocated_to_sales_orders')
                    - F('allocated_to_build_orders'),
                    output_field=models.DecimalField(),
                ),
                Decimal(0),
                output_field=models.DecimalField(),
            )
        )

        # Annotate with the total 'required for builds' quantity
        queryset = queryset.annotate(
            required_for_build_orders=part_filters.annotate_build_order_requirements(),
            required_for_sales_orders=part_filters.annotate_sales_order_requirements(),
        )

        queryset = queryset.annotate(
            category_default_location=part_filters.annotate_default_location(
                'category__'
            )
        )

        return queryset

    def get_starred(self, part) -> bool:
        """Return "true" if the part is starred by the current user."""
        return part in self.starred_parts

    # Extra detail for the category
    category_detail = enable_filter(
        CategorySerializer(
            source='category', many=False, read_only=True, allow_null=True
        ),
        prefetch_fields=['category'],
    )

    category_path = enable_filter(
        FilterableListField(
            child=serializers.DictField(),
            source='category.get_path',
            read_only=True,
            allow_null=True,
        ),
        filter_name='path_detail',
        prefetch_fields=['category'],
    )

    default_location_detail = enable_filter(
        DefaultLocationSerializer(
            source='default_location', many=False, read_only=True, allow_null=True
        ),
        filter_name='location_detail',
        prefetch_fields=['default_location'],
    )

    category_name = serializers.CharField(
        source='category.name', read_only=True, label=_('Category Name')
    )

    responsible = serializers.PrimaryKeyRelatedField(
        queryset=users.models.Owner.objects.all(),
        required=False,
        allow_null=True,
        source='responsible_owner',
    )

    creation_user = serializers.PrimaryKeyRelatedField(
        queryset=users.models.User.objects.all(), required=False, allow_null=True
    )

    IPN = serializers.CharField(
        required=False, default='', allow_blank=True, label=_('IPN'), max_length=100
    )

    revision = serializers.CharField(
        required=False, default='', allow_blank=True, allow_null=True, max_length=100
    )

    # Annotated fields
    allocated_to_build_orders = serializers.FloatField(read_only=True, allow_null=True)
    allocated_to_sales_orders = serializers.FloatField(read_only=True, allow_null=True)

    building = serializers.FloatField(
        read_only=True,
        allow_null=True,
        label=_('Building'),
        help_text=_('Quantity of this part currently being in production'),
    )

    scheduled_to_build = serializers.FloatField(
        read_only=True,
        allow_null=True,
        label=_('Scheduled to Build'),
        help_text=_('Outstanding quantity of this part scheduled to be built'),
    )

    in_stock = serializers.FloatField(
        read_only=True, allow_null=True, label=_('In Stock')
    )

    ordering = serializers.FloatField(
        read_only=True, allow_null=True, label=_('On Order')
    )

    required_for_build_orders = serializers.IntegerField(
        read_only=True, allow_null=True
    )

    required_for_sales_orders = serializers.IntegerField(
        read_only=True, allow_null=True
    )

    stock_item_count = serializers.IntegerField(
        read_only=True, allow_null=True, label=_('Stock Items')
    )

    revision_count = serializers.IntegerField(
        read_only=True, allow_null=True, label=_('Revisions')
    )

    total_in_stock = serializers.FloatField(
        read_only=True, allow_null=True, label=_('Total Stock')
    )

    external_stock = serializers.FloatField(
        read_only=True, allow_null=True, label=_('External Stock')
    )

    unallocated_stock = serializers.FloatField(
        read_only=True, allow_null=True, label=_('Unallocated Stock')
    )

    category_default_location = serializers.IntegerField(
        read_only=True, allow_null=True
    )

    variant_stock = serializers.FloatField(
        read_only=True, allow_null=True, label=_('Variant Stock')
    )

    minimum_stock = serializers.FloatField(
        required=False, label=_('Minimum Stock'), default=0
    )

    image = InvenTree.serializers.InvenTreeImageSerializerField(
        required=False, allow_null=True
    )
    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)
    starred = serializers.SerializerMethodField()

    # PrimaryKeyRelated fields (Note: enforcing field type here results in much faster queries, somehow...)
    category = serializers.PrimaryKeyRelatedField(
        queryset=PartCategory.objects.all(), required=False, allow_null=True
    )

    # Pricing fields
    pricing_min = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(
            source='pricing_data.overall_min', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )
    pricing_max = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(
            source='pricing_data.overall_max', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )
    pricing_updated = enable_filter(
        FilterableDateTimeField(
            source='pricing_data.updated', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )

    parameters = common.filters.enable_parameters_filter()

    tags = common.filters.enable_tags_filter()

    price_breaks = enable_filter(
        PartSalePriceSerializer(
            source='salepricebreaks', many=True, read_only=True, allow_null=True
        ),
        False,
        filter_name='price_breaks',
        prefetch_fields=['salepricebreaks'],
    )

    # Extra fields used only for creation of a new Part instance
    duplicate = DuplicatePartSerializer(
        label=_('Duplicate Part'),
        help_text=_('Copy initial data from another Part'),
        write_only=True,
        required=False,
    )

    initial_stock = InitialStockSerializer(
        label=_('Initial Stock'),
        help_text=_('Create Part with initial stock quantity'),
        write_only=True,
        required=False,
    )

    initial_supplier = InitialSupplierSerializer(
        label=_('Supplier Information'),
        help_text=_('Add initial supplier information for this part'),
        write_only=True,
        required=False,
    )

    copy_category_parameters = serializers.BooleanField(
        default=True,
        required=False,
        write_only=True,
        label=_('Copy Category Parameters'),
        help_text=_('Copy parameter templates from selected part category'),
    )

    # Allow selection of an existing part image file
    existing_image = serializers.CharField(
        label=_('Existing Image'),
        help_text=_('Filename of an existing part image'),
        write_only=True,
        required=False,
        allow_blank=False,
    )

    def validate_existing_image(self, img):
        """Validate the selected image file."""
        if not img:
            return img

        img = img.split(os.path.sep)[-1]

        # Ensure that the file actually exists
        img_path = os.path.join(part_helpers.get_part_image_directory(), img)

        if not os.path.exists(img_path) or not os.path.isfile(img_path):
            raise ValidationError(_('Image file does not exist'))

        return img

    @transaction.atomic
    def create(self, validated_data):
        """Custom method for creating a new Part instance using this serializer."""
        duplicate = validated_data.pop('duplicate', None)
        initial_stock = validated_data.pop('initial_stock', None)
        initial_supplier = validated_data.pop('initial_supplier', None)
        copy_category_parameters = validated_data.pop('copy_category_parameters', False)

        instance = super().create(validated_data)

        # Save user information
        if request := self.context.get('request'):
            instance.creation_user = request.user
            instance.save()

        # Copy data from original Part
        if duplicate:
            original = duplicate['part']

            if duplicate.get('copy_bom', False):
                instance.copy_bom_from(original)

            if duplicate.get('copy_notes', False):
                instance.notes = original.notes
                instance.save()

            if duplicate.get('copy_image', False):
                instance.image = original.image
                instance.save()

            if duplicate.get('copy_parameters', False):
                instance.copy_parameters_from(original)

            if duplicate.get('copy_tests', False):
                instance.copy_tests_from(original)

        # Duplicate parameter data from part category (and parents)
        if copy_category_parameters and instance.category is not None:
            # Get flattened list of parent categories
            instance.copy_category_parameters(instance.category)

        # Create initial stock entry
        if initial_stock:
            quantity = initial_stock['quantity']
            location = initial_stock.get('location', None) or instance.default_location

            if quantity > 0:
                stockitem = stock.models.StockItem(
                    part=instance, quantity=quantity, location=location
                )

                if request := self.context.get('request', None):
                    stockitem.save(user=request.user)

        # Create initial supplier information
        if initial_supplier:
            manufacturer = initial_supplier.get('manufacturer', None)
            mpn = initial_supplier.get('mpn', '')

            if manufacturer and mpn:
                manufacturer_part = company.models.ManufacturerPart.objects.create(
                    part=instance, manufacturer=manufacturer, MPN=mpn
                )
            else:
                manufacturer_part = None

            supplier = initial_supplier.get('supplier', None)
            sku = initial_supplier.get('sku', '')

            if supplier and sku:
                company.models.SupplierPart.objects.create(
                    part=instance,
                    supplier=supplier,
                    SKU=sku,
                    manufacturer_part=manufacturer_part,
                )

        return instance

    def save(self):
        """Save the Part instance."""
        super().save()

        part = self.instance
        data = self.validated_data

        existing_image = data.pop('existing_image', None)

        if existing_image:
            img_path = os.path.join(part_helpers.PART_IMAGE_DIR, existing_image)

            part.image = img_path
            part.save()

        # Check if an image was downloaded from a remote URL
        remote_img = getattr(self, 'remote_image_file', None)

        if remote_img and part:
            fmt = remote_img.format or 'PNG'
            buffer = io.BytesIO()
            remote_img.save(buffer, format=fmt)

            # Construct a simplified name for the image
            filename = f'part_{part.pk}_image.{fmt.lower()}'

            part.image.save(filename, ContentFile(buffer.getvalue()))

        return self.instance


class PartBomValidateSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for Part BOM information."""

    class Meta:
        """Metaclass options."""

        model = Part
        fields = [
            'pk',
            'bom_validated',
            'bom_checksum',
            'bom_checked_by',
            'bom_checked_by_detail',
            'bom_checked_date',
            'valid',
        ]

        read_only_fields = [
            'bom_validated',
            'bom_checksum',
            'bom_checked_by',
            'bom_checked_by_detail',
            'bom_checked_date',
        ]

    valid = serializers.BooleanField(
        write_only=True,
        default=False,
        required=False,
        label=_('Valid'),
        help_text=_('Validate entire Bill of Materials'),
    )

    bom_checked_by_detail = UserSerializer(
        source='bom_checked_by', many=False, read_only=True, allow_null=True
    )


class PartRequirementsSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for Part requirements."""

    class Meta:
        """Metaclass options."""

        model = Part
        fields = [
            'total_stock',
            'unallocated_stock',
            'can_build',
            'ordering',
            'building',
            'scheduled_to_build',
            'required_for_build_orders',
            'allocated_to_build_orders',
            'required_for_sales_orders',
            'allocated_to_sales_orders',
        ]

    total_stock = serializers.FloatField(read_only=True, label=_('Total Stock'))

    unallocated_stock = serializers.FloatField(
        source='available_stock', read_only=True, label=_('Available Stock')
    )

    can_build = serializers.FloatField(read_only=True, label=_('Can Build'))

    ordering = serializers.FloatField(
        source='on_order', read_only=True, label=_('On Order')
    )

    building = serializers.FloatField(
        read_only=True, label=_('In Production'), source='quantity_in_production'
    )

    scheduled_to_build = serializers.IntegerField(
        read_only=True, label=_('Scheduled to Build'), source='quantity_being_built'
    )

    required_for_build_orders = serializers.FloatField(
        source='required_build_order_quantity',
        read_only=True,
        label=_('Required for Build Orders'),
    )

    allocated_to_build_orders = serializers.FloatField(
        read_only=True,
        label=_('Allocated to Build Orders'),
        source='build_order_allocation_count',
    )

    required_for_sales_orders = serializers.FloatField(
        source='required_sales_order_quantity',
        read_only=True,
        label=_('Required for Sales Orders'),
    )

    allocated_to_sales_orders = serializers.SerializerMethodField(
        read_only=True, label=_('Allocated to Sales Orders')
    )

    def get_allocated_to_sales_orders(self, part) -> float:
        """Return the allocated sales order quantity."""
        return part.sales_order_allocation_count(include_variants=True, pending=True)


class PartStocktakeSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for the PartStocktake model."""

    class Meta:
        """Metaclass options."""

        model = PartStocktake
        fields = [
            'pk',
            'date',
            'part',
            'item_count',
            'quantity',
            'cost_min',
            'cost_min_currency',
            'cost_max',
            'cost_max_currency',
        ]

        read_only_fields = ['date', 'user']

    quantity = serializers.FloatField()

    cost_min = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    cost_min_currency = InvenTree.serializers.InvenTreeCurrencySerializer()

    cost_max = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    cost_max_currency = InvenTree.serializers.InvenTreeCurrencySerializer()

    def save(self):
        """Called when this serializer is saved."""
        data = self.validated_data

        # Add in user information automatically
        request = self.context.get('request')
        data['user'] = request.user if request else None
        return super().save()


@extend_schema_field(
    serializers.CharField(
        help_text=_('Select currency from available options')
        + '\n\n'
        + '\n'.join(
            f'* `{value}` - {label}'
            for value, label in common.currency.currency_code_mappings()
        )
        + "\n\nOther valid currencies may be found in the 'CURRENCY_CODES' global setting."
    )
)
class PartPricingCurrencySerializer(serializers.ChoiceField):
    """Serializer to allow annotating the schema to use String on currency fields."""


class PartPricingSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for Part pricing information."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartPricing
        fields = [
            'currency',
            'updated',
            'scheduled_for_update',
            'bom_cost_min',
            'bom_cost_max',
            'purchase_cost_min',
            'purchase_cost_max',
            'internal_cost_min',
            'internal_cost_max',
            'supplier_price_min',
            'supplier_price_max',
            'variant_cost_min',
            'variant_cost_max',
            'override_min',
            'override_min_currency',
            'override_max',
            'override_max_currency',
            'overall_min',
            'overall_max',
            'sale_price_min',
            'sale_price_max',
            'sale_history_min',
            'sale_history_max',
            'update',
        ]

    currency = serializers.CharField(allow_null=True, read_only=True)

    updated = serializers.DateTimeField(allow_null=True, read_only=True)

    scheduled_for_update = serializers.BooleanField(read_only=True)

    # Custom serializers
    bom_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    bom_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    purchase_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    purchase_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    internal_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    internal_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    supplier_price_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    supplier_price_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    variant_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    variant_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    override_min = InvenTree.serializers.InvenTreeMoneySerializer(
        label=_('Minimum Price'),
        help_text=_('Override calculated value for minimum price'),
        allow_null=True,
        read_only=False,
        required=False,
    )

    override_min_currency = PartPricingCurrencySerializer(
        label=_('Minimum price currency'),
        read_only=False,
        required=False,
        choices=common.currency.currency_code_mappings(),
    )

    override_max = InvenTree.serializers.InvenTreeMoneySerializer(
        label=_('Maximum Price'),
        help_text=_('Override calculated value for maximum price'),
        allow_null=True,
        read_only=False,
        required=False,
    )

    override_max_currency = PartPricingCurrencySerializer(
        label=_('Maximum price currency'),
        read_only=False,
        required=False,
        choices=common.currency.currency_code_mappings(),
    )

    overall_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    overall_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    sale_price_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    sale_price_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    sale_history_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    sale_history_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    update = serializers.BooleanField(
        write_only=True,
        label=_('Update'),
        help_text=_('Update pricing for this part'),
        default=False,
        required=False,
        allow_null=True,
    )

    def validate(self, data):
        """Validate supplied pricing data."""
        super().validate(data)

        # Check that override_min is not greater than override_max
        override_min = data.get('override_min', None)
        override_max = data.get('override_max', None)

        default_currency = common.currency.currency_code_default()

        if override_min is not None and override_max is not None:
            try:
                override_min = convert_money(override_min, default_currency)
                override_max = convert_money(override_max, default_currency)
            except MissingRate:
                raise ValidationError(
                    _(
                        f'Could not convert from provided currencies to {default_currency}'
                    )
                )

            if override_min > override_max:
                raise ValidationError({
                    'override_min': _(
                        'Minimum price must not be greater than maximum price'
                    ),
                    'override_max': _(
                        'Maximum price must not be less than minimum price'
                    ),
                })

        return data

    def save(self):
        """Called when the serializer is saved."""
        super().save()

        data = self.validated_data

        if data.get('update', False):
            # Update part pricing
            pricing = self.instance
            pricing.update_pricing()


class PartSerialNumberSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for Part serial number information."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = Part
        fields = ['latest', 'next']

    latest = serializers.CharField(
        source='get_latest_serial_number', read_only=True, allow_null=True
    )
    next = serializers.CharField(source='get_next_serial_number', read_only=True)


class PartRelationSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for a PartRelated model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartRelated
        fields = ['pk', 'part_1', 'part_1_detail', 'part_2', 'part_2_detail', 'note']

    part_1_detail = PartSerializer(source='part_1', read_only=True, many=False)
    part_2_detail = PartSerializer(source='part_2', read_only=True, many=False)


class PartStarSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for a PartStar object."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartStar
        fields = ['pk', 'part', 'partname', 'user', 'username']

    partname = serializers.CharField(source='part.full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)


class BomItemSubstituteSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for the BomItemSubstitute class."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = BomItemSubstitute
        fields = ['pk', 'bom_item', 'part', 'part_detail']
        list_serializer_class = FilterableListSerializer

    part_detail = PartBriefSerializer(
        source='part', read_only=True, many=False, pricing=False
    )


@register_importer()
class BomItemSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    DataImportExportSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for BomItem object."""

    import_exclude_fields = ['validated', 'substitutes']

    export_exclude_fields = ['substitutes']

    export_child_fields = [
        'sub_part_detail.name',
        'sub_part_detail.IPN',
        'sub_part_detail.description',
    ]

    class Meta:
        """Metaclass defining serializer fields."""

        model = BomItem
        fields = [
            'part',
            'sub_part',
            'reference',
            'quantity',
            'allow_variants',
            'inherited',
            'optional',
            'consumable',
            'setup_quantity',
            'attrition',
            'rounding_multiple',
            'note',
            'pk',
            'pricing_min',
            'pricing_max',
            'pricing_min_total',
            'pricing_max_total',
            'pricing_updated',
            'substitutes',
            'validated',
            # Annotated fields describing available quantity
            'available_stock',
            'available_substitute_stock',
            'available_variant_stock',
            'external_stock',
            # Annotated field describing quantity on order
            'on_order',
            # Annotated field describing quantity being built
            'building',
            # Annotate the total potential quantity we can build
            'can_build',
            # Optional detail fields
            'part_detail',
            'sub_part_detail',
            'category_detail',
        ]

    quantity = InvenTree.serializers.InvenTreeDecimalField(required=True)

    setup_quantity = InvenTree.serializers.InvenTreeDecimalField(required=False)

    attrition = InvenTree.serializers.InvenTreeDecimalField(required=False)

    rounding_multiple = InvenTree.serializers.InvenTreeDecimalField(
        required=False, allow_null=True
    )

    def validate_quantity(self, quantity):
        """Perform validation for the BomItem quantity field."""
        if quantity <= 0:
            raise serializers.ValidationError(_('Quantity must be greater than zero'))

        return quantity

    part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.filter(assembly=True),
        label=_('Assembly'),
        help_text=_('Select the parent assembly'),
    )

    substitutes = enable_filter(
        BomItemSubstituteSerializer(many=True, read_only=True, allow_null=True),
        False,
        filter_name='substitutes',
        prefetch_fields=[
            'substitutes',
            'substitutes__part',
            'substitutes__part__stock_items',
            'substitutes__part__pricing_data',
        ],
    )

    part_detail = enable_filter(
        PartBriefSerializer(
            source='part',
            label=_('Assembly'),
            many=False,
            read_only=True,
            allow_null=True,
        )
    )

    sub_part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.filter(component=True),
        label=_('Component'),
        help_text=_('Select the component part'),
    )

    sub_part_detail = enable_filter(
        PartBriefSerializer(
            source='sub_part',
            label=_('Component'),
            many=False,
            read_only=True,
            allow_null=True,
        ),
        True,
    )

    category_detail = enable_filter(
        CategorySerializer(
            source='sub_part.category',
            label=_('Category'),
            many=False,
            read_only=True,
            allow_null=True,
        ),
        False,
    )

    on_order = serializers.FloatField(
        label=_('On Order'), read_only=True, allow_null=True
    )

    building = serializers.FloatField(
        label=_('In Production'), read_only=True, allow_null=True
    )

    can_build = enable_filter(
        FilterableFloatField(label=_('Can Build'), read_only=True, allow_null=True),
        True,
    )

    # Cached pricing fields
    pricing_min = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(
            source='sub_part.pricing_data.overall_min', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )
    pricing_max = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(
            source='sub_part.pricing_data.overall_max', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )
    pricing_min_total = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True, read_only=True),
        True,
        filter_name='pricing',
    )
    pricing_max_total = enable_filter(
        InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True, read_only=True),
        True,
        filter_name='pricing',
    )
    pricing_updated = enable_filter(
        FilterableDateTimeField(
            source='sub_part.pricing_data.updated', allow_null=True, read_only=True
        ),
        True,
        filter_name='pricing',
    )

    # Annotated fields for available stock
    available_stock = serializers.FloatField(
        label=_('Available Stock'), read_only=True, allow_null=True
    )

    available_substitute_stock = serializers.FloatField(read_only=True, allow_null=True)
    available_variant_stock = serializers.FloatField(read_only=True, allow_null=True)

    external_stock = serializers.FloatField(read_only=True, allow_null=True)

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the BomItem queryset with extra information.

        Annotations:
            available_stock: The amount of stock available for the sub_part Part object
        """
        """
        Construct an "available stock" quantity:
        available_stock = total_stock - build_order_allocations - sales_order_allocations
        """

        # Prefetch related fields
        queryset = queryset.prefetch_related(
            'part',
            'part__category',
            'part__stock_items',
            'sub_part',
            'sub_part__builds',
            'sub_part__category',
            'sub_part__pricing_data',
            'sub_part__stock_items',
            'sub_part__stock_items__allocations',
            'sub_part__stock_items__sales_order_allocations',
        )

        # Annotate with the 'total pricing' information based on unit pricing and quantity
        queryset = queryset.annotate(
            pricing_min_total=ExpressionWrapper(
                F('quantity') * F('sub_part__pricing_data__overall_min'),
                output_field=models.DecimalField(),
            ),
            pricing_max_total=ExpressionWrapper(
                F('quantity') * F('sub_part__pricing_data__overall_max'),
                output_field=models.DecimalField(),
            ),
        )

        ref = 'sub_part__'

        # Annotate with the total "on order" amount for the sub-part
        queryset = queryset.annotate(
            on_order=part_filters.annotate_on_order_quantity(ref)
        )

        # Annotate with the total "building" amount for the sub-part
        queryset = queryset.annotate(
            building=part_filters.annotate_in_production_quantity(ref)
        )

        # Calculate 'external_stock'
        queryset = queryset.annotate(
            external_stock=part_filters.annotate_total_stock(
                reference=ref, filter=Q(location__external=True)
            )
        )

        # Annotate available stock and "can_build" quantities
        queryset = part_filters.annotate_bom_item_can_build(queryset)

        return queryset


@register_importer()
class CategoryParameterTemplateSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    DataImportExportSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for the PartCategoryParameterTemplate model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartCategoryParameterTemplate
        fields = [
            'pk',
            'category',
            'category_detail',
            'template',
            'template_detail',
            'default_value',
        ]

    template_detail = enable_filter(
        common.serializers.ParameterTemplateSerializer(
            source='template', many=False, read_only=True
        ),
        True,
        prefetch_fields=['template'],
    )

    category_detail = enable_filter(
        CategorySerializer(
            source='category', many=False, read_only=True, allow_null=True
        ),
        True,
        prefetch_fields=['category'],
    )


class PartCopyBOMSerializer(serializers.Serializer):
    """Serializer for copying a BOM from another part."""

    class Meta:
        """Metaclass defining serializer fields."""

        fields = [
            'part',
            'remove_existing',
            'copy_substitutes',
            'include_inherited',
            'skip_invalid',
        ]

    part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Part'),
        help_text=_('Select part to copy BOM from'),
    )

    def validate_part(self, part):
        """Check that a 'valid' part was selected."""
        return part

    remove_existing = serializers.BooleanField(
        label=_('Remove Existing Data'),
        help_text=_('Remove existing BOM items before copying'),
        default=True,
    )

    include_inherited = serializers.BooleanField(
        label=_('Include Inherited'),
        help_text=_('Include BOM items which are inherited from templated parts'),
        default=False,
    )

    skip_invalid = serializers.BooleanField(
        label=_('Skip Invalid Rows'),
        help_text=_('Enable this option to skip invalid rows'),
        default=False,
    )

    copy_substitutes = serializers.BooleanField(
        label=_('Copy Substitute Parts'),
        help_text=_('Copy substitute parts when duplicate BOM items'),
        default=True,
    )

    def save(self):
        """Actually duplicate the BOM."""
        base_part = self.context['part']

        data = self.validated_data

        base_part.copy_bom_from(
            data['part'],
            clear=data.get('remove_existing', True),
            skip_invalid=data.get('skip_invalid', False),
            include_inherited=data.get('include_inherited', False),
            copy_substitutes=data.get('copy_substitutes', True),
        )
