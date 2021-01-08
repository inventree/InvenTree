# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, filters

import InvenTree.helpers

from stock.models import StockItem

from .models import StockItemLabel
from .serializers import StockItemLabelSerializer


class StockItemLabelList(generics.ListAPIView):
    """
    API endpoint for viewing list of StockItemLabel objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - item: Filter by single stock item
    - items[]: Filter by list of stock items

    """

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer

    def get_items(self):
        """
        Return a list of requested stock items
        """

        items = []

        params = self.request.query_params

        if 'items' in params:
            items = params.getlist('items', [])
        elif 'item' in params:
            items = [params.get('item', None)]

        if type(items) not in [list, tuple]:
            items = [items]

        valid_ids = []

        for item in items:
            try:
                valid_ids.append(int(item))
            except (ValueError):
                pass

        # List of StockItems which match provided values
        valid_items = StockItem.objects.filter(pk__in=valid_ids)

        return valid_items

    def filter_queryset(self, queryset):
        """
        Filter the StockItem label queryset.
        """
        
        queryset = super().filter_queryset(queryset)

        # List of StockItem objects to match against
        items = self.get_items()

        # We wish to filter by stock items
        if len(items) > 0:
            """
            At this point, we are basically forced to be inefficient,
            as we need to compare the 'filters' string of each label,
            and see if it matches against each of the requested items.

            TODO: In the future, if this becomes excessively slow, it
                  will need to be readdressed.
            """

            # Keep track of which labels match every specified stockitem
            valid_label_ids = set()
            
            for label in queryset.all():

                matches = True

                # Filter string defined for the StockItem label
                filters = InvenTree.helpers.validateFilterString(label.filters)

                for item in items:

                    item_query = StockItem.objects.filter(pk=item.pk)

                    if not item_query.filter(**filters).exists():
                        matches = False

                # Matched all items
                if matches:
                    valid_label_ids.add(label.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[id for id in valid_label_ids])

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter
    ]

    filter_fields = [
        'enabled',
    ]

    search_fields = [
        'name',
        'description',
    ]


label_api_urls = [

    # Stock item labels
    url(r'stock/', include([
        url(r'^.*$', StockItemLabelList.as_view(), name='api-stock-label-list'),
    ])),
]
