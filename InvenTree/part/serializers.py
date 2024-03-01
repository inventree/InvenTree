"""DRF data serializers for Part app."""

import imghdr
import io
import logging
import os
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models, transaction
from django.db.models import ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from rest_framework import serializers
from sql_util.utils import SubqueryCount, SubquerySum
from taggit.serializers import TagListSerializerField

import common.models
import common.settings
import company.models
import InvenTree.helpers
import InvenTree.serializers
import InvenTree.status
import part.filters
import part.helpers as part_helpers
import part.stocktake
import part.tasks
import stock.models
import users.models
from InvenTree.status_codes import BuildStatusGroups
from InvenTree.tasks import offload_task

from .models import (
    BomItem,
    BomItemSubstitute,
    Part,
    PartAttachment,
    PartCategory,
    PartCategoryParameterTemplate,
    PartInternalPriceBreak,
    PartParameter,
    PartParameterTemplate,
    PartPricing,
    PartRelated,
    PartSellPriceBreak,
    PartStar,
    PartStocktake,
    PartStocktakeReport,
    PartTestTemplate,
)

logger = logging.getLogger('inventree')


class CategorySerializer(InvenTree.serializers.InvenTreeModelSerializer):
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
            'url',
            'structural',
            'icon',
        ]

    def __init__(self, *args, **kwargs):
        """Optionally add or remove extra fields."""
        path_detail = kwargs.pop('path_detail', False)

        super().__init__(*args, **kwargs)

        if not path_detail:
            self.fields.pop('path')

    def get_starred(self, category) -> bool:
        """Return True if the category is directly "starred" by the current user."""
        return category in self.context.get('starred_categories', [])

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate extra information to the queryset."""
        # Annotate the number of 'parts' which exist in each category (including subcategories!)
        queryset = queryset.annotate(
            part_count=part.filters.annotate_category_parts(),
            subcategories=part.filters.annotate_sub_categories(),
        )

        return queryset

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    part_count = serializers.IntegerField(read_only=True, label=_('Parts'))

    subcategories = serializers.IntegerField(read_only=True, label=_('Subcategories'))

    level = serializers.IntegerField(read_only=True)

    starred = serializers.SerializerMethodField()

    path = serializers.ListField(
        child=serializers.DictField(), source='get_path', read_only=True
    )


class CategoryTree(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for PartCategory tree."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartCategory
        fields = ['pk', 'name', 'parent', 'icon', 'structural', 'subcategories']

    subcategories = serializers.IntegerField(label=_('Subcategories'), read_only=True)

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the queryset with the number of subcategories."""
        return queryset.annotate(subcategories=part.filters.annotate_sub_categories())


class PartAttachmentSerializer(InvenTree.serializers.InvenTreeAttachmentSerializer):
    """Serializer for the PartAttachment class."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartAttachment

        fields = InvenTree.serializers.InvenTreeAttachmentSerializer.attachment_fields([
            'part'
        ])


class PartTestTemplateSerializer(InvenTree.serializers.InvenTreeModelSerializer):
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


class PartSalePriceSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for sale prices for Part model."""

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

    image = serializers.URLField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class PartThumbSerializerUpdate(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for updating Part thumbnail."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = Part
        fields = ['image']

    def validate_image(self, value):
        """Check that file is an image."""
        validate = imghdr.what(value)
        if not validate:
            raise serializers.ValidationError('File is not an image')
        return value

    image = InvenTree.serializers.InvenTreeAttachmentSerializerField(required=True)


class PartParameterTemplateSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """JSON serializer for the PartParameterTemplate model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartParameterTemplate
        fields = ['pk', 'name', 'units', 'description', 'parts', 'checkbox', 'choices']

    parts = serializers.IntegerField(
        read_only=True,
        label=_('Parts'),
        help_text=_('Number of parts using this template'),
    )

    @staticmethod
    def annotate_queryset(queryset):
        """Annotate the queryset with the number of parts which use each parameter template."""
        return queryset.annotate(parts=SubqueryCount('instances'))


class PartBriefSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for Part (brief detail)."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = Part
        fields = [
            'pk',
            'IPN',
            'barcode_hash',
            'default_location',
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
            'trackable',
            'virtual',
            'units',
            'pricing_min',
            'pricing_max',
        ]

        read_only_fields = ['barcode_hash']

    def __init__(self, *args, **kwargs):
        """Custom initialization routine for the PartBrief serializer."""
        pricing = kwargs.pop('pricing', True)

        super().__init__(*args, **kwargs)

        if not pricing:
            self.fields.pop('pricing_min')
            self.fields.pop('pricing_max')

    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)

    # Pricing fields
    pricing_min = InvenTree.serializers.InvenTreeMoneySerializer(
        source='pricing_data.overall_min', allow_null=True, read_only=True
    )
    pricing_max = InvenTree.serializers.InvenTreeMoneySerializer(
        source='pricing_data.overall_max', allow_null=True, read_only=True
    )


class PartParameterSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """JSON serializers for the PartParameter model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartParameter
        fields = [
            'pk',
            'part',
            'part_detail',
            'template',
            'template_detail',
            'data',
            'data_numeric',
        ]

    def __init__(self, *args, **kwargs):
        """Custom initialization method for the serializer.

        Allows us to optionally include or exclude particular information
        """
        template_detail = kwargs.pop('template_detail', True)
        part_detail = kwargs.pop('part_detail', False)

        super().__init__(*args, **kwargs)

        if not part_detail:
            self.fields.pop('part_detail')

        if not template_detail:
            self.fields.pop('template_detail')

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    template_detail = PartParameterTemplateSerializer(
        source='template', many=False, read_only=True
    )


class PartSetCategorySerializer(serializers.Serializer):
    """Serializer for changing PartCategory for multiple Part objects."""

    class Meta:
        """Metaclass options."""

        fields = ['parts', 'category']

    parts = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.all(),
        many=True,
        required=True,
        allow_null=False,
        label=_('Parts'),
    )

    def validate_parts(self, parts):
        """Validate the selected parts."""
        if len(parts) == 0:
            raise serializers.ValidationError(_('No parts selected'))

        return parts

    category = serializers.PrimaryKeyRelatedField(
        queryset=PartCategory.objects.filter(structural=False),
        many=False,
        required=True,
        allow_null=False,
        label=_('Category'),
        help_text=_('Select category'),
    )

    @transaction.atomic
    def save(self):
        """Save the serializer to change the location of the selected parts."""
        data = self.validated_data
        parts = data['parts']
        category = data['category']

        parts_to_save = []

        for p in parts:
            if p.category == category:
                continue

            p.category = category
            parts_to_save.append(p)

        Part.objects.bulk_update(parts_to_save, ['category'])


class DuplicatePartSerializer(serializers.Serializer):
    """Serializer for specifying options when duplicating a Part.

    The fields in this serializer control how the Part is duplicated.
    """

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


class InitialStockSerializer(serializers.Serializer):
    """Serializer for creating initial stock quantity."""

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


class PartSerializer(
    InvenTree.serializers.RemoteImageMixin,
    InvenTree.serializers.InvenTreeTagModelSerializer,
):
    """Serializer for complete detail information of a part.

    Used when displaying all details of a single component.
    """

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
            'component',
            'creation_date',
            'creation_user',
            'default_expiry',
            'default_location',
            'default_supplier',
            'description',
            'full_name',
            'image',
            'remote_image',
            'existing_image',
            'IPN',
            'is_template',
            'keywords',
            'last_stocktake',
            'link',
            'minimum_stock',
            'name',
            'notes',
            'parameters',
            'pk',
            'purchaseable',
            'revision',
            'salable',
            'starred',
            'thumbnail',
            'trackable',
            'units',
            'variant_of',
            'virtual',
            'pricing_min',
            'pricing_max',
            'responsible',
            # Annotated fields
            'allocated_to_build_orders',
            'allocated_to_sales_orders',
            'building',
            'in_stock',
            'ordering',
            'required_for_build_orders',
            'required_for_sales_orders',
            'stock_item_count',
            'suppliers',
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

        read_only_fields = ['barcode_hash', 'creation_date']

    tags = TagListSerializerField(required=False)

    def __init__(self, *args, **kwargs):
        """Custom initialization method for PartSerializer.

        - Allows us to optionally pass extra fields based on the query.
        """
        self.starred_parts = kwargs.pop('starred_parts', [])
        category_detail = kwargs.pop('category_detail', False)
        parameters = kwargs.pop('parameters', False)
        create = kwargs.pop('create', False)
        pricing = kwargs.pop('pricing', True)
        path_detail = kwargs.pop('path_detail', False)

        super().__init__(*args, **kwargs)

        if not category_detail:
            self.fields.pop('category_detail')

        if not parameters:
            self.fields.pop('parameters')

        if not path_detail:
            self.fields.pop('category_path')

        if not create:
            # These fields are only used for the LIST API endpoint
            for f in self.skip_create_fields():
                # Fields required for certain operations, but are not part of the model
                if f in ['remote_image', 'existing_image']:
                    continue
                self.fields.pop(f)

        if not pricing:
            self.fields.pop('pricing_min')
            self.fields.pop('pricing_max')

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
        # Annotate with the total number of stock items
        queryset = queryset.annotate(stock_item_count=SubqueryCount('stock_items'))

        # Annotate with the total variant stock quantity
        variant_query = part.filters.variant_stock_query()

        queryset = queryset.annotate(
            variant_stock=part.filters.annotate_variant_quantity(
                variant_query, reference='quantity'
            )
        )

        # Filter to limit builds to "active"
        build_filter = Q(status__in=BuildStatusGroups.ACTIVE_CODES)

        # Annotate with the total 'building' quantity
        queryset = queryset.annotate(
            building=Coalesce(
                SubquerySum('builds__quantity', filter=build_filter),
                Decimal(0),
                output_field=models.DecimalField(),
            )
        )

        # Annotate with the number of 'suppliers'
        queryset = queryset.annotate(
            suppliers=Coalesce(
                SubqueryCount('supplier_parts'),
                Decimal(0),
                output_field=models.DecimalField(),
            )
        )

        # TODO: This could do with some refactoring
        # TODO: Note that BomItemSerializer and BuildLineSerializer have very similar code

        queryset = queryset.annotate(
            ordering=part.filters.annotate_on_order_quantity(),
            in_stock=part.filters.annotate_total_stock(),
            allocated_to_sales_orders=part.filters.annotate_sales_order_allocations(),
            allocated_to_build_orders=part.filters.annotate_build_order_allocations(),
        )

        # Annotate the queryset with the 'total_in_stock' quantity
        # This is the 'in_stock' quantity summed with the 'variant_stock' quantity
        queryset = queryset.annotate(
            total_in_stock=ExpressionWrapper(
                F('in_stock') + F('variant_stock'), output_field=models.DecimalField()
            )
        )

        queryset = queryset.annotate(
            external_stock=part.filters.annotate_total_stock(
                filter=Q(location__external=True)
            )
        )

        # Annotate with the total 'available stock' quantity
        # This is the current stock, minus any allocations
        queryset = queryset.annotate(
            unallocated_stock=ExpressionWrapper(
                F('total_in_stock')
                - F('allocated_to_sales_orders')
                - F('allocated_to_build_orders'),
                output_field=models.DecimalField(),
            )
        )

        # Annotate with the total 'required for builds' quantity
        queryset = queryset.annotate(
            required_for_build_orders=part.filters.annotate_build_order_requirements(),
            required_for_sales_orders=part.filters.annotate_sales_order_requirements(),
        )

        return queryset

    def get_starred(self, part) -> bool:
        """Return "true" if the part is starred by the current user."""
        return part in self.starred_parts

    # Extra detail for the category
    category_detail = CategorySerializer(source='category', many=False, read_only=True)

    category_path = serializers.ListField(
        child=serializers.DictField(), source='category.get_path', read_only=True
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

    # Annotated fields
    allocated_to_build_orders = serializers.FloatField(read_only=True)
    allocated_to_sales_orders = serializers.FloatField(read_only=True)
    building = serializers.FloatField(read_only=True)
    in_stock = serializers.FloatField(read_only=True)
    ordering = serializers.FloatField(read_only=True, label=_('On Order'))
    required_for_build_orders = serializers.IntegerField(read_only=True)
    required_for_sales_orders = serializers.IntegerField(read_only=True)
    stock_item_count = serializers.IntegerField(read_only=True, label=_('Stock Items'))
    suppliers = serializers.IntegerField(read_only=True, label=_('Suppliers'))
    total_in_stock = serializers.FloatField(read_only=True, label=_('Total Stock'))
    external_stock = serializers.FloatField(read_only=True, label=_('External Stock'))
    unallocated_stock = serializers.FloatField(
        read_only=True, label=_('Unallocated Stock')
    )
    variant_stock = serializers.FloatField(read_only=True, label=_('Variant Stock'))

    minimum_stock = serializers.FloatField()

    image = InvenTree.serializers.InvenTreeImageSerializerField(
        required=False, allow_null=True
    )
    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)
    starred = serializers.SerializerMethodField()

    # PrimaryKeyRelated fields (Note: enforcing field type here results in much faster queries, somehow...)
    category = serializers.PrimaryKeyRelatedField(queryset=PartCategory.objects.all())

    # Pricing fields
    pricing_min = InvenTree.serializers.InvenTreeMoneySerializer(
        source='pricing_data.overall_min', allow_null=True, read_only=True
    )
    pricing_max = InvenTree.serializers.InvenTreeMoneySerializer(
        source='pricing_data.overall_max', allow_null=True, read_only=True
    )

    parameters = PartParameterSerializer(many=True, read_only=True)

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
        if self.context['request']:
            instance.creation_user = self.context['request'].user
            instance.save()

        # Copy data from original Part
        if duplicate:
            original = duplicate['part']

            if duplicate['copy_bom']:
                instance.copy_bom_from(original)

            if duplicate['copy_notes']:
                instance.notes = original.notes
                instance.save()

            if duplicate['copy_image']:
                instance.image = original.image
                instance.save()

            if duplicate['copy_parameters']:
                instance.copy_parameters_from(original)

        # Duplicate parameter data from part category (and parents)
        if copy_category_parameters and instance.category is not None:
            # Get flattened list of parent categories
            categories = instance.category.get_ancestors(include_self=True)

            # All parameter templates within these categories
            templates = PartCategoryParameterTemplate.objects.filter(
                category__in=categories
            )

            for template in templates:
                # First ensure that the part doesn't have that parameter
                if PartParameter.objects.filter(
                    part=instance, template=template.parameter_template
                ).exists():
                    continue

                try:
                    PartParameter.create(
                        part=instance,
                        template=template.parameter_template,
                        data=template.default_value,
                        save=True,
                    )
                except IntegrityError:
                    logger.exception(
                        'Could not create new PartParameter for part %s', instance
                    )

        # Create initial stock entry
        if initial_stock:
            quantity = initial_stock['quantity']
            location = initial_stock.get('location', None) or instance.default_location

            if quantity > 0:
                stockitem = stock.models.StockItem(
                    part=instance, quantity=quantity, location=location
                )

                stockitem.save(user=self.context['request'].user)

        # Create initial supplier information
        if initial_supplier:
            manufacturer = initial_supplier.get('manufacturer', None)
            mpn = initial_supplier.get('mpn', '')

            if manufacturer and mpn:
                manu_part = company.models.ManufacturerPart.objects.create(
                    part=instance, manufacturer=manufacturer, MPN=mpn
                )
            else:
                manu_part = None

            supplier = initial_supplier.get('supplier', None)
            sku = initial_supplier.get('sku', '')

            if supplier and sku:
                company.models.SupplierPart.objects.create(
                    part=instance,
                    supplier=supplier,
                    SKU=sku,
                    manufacturer_part=manu_part,
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
            'note',
            'user',
            'user_detail',
        ]

        read_only_fields = ['date', 'user']

    quantity = serializers.FloatField()

    user_detail = InvenTree.serializers.UserSerializer(
        source='user', read_only=True, many=False
    )

    cost_min = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    cost_min_currency = InvenTree.serializers.InvenTreeCurrencySerializer()

    cost_max = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    cost_max_currency = InvenTree.serializers.InvenTreeCurrencySerializer()

    def save(self):
        """Called when this serializer is saved."""
        data = self.validated_data

        # Add in user information automatically
        request = self.context['request']
        data['user'] = request.user

        super().save()


class PartStocktakeReportSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for stocktake report class."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = PartStocktakeReport
        fields = ['pk', 'date', 'report', 'part_count', 'user', 'user_detail']

    user_detail = InvenTree.serializers.UserSerializer(
        source='user', read_only=True, many=False
    )

    report = InvenTree.serializers.InvenTreeAttachmentSerializerField(read_only=True)


class PartStocktakeReportGenerateSerializer(serializers.Serializer):
    """Serializer class for manually generating a new PartStocktakeReport via the API."""

    part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.all(),
        required=False,
        allow_null=True,
        label=_('Part'),
        help_text=_(
            'Limit stocktake report to a particular part, and any variant parts'
        ),
    )

    category = serializers.PrimaryKeyRelatedField(
        queryset=PartCategory.objects.all(),
        required=False,
        allow_null=True,
        label=_('Category'),
        help_text=_(
            'Limit stocktake report to a particular part category, and any child categories'
        ),
    )

    location = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockLocation.objects.all(),
        required=False,
        allow_null=True,
        label=_('Location'),
        help_text=_(
            'Limit stocktake report to a particular stock location, and any child locations'
        ),
    )

    exclude_external = serializers.BooleanField(
        default=True,
        label=_('Exclude External Stock'),
        help_text=_('Exclude stock items in external locations'),
    )

    generate_report = serializers.BooleanField(
        default=True,
        label=_('Generate Report'),
        help_text=_('Generate report file containing calculated stocktake data'),
    )

    update_parts = serializers.BooleanField(
        default=True,
        label=_('Update Parts'),
        help_text=_('Update specified parts with calculated stocktake data'),
    )

    def validate(self, data):
        """Custom validation for this serializer."""
        # Stocktake functionality must be enabled
        if not common.models.InvenTreeSetting.get_setting('STOCKTAKE_ENABLE', False):
            raise serializers.ValidationError(
                _('Stocktake functionality is not enabled')
            )

        # Check that background worker is running
        if not InvenTree.status.is_worker_running():
            raise serializers.ValidationError(_('Background worker check failed'))

        return data

    def save(self):
        """Saving this serializer instance requests generation of a new stocktake report."""
        data = self.validated_data
        user = self.context['request'].user

        # Generate a new report
        offload_task(
            part.stocktake.generate_stocktake_report,
            force_async=True,
            user=user,
            part=data.get('part', None),
            category=data.get('category', None),
            location=data.get('location', None),
            exclude_external=data.get('exclude_external', True),
            generate_report=data.get('generate_report', True),
            update_parts=data.get('update_parts', True),
        )


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

    override_min_currency = serializers.ChoiceField(
        label=_('Minimum price currency'),
        read_only=False,
        required=False,
        choices=common.settings.currency_code_mappings(),
    )

    override_max = InvenTree.serializers.InvenTreeMoneySerializer(
        label=_('Maximum Price'),
        help_text=_('Override calculated value for maximum price'),
        allow_null=True,
        read_only=False,
        required=False,
    )

    override_max_currency = serializers.ChoiceField(
        label=_('Maximum price currency'),
        read_only=False,
        required=False,
        choices=common.settings.currency_code_mappings(),
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

        default_currency = common.settings.currency_code_default()

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

        # Update part pricing
        pricing = self.instance
        pricing.update_pricing()


class PartRelationSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for a PartRelated model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartRelated
        fields = ['pk', 'part_1', 'part_1_detail', 'part_2', 'part_2_detail']

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

    part_detail = PartBriefSerializer(
        source='part', read_only=True, many=False, pricing=False
    )


class BomItemSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for BomItem object."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = BomItem
        fields = [
            'allow_variants',
            'inherited',
            'note',
            'optional',
            'consumable',
            'overage',
            'pk',
            'part',
            'part_detail',
            'pricing_min',
            'pricing_max',
            'quantity',
            'reference',
            'sub_part',
            'sub_part_detail',
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
        ]

    def __init__(self, *args, **kwargs):
        """Determine if extra detail fields are to be annotated on this serializer.

        - part_detail and sub_part_detail serializers are only included if requested.
        - This saves a bunch of database requests
        """
        part_detail = kwargs.pop('part_detail', False)
        sub_part_detail = kwargs.pop('sub_part_detail', False)
        pricing = kwargs.pop('pricing', True)

        super().__init__(*args, **kwargs)

        if not part_detail:
            self.fields.pop('part_detail')

        if not sub_part_detail:
            self.fields.pop('sub_part_detail')

        if not pricing:
            self.fields.pop('pricing_min')
            self.fields.pop('pricing_max')

    quantity = InvenTree.serializers.InvenTreeDecimalField(required=True)

    def validate_quantity(self, quantity):
        """Perform validation for the BomItem quantity field."""
        if quantity <= 0:
            raise serializers.ValidationError(_('Quantity must be greater than zero'))

        return quantity

    part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.filter(assembly=True)
    )

    substitutes = BomItemSubstituteSerializer(many=True, read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    sub_part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.filter(component=True)
    )

    sub_part_detail = PartBriefSerializer(source='sub_part', many=False, read_only=True)

    on_order = serializers.FloatField(label=_('On Order'), read_only=True)

    building = serializers.FloatField(label=_('In Production'), read_only=True)

    # Cached pricing fields
    pricing_min = InvenTree.serializers.InvenTreeMoneySerializer(
        source='sub_part.pricing.overall_min', allow_null=True, read_only=True
    )
    pricing_max = InvenTree.serializers.InvenTreeMoneySerializer(
        source='sub_part.pricing.overall_max', allow_null=True, read_only=True
    )

    # Annotated fields for available stock
    available_stock = serializers.FloatField(label=_('Available Stock'), read_only=True)

    available_substitute_stock = serializers.FloatField(read_only=True)
    available_variant_stock = serializers.FloatField(read_only=True)

    external_stock = serializers.FloatField(read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        """Prefetch against the provided queryset to speed up database access."""
        queryset = queryset.prefetch_related('part')
        queryset = queryset.prefetch_related('part__category')
        queryset = queryset.prefetch_related('part__stock_items')

        queryset = queryset.prefetch_related('sub_part')
        queryset = queryset.prefetch_related('sub_part__category')

        queryset = queryset.prefetch_related(
            'sub_part__stock_items',
            'sub_part__stock_items__allocations',
            'sub_part__stock_items__sales_order_allocations',
        )

        queryset = queryset.prefetch_related(
            'substitutes', 'substitutes__part__stock_items'
        )

        queryset = queryset.prefetch_related('sub_part__builds')

        return queryset

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

        ref = 'sub_part__'

        # Annotate with the total "on order" amount for the sub-part
        queryset = queryset.annotate(
            on_order=part.filters.annotate_on_order_quantity(ref)
        )

        # Annotate with the total "building" amount for the sub-part
        queryset = queryset.annotate(
            building=Coalesce(
                SubquerySum(
                    'sub_part__builds__quantity',
                    filter=Q(status__in=BuildStatusGroups.ACTIVE_CODES),
                ),
                Decimal(0),
                output_field=models.DecimalField(),
            )
        )

        # Calculate "total stock" for the referenced sub_part
        # Calculate the "build_order_allocations" for the sub_part
        # Note that these fields are only aliased, not annotated
        queryset = queryset.alias(
            total_stock=part.filters.annotate_total_stock(reference=ref),
            allocated_to_sales_orders=part.filters.annotate_sales_order_allocations(
                reference=ref
            ),
            allocated_to_build_orders=part.filters.annotate_build_order_allocations(
                reference=ref
            ),
        )

        # Calculate 'available_stock' based on previously annotated fields
        queryset = queryset.annotate(
            available_stock=ExpressionWrapper(
                F('total_stock')
                - F('allocated_to_sales_orders')
                - F('allocated_to_build_orders'),
                output_field=models.DecimalField(),
            )
        )

        # Calculate 'external_stock'
        queryset = queryset.annotate(
            external_stock=part.filters.annotate_total_stock(
                reference=ref, filter=Q(location__external=True)
            )
        )

        ref = 'substitutes__part__'

        # Extract similar information for any 'substitute' parts
        queryset = queryset.alias(
            substitute_stock=part.filters.annotate_total_stock(reference=ref),
            substitute_build_allocations=part.filters.annotate_build_order_allocations(
                reference=ref
            ),
            substitute_sales_allocations=part.filters.annotate_sales_order_allocations(
                reference=ref
            ),
        )

        # Calculate 'available_substitute_stock' field
        queryset = queryset.annotate(
            available_substitute_stock=ExpressionWrapper(
                F('substitute_stock')
                - F('substitute_build_allocations')
                - F('substitute_sales_allocations'),
                output_field=models.DecimalField(),
            )
        )

        # Annotate the queryset with 'available variant stock' information
        variant_stock_query = part.filters.variant_stock_query(reference='sub_part__')

        queryset = queryset.alias(
            variant_stock_total=part.filters.annotate_variant_quantity(
                variant_stock_query, reference='quantity'
            ),
            variant_bo_allocations=part.filters.annotate_variant_quantity(
                variant_stock_query, reference='sales_order_allocations__quantity'
            ),
            variant_so_allocations=part.filters.annotate_variant_quantity(
                variant_stock_query, reference='allocations__quantity'
            ),
        )

        queryset = queryset.annotate(
            available_variant_stock=ExpressionWrapper(
                F('variant_stock_total')
                - F('variant_bo_allocations')
                - F('variant_so_allocations'),
                output_field=FloatField(),
            )
        )

        return queryset


class CategoryParameterTemplateSerializer(
    InvenTree.serializers.InvenTreeModelSerializer
):
    """Serializer for the PartCategoryParameterTemplate model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartCategoryParameterTemplate
        fields = [
            'pk',
            'category',
            'category_detail',
            'parameter_template',
            'parameter_template_detail',
            'default_value',
        ]

    parameter_template_detail = PartParameterTemplateSerializer(
        source='parameter_template', many=False, read_only=True
    )

    category_detail = CategorySerializer(source='category', many=False, read_only=True)


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


class BomImportUploadSerializer(InvenTree.serializers.DataFileUploadSerializer):
    """Serializer for uploading a file and extracting data from it."""

    TARGET_MODEL = BomItem

    class Meta:
        """Metaclass defining serializer fields."""

        fields = ['data_file', 'part', 'clear_existing_bom']

    part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.all(), required=True, allow_null=False, many=False
    )

    clear_existing_bom = serializers.BooleanField(
        label=_('Clear Existing BOM'),
        help_text=_('Delete existing BOM items before uploading'),
    )

    def save(self):
        """The uploaded data file has been validated, accept the submitted data."""
        data = self.validated_data

        if data.get('clear_existing_bom', False):
            part = data['part']

            with transaction.atomic():
                part.bom_items.all().delete()


class BomImportExtractSerializer(InvenTree.serializers.DataFileExtractSerializer):
    """Serializer class for exatracting BOM data from an uploaded file.

    The parent class DataFileExtractSerializer does most of the heavy lifting here.
    """

    TARGET_MODEL = BomItem

    def validate_extracted_columns(self):
        """Validate that the extracted columns are correct."""
        super().validate_extracted_columns()

        part_columns = ['part', 'part_name', 'part_ipn', 'part_id']

        if not any(col in self.columns for col in part_columns):
            # At least one part column is required!
            raise serializers.ValidationError(_('No part column specified'))

    @staticmethod
    def process_row(row):
        """Process a single row from the loaded BOM file."""
        # Skip any rows which are at a lower "level"
        level = row.get('level', None)

        if level is not None:
            try:
                level = int(level)
                if level != 1:
                    # Skip this row
                    return None
            except Exception:
                pass

        # Attempt to extract a valid part based on the provided data
        part_id = row.get('part_id', row.get('part', None))
        part_name = row.get('part_name', row.get('part', None))
        part_ipn = row.get('part_ipn', None)

        part = None

        if part_id is not None:
            try:
                part = Part.objects.get(pk=part_id)
            except (ValueError, Part.DoesNotExist):
                pass

        # No direct match, where else can we look?
        if part is None and (part_name or part_ipn):
            queryset = Part.objects.all()

            if part_name:
                queryset = queryset.filter(name=part_name)

            if part_ipn:
                queryset = queryset.filter(IPN=part_ipn)

            if queryset.exists():
                if queryset.count() == 1:
                    part = queryset.first()
                else:
                    row['errors']['part'] = _('Multiple matching parts found')

        if part is None:
            row['errors']['part'] = _('No matching part found')
        else:
            if not part.component:
                row['errors']['part'] = _('Part is not designated as a component')

        # Update the 'part' value in the row
        row['part'] = part.pk if part is not None else None

        # Check the provided 'quantity' value
        quantity = row.get('quantity', None)

        if quantity is None:
            row['errors']['quantity'] = _('Quantity not provided')
        else:
            try:
                quantity = Decimal(quantity)

                if quantity <= 0:
                    row['errors']['quantity'] = _('Quantity must be greater than zero')
            except Exception:
                row['errors']['quantity'] = _('Invalid quantity')

        return row


class BomImportSubmitSerializer(serializers.Serializer):
    """Serializer for uploading a BOM against a specified part.

    A "BOM" is a set of BomItem objects which are to be validated together as a set
    """

    items = BomItemSerializer(many=True, required=True)

    def validate(self, data):
        """Validate the submitted BomItem data.

        At least one line (BomItem) is required
        """
        items = data['items']

        if len(items) == 0:
            raise serializers.ValidationError(_('At least one BOM item is required'))

        data = super().validate(data)

        return data

    def save(self):
        """POST: Perform final save of submitted BOM data.

        Actions:
        - By this stage each line in the BOM has been validated
        - Individually 'save' (create) each BomItem line
        """
        data = self.validated_data

        items = data['items']

        bom_items = []

        try:
            for item in items:
                part = item['part']
                sub_part = item['sub_part']

                # Ignore duplicate BOM items
                if BomItem.objects.filter(part=part, sub_part=sub_part).exists():
                    continue

                bom_items.append(BomItem(**item))

            if len(bom_items) > 0:
                logger.info('Importing %s BOM items', len(bom_items))
                BomItem.objects.bulk_create(bom_items)

        except Exception as e:
            raise serializers.ValidationError(detail=serializers.as_serializer_error(e))
