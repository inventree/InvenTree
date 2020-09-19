"""
Provides a JSON API for the Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.db.models import Q, F, Count

from rest_framework import status
from rest_framework.response import Response
from rest_framework import filters, serializers
from rest_framework import generics, permissions

from django.conf.urls import url, include
from django.urls import reverse

from .models import Part, PartCategory, BomItem, PartStar
from .models import PartParameter, PartParameterTemplate
from .models import PartAttachment, PartTestTemplate
from .models import PartSellPriceBreak

from . import serializers as part_serializers

from InvenTree.views import TreeSerializer
from InvenTree.helpers import str2bool, isNull
from InvenTree.api import AttachmentMixin


class PartCategoryTree(TreeSerializer):

    title = "Parts"
    model = PartCategory
    
    @property
    def root_url(self):
        return reverse('part-index')

    def get_items(self):
        return PartCategory.objects.all().prefetch_related('parts', 'children')


class CategoryList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartCategory objects.

    - GET: Return a list of PartCategory objects
    - POST: Create a new PartCategory object
    """

    queryset = PartCategory.objects.all()
    serializer_class = part_serializers.CategorySerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Custom filtering:
        - Allow filtering by "null" parent to retrieve top-level part categories
        """

        cat_id = self.request.query_params.get('parent', None)

        queryset = super().get_queryset()

        if cat_id is not None:
            
            # Look for top-level categories
            if isNull(cat_id):
                queryset = queryset.filter(parent=None)
            
            else:
                try:
                    cat_id = int(cat_id)
                    queryset = queryset.filter(parent=cat_id)
                except ValueError:
                    pass

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
    ]

    ordering = 'name'

    search_fields = [
        'name',
        'description',
    ]


class CategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of a single PartCategory object """
    serializer_class = part_serializers.CategorySerializer
    queryset = PartCategory.objects.all()


class PartSalePriceList(generics.ListCreateAPIView):
    """
    API endpoint for list view of PartSalePriceBreak model
    """

    queryset = PartSellPriceBreak.objects.all()
    serializer_class = part_serializers.PartSalePriceSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

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

    filter_fields = [
        'part',
    ]


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

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]


class PartThumbs(generics.ListAPIView):
    """ API endpoint for retrieving information on available Part thumbnails """

    serializer_class = part_serializers.PartThumbSerializer

    def list(self, request, *args, **kwargs):
        """
        Serialize the available Part images.
        - Images may be used for multiple parts!
        """

        # Get all Parts which have an associated image
        queryset = Part.objects.all().exclude(image='')

        # TODO - We should return the thumbnails here, not the full image!

        # Return the most popular parts first
        data = queryset.values(
            'image',
        ).annotate(count=Count('image')).order_by('-count')

        return Response(data)


class PartThumbsUpdate(generics.RetrieveUpdateAPIView):
    """ API endpoint for updating Part thumbnails"""

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartThumbSerializerUpdate

    permission_classes = [
        permissions.IsAuthenticated,
    ]

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

        queryset = part_serializers.PartSerializer.prefetch_queryset(queryset)
        queryset = part_serializers.PartSerializer.annotate_queryset(queryset)

        return queryset

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['category_detail'] = str2bool(self.request.query_params.get('category_detail', False))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        # Pass a list of "starred" parts fo the current user to the serializer
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


class PartList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Part objects

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
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        # Do we wish to include PartCategory detail?
        if str2bool(request.query_params.get('category_detail', False)):

            # Work out which part categorie we need to query
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
        if request.is_ajax():
            return JsonResponse(data, safe=False)
        else:
            return Response(data)

    def perform_create(self, serializer):
        """
        We wish to save the user who created this part!

        Note: Implementation copied from DRF class CreateModelMixin
        """

        part = serializer.save()
        part.creation_user = self.request.user
        part.save()

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)
        
        queryset = part_serializers.PartSerializer.prefetch_queryset(queryset)
        queryset = part_serializers.PartSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """
        Perform custom filtering of the queryset.
        We overide the DRF filter_fields here because
        """

        params = self.request.query_params

        queryset = super().filter_queryset(queryset)

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

        # Cascade?
        cascade = str2bool(params.get('cascade', None))

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

        # Annotate calculated data to the queryset
        # (This will be used for further filtering)
        queryset = part_serializers.PartSerializer.annotate_queryset(queryset)

        # Filter by whether the part has stock
        has_stock = params.get("has_stock", None)

        if has_stock is not None:
            has_stock = str2bool(has_stock)

            if has_stock:
                queryset = queryset.filter(Q(in_stock__gt=0))
            else:
                queryset = queryset.filter(Q(in_stock__lte=0))

        # If we are filtering by 'low_stock' status
        low_stock = params.get('low_stock', None)

        if low_stock is not None:
            low_stock = str2bool(low_stock)

            if low_stock:
                # Ignore any parts which do not have a specified 'minimum_stock' level
                queryset = queryset.exclude(minimum_stock=0)
                # Filter items which have an 'in_stock' level lower than 'minimum_stock'
                queryset = queryset.filter(Q(in_stock__lt=F('minimum_stock')))
            else:
                # Filter items which have an 'in_stock' level higher than 'minimum_stock'
                queryset = queryset.filter(Q(in_stock__gte=F('minimum_stock')))

        # Filter by "parts which need stock to complete build"
        stock_to_build = params.get('stock_to_build', None)

        # TODO: This is super expensive, database query wise...
        # TODO: Need to figure out a cheaper way of making this filter query

        if stock_to_build is not None:
            # Filter only active parts
            queryset = queryset.filter(active=True)
            parts_need_stock = []

            # Find parts with active builds
            # where any subpart's stock is lower than quantity being built
            for part in queryset:
                if part.active_builds and part.can_build < part.quantity_being_built:
                    parts_need_stock.append(part.pk)

            queryset = queryset.filter(pk__in=parts_need_stock)

        # Limit choices
        limit = params.get('limit', None)

        if limit is not None:
            try:
                limit = int(limit)
                if limit > 0:
                    queryset = queryset[:limit]
            except ValueError:
                pass

        return queryset

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'is_template',
        'variant_of',
        'assembly',
        'component',
        'trackable',
        'purchaseable',
        'salable',
        'active',
    ]

    ordering_fields = [
        'name',
        'creation_date',
    ]

    # Default ordering
    ordering = 'name'

    search_fields = [
        '$name',
        'description',
        '$IPN',
        'keywords',
    ]


class PartStarDetail(generics.RetrieveDestroyAPIView):
    """ API endpoint for viewing or removing a PartStar object """

    queryset = PartStar.objects.all()
    serializer_class = part_serializers.PartStarSerializer


class PartStarList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartStar objects.

    - GET: Return list of PartStar objects
    - POST: Create a new PartStar object
    """

    queryset = PartStar.objects.all()
    serializer_class = part_serializers.PartStarSerializer

    def create(self, request, *args, **kwargs):

        # Override the user field (with the logged-in user)
        data = request.data.copy()
        data['user'] = str(request.user.id)

        serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter
    ]

    filter_fields = [
        'part',
        'user',
    ]

    search_fields = [
        'partname'
    ]


class PartParameterTemplateList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartParameterTemplate objects.

    - GET: Return list of PartParameterTemplate objects
    - POST: Create a new PartParameterTemplate object
    """

    queryset = PartParameterTemplate.objects.all()
    serializer_class = part_serializers.PartParameterTemplateSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

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

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend
    ]

    filter_fields = [
        'part',
        'template',
    ]


class BomList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of BomItem objects.

    - GET: Return list of BomItem objects
    - POST: Create a new BomItem object
    """

    serializer_class = part_serializers.BomItemSerializer

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        if request.is_ajax():
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
        
        # Ensure the request context is passed through!
        kwargs['context'] = self.get_serializer_context()
        
        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = BomItem.objects.all()

        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        return queryset

    def filter_queryset(self, queryset):

        queryset = super().filter_queryset(queryset)

        # Filter by part?
        part = self.request.query_params.get('part', None)

        if part is not None:
            queryset = queryset.filter(part=part)
        
        # Filter by sub-part?
        sub_part = self.request.query_params.get('sub_part', None)

        if sub_part is not None:
            queryset = queryset.filter(sub_part=sub_part)

        return queryset

    permission_classes = [
        permissions.IsAuthenticated,
    ]

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

    permission_classes = [
        permissions.IsAuthenticated,
    ]


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


part_api_urls = [
    url(r'^tree/?', PartCategoryTree.as_view(), name='api-part-tree'),

    # Base URL for PartCategory API endpoints
    url(r'^category/', include([
        url(r'^(?P<pk>\d+)/?', CategoryDetail.as_view(), name='api-part-category-detail'),
        url(r'^$', CategoryList.as_view(), name='api-part-category-list'),
    ])),

    # Base URL for PartTestTemplate API endpoints
    url(r'^test-template/', include([
        url(r'^$', PartTestTemplateList.as_view(), name='api-part-test-template-list'),
    ])),

    # Base URL for PartAttachment API endpoints
    url(r'^attachment/', include([
        url(r'^$', PartAttachmentList.as_view(), name='api-part-attachment-list'),
    ])),
    
    # Base URL for PartStar API endpoints
    url(r'^star/', include([
        url(r'^(?P<pk>\d+)/?', PartStarDetail.as_view(), name='api-part-star-detail'),
        url(r'^$', PartStarList.as_view(), name='api-part-star-list'),
    ])),

    # Base URL for part sale pricing
    url(r'^sale-price/', include([
        url(r'^.*$', PartSalePriceList.as_view(), name='api-part-sale-price-list'),
    ])),
    
    # Base URL for PartParameter API endpoints
    url(r'^parameter/', include([
        url(r'^template/$', PartParameterTemplateList.as_view(), name='api-part-param-template-list'),
        url(r'^.*$', PartParameterList.as_view(), name='api-part-param-list'),
    ])),

    url(r'^thumbs/', include([
        url(r'^$', PartThumbs.as_view(), name='api-part-thumbs'),
        url(r'^(?P<pk>\d+)/?', PartThumbsUpdate.as_view(), name='api-part-thumbs-update'),
    ])),

    url(r'^(?P<pk>\d+)/?', PartDetail.as_view(), name='api-part-detail'),

    url(r'^.*$', PartList.as_view(), name='api-part-list'),
]

bom_api_urls = [
    # BOM Item Detail
    url(r'^(?P<pk>\d+)/', include([
        url(r'^validate/?', BomItemValidate.as_view(), name='api-bom-item-validate'),
        url(r'^.*$', BomDetail.as_view(), name='api-bom-item-detail'),
    ])),

    # Catch-all
    url(r'^.*$', BomList.as_view(), name='api-bom-list'),
]
