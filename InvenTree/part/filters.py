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
from django.db.models import ExpressionWrapper, F, Q
from django.db.models.functions import Coalesce

from sql_util.utils import SubquerySum

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


def annotate_stock_allocations(queryset, reference: str = '', alias: bool = True, prefix: str = ''):
    """Annotate stock allocation data to each part in a queryset:

    This function can be used to annotate the 'available stock' count
    to each part in a queryset, without incurring the "1 + N" query penalty.

    It uses a number of subquery annotations to achieve this (refer to the functions above).

    Each required subquery annotation is applied in sequence to the queryset,
    to perform the equivalent of the following mathematical operation:

    unallocated_stock = in_stock - build_order_allocation_quantity - sales_order_allocation_quantity

    Args:
        queryset: The QuerySet instance to annotate
        reference: The relationship reference of the 'part' object from the current model
        alias: If True, intermediate steps are performed as an alias operation (more efficient)
        prefix: Optional prefix to prepend to output annotated fields
    """

    print(f"annotate_stock_allocations: reference='{reference}', prefix='{prefix}'")

    # Construct a set of intermediate annotations to perform
    annotations = {
        f'{prefix}in_stock': annotate_total_stock(reference),
        f'{prefix}build_order_allocation_quantity': annotate_build_order_allocations(reference),
        f'{prefix}sales_order_allocation_quantity': annotate_sales_order_allocations(reference),
    }

    # Alias or annotate the intermediate annotations to the queryset
    # if alias:
    #     queryset = queryset.alias(**annotations)
    # else:
    #     queryset = queryset.annotate(**annotations)

    queryset = queryset.annotate(
        in_stock=annotate_total_stock(reference),
        build_order_allocation_quantity=annotate_build_order_allocations(reference),
        sales_order_allocation_quantity=annotate_sales_order_allocations(reference),
    )

    # Next, calculate the 'unallocated_stock' annotation based on previous calculations
    # annotations = {
    #     f'{prefix}unallocated_stock': ExpressionWrapper(
    #         F(f'{prefix}in_stock') - F(f'{prefix}build_order_allocation_quantity') - F(f'{prefix}sales_order_allocation_quantity'),
    #         output_field=models.DecimalField(),
    #     )
    # }

    print("Annotations:")
    print(annotations)

    queryset = queryset.annotate(
        unallocated_quantity=ExpressionWrapper(
            F('in_stock') - F('build_order_allocation-quantity') - F('sales_order_allocation_quantity'),
            output_field=models.DecimalField()
        )
    )
    # queryset = queryset.annotate(**annotations)

    print(queryset)

    return queryset
