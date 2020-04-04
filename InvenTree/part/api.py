"""
Provides a JSON API for the Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from django.db.models import Q, Sum, Count

from rest_framework import status
from rest_framework.response import Response
from rest_framework import filters, serializers
from rest_framework import generics, permissions

from django.conf.urls import url, include
from django.urls import reverse

import os

from .models import Part, PartCategory, BomItem, PartStar
from .models import PartParameter, PartParameterTemplate

from . import serializers as part_serializers

from InvenTree.status_codes import OrderStatus, StockStatus, BuildStatus
from InvenTree.views import TreeSerializer
from InvenTree.helpers import str2bool, isNull


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


class PartThumbs(generics.ListAPIView):
    """ API endpoint for retrieving information on available Part thumbnails """

    serializer_class = part_serializers.PartThumbSerializer

    def list(self, reguest, *args, **kwargs):
        """
        Serialize the available Part images.
        - Images may be used for multiple parts!
        """

        # Get all Parts which have an associated image
        queryset = Part.objects.all().exclude(image='')

        # Return the most popular parts first
        data = queryset.values(
            'image',
        ).annotate(count=Count('image')).order_by('-count')

        return Response(data)


class PartDetail(generics.RetrieveUpdateAPIView):
    """ API endpoint for detail view of a single Part object """

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]


class PartList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Part objects

    - GET: Return list of objects
    - POST: Create a new Part object
    """

    serializer_class = part_serializers.PartSerializer

    def create(self, request, *args, **kwargs):
        """ Override the default 'create' behaviour:
        We wish to save the user who created this part!

        Note: Implementation coped from DRF class CreateModelMixin
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Record the user who created this Part object
        part = serializer.save()
        part.creation_user = request.user
        part.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        """
        Instead of using the DRF serialiser to LIST,
        we serialize the objects manually.
        This turns out to be significantly faster.
        """

        queryset = self.filter_queryset(self.get_queryset())

        # Filters for annotations

        # "in_stock" count should only sum stock items which are "in stock"
        stock_filter = Q(stock_items__status__in=StockStatus.AVAILABLE_CODES)

        # "on_order" items should only sum orders which are currently outstanding
        order_filter = Q(supplier_parts__purchase_order_line_items__order__status__in=OrderStatus.OPEN)

        # "building" should only reference builds which are active
        build_filter = Q(builds__status__in=BuildStatus.ACTIVE_CODES)

        # Set of fields we wish to serialize
        data = queryset.values(
            'pk',
            'category',
            'image',
            'name',
            'IPN',
            'revision',
            'description',
            'keywords',
            'is_template',
            'URL',
            'units',
            'minimum_stock',
            'trackable',
            'assembly',
            'component',
            'salable',
            'active',
        ).annotate(
            # Quantity of items which are "in stock"
            in_stock=Sum('stock_items__quantity', filter=stock_filter),
            on_order=Sum('supplier_parts__purchase_order_line_items__quantity', filter=order_filter),
            building=Sum('builds__quantity', filter=build_filter),
        )

        # Reduce the number of lookups we need to do for the part categories
        categories = {}

        for item in data:

            if item['image']:
                img = item['image']

                # Use the 'thumbnail' image here instead of the full-size image
                # Note: The full-size image is used when requesting the /api/part/<x>/ endpoint
                fn, ext = os.path.splitext(img)

                thumb = "{fn}.thumbnail{ext}".format(fn=fn, ext=ext)

                item['thumbnail'] = os.path.join(settings.MEDIA_URL, thumb)

                del item['image']

            cat_id = item['category']

            if cat_id:
                if cat_id not in categories:
                    categories[cat_id] = PartCategory.objects.get(pk=cat_id).pathstring

                item['category__name'] = categories[cat_id]
            else:
                item['category__name'] = None

        return Response(data)

    def get_queryset(self):

        # Does the user wish to filter by category?
        cat_id = self.request.query_params.get('category', None)

        # Start with all objects
        parts_list = Part.objects.all()

        cascade = str2bool(self.request.query_params.get('cascade', False))

        if cat_id is not None:

            if isNull(cat_id):
                parts_list = parts_list.filter(category=None)
            else:
                try:
                    cat_id = int(cat_id)
                    category = PartCategory.objects.get(pk=cat_id)

                    # If '?cascade=true' then include parts which exist in sub-categories
                    if cascade:
                        parts_list = parts_list.filter(category__in=category.getUniqueChildren())
                    # Just return parts directly in the requested category
                    else:
                        parts_list = parts_list.filter(category=cat_id)
                except (ValueError, PartCategory.DoesNotExist):
                    pass

        # Ensure that related models are pre-loaded to reduce DB trips
        parts_list = self.get_serializer_class().setup_eager_loading(parts_list)

        return parts_list

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
    ]

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
    
    def get_serializer(self, *args, **kwargs):

        # Do we wish to include extra detail?
        try:
            part_detail = str2bool(self.request.GET.get('part_detail', None))
            sub_part_detail = str2bool(self.request.GET.get('sub_part_detail', None))
        except AttributeError:
            part_detail = None
            sub_part_detail = None

        kwargs['part_detail'] = part_detail
        kwargs['sub_part_detail'] = sub_part_detail

        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        queryset = BomItem.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
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
        'part',
        'sub_part',
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


cat_api_urls = [

    url(r'^(?P<pk>\d+)/?', CategoryDetail.as_view(), name='api-part-category-detail'),

    url(r'^$', CategoryList.as_view(), name='api-part-category-list'),
]


part_star_api_urls = [
    url(r'^(?P<pk>\d+)/?', PartStarDetail.as_view(), name='api-part-star-detail'),

    # Catchall
    url(r'^.*$', PartStarList.as_view(), name='api-part-star-list'),
]

part_param_api_urls = [
    url(r'^template/$', PartParameterTemplateList.as_view(), name='api-part-param-template-list'),

    url(r'^.*$', PartParameterList.as_view(), name='api-part-param-list'),
]

part_api_urls = [
    url(r'^tree/?', PartCategoryTree.as_view(), name='api-part-tree'),

    url(r'^category/', include(cat_api_urls)),
    url(r'^star/', include(part_star_api_urls)),
    url(r'^parameter/', include(part_param_api_urls)),

    url(r'^thumbs/', PartThumbs.as_view(), name='api-part-thumbs'),

    url(r'^(?P<pk>\d+)/?', PartDetail.as_view(), name='api-part-detail'),

    url(r'^.*$', PartList.as_view(), name='api-part-list'),
]

bom_item_urls = [

    url(r'^validate/?', BomItemValidate.as_view(), name='api-bom-item-validate'),

    url(r'^.*$', BomDetail.as_view(), name='api-bom-item-detail'),
]

bom_api_urls = [
    # BOM Item Detail
    url(r'^(?P<pk>\d+)/', include(bom_item_urls)),

    # Catch-all
    url(r'^.*$', BomList.as_view(), name='api-bom-list'),
]
