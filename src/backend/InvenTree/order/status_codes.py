"""Order status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import StatusCode


class PurchaseOrderStatus(StatusCode):
    """Defines a set of status codes for a PurchaseOrder."""

    # Order status codes
    PENDING = 10, _('Pending'), 'secondary'  # Order is pending (not yet placed)
    PLACED = 20, _('Placed'), 'primary'  # Order has been placed with supplier
    COMPLETE = 30, _('Complete'), 'success'  # Order has been completed
    CANCELLED = 40, _('Cancelled'), 'danger'  # Order was cancelled
    LOST = 50, _('Lost'), 'warning'  # Order was lost
    RETURNED = 60, _('Returned'), 'warning'  # Order was returned


class PurchaseOrderStatusGroups:
    """Groups for PurchaseOrderStatus codes."""

    # Open orders
    OPEN = [PurchaseOrderStatus.PENDING.value, PurchaseOrderStatus.PLACED.value]

    # Failed orders
    FAILED = [
        PurchaseOrderStatus.CANCELLED.value,
        PurchaseOrderStatus.LOST.value,
        PurchaseOrderStatus.RETURNED.value,
    ]


class SalesOrderStatus(StatusCode):
    """Defines a set of status codes for a SalesOrder."""

    PENDING = 10, _('Pending'), 'secondary'  # Order is pending
    IN_PROGRESS = (
        15,
        _('In Progress'),
        'primary',
    )  # Order has been issued, and is in progress
    SHIPPED = 20, _('Shipped'), 'success'  # Order has been shipped to customer
    COMPLETE = 30, _('Complete'), 'success'  # Order is complete
    CANCELLED = 40, _('Cancelled'), 'danger'  # Order has been cancelled
    LOST = 50, _('Lost'), 'warning'  # Order was lost
    RETURNED = 60, _('Returned'), 'warning'  # Order was returned


class SalesOrderStatusGroups:
    """Groups for SalesOrderStatus codes."""

    # Open orders
    OPEN = [SalesOrderStatus.PENDING.value, SalesOrderStatus.IN_PROGRESS.value]

    # Completed orders
    COMPLETE = [SalesOrderStatus.SHIPPED.value, SalesOrderStatus.COMPLETE.value]


class ReturnOrderStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrder."""

    # Order is pending, waiting for receipt of items
    PENDING = 10, _('Pending'), 'secondary'

    # Items have been received, and are being inspected
    IN_PROGRESS = 20, _('In Progress'), 'primary'

    COMPLETE = 30, _('Complete'), 'success'
    CANCELLED = 40, _('Cancelled'), 'danger'


class ReturnOrderStatusGroups:
    """Groups for ReturnOrderStatus codes."""

    OPEN = [ReturnOrderStatus.PENDING.value, ReturnOrderStatus.IN_PROGRESS.value]


class ReturnOrderLineStatus(StatusCode):
    """Defines a set of status codes for a ReturnOrderLineItem."""

    PENDING = 10, _('Pending'), 'secondary'

    # Item is to be returned to customer, no other action
    RETURN = 20, _('Return'), 'success'

    # Item is to be repaired, and returned to customer
    REPAIR = 30, _('Repair'), 'primary'

    # Item is to be replaced (new item shipped)
    REPLACE = 40, _('Replace'), 'warning'

    # Item is to be refunded (cannot be repaired)
    REFUND = 50, _('Refund'), 'info'

    # Item is rejected
    REJECT = 60, _('Reject'), 'danger'
