from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator

from InvenTree.models import Company
from part.models import Part


class Supplier(Company):
    """ Represents a manufacturer or supplier
    """
    pass


class Manufacturer(Company):
    """ Represents a manfufacturer
    """
    pass


class Customer(Company):
    """ Represents a customer
    """
    pass


class SupplierPart(models.Model):
    """ Represents a unique part as provided by a Supplier
    Each SupplierPart is identified by a MPN (Manufacturer Part Number)
    Each SupplierPart is also linked to a Part object
    - A Part may be available from multiple suppliers
    """

    class Meta:
        unique_together = ('part', 'supplier', 'SKU')

    part = models.ForeignKey(Part, null=True, blank=True, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    SKU = models.CharField(max_length=100)

    manufacturer = models.ForeignKey(Manufacturer, blank=True, null=True, on_delete=models.CASCADE)
    MPN = models.CharField(max_length=100, blank=True)

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
