"""
Provides a JSON API for the Part app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status
from rest_framework.response import Response
from rest_framework import filters
from rest_framework import generics, permissions

from django.conf.urls import url, include
from django.urls import reverse

from .models import Part, PartCategory, BomItem, PartStar

from .serializers import PartSerializer, BomItemSerializer
from .serializers import CategorySerializer
from .serializers import PartStarSerializer

from InvenTree.views import TreeSerializer


class PartCategoryTree(TreeSerializer):

    title = "Parts"
    model = PartCategory
    
    @property
    def root_url(self):
        return reverse('part-index')


class CategoryList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PartCategory objects.

    - GET: Return a list of PartCategory objects
    - POST: Create a new PartCategory object
    """

    queryset = PartCategory.objects.all()
    serializer_class = CategorySerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        # filters.SearchFilter,
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
        permissions.IsAuthenticatedOrReadOnly,
    ]


class PartList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of Part objects

    - GET: Return list of objects
    - POST: Create a new Part object
    """

    serializer_class = PartSerializer

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

        return parts_list

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'buildable',
        'consumable',
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
        permissions.IsAuthenticatedOrReadOnly,
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


class BomList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of BomItem objects.

    - GET: Return list of BomItem objects
    - POST: Create a new BomItem object
    """

    queryset = BomItem.objects.all()
    serializer_class = BomItemSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'part',
        'sub_part'
    ]


class BomDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of a single BomItem object """

    queryset = BomItem.objects.all()
    serializer_class = BomItemSerializer

    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]


cat_api_urls = [

    url(r'^(?P<pk>\d+)/?', CategoryDetail.as_view(), name='api-part-category-detail'),

    url(r'^$', CategoryList.as_view(), name='api-part-category-list'),
]


part_star_api_urls = [
    url(r'^(?P<pk>\d+)/?', PartStarDetail.as_view(), name='api-part-star-detail'),

    # Catchall
    url(r'^.*$', PartStarList.as_view(), name='api-part-star-list'),
]


part_api_urls = [
    url(r'^tree/?', PartCategoryTree.as_view(), name='api-part-tree'),

    url(r'^category/', include(cat_api_urls)),
    url(r'^star/', include(part_star_api_urls)),

    url(r'^(?P<pk>\d+)/', PartDetail.as_view(), name='api-part-detail'),

    url(r'^.*$', PartList.as_view(), name='api-part-list'),
]


bom_api_urls = [
    # BOM Item Detail
    url('^(?P<pk>\d+)/', BomDetail.as_view(), name='api-bom-detail'),

    # Catch-all
    url(r'^.*$', BomList.as_view(), name='api-bom-list'),
]
