"""Order status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class PurchaseOrderStatus(StatusCode):
    """Defines a set of status codes for a PurchaseOrder.

    Attributes:
        PENDING: Order is pending (not yet placed)
        PLACED: Order has been placed with supplier
        ON_HOLD: Order is on hold
        COMPLETE: Order has been completed
        CANCELLED: Order was cancelled
        LOST: Order was lost
        RETURNED: Order was returned
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    PLACED = 20, _('Placed'), ColorEnum.primary
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning
    COMPLETE = 30, _('Complete'), ColorEnum.success
    CANCELLED = 40, _('Cancelled'), ColorEnum.danger
    LOST = 50, _('Lost'), ColorEnum.warning
    RETURNED = 60, _('Returned'), ColorEnum.warning


class PurchaseOrderStatusGroups:
    """Groups for PurchaseOrderStatus codes."""

    # Open orders
    OPEN = [
        PurchaseOrderStatus.PENDING.value,
        PurchaseOrderStatus.ON_HOLD.value,
        PurchaseOrderStatus.PLACED.value,
    ]

    # Failed orders
    FAILED = [
        PurchaseOrderStatus.CANCELLED.value,
        PurchaseOrderStatus.LOST.value,
        PurchaseOrderStatus.RETURNED.value,
    ]

    COMPLETE = [PurchaseOrderStatus.COMPLETE.value]


class SalesOrderStatus(StatusCode):
    """Defines a set of status codes for a SalesOrder.

    Attributes:
        PENDING: Order is pending
        IN_PROGRESS: Order has been issued, and is in progress
        SHIPPED: Order has been shipped to customer
        ON_HOLD: Order is on hold
        COMPLETE: Order is complete
        CANCELLED: Order has been cancelled
        LOST: Order was lost
        RETURNED: Order was returned
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    IN_PROGRESS = 15, _('In Progress'), ColorEnum.primary
    SHIPPED = 20, _('Shipped'), ColorEnum.primary
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning
    COMPLETE = 30, _('Complete'), ColorEnum.success
    CANCELLED = 40, _('Cancelled'), ColorEnum.danger
    LOST = 50, _('Lost'), ColorEnum.warning
    RETURNED = 60, _('Returned'), ColorEnum.warning


class SalesOrderStatusGroups:
    """Groups for SalesOrderStatus codes."""

    # Open orders
    OPEN = [
        SalesOrderStatus.PENDING.value,
        SalesOrderStatus.ON_HOLD.value,
        SalesOrderStatus.IN_PROGRESS.value,
        SalesOrderStatus.SHIPPED.value,
    ]

    # Completed orders
    COMPLETE = [SalesOrderStatus.COMPLETE.value]


class ReturnOrderStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrder.

    Attributes:
        PENDING: Order is pending, waiting for receipt of items
        IN_PROGRESS: Items have been received, and are being inspected
        ON_HOLD: Order is on hold
        COMPLETE: Order is complete
        CANCELLED: Order has been cancelled
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    IN_PROGRESS = 20, _('In Progress'), ColorEnum.primary
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning
    COMPLETE = 30, _('Complete'), ColorEnum.success
    CANCELLED = 40, _('Cancelled'), ColorEnum.danger


class ReturnOrderStatusGroups:
    """Groups for ReturnOrderStatus codes."""

    OPEN = [
        ReturnOrderStatus.PENDING.value,
        ReturnOrderStatus.ON_HOLD.value,
        ReturnOrderStatus.IN_PROGRESS.value,
    ]

    COMPLETE = [ReturnOrderStatus.COMPLETE.value]


class ReturnOrderLineStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrderLineItem.

    Attributes:
        PENDING: No outcome has been decided yet (default value for a new line item)
        RETURN: The item is to be returned to the customer, with no further action
        REPAIR: The item is to be repaired, and returned to the customer
        REPLACE: The item is to be replaced with a new item
        REFUND: The item cannot be repaired, and a refund is to be issued
        REJECT: The return is rejected
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    RETURN = 20, _('Return'), ColorEnum.success
    REPAIR = 30, _('Repair'), ColorEnum.primary
    REPLACE = 40, _('Replace'), ColorEnum.warning
    REFUND = 50, _('Refund'), ColorEnum.info
    REJECT = 60, _('Reject'), ColorEnum.danger


class TransferOrderStatus(StatusCode):
    """Defines a set of status codes for a TransferOrder.

    Attributes:
        PENDING: Order is pending (not yet issued)
        ISSUED: Order has been issued
        ON_HOLD: Order is on hold
        COMPLETE: Order has been completed
        CANCELLED: Order was cancelled
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    ISSUED = 20, _('Issued'), ColorEnum.primary
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning
    COMPLETE = 30, _('Complete'), ColorEnum.success
    CANCELLED = 40, _('Cancelled'), ColorEnum.danger


class TransferOrderStatusGroups:
    """Groups for TransferOrderStatus codes."""

    # Open orders
    OPEN = [
        TransferOrderStatus.PENDING.value,
        TransferOrderStatus.ON_HOLD.value,
        TransferOrderStatus.ISSUED.value,
    ]

    # Failed orders
    FAILED = [TransferOrderStatus.CANCELLED.value]

    COMPLETE = [TransferOrderStatus.COMPLETE.value]
