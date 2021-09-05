# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.filters import OrderingFilter


class InvenTreeOrderingFilter(OrderingFilter):
    """
    Custom OrderingFilter class which allows aliased filtering of related fields.

    To use, simply specify this filter in the "filter_backends" section.

    filter_backends = [
        InvenTreeOrderingFilter,
    ]

    Then, specify a ordering_field_aliases attribute:

    ordering_field_alises = {
        'name': 'part__part__name',
        'SKU': 'part__SKU',
    }
    """

    def get_ordering(self, request, queryset, view):

        ordering = super().get_ordering(request, queryset, view)

        aliases = getattr(view, 'ordering_field_aliases', None)

        # Attempt to map ordering fields based on provided aliases
        if ordering is not None and aliases is not None:
            """
            Ordering fields should be mapped to separate fields
            """

            for idx, field in enumerate(ordering):

                reverse = False

                if field.startswith('-'):
                    field = field[1:]
                    reverse = True

                if field in aliases:
                    ordering[idx] = aliases[field]

                    if reverse:
                        ordering[idx] = '-' + ordering[idx]

        return ordering
