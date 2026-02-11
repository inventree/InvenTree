"""Provides a JSON API for the Company app."""

from django.db.models import Q
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

import django_filters.rest_framework.filters as rest_filters
from django_filters.rest_framework.filterset import FilterSet

import part.models
from data_exporter.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, ParameterListMixin, meta_path
from InvenTree.fields import InvenTreeOutputOption, OutputConfiguration
from InvenTree.filters import SEARCH_ORDER_FILTER, SEARCH_ORDER_FILTER_ALIAS
from InvenTree.mixins import (
    ListCreateAPI,
    OutputOptionsMixin,
    RetrieveUpdateDestroyAPI,
    SerializerContextMixin,
)

from .models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    SupplierPart,
    SupplierPriceBreak,
)
from .serializers import (
    AddressSerializer,
    CompanySerializer,
    ContactSerializer,
    ManufacturerPartSerializer,
    SupplierPartSerializer,
    SupplierPriceBreakSerializer,
)


class CompanyMixin(OutputOptionsMixin):
    """Mixin class for Company API endpoints."""

    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):
        """Return annotated queryset for the company endpoints."""
        queryset = super().get_queryset()
        queryset = CompanySerializer.annotate_queryset(queryset)

        return queryset


class CompanyList(CompanyMixin, ParameterListMixin, DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of Company objects.

    Provides two methods:

    - GET: Return list of objects
    - POST: Create a new Company object
    """

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = [
        'is_customer',
        'is_manufacturer',
        'is_supplier',
        'name',
        'active',
    ]

    search_fields = ['name', 'description', 'website', 'tax_id']

    ordering_fields = ['active', 'name', 'parts_supplied', 'parts_manufactured']

    ordering = 'name'


class CompanyDetail(CompanyMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail of a single Company object."""


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


class ManufacturerPartFilter(FilterSet):
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


class ManufacturerOutputOptions(OutputConfiguration):
    """Available output options for the ManufacturerPart endpoints."""

    OPTIONS = [
        InvenTreeOutputOption(
            description='Include detailed information about the linked Part in the response',
            flag='part_detail',
            default=False,
        ),
        InvenTreeOutputOption(
            description='Include detailed information about the Manufacturer in the response',
            flag='manufacturer_detail',
            default=False,
        ),
        InvenTreeOutputOption(
            description='Format the output with a more readable (pretty) name',
            flag='pretty',
            default=False,
        ),
    ]


class ManufacturerPartMixin(SerializerContextMixin):
    """Mixin class for ManufacturerPart API endpoints."""

    queryset = ManufacturerPart.objects.all()
    serializer_class = ManufacturerPartSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for the ManufacturerPart list endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('supplier_parts')

        return queryset


class ManufacturerPartList(
    ManufacturerPartMixin,
    SerializerContextMixin,
    OutputOptionsMixin,
    ParameterListMixin,
    ListCreateDestroyAPIView,
):
    """API endpoint for list view of ManufacturerPart object.

    - GET: Return list of ManufacturerPart objects
    - POST: Create a new ManufacturerPart object
    """

    filterset_class = ManufacturerPartFilter
    filter_backends = SEARCH_ORDER_FILTER_ALIAS
    output_options = ManufacturerOutputOptions

    ordering_fields = ['part', 'IPN', 'MPN', 'manufacturer']

    ordering_field_aliases = {
        'part': 'part__name',
        'IPN': 'part__IPN',
        'manufacturer': 'manufacturer__name',
    }

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


class ManufacturerPartDetail(
    ManufacturerPartMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI
):
    """API endpoint for detail view of ManufacturerPart object.

    - GET: Retrieve detail view
    - PATCH: Update object
    - DELETE: Delete object
    """


class SupplierPartFilter(FilterSet):
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

    def filter_company(self, queryset, name, value: int):
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


class SupplierPartOutputOptions(OutputConfiguration):
    """Available output options for the SupplierPart endpoints."""

    OPTIONS = [
        InvenTreeOutputOption(
            description='Include detailed information about the linked Part in the response',
            flag='part_detail',
            default=False,
        ),
        InvenTreeOutputOption(
            description='Include detailed information about the Supplier in the response',
            flag='supplier_detail',
            default=False,
        ),
        InvenTreeOutputOption(
            description='Include detailed information about the Manufacturer in the response',
            flag='manufacturer_detail',
            default=False,
        ),
        InvenTreeOutputOption(
            flag='manufacturer_part_detail',
            description='Include detailed information about the linked ManufacturerPart in the response',
            default=False,
        ),
        InvenTreeOutputOption(
            description='Format the output with a more readable (pretty) name',
            flag='pretty',
            default=False,
        ),
    ]


class SupplierPartMixin:
    """Mixin class for SupplierPart API endpoints."""

    queryset = SupplierPart.objects.all()
    serializer_class = SupplierPartSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset object for the SupplierPart list."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = SupplierPartSerializer.annotate_queryset(queryset)

        queryset = queryset.prefetch_related('part', 'part__pricing_data')

        return queryset


class SupplierPartList(
    DataExportViewMixin,
    SupplierPartMixin,
    ParameterListMixin,
    OutputOptionsMixin,
    ListCreateDestroyAPIView,
):
    """API endpoint for list view of SupplierPart object.

    - GET: Return list of SupplierPart objects
    - POST: Create a new SupplierPart object
    """

    filterset_class = SupplierPartFilter
    filter_backends = SEARCH_ORDER_FILTER_ALIAS
    output_options = SupplierPartOutputOptions

    ordering_fields = [
        'part',
        'supplier',
        'manufacturer',
        'active',
        'IPN',
        'MPN',
        'SKU',
        'packaging',
        'pack_quantity',
        'in_stock',
        'updated',
    ]

    ordering_field_aliases = {
        'part': 'part__name',
        'supplier': 'supplier__name',
        'manufacturer': 'manufacturer_part__manufacturer__name',
        'pack_quantity': ['pack_quantity_native', 'pack_quantity'],
        'IPN': 'part__IPN',
        'MPN': 'manufacturer_part__MPN',
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


class SupplierPartDetail(
    SupplierPartMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI
):
    """API endpoint for detail view of SupplierPart object.

    - GET: Retrieve detail view
    - PATCH: Update object
    - DELETE: Delete object
    """

    output_options = SupplierPartOutputOptions


class SupplierPriceBreakFilter(FilterSet):
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


class SupplierPriceBreakMixin:
    """Mixin class for SupplierPriceBreak API endpoints."""

    queryset = SupplierPriceBreak.objects.all()
    serializer_class = SupplierPriceBreakSerializer


class SupplierPriceBreakOutputOptions(OutputConfiguration):
    """Available output options for the SupplierPriceBreak endpoints."""

    OPTIONS = [
        InvenTreeOutputOption(
            description='Include detailed information about the linked Part in the response',
            flag='part_detail',
            default=False,
        ),
        InvenTreeOutputOption(
            description='Include detailed information about the Supplier in the response',
            flag='supplier_detail',
            default=False,
        ),
    ]


class SupplierPriceBreakList(
    DataExportViewMixin,
    SupplierPriceBreakMixin,
    SerializerContextMixin,
    OutputOptionsMixin,
    ListCreateAPI,
):
    """API endpoint for list view of SupplierPriceBreak object.

    - GET: Retrieve list of SupplierPriceBreak objects
    - POST: Create a new SupplierPriceBreak object
    """

    output_options = SupplierPriceBreakOutputOptions

    filterset_class = SupplierPriceBreakFilter
    filter_backends = SEARCH_ORDER_FILTER_ALIAS
    ordering_fields = ['quantity', 'supplier', 'SKU', 'price']

    search_fields = ['part__SKU', 'part__supplier__name']

    ordering_field_aliases = {'supplier': 'part__supplier__name', 'SKU': 'part__SKU'}

    ordering = 'quantity'


class SupplierPriceBreakDetail(SupplierPriceBreakMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for SupplierPriceBreak object."""


manufacturer_part_api_urls = [
    path(
        '<int:pk>/',
        include([
            meta_path(ManufacturerPart),
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
    path(
        '<int:pk>/',
        include([
            meta_path(SupplierPart),
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
            path(
                '<int:pk>/',
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
    path(
        '<int:pk>/',
        include([
            meta_path(Company),
            path('', CompanyDetail.as_view(), name='api-company-detail'),
        ]),
    ),
    path(
        'contact/',
        include([
            path(
                '<int:pk>/',
                include([
                    meta_path(Contact),
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
