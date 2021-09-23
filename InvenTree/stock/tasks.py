# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.core.exceptions import AppRegistryNotReady


logger = logging.getLogger('inventree')


def delete_old_stock_items():
    """
    This function removes StockItem objects which have been marked for deletion.

    Bulk "delete" operations for database entries with foreign-key relationships
    can be pretty expensive, and thus can "block" the UI for a period of time.

    Thus, instead of immediately deleting multiple StockItems, some UI actions
    simply mark each StockItem as "scheduled for deletion".

    The background worker then manually deletes these at a later stage
    """

    try:
        from stock.models import StockItem
    except AppRegistryNotReady:
        logger.info("Could not delete scheduled StockItems - AppRegistryNotReady")
        return

    items = StockItem.objects.filter(scheduled_for_deletion=True)

    if items.count() > 0:
        logger.info(f"Removing {items.count()} StockItem objects scheduled for deletion")
        items.delete()
