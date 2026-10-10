"""Sample plugin which demonstrates custom stock allocation functionality."""

from plugin import InvenTreePlugin
from plugin.mixins import AllocateMixin

# Batch code which marks a stock item as excluded from auto-allocation
REJECT_BATCH_CODE = 'REJECT'


class SampleAllocatePlugin(AllocateMixin, InvenTreePlugin):
    """A sample plugin for demonstrating custom auto-allocation behavior.

    Any stock item with a batch code of 'REJECT' is excluded from
    auto-allocation, for both build orders and sales orders.
    """

    NAME = 'SampleAllocate'
    SLUG = 'sampleallocate'
    TITLE = 'Sample Allocate Plugin'
    DESCRIPTION = (
        'A sample plugin for demonstrating custom stock allocation functionality'
    )
    VERSION = '0.1.0'

    def filter_build_allocation(self, build_line, stock_items, **kwargs):
        """Exclude any stock item with a 'REJECT' batch code."""
        return [item for item in stock_items if item.batch != REJECT_BATCH_CODE]

    def filter_sales_order_allocation(self, order_line, stock_items, **kwargs):
        """Exclude any stock item with a 'REJECT' batch code."""
        return [item for item in stock_items if item.batch != REJECT_BATCH_CODE]
