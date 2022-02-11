"""
JSON serializers for Part app
"""

import imghdr
from decimal import Decimal
import os
import tablib

from django.urls import reverse_lazy
from django.db import models, transaction
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from sql_util.utils import SubqueryCount, SubquerySum
from djmoney.contrib.django_rest_framework import MoneyField

from InvenTree.serializers import (InvenTreeAttachmentSerializerField,
                                   InvenTreeDecimalField,
                                   InvenTreeImageSerializerField,
                                   InvenTreeModelSerializer,
                                   InvenTreeAttachmentSerializer,
                                   InvenTreeMoneySerializer)

from InvenTree.status_codes import BuildStatus, PurchaseOrderStatus
from stock.models import StockItem

from .models import (BomItem, BomItemSubstitute,
                     Part, PartAttachment, PartCategory, PartRelated,
                     PartParameter, PartParameterTemplate, PartSellPriceBreak,
                     PartStar, PartTestTemplate, PartCategoryParameterTemplate,
                     PartInternalPriceBreak)


class CategorySerializer(InvenTreeModelSerializer):
    """ Serializer for PartCategory """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    def get_starred(self, category):
        """
        Return True if the category is directly "starred" by the current user
        """

        return category in self.context.get('starred_categories', [])

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    parts = serializers.IntegerField(source='item_count', read_only=True)

    level = serializers.IntegerField(read_only=True)

    starred = serializers.SerializerMethodField()

    class Meta:
        model = PartCategory
        fields = [
            'pk',
            'name',
            'description',
            'default_location',
            'default_keywords',
            'level',
            'parent',
            'parts',
            'pathstring',
            'starred',
            'url',
        ]


class CategoryTree(InvenTreeModelSerializer):
    """
    Serializer for PartCategory tree
    """

    class Meta:
        model = PartCategory
        fields = [
            'pk',
            'name',
            'parent',
        ]


class PartAttachmentSerializer(InvenTreeAttachmentSerializer):
    """
    Serializer for the PartAttachment class
    """

    class Meta:
        model = PartAttachment

        fields = [
            'pk',
            'part',
            'attachment',
            'filename',
            'link',
            'comment',
            'upload_date',
        ]

        read_only_fields = [
            'upload_date',
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

    quantity = InvenTreeDecimalField()

    price = InvenTreeMoneySerializer(
        allow_null=True
    )

    price_string = serializers.CharField(source='price', read_only=True)

    class Meta:
        model = PartSellPriceBreak
        fields = [
            'pk',
            'part',
            'quantity',
            'price',
            'price_string',
        ]


class PartInternalPriceSerializer(InvenTreeModelSerializer):
    """
    Serializer for internal prices for Part model.
    """

    quantity = InvenTreeDecimalField()

    price = InvenTreeMoneySerializer(
        allow_null=True
    )

    price_string = serializers.CharField(source='price', read_only=True)

    class Meta:
        model = PartInternalPriceBreak
        fields = [
            'pk',
            'part',
            'quantity',
            'price',
            'price_string',
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
            'stock',
            'trackable',
            'virtual',
            'units',
        ]


class PartSerializer(InvenTreeModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    def get_api_url(self):
        return reverse_lazy('api-part-list')

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
    def annotate_queryset(queryset):
        """
        Add some extra annotations to the queryset,
        performing database queries as efficiently as possible,
        to reduce database trips.
        """

        # TODO: Update the "in_stock" annotation to include stock for variants of the part
        # Ref: https://github.com/inventree/InvenTree/issues/2240

        # Annotate with the total 'in stock' quantity
        queryset = queryset.annotate(
            in_stock=Coalesce(
                SubquerySum('stock_items__quantity', filter=StockItem.IN_STOCK_FILTER),
                Decimal(0),
                output_field=models.DecimalField(),
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
                output_field=models.DecimalField(),
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
                output_field=models.DecimalField(),
            ) - Coalesce(
                SubquerySum('supplier_parts__purchase_order_line_items__received', filter=order_filter),
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
            ),
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
    suppliers = serializers.IntegerField(read_only=True)

    image = InvenTreeImageSerializerField(required=False, allow_null=True)
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
            'default_expiry',
            'default_location',
            'default_supplier',
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
            'suppliers',
            'thumbnail',
            'trackable',
            'units',
            # 'used_in',
            'variant_of',
            'virtual',
        ]


class PartRelationSerializer(InvenTreeModelSerializer):
    """
    Serializer for a PartRelated model
    """

    part_1_detail = PartSerializer(source='part_1', read_only=True, many=False)
    part_2_detail = PartSerializer(source='part_2', read_only=True, many=False)

    class Meta:
        model = PartRelated
        fields = [
            'pk',
            'part_1',
            'part_1_detail',
            'part_2',
            'part_2_detail',
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


class BomItemSubstituteSerializer(InvenTreeModelSerializer):
    """
    Serializer for the BomItemSubstitute class
    """

    part_detail = PartBriefSerializer(source='part', read_only=True, many=False)

    class Meta:
        model = BomItemSubstitute
        fields = [
            'pk',
            'bom_item',
            'part',
            'part_detail',
        ]


class BomItemSerializer(InvenTreeModelSerializer):
    """
    Serializer for BomItem object
    """

    price_range = serializers.CharField(read_only=True)

    quantity = InvenTreeDecimalField(required=True)

    def validate_quantity(self, quantity):
        if quantity <= 0:
            raise serializers.ValidationError(_("Quantity must be greater than zero"))

        return quantity

    part = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(assembly=True))

    substitutes = BomItemSubstituteSerializer(many=True, read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    sub_part = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(component=True))

    sub_part_detail = PartBriefSerializer(source='sub_part', many=False, read_only=True)

    validated = serializers.BooleanField(read_only=True, source='is_line_valid')

    purchase_price_min = MoneyField(max_digits=19, decimal_places=4, read_only=True)

    purchase_price_max = MoneyField(max_digits=19, decimal_places=4, read_only=True)

    purchase_price_avg = serializers.SerializerMethodField()

    purchase_price_range = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        # part_detail and sub_part_detail serializers are only included if requested.
        # This saves a bunch of database requests

        part_detail = kwargs.pop('part_detail', False)
        sub_part_detail = kwargs.pop('sub_part_detail', False)
        include_pricing = kwargs.pop('include_pricing', False)

        super(BomItemSerializer, self).__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if sub_part_detail is not True:
            self.fields.pop('sub_part_detail')

        if not include_pricing:
            # Remove all pricing related fields
            self.fields.pop('price_range')
            self.fields.pop('purchase_price_min')
            self.fields.pop('purchase_price_max')
            self.fields.pop('purchase_price_avg')
            self.fields.pop('purchase_price_range')

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

    def get_purchase_price_range(self, obj):
        """ Return purchase price range """

        try:
            purchase_price_min = obj.purchase_price_min
        except AttributeError:
            return None

        try:
            purchase_price_max = obj.purchase_price_max
        except AttributeError:
            return None

        if purchase_price_min and not purchase_price_max:
            # Get price range
            purchase_price_range = str(purchase_price_max)
        elif not purchase_price_min and purchase_price_max:
            # Get price range
            purchase_price_range = str(purchase_price_max)
        elif purchase_price_min and purchase_price_max:
            # Get price range
            if purchase_price_min >= purchase_price_max:
                # If min > max: use min only
                purchase_price_range = str(purchase_price_min)
            else:
                purchase_price_range = str(purchase_price_min) + " - " + str(purchase_price_max)
        else:
            purchase_price_range = '-'

        return purchase_price_range

    def get_purchase_price_avg(self, obj):
        """ Return purchase price average """

        try:
            purchase_price_avg = obj.purchase_price_avg
        except AttributeError:
            return None

        if purchase_price_avg:
            # Get string representation of price average
            purchase_price_avg = str(purchase_price_avg)
        else:
            purchase_price_avg = '-'

        return purchase_price_avg

    class Meta:
        model = BomItem
        fields = [
            'allow_variants',
            'inherited',
            'note',
            'optional',
            'overage',
            'pk',
            'part',
            'part_detail',
            'purchase_price_avg',
            'purchase_price_max',
            'purchase_price_min',
            'purchase_price_range',
            'quantity',
            'reference',
            'sub_part',
            'sub_part_detail',
            'substitutes',
            'price_range',
            'validated',
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


class PartParameterSerializer(InvenTreeModelSerializer):
    """ JSON serializers for the PartParameter model """

    template_detail = PartParameterTemplateSerializer(source='template', many=False, read_only=True)

    class Meta:
        model = PartParameter
        fields = [
            'pk',
            'part',
            'template',
            'template_detail',
            'data'
        ]


class CategoryParameterTemplateSerializer(InvenTreeModelSerializer):
    """ Serializer for PartCategoryParameterTemplate """

    parameter_template = PartParameterTemplateSerializer(many=False,
                                                         read_only=True)

    category_detail = CategorySerializer(source='category', many=False, read_only=True)

    class Meta:
        model = PartCategoryParameterTemplate
        fields = [
            'pk',
            'category',
            'category_detail',
            'parameter_template',
            'default_value',
        ]


class PartCopyBOMSerializer(serializers.Serializer):
    """
    Serializer for copying a BOM from another part
    """

    class Meta:
        fields = [
            'part',
            'remove_existing',
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
        """
        Check that a 'valid' part was selected
        """

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

    def save(self):
        """
        Actually duplicate the BOM
        """

        base_part = self.context['part']

        data = self.validated_data

        base_part.copy_bom_from(
            data['part'],
            clear=data.get('remove_existing', True),
            skip_invalid=data.get('skip_invalid', False),
            include_inherited=data.get('include_inherited', False),
        )


class BomExtractSerializer(serializers.Serializer):
    """
    Serializer for uploading a file and extracting data from it.

    Note: 2022-02-04 - This needs a *serious* refactor in future, probably

    When parsing the file, the following things happen:

    a) Check file format and validity
    b) Look for "required" fields
    c) Look for "part" fields - used to "infer" part

    Once the file itself has been validated, we iterate through each data row:

    - If the "level" column is provided, ignore anything below level 1
    - Try to "guess" the part based on part_id / part_name / part_ipn
    - Extract other fields as required

    """

    class Meta:
        fields = [
            'bom_file',
            'part',
            'clear_existing',
        ]

    # These columns must be present
    REQUIRED_COLUMNS = [
        'quantity',
    ]

    # We need at least one column to specify a "part"
    PART_COLUMNS = [
        'part',
        'part_id',
        'part_name',
        'part_ipn',
    ]

    # These columns are "optional"
    OPTIONAL_COLUMNS = [
        'allow_variants',
        'inherited',
        'optional',
        'overage',
        'note',
        'reference',
    ]

    def find_matching_column(self, col_name, columns):

        # Direct match
        if col_name in columns:
            return col_name

        col_name = col_name.lower().strip()

        for col in columns:
            if col.lower().strip() == col_name:
                return col

        # No match
        return None

    def find_matching_data(self, row, col_name, columns):
        """
        Extract data from the row, based on the "expected" column name
        """

        col_name = self.find_matching_column(col_name, columns)

        return row.get(col_name, None)

    bom_file = serializers.FileField(
        label=_("BOM File"),
        help_text=_("Select Bill of Materials file"),
        required=True,
        allow_empty_file=False,
    )

    def validate_bom_file(self, bom_file):
        """
        Perform validation checks on the uploaded BOM file
        """

        self.filename = bom_file.name

        name, ext = os.path.splitext(bom_file.name)

        # Remove the leading . from the extension
        ext = ext[1:]

        accepted_file_types = [
            'xls', 'xlsx',
            'csv', 'tsv',
            'xml',
        ]

        if ext not in accepted_file_types:
            raise serializers.ValidationError(_("Unsupported file type"))

        # Impose a 50MB limit on uploaded BOM files
        max_upload_file_size = 50 * 1024 * 1024

        if bom_file.size > max_upload_file_size:
            raise serializers.ValidationError(_("File is too large"))

        # Read file data into memory (bytes object)
        try:
            data = bom_file.read()
        except Exception as e:
            raise serializers.ValidationError(str(e))

        if ext in ['csv', 'tsv', 'xml']:
            try:
                data = data.decode()
            except Exception as e:
                raise serializers.ValidationError(str(e))

        # Convert to a tablib dataset (we expect headers)
        try:
            self.dataset = tablib.Dataset().load(data, ext, headers=True)
        except Exception as e:
            raise serializers.ValidationError(str(e))

        for header in self.REQUIRED_COLUMNS:

            match = self.find_matching_column(header, self.dataset.headers)

            if match is None:
                raise serializers.ValidationError(_("Missing required column") + f": '{header}'")

        part_column_matches = {}

        part_match = False

        for col in self.PART_COLUMNS:
            col_match = self.find_matching_column(col, self.dataset.headers)

            part_column_matches[col] = col_match

            if col_match is not None:
                part_match = True

        if not part_match:
            raise serializers.ValidationError(_("No part column found"))

        if len(self.dataset) == 0:
            raise serializers.ValidationError(_("No data rows found"))

        return bom_file

    def extract_data(self):
        """
        Read individual rows out of the BOM file
        """

        rows = []
        errors = []

        found_parts = set()

        headers = self.dataset.headers

        level_column = self.find_matching_column('level', headers)

        for row in self.dataset.dict:

            row_error = {}

            """
            If the "level" column is specified, and this is not a top-level BOM item, ignore the row!
            """
            if level_column is not None:
                level = row.get('level', None)

                if level is not None:
                    try:
                        level = int(level)
                        if level != 1:
                            continue
                    except:
                        pass

            """
            Next, we try to "guess" the part, based on the provided data.

            A) If the part_id is supplied, use that!
            B) If the part name and/or part_ipn are supplied, maybe we can use those?
            """
            part_id = self.find_matching_data(row, 'part_id', headers)
            part_name = self.find_matching_data(row, 'part_name', headers)
            part_ipn = self.find_matching_data(row, 'part_ipn', headers)

            part = None

            if part_id is not None:
                try:
                    part = Part.objects.get(pk=part_id)
                except (ValueError, Part.DoesNotExist):
                    pass

            # Optionally, specify using field "part"
            if part is None:
                pk = self.find_matching_data(row, 'part', headers)

                if pk is not None:
                    try:
                        part = Part.objects.get(pk=pk)
                    except (ValueError, Part.DoesNotExist):
                        pass

            if part is None:

                if part_name or part_ipn:
                    queryset = Part.objects.all()

                    if part_name:
                        queryset = queryset.filter(name=part_name)

                    if part_ipn:
                        queryset = queryset.filter(IPN=part_ipn)

                    # Only if we have a single direct match
                    if queryset.exists():
                        if queryset.count() == 1:
                            part = queryset.first()
                        else:
                            # Multiple matches!
                            row_error['part'] = _('Multiple matching parts found')

            if part is None:
                if 'part' not in row_error:
                    row_error['part'] = _('No matching part found')
            else:
                if part.pk in found_parts:
                    row_error['part'] = _("Duplicate part selected")

                elif not part.component:
                    row_error['part'] = _('Part is not designated as a component')

                found_parts.add(part.pk)

            row['part'] = part.pk if part is not None else None

            """
            Read out the 'quantity' column - check that it is valid
            """
            quantity = self.find_matching_data(row, 'quantity', self.dataset.headers)

            if quantity is None:
                row_error['quantity'] = _('Quantity not provided')
            else:
                try:
                    quantity = Decimal(quantity)

                    if quantity <= 0:
                        row_error['quantity'] = _('Quantity must be greater than zero')
                except:
                    row_error['quantity'] = _('Invalid quantity')

            # For each "optional" column, ensure the column names are allocated correctly
            for field_name in self.OPTIONAL_COLUMNS:
                if field_name not in row:
                    row[field_name] = self.find_matching_data(row, field_name, self.dataset.headers)

            rows.append(row)
            errors.append(row_error)

        return {
            'rows': rows,
            'errors': errors,
            'headers': headers,
            'filename': self.filename,
        }

    part = serializers.PrimaryKeyRelatedField(queryset=Part.objects.filter(assembly=True), required=True)

    clear_existing = serializers.BooleanField(
        label=_("Clear Existing BOM"),
        help_text=_("Delete existing BOM data first"),
    )

    def save(self):

        data = self.validated_data

        master_part = data['part']
        clear_existing = data['clear_existing']

        if clear_existing:

            # Remove all existing BOM items
            master_part.bom_items.all().delete()


class BomUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading a BOM against a specified part.

    A "BOM" is a set of BomItem objects which are to be validated together as a set
    """

    items = BomItemSerializer(many=True, required=True)

    def validate(self, data):

        items = data['items']

        if len(items) == 0:
            raise serializers.ValidationError(_("At least one BOM item is required"))

        data = super().validate(data)

        return data

    def save(self):

        data = self.validated_data

        items = data['items']

        try:
            with transaction.atomic():

                for item in items:

                    part = item['part']
                    sub_part = item['sub_part']

                    # Ignore duplicate BOM items
                    if BomItem.objects.filter(part=part, sub_part=sub_part).exists():
                        continue

                    # Create a new BomItem object
                    BomItem.objects.create(**item)

        except Exception as e:
            raise serializers.ValidationError(detail=serializers.as_serializer_error(e))
