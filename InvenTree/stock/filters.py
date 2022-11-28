"""Custom query filters for the Stock models"""

from django.db.models import F, Func, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

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
            ).values('total')
        ),
        0,
        output_field=IntegerField()
    )
