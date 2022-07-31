"""Custom query filters for the Part model

The code here makes heavy use of subquery annotations!

Useful References:

- https://hansonkd.medium.com/the-dramatic-benefits-of-django-subqueries-and-annotations-4195e0dafb16
- https://pypi.org/project/django-sql-utils/
- https://docs.djangoproject.com/en/4.0/ref/models/expressions/
- https://stackoverflow.com/questions/42543978/django-1-11-annotating-a-subquery-aggregate

Relevant PRs:

- https://github.com/inventree/InvenTree/pull/2797/
- https://github.com/inventree/InvenTree/pull/2827

"""

from decimal import Decimal

from django.db import models
from django.db.models import F, FloatField, Func, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from sql_util.utils import SubquerySum

import part.models
import stock.models
from InvenTree.status_codes import (BuildStatus, PurchaseOrderStatus,
                                    SalesOrderStatus)


def annotate_on_order_quantity(reference: str = ''):
    """Annotate the 'on order' quantity for each part in a queryset"""

    # Filter only 'active' purhase orders
    order_filter = Q(order__status__in=PurchaseOrderStatus.OPEN)

    return Coalesce(
        SubquerySum(f'{reference}supplier_parts__purchase_order_line_items__quantity', filter=order_filter),
        Decimal(0),
        output_field=models.DecimalField()
    ) - Coalesce(
        SubquerySum(f'{reference}supplier_parts__purchase_order_line_items__received', filter=order_filter),
        Decimal(0),
        output_field=models.DecimalField(),
    )


def annotate_total_stock(reference: str = ''):
    """Annotate 'total stock' quantity against a queryset:

    - This function calculates the 'total stock' for a given part
    - Finds all stock items associated with each part (using the provided filter)
    - Aggregates the 'quantity' of each relevent stock item

    Args:
        reference: The relationship reference of the part from the current model e.g. 'part'
        stock_filter: Q object which defines how to filter the stock items
    """

    # Stock filter only returns 'in stock' items
    stock_filter = stock.models.StockItem.IN_STOCK_FILTER

    return Coalesce(
        SubquerySum(
            f'{reference}stock_items__quantity',
            filter=stock_filter,
        ),
        Decimal(0),
        output_field=models.DecimalField(),
    )


def annotate_build_order_allocations(reference: str = ''):
    """Annotate the total quantity of each part allocated to build orders:

    - This function calculates the total part quantity allocated to open build orders
    - Finds all build order allocations for each part (using the provided filter)
    - Aggregates the 'allocated quantity' for each relevent build order allocation item

    Args:
        reference: The relationship reference of the part from the current model
        build_filter: Q object which defines how to filter the allocation items
    """

    # Build filter only returns 'active' build orders
    build_filter = Q(build__status__in=BuildStatus.ACTIVE_CODES)

    return Coalesce(
        SubquerySum(
            f'{reference}stock_items__allocations__quantity',
            filter=build_filter,
        ),
        Decimal(0),
        output_field=models.DecimalField(),
    )


def annotate_sales_order_allocations(reference: str = ''):
    """Annotate the total quantity of each part allocated to sales orders:

    - This function calculates the total part quantity allocated to open sales orders"
    - Finds all sales order allocations for each part (using the provided filter)
    - Aggregates the 'allocated quantity' for each relevent sales order allocation item

    Args:
        reference: The relationship reference of the part from the current model
        order_filter: Q object which defines how to filter the allocation items
    """

    # Order filter only returns incomplete shipments for open orders
    order_filter = Q(
        line__order__status__in=SalesOrderStatus.OPEN,
        shipment__shipment_date=None,
    )

    return Coalesce(
        SubquerySum(
            f'{reference}stock_items__sales_order_allocations__quantity',
            filter=order_filter,
        ),
        Decimal(0),
        output_field=models.DecimalField(),
    )


def variant_stock_query(reference: str = '', filter: Q = stock.models.StockItem.IN_STOCK_FILTER):
    """Create a queryset to retrieve all stock items for variant parts under the specified part

    - Useful for annotating a queryset with aggregated information about variant parts

    Args:
        reference: The relationship reference of the part from the current model
        filter: Q object which defines how to filter the returned StockItem instances
    """

    return stock.models.StockItem.objects.filter(
        part__tree_id=OuterRef(f'{reference}tree_id'),
        part__lft__gt=OuterRef(f'{reference}lft'),
        part__rght__lt=OuterRef(f'{reference}rght'),
    ).filter(filter)


def annotate_variant_quantity(subquery: Q, reference: str = 'quantity'):
    """Create a subquery annotation for all variant part stock items on the given parent query

    Args:
        subquery: A 'variant_stock_query' Q object
        reference: The relationship reference of the variant stock items from the current queryset
    """

    return Coalesce(
        Subquery(
            subquery.annotate(
                total=Func(F(reference), function='SUM', output_field=FloatField())
            ).values('total')
        ),
        0,
        output_field=FloatField(),
    )


def annotate_category_parts():
    """Construct a queryset annotation which returns the number of parts in a particular category.

    - Includes parts in subcategories also
    - Requires subquery to perform annotation
    """

    # Construct a subquery to provide all parts in this category and any subcategories:
    subquery = part.models.Part.objects.filter(
        category__tree_id=OuterRef('tree_id'),
        category__lft__gte=OuterRef('lft'),
        category__rght__lte=OuterRef('rght'),
    )

    return Coalesce(
        Subquery(
            subquery.annotate(
                total=Func(F('pk'), function='COUNT', output_field=FloatField())
            ).values('total'),
        ),
        0,
        output_field=FloatField()
    )
