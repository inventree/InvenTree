from django_filters.rest_framework import FilterSet, DjangoFilterBackend

from rest_framework import generics, permissions

from .models import Supplier, SupplierPart, SupplierPriceBreak
from .models import Manufacturer, Customer
from .serializers import SupplierSerializer
from .serializers import SupplierPartSerializer
from .serializers import SupplierPriceBreakSerializer
from .serializers import ManufacturerSerializer
from .serializers import CustomerSerializer


class ManufacturerDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single Manufacturer

    post:
    Update a Manufacturer

    delete:
    Remove a Manufacturer

    """

    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ManufacturerList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all Manufacturers

    post:
    Create a new Manufacturer

    """

    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single Customer

    post:
    Update a Customer

    delete:
    Remove a Customer

    """

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class CustomerList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all Cutstomers

    post:
    Create a new Customer

    """

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single Supplier

    post:
    Update a supplier

    delete:
    Remove a supplier

    """

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all Suppliers

    post:
    Create a new Supplier

    """

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierPartDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single SupplierPart

    post:
    Update a SupplierPart

    delete:
    Remove a SupplierPart

    """

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SupplierPartFilter(FilterSet):

    class Meta:
        model = SupplierPart
        fields = ['supplier', 'part', 'manufacturer']


class SupplierPartList(generics.ListCreateAPIView):
    """

    get:
    List all SupplierParts
    (with optional query filters)

    post:
    Create a new SupplierPart

    """

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    filter_backends = (DjangoFilterBackend,)
    filter_class = SupplierPartFilter


class SupplierPriceBreakDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single SupplierPriceBreak

    post:
    Update a SupplierPriceBreak

    delete:
    Remove a SupplierPriceBreak

    """

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PriceBreakFilter(FilterSet):

    class Meta:
        model = SupplierPriceBreak
        fields = ['part']


class SupplierPriceBreakList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all SupplierPriceBreaks
    (with optional query filters)

    post:
    Create a new SupplierPriceBreak

    """

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    filter_backends = (DjangoFilterBackend,)
    filter_class = PriceBreakFilter
