import django_filters
from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from django_filters import NumberFilter

from rest_framework import generics, permissions

# from InvenTree.models import FilterChildren
from .models import StockLocation, StockItem
from .serializers import StockItemSerializer, LocationSerializer


class StockDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single StockItem object

    post:
    Update a StockItem

    delete:
    Remove a StockItem
    """

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class StockFilter(FilterSet):
    min_stock = NumberFilter(name='quantity', lookup_expr='gte')
    max_stock = NumberFilter(name='quantity', lookup_expr='lte')
    part = NumberFilter(name='part', lookup_expr='exact')
    location = NumberFilter(name='location', lookup_expr='exact')

    class Meta:
        model = StockItem
        fields = ['quantity', 'part', 'location']


class StockList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all StockItem objects
    (with optional query filters)

    post:
    Create a new StockItem
    """

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = StockFilter


class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single StockLocation object

    post:
    Update a StockLocation object

    delete:
    Remove a StockLocation object

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
    """

    get:
    Return a list of all StockLocation objects
    (with optional query filter)

    post:
    Create a new StockLocation

    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = StockLocationFilter
