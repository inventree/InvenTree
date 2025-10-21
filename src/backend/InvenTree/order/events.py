"""Event definitions and triggers for the order app."""

from generic.events import BaseEventEnum


class PurchaseOrderEvents(BaseEventEnum):
    """Event enumeration for the PurchaseOrder models."""

    PLACED = 'purchaseorder.placed'
    COMPLETED = 'purchaseorder.completed'
    CANCELLED = 'purchaseorder.cancelled'
    HOLD = 'purchaseorder.hold'

    OVERDUE = 'order.overdue_purchase_order'

    ITEM_RECEIVED = 'purchaseorderitem.received'


class SalesOrderEvents(BaseEventEnum):
    """Event enumeration for the SalesOrder models."""

    ISSUED = 'salesorder.issued'
    HOLD = 'salesorder.onhold'
    COMPLETED = 'salesorder.completed'
    CANCELLED = 'salesorder.cancelled'

    OVERDUE = 'order.overdue_sales_order'

    SHIPMENT_COMPLETE = 'salesordershipment.completed'


class ReturnOrderEvents(BaseEventEnum):
    """Event enumeration for the Return models."""

    ISSUED = 'returnorder.issued'
    RECEIVED = 'returnorder.received'
    COMPLETED = 'returnorder.completed'
    CANCELLED = 'returnorder.cancelled'
    HOLD = 'returnorder.hold'
