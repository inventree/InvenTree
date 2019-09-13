"""
Company database model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import math
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum

from django.apps import apps
from django.urls import reverse
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

from InvenTree.fields import InvenTreeURLField
from InvenTree.status_codes import OrderStatus
from common.models import Currency


def rename_company_image(instance, filename):
    """ Function to rename a company image after upload

    Args:
        instance: Company object
        filename: uploaded image filename

    Returns:
        New image filename
    """

    base = 'company_images'

    if filename.count('.') > 0:
        ext = filename.split('.')[-1]
    else:
        ext = ''

    fn = 'company_{pk}_img'.format(pk=instance.pk)

    if ext:
        fn += '.' + ext

    return os.path.join(base, fn)


class Company(models.Model):
    """ A Company object represents an external company.
    It may be a supplier or a customer (or both).

    Attributes:
        name: Brief name of the company
        description: Longer form description
        website: URL for the company website
        address: Postal address
        phone: contact phone number
        email: contact email address
        URL: Secondary URL e.g. for link to internal Wiki page
        image: Company image / logo
        notes: Extra notes about the company
        is_customer: boolean value, is this company a customer
        is_supplier: boolean value, is this company a supplier
    """

    name = models.CharField(max_length=100, blank=False, unique=True,
                            help_text='Company name')

    description = models.CharField(max_length=500, help_text='Description of the company')

    website = models.URLField(blank=True, help_text='Company website URL')

    address = models.CharField(max_length=200,
                               blank=True, help_text='Company address')

    phone = models.CharField(max_length=50,
                             blank=True, help_text='Contact phone number')

    email = models.EmailField(blank=True, help_text='Contact email address')

    contact = models.CharField(max_length=100,
                               blank=True, help_text='Point of contact')

    URL = InvenTreeURLField(blank=True, help_text='Link to external company information')

    image = models.ImageField(upload_to=rename_company_image, max_length=255, null=True, blank=True)

    notes = models.TextField(blank=True)

    is_customer = models.BooleanField(default=False, help_text='Do you sell items to this company?')

    is_supplier = models.BooleanField(default=True, help_text='Do you purchase items from this company?')

    def __str__(self):
        """ Get string representation of a Company """
        return "{n} - {d}".format(n=self.name, d=self.description)

    def get_absolute_url(self):
        """ Get the web URL for the detail view for this Company """
        return reverse('company-detail', kwargs={'pk': self.id})

    def get_image_url(self):
        """ Return the URL of the image for this company """

        if self.image:
            return os.path.join(settings.MEDIA_URL, str(self.image.url))
        else:
            return static('/img/blank_image.png')

    @property
    def part_count(self):
        """ The number of parts supplied by this company """
        return self.parts.count()

    @property
    def has_parts(self):
        """ Return True if this company supplies any parts """
        return self.part_count > 0

    @property
    def stock_items(self):
        """ Return a list of all stock items supplied by this company """
        stock = apps.get_model('stock', 'StockItem')
        return stock.objects.filter(supplier_part__supplier=self.id).all()

    @property
    def stock_count(self):
        """ Return the number of stock items supplied by this company """
        stock = apps.get_model('stock', 'StockItem')
        return stock.objects.filter(supplier_part__supplier=self.id).count()

    def outstanding_purchase_orders(self):
        """ Return purchase orders which are 'outstanding' """
        return self.purchase_orders.filter(status__in=OrderStatus.OPEN)

    def pending_purchase_orders(self):
        """ Return purchase orders which are PENDING (not yet issued) """
        return self.purchase_orders.filter(status=OrderStatus.PENDING)

    def closed_purchase_orders(self):
        """ Return purchase orders which are not 'outstanding'

        - Complete
        - Failed / lost
        - Returned
        """

        return self.purchase_orders.exclude(status__in=OrderStatus.OPEN)

    def complete_purchase_orders(self):
        return self.purchase_orders.filter(status=OrderStatus.COMPLETE)

    def failed_purchase_orders(self):
        """ Return any purchase orders which were not successful """

        return self.purchase_orders.filter(status__in=OrderStatus.FAILED)


class Contact(models.Model):
    """ A Contact represents a person who works at a particular company.
    A Company may have zero or more associated Contact objects.

    Attributes:
        company: Company link for this contact
        name: Name of the contact
        phone: contact phone number
        email: contact email
        role: position in company
    """

    company = models.ForeignKey(Company, related_name='contacts',
                                on_delete=models.CASCADE)

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=100, blank=True)

    email = models.EmailField(blank=True)

    role = models.CharField(max_length=100, blank=True)

    company = models.ForeignKey(Company, related_name='contacts',
                                on_delete=models.CASCADE)


class SupplierPart(models.Model):
    """ Represents a unique part as provided by a Supplier
    Each SupplierPart is identified by a MPN (Manufacturer Part Number)
    Each SupplierPart is also linked to a Part object.
    A Part may be available from multiple suppliers

    Attributes:
        part: Link to the master Part
        supplier: Company that supplies this SupplierPart object
        SKU: Stock keeping unit (supplier part number)
        manufacturer: Manufacturer name
        MPN: Manufacture part number
        URL: Link to external website for this part
        description: Descriptive notes field
        note: Longer form note field
        base_cost: Base charge added to order independent of quantity e.g. "Reeling Fee"
        multiple: Multiple that the part is provided in
        lead_time: Supplier lead time
        packaging: packaging that the part is supplied in, e.g. "Reel"
    """

    def get_absolute_url(self):
        return reverse('supplier-part-detail', kwargs={'pk': self.id})

    class Meta:
        unique_together = ('part', 'supplier', 'SKU')

        # This model was moved from the 'Part' app
        db_table = 'part_supplierpart'

    part = models.ForeignKey('part.Part', on_delete=models.CASCADE,
                             related_name='supplier_parts',
                             limit_choices_to={
                                 'purchaseable': True,
                                 'is_template': False,
                             },
                             help_text='Select part',
                             )

    supplier = models.ForeignKey(Company, on_delete=models.CASCADE,
                                 related_name='parts',
                                 limit_choices_to={'is_supplier': True},
                                 help_text='Select supplier',
                                 )

    SKU = models.CharField(max_length=100, help_text='Supplier stock keeping unit')

    manufacturer = models.CharField(max_length=100, blank=True, help_text='Manufacturer')

    MPN = models.CharField(max_length=100, blank=True, help_text='Manufacturer part number')

    URL = InvenTreeURLField(blank=True, help_text='URL for external supplier part link')

    description = models.CharField(max_length=250, blank=True, help_text='Supplier part description')

    note = models.CharField(max_length=100, blank=True, help_text='Notes')

    base_cost = models.DecimalField(max_digits=10, decimal_places=3, default=0, validators=[MinValueValidator(0)], help_text='Minimum charge (e.g. stocking fee)')

    packaging = models.CharField(max_length=50, blank=True, help_text='Part packaging')
    
    multiple = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text='Order multiple')

    # TODO - Reimplement lead-time as a charfield with special validation (pattern matching).
    # lead_time = models.DurationField(blank=True, null=True)

    @property
    def manufacturer_string(self):
        """ Format a MPN string for this SupplierPart.
        Concatenates manufacture name and part number.
        """

        items = []

        if self.manufacturer:
            items.append(self.manufacturer)
        if self.MPN:
            items.append(self.MPN)

        return ' | '.join(items)

    @property
    def has_price_breaks(self):
        return self.price_breaks.count() > 0

    @property
    def price_breaks(self):
        """ Return the associated price breaks in the correct order """
        return self.pricebreaks.order_by('quantity').all()

    @property
    def unit_pricing(self):
        return self.get_price(1)

    def get_price(self, quantity, moq=True, multiples=True):
        """ Calculate the supplier price based on quantity price breaks.

        - Don't forget to add in flat-fee cost (base_cost field)
        - If MOQ (minimum order quantity) is required, bump quantity
        - If order multiples are to be observed, then we need to calculate based on that, too
        """

        price_breaks = self.price_breaks.filter(quantity__lte=quantity)

        # No price break information available?
        if len(price_breaks) == 0:
            return None

        # Order multiples
        if multiples:
            quantity = int(math.ceil(quantity / self.multiple) * self.multiple)

        pb_found = False
        pb_quantity = -1
        pb_cost = 0.0

        for pb in self.price_breaks.all():
            # Ignore this pricebreak (quantity is too high)
            if pb.quantity > quantity:
                continue

            pb_found = True

            # If this price-break quantity is the largest so far, use it!
            if pb.quantity > pb_quantity:
                pb_quantity = pb.quantity
                # Convert everything to base currency
                pb_cost = pb.converted_cost

        if pb_found:
            cost = pb_cost * quantity
            return cost + self.base_cost
        else:
            return None

    def open_orders(self):
        """ Return a database query for PO line items for this SupplierPart,
        limited to purchase orders that are open / outstanding.
        """

        return self.purchase_order_line_items.prefetch_related('order').filter(order__status__in=OrderStatus.OPEN)

    def on_order(self):
        """ Return the total quantity of items currently on order.

        Subtract partially received stock as appropriate
        """

        totals = self.open_orders().aggregate(Sum('quantity'), Sum('received'))

        # Quantity on order
        q = totals.get('quantity__sum', 0)

        # Quantity received
        r = totals.get('received__sum', 0)

        if q is None or r is None:
            return 0
        else:
            return max(q - r, 0)

    def purchase_orders(self):
        """ Returns a list of purchase orders relating to this supplier part """

        return [line.order for line in self.purchase_order_line_items.all().prefetch_related('order')]

    def __str__(self):
        s = "{supplier} ({sku})".format(
            sku=self.SKU,
            supplier=self.supplier.name)

        if self.manufacturer_string:
            s = s + ' - ' + self.manufacturer_string
        
        return s


class SupplierPriceBreak(models.Model):
    """ Represents a quantity price break for a SupplierPart.
    - Suppliers can offer discounts at larger quantities
    - SupplierPart(s) may have zero-or-more associated SupplierPriceBreak(s)

    Attributes:
        part: Link to a SupplierPart object that this price break applies to
        quantity: Quantity required for price break
        cost: Cost at specified quantity
        currency: Reference to the currency of this pricebreak (leave empty for base currency)
    """

    part = models.ForeignKey(SupplierPart, on_delete=models.CASCADE, related_name='pricebreaks')

    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    cost = models.DecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)])

    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.SET_NULL)

    @property
    def converted_cost(self):
        """ Return the cost of this price break, converted to the base currency """

        scaler = Decimal(1.0)

        if self.currency:
            scaler = self.currency.value

        return self.cost * scaler

    class Meta:
        unique_together = ("part", "quantity")

        # This model was moved from the 'Part' app
        db_table = 'part_supplierpricebreak'

    def __str__(self):
        return "{mpn} - {cost} @ {quan}".format(
            mpn=self.part.MPN,
            cost=self.cost,
            quan=self.quantity)
