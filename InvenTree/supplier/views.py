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


class SupplierPartList(generics.ListCreateAPIView):

    serializer_class = SupplierPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        parts = SupplierPart.objects.all()
        params = self.request.query_params

        supplier_id = params.get('supplier', None)
        if supplier_id:
            parts = parts.filter(supplier=supplier_id)

        part_id = params.get('part', None)
        if part_id:
            parts = parts.filter(part=part_id)

        manu_id = params.get('manufacturer', None)
        if manu_id:
            parts = parts.filter(manufacturer=manu_id)

        return parts


class SupplierPriceBreakDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierPriceBreakList(generics.ListCreateAPIView):

    def get_queryset(self):
        prices = SupplierPriceBreak.objects.all()
        params = self.request.query_params

        part_id = params.get('part', None)
        if part_id:
            prices = prices.filter(part=part_id)

        return prices

    serializer_class = SupplierPriceBreakSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
