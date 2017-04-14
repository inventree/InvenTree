from rest_framework import generics, permissions
import django_filters

from InvenTree.models import FilterChildren
from .models import StockLocation, StockItem
from .serializers import StockItemSerializer, LocationDetailSerializer


class StockDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class StockFilter(django_filters.rest_framework.FilterSet):
    min_stock = django_filters.NumberFilter(name='quantity', lookup_expr='gte')
    max_stock = django_filters.NumberFilter(name='quantity', lookup_expr='lte')

    class Meta:
        model = StockItem
        fields = ['quantity']


class StockList(generics.ListCreateAPIView):

    serializer_class = StockItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = StockFilter

    def get_queryset(self):
        items = StockItem.objects.all()

        # Specify a particular part
        part_id = self.request.query_params.get('part', None)
        if part_id:
            items = items.filter(part=part_id)

        # Specify a particular location
        loc_id = self.request.query_params.get('location', None)

        if loc_id:
            items = items.filter(location=loc_id)

        return items


class LocationDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Return information on a specific stock location
    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class LocationList(generics.ListCreateAPIView):
    """ Return a list of top-level locations
    Locations are considered "top-level" if they do not have a parent
    """

    def get_queryset(self):
        params = self.request.query_params

        locations = StockLocation.objects.all()

        locations = FilterChildren(locations, params.get('parent', None))

        return locations

    serializer_class = LocationDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
