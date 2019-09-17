"""
Part database model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.conf import settings

from django.core.files.base import ContentFile
from django.db import models, transaction
from django.db.models import Sum
from django.db.models import prefetch_related_objects
from django.core.validators import MinValueValidator

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from mptt.models import TreeForeignKey

from datetime import datetime
from fuzzywuzzy import fuzz
import hashlib

from InvenTree import helpers
from InvenTree import validators
from InvenTree.models import InvenTreeTree
from InvenTree.fields import InvenTreeURLField

from InvenTree.status_codes import BuildStatus, StockStatus, OrderStatus

from company.models import SupplierPart


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
        help_text='Default location for parts in this category'
    )

    default_keywords = models.CharField(blank=True, max_length=250, help_text='Default keywords for parts in this category')

    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'pk': self.id})

    class Meta:
        verbose_name = "Part Category"
        verbose_name_plural = "Part Categories"

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

    if filename.count('.') > 0:
        ext = filename.split('.')[-1]
    else:
        ext = ''

    fn = 'part_{pk}_img'.format(pk=instance.pk)

    if ext:
        fn += '.' + ext

    return os.path.join(base, fn)


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


class Part(models.Model):
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
        URL: Link to an external page with more information about this part (e.g. internal Wiki)
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
    """

    class Meta:
        verbose_name = "Part"
        verbose_name_plural = "Parts"

    def __str__(self):
        return "{n} - {d}".format(n=self.full_name, d=self.description)

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
            return os.path.join(settings.MEDIA_URL, str(self.image.url))
        else:
            return static('/img/blank_image.png')

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

        if self.is_template and self.variant_of is not None:
            raise ValidationError({
                'is_template': _("Part cannot be a template part if it is a variant of another part"),
                'variant_of': _("Part cannot be a variant of another part if it is already a template"),
            })

    name = models.CharField(max_length=100, blank=False,
                            help_text='Part name',
                            validators=[validators.validate_part_name]
                            )

    is_template = models.BooleanField(default=False, help_text='Is this part a template part?')

    variant_of = models.ForeignKey('part.Part', related_name='variants',
                                   null=True, blank=True,
                                   limit_choices_to={
                                       'is_template': True,
                                       'active': True,
                                   },
                                   on_delete=models.SET_NULL,
                                   help_text='Is this part a variant of another part?')

    description = models.CharField(max_length=250, blank=False, help_text='Part description')

    keywords = models.CharField(max_length=250, blank=True, help_text='Part keywords to improve visibility in search results')

    category = TreeForeignKey(PartCategory, related_name='parts',
                              null=True, blank=True,
                              on_delete=models.DO_NOTHING,
                              help_text='Part category')

    IPN = models.CharField(max_length=100, blank=True, help_text='Internal Part Number')

    revision = models.CharField(max_length=100, blank=True, help_text='Part revision or version number')

    URL = InvenTreeURLField(blank=True, help_text='Link to extenal URL')

    image = models.ImageField(upload_to=rename_part_image, max_length=255, null=True, blank=True)

    default_location = TreeForeignKey('stock.StockLocation', on_delete=models.SET_NULL,
                                      blank=True, null=True,
                                      help_text='Where is this item normally stored?',
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
                                         help_text='Default supplier part',
                                         related_name='default_parts')

    minimum_stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], help_text='Minimum allowed stock level')

    units = models.CharField(max_length=20, default="pcs", blank=True, help_text='Stock keeping units for this part')

    assembly = models.BooleanField(default=False, verbose_name='Assembly', help_text='Can this part be built from other parts?')

    component = models.BooleanField(default=True, verbose_name='Component', help_text='Can this part be used to build other parts?')

    trackable = models.BooleanField(default=False, help_text='Does this part have tracking for unique items?')

    purchaseable = models.BooleanField(default=True, help_text='Can this part be purchased from external suppliers?')

    salable = models.BooleanField(default=False, help_text="Can this part be sold to customers?")

    active = models.BooleanField(default=True, help_text='Is this part active?')

    virtual = models.BooleanField(default=False, help_text='Is this a virtual part, such as a software product or license?')

    notes = models.TextField(blank=True)

    bom_checksum = models.CharField(max_length=128, blank=True, help_text='Stored BOM checksum')

    bom_checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                       related_name='boms_checked')

    bom_checked_date = models.DateField(blank=True, null=True)

    def format_barcode(self):
        """ Return a JSON string for formatting a barcode for this Part object """

        return helpers.MakeBarcode(
            "Part",
            self.id,
            reverse('api-part-detail', kwargs={'pk': self.id}),
            {
                'name': self.name,
            }
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

        total -= self.allocation_count

        return max(total, 0)

    @property
    def quantity_to_order(self):
        """ Return the quantity needing to be ordered for this part. """

        required = -1 * self.net_stock
        return max(required, 0)

    @property
    def net_stock(self):
        """ Return the 'net' stock. It takes into account:

        - Stock on hand (total_stock)
        - Stock on order (on_order)
        - Stock allocated (allocation_count)

        This number (unlike 'available_stock') can be negative.
        """

        return self.total_stock - self.allocation_count + self.on_order

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
            n = int(1.0 * stock / item.quantity)

            if total is None or n < total:
                total = n

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

        return sum([b.quantity for b in self.active_builds])

    @property
    def build_allocation(self):
        """ Return list of builds to which this part is allocated
        """

        builds = []

        for item in self.used_in.all().prefetch_related('part__builds'):

            active = item.part.active_builds
            
            for build in active:
                b = {}

                b['build'] = build
                b['quantity'] = item.quantity * build.quantity

                builds.append(b)

        prefetch_related_objects(builds, 'build_items')

        return builds

    @property
    def allocated_build_count(self):
        """ Return the total number of this part that are allocated for builds
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
        """ Return all 'in stock' items. To be in stock:

        - customer is None
        - belongs_to is None
        """

        return self.stock_items.filter(customer=None, belongs_to=None)

    @property
    def total_stock(self):
        """ Return the total stock quantity for this part.
        Part may be stored in multiple locations
        """

        if self.is_template:
            total = sum([variant.total_stock for variant in self.variants.all()])
        else:
            total = self.stock_entries.filter(status__in=StockStatus.AVAILABLE_CODES).aggregate(total=Sum('quantity'))['total']

        if total:
            return total
        else:
            return 0

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

    @property
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
        """

        # Copy the part image
        if kwargs.get('image', True):
            if other.image:
                image_file = ContentFile(other.image.read())
                image_file.name = rename_part_image(self, other.image.url)

                self.image = image_file

        # Copy the BOM data
        if kwargs.get('bom', False):
            for item in other.bom_items.all():
                # Point the item to THIS part.
                # Set the pk to None so a new entry is created.
                item.part = self
                item.pk = None
                item.save()

        # Copy the fields that aren't available in the duplicate form
        self.salable = other.salable
        self.assembly = other.assembly
        self.component = other.component
        self.purchaseable = other.purchaseable
        self.trackable = other.trackable
        self.virtual = other.virtual

        self.save()

    @property
    def attachment_count(self):
        """ Count the number of attachments for this part.
        If the part is a variant of a template part,
        include the number of attachments for the template part.

        """

        n = self.attachments.count()

        if self.variant_of:
            n += self.variant_of.attachments.count()

        return n

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

        return [order for order in self.purchase_orders() if order.status in OrderStatus.OPEN]

    def closed_purchase_orders(self):
        """ Return a list of closed purchase orders against this part """

        return [order for order in self.purchase_orders() if order.status not in OrderStatus.OPEN]

    @property
    def on_order(self):
        """ Return the total number of items on order for this part. """

        return sum([part.on_order() for part in self.supplier_parts.all().prefetch_related('purchase_order_line_items')])

    def get_parameters(self):
        """ Return all parameters for this part, ordered by name """

        return self.parameters.order_by('template__name')


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

    Attributes:
        part: Link to a Part object
        attachment: File
        comment: String descriptor for the attachment
    """

    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='attachments')

    attachment = models.FileField(upload_to=attach_file,
                                  help_text='Select file to attach')

    comment = models.CharField(max_length=100, help_text='File comment')

    @property
    def basename(self):
        return os.path.basename(self.attachment.name)


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

    name = models.CharField(max_length=100, help_text='Parameter Name', unique=True)

    units = models.CharField(max_length=25, help_text='Parameter Units', blank=True)


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

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='parameters', help_text='Parent Part')

    template = models.ForeignKey(PartParameterTemplate, on_delete=models.CASCADE, related_name='instances', help_text='Parameter Template')

    data = models.CharField(max_length=500, help_text='Parameter Value')


class BomItem(models.Model):
    """ A BomItem links a part to its component items.
    A part can have a BOM (bill of materials) which defines
    which parts are required (and in what quatity) to make it.

    Attributes:
        part: Link to the parent part (the part that will be produced)
        sub_part: Link to the child part (the part that will be consumed)
        quantity: Number of 'sub_parts' consumed to produce one 'part'
        reference: BOM reference field (e.g. part designators)
        overage: Estimated losses for a Build. Can be expressed as absolute value (e.g. '7') or a percentage (e.g. '2%')
        note: Note field for this BOM item
        checksum: Validation checksum for the particular BOM line item
    """

    def get_absolute_url(self):
        return reverse('bom-item-detail', kwargs={'pk': self.id})

    # A link to the parent part
    # Each part will get a reverse lookup field 'bom_items'
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='bom_items',
                             help_text='Select parent part',
                             limit_choices_to={
                                 'assembly': True,
                             })

    # A link to the child item (sub-part)
    # Each part will get a reverse lookup field 'used_in'
    sub_part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='used_in',
                                 help_text='Select part to be used in BOM',
                                 limit_choices_to={
                                     'component': True,
                                 })

    # Quantity required
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)], help_text='BOM quantity for this BOM item')

    overage = models.CharField(max_length=24, blank=True, validators=[validators.validate_overage],
                               help_text='Estimated build wastage quantity (absolute or percentage)'
                               )

    reference = models.CharField(max_length=500, blank=True, help_text='BOM item reference')

    # Note attached to this BOM line item
    note = models.CharField(max_length=500, blank=True, help_text='BOM item notes')

    checksum = models.CharField(max_length=128, blank=True, help_text='BOM line checksum')

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

        # A part cannot refer to itself in its BOM
        try:
            if self.sub_part is not None and self.part is not None:
                if self.part == self.sub_part:
                    raise ValidationError({'sub_part': _('Part cannot be added to its own Bill of Materials')})
        
            # TODO - Make sure that there is no recusion

            # Test for simple recursion
            for item in self.sub_part.bom_items.all():
                if self.part == item.sub_part:
                    raise ValidationError({'sub_part': _("Part '{p1}' is  used in BOM for '{p2}' (recursive)".format(p1=str(self.part), p2=str(self.sub_part)))})
        
        except Part.DoesNotExist:
            # A blank Part will be caught elsewhere
            pass

    class Meta:
        verbose_name = "BOM Item"

        # Prevent duplication of parent/child rows
        unique_together = ('part', 'sub_part')

    def __str__(self):
        return "{n} x {child} to make {parent}".format(
            parent=self.part.full_name,
            child=self.sub_part.full_name,
            n=self.quantity)

    def get_overage_quantity(self, quantity):
        """ Calculate overage quantity
        """

        # Most of the time overage string will be empty
        if len(self.overage) == 0:
            return 0

        overage = str(self.overage).strip()

        # Is the overage an integer value?
        try:
            ovg = int(overage)

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

                return int(percent * quantity)

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

        return base_quantity + self.get_overage_quantity(base_quantity)

    @property
    def price_range(self):
        """ Return the price-range for this BOM item. """

        prange = self.sub_part.get_price_range(self.quantity)

        if prange is None:
            return prange

        pmin, pmax = prange

        if pmin == pmax:
            return str(pmin)

        return "{pmin} to {pmax}".format(pmin=pmin, pmax=pmax)
