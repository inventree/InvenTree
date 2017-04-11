from rest_framework import generics

from .models import StockLocation, StockItem

from .serializers import StockItemSerializer, LocationDetailSerializer


class PartStockDetail(generics.ListAPIView):
    """ Return a list of all stockitems for a given part
    """

    serializer_class = StockItemSerializer

    def get_queryset(self):
        part_id = self.kwargs['part']
        return StockItem.objects.filter(part=part_id)


class LocationDetail(generics.RetrieveAPIView):
    """ Return information on a specific stock location
    """

    queryset = StockLocation.objects.all()
    serializer_class = LocationDetailSerializer


class LocationList(generics.ListAPIView):
    """ Return a list of top-level locations
    Locations are considered "top-level" if they do not have a parent
    """

    queryset = StockLocation.objects.filter(parent=None)
    serializer_class = LocationDetailSerializer
