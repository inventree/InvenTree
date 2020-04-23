"""
Provide templates for the various model status codes.
"""

from django import template
from django.utils.safestring import mark_safe
from InvenTree.status_codes import PurchaseOrderStatus, SalesOrderStatus
from InvenTree.status_codes import StockStatus, BuildStatus

register = template.Library()


@register.simple_tag
def purchase_order_status_label(key, *args, **kwargs):
    """ Render a PurchaseOrder status label """
    return mark_safe(PurchaseOrderStatus.render(key))


@register.simple_tag
def sales_order_status_label(key, *args, **kwargs):
    """ Render a SalesOrder status label """
    return mark_safe(SalesOrderStatus.render(key))


@register.simple_tag
def stock_status_label(key, *args, **kwargs):
    """ Render a StockItem status label """
    return mark_safe(StockStatus.render(key))


@register.simple_tag
def build_status_label(key, *args, **kwargs):
    """ Render a Build status label """
    return mark_safe(BuildStatus.render(key))
