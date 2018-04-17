# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from django.db import models
from django.core.validators import MinValueValidator

from InvenTree.models import Company
from part.models import Part


class Supplier(Company):
    """ Represents a manufacturer or supplier
    """

    def get_absolute_url(self):
        return "/supplier/{id}/".format(id=self.id)

    @property
    def part_count(self):
        return self.parts.count()

    @property
    def has_parts(self):
        return self.part_count > 0

    @property
    def order_count(self):
        return self.orders.count()

    @property
    def has_orders(self):
        return self.order_count > 0


class Manufacturer(Company):
    """ Represents a manfufacturer
    """
    pass


class SupplierPart(models.Model):
    """ Represents a unique part as provided by a Supplier
    Each SupplierPart is identified by a MPN (Manufacturer Part Number)
    Each SupplierPart is also linked to a Part object
    - A Part may be available from multiple suppliers
    """

    def get_absolute_url(self):
        return "/supplier/part/{id}/".format(id=self.id)

    class Meta:
        unique_together = ('part', 'supplier', 'SKU')

    # Link to an actual part
# The part will have a field 'supplier_parts' which links to the supplier part options
    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='supplier_parts')

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE,
                                 related_name='parts')

    SKU = models.CharField(max_length=100, help_text='Supplier stock keeping unit')

    manufacturer = models.ForeignKey(Manufacturer, blank=True, null=True, on_delete=models.SET_NULL, help_text='Manufacturer')

    MPN = models.CharField(max_length=100, blank=True, help_text='Manufacturer part number')

    URL = models.URLField(blank=True)

    description = models.CharField(max_length=250, blank=True)

    # Default price for a single unit
    single_price = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Base charge added to order independent of quantity e.g. "Reeling Fee"
    base_cost = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # packaging that the part is supplied in, e.g. "Reel"
    packaging = models.CharField(max_length=50, blank=True)

    # multiple that the part is provided in
    multiple = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])

    # Mimumum number required to order
    minimum = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])

    # lead time for parts that cannot be delivered immediately
    lead_time = models.DurationField(blank=True, null=True)

    def __str__(self):
        return "{sku} - {supplier}".format(
            sku=self.SKU,
            supplier=self.supplier.name)


class SupplierPriceBreak(models.Model):
    """ Represents a quantity price break for a SupplierPart
    - Suppliers can offer discounts at larger quantities
    - SupplierPart(s) may have zero-or-more associated SupplierPriceBreak(s)
    """

    part = models.ForeignKey(SupplierPart, on_delete=models.CASCADE, related_name='price_breaks')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    cost = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        unique_together = ("part", "quantity")

    def __str__(self):
        return "{mpn} - {cost}{currency} @ {quan}".format(
            mpn=self.part.MPN,
            cost=self.cost,
            currency=self.currency if self.currency else '',
            quan=self.quantity)


class SupplierOrder(models.Model):
    """
    An order of parts from a supplier, made up of multiple line items
    """

    def get_absolute_url(self):
        return "/supplier/order/{id}/".format(id=self.id)

    # Interal reference for this order
    internal_ref = models.CharField(max_length=25, unique=True)

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE,
                                 related_name='orders')

    created_date = models.DateField(auto_now_add=True, editable=False)

    issued_date = models.DateField(blank=True, null=True, help_text="Date the purchase order was issued")

    notes = models.TextField(blank=True, help_text="Order notes")

    def __str__(self):
        return "PO {ref} ({status})".format(ref=self.internal_ref,
                                            status=self.get_status_display)

    PENDING = 10  # Order is pending (not yet placed)
    PLACED = 20  # Order has been placed
    RECEIVED = 30  # Order has been received
    CANCELLED = 40  # Order was cancelled
    LOST = 50  # Order was lost

    ORDER_STATUS_CODES = {PENDING: _("Pending"),
                          PLACED: _("Placed"),
                          CANCELLED: _("Cancelled"),
                          RECEIVED: _("Received"),
                          LOST: _("Lost")
                         }

    status = models.PositiveIntegerField(default=PENDING,
                                         choices=ORDER_STATUS_CODES.items())

    delivery_date = models.DateField(blank=True, null=True)



class SupplierOrderLineItem(models.Model):
    """
    A line item in a supplier order, corresponding to some quantity of part
    """

    class Meta:
        unique_together = [
            ('order', 'line_number'),
            ('order', 'supplier_part'),
            ('order', 'internal_part'),
        ]

    order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE)

    line_number = models.PositiveIntegerField(default=1)

    internal_part = models.ForeignKey(Part, null=True, blank=True, on_delete=models.SET_NULL)

    supplier_part = models.ForeignKey(SupplierPart, null=True, blank=True, on_delete=models.SET_NULL)

    quantity = models.PositiveIntegerField(default=1)

    notes = models.TextField(blank=True)

    received = models.BooleanField(default=False)
