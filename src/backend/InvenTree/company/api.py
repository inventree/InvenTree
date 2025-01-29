"""Provides a JSON API for the Company app."""

from django.db.models import Q
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters

import part.models
from importer.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import SEARCH_ORDER_FILTER, SEARCH_ORDER_FILTER_ALIAS
from InvenTree.helpers import str2bool
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI

from .models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    ManufacturerPartParameter,
    SupplierPart,
    SupplierPriceBreak,
)
from .serializers import (
    AddressSerializer,
    CompanySerializer,
    ContactSerializer,
    ManufacturerPartParameterSerializer,
    ManufacturerPartSerializer,
    SupplierPartSerializer,
    SupplierPriceBreakSerializer,
)


class CompanyList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of Company objects.

    Provides two methods:

    - GET: Return list of objects
    - POST: Create a new Company object
    """

    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        """Return annotated queryset for the company list endpoint."""
        queryset = super().get_queryset()
        return CompanySerializer.annotate_queryset(queryset)

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = [
        'is_customer',
        'is_manufacturer',
        'is_supplier',
        'name',
        'active',
    ]

    search_fields = ['name', 'description', 'website']

    ordering_fields = ['active', 'name', 'parts_supplied', 'parts_manufactured']

    ordering = 'name'


class CompanyDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail of a single Company object."""

    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):
        """Return annotated queryset for the company detail endpoint."""
        queryset = super().get_queryset()
        queryset = CompanySerializer.annotate_queryset(queryset)

        return queryset


class ContactList(DataExportViewMixin, ListCreateDestroyAPIView):
    """API endpoint for list view of Company model."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['company']

    search_fields = ['company__name', 'name']

    ordering_fields = ['name']

    ordering = 'name'


class ContactDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for Company model."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class AddressList(DataExportViewMixin, ListCreateDestroyAPIView):
    """API endpoint for list view of Address model."""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['company']

    ordering_fields = ['title']

    ordering = 'title'


class AddressDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single Address object."""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class ManufacturerPartFilter(rest_filters.FilterSet):
    """Custom API filters for the ManufacturerPart list endpoint."""

    class Meta:
        """Metaclass options."""

        model = ManufacturerPart
        fields = ['manufacturer', 'MPN', 'part', 'tags__name', 'tags__slug']

    # Filter by 'active' status of linked part
    part_active = rest_filters.BooleanFilter(
        field_name='part__active', label=_('Part is Active')
    )

    manufacturer_active = rest_filters.BooleanFilter(
        field_name='manufacturer__active', label=_('Manufacturer is Active')
    )


class ManufacturerPartList(DataExportViewMixin, ListCreateDestroyAPIView):
    """API endpoint for list view of ManufacturerPart object.

    - GET: Return list of ManufacturerPart objects
    - POST: Create a new ManufacturerPart object
    """

    queryset = ManufacturerPart.objects.all().prefetch_related(
        'part', 'manufacturer', 'supplier_parts', 'tags'
    )

    serializer_class = ManufacturerPartSerializer
    filterset_class = ManufacturerPartFilter

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        # Do we wish to include extra detail?
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', None))
            kwargs['manufacturer_detail'] = str2bool(
                params.get('manufacturer_detail', None)
            )
            kwargs['pretty'] = str2bool(params.get('pretty', None))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = [
        'manufacturer__name',
        'description',
        'MPN',
        'part__IPN',
        'part__name',
        'part__description',
        'tags__name',
        'tags__slug',
    ]


class ManufacturerPartDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of ManufacturerPart object.

    - GET: Retrieve detail view
    - PATCH: Update object
    - DELETE: Delete object
    """

    queryset = ManufacturerPart.objects.all()
    serializer_class = ManufacturerPartSerializer


class ManufacturerPartParameterFilter(rest_filters.FilterSet):
    """Custom filterset for the ManufacturerPartParameterList API endpoint."""

    class Meta:
        """Metaclass options."""

        model = ManufacturerPartParameter
        fields = ['name', 'value', 'units', 'manufacturer_part']

    manufacturer = rest_filters.ModelChoiceFilter(
        queryset=Company.objects.all(), field_name='manufacturer_part__manufacturer'
    )

    part = rest_filters.ModelChoiceFilter(
        queryset=part.models.Part.objects.all(), field_name='manufacturer_part__part'
    )


class ManufacturerPartParameterList(ListCreateDestroyAPIView):
    """API endpoint for list view of ManufacturerPartParamater model."""

    queryset = ManufacturerPartParameter.objects.all()
    serializer_class = ManufacturerPartParameterSerializer
    filterset_class = ManufacturerPartParameterFilter

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        # Do we wish to include any extra detail?
        try:
            params = self.request.query_params

            optional_fields = ['manufacturer_part_detail']

            for key in optional_fields:
                kwargs[key] = str2bool(params.get(key, None))

        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['name', 'value', 'units']


class ManufacturerPartParameterDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of ManufacturerPartParameter model."""

    queryset = ManufacturerPartParameter.objects.all()
    serializer_class = ManufacturerPartParameterSerializer


class SupplierPartFilter(rest_filters.FilterSet):
    """API filters for the SupplierPartList endpoint."""

    class Meta:
        """Metaclass option."""

        model = SupplierPart
        fields = [
            'supplier',
            'part',
            'manufacturer_part',
            'SKU',
            'tags__name',
            'tags__slug',
        ]

    active = rest_filters.BooleanFilter(label=_('Supplier Part is Active'))

    # Filter by 'active' status of linked part
    part_active = rest_filters.BooleanFilter(
        field_name='part__active', label=_('Internal Part is Active')
    )

    # Filter by 'active' status of linked supplier
    supplier_active = rest_filters.BooleanFilter(
        field_name='supplier__active', label=_('Supplier is Active')
    )

    # Filter by the 'MPN' of linked manufacturer part
    MPN = rest_filters.CharFilter(
        label='Manufacturer Part Number',
        field_name='manufacturer_part__MPN',
        lookup_expr='iexact',
    )

    # Filter by 'manufacturer'
    manufacturer = rest_filters.ModelChoiceFilter(
        label=_('Manufacturer'),
        queryset=Company.objects.all(),
        field_name='manufacturer_part__manufacturer',
    )

    # Filter by 'company' (either manufacturer or supplier)
    company = rest_filters.ModelChoiceFilter(
        label=_('Company'), queryset=Company.objects.all(), method='filter_company'
    )

    def filter_company(self, queryset, name, value):
        """Filter the queryset by either manufacturer or supplier."""
        return queryset.filter(
            Q(manufacturer_part__manufacturer=value) | Q(supplier=value)
        ).distinct()

    has_stock = rest_filters.BooleanFilter(
        label=_('Has Stock'), method='filter_has_stock'
    )

    def filter_has_stock(self, queryset, name, value):
        """Filter the queryset based on whether the SupplierPart has stock available."""
        if value:
            return queryset.filter(in_stock__gt=0)
        else:
            return queryset.exclude(in_stock__gt=0)


class SupplierPartMixin:
    """Mixin class for SupplierPart API endpoints."""

    queryset = SupplierPart.objects.all().prefetch_related('tags')
    serializer_class = SupplierPartSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryest object for the SupplierPart list."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = SupplierPartSerializer.annotate_queryset(queryset)

        queryset = queryset.prefetch_related('part', 'part__pricing_data')

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        # Do we wish to include extra detail?
        try:
            params = self.request.query_params
            kwargs['part_detail'] = str2bool(params.get('part_detail', None))
            kwargs['supplier_detail'] = str2bool(params.get('supplier_detail', True))
            kwargs['manufacturer_detail'] = str2bool(
                params.get('manufacturer_detail', None)
            )
            kwargs['pretty'] = str2bool(params.get('pretty', None))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)


class SupplierPartList(
    DataExportViewMixin, SupplierPartMixin, ListCreateDestroyAPIView
):
    """API endpoint for list view of SupplierPart object.

    - GET: Return list of SupplierPart objects
    - POST: Create a new SupplierPart object
    """

    filterset_class = SupplierPartFilter

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = [
        'SKU',
        'part',
        'supplier',
        'manufacturer',
        'active',
        'MPN',
        'packaging',
        'pack_quantity',
        'in_stock',
        'updated',
    ]

    ordering_field_aliases = {
        'part': 'part__name',
        'supplier': 'supplier__name',
        'manufacturer': 'manufacturer_part__manufacturer__name',
        'MPN': 'manufacturer_part__MPN',
        'pack_quantity': ['pack_quantity_native', 'pack_quantity'],
    }

    search_fields = [
        'SKU',
        'supplier__name',
        'manufacturer_part__manufacturer__name',
        'description',
        'manufacturer_part__MPN',
        'part__IPN',
        'part__name',
        'part__description',
        'part__keywords',
        'tags__name',
        'tags__slug',
    ]


class SupplierPartDetail(SupplierPartMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of SupplierPart object.

    - GET: Retrieve detail view
    - PATCH: Update object
    - DELETE: Delete object
    """


class SupplierPriceBreakFilter(rest_filters.FilterSet):
    """Custom API filters for the SupplierPriceBreak list endpoint."""

    class Meta:
        """Metaclass options."""

        model = SupplierPriceBreak
        fields = ['part', 'quantity']

    base_part = rest_filters.ModelChoiceFilter(
        label='Base Part',
        queryset=part.models.Part.objects.all(),
        field_name='part__part',
    )

    supplier = rest_filters.ModelChoiceFilter(
        label='Supplier', queryset=Company.objects.all(), field_name='part__supplier'
    )


class SupplierPriceBreakList(ListCreateAPI):
    """API endpoint for list view of SupplierPriceBreak object.

    - GET: Retrieve list of SupplierPriceBreak objects
    - POST: Create a new SupplierPriceBreak object
    """

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer
    filterset_class = SupplierPriceBreakFilter

    def get_queryset(self):
        """Return annotated queryset for the SupplierPriceBreak list endpoint."""
        queryset = super().get_queryset()
        queryset = SupplierPriceBreakSerializer.annotate_queryset(queryset)

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['supplier_detail'] = str2bool(params.get('supplier_detail', False))

        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = ['quantity', 'supplier', 'SKU', 'price']

    search_fields = ['part__SKU', 'part__supplier__name']

    ordering_field_aliases = {'supplier': 'part__supplier__name', 'SKU': 'part__SKU'}

    ordering = 'quantity'


class SupplierPriceBreakDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for SupplierPriceBreak object."""

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer

    def get_queryset(self):
        """Return annotated queryset for the SupplierPriceBreak list endpoint."""
        queryset = super().get_queryset()
        queryset = SupplierPriceBreakSerializer.annotate_queryset(queryset)

        return queryset


manufacturer_part_api_urls = [
    path(
        'parameter/',
        include([
            path(
                '<int:pk>/',
                ManufacturerPartParameterDetail.as_view(),
                name='api-manufacturer-part-parameter-detail',
            ),
            # Catch anything else
            path(
                '',
                ManufacturerPartParameterList.as_view(),
                name='api-manufacturer-part-parameter-list',
            ),
        ]),
    ),
    re_path(
        r'^(?P<pk>\d+)/?',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': ManufacturerPart},
                name='api-manufacturer-part-metadata',
            ),
            path(
                '',
                ManufacturerPartDetail.as_view(),
                name='api-manufacturer-part-detail',
            ),
        ]),
    ),
    # Catch anything else
    path('', ManufacturerPartList.as_view(), name='api-manufacturer-part-list'),
]


supplier_part_api_urls = [
    re_path(
        r'^(?P<pk>\d+)/?',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': SupplierPart},
                name='api-supplier-part-metadata',
            ),
            path('', SupplierPartDetail.as_view(), name='api-supplier-part-detail'),
        ]),
    ),
    # Catch anything else
    path('', SupplierPartList.as_view(), name='api-supplier-part-list'),
]


company_api_urls = [
    path('part/manufacturer/', include(manufacturer_part_api_urls)),
    path('part/', include(supplier_part_api_urls)),
    # Supplier price breaks
    path(
        'price-break/',
        include([
            re_path(
                r'^(?P<pk>\d+)/?',
                SupplierPriceBreakDetail.as_view(),
                name='api-part-supplier-price-detail',
            ),
            path(
                '',
                SupplierPriceBreakList.as_view(),
                name='api-part-supplier-price-list',
            ),
        ]),
    ),
    re_path(
        r'^(?P<pk>\d+)/?',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': Company},
                name='api-company-metadata',
            ),
            path('', CompanyDetail.as_view(), name='api-company-detail'),
        ]),
    ),
    path(
        'contact/',
        include([
            re_path(
                r'^(?P<pk>\d+)/?',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': Contact},
                        name='api-contact-metadata',
                    ),
                    path('', ContactDetail.as_view(), name='api-contact-detail'),
                ]),
            ),
            path('', ContactList.as_view(), name='api-contact-list'),
        ]),
    ),
    path(
        'address/',
        include([
            path('<int:pk>/', AddressDetail.as_view(), name='api-address-detail'),
            path('', AddressList.as_view(), name='api-address-list'),
        ]),
    ),
    path('', CompanyList.as_view(), name='api-company-list'),
]
