"""
Part database model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import math

import tablib

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse

from django.db import models
from django.core.validators import MinValueValidator

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from InvenTree.models import InvenTreeTree
from company.models import Company


class PartCategory(InvenTreeTree):
    """ PartCategory provides hierarchical organization of Part objects.
    """

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'pk': self.id})

    class Meta:
        verbose_name = "Part Category"
        verbose_name_plural = "Part Categories"

    @property
    def partcount(self):
        """ Return the total part count under this category
        (including children of child categories)
        """

        count = self.parts.count()

        for child in self.children.all():
            count += child.partcount

        return count

    @property
    def has_parts(self):
        """ True if there are any parts in this category """
        return self.parts.count() > 0


@receiver(pre_delete, sender=PartCategory, dispatch_uid='partcategory_delete_log')
def before_delete_part_category(sender, instance, using, **kwargs):
    """ Receives before_delete signal for PartCategory object

    Before deleting, update child Part and PartCategory objects:

    - For each child category, set the parent to the parent of *this* category
    - For each part, set the 'category' to the parent of *this* category
    """

    # Update each part in this category to point to the parent category
    for part in instance.parts.all():
        part.category = instance.parent
        part.save()

    # Update each child category
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()


# Function to automatically rename a part image on upload
# Format: part_pk.<img>
def rename_part_image(instance, filename):
    """ Function for renaming a part image file

    Args:
        instance: Instance of a Part object
        filename: Name of original uploaded file

    Returns:
        Cleaned filename in format part_<n>_img
    """

    base = 'part_images'

    if filename.count('.') > 0:
        ext = filename.split('.')[-1]
    else:
        ext = ''

    fn = 'part_{pk}_img'.format(pk=instance.pk)

    if ext:
        fn += '.' + ext

    return os.path.join(base, fn)


class Part(models.Model):
    """ Represents an abstract part
    Parts can be "stocked" in multiple warehouses,
    and can be combined to form other parts
    """

    def get_absolute_url(self):
        return reverse('part-detail', kwargs={'pk': self.id})

    # Short name of the part
    name = models.CharField(max_length=100, unique=True, help_text='Part name (must be unique)')

    # Longer description of the part (optional)
    description = models.CharField(max_length=250, help_text='Part description')

    # Internal Part Number (optional)
    # Potentially multiple parts map to the same internal IPN (variants?)
    # So this does not have to be unique
    IPN = models.CharField(max_length=100, blank=True, help_text='Internal Part Number')

    # Provide a URL for an external link
    URL = models.URLField(blank=True, help_text='Link to extenal URL')

    # Part category - all parts must be assigned to a category
    category = models.ForeignKey(PartCategory, related_name='parts',
                                 null=True, blank=True,
                                 on_delete=models.DO_NOTHING,
                                 help_text='Part category')

    image = models.ImageField(upload_to=rename_part_image, max_length=255, null=True, blank=True)

    default_location = models.ForeignKey('stock.StockLocation', on_delete=models.SET_NULL,
                                         blank=True, null=True,
                                         help_text='Where is this item normally stored?',
                                         related_name='default_parts')

    # Default supplier part
    default_supplier = models.ForeignKey('part.SupplierPart',
                                         on_delete=models.SET_NULL,
                                         blank=True, null=True,
                                         help_text='Default supplier part',
                                         related_name='default_parts')

    # Minimum "allowed" stock level
    minimum_stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], help_text='Minimum allowed stock level')

    # Units of quantity for this part. Default is "pcs"
    units = models.CharField(max_length=20, default="pcs", blank=True)

    # Can this part be built from other parts?
    buildable = models.BooleanField(default=False, help_text='Can this part be built from other parts?')

    # Can this part be used to make other parts?
    consumable = models.BooleanField(default=True, help_text='Can this part be used to build other parts?')

    # Is this part "trackable"?
    # Trackable parts can have unique instances
    # which are assigned serial numbers (or batch numbers)
    # and can have their movements tracked
    trackable = models.BooleanField(default=False, help_text='Does this part have tracking for unique items?')

    # Is this part "purchaseable"?
    purchaseable = models.BooleanField(default=True, help_text='Can this part be purchased from external suppliers?')

    # Can this part be sold to customers?
    salable = models.BooleanField(default=False, help_text="Can this part be sold to customers?")

    # Is this part active?
    active = models.BooleanField(default=True, help_text='Is this part active?')

    notes = models.TextField(blank=True)

    def __str__(self):
        return "{n} - {d}".format(n=self.name, d=self.description)

    class Meta:
        verbose_name = "Part"
        verbose_name_plural = "Parts"

    @property
    def category_path(self):
        if self.category:
            return self.category.pathstring
        return ''

    @property
    def available_stock(self):
        """
        Return the total available stock.
        This subtracts stock which is already allocated
        """

        total = self.total_stock

        total -= self.allocation_count

        return max(total, 0)

    @property
    def can_build(self):
        """ Return the number of units that can be build with available stock
        """

        # If this part does NOT have a BOM, result is simply the currently available stock
        if not self.has_bom:
            return self.available_stock

        total = None

        # Calculate the minimum number of parts that can be built using each sub-part
        for item in self.bom_items.all():
            stock = item.sub_part.available_stock
            n = int(1.0 * stock / item.quantity)

            if total is None or n < total:
                total = n

        return max(total, 0)

    @property
    def active_builds(self):
        """ Return a list of outstanding builds.
        Builds marked as 'complete' or 'cancelled' are ignored
        """

        return [b for b in self.builds.all() if b.is_active]

    @property
    def inactive_builds(self):
        """ Return a list of inactive builds
        """

        return [b for b in self.builds.all() if not b.is_active]

    @property
    def quantity_being_built(self):
        """ Return the current number of parts currently being built
        """

        return sum([b.quantity for b in self.active_builds])

    @property
    def build_allocation(self):
        """ Return list of builds to which this part is allocated
        """

        builds = []

        for item in self.used_in.all():

            for build in item.part.active_builds:
                b = {}

                b['build'] = build
                b['quantity'] = item.quantity * build.quantity

                builds.append(b)

        return builds

    @property
    def allocated_build_count(self):
        """ Return the total number of this that are allocated for builds
        """

        return sum([a['quantity'] for a in self.build_allocation])

    @property
    def allocation_count(self):
        """ Return true if any of this part is allocated:

        - To another build
        - To a customer order
        """

        return sum([
            self.allocated_build_count,
        ])

    @property
    def stock_entries(self):
        return [loc for loc in self.locations.all() if loc.in_stock]

    @property
    def total_stock(self):
        """ Return the total stock quantity for this part.
        Part may be stored in multiple locations
        """

        return sum([loc.quantity for loc in self.stock_entries])

    @property
    def has_bom(self):
        return self.bom_count > 0

    @property
    def bom_count(self):
        return self.bom_items.count()

    @property
    def used_in_count(self):
        return self.used_in.count()

    @property
    def supplier_count(self):
        # Return the number of supplier parts available for this part
        return self.supplier_parts.count()

    def export_bom(self, **kwargs):

        data = tablib.Dataset(headers=[
            'Part',
            'Description',
            'Quantity',
            'Note',
        ])

        for it in self.bom_items.all():
            line = []

            line.append(it.sub_part.name)
            line.append(it.sub_part.description)
            line.append(it.quantity)
            line.append(it.note)

            data.append(line)

        file_format = kwargs.get('format', 'csv').lower()

        return data.export(file_format)


def attach_file(instance, filename):
    """ Function for storing a file for a PartAttachment

    Args:
        instance: Instance of a PartAttachment object
        filename: name of uploaded file

    Returns:
        path to store file, format: 'part_file_<pk>_filename'
    """
    # Construct a path to store a file attachment
    return os.path.join('part_files', str(instance.part.id), filename)


class PartAttachment(models.Model):
    """ A PartAttachment links a file to a part
    Parts can have multiple files such as datasheets, etc
    """

    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='attachments')

    attachment = models.FileField(upload_to=attach_file, null=True, blank=True)

    @property
    def basename(self):
        return os.path.basename(self.attachment.name)


class BomItem(models.Model):
    """ A BomItem links a part to its component items.
    A part can have a BOM (bill of materials) which defines
    which parts are required (and in what quatity) to make it
    """

    def get_absolute_url(self):
        return reverse('bom-item-detail', kwargs={'pk': self.id})

    # A link to the parent part
    # Each part will get a reverse lookup field 'bom_items'
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='bom_items',
                             limit_choices_to={'buildable': True})

    # A link to the child item (sub-part)
    # Each part will get a reverse lookup field 'used_in'
    sub_part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='used_in',
                                 limit_choices_to={'consumable': True})

    # Quantity required
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])

    # Note attached to this BOM line item
    note = models.CharField(max_length=100, blank=True, help_text='Item notes')

    def clean(self):
        """ Check validity of the BomItem model.

        Performs model checks beyond simple field validation.

        - A part cannot refer to itself in its BOM
        - A part cannot refer to a part which refers to it
        """

        # A part cannot refer to itself in its BOM
        if self.part == self.sub_part:
            raise ValidationError({'sub_part': _('Part cannot be added to its own Bill of Materials')})

        # Test for simple recursion
        for item in self.sub_part.bom_items.all():
            if self.part == item.sub_part:
                raise ValidationError({'sub_part': _("Part '{p1}' is  used in BOM for '{p2}' (recursive)".format(p1=str(self.part), p2=str(self.sub_part)))})

    class Meta:
        verbose_name = "BOM Item"

        # Prevent duplication of parent/child rows
        unique_together = ('part', 'sub_part')

    def __str__(self):
        return "{par} -> {child} ({n})".format(
            par=self.part.name,
            child=self.sub_part.name,
            n=self.quantity)


class SupplierPart(models.Model):
    """ Represents a unique part as provided by a Supplier
    Each SupplierPart is identified by a MPN (Manufacturer Part Number)
    Each SupplierPart is also linked to a Part object.

    A Part may be available from multiple suppliers
    """

    def get_absolute_url(self):
        return reverse('supplier-part-detail', kwargs={'pk': self.id})

    class Meta:
        unique_together = ('part', 'supplier', 'SKU')

    # Link to an actual part
# The part will have a field 'supplier_parts' which links to the supplier part options
    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='supplier_parts',
                             limit_choices_to={'purchaseable': True},
                             )

    supplier = models.ForeignKey(Company, on_delete=models.CASCADE,
                                 related_name='parts',
                                 limit_choices_to={'is_supplier': True}
                                 )

    SKU = models.CharField(max_length=100, help_text='Supplier stock keeping unit')

    manufacturer = models.CharField(max_length=100, blank=True, help_text='Manufacturer')

    MPN = models.CharField(max_length=100, blank=True, help_text='Manufacturer part number')

    URL = models.URLField(blank=True)

    description = models.CharField(max_length=250, blank=True, help_text='Supplier part description')

    # Note attached to this BOM line item
    note = models.CharField(max_length=100, blank=True, help_text='Notes')

    # Default price for a single unit
    single_price = models.DecimalField(max_digits=10, decimal_places=3, default=0, validators=[MinValueValidator(0)], help_text='Price for single quantity')

    # Base charge added to order independent of quantity e.g. "Reeling Fee"
    base_cost = models.DecimalField(max_digits=10, decimal_places=3, default=0, validators=[MinValueValidator(0)], help_text='Minimum charge (e.g. stocking fee)')

    # packaging that the part is supplied in, e.g. "Reel"
    packaging = models.CharField(max_length=50, blank=True, help_text='Part packaging')

    # multiple that the part is provided in
    multiple = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text='Order multiple')

    # Mimumum number required to order
    minimum = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text='Minimum order quantity (MOQ)')

    # lead time for parts that cannot be delivered immediately
    lead_time = models.DurationField(blank=True, null=True)

    @property
    def manufacturer_string(self):

        items = []

        if self.manufacturer:
            items.append(self.manufacturer)
        if self.MPN:
            items.append(self.MPN)

        return ' | '.join(items)

    @property
    def has_price_breaks(self):
        return self.price_breaks.count() > 0

    def get_price(self, quantity, moq=True, multiples=True):
        """ Calculate the supplier price based on quantity price breaks.
        
        - If no price breaks available, use the single_price field
        - Don't forget to add in flat-fee cost (base_cost field)
        - If MOQ (minimum order quantity) is required, bump quantity
        - If order multiples are to be observed, then we need to calculate based on that, too
        """

        # Order multiples
        if multiples:
            quantity = int(math.ceil(quantity / self.multipe) * self.multiple)

        # Minimum ordering requirement
        if moq and self.minimum > quantity:
            quantity = self.minimum

        pb_found = False
        pb_quantity = -1
        pb_cost = 0.0

        for pb in self.price_breaks.all():
            # Ignore this pricebreak!
            if pb.quantity > quantity:
                continue

            pb_found = True

            # If this price-break quantity is the largest so far, use it!
            if pb.quantity > pb_quantity:
                pb_quantity = pb.quantity
                pb_cost = pb.cost

        # No appropriate price-break found - use the single cost!
        if pb_found:
            cost = pb_cost * quantity
        else:
            cost = self.single_price * quantity

        return cost + self.base_cost

    def __str__(self):
        return "{supplier} ({sku})".format(
            sku=self.SKU,
            supplier=self.supplier.name)


class SupplierPriceBreak(models.Model):
    """ Represents a quantity price break for a SupplierPart
    - Suppliers can offer discounts at larger quantities
    - SupplierPart(s) may have zero-or-more associated SupplierPriceBreak(s)
    """

    part = models.ForeignKey(SupplierPart, on_delete=models.CASCADE, related_name='price_breaks')

    # At least 2 units are required for a 'price break' - Otherwise, just use single-price!
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(2)])

    cost = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ("part", "quantity")

    def __str__(self):
        return "{mpn} - {cost}{currency} @ {quan}".format(
            mpn=self.part.MPN,
            cost=self.cost,
            currency=self.currency if self.currency else '',
            quan=self.quantity)
