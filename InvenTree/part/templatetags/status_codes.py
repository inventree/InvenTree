"""Provide templates for the various model status codes."""

from django import template
from django.utils.safestring import mark_safe

from InvenTree.status_codes import (BuildStatus, PurchaseOrderStatus,
                                    SalesOrderStatus, StockStatus)

register = template.Library()


@register.simple_tag
def purchase_order_status_label(key, *args, **kwargs):
    """Render a PurchaseOrder status label."""
    return mark_safe(PurchaseOrderStatus.render(key, large=kwargs.get('large', False)))


@register.simple_tag
def sales_order_status_label(key, *args, **kwargs):
    """Render a SalesOrder status label."""
    return mark_safe(SalesOrderStatus.render(key, large=kwargs.get('large', False)))


@register.simple_tag
def stock_status_label(key, *args, **kwargs):
    """Render a StockItem status label."""
    return mark_safe(StockStatus.render(key, large=kwargs.get('large', False)))


@register.simple_tag
def stock_status_text(key, *args, **kwargs):
    """Render the text value of a StockItem status value"""
    return mark_safe(StockStatus.text(key))


@register.simple_tag
def build_status_label(key, *args, **kwargs):
    """Render a Build status label."""
    return mark_safe(BuildStatus.render(key, large=kwargs.get('large', False)))
