"""Provide templates for the various model status codes."""

from django import template
from django.utils.safestring import mark_safe

from InvenTree.status_codes import (BuildStatus, PurchaseOrderStatus,
                                    ReturnOrderStatus, SalesOrderStatus,
                                    StockStatus)

register = template.Library()


@register.simple_tag
def status_label(typ: str, key: int, *args, **kwargs):
    """Render a status label."""
    opts = {
        'build': BuildStatus,
        'purchase_order': PurchaseOrderStatus,
        'return_order': ReturnOrderStatus,
        'sales_order': SalesOrderStatus,
        'stock': StockStatus,
    }
    state = opts.get(typ, None)
    if state:
        return mark_safe(state.render(key, large=kwargs.get('large', False)))
    raise ValueError(f"Unknown status type '{typ}'")
