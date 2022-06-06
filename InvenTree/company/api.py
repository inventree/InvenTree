"""Provides a JSON API for the Company app."""

from django.db.models import Q
from django.urls import include, re_path

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from InvenTree.api import AttachmentMixin, ListCreateDestroyAPIView
from InvenTree.helpers import str2bool

from .models import (Company, ManufacturerPart, ManufacturerPartAttachment,
                     ManufacturerPartParameter, SupplierPart,
                     SupplierPriceBreak)
from .serializers import (CompanySerializer,
                          ManufacturerPartAttachmentSerializer,
                          ManufacturerPartParameterSerializer,
                          ManufacturerPartSerializer, SupplierPartSerializer,
                          SupplierPriceBreakSerializer)


class CompanyList(generics.ListCreateAPIView):
    """API endpoint for accessing a list of Company objects.

    Provides two methods:

    - GET: Return list of objects
    - POST: Create a new Company object
    """

    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        """Return annotated queryset for the company list endpoint"""
        queryset = super().get_queryset()
        queryset = CompanySerializer.annotate_queryset(queryset)

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'is_customer',
        'is_manufacturer',
        'is_supplier',
        'name',
    ]

    search_fields = [
        'name',
        'description',
        'website',
    ]

    ordering_fields = [
        'name',
        'parts_supplied',
        'parts_manufactured',
    ]

    ordering = 'name'


class CompanyDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for detail of a single Company object."""

    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):
        """Return annotated queryset for the company detail endpoint"""
        queryset = super().get_queryset()
        queryset = CompanySerializer.annotate_queryset(queryset)

        return queryset


class ManufacturerPartFilter(rest_filters.FilterSet):
    """Custom API filters for the ManufacturerPart list endpoint."""

    class Meta:
        """Metaclass options."""

        model = ManufacturerPart
        fields = [
            'manufacturer',
            'MPN',
            'part',
        ]

    # Filter by 'active' status of linked part
    active = rest_filters.BooleanFilter(field_name='part__active')


class ManufacturerPartList(ListCreateDestroyAPIView):
    """API endpoint for list view of ManufacturerPart object.

    - GET: Return list of ManufacturerPart objects
    - POST: Create a new ManufacturerPart object
    """

    queryset = ManufacturerPart.objects.all().prefetch_related(
        'part',
        'manufacturer',
        'supplier_parts',
    )

    serializer_class = ManufacturerPartSerializer
    filterset_class = ManufacturerPartFilter

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint"""
        # Do we wish to include extra detail?
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', None))
            kwargs['manufacturer_detail'] = str2bool(params.get('manufacturer_detail', None))
            kwargs['pretty'] = str2bool(params.get('pretty', None))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        'manufacturer__name',
        'description',
        'MPN',
        'part__IPN',
        'part__name',
        'part__description',
    ]


class ManufacturerPartDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for detail view of ManufacturerPart object.

    - GET: Retrieve detail view
    - PATCH: Update object
    - DELETE: Delete object
    """

    queryset = ManufacturerPart.objects.all()
    serializer_class = ManufacturerPartSerializer


class ManufacturerPartAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) a ManufacturerPartAttachment (file upload)."""

    queryset = ManufacturerPartAttachment.objects.all()
    serializer_class = ManufacturerPartAttachmentSerializer

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'manufacturer_part',
    ]


class ManufacturerPartAttachmentDetail(AttachmentMixin, generics.RetrieveUpdateDestroyAPIView):
    """Detail endpooint for ManufacturerPartAttachment model."""

    queryset = ManufacturerPartAttachment.objects.all()
    serializer_class = ManufacturerPartAttachmentSerializer


class ManufacturerPartParameterList(ListCreateDestroyAPIView):
    """API endpoint for list view of ManufacturerPartParamater model."""

    queryset = ManufacturerPartParameter.objects.all()
    serializer_class = ManufacturerPartParameterSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint"""
        # Do we wish to include any extra detail?
        try:
            params = self.request.query_params

            optional_fields = [
                'manufacturer_part_detail',
            ]

            for key in optional_fields:
                kwargs[key] = str2bool(params.get(key, None))

        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def filter_queryset(self, queryset):
        """Custom filtering for the queryset."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by manufacturer?
        manufacturer = params.get('manufacturer', None)

        if manufacturer is not None:
            queryset = queryset.filter(manufacturer_part__manufacturer=manufacturer)

        # Filter by part?
        part = params.get('part', None)

        if part is not None:
            queryset = queryset.filter(manufacturer_part__part=part)

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'name',
        'value',
        'units',
        'manufacturer_part',
    ]

    search_fields = [
        'name',
        'value',
        'units',
    ]


class ManufacturerPartParameterDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for detail view of ManufacturerPartParameter model."""

    queryset = ManufacturerPartParameter.objects.all()
    serializer_class = ManufacturerPartParameterSerializer


class SupplierPartList(ListCreateDestroyAPIView):
    """API endpoint for list view of SupplierPart object.

    - GET: Return list of SupplierPart objects
    - POST: Create a new SupplierPart object
    """

    queryset = SupplierPart.objects.all()

    def filter_queryset(self, queryset):
        """Custom filtering for the queryset."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by manufacturer
        manufacturer = params.get('manufacturer', None)

        if manufacturer is not None:
            queryset = queryset.filter(manufacturer_part__manufacturer=manufacturer)

        # Filter by supplier
        supplier = params.get('supplier', None)

        if supplier is not None:
            queryset = queryset.filter(supplier=supplier)

        # Filter by EITHER manufacturer or supplier
        company = params.get('company', None)

        if company is not None:
            queryset = queryset.filter(Q(manufacturer_part__manufacturer=company) | Q(supplier=company))

        # Filter by parent part?
        part = params.get('part', None)

        if part is not None:
            queryset = queryset.filter(part=part)

        # Filter by manufacturer part?
        manufacturer_part = params.get('manufacturer_part', None)

        if manufacturer_part is not None:
            queryset = queryset.filter(manufacturer_part=manufacturer_part)

        # Filter by 'active' status of the part?
        active = params.get('active', None)

        if active is not None:
            active = str2bool(active)
            queryset = queryset.filter(part__active=active)

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint"""

        # Do we wish to include extra detail?
        try:
            params = self.request.query_params
            kwargs['part_detail'] = str2bool(params.get('part_detail', None))
            kwargs['supplier_detail'] = str2bool(params.get('supplier_detail', True))
            kwargs['manufacturer_detail'] = str2bool(params.get('manufacturer_detail', None))
            kwargs['pretty'] = str2bool(params.get('pretty', None))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    serializer_class = SupplierPartSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
    ]

    search_fields = [
        'SKU',
        'supplier__name',
        'manufacturer_part__manufacturer__name',
        'description',
        'manufacturer_part__MPN',
        'part__IPN',
        'part__name',
        'part__description',
    ]


class SupplierPartDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for detail view of SupplierPart object.

    - GET: Retrieve detail view
    - PATCH: Update object
    - DELETE: Delete object
    """

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer

    read_only_fields = [
    ]


class SupplierPriceBreakList(generics.ListCreateAPIView):
    """API endpoint for list view of SupplierPriceBreak object.

    - GET: Retrieve list of SupplierPriceBreak objects
    - POST: Create a new SupplierPriceBreak object
    """

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'part',
    ]


class SupplierPriceBreakDetail(generics.RetrieveUpdateDestroyAPIView):
    """Detail endpoint for SupplierPriceBreak object."""

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer


manufacturer_part_api_urls = [

    # Base URL for ManufacturerPartAttachment API endpoints
    re_path(r'^attachment/', include([
        re_path(r'^(?P<pk>\d+)/', ManufacturerPartAttachmentDetail.as_view(), name='api-manufacturer-part-attachment-detail'),
        re_path(r'^$', ManufacturerPartAttachmentList.as_view(), name='api-manufacturer-part-attachment-list'),
    ])),

    re_path(r'^parameter/', include([
        re_path(r'^(?P<pk>\d+)/', ManufacturerPartParameterDetail.as_view(), name='api-manufacturer-part-parameter-detail'),

        # Catch anything else
        re_path(r'^.*$', ManufacturerPartParameterList.as_view(), name='api-manufacturer-part-parameter-list'),
    ])),

    re_path(r'^(?P<pk>\d+)/?', ManufacturerPartDetail.as_view(), name='api-manufacturer-part-detail'),

    # Catch anything else
    re_path(r'^.*$', ManufacturerPartList.as_view(), name='api-manufacturer-part-list'),
]


supplier_part_api_urls = [

    re_path(r'^(?P<pk>\d+)/?', SupplierPartDetail.as_view(), name='api-supplier-part-detail'),

    # Catch anything else
    re_path(r'^.*$', SupplierPartList.as_view(), name='api-supplier-part-list'),
]


company_api_urls = [
    re_path(r'^part/manufacturer/', include(manufacturer_part_api_urls)),

    re_path(r'^part/', include(supplier_part_api_urls)),

    # Supplier price breaks
    re_path(r'^price-break/', include([

        re_path(r'^(?P<pk>\d+)/?', SupplierPriceBreakDetail.as_view(), name='api-part-supplier-price-detail'),
        re_path(r'^.*$', SupplierPriceBreakList.as_view(), name='api-part-supplier-price-list'),
    ])),

    re_path(r'^(?P<pk>\d+)/?', CompanyDetail.as_view(), name='api-company-detail'),

    re_path(r'^.*$', CompanyList.as_view(), name='api-company-list'),
]
