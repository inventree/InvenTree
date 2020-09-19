"""
Part database model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse

from django.db import models, transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.core.validators import MinValueValidator

from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from markdownx.models import MarkdownxField

from django_cleanup import cleanup

from mptt.models import TreeForeignKey, MPTTModel

from stdimage.models import StdImageField

from decimal import Decimal
from datetime import datetime
from rapidfuzz import fuzz
import hashlib

from InvenTree import helpers
from InvenTree import validators
from InvenTree.models import InvenTreeTree, InvenTreeAttachment
from InvenTree.fields import InvenTreeURLField
from InvenTree.helpers import decimal2string, normalize

from InvenTree.status_codes import BuildStatus, PurchaseOrderStatus

from build import models as BuildModels
from order import models as OrderModels
from company.models import SupplierPart
from stock import models as StockModels

import common.models


class PartCategory(InvenTreeTree):
    """ PartCategory provides hierarchical organization of Part objects.

    Attributes:
        name: Name of this category
        parent: Parent category
        default_location: Default storage location for parts in this category or child categories
        default_keywords: Default keywords for parts created in this category
    """

    default_location = TreeForeignKey(
        'stock.StockLocation', related_name="default_categories",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text=_('Default location for parts in this category')
    )

    default_keywords = models.CharField(null=True, blank=True, max_length=250, help_text=_('Default keywords for parts in this category'))

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'pk': self.id})

    class Meta:
        verbose_name = _("Part Category")
        verbose_name_plural = _("Part Categories")

    def get_parts(self, cascade=True):
        """ Return a queryset for all parts under this category.

        args:
            cascade - If True, also look under subcategories (default = True)
        """

        if cascade:
            """ Select any parts which exist in this category or any child categories """
            query = Part.objects.filter(category__in=self.getUniqueChildren(include_self=True))
        else:
            query = Part.objects.filter(category=self.pk)

        return query

    @property
    def item_count(self):
        return self.partcount()

    def partcount(self, cascade=True, active=False):
        """ Return the total part count under this category
        (including children of child categories)
        """

        query = self.get_parts(cascade=cascade)

        if active:
            query = query.filter(active=True)

        return query.count()

    @property
    def has_parts(self):
        """ True if there are any parts in this category """
        return self.partcount() > 0


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


def rename_part_image(instance, filename):
    """ Function for renaming a part image file

    Args:
        instance: Instance of a Part object
        filename: Name of original uploaded file

    Returns:
        Cleaned filename in format part_<n>_img
    """

    base = 'part_images'
    fname = os.path.basename(filename)

    return os.path.join(base, fname)


def match_part_names(match, threshold=80, reverse=True, compare_length=False):
    """ Return a list of parts whose name matches the search term using fuzzy search.

    Args:
        match: Term to match against
        threshold: Match percentage that must be exceeded (default = 65)
        reverse: Ordering for search results (default = True - highest match is first)
        compare_length: Include string length checks

    Returns:
        A sorted dict where each element contains the following key:value pairs:
            - 'part' : The matched part
            - 'ratio' : The matched ratio
    """

    match = str(match).strip().lower()

    if len(match) == 0:
        return []

    parts = Part.objects.all()

    matches = []

    for part in parts:
        compare = str(part.name).strip().lower()

        if len(compare) == 0:
            continue

        ratio = fuzz.partial_token_sort_ratio(compare, match)

        if compare_length:
            # Also employ primitive length comparison
            # TODO - Improve this somewhat...
            l_min = min(len(match), len(compare))
            l_max = max(len(match), len(compare))

            ratio *= (l_min / l_max)

        if ratio >= threshold:
            matches.append({
                'part': part,
                'ratio': ratio
            })

    matches = sorted(matches, key=lambda item: item['ratio'], reverse=reverse)

    return matches


@cleanup.ignore
class Part(MPTTModel):
    """ The Part object represents an abstract part, the 'concept' of an actual entity.

    An actual physical instance of a Part is a StockItem which is treated separately.

    Parts can be used to create other parts (as part of a Bill of Materials or BOM).

    Attributes:
        name: Brief name for this part
        variant: Optional variant number for this part - Must be unique for the part name
        category: The PartCategory to which this part belongs
        description: Longer form description of the part
        keywords: Optional keywords for improving part search results
        IPN: Internal part number (optional)
        revision: Part revision
        is_template: If True, this part is a 'template' part and cannot be instantiated as a StockItem
        link: Link to an external page with more information about this part (e.g. internal Wiki)
        image: Image of this part
        default_location: Where the item is normally stored (may be null)
        default_supplier: The default SupplierPart which should be used to procure and stock this part
        minimum_stock: Minimum preferred quantity to keep in stock
        units: Units of measure for this part (default='pcs')
        salable: Can this part be sold to customers?
        assembly: Can this part be build from other parts?
        component: Can this part be used to make other parts?
        purchaseable: Can this part be purchased from suppliers?
        trackable: Trackable parts can have unique serial numbers assigned, etc, etc
        active: Is this part active? Parts are deactivated instead of being deleted
        virtual: Is this part "virtual"? e.g. a software product or similar
        notes: Additional notes field for this part
        creation_date: Date that this part was added to the database
        creation_user: User who added this part to the database
        responsible: User who is responsible for this part (optional)
    """

    class Meta:
        verbose_name = _("Part")
        verbose_name_plural = _("Parts")
        ordering = ['name', ]

    class MPTTMeta:
        # For legacy reasons the 'variant_of' field is used to indicate the MPTT parent
        parent_attr = 'variant_of'

    def save(self, *args, **kwargs):
        """
        Overrides the save() function for the Part model.
        If the part image has been updated,
        then check if the "old" (previous) image is still used by another part.
        If not, it is considered "orphaned" and will be deleted.
        """

        if self.pk:
            previous = Part.objects.get(pk=self.pk)

            if previous.image and not self.image == previous.image:
                # Are there any (other) parts which reference the image?
                n_refs = Part.objects.filter(image=previous.image).exclude(pk=self.pk).count()

                if n_refs == 0:
                    previous.image.delete(save=False)

        self.clean()
        self.validate_unique()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.description}"

    def checkAddToBOM(self, parent):
        """
        Check if this Part can be added to the BOM of another part.

        This will fail if:

        a) The parent part is the same as this one
        b) The parent part is used in the BOM for *this* part
        c) The parent part is used in the BOM for any child parts under this one
        
        Failing this check raises a ValidationError!

        """

        if parent is None:
            return

        if self.pk == parent.pk:
            raise ValidationError({'sub_part': _("Part '{p1}' is  used in BOM for '{p2}' (recursive)".format(
                p1=str(self),
                p2=str(parent)
            ))})

        # Ensure that the parent part does not appear under any child BOM item!
        for item in self.bom_items.all():

            # Check for simple match
            if item.sub_part == parent:
                raise ValidationError({'sub_part': _("Part '{p1}' is  used in BOM for '{p2}' (recursive)".format(
                    p1=str(parent),
                    p2=str(self)
                ))})

            # And recursively check too
            item.sub_part.checkAddToBOM(parent)

    def checkIfSerialNumberExists(self, sn):
        """
        Check if a serial number exists for this Part.

        Note: Serial numbers must be unique across an entire Part "tree",
        so here we filter by the entire tree.
        """

        parts = Part.objects.filter(tree_id=self.tree_id)
        stock = StockModels.StockItem.objects.filter(part__in=parts, serial=sn)

        return stock.exists()

    def getLatestSerialNumber(self):
        """
        Return the "latest" serial number for this Part.

        If *all* the serial numbers are integers, then this will return the highest one.
        Otherwise, it will simply return the serial number most recently added.

        Note: Serial numbers must be unique across an entire Part "tree",
        so we filter by the entire tree.
        """

        parts = Part.objects.filter(tree_id=self.tree_id)
        stock = StockModels.StockItem.objects.filter(part__in=parts).exclude(serial=None)
        
        # There are no matchin StockItem objects (skip further tests)
        if not stock.exists():
            return None

        # Attempt to coerce the returned serial numbers to integers
        # If *any* are not integers, fail!
        try:
            ordered = sorted(stock.all(), reverse=True, key=lambda n: int(n.serial))

            if len(ordered) > 0:
                return ordered[0].serial

        # One or more of the serial numbers was non-numeric
        # In this case, the "best" we can do is return the most recent
        except ValueError:
            return stock.last().serial

        # No serial numbers found
        return None

    def getSerialNumberString(self, quantity=1):
        """
        Return a formatted string representing the next available serial numbers,
        given a certain quantity of items.
        """

        latest = self.getLatestSerialNumber()

        quantity = int(quantity)

        # No serial numbers can be found, assume 1 as the first serial
        if latest is None:
            latest = 0

        # Attempt to turn into an integer
        try:
            latest = int(latest)
        except:
            pass

        if type(latest) is int:

            if quantity >= 2:
                text = '{n} - {m}'.format(n=latest + 1, m=latest + 1 + quantity)

                return _('Next available serial numbers are') + ' ' + text
            else:
                text = str(latest)

                return _('Next available serial number is') + ' ' + text

        else:
            # Non-integer values, no option but to return latest

            return _('Most recent serial number is') + ' ' + str(latest)

    @property
    def full_name(self):
        """ Format a 'full name' for this Part.

        - IPN (if not null)
        - Part name
        - Part variant (if not null)

        Elements are joined by the | character
        """

        elements = []

        if self.IPN:
            elements.append(self.IPN)
        
        elements.append(self.name)

        if self.revision:
            elements.append(self.revision)

        return ' | '.join(elements)

    def set_category(self, category):

        # Ignore if the category is already the same
        if self.category == category:
            return

        self.category = category
        self.save()

    def get_absolute_url(self):
        """ Return the web URL for viewing this part """
        return reverse('part-detail', kwargs={'pk': self.id})

    def get_image_url(self):
        """ Return the URL of the image for this part """

        if self.image:
            return helpers.getMediaUrl(self.image.url)
        else:
            return helpers.getBlankImage()

    def get_thumbnail_url(self):
        """
        Return the URL of the image thumbnail for this part
        """

        if self.image:
            return helpers.getMediaUrl(self.image.thumbnail.url)
        else:
            return helpers.getBlankThumbnail()

    def validate_unique(self, exclude=None):
        """ Validate that a part is 'unique'.
        Uniqueness is checked across the following (case insensitive) fields:

        * Name
        * IPN
        * Revision

        e.g. there can exist multiple parts with the same name, but only if
        they have a different revision or internal part number.

        """
        super().validate_unique(exclude)

        # Part name uniqueness should be case insensitive
        try:
            parts = Part.objects.exclude(id=self.id).filter(
                name__iexact=self.name,
                IPN__iexact=self.IPN,
                revision__iexact=self.revision)

            if parts.exists():
                msg = _("Part must be unique for name, IPN and revision")
                raise ValidationError({
                    "name": msg,
                    "IPN": msg,
                    "revision": msg,
                })
        except Part.DoesNotExist:
            pass

    def clean(self):
        """ Perform cleaning operations for the Part model """

        super().clean()

    name = models.CharField(max_length=100, blank=False,
                            help_text=_('Part name'),
                            validators=[validators.validate_part_name]
                            )

    is_template = models.BooleanField(default=False, help_text=_('Is this part a template part?'))

    variant_of = models.ForeignKey('part.Part', related_name='variants',
                                   null=True, blank=True,
                                   limit_choices_to={
                                       'is_template': True,
                                       'active': True,
                                   },
                                   on_delete=models.SET_NULL,
                                   help_text=_('Is this part a variant of another part?'))

    description = models.CharField(max_length=250, blank=False, help_text=_('Part description'))

    keywords = models.CharField(max_length=250, blank=True, null=True, help_text=_('Part keywords to improve visibility in search results'))

    category = TreeForeignKey(PartCategory, related_name='parts',
                              null=True, blank=True,
                              on_delete=models.DO_NOTHING,
                              help_text=_('Part category'))

    IPN = models.CharField(max_length=100, blank=True, null=True, help_text=_('Internal Part Number'), validators=[validators.validate_part_ipn])

    revision = models.CharField(max_length=100, blank=True, null=True, help_text=_('Part revision or version number'))

    link = InvenTreeURLField(blank=True, null=True, help_text=_('Link to extenal URL'))

    image = StdImageField(
        upload_to=rename_part_image,
        null=True,
        blank=True,
        variations={'thumbnail': (128, 128)},
        delete_orphans=True,
    )

    default_location = TreeForeignKey('stock.StockLocation', on_delete=models.SET_NULL,
                                      blank=True, null=True,
                                      help_text=_('Where is this item normally stored?'),
                                      related_name='default_parts')

    def get_default_location(self):
        """ Get the default location for a Part (may be None).

        If the Part does not specify a default location,
        look at the Category this part is in.
        The PartCategory object may also specify a default stock location
        """

        if self.default_location:
            return self.default_location
        elif self.category:
            # Traverse up the category tree until we find a default location
            cats = self.category.get_ancestors(ascending=True, include_self=True)

            for cat in cats:
                if cat.default_location:
                    return cat.default_location

        # Default case - no default category found
        return None

    def get_default_supplier(self):
        """ Get the default supplier part for this part (may be None).

        - If the part specifies a default_supplier, return that
        - If there is only one supplier part available, return that
        - Else, return None
        """

        if self.default_supplier:
            return self.default_supplier

        if self.supplier_count == 1:
            return self.supplier_parts.first()

        # Default to None if there are multiple suppliers to choose from
        return None

    default_supplier = models.ForeignKey(SupplierPart,
                                         on_delete=models.SET_NULL,
                                         blank=True, null=True,
                                         help_text=_('Default supplier part'),
                                         related_name='default_parts')

    minimum_stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], help_text=_('Minimum allowed stock level'))

    units = models.CharField(max_length=20, default="", blank=True, null=True, help_text=_('Stock keeping units for this part'))

    assembly = models.BooleanField(default=False, verbose_name='Assembly', help_text=_('Can this part be built from other parts?'))

    component = models.BooleanField(default=True, verbose_name='Component', help_text=_('Can this part be used to build other parts?'))

    trackable = models.BooleanField(default=False, help_text=_('Does this part have tracking for unique items?'))

    purchaseable = models.BooleanField(default=True, help_text=_('Can this part be purchased from external suppliers?'))

    salable = models.BooleanField(default=False, help_text=_("Can this part be sold to customers?"))

    active = models.BooleanField(default=True, help_text=_('Is this part active?'))

    virtual = models.BooleanField(default=False, help_text=_('Is this a virtual part, such as a software product or license?'))

    notes = MarkdownxField(blank=True, null=True, help_text=_('Part notes - supports Markdown formatting'))

    bom_checksum = models.CharField(max_length=128, blank=True, help_text=_('Stored BOM checksum'))

    bom_checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                       related_name='boms_checked')

    bom_checked_date = models.DateField(blank=True, null=True)

    creation_date = models.DateField(auto_now_add=True, editable=False, blank=True, null=True)

    creation_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='parts_created')

    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='parts_responible')

    def format_barcode(self, **kwargs):
        """ Return a JSON string for formatting a barcode for this Part object """

        return helpers.MakeBarcode(
            "part",
            self.id,
            {
                "name": self.full_name,
                "url": reverse('api-part-detail', kwargs={'pk': self.id}),
            },
            **kwargs
        )

    @property
    def category_path(self):
        if self.category:
            return self.category.pathstring
        return ''

    @property
    def available_stock(self):
        """
        Return the total available stock.

        - This subtracts stock which is already allocated to builds
        """

        total = self.total_stock
        total -= self.allocation_count()

        return max(total, 0)

    @property
    def quantity_to_order(self):
        """ Return the quantity needing to be ordered for this part. """

        # How many do we need to have "on hand" at any point?
        required = self.net_stock - self.minimum_stock

        if required < 0:
            return abs(required)

        # Do not need to order any
        return 0

        required = self.net_stock
        return max(required, 0)

    @property
    def net_stock(self):
        """ Return the 'net' stock. It takes into account:

        - Stock on hand (total_stock)
        - Stock on order (on_order)
        - Stock allocated (allocation_count)

        This number (unlike 'available_stock') can be negative.
        """

        return self.total_stock - self.allocation_count() + self.on_order

    def isStarredBy(self, user):
        """ Return True if this part has been starred by a particular user """

        try:
            PartStar.objects.get(part=self, user=user)
            return True
        except PartStar.DoesNotExist:
            return False

    def need_to_restock(self):
        """ Return True if this part needs to be restocked
        (either by purchasing or building).

        If the allocated_stock exceeds the total_stock,
        then we need to restock.
        """

        return (self.total_stock + self.on_order - self.allocation_count) < self.minimum_stock

    @property
    def can_build(self):
        """ Return the number of units that can be build with available stock
        """

        # If this part does NOT have a BOM, result is simply the currently available stock
        if not self.has_bom:
            return 0

        total = None

        # Calculate the minimum number of parts that can be built using each sub-part
        for item in self.bom_items.all().prefetch_related('sub_part__stock_items'):
            stock = item.sub_part.available_stock

            # If (by some chance) we get here but the BOM item quantity is invalid,
            # ignore!
            if item.quantity <= 0:
                continue

            n = int(stock / item.quantity)

            if total is None or n < total:
                total = n

        if total is None:
            total = 0
        
        return max(total, 0)

    @property
    def active_builds(self):
        """ Return a list of outstanding builds.
        Builds marked as 'complete' or 'cancelled' are ignored
        """

        return self.builds.filter(status__in=BuildStatus.ACTIVE_CODES)

    @property
    def inactive_builds(self):
        """ Return a list of inactive builds
        """

        return self.builds.exclude(status__in=BuildStatus.ACTIVE_CODES)

    @property
    def quantity_being_built(self):
        """ Return the current number of parts currently being built
        """

        quantity = self.active_builds.aggregate(quantity=Sum('quantity'))['quantity']

        if quantity is None:
            quantity = 0

        return quantity

    def build_order_allocations(self):
        """
        Return all 'BuildItem' objects which allocate this part to Build objects
        """

        return BuildModels.BuildItem.objects.filter(stock_item__part__id=self.id)

    def build_order_allocation_count(self):
        """
        Return the total amount of this part allocated to build orders
        """

        query = self.build_order_allocations().aggregate(total=Coalesce(Sum('quantity'), 0))

        return query['total']

    def sales_order_allocations(self):
        """
        Return all sales-order-allocation objects which allocate this part to a SalesOrder
        """

        return OrderModels.SalesOrderAllocation.objects.filter(item__part__id=self.id)

    def sales_order_allocation_count(self):
        """
        Return the tutal quantity of this part allocated to sales orders
        """

        query = self.sales_order_allocations().aggregate(total=Coalesce(Sum('quantity'), 0))

        return query['total']

    def allocation_count(self):
        """
        Return the total quantity of stock allocated for this part,
        against both build orders and sales orders.
        """

        return sum([
            self.build_order_allocation_count(),
            self.sales_order_allocation_count(),
        ])

    def stock_entries(self, include_variants=True, in_stock=None):
        """ Return all stock entries for this Part.

        - If this is a template part, include variants underneath this.

        Note: To return all stock-entries for all part variants under this one,
        we need to be creative with the filtering.
        """

        if include_variants:
            query = StockModels.StockItem.objects.filter(part__in=self.get_descendants(include_self=True))
        else:
            query = self.stock_items

        if in_stock is True:
            query = query.filter(StockModels.StockItem.IN_STOCK_FILTER)
        elif in_stock is False:
            query = query.exclude(StockModels.StockItem.IN_STOCK_FILTER)

        return query

    @property
    def total_stock(self):
        """ Return the total stock quantity for this part.
        
        - Part may be stored in multiple locations
        - If this part is a "template" (variants exist) then these are counted too
        """

        entries = self.stock_entries(in_stock=True)

        query = entries.aggregate(t=Coalesce(Sum('quantity'), Decimal(0)))

        return query['t']

    @property
    def has_bom(self):
        return self.bom_count > 0

    @property
    def bom_count(self):
        """ Return the number of items contained in the BOM for this part """
        return self.bom_items.count()

    @property
    def used_in_count(self):
        """ Return the number of part BOMs that this part appears in """
        return self.used_in.count()

    def get_bom_hash(self):
        """ Return a checksum hash for the BOM for this part.
        Used to determine if the BOM has changed (and needs to be signed off!)

        The hash is calculated by hashing each line item in the BOM.

        returns a string representation of a hash object which can be compared with a stored value
        """

        hash = hashlib.md5(str(self.id).encode())

        for item in self.bom_items.all().prefetch_related('sub_part'):
            hash.update(str(item.get_item_hash()).encode())

        return str(hash.digest())

    def is_bom_valid(self):
        """ Check if the BOM is 'valid' - if the calculated checksum matches the stored value
        """

        return self.get_bom_hash() == self.bom_checksum

    @transaction.atomic
    def validate_bom(self, user):
        """ Validate the BOM (mark the BOM as validated by the given User.

        - Calculates and stores the hash for the BOM
        - Saves the current date and the checking user
        """

        # Validate each line item too
        for item in self.bom_items.all():
            item.validate_hash()

        self.bom_checksum = self.get_bom_hash()
        self.bom_checked_by = user
        self.bom_checked_date = datetime.now().date()

        self.save()

    @transaction.atomic
    def clear_bom(self):
        """ Clear the BOM items for the part (delete all BOM lines).
        """

        self.bom_items.all().delete()

    def required_parts(self):
        """ Return a list of parts required to make this part (list of BOM items) """
        parts = []
        for bom in self.bom_items.all().select_related('sub_part'):
            parts.append(bom.sub_part)
        return parts

    def get_allowed_bom_items(self):
        """ Return a list of parts which can be added to a BOM for this part.

        - Exclude parts which are not 'component' parts
        - Exclude parts which this part is in the BOM for
        """

        parts = Part.objects.filter(component=True).exclude(id=self.id)
        parts = parts.exclude(id__in=[part.id for part in self.used_in.all()])

        return parts

    @property
    def supplier_count(self):
        """ Return the number of supplier parts available for this part """
        return self.supplier_parts.count()

    @property
    def has_pricing_info(self):
        """ Return true if there is pricing information for this part """
        return self.get_price_range() is not None

    @property
    def has_complete_bom_pricing(self):
        """ Return true if there is pricing information for each item in the BOM. """

        for item in self.bom_items.all().select_related('sub_part'):
            if not item.sub_part.has_pricing_info:
                return False

        return True

    def get_price_info(self, quantity=1, buy=True, bom=True):
        """ Return a simplified pricing string for this part
        
        Args:
            quantity: Number of units to calculate price for
            buy: Include supplier pricing (default = True)
            bom: Include BOM pricing (default = True)
        """

        price_range = self.get_price_range(quantity, buy, bom)

        if price_range is None:
            return None

        min_price, max_price = price_range

        if min_price == max_price:
            return min_price

        min_price = normalize(min_price)
        max_price = normalize(max_price)

        return "{a} - {b}".format(a=min_price, b=max_price)

    def get_supplier_price_range(self, quantity=1):
        
        min_price = None
        max_price = None

        for supplier in self.supplier_parts.all():

            price = supplier.get_price(quantity)

            if price is None:
                continue

            if min_price is None or price < min_price:
                min_price = price

            if max_price is None or price > max_price:
                max_price = price

        if min_price is None or max_price is None:
            return None

        min_price = normalize(min_price)
        max_price = normalize(max_price)

        return (min_price, max_price)

    def get_bom_price_range(self, quantity=1):
        """ Return the price range of the BOM for this part.
        Adds the minimum price for all components in the BOM.

        Note: If the BOM contains items without pricing information,
        these items cannot be included in the BOM!
        """

        min_price = None
        max_price = None

        for item in self.bom_items.all().select_related('sub_part'):

            if item.sub_part.pk == self.pk:
                print("Warning: Item contains itself in BOM")
                continue

            prices = item.sub_part.get_price_range(quantity * item.quantity)

            if prices is None:
                continue

            low, high = prices

            if min_price is None:
                min_price = 0

            if max_price is None:
                max_price = 0

            min_price += low
            max_price += high

        if min_price is None or max_price is None:
            return None

        min_price = normalize(min_price)
        max_price = normalize(max_price)

        return (min_price, max_price)

    def get_price_range(self, quantity=1, buy=True, bom=True):
        
        """ Return the price range for this part. This price can be either:

        - Supplier price (if purchased from suppliers)
        - BOM price (if built from other parts)

        Returns:
            Minimum of the supplier price or BOM price. If no pricing available, returns None
        """

        buy_price_range = self.get_supplier_price_range(quantity) if buy else None
        bom_price_range = self.get_bom_price_range(quantity) if bom else None

        if buy_price_range is None:
            return bom_price_range

        elif bom_price_range is None:
            return buy_price_range

        else:
            return (
                min(buy_price_range[0], bom_price_range[0]),
                max(buy_price_range[1], bom_price_range[1])
            )

    def deepCopy(self, other, **kwargs):
        """ Duplicates non-field data from another part.
        Does not alter the normal fields of this part,
        but can be used to copy other data linked by ForeignKey refernce.

        Keyword Args:
            image: If True, copies Part image (default = True)
            bom: If True, copies BOM data (default = False)
            parameters: If True, copies Parameters data (default = True)
        """

        # Copy the part image
        if kwargs.get('image', True):
            if other.image:
                # Reference the other image from this Part
                self.image = other.image

        # Copy the BOM data
        if kwargs.get('bom', False):
            for item in other.bom_items.all():
                # Point the item to THIS part.
                # Set the pk to None so a new entry is created.
                item.part = self
                item.pk = None
                item.save()

        # Copy the parameters data
        if kwargs.get('parameters', True):
            # Get template part parameters
            parameters = other.get_parameters()
            # Copy template part parameters to new variant part
            for parameter in parameters:
                PartParameter.create(part=self,
                                     template=parameter.template,
                                     data=parameter.data,
                                     save=True)

        # Copy the fields that aren't available in the duplicate form
        self.salable = other.salable
        self.assembly = other.assembly
        self.component = other.component
        self.purchaseable = other.purchaseable
        self.trackable = other.trackable
        self.virtual = other.virtual

        self.save()

    def getTestTemplates(self, required=None, include_parent=True):
        """
        Return a list of all test templates associated with this Part.
        These are used for validation of a StockItem.

        args:
            required: Set to True or False to filter by "required" status
            include_parent: Set to True to traverse upwards
        """

        if include_parent:
            tests = PartTestTemplate.objects.filter(part__in=self.get_ancestors(include_self=True))
        else:
            tests = self.test_templates

        if required is not None:
            tests = tests.filter(required=required)

        return tests
    
    def getRequiredTests(self):
        # Return the tests which are required by this part
        return self.getTestTemplates(required=True)

    def requiredTestCount(self):
        return self.getRequiredTests().count()

    @property
    def attachment_count(self):
        """ Count the number of attachments for this part.
        If the part is a variant of a template part,
        include the number of attachments for the template part.

        """

        return self.part_attachments.count()

    @property
    def part_attachments(self):
        """
        Return *all* attachments for this part,
        potentially including attachments for template parts
        above this one.
        """

        ancestors = self.get_ancestors(include_self=True)

        attachments = PartAttachment.objects.filter(part__in=ancestors)

        return attachments

    def sales_orders(self):
        """ Return a list of sales orders which reference this part """

        orders = []

        for line in self.sales_order_line_items.all().prefetch_related('order'):
            if line.order not in orders:
                orders.append(line.order)

        return orders

    def purchase_orders(self):
        """ Return a list of purchase orders which reference this part """

        orders = []

        for part in self.supplier_parts.all().prefetch_related('purchase_order_line_items'):
            for order in part.purchase_orders():
                if order not in orders:
                    orders.append(order)

        return orders

    def open_purchase_orders(self):
        """ Return a list of open purchase orders against this part """

        return [order for order in self.purchase_orders() if order.status in PurchaseOrderStatus.OPEN]

    def closed_purchase_orders(self):
        """ Return a list of closed purchase orders against this part """

        return [order for order in self.purchase_orders() if order.status not in PurchaseOrderStatus.OPEN]

    @property
    def on_order(self):
        """ Return the total number of items on order for this part. """

        orders = self.supplier_parts.filter(purchase_order_line_items__order__status__in=PurchaseOrderStatus.OPEN).aggregate(
            quantity=Sum('purchase_order_line_items__quantity'),
            received=Sum('purchase_order_line_items__received')
        )

        quantity = orders['quantity']
        received = orders['received']

        if quantity is None:
            quantity = 0

        if received is None:
            received = 0

        return quantity - received

    def get_parameters(self):
        """ Return all parameters for this part, ordered by name """

        return self.parameters.order_by('template__name')

    @property
    def has_variants(self):
        """ Check if this Part object has variants underneath it. """

        return self.get_all_variants().count() > 0

    def get_all_variants(self):
        """ Return all Part object which exist as a variant under this part. """

        return self.get_descendants(include_self=False)


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


class PartAttachment(InvenTreeAttachment):
    """
    Model for storing file attachments against a Part object
    """
    
    def getSubdir(self):
        return os.path.join("part_files", str(self.part.id))

    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='attachments')


class PartSellPriceBreak(common.models.PriceBreak):
    """
    Represents a price break for selling this part
    """

    part = models.ForeignKey(
        Part, on_delete=models.CASCADE,
        related_name='salepricebreaks',
        limit_choices_to={'salable': True}
    )

    class Meta:
        unique_together = ('part', 'quantity')


class PartStar(models.Model):
    """ A PartStar object creates a relationship between a User and a Part.

    It is used to designate a Part as 'starred' (or favourited) for a given User,
    so that the user can track a list of their favourite parts.

    Attributes:
        part: Link to a Part object
        user: Link to a User object
    """

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='starred_users')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starred_parts')

    class Meta:
        unique_together = ['part', 'user']


class PartTestTemplate(models.Model):
    """
    A PartTestTemplate defines a 'template' for a test which is required to be run
    against a StockItem (an instance of the Part).

    The test template applies "recursively" to part variants, allowing tests to be
    defined in a heirarchy.

    Test names are simply strings, rather than enforcing any sort of structure or pattern.
    It is up to the user to determine what tests are defined (and how they are run).

    To enable generation of unique lookup-keys for each test, there are some validation tests
    run on the model (refer to the validate_unique function).
    """

    def save(self, *args, **kwargs):

        self.clean()

        super().save(*args, **kwargs)

    def clean(self):

        self.test_name = self.test_name.strip()

        self.validate_unique()
        super().clean()

    def validate_unique(self, exclude=None):
        """
        Test that this test template is 'unique' within this part tree.
        """

        if not self.part.trackable:
            raise ValidationError({
                'part': _('Test templates can only be created for trackable parts')
            })

        # Get a list of all tests "above" this one
        tests = PartTestTemplate.objects.filter(
            part__in=self.part.get_ancestors(include_self=True)
        )

        # If this item is already in the database, exclude it from comparison!
        if self.pk is not None:
            tests = tests.exclude(pk=self.pk)

        key = self.key

        for test in tests:
            if test.key == key:
                raise ValidationError({
                    'test_name': _("Test with this name already exists for this part")
                })

        super().validate_unique(exclude)

    @property
    def key(self):
        """ Generate a key for this test """
        return helpers.generateTestKey(self.test_name)

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='test_templates',
        limit_choices_to={'trackable': True},
    )

    test_name = models.CharField(
        blank=False, max_length=100,
        verbose_name=_("Test Name"),
        help_text=_("Enter a name for the test")
    )

    description = models.CharField(
        blank=False, null=True, max_length=100,
        verbose_name=_("Test Description"),
        help_text=_("Enter description for this test")
    )

    required = models.BooleanField(
        default=True,
        verbose_name=_("Required"),
        help_text=_("Is this test required to pass?")
    )

    requires_value = models.BooleanField(
        default=False,
        verbose_name=_("Requires Value"),
        help_text=_("Does this test require a value when adding a test result?")
    )

    requires_attachment = models.BooleanField(
        default=False,
        verbose_name=_("Requires Attachment"),
        help_text=_("Does this test require a file attachment when adding a test result?")
    )


class PartParameterTemplate(models.Model):
    """
    A PartParameterTemplate provides a template for key:value pairs for extra
    parameters fields/values to be added to a Part.
    This allows users to arbitrarily assign data fields to a Part
    beyond the built-in attributes.

    Attributes:
        name: The name (key) of the Parameter [string]
        units: The units of the Parameter [string]
    """

    def __str__(self):
        s = str(self.name)
        if self.units:
            s += " ({units})".format(units=self.units)
        return s

    def validate_unique(self, exclude=None):
        """ Ensure that PartParameterTemplates cannot be created with the same name.
        This test should be case-insensitive (which the unique caveat does not cover).
        """

        super().validate_unique(exclude)

        try:
            others = PartParameterTemplate.objects.filter(name__iexact=self.name).exclude(pk=self.pk)

            if others.exists():
                msg = _("Parameter template name must be unique")
                raise ValidationError({"name": msg})
        except PartParameterTemplate.DoesNotExist:
            pass

    name = models.CharField(max_length=100, help_text=_('Parameter Name'), unique=True)

    units = models.CharField(max_length=25, help_text=_('Parameter Units'), blank=True)


class PartParameter(models.Model):
    """
    A PartParameter is a specific instance of a PartParameterTemplate. It assigns a particular parameter <key:value> pair to a part.

    Attributes:
        part: Reference to a single Part object
        template: Reference to a single PartParameterTemplate object
        data: The data (value) of the Parameter [string]
    """

    def __str__(self):
        # String representation of a PartParameter (used in the admin interface)
        return "{part} : {param} = {data}{units}".format(
            part=str(self.part.full_name),
            param=str(self.template.name),
            data=str(self.data),
            units=str(self.template.units)
        )

    class Meta:
        # Prevent multiple instances of a parameter for a single part
        unique_together = ('part', 'template')

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='parameters', help_text=_('Parent Part'))

    template = models.ForeignKey(PartParameterTemplate, on_delete=models.CASCADE, related_name='instances', help_text=_('Parameter Template'))

    data = models.CharField(max_length=500, help_text=_('Parameter Value'))

    @classmethod
    def create(cls, part, template, data, save=False):
        part_parameter = cls(part=part, template=template, data=data)
        if save:
            part_parameter.save()
        return part_parameter


class BomItem(models.Model):
    """ A BomItem links a part to its component items.
    A part can have a BOM (bill of materials) which defines
    which parts are required (and in what quantity) to make it.

    Attributes:
        part: Link to the parent part (the part that will be produced)
        sub_part: Link to the child part (the part that will be consumed)
        quantity: Number of 'sub_parts' consumed to produce one 'part'
        reference: BOM reference field (e.g. part designators)
        overage: Estimated losses for a Build. Can be expressed as absolute value (e.g. '7') or a percentage (e.g. '2%')
        note: Note field for this BOM item
        checksum: Validation checksum for the particular BOM line item
    """

    def save(self, *args, **kwargs):

        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('bom-item-detail', kwargs={'pk': self.id})

    # A link to the parent part
    # Each part will get a reverse lookup field 'bom_items'
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='bom_items',
                             help_text=_('Select parent part'),
                             limit_choices_to={
                                 'assembly': True,
                             })

    # A link to the child item (sub-part)
    # Each part will get a reverse lookup field 'used_in'
    sub_part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='used_in',
                                 help_text=_('Select part to be used in BOM'),
                                 limit_choices_to={
                                     'component': True,
                                 })

    # Quantity required
    quantity = models.DecimalField(default=1.0, max_digits=15, decimal_places=5, validators=[MinValueValidator(0)], help_text=_('BOM quantity for this BOM item'))

    overage = models.CharField(max_length=24, blank=True, validators=[validators.validate_overage],
                               help_text=_('Estimated build wastage quantity (absolute or percentage)')
                               )

    reference = models.CharField(max_length=500, blank=True, help_text=_('BOM item reference'))

    # Note attached to this BOM line item
    note = models.CharField(max_length=500, blank=True, help_text=_('BOM item notes'))

    checksum = models.CharField(max_length=128, blank=True, help_text=_('BOM line checksum'))

    def get_item_hash(self):
        """ Calculate the checksum hash of this BOM line item:

        The hash is calculated from the following fields:

        - Part.full_name (if the part name changes, the BOM checksum is invalidated)
        - Quantity
        - Reference field
        - Note field

        """

        # Seed the hash with the ID of this BOM item
        hash = hashlib.md5(str(self.id).encode())

        # Update the hash based on line information
        hash.update(str(self.sub_part.id).encode())
        hash.update(str(self.sub_part.full_name).encode())
        hash.update(str(self.quantity).encode())
        hash.update(str(self.note).encode())
        hash.update(str(self.reference).encode())

        return str(hash.digest())

    def validate_hash(self, valid=True):
        """ Mark this item as 'valid' (store the checksum hash).
        
        Args:
            valid: If true, validate the hash, otherwise invalidate it (default = True)
        """

        if valid:
            self.checksum = str(self.get_item_hash())
        else:
            self.checksum = ''

        self.save()

    @property
    def is_line_valid(self):
        """ Check if this line item has been validated by the user """

        # Ensure an empty checksum returns False
        if len(self.checksum) == 0:
            return False

        return self.get_item_hash() == self.checksum

    def clean(self):
        """ Check validity of the BomItem model.

        Performs model checks beyond simple field validation.

        - A part cannot refer to itself in its BOM
        - A part cannot refer to a part which refers to it
        """

        # If the sub_part is 'trackable' then the 'quantity' field must be an integer
        try:
            if self.sub_part.trackable:
                if not self.quantity == int(self.quantity):
                    raise ValidationError({
                        "quantity": _("Quantity must be integer value for trackable parts")
                    })
        except Part.DoesNotExist:
            pass

        # Check for circular BOM references
        self.sub_part.checkAddToBOM(self.part)

    class Meta:
        verbose_name = _("BOM Item")

        # Prevent duplication of parent/child rows
        unique_together = ('part', 'sub_part')

    def __str__(self):
        return "{n} x {child} to make {parent}".format(
            parent=self.part.full_name,
            child=self.sub_part.full_name,
            n=helpers.decimal2string(self.quantity))

    def available_stock(self):
        """
        Return the available stock items for the referenced sub_part
        """

        query = self.sub_part.stock_items.filter(StockModels.StockItem.IN_STOCK_FILTER).aggregate(
            available=Coalesce(Sum('quantity'), 0)
        )

        return query['available']

    def get_overage_quantity(self, quantity):
        """ Calculate overage quantity
        """

        # Most of the time overage string will be empty
        if len(self.overage) == 0:
            return 0

        overage = str(self.overage).strip()

        # Is the overage a numerical value?
        try:
            ovg = float(overage)

            if ovg < 0:
                ovg = 0

            return ovg
        except ValueError:
            pass

        # Is the overage a percentage?
        if overage.endswith('%'):
            overage = overage[:-1].strip()

            try:
                percent = float(overage) / 100.0
                if percent > 1:
                    percent = 1
                if percent < 0:
                    percent = 0

                # Must be represented as a decimal
                percent = Decimal(percent)

                return float(percent * quantity)

            except ValueError:
                pass

        # Default = No overage
        return 0

    def get_required_quantity(self, build_quantity):
        """ Calculate the required part quantity, based on the supplier build_quantity.
        Includes overage estimate in the returned value.
        
        Args:
            build_quantity: Number of parts to build

        Returns:
            Quantity required for this build (including overage)
        """

        # Base quantity requirement
        base_quantity = self.quantity * build_quantity

        # Overage requiremet
        ovrg_quantity = self.get_overage_quantity(base_quantity)

        required = float(base_quantity) + float(ovrg_quantity)

        return required

    @property
    def price_range(self):
        """ Return the price-range for this BOM item. """

        prange = self.sub_part.get_price_range(self.quantity)

        if prange is None:
            return prange

        pmin, pmax = prange

        if pmin == pmax:
            return decimal2string(pmin)

        # Convert to better string representation
        pmin = decimal2string(pmin)
        pmax = decimal2string(pmax)

        return "{pmin} to {pmax}".format(pmin=pmin, pmax=pmax)
