"""Order status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class PurchaseOrderStatus(StatusCode):
    """Defines a set of status codes for a PurchaseOrder."""

    # Order status codes
    PENDING = 10, _('Pending'), ColorEnum.secondary  # Order is pending (not yet placed)
    PLACED = 20, _('Placed'), ColorEnum.primary  # Order has been placed with supplier
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning  # Order is on hold
    COMPLETE = 30, _('Complete'), ColorEnum.success  # Order has been completed
    CANCELLED = 40, _('Cancelled'), ColorEnum.danger  # Order was cancelled
    LOST = 50, _('Lost'), ColorEnum.warning  # Order was lost
    RETURNED = 60, _('Returned'), ColorEnum.warning  # Order was returned


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
    """Defines a set of status codes for a SalesOrder."""

    PENDING = 10, _('Pending'), ColorEnum.secondary  # Order is pending
    IN_PROGRESS = (
        15,
        _('In Progress'),
        ColorEnum.primary,
    )  # Order has been issued, and is in progress
    SHIPPED = 20, _('Shipped'), ColorEnum.success  # Order has been shipped to customer
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning  # Order is on hold
    COMPLETE = 30, _('Complete'), ColorEnum.success  # Order is complete
    CANCELLED = 40, _('Cancelled'), ColorEnum.danger  # Order has been cancelled
    LOST = 50, _('Lost'), ColorEnum.warning  # Order was lost
    RETURNED = 60, _('Returned'), ColorEnum.warning  # Order was returned


class SalesOrderStatusGroups:
    """Groups for SalesOrderStatus codes."""

    # Open orders
    OPEN = [
        SalesOrderStatus.PENDING.value,
        SalesOrderStatus.ON_HOLD.value,
        SalesOrderStatus.IN_PROGRESS.value,
    ]

    # Completed orders
    COMPLETE = [SalesOrderStatus.SHIPPED.value, SalesOrderStatus.COMPLETE.value]


class ReturnOrderStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrder."""

    # Order is pending, waiting for receipt of items
    PENDING = 10, _('Pending'), ColorEnum.secondary

    # Items have been received, and are being inspected
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
    """Defines a set of status codes for a ReturnOrderLineItem."""

    PENDING = 10, _('Pending'), ColorEnum.secondary

    # Item is to be returned to customer, no other action
    RETURN = 20, _('Return'), ColorEnum.success

    # Item is to be repaired, and returned to customer
    REPAIR = 30, _('Repair'), ColorEnum.primary

    # Item is to be replaced (new item shipped)
    REPLACE = 40, _('Replace'), ColorEnum.warning

    # Item is to be refunded (cannot be repaired)
    REFUND = 50, _('Refund'), ColorEnum.info

    # Item is rejected
    REJECT = 60, _('Reject'), ColorEnum.danger
