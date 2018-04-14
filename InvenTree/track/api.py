from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from django_filters import NumberFilter

from rest_framework import generics, permissions

from .models import UniquePart, PartTrackingInfo
from .serializers import UniquePartSerializer, PartTrackingInfoSerializer


class UniquePartDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single UniquePart

    post:
    Update a UniquePart

    delete:
    Remove a UniquePart

    """

    queryset = UniquePart.objects.all()
    serializer_class = UniquePartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class UniquePartFilter(FilterSet):
    # Filter based on serial number
    min_sn = NumberFilter(name='serial', lookup_expr='gte')
    max_sn = NumberFilter(name='serial', lookup_expr='lte')

    class Meta:
        model = UniquePart
        fields = ['serial', 'part', 'customer']


class UniquePartList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all UniqueParts
    (with optional query filter)

    post:
    Create a new UniquePart
    """

    queryset = UniquePart.objects.all()
    serializer_class = UniquePartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = UniquePartFilter


class PartTrackingDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single PartTrackingInfo object

    post:
    Update a PartTrackingInfo object

    delete:
    Remove a PartTrackingInfo object
    """

    queryset = PartTrackingInfo.objects.all()
    serializer_class = PartTrackingInfoSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartTrackingFilter(FilterSet):

    class Meta:
        model = PartTrackingInfo
        fields = ['part']


class PartTrackingList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all PartTrackingInfo objects
    (with optional query filter)

    post:
    Create a new PartTrackingInfo object
    """

    queryset = PartTrackingInfo.objects.all()
    serializer_class = PartTrackingInfoSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = PartTrackingFilter
