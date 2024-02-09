"""Custom query filters for the Stock models."""

from django.db.models import F, Func, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from sql_util.utils import SubqueryCount

import stock.models


def annotate_location_items(filter: Q = None):
    """Construct a queryset annotation which returns the number of stock items in a particular location.

    - Includes items in subcategories also
    - Requires subquery to perform annotation
    """
    # Construct a subquery to provide all items in this location and any sublocations
    subquery = stock.models.StockItem.objects.exclude(location=None).filter(
        location__tree_id=OuterRef('tree_id'),
        location__lft__gte=OuterRef('lft'),
        location__rght__lte=OuterRef('rght'),
        location__level__gte=OuterRef('level'),
    )

    # Optionally apply extra filter to returned results
    if filter is not None:
        subquery = subquery.filter(filter)

    return Coalesce(
        Subquery(
            subquery.annotate(
                total=Func(F('pk'), function='COUNT', output_field=IntegerField())
            )
            .values('total')
            .order_by()
        ),
        0,
        output_field=IntegerField(),
    )


def annotate_child_items():
    """Construct a queryset annotation which returns the number of children below a certain StockItem node in a StockItem tree."""
    child_stock_query = stock.models.StockItem.objects.filter(
        tree_id=OuterRef('tree_id'),
        lft__gt=OuterRef('lft'),
        rght__lt=OuterRef('rght'),
        level__gte=OuterRef('level'),
    )

    return Coalesce(
        Subquery(
            child_stock_query.annotate(
                count=Func(F('pk'), function='COUNT', output_field=IntegerField())
            )
            .values('count')
            .order_by()
        ),
        0,
        output_field=IntegerField(),
    )
