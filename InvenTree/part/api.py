"""
Provides a JSON API for the Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.http import JsonResponse
from django.db.models import Q, F, Count, Min, Max, Avg
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework import filters, serializers
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as rest_filters

from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money
from djmoney.contrib.exchange.exceptions import MissingRate

from decimal import Decimal, InvalidOperation

from .models import Part, PartCategory
from .models import BomItem, BomItemSubstitute
from .models import PartParameter, PartParameterTemplate
from .models import PartAttachment, PartTestTemplate
from .models import PartSellPriceBreak, PartInternalPriceBreak
from .models import PartCategoryParameterTemplate

from company.models import Company, ManufacturerPart, SupplierPart

from stock.models import StockItem, StockLocation

from common.models import InvenTreeSetting
from build.models import Build

from . import serializers as part_serializers

from InvenTree.helpers import str2bool, isNull
from InvenTree.api import AttachmentMixin

from InvenTree.status_codes import BuildStatus


class CategoryList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartCategory objects.

    - GET: Return a list of PartCategory objects
    - POST: Create a new PartCategory object
    """

    queryset = PartCategory.objects.all()
    serializer_class = part_serializers.CategorySerializer

    def get_serializer_context(self):

        ctx = super().get_serializer_context()

        ctx['starred_categories'] = [star.category for star in self.request.user.starred_categories.all()]

        return ctx

    def filter_queryset(self, queryset):
        """
        Custom filtering:
        - Allow filtering by "null" parent to retrieve top-level part categories
        """

        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        cat_id = params.get('parent', None)

        cascade = str2bool(params.get('cascade', False))

        # Do not filter by category
        if cat_id is None:
            pass
        # Look for top-level categories
        elif isNull(cat_id):

            if not cascade:
                queryset = queryset.filter(parent=None)

        else:
            try:
                category = PartCategory.objects.get(pk=cat_id)

                if cascade:
                    parents = category.get_descendants(include_self=True)
                    parent_ids = [p.id for p in parents]

                    queryset = queryset.filter(parent__in=parent_ids)
                else:
                    queryset = queryset.filter(parent=category)

            except (ValueError, PartCategory.DoesNotExist):
                pass

        # Exclude PartCategory tree
        exclude_tree = params.get('exclude_tree', None)

        if exclude_tree is not None:
            try:
                cat = PartCategory.objects.get(pk=exclude_tree)

                queryset = queryset.exclude(
                    pk__in=[c.pk for c in cat.get_descendants(include_self=True)]
                )

            except (ValueError, PartCategory.DoesNotExist):
                pass

        # Filter by "starred" status
        starred = params.get('starred', None)

        if starred is not None:
            starred = str2bool(starred)
            starred_categories = [star.category.pk for star in self.request.user.starred_categories.all()]

            if starred:
                queryset = queryset.filter(pk__in=starred_categories)
            else:
                queryset = queryset.exclude(pk__in=starred_categories)

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
    ]

    ordering_fields = [
        'name',
        'level',
        'tree_id',
        'lft',
    ]

    # Use hierarchical ordering by default
    ordering = [
        'tree_id',
        'lft',
        'name'
    ]

    search_fields = [
        'name',
        'description',
    ]


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detail view of a single PartCategory object
    """
    
    serializer_class = part_serializers.CategorySerializer
    queryset = PartCategory.objects.all()

    def get_serializer_context(self):

        ctx = super().get_serializer_context()

        ctx['starred_categories'] = [star.category for star in self.request.user.starred_categories.all()]

        return ctx


class CategoryParameterList(generics.ListAPIView):
    """ API endpoint for accessing a list of PartCategoryParameterTemplate objects.

    - GET: Return a list of PartCategoryParameterTemplate objects
    """

    queryset = PartCategoryParameterTemplate.objects.all()
    serializer_class = part_serializers.CategoryParameterTemplateSerializer

    def get_queryset(self):
        """
        Custom filtering:
        - Allow filtering by "null" parent to retrieve all categories parameter templates
        - Allow filtering by category
        - Allow traversing all parent categories
        """

        queryset = super().get_queryset()

        params = self.request.query_params

        category = params.get('category', None)

        if category is not None:
            try:
                
                category = PartCategory.objects.get(pk=category)

                fetch_parent = str2bool(params.get('fetch_parent', True))

                if fetch_parent:
                    parents = category.get_ancestors(include_self=True)
                    queryset = queryset.filter(category__in=[cat.pk for cat in parents])
                else:
                    queryset = queryset.filter(category=category)

            except (ValueError, PartCategory.DoesNotExist):
                pass

        return queryset


class PartSalePriceList(generics.ListCreateAPIView):
    """
    API endpoint for list view of PartSalePriceBreak model
    """

    queryset = PartSellPriceBreak.objects.all()
    serializer_class = part_serializers.PartSalePriceSerializer

    filter_backends = [
        DjangoFilterBackend
    ]

    filter_fields = [
        'part',
    ]


class PartInternalPriceList(generics.ListCreateAPIView):
    """
    API endpoint for list view of PartInternalPriceBreak model
    """

    queryset = PartInternalPriceBreak.objects.all()
    serializer_class = part_serializers.PartInternalPriceSerializer
    permission_required = 'roles.sales_order.show'

    filter_backends = [
        DjangoFilterBackend
    ]

    filter_fields = [
        'part',
    ]


class PartAttachmentList(generics.ListCreateAPIView, AttachmentMixin):
    """
    API endpoint for listing (and creating) a PartAttachment (file upload).
    """

    queryset = PartAttachment.objects.all()
    serializer_class = part_serializers.PartAttachmentSerializer

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'part',
    ]


class PartAttachmentDetail(generics.RetrieveUpdateDestroyAPIView, AttachmentMixin):
    """
    Detail endpoint for PartAttachment model
    """

    queryset = PartAttachment.objects.all()
    serializer_class = part_serializers.PartAttachmentSerializer


class PartTestTemplateDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Detail endpoint for PartTestTemplate model
    """

    queryset = PartTestTemplate.objects.all()
    serializer_class = part_serializers.PartTestTemplateSerializer


class PartTestTemplateList(generics.ListCreateAPIView):
    """
    API endpoint for listing (and creating) a PartTestTemplate.
    """

    queryset = PartTestTemplate.objects.all()
    serializer_class = part_serializers.PartTestTemplateSerializer

    def filter_queryset(self, queryset):
        """
        Filter the test list queryset.

        If filtering by 'part', we include results for any parts "above" the specified part.
        """

        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        part = params.get('part', None)

        # Filter by part
        if part:
            try:
                part = Part.objects.get(pk=part)
                queryset = queryset.filter(part__in=part.get_ancestors(include_self=True))
            except (ValueError, Part.DoesNotExist):
                pass

        # Filter by 'required' status
        required = params.get('required', None)

        if required is not None:
            queryset = queryset.filter(required=required)

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]


class PartThumbs(generics.ListAPIView):
    """
    API endpoint for retrieving information on available Part thumbnails
    """

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartThumbSerializer

    def get_queryset(self):

        queryset = super().get_queryset()

        # Get all Parts which have an associated image
        queryset = queryset.exclude(image='')

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Serialize the available Part images.
        - Images may be used for multiple parts!
        """

        queryset = self.filter_queryset(self.get_queryset())

        # Return the most popular parts first
        data = queryset.values(
            'image',
        ).annotate(count=Count('image')).order_by('-count')

        return Response(data)

    filter_backends = [
        filters.SearchFilter,
    ]

    search_fields = [
        'name',
        'description',
        'IPN',
        'revision',
        'keywords',
        'category__name',
    ]


class PartThumbsUpdate(generics.RetrieveUpdateAPIView):
    """ API endpoint for updating Part thumbnails"""

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartThumbSerializerUpdate

    filter_backends = [
        DjangoFilterBackend
    ]


class PartDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of a single Part object """

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartSerializer

    starred_parts = None

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)

        queryset = part_serializers.PartSerializer.annotate_queryset(queryset)

        return queryset

    def get_serializer(self, *args, **kwargs):

        # By default, include 'category_detail' information in the detail view
        try:
            kwargs['category_detail'] = str2bool(self.request.query_params.get('category_detail', True))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        # Pass a list of "starred" parts of the current user to the serializer
        # We do this to reduce the number of database queries required!
        if self.starred_parts is None and self.request is not None:
            self.starred_parts = [star.part for star in self.request.user.starred_parts.all()]

        kwargs['starred_parts'] = self.starred_parts

        return self.serializer_class(*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Retrieve part
        part = Part.objects.get(pk=int(kwargs['pk']))
        # Check if inactive
        if not part.active:
            # Delete
            return super(PartDetail, self).destroy(request, *args, **kwargs)
        else:
            # Return 405 error
            message = f'Part \'{part.name}\' (pk = {part.pk}) is active: cannot delete'
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data=message)

    def update(self, request, *args, **kwargs):
        """
        Custom update functionality for Part instance.

        - If the 'starred' field is provided, update the 'starred' status against current user
        """

        if 'starred' in request.data:
            starred = str2bool(request.data.get('starred', None))

            self.get_object().set_starred(request.user, starred)

        response = super().update(request, *args, **kwargs)

        return response


class PartFilter(rest_filters.FilterSet):
    """
    Custom filters for the PartList endpoint.
    Uses the django_filters extension framework
    """

    # Filter by parts which have (or not) an IPN value
    has_ipn = rest_filters.BooleanFilter(label='Has IPN', method='filter_has_ipn')

    def filter_has_ipn(self, queryset, name, value):

        value = str2bool(value)

        if value:
            queryset = queryset.exclude(IPN='')
        else:
            queryset = queryset.filter(IPN='')

        return queryset

    # Regex filter for name
    name_regex = rest_filters.CharFilter(label='Filter by name (regex)', field_name='name', lookup_expr='iregex')

    # Exact match for IPN
    IPN = rest_filters.CharFilter(
        label='Filter by exact IPN (internal part number)',
        field_name='IPN',
        lookup_expr="iexact"
    )

    # Regex match for IPN
    IPN_regex = rest_filters.CharFilter(label='Filter by regex on IPN (internal part number)', field_name='IPN', lookup_expr='iregex')

    # low_stock filter
    low_stock = rest_filters.BooleanFilter(label='Low stock', method='filter_low_stock')

    def filter_low_stock(self, queryset, name, value):
        """
        Filter by "low stock" status
        """

        value = str2bool(value)

        if value:
            # Ignore any parts which do not have a specified 'minimum_stock' level
            queryset = queryset.exclude(minimum_stock=0)
            # Filter items which have an 'in_stock' level lower than 'minimum_stock'
            queryset = queryset.filter(Q(in_stock__lt=F('minimum_stock')))
        else:
            # Filter items which have an 'in_stock' level higher than 'minimum_stock'
            queryset = queryset.filter(Q(in_stock__gte=F('minimum_stock')))

        return queryset

    # has_stock filter
    has_stock = rest_filters.BooleanFilter(label='Has stock', method='filter_has_stock')

    def filter_has_stock(self, queryset, name, value):

        value = str2bool(value)

        if value:
            queryset = queryset.filter(Q(in_stock__gt=0))
        else:
            queryset = queryset.filter(Q(in_stock__lte=0))

        return queryset

    is_template = rest_filters.BooleanFilter()

    assembly = rest_filters.BooleanFilter()

    component = rest_filters.BooleanFilter()

    trackable = rest_filters.BooleanFilter()

    purchaseable = rest_filters.BooleanFilter()

    salable = rest_filters.BooleanFilter()

    active = rest_filters.BooleanFilter()


class PartList(generics.ListCreateAPIView):
    """
    API endpoint for accessing a list of Part objects

    - GET: Return list of objects
    - POST: Create a new Part object

    The Part object list can be filtered by:
        - category: Filter by PartCategory reference
        - cascade: If true, include parts from sub-categories
        - starred: Is the part "starred" by the current user?
        - is_template: Is the part a template part?
        - variant_of: Filter by variant_of Part reference
        - assembly: Filter by assembly field
        - component: Filter by component field
        - trackable: Filter by trackable field
        - purchaseable: Filter by purcahseable field
        - salable: Filter by salable field
        - active: Filter by active field
        - ancestor: Filter parts by 'ancestor' (template / variant tree)
    """

    serializer_class = part_serializers.PartSerializer
    queryset = Part.objects.all()
    filterset_class = PartFilter

    starred_parts = None

    def get_serializer(self, *args, **kwargs):

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        # Pass a list of "starred" parts fo the current user to the serializer
        # We do this to reduce the number of database queries required!
        if self.starred_parts is None and self.request is not None:
            self.starred_parts = [star.part for star in self.request.user.starred_parts.all()]

        kwargs['starred_parts'] = self.starred_parts

        return self.serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Overide the 'list' method, as the PartCategory objects are
        very expensive to serialize!

        So we will serialize them first, and keep them in memory,
        so that they do not have to be serialized multiple times...
        """

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        # Do we wish to include PartCategory detail?
        if str2bool(request.query_params.get('category_detail', False)):

            # Work out which part categories we need to query
            category_ids = set()

            for part in data:
                cat_id = part['category']

                if cat_id is not None:
                    category_ids.add(cat_id)

            # Fetch only the required PartCategory objects from the database
            categories = PartCategory.objects.filter(pk__in=category_ids).prefetch_related(
                'parts',
                'parent',
                'children',
            )

            category_map = {}

            # Serialize each PartCategory object
            for category in categories:
                category_map[category.pk] = part_serializers.CategorySerializer(category).data

            for part in data:
                cat_id = part['category']

                if cat_id is not None and cat_id in category_map.keys():
                    detail = category_map[cat_id]
                else:
                    detail = None

                part['category_detail'] = detail

        """
        Determine the response type based on the request.
        a) For HTTP requests (e.g. via the browseable API) return a DRF response
        b) For AJAX requests, simply return a JSON rendered response.
        """
        if page is not None:
            return self.get_paginated_response(data)
        elif request.is_ajax():
            return JsonResponse(data, safe=False)
        else:
            return Response(data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        We wish to save the user who created this part!

        Note: Implementation copied from DRF class CreateModelMixin
        """

        # TODO: Unit tests for this function!

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        part = serializer.save()
        part.creation_user = self.request.user

        # Optionally copy templates from category or parent category
        copy_templates = {
            'main': str2bool(request.data.get('copy_category_templates', False)),
            'parent': str2bool(request.data.get('copy_parent_templates', False))
        }

        part.save(**{'add_category_templates': copy_templates})

        # Optionally copy data from another part (e.g. when duplicating)
        copy_from = request.data.get('copy_from', None)

        if copy_from is not None:

            try:
                original = Part.objects.get(pk=copy_from)

                copy_bom = str2bool(request.data.get('copy_bom', False))
                copy_parameters = str2bool(request.data.get('copy_parameters', False))
                copy_image = str2bool(request.data.get('copy_image', True))

                # Copy image?
                if copy_image:
                    part.image = original.image
                    part.save()

                # Copy BOM?
                if copy_bom:
                    part.copy_bom_from(original)

                # Copy parameter data?
                if copy_parameters:
                    part.copy_parameters_from(original)

            except (ValueError, Part.DoesNotExist):
                pass

        # Optionally create initial stock item
        initial_stock = str2bool(request.data.get('initial_stock', False))

        if initial_stock:
            try:

                initial_stock_quantity = Decimal(request.data.get('initial_stock_quantity', ''))

                if initial_stock_quantity <= 0:
                    raise ValidationError({
                        'initial_stock_quantity': [_('Must be greater than zero')],
                    })
            except (ValueError, InvalidOperation):  # Invalid quantity provided
                raise ValidationError({
                    'initial_stock_quantity': [_('Must be a valid quantity')],
                })
            
            initial_stock_location = request.data.get('initial_stock_location', None)

            try:
                initial_stock_location = StockLocation.objects.get(pk=initial_stock_location)
            except (ValueError, StockLocation.DoesNotExist):
                initial_stock_location = None

            if initial_stock_location is None:
                if part.default_location is not None:
                    initial_stock_location = part.default_location
                else:
                    raise ValidationError({
                        'initial_stock_location': [_('Specify location for initial part stock')],
                    })

            stock_item = StockItem(
                part=part,
                quantity=initial_stock_quantity,
                location=initial_stock_location,
            )

            stock_item.save(user=request.user)

        # Optionally add manufacturer / supplier data to the part
        if part.purchaseable and str2bool(request.data.get('add_supplier_info', False)):

            try:
                manufacturer = Company.objects.get(pk=request.data.get('manufacturer', None))
            except:
                manufacturer = None

            try:
                supplier = Company.objects.get(pk=request.data.get('supplier', None))
            except:
                supplier = None

            mpn = str(request.data.get('MPN', '')).strip()
            sku = str(request.data.get('SKU', '')).strip()

            # Construct a manufacturer part
            if manufacturer or mpn:
                if not manufacturer:
                    raise ValidationError({
                        'manufacturer': [_("This field is required")]
                    })
                if not mpn:
                    raise ValidationError({
                        'MPN': [_("This field is required")]
                    })

                manufacturer_part = ManufacturerPart.objects.create(
                    part=part,
                    manufacturer=manufacturer,
                    MPN=mpn
                )
            else:
                # No manufacturer part data specified
                manufacturer_part = None

            if supplier or sku:
                if not supplier:
                    raise ValidationError({
                        'supplier': [_("This field is required")]
                    })
                if not sku:
                    raise ValidationError({
                        'SKU': [_("This field is required")]
                    })

                SupplierPart.objects.create(
                    part=part,
                    supplier=supplier,
                    SKU=sku,
                    manufacturer_part=manufacturer_part,
                )

        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)
        queryset = part_serializers.PartSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """
        Perform custom filtering of the queryset.
        We overide the DRF filter_fields here because
        """

        params = self.request.query_params

        queryset = super().filter_queryset(queryset)

        # Filter by "uses" query - Limit to parts which use the provided part
        uses = params.get('uses', None)

        if uses:
            try:
                uses = Part.objects.get(pk=uses)

                queryset = queryset.filter(uses.get_used_in_filter())

            except (ValueError, Part.DoesNotExist):
                pass

        # Exclude specific part ID values?
        exclude_id = []

        for key in ['exclude_id', 'exclude_id[]']:
            if key in params:
                exclude_id += params.getlist(key, [])

        if exclude_id:

            id_values = []

            for val in exclude_id:
                try:
                    # pk values must be integer castable
                    val = int(val)
                    id_values.append(val)
                except ValueError:
                    pass
            
            queryset = queryset.exclude(pk__in=id_values)

        # Exclude part variant tree?
        exclude_tree = params.get('exclude_tree', None)

        if exclude_tree is not None:
            try:
                top_level_part = Part.objects.get(pk=exclude_tree)

                queryset = queryset.exclude(
                    pk__in=[prt.pk for prt in top_level_part.get_descendants(include_self=True)]
                )

            except (ValueError, Part.DoesNotExist):
                pass

        # Filter by 'ancestor'?
        ancestor = params.get('ancestor', None)

        if ancestor is not None:
            # If an 'ancestor' part is provided, filter to match only children
            try:
                ancestor = Part.objects.get(pk=ancestor)
                descendants = ancestor.get_descendants(include_self=False)
                queryset = queryset.filter(pk__in=[d.pk for d in descendants])
            except (ValueError, Part.DoesNotExist):
                pass

        # Filter by whether the BOM has been validated (or not)
        bom_valid = params.get('bom_valid', None)

        # TODO: Querying bom_valid status may be quite expensive
        # TODO: (It needs to be profiled!)
        # TODO: It might be worth caching the bom_valid status to a database column

        if bom_valid is not None:

            bom_valid = str2bool(bom_valid)

            # Limit queryset to active assemblies
            queryset = queryset.filter(active=True, assembly=True)

            pks = []

            for part in queryset:
                if part.is_bom_valid() == bom_valid:
                    pks.append(part.pk)

            queryset = queryset.filter(pk__in=pks)

        # Filter by 'starred' parts?
        starred = params.get('starred', None)

        if starred is not None:
            starred = str2bool(starred)
            starred_parts = [star.part.pk for star in self.request.user.starred_parts.all()]

            if starred:
                queryset = queryset.filter(pk__in=starred_parts)
            else:
                queryset = queryset.exclude(pk__in=starred_parts)

        # Cascade? (Default = True)
        cascade = str2bool(params.get('cascade', True))

        # Does the user wish to filter by category?
        cat_id = params.get('category', None)

        if cat_id is None:
            # No category filtering if category is not specified
            pass

        else:
            # Category has been specified!
            if isNull(cat_id):
                # A 'null' category is the top-level category
                if cascade is False:
                    # Do not cascade, only list parts in the top-level category
                    queryset = queryset.filter(category=None)

            else:
                try:
                    category = PartCategory.objects.get(pk=cat_id)

                    # If '?cascade=true' then include parts which exist in sub-categories
                    if cascade:
                        queryset = queryset.filter(category__in=category.getUniqueChildren())
                    # Just return parts directly in the requested category
                    else:
                        queryset = queryset.filter(category=cat_id)
                except (ValueError, PartCategory.DoesNotExist):
                    pass

        # Filer by 'depleted_stock' status -> has no stock and stock items
        depleted_stock = params.get('depleted_stock', None)

        if depleted_stock is not None:
            depleted_stock = str2bool(depleted_stock)

            if depleted_stock:
                queryset = queryset.filter(Q(in_stock=0) & ~Q(stock_item_count=0))

        # Filter by "parts which need stock to complete build"
        stock_to_build = params.get('stock_to_build', None)

        # TODO: This is super expensive, database query wise...
        # TODO: Need to figure out a cheaper way of making this filter query

        if stock_to_build is not None:
            # Get active builds
            builds = Build.objects.filter(status__in=BuildStatus.ACTIVE_CODES)
            # Store parts with builds needing stock
            parts_needed_to_complete_builds = []
            # Filter required parts
            for build in builds:
                parts_needed_to_complete_builds += [part.pk for part in build.required_parts_to_complete_build]

            queryset = queryset.filter(pk__in=parts_needed_to_complete_builds)

        # Optionally limit the maximum number of returned results
        # e.g. for displaying "recent part" list
        max_results = params.get('max_results', None)

        if max_results is not None:
            try:
                max_results = int(max_results)

                if max_results > 0:
                    queryset = queryset[:max_results]

            except (ValueError):
                pass

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'variant_of',
    ]

    ordering_fields = [
        'name',
        'creation_date',
        'IPN',
        'in_stock',
        'category',
    ]

    # Default ordering
    ordering = 'name'

    search_fields = [
        'name',
        'description',
        'IPN',
        'revision',
        'keywords',
        'category__name',
    ]


class PartParameterTemplateList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartParameterTemplate objects.

    - GET: Return list of PartParameterTemplate objects
    - POST: Create a new PartParameterTemplate object
    """

    queryset = PartParameterTemplate.objects.all()
    serializer_class = part_serializers.PartParameterTemplateSerializer

    filter_backends = [
        filters.OrderingFilter,
    ]

    filter_fields = [
        'name',
    ]


class PartParameterList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartParameter objects

    - GET: Return list of PartParameter objects
    - POST: Create a new PartParameter object
    """

    queryset = PartParameter.objects.all()
    serializer_class = part_serializers.PartParameterSerializer

    filter_backends = [
        DjangoFilterBackend
    ]

    filter_fields = [
        'part',
        'template',
    ]


class PartParameterDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detail view of a single PartParameter object
    """

    queryset = PartParameter.objects.all()
    serializer_class = part_serializers.PartParameterSerializer


class BomFilter(rest_filters.FilterSet):
    """
    Custom filters for the BOM list
    """

    # Boolean filters for BOM item
    optional = rest_filters.BooleanFilter(label='BOM line is optional')
    inherited = rest_filters.BooleanFilter(label='BOM line is inherited')
    allow_variants = rest_filters.BooleanFilter(label='Variants are allowed')

    validated = rest_filters.BooleanFilter(label='BOM line has been validated', method='filter_validated')

    def filter_validated(self, queryset, name, value):

        # Work out which lines have actually been validated
        pks = []

        for bom_item in queryset.all():
            if bom_item.is_line_valid():
                pks.append(bom_item.pk)

        if str2bool(value):
            queryset = queryset.filter(pk__in=pks)
        else:
            queryset = queryset.exclude(pk__in=pks)
    
        return queryset

    # Filters for linked 'part'
    part_active = rest_filters.BooleanFilter(label='Master part is active', field_name='part__active')
    part_trackable = rest_filters.BooleanFilter(label='Master part is trackable', field_name='part__trackable')

    # Filters for linked 'sub_part'
    sub_part_trackable = rest_filters.BooleanFilter(label='Sub part is trackable', field_name='sub_part__trackable')
    sub_part_assembly = rest_filters.BooleanFilter(label='Sub part is an assembly', field_name='sub_part__assembly')


class BomList(generics.ListCreateAPIView):
    """
    API endpoint for accessing a list of BomItem objects.

    - GET: Return list of BomItem objects
    - POST: Create a new BomItem object
    """

    serializer_class = part_serializers.BomItemSerializer
    queryset = BomItem.objects.all()
    filterset_class = BomFilter

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        """
        Determine the response type based on the request.
        a) For HTTP requests (e.g. via the browseable API) return a DRF response
        b) For AJAX requests, simply return a JSON rendered response.
        """
        if page is not None:
            return self.get_paginated_response(data)
        elif request.is_ajax():
            return JsonResponse(data, safe=False)
        else:
            return Response(data)

    def get_serializer(self, *args, **kwargs):

        # Do we wish to include extra detail?
        try:
            kwargs['part_detail'] = str2bool(self.request.GET.get('part_detail', None))
        except AttributeError:
            pass

        try:
            kwargs['sub_part_detail'] = str2bool(self.request.GET.get('sub_part_detail', None))
        except AttributeError:
            pass

        try:
            # Include or exclude pricing information in the serialized data
            kwargs['include_pricing'] = self.include_pricing()
        except AttributeError:
            pass

        # Ensure the request context is passed through!
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = BomItem.objects.all()

        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        return queryset

    def filter_queryset(self, queryset):

        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by part?
        part = params.get('part', None)

        if part is not None:
            """
            If we are filtering by "part", there are two cases to consider:

            a) Bom items which are defined for *this* part
            b) Inherited parts which are defined for a *parent* part

            So we need to construct two queries!
            """

            # First, check that the part is actually valid!
            try:
                part = Part.objects.get(pk=part)

                queryset = queryset.filter(part.get_bom_item_filter())

            except (ValueError, Part.DoesNotExist):
                pass

        if self.include_pricing():
            queryset = self.annotate_pricing(queryset)

        return queryset
    
    def include_pricing(self):
        """
        Determine if pricing information should be included in the response
        """
        pricing_default = InvenTreeSetting.get_setting('PART_SHOW_PRICE_IN_BOM')

        return str2bool(self.request.query_params.get('include_pricing', pricing_default))

    def annotate_pricing(self, queryset):
        """
        Add part pricing information to the queryset
        """

        # Annotate with purchase prices
        queryset = queryset.annotate(
            purchase_price_min=Min('sub_part__stock_items__purchase_price'),
            purchase_price_max=Max('sub_part__stock_items__purchase_price'),
            purchase_price_avg=Avg('sub_part__stock_items__purchase_price'),
        )

        # Get values for currencies
        currencies = queryset.annotate(
            purchase_price=F('sub_part__stock_items__purchase_price'),
            purchase_price_currency=F('sub_part__stock_items__purchase_price_currency'),
        ).values('pk', 'sub_part', 'purchase_price', 'purchase_price_currency')

        def convert_price(price, currency, decimal_places=4):
            """ Convert price field, returns Money field """

            price_adjusted = None

            # Get default currency from settings
            default_currency = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY')
            
            if price:
                if currency and default_currency:
                    try:
                        # Get adjusted price
                        price_adjusted = convert_money(Money(price, currency), default_currency)
                    except MissingRate:
                        # No conversion rate set
                        price_adjusted = Money(price, currency)
                else:
                    # Currency exists
                    if currency:
                        price_adjusted = Money(price, currency)
                    # Default currency exists
                    if default_currency:
                        price_adjusted = Money(price, default_currency)

            if price_adjusted and decimal_places:
                price_adjusted.decimal_places = decimal_places

            return price_adjusted

        # Convert prices to default currency (using backend conversion rates)
        for bom_item in queryset:
            # Find associated currency (select first found)
            purchase_price_currency = None
            for currency_item in currencies:
                if currency_item['pk'] == bom_item.pk and currency_item['sub_part'] == bom_item.sub_part.pk and currency_item['purchase_price']:
                    purchase_price_currency = currency_item['purchase_price_currency']
                    break
            # Convert prices
            bom_item.purchase_price_min = convert_price(bom_item.purchase_price_min, purchase_price_currency)
            bom_item.purchase_price_max = convert_price(bom_item.purchase_price_max, purchase_price_currency)
            bom_item.purchase_price_avg = convert_price(bom_item.purchase_price_avg, purchase_price_currency)

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
    ]


class BomDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of a single BomItem object """

    queryset = BomItem.objects.all()
    serializer_class = part_serializers.BomItemSerializer


class BomItemValidate(generics.UpdateAPIView):
    """ API endpoint for validating a BomItem """

    # Very simple serializers
    class BomItemValidationSerializer(serializers.Serializer):

        valid = serializers.BooleanField(default=False)

    queryset = BomItem.objects.all()
    serializer_class = BomItemValidationSerializer

    def update(self, request, *args, **kwargs):
        """ Perform update request """

        partial = kwargs.pop('partial', False)

        valid = request.data.get('valid', False)

        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if type(instance) == BomItem:
            instance.validate_hash(valid)

        return Response(serializer.data)


class BomItemSubstituteList(generics.ListCreateAPIView):
    """
    API endpoint for accessing a list of BomItemSubstitute objects
    """

    serializer_class = part_serializers.BomItemSubstituteSerializer
    queryset = BomItemSubstitute.objects.all()
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'part',
        'bom_item',
    ]


class BomItemSubstituteDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detail view of a single BomItemSubstitute object
    """

    queryset = BomItemSubstitute.objects.all()
    serializer_class = part_serializers.BomItemSubstituteSerializer


part_api_urls = [

    # Base URL for PartCategory API endpoints
    url(r'^category/', include([
        url(r'^parameters/', CategoryParameterList.as_view(), name='api-part-category-parameter-list'),

        url(r'^(?P<pk>\d+)/?', CategoryDetail.as_view(), name='api-part-category-detail'),
        url(r'^$', CategoryList.as_view(), name='api-part-category-list'),
    ])),

    # Base URL for PartTestTemplate API endpoints
    url(r'^test-template/', include([
        url(r'^(?P<pk>\d+)/', PartTestTemplateDetail.as_view(), name='api-part-test-template-detail'),
        url(r'^$', PartTestTemplateList.as_view(), name='api-part-test-template-list'),
    ])),

    # Base URL for PartAttachment API endpoints
    url(r'^attachment/', include([
        url(r'^(?P<pk>\d+)/', PartAttachmentDetail.as_view(), name='api-part-attachment-detail'),
        url(r'^$', PartAttachmentList.as_view(), name='api-part-attachment-list'),
    ])),

    # Base URL for part sale pricing
    url(r'^sale-price/', include([
        url(r'^.*$', PartSalePriceList.as_view(), name='api-part-sale-price-list'),
    ])),

    # Base URL for part internal pricing
    url(r'^internal-price/', include([
        url(r'^.*$', PartInternalPriceList.as_view(), name='api-part-internal-price-list'),
    ])),

    # Base URL for PartParameter API endpoints
    url(r'^parameter/', include([
        url(r'^template/$', PartParameterTemplateList.as_view(), name='api-part-parameter-template-list'),

        url(r'^(?P<pk>\d+)/', PartParameterDetail.as_view(), name='api-part-parameter-detail'),
        url(r'^.*$', PartParameterList.as_view(), name='api-part-parameter-list'),
    ])),

    url(r'^thumbs/', include([
        url(r'^$', PartThumbs.as_view(), name='api-part-thumbs'),
        url(r'^(?P<pk>\d+)/?', PartThumbsUpdate.as_view(), name='api-part-thumbs-update'),
    ])),

    url(r'^(?P<pk>\d+)/', PartDetail.as_view(), name='api-part-detail'),

    url(r'^.*$', PartList.as_view(), name='api-part-list'),
]

bom_api_urls = [

    url(r'^substitute/', include([

        # Detail view
        url(r'^(?P<pk>\d+)/', BomItemSubstituteDetail.as_view(), name='api-bom-substitute-detail'),

        # Catch all
        url(r'^.*$', BomItemSubstituteList.as_view(), name='api-bom-substitute-list'),
    ])),

    # BOM Item Detail
    url(r'^(?P<pk>\d+)/', include([
        url(r'^validate/?', BomItemValidate.as_view(), name='api-bom-item-validate'),
        url(r'^.*$', BomDetail.as_view(), name='api-bom-item-detail'),
    ])),

    # Catch-all
    url(r'^.*$', BomList.as_view(), name='api-bom-list'),
]
