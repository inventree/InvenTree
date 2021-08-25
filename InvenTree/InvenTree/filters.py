# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.filters import OrderingFilter


class InvenTreeOrderingFilter(OrderingFilter):
    """
    Custom OrderingFilter class which allows aliased filtering of related fields.

    To use, simply specify this filter in the "filter_backends" section.

    Then, you can specify aliasing for ordering fields (or use ordering_fields as normal), e.g.

    filter_backends = [
        InvenTreeOrderingFilter,
    ]

    ordering_fields = [
        'name',
        'quantity',
        ('part__SKU', 'SKU')
    ]

    Here, ordering by "SKU" will actually order by the "SKU" field on the related part field

    """

    def get_ordering(self, request, queryset, view):

        ordering = super().get_ordering(request, queryset, view)

        print("ORDERING:", ordering)
        return ordering