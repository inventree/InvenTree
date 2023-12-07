"""Custom query filters for the Part models

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
from django.db.models import (Case, DecimalField, Exists, ExpressionWrapper, F,
                              FloatField, Func, IntegerField, OuterRef, Q,
                              Subquery, Value, When)
from django.db.models.functions import Coalesce

from sql_util.utils import SubquerySum

import part.models
import stock.models
from InvenTree.status_codes import (BuildStatusGroups,
                                    PurchaseOrderStatusGroups,
                                    SalesOrderStatusGroups)


def annotate_on_order_quantity(reference: str = ''):
    """Annotate the 'on order' quantity for each part in a queryset.

    Sum the 'remaining quantity' of each line item for any open purchase orders for each part:

    - Purchase order must be 'active' or 'pending'
    - Received quantity must be less than line item quantity

    Note that in addition to the 'quantity' on order, we must also take into account 'pack_quantity'.
    """
    # Filter only 'active' purhase orders
    # Filter only line with outstanding quantity
    order_filter = Q(
        order__status__in=PurchaseOrderStatusGroups.OPEN,
        quantity__gt=F('received'),
    )

    return Coalesce(
        SubquerySum(
            ExpressionWrapper(
                F(f'{reference}supplier_parts__purchase_order_line_items__quantity') * F(f'{reference}supplier_parts__pack_quantity_native'),
                output_field=DecimalField(),
            ),
            filter=order_filter
        ),
        Decimal(0),
        output_field=DecimalField()
    ) - Coalesce(
        SubquerySum(
            ExpressionWrapper(
                F(f'{reference}supplier_parts__purchase_order_line_items__received') * F(f'{reference}supplier_parts__pack_quantity_native'),
                output_field=DecimalField(),
            ),
            filter=order_filter
        ),
        Decimal(0),
        output_field=DecimalField(),
    )


def annotate_total_stock(reference: str = ''):
    """Annotate 'total stock' quantity against a queryset:

    - This function calculates the 'total stock' for a given part
    - Finds all stock items associated with each part (using the provided filter)
    - Aggregates the 'quantity' of each relevant stock item

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


def annotate_build_order_requirements(reference: str = ''):
    """Annotate the total quantity of each part required for build orders.

    - Only interested in 'active' build orders
    - We are looking for any BuildLine items which required this part (bom_item.sub_part)
    - We are interested in the 'quantity' of each BuildLine item

    """
    # Active build orders only
    build_filter = Q(build__status__in=BuildStatusGroups.ACTIVE_CODES)

    return Coalesce(
        SubquerySum(
            f'{reference}used_in__build_lines__quantity',
            filter=build_filter,
        ),
        Decimal(0),
        output_field=models.DecimalField(),
    )


def annotate_build_order_allocations(reference: str = ''):
    """Annotate the total quantity of each part allocated to build orders:

    - This function calculates the total part quantity allocated to open build orders
    - Finds all build order allocations for each part (using the provided filter)
    - Aggregates the 'allocated quantity' for each relevant build order allocation item

    Args:
        reference: The relationship reference of the part from the current model
        build_filter: Q object which defines how to filter the allocation items
    """
    # Build filter only returns 'active' build orders
    build_filter = Q(build_line__build__status__in=BuildStatusGroups.ACTIVE_CODES)

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
    - Aggregates the 'allocated quantity' for each relevant sales order allocation item

    Args:
        reference: The relationship reference of the part from the current model
        order_filter: Q object which defines how to filter the allocation items
    """
    # Order filter only returns incomplete shipments for open orders
    order_filter = Q(
        line__order__status__in=SalesOrderStatusGroups.OPEN,
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
    subquery = part.models.Part.objects.exclude(category=None).filter(
        category__tree_id=OuterRef('tree_id'),
        category__lft__gte=OuterRef('lft'),
        category__rght__lte=OuterRef('rght'),
        category__level__gte=OuterRef('level'),
    )

    return Coalesce(
        Subquery(
            subquery.annotate(
                total=Func(F('pk'), function='COUNT', output_field=IntegerField())
            ).values('total'),
        ),
        0,
        output_field=IntegerField()
    )


def filter_by_parameter(queryset, template_id: int, value: str, func: str = ''):
    """Filter the given queryset by a given template parameter

    Parts which do not have a value for the given parameter are excluded.

    Arguments:
        queryset - A queryset of Part objects
        template_id - The ID of the template parameter to filter by
        value - The value of the parameter to filter by
        func - The function to use for the filter (e.g. __gt, __lt, __contains)

    Returns:
        A queryset of Part objects filtered by the given parameter
    """
    # TODO
    return queryset


def order_by_parameter(queryset, template_id: int, ascending=True):
    """Order the given queryset by a given template parameter

    Parts which do not have a value for the given parameter are ordered last.

    Arguments:
        queryset - A queryset of Part objects
        template_id - The ID of the template parameter to order by

    Returns:
        A queryset of Part objects ordered by the given parameter
    """
    template_filter = part.models.PartParameter.objects.filter(
        template__id=template_id,
        part_id=OuterRef('id'),
    )

    # Annotate the queryset with the parameter value, and whether it exists
    queryset = queryset.annotate(
        parameter_exists=Exists(template_filter)
    )

    # Annotate the text data value
    queryset = queryset.annotate(
        parameter_value=Case(
            When(
                parameter_exists=True,
                then=Subquery(template_filter.values('data')[:1], output_field=models.CharField()),
            ),
            default=Value('', output_field=models.CharField()),
        ),
        parameter_value_numeric=Case(
            When(
                parameter_exists=True,
                then=Subquery(template_filter.values('data_numeric')[:1], output_field=models.FloatField()),
            ),
            default=Value(0, output_field=models.FloatField()),
        )
    )

    prefix = '' if ascending else '-'

    # Return filtered queryset

    return queryset.order_by(
        '-parameter_exists',
        f'{prefix}parameter_value_numeric',
        f'{prefix}parameter_value',
    )
