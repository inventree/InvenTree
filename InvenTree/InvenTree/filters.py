"""General filters for InvenTree."""

from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.timezone import make_aware

from django_filters import rest_framework as rest_filters
from rest_framework import filters

import InvenTree.helpers


class InvenTreeDateFilter(rest_filters.DateFilter):
    """Custom DateFilter class which handles timezones correctly."""

    def filter(self, qs, value):
        """Override the filter method to handle timezones correctly."""

        if settings.USE_TZ:
            if value is not None:
                tz = timezone.get_current_timezone()
                value = datetime(value.year, value.month, value.day)
                value = make_aware(value, tz, True)

        return super().filter(qs, value)


class InvenTreeSearchFilter(filters.SearchFilter):
    """Custom search filter which allows adjusting of search terms dynamically"""

    def get_search_fields(self, view, request):
        """Return a set of search fields for the request, adjusted based on request params.

        The following query params are available to 'augment' the search (in decreasing order of priority)
        - search_regex: If True, search is performed on 'regex' comparison
        """
        regex = InvenTree.helpers.str2bool(request.query_params.get('search_regex', False))

        search_fields = super().get_search_fields(view, request)

        fields = []

        if search_fields:
            for field in search_fields:
                if regex:
                    field = '$' + field

                fields.append(field)

        return fields

    def get_search_terms(self, request):
        """Return the search terms for this search request.

        Depending on the request parameters, we may "augment" these somewhat
        """
        whole = InvenTree.helpers.str2bool(request.query_params.get('search_whole', False))

        terms = []

        search_terms = super().get_search_terms(request)

        if search_terms:
            for term in search_terms:
                term = term.strip()

                if not term:
                    # Ignore blank inputs
                    continue

                if whole:
                    # Wrap the search term to enable word-boundary matching
                    term = r"\y" + term + r"\y"

                terms.append(term)

        return terms


class InvenTreeOrderingFilter(filters.OrderingFilter):
    """Custom OrderingFilter class which provides additional filtering options.

    To use, simply specify this filter in the "filter_backends" section.

    filter_backends = [
        InvenTreeOrderingFilter,
    ]

    Filter aliases can be defined in the view class:

    ordering_field_alises = {
        'name': 'part__part__name',
        'SKU': 'part__SKU',
    }

    We can also order on annotated fields:

    annotated_ordering_fields = [
        'my_custom_field',
        'another_custom_field',
    ]

    """

    def get_ordering(self, request, queryset, view):
        """Override ordering for supporting aliases."""
        ordering = super().get_ordering(request, queryset, view) or None

        if ordering is None:
            ordering = []

        aliases = getattr(view, 'ordering_field_aliases', None)

        # Attempt to map ordering fields based on provided aliases
        if aliases:
            """Ordering fields should be mapped to separate fields."""

            ordering_initial = ordering
            ordering = []

            for field in ordering_initial:

                reverse = field.startswith('-')

                if reverse:
                    field = field[1:]

                # Are aliases defined for this field?
                if field in aliases:
                    alias = aliases[field]
                else:
                    alias = field

                """
                Potentially, a single field could be "aliased" to multiple field,

                (For example to enforce a particular ordering sequence)

                e.g. to filter first by the integer value...

                ordering_field_aliases = {
                    "reference": ["integer_ref", "reference"]
                }

                """

                if type(alias) is str:
                    alias = [alias]
                elif type(alias) in [list, tuple]:
                    pass
                else:
                    # Unsupported alias type
                    continue

                for a in alias:
                    if reverse:
                        a = '-' + a

                    ordering.append(a)

        return ordering

    def filter_queryset(self, request, queryset, view):
        """Override filter_queryset method to support annotated ordering fields."""

        queryset = super().filter_queryset(request, queryset, view)

        annotated_fields = getattr(view, 'annotated_ordering_fields', None)
        ordering = request.query_params.get('ordering', None)

        if ordering and annotated_fields:
            if ordering.replace('-', '') in annotated_fields:
                # Ordering on an annotated field
                queryset = queryset.order_by(ordering)

        return queryset


SEARCH_ORDER_FILTER = [
    rest_filters.DjangoFilterBackend,
    InvenTreeSearchFilter,
    filters.OrderingFilter,
]

SEARCH_ORDER_FILTER_ALIAS = [
    rest_filters.DjangoFilterBackend,
    InvenTreeSearchFilter,
    InvenTreeOrderingFilter,
]

ORDER_FILTER = [
    rest_filters.DjangoFilterBackend,
    filters.OrderingFilter,
]
