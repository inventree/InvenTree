from django_filters.rest_framework import FilterSet, DjangoFilterBackend
from django_filters import NumberFilter

from rest_framework import generics, permissions

from .models import Supplier, SupplierPart, SupplierPriceBreak
from .models import Manufacturer, Customer
from .serializers import SupplierSerializer
from .serializers import SupplierPartSerializer
from .serializers import SupplierPriceBreakSerializer
from .serializers import ManufacturerSerializer
from .serializers import CustomerSerializer


class ManufacturerDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ManufacturerList(generics.ListCreateAPIView):

    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class CustomerList(generics.ListCreateAPIView):

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierList(generics.ListCreateAPIView):

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierPartDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierPartFilter(FilterSet):

    supplier = NumberFilter(name='supplier', lookup_expr='exact')

    part = NumberFilter(name='part', lookup_expr='exact')

    manufacturer = NumberFilter(name='manufacturer', lookup_expr='exact')

    class Meta:
        model = SupplierPart
        fields = ['supplier', 'part', 'manufacturer']


class SupplierPartList(generics.ListCreateAPIView):

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    filter_backends = (DjangoFilterBackend,)
    filter_class = SupplierPartFilter


class SupplierPriceBreakDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PriceBreakFilter(FilterSet):

    part = NumberFilter(name='part', lookup_expr='exact')

    class Meta:
        model = SupplierPriceBreak
        fields = ['part']


class SupplierPriceBreakList(generics.ListCreateAPIView):

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    filter_backends = (DjangoFilterBackend,)
    filter_class = PriceBreakFilter
