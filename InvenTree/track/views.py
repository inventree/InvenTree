import django_filters

from rest_framework import generics, permissions

from .models import UniquePart, PartTrackingInfo
from .serializers import UniquePartSerializer, PartTrackingInfoSerializer


class UniquePartDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = UniquePart.objects.all()
    serializer_class = UniquePartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class UniquePartFilter(django_filters.rest_framework.FilterSet):
    # Filter based on serial number
    min_sn = django_filters.NumberFilter(name='serial', lookup_expr='gte')
    max_sn = django_filters.NumberFilter(name='serial', lookup_expr='lte')

    class Meta:
        model = UniquePart
        fields = ['serial', ]


class UniquePartList(generics.ListCreateAPIView):

    serializer_class = UniquePartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = UniquePartFilter

    def get_queryset(self):
        parts = UniquePart.objects.all()
        query = self.request.query_params

        # Filter by associated part
        part_id = query.get('part', None)
        if part_id:
            parts = parts.filter(part=part_id)

        # Filter by serial number
        sn = query.get('sn', None)
        if sn:
            parts = parts.filter(serial=sn)

        # Filter by customer
        customer = query.get('customer', None)
        if customer:
            parts = parts.filter(customer=customer)

        return parts


class PartTrackingDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = PartTrackingInfo.objects.all()
    serializer_class = PartTrackingInfoSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartTrackingList(generics.ListCreateAPIView):

    serializer_class = PartTrackingInfoSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        tracking = PartTrackingInfo.objects.all()
        query = self.request.query_params

        part_id = query.get('part', None)
        if part_id:
            tracking = tracking.filter(part=part_id)

        return tracking
