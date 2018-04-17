from django.db import models

from InvenTree.models import Company
from part.models import Part

import datetime


class Customer(Company):
    """ Represents a customer
    """
    pass


class CustomerOrder(models.Model):
    """
    An order from a customer, made up of multiple 'lines'
    """
    # Reference 'number' internal to company, must be unique
    internal_ref = models.CharField(max_length=100, unique=True)

    # TODO: Should the Customer model move to the customer_orders app?
    # Orders can exist even if the customer doesn't in the database
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL,
                                 blank=True, null=True, help_text="Customer that placed this order")

    # Reference from customer, if provided
    customer_ref = models.CharField(max_length=100, blank=True, default="")

    # TODO: Should the customer and customer_ref together be unique?

    # Date the order was entered into system
    created_date = models.DateField(auto_now_add=True, blank=True, help_text="Date order entered "
                                                                                                 "in system")

    # Date the order was issued on the paperwork, if provided
    issued_date = models.DateField(blank=True, help_text="Date order issued by customer")

    # Order notes
    notes = models.TextField(blank=True, default="", help_text="Order notes")

    def __str__(self):
        return "OrderRef {internal_ref}".format(internal_ref=self.internal_ref)


class CustomerOrderLine(models.Model):
    """
    A line on an order from a customer, corresponding to some quantity of some parts (hopefully just one part per line
    in a sane world, but maybe not).

    The line describes the Part ordered, but something needs to associate the StockItem assigned, possibly that will
    be the StockItem itself.
    """

    class Meta:
        unique_together = [
            ('customer_order', 'line_number')
        ]

    # Point to a specific customer order
    customer_order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, help_text="Order this line belongs to")

    line_number = models.PositiveIntegerField(default=0, help_text="Line number")

    # TODO: for now, each line corresponds to some quantity of some part, but in future we might want more flexibility
    part = models.ForeignKey(Part, blank=True, help_text="Part")

    # TODO: should quantity field here somehow related to quantity field of related part? Views will handle this, right?
    quantity = models.PositiveIntegerField(blank=True, help_text="Quantity of part")

    # Line notes
    notes = models.TextField(blank=True, help_text="Line notes")

