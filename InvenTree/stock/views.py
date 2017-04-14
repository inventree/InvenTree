import django_filters
from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from django_filters import NumberFilter

from rest_framework import generics, permissions

# from InvenTree.models import FilterChildren
from .models import StockLocation, StockItem
from .serializers import StockItemSerializer, LocationSerializer


class StockDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class StockFilter(django_filters.rest_framework.FilterSet):
    min_stock = NumberFilter(name='quantity', lookup_expr='gte')
    max_stock = NumberFilter(name='quantity', lookup_expr='lte')
    part = NumberFilter(name='part', lookup_expr='exact')
    location = NumberFilter(name='location', lookup_expr='exact')

    class Meta:
        model = StockItem
        fields = ['quantity', 'part', 'location']


class StockList(generics.ListCreateAPIView):

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = StockFilter


class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Return information on a specific stock location
    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class StockLocationFilter(FilterSet):

    parent = NumberFilter(name='parent', lookup_expr='exact')

    class Meta:
        model = StockLocation
        fields = ['parent']


class LocationList(generics.ListCreateAPIView):
    """ Return a list of top-level locations
    Locations are considered "top-level" if they do not have a parent
    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = StockLocationFilter
