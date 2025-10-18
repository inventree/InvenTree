"""APIs for parameters."""

from django.urls import include, path

from django_filters import rest_framework as rest_filters

from generic.parameters.models import (
    PartCategoryParameterTemplate,
    PartParameter,
    PartParameterTemplate,
    PartParameterTemplateFilter,
)
from importer.mixins import DataExportViewMixin
from InvenTree.api import MetadataView
from InvenTree.filters import SEARCH_ORDER_FILTER, SEARCH_ORDER_FILTER_ALIAS
from InvenTree.helpers import str2bool
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI
from part import serializers as part_serializers
from part.models import Part, PartCategory


class CategoryParameterList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartCategoryParameterTemplate objects.

    - GET: Return a list of PartCategoryParameterTemplate objects
    """

    queryset = PartCategoryParameterTemplate.objects.all()
    serializer_class = part_serializers.CategoryParameterTemplateSerializer

    def get_queryset(self):
        """Custom filtering.

        Rules:
        - Allow filtering by "null" parent to retrieve all categories parameter templates
        - Allow filtering by category
        - Allow traversing all parent categories
        """
        queryset = super().get_queryset()

        params = self.request.query_params

        category = params.get('category', None)

        if category is not None:
            try:
                category = PartCategory.objects.get(pk=category)

                fetch_parent = str2bool(params.get('fetch_parent', True))

                if fetch_parent:
                    parents = category.get_ancestors(include_self=True)
                    queryset = queryset.filter(category__in=[cat.pk for cat in parents])
                else:
                    queryset = queryset.filter(category=category)

            except (ValueError, PartCategory.DoesNotExist):
                pass

        return queryset


class CategoryParameterDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for the PartCategoryParameterTemplate model."""

    queryset = PartCategoryParameterTemplate.objects.all()
    serializer_class = part_serializers.CategoryParameterTemplateSerializer


class PartParameterFilter(rest_filters.FilterSet):
    """Custom filters for the PartParameterList API endpoint."""

    class Meta:
        """Metaclass options for the filterset."""

        model = PartParameter
        fields = ['template']

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), method='filter_part'
    )

    def filter_part(self, queryset, name, part):
        """Filter against the provided part.

        If 'include_variants' query parameter is provided, filter against variant parts also
        """
        try:
            include_variants = str2bool(self.request.GET.get('include_variants', False))
        except AttributeError:
            include_variants = False

        if include_variants:
            return queryset.filter(part__in=part.get_descendants(include_self=True))
        else:
            return queryset.filter(part=part)


class PartParameterTemplateMixin:
    """Mixin class for PartParameterTemplate API endpoints."""

    queryset = PartParameterTemplate.objects.all()
    serializer_class = part_serializers.PartParameterTemplateSerializer

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset for the PartParameterTemplateDetail endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = part_serializers.PartParameterTemplateSerializer.annotate_queryset(
            queryset
        )

        return queryset


class PartParameterTemplateDetail(PartParameterTemplateMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for accessing the detail view for a PartParameterTemplate object."""


class PartParameterTemplateList(
    PartParameterTemplateMixin, DataExportViewMixin, ListCreateAPI
):
    """API endpoint for accessing a list of PartParameterTemplate objects.

    - GET: Return list of PartParameterTemplate objects
    - POST: Create a new PartParameterTemplate object
    """

    filterset_class = PartParameterTemplateFilter

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['name', 'description']

    ordering_fields = ['name', 'units', 'checkbox', 'parts']


class PartParameterAPIMixin:
    """Mixin class for PartParameter API endpoints."""

    queryset = PartParameter.objects.all()
    serializer_class = part_serializers.PartParameterSerializer

    def get_queryset(self, *args, **kwargs):
        """Override get_queryset method to prefetch related fields."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = queryset.prefetch_related('part', 'template')
        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this API endpoint.

        If requested, extra detail fields are annotated to the queryset:
        - part_detail
        - template_detail
        """
        try:
            kwargs['part_detail'] = str2bool(self.request.GET.get('part_detail', False))
            kwargs['template_detail'] = str2bool(
                self.request.GET.get('template_detail', True)
            )
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)


class PartParameterList(PartParameterAPIMixin, DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartParameter objects.

    - GET: Return list of PartParameter objects
    - POST: Create a new PartParameter object
    """

    filterset_class = PartParameterFilter

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = ['name', 'data', 'part', 'template']

    ordering_field_aliases = {
        'name': 'template__name',
        'units': 'template__units',
        'data': ['data_numeric', 'data'],
        'part': 'part__name',
    }

    search_fields = [
        'data',
        'template__name',
        'template__description',
        'template__units',
    ]


class PartParameterDetail(PartParameterAPIMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single PartParameter object."""


partcategory_parameter_urls = include([
    path(
        '<int:pk>/',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': PartCategoryParameterTemplate},
                name='api-part-category-parameter-metadata',
            ),
            path(
                '',
                CategoryParameterDetail.as_view(),
                name='api-part-category-parameter-detail',
            ),
        ]),
    ),
    path('', CategoryParameterList.as_view(), name='api-part-category-parameter-list'),
])
part_parameters_urls = include([
    path(
        'template/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartParameterTemplate},
                        name='api-part-parameter-template-metadata',
                    ),
                    path(
                        '',
                        PartParameterTemplateDetail.as_view(),
                        name='api-part-parameter-template-detail',
                    ),
                ]),
            ),
            path(
                '',
                PartParameterTemplateList.as_view(),
                name='api-part-parameter-template-list',
            ),
        ]),
    ),
    path(
        '<int:pk>/',
        include([
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': PartParameter},
                name='api-part-parameter-metadata',
            ),
            path('', PartParameterDetail.as_view(), name='api-part-parameter-detail'),
        ]),
    ),
    path('', PartParameterList.as_view(), name='api-part-parameter-list'),
])
