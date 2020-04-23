# -*- coding: utf-8 -*-

"""
Provides extra global data to all templates.
"""

from InvenTree.status_codes import SalesOrderStatus, PurchaseOrderStatus
from InvenTree.status_codes import BuildStatus, StockStatus


def status_codes(request):

    return {
        # Expose the StatusCode classes to the templates
        'SalesOrderStatus': SalesOrderStatus,
        'PurchaseOrderStatus': PurchaseOrderStatus,
        'BuildStatus': BuildStatus,
        'StockStatus': StockStatus,
    }
