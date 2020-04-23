from django.utils.translation import ugettext as _


class StatusCode:
    """
    Base class for representing a set of StatusCodes.
    This is used to map a set of integer values to text.
    """

    labels = {}

    @classmethod
    def render(cls, key):
        """
        Render the value as a label.
        """

        # If the key cannot be found, pass it back
        if key not in cls.options.keys():
            return key
        
        value = cls.options.get(key, key)
        label = cls.labels.get(key, None)

        if label:
            return "<span class='label label-{label}'>{value}</span>".format(label=label, value=value)
        else:
            return value

    @classmethod
    def list(cls):
        """
        Return the StatusCode options as a list of mapped key / value items
        """

        codes = []

        for key in cls.options.keys():

            opt = {
                'key': key,
                'value': cls.options[key]
            }

            label = cls.labels.get(key)

            if label:
                opt['label'] = label

            codes.append(opt)

        return codes

    @classmethod
    def items(cls):
        return cls.options.items()

    @classmethod
    def label(cls, value):
        """ Return the status code label associated with the provided value """
        return cls.options.get(value, value)

    @classmethod
    def value(cls, label):
        """ Return the value associated with the provided label """
        for k in cls.options.keys():
            if cls.options[k].lower() == label.lower():
                return k

        raise ValueError("Label not found")


class PurchaseOrderStatus(StatusCode):
    """
    Defines a set of status codes for a PurchaseOrder
    """

    # Order status codes
    PENDING = 10  # Order is pending (not yet placed)
    PLACED = 20  # Order has been placed with supplier
    COMPLETE = 30  # Order has been completed
    CANCELLED = 40  # Order was cancelled
    LOST = 50  # Order was lost
    RETURNED = 60  # Order was returned

    options = {
        PENDING: _("Pending"),
        PLACED: _("Placed"),
        COMPLETE: _("Complete"),
        CANCELLED: _("Cancelled"),
        LOST: _("Lost"),
        RETURNED: _("Returned"),
    }

    labels = {
        PENDING: "primary",
        PLACED: "primary",
        COMPLETE: "success",
        CANCELLED: "danger",
        LOST: "warning",
        RETURNED: "warning",
    }

    # Open orders
    OPEN = [
        PENDING,
        PLACED,
    ]

    # Failed orders
    FAILED = [
        CANCELLED,
        LOST,
        RETURNED
    ]


class SalesOrderStatus(StatusCode):
    """ Defines a set of status codes for a SalesOrder """

    PENDING = 10  # Order is pending
    SHIPPED = 20  # Order has been shipped to customer
    CANCELLED = 40  # Order has been cancelled
    LOST = 50  # Order was lost
    RETURNED = 60  # Order was returned

    options = {
        PENDING: _("Pending"),
        SHIPPED: _("Shipped"),
        CANCELLED: _("Cancelled"),
        LOST: _("Lost"),
        RETURNED: _("Returned"),
    }

    labels = {
        PENDING: "primary",
        SHIPPED: "success",
        CANCELLED: "danger",
        LOST: "warning",
        RETURNED: "warning",
    }

class StockStatus(StatusCode):

    OK = 10  # Item is OK
    ATTENTION = 50  # Item requires attention
    DAMAGED = 55  # Item is damaged
    DESTROYED = 60  # Item is destroyed
    LOST = 70  # Item has been lost
    RETURNED = 85  # Item has been returned from a customer

    # Any stock code above 100 means that the stock item is not "in stock"
    # This can be used as a quick check for filtering
    NOT_IN_STOCK = 100

    SHIPPED = 110  # Item has been shipped to a customer

    options = {
        OK: _("OK"),
        ATTENTION: _("Attention needed"),
        DAMAGED: _("Damaged"),
        DESTROYED: _("Destroyed"),
        LOST: _("Lost"),
        SHIPPED: _("Shipped"),
        RETURNED: _("Returned"),
    }

    labels = {
        OK: 'success',
        ATTENTION: 'warning',
        DAMAGED: 'danger',
        DESTROYED: 'danger',
    }

    # The following codes correspond to parts that are 'available' or 'in stock'
    AVAILABLE_CODES = [
        OK,
        ATTENTION,
        DAMAGED,
        RETURNED,
    ]

    # The following codes correspond to parts that are 'unavailable'
    UNAVAILABLE_CODES = [
        DESTROYED,
        LOST,
        SHIPPED,
    ]


class BuildStatus(StatusCode):

    # Build status codes
    PENDING = 10  # Build is pending / active
    ALLOCATED = 20  # Parts have been removed from stock
    CANCELLED = 30  # Build was cancelled
    COMPLETE = 40  # Build is complete

    options = {
        PENDING: _("Pending"),
        ALLOCATED: _("Allocated"),
        CANCELLED: _("Cancelled"),
        COMPLETE: _("Complete"),
    }

    labels = {
        PENDING: 'primary',
        ALLOCATED: 'info',
        COMPLETE: 'success',
        CANCELLED: 'danger',
    }

    ACTIVE_CODES = [
        PENDING,
        ALLOCATED
    ]
