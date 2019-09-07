"""
Provides a JSON API for the Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from django.db.models import Sum

from rest_framework import status
from rest_framework.response import Response
from rest_framework import filters, serializers
from rest_framework import generics, permissions

from django.conf.urls import url, include
from django.urls import reverse

import os

from .models import Part, PartCategory, BomItem, PartStar
from .models import PartParameter, PartParameterTemplate

from .serializers import PartSerializer, BomItemSerializer
from .serializers import CategorySerializer
from .serializers import PartStarSerializer
from .serializers import PartParameterSerializer, PartParameterTemplateSerializer

from InvenTree.views import TreeSerializer
from InvenTree.helpers import str2bool


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
    serializer_class = CategorySerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'parent',
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
    serializer_class = CategorySerializer
    queryset = PartCategory.objects.all()


class PartDetail(generics.RetrieveUpdateAPIView):
    """ API endpoint for detail view of a single Part object """
    queryset = Part.objects.all()
    serializer_class = PartSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]


class PartList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Part objects

    - GET: Return list of objects
    - POST: Create a new Part object
    """

    serializer_class = PartSerializer

    def list(self, request, *args, **kwargs):
        """
        Instead of using the DRF serialiser to LIST,
        we serialize the objects manuually.
        This turns out to be significantly faster.
        """

        queryset = self.filter_queryset(self.get_queryset())

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
            'trackable',
            'assembly',
            'component',
            'salable',
            'active',
        ).annotate(
            in_stock=Sum('stock_items__quantity'),
        )

        # TODO - Annotate total being built
        # TODO - Annotate total on order

        # Reduce the number of lookups we need to do for the part categories
        categories = {}

        for item in data:

            if item['image']:
                item['image'] = os.path.join(settings.MEDIA_URL, item['image'])

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

        if cat_id:
            try:
                category = PartCategory.objects.get(pk=cat_id)
                parts_list = parts_list.filter(category__in=category.getUniqueChildren())
            except PartCategory.DoesNotExist:
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
    serializer_class = PartStarSerializer


class PartStarList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartStar objects.

    - GET: Return list of PartStar objects
    - POST: Create a new PartStar object
    """

    queryset = PartStar.objects.all()
    serializer_class = PartStarSerializer

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
    serializer_class = PartParameterTemplateSerializer

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
    serializer_class = PartParameterSerializer

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

    serializer_class = BomItemSerializer
    
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
    serializer_class = BomItemSerializer

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
