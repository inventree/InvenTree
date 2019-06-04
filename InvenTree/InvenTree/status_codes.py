from django.utils.translation import ugettext as _


class StatusCode:

    @classmethod
    def items(cls):
        return cls.options.items()


class OrderStatus(StatusCode):

    # Order status codes
    PENDING = 10  # Order is pending (not yet placed)
    PLACED = 20  # Order has been placed
    COMPLETE = 30  # Order has been completed
    CANCELLED = 40  # Order was cancelled
    LOST = 50  # Order was lost
    RETURNED = 60 # Order was returned

    options = {
        PENDING: _("Pending"),
        PLACED: _("Placed"),
        COMPLETE: _("Complete"),
        CANCELLED: _("Cancelled"),
        LOST: _("Lost"),
        RETURNED: _("Returned"),
    }
