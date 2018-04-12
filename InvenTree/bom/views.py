from django_filters.rest_framework import FilterSet, DjangoFilterBackend

from rest_framework import generics, permissions

from InvenTree.models import FilterChildren

from .models import BomItem

from .serializers import BomItemSerializer


class BomItemDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = BomItem.objects.all()
    serializer_class = BomItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class BomItemFilter(FilterSet):

    class Meta:
        model = BomItem
        fields = ['part', 'sub_part']


class BomItemList(generics.ListCreateAPIView):

    #def get_queryset(self):
    #    params = self.request.

    queryset = BomItem.objects.all()
    serializer_class = BomItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = BomItemFilter