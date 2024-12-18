"""Custom query filters for the Company app."""

from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Q
from django.db.models.functions import Coalesce

from sql_util.utils import SubquerySum

from order.status_codes import PurchaseOrderStatusGroups


def annotate_on_order_quantity():
    """Annotate the 'on_order' quantity for each SupplierPart in a queryset.

    - This is the total quantity of parts on order from all open purchase orders
    - Takes into account the 'received' quantity for each order line
    """
    # Filter only 'active' purhase orders
    # Filter only line with outstanding quantity
    order_filter = Q(
        order__status__in=PurchaseOrderStatusGroups.OPEN, quantity__gt=F('received')
    )

    return Coalesce(
        SubquerySum(
            ExpressionWrapper(
                F('purchase_order_line_items__quantity')
                - F('purchase_order_line_items__received'),
                output_field=DecimalField(),
            ),
            filter=order_filter,
        ),
        Decimal(0),
        output_field=DecimalField(),
    )
