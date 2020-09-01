"""
Stock database model definitions
"""


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse

from django.db import models, transaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from markdownx.models import MarkdownxField

from mptt.models import MPTTModel, TreeForeignKey

from decimal import Decimal, InvalidOperation
from datetime import datetime
from InvenTree import helpers

from InvenTree.status_codes import StockStatus
from InvenTree.models import InvenTreeTree, InvenTreeAttachment
from InvenTree.fields import InvenTreeURLField

from company import models as CompanyModels
from part import models as PartModels


class StockLocation(InvenTreeTree):
    """ Organization tree for StockItem objects
    A "StockLocation" can be considered a warehouse, or storage location
    Stock locations can be heirarchical as required
    """

    def get_absolute_url(self):
        return reverse('stock-location-detail', kwargs={'pk': self.id})

    def format_barcode(self, **kwargs):
        """ Return a JSON string for formatting a barcode for this StockLocation object """

        return helpers.MakeBarcode(
            'stocklocation',
            self.pk,
            {
                "name": self.name,
                "url": reverse('api-location-detail', kwargs={'pk': self.id}),
            },
            **kwargs
        )

    def get_stock_items(self, cascade=True):
        """ Return a queryset for all stock items under this category.

        Args:
            cascade: If True, also look under sublocations (default = True)
        """

        if cascade:
            query = StockItem.objects.filter(location__in=self.getUniqueChildren(include_self=True))
        else:
            query = StockItem.objects.filter(location=self.pk)

        return query

    def stock_item_count(self, cascade=True):
        """ Return the number of StockItem objects which live in or under this category
        """

        return self.get_stock_items(cascade).count()

    def has_items(self, cascade=True):
        """ Return True if there are StockItems existing in this category.

        Args:
            cascade: If True, also search an sublocations (default = True)
        """
        return self.stock_item_count(cascade) > 0

    @property
    def item_count(self):
        """ Simply returns the number of stock items in this location.
        Required for tree view serializer.
        """
        return self.stock_item_count()


@receiver(pre_delete, sender=StockLocation, dispatch_uid='stocklocation_delete_log')
def before_delete_stock_location(sender, instance, using, **kwargs):

    # Update each part in the stock location
    for item in instance.stock_items.all():
        item.location = instance.parent
        item.save()

    # Update each child category
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()


class StockItem(MPTTModel):
    """
    A StockItem object represents a quantity of physical instances of a part.
    
    Attributes:
        parent: Link to another StockItem from which this StockItem was created
        uid: Field containing a unique-id which is mapped to a third-party identifier (e.g. a barcode)
        part: Link to the master abstract part that this StockItem is an instance of
        supplier_part: Link to a specific SupplierPart (optional)
        location: Where this StockItem is located
        quantity: Number of stocked units
        batch: Batch number for this StockItem
        serial: Unique serial number for this StockItem
        link: Optional URL to link to external resource
        updated: Date that this stock item was last updated (auto)
        stocktake_date: Date of last stocktake for this item
        stocktake_user: User that performed the most recent stocktake
        review_needed: Flag if StockItem needs review
        delete_on_deplete: If True, StockItem will be deleted when the stock level gets to zero
        status: Status of this StockItem (ref: InvenTree.status_codes.StockStatus)
        notes: Extra notes field
        build: Link to a Build (if this stock item was created from a build)
        purchase_order: Link to a PurchaseOrder (if this stock item was created from a PurchaseOrder)
        infinite: If True this StockItem can never be exhausted
        sales_order: Link to a SalesOrder object (if the StockItem has been assigned to a SalesOrder)
        build_order: Link to a BuildOrder object (if the StockItem has been assigned to a BuildOrder)
    """

    # A Query filter which will be re-used in multiple places to determine if a StockItem is actually "in stock"
    IN_STOCK_FILTER = Q(
        sales_order=None,
        build_order=None,
        belongs_to=None,
        customer=None,
        status__in=StockStatus.AVAILABLE_CODES
    )

    def save(self, *args, **kwargs):
        """
        Save this StockItem to the database. Performs a number of checks:

        - Unique serial number requirement
        - Adds a transaction note when the item is first created.
        """

        self.validate_unique()
        self.clean()

        if not self.pk:
            # StockItem has not yet been saved
            add_note = True
        else:
            # StockItem has already been saved
            add_note = False

        user = kwargs.pop('user', None)
        
        add_note = add_note and kwargs.pop('note', True)

        super(StockItem, self).save(*args, **kwargs)

        if add_note:
            # This StockItem is being saved for the first time
            self.addTransactionNote(
                'Created stock item',
                user,
                notes="Created new stock item for part '{p}'".format(p=str(self.part)),
                system=True
            )

    @property
    def status_label(self):

        return StockStatus.label(self.status)

    @property
    def serialized(self):
        """ Return True if this StockItem is serialized """
        return self.serial is not None and self.quantity == 1

    def validate_unique(self, exclude=None):
        """
        Test that this StockItem is "unique".
        If the StockItem is serialized, the same serial number.
        cannot exist for the same part (or part tree).
        """

        super(StockItem, self).validate_unique(exclude)

        if self.serial is not None:
            # Query to look for duplicate serial numbers
            parts = PartModels.Part.objects.filter(tree_id=self.part.tree_id)
            stock = StockItem.objects.filter(part__in=parts, serial=self.serial)

            # Exclude myself from the search
            if self.pk is not None:
                stock = stock.exclude(pk=self.pk)

            if stock.exists():
                raise ValidationError({"serial": _("StockItem with this serial number already exists")})

    def clean(self):
        """ Validate the StockItem object (separate to field validation)

        The following validation checks are performed:

        - The 'part' and 'supplier_part.part' fields cannot point to the same Part object
        - The 'part' does not belong to itself
        - Quantity must be 1 if the StockItem has a serial number
        """

        super().clean()

        try:
            if self.part.trackable:
                # Trackable parts must have integer values for quantity field!
                if not self.quantity == int(self.quantity):
                    raise ValidationError({
                        'quantity': _('Quantity must be integer value for trackable parts')
                    })
        except PartModels.Part.DoesNotExist:
            # For some reason the 'clean' process sometimes throws errors because self.part does not exist
            # It *seems* that this only occurs in unit testing, though.
            # Probably should investigate this at some point.
            pass

        if self.quantity < 0:
            raise ValidationError({
                'quantity': _('Quantity must be greater than zero')
            })

        # The 'supplier_part' field must point to the same part!
        try:
            if self.supplier_part is not None:
                if not self.supplier_part.part == self.part:
                    raise ValidationError({'supplier_part': _("Part type ('{pf}') must be {pe}").format(
                                           pf=str(self.supplier_part.part),
                                           pe=str(self.part))
                                           })

            if self.part is not None:
                # A part with a serial number MUST have the quantity set to 1
                if self.serial is not None:
                    if self.quantity > 1:
                        raise ValidationError({
                            'quantity': _('Quantity must be 1 for item with a serial number'),
                            'serial': _('Serial number cannot be set if quantity greater than 1')
                        })

                    if self.quantity == 0:
                        self.quantity = 1

                    elif self.quantity > 1:
                        raise ValidationError({
                            'quantity': _('Quantity must be 1 for item with a serial number')
                        })

                    # Serial numbered items cannot be deleted on depletion
                    self.delete_on_deplete = False

        except PartModels.Part.DoesNotExist:
            # This gets thrown if self.supplier_part is null
            # TODO - Find a test than can be perfomed...
            pass

        if self.belongs_to and self.belongs_to.pk == self.pk:
            raise ValidationError({
                'belongs_to': _('Item cannot belong to itself')
            })

    def get_absolute_url(self):
        return reverse('stock-item-detail', kwargs={'pk': self.id})

    def get_part_name(self):
        return self.part.full_name

    def format_barcode(self, **kwargs):
        """ Return a JSON string for formatting a barcode for this StockItem.
        Can be used to perform lookup of a stockitem using barcode

        Contains the following data:

        { type: 'StockItem', stock_id: <pk>, part_id: <part_pk> }

        Voltagile data (e.g. stock quantity) should be looked up using the InvenTree API (as it may change)
        """

        return helpers.MakeBarcode(
            "stockitem",
            self.id,
            {
                "url": reverse('api-stock-detail', kwargs={'pk': self.id}),
            },
            **kwargs
        )

    uid = models.CharField(blank=True, max_length=128, help_text=("Unique identifier field"))

    parent = TreeForeignKey(
        'self',
        verbose_name=_('Parent Stock Item'),
        on_delete=models.DO_NOTHING,
        blank=True, null=True,
        related_name='children'
    )

    part = models.ForeignKey(
        'part.Part', on_delete=models.CASCADE,
        verbose_name=_('Base Part'),
        related_name='stock_items', help_text=_('Base part'),
        limit_choices_to={
            'active': True,
            'virtual': False
        })

    supplier_part = models.ForeignKey(
        'company.SupplierPart', blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_('Supplier Part'),
        help_text=_('Select a matching supplier part for this stock item')
    )

    location = TreeForeignKey(
        StockLocation, on_delete=models.DO_NOTHING,
        verbose_name=_('Stock Location'),
        related_name='stock_items',
        blank=True, null=True,
        help_text=_('Where is this stock item located?')
    )

    belongs_to = models.ForeignKey(
        'self',
        verbose_name=_('Installed In'),
        on_delete=models.DO_NOTHING,
        related_name='owned_parts', blank=True, null=True,
        help_text=_('Is this item installed in another item?')
    )

    customer = models.ForeignKey(
        CompanyModels.Company,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'is_customer': True},
        related_name='assigned_stock',
        help_text=_("Customer"),
        verbose_name=_("Customer"),
    )

    serial = models.CharField(
        verbose_name=_('Serial Number'),
        max_length=100, blank=True, null=True,
        help_text=_('Serial number for this item')
    )
 
    link = InvenTreeURLField(
        verbose_name=_('External Link'),
        max_length=125, blank=True,
        help_text=_("Link to external URL")
    )

    batch = models.CharField(
        verbose_name=_('Batch Code'),
        max_length=100, blank=True, null=True,
        help_text=_('Batch code for this stock item')
    )

    quantity = models.DecimalField(
        verbose_name=_("Stock Quantity"),
        max_digits=15, decimal_places=5, validators=[MinValueValidator(0)],
        default=1
    )

    updated = models.DateField(auto_now=True, null=True)

    build = models.ForeignKey(
        'build.Build', on_delete=models.SET_NULL,
        verbose_name=_('Source Build'),
        blank=True, null=True,
        help_text=_('Build for this stock item'),
        related_name='build_outputs',
    )

    purchase_order = models.ForeignKey(
        'order.PurchaseOrder',
        on_delete=models.SET_NULL,
        verbose_name=_('Source Purchase Order'),
        related_name='stock_items',
        blank=True, null=True,
        help_text=_('Purchase order for this stock item')
    )

    sales_order = models.ForeignKey(
        'order.SalesOrder',
        on_delete=models.SET_NULL,
        verbose_name=_("Destination Sales Order"),
        related_name='stock_items',
        null=True, blank=True)

    build_order = models.ForeignKey(
        'build.Build',
        on_delete=models.SET_NULL,
        verbose_name=_("Destination Build Order"),
        related_name='stock_items',
        null=True, blank=True
    )

    # last time the stock was checked / counted
    stocktake_date = models.DateField(blank=True, null=True)

    stocktake_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                       related_name='stocktake_stock')

    review_needed = models.BooleanField(default=False)

    delete_on_deplete = models.BooleanField(default=True, help_text=_('Delete this Stock Item when stock is depleted'))

    status = models.PositiveIntegerField(
        default=StockStatus.OK,
        choices=StockStatus.items(),
        validators=[MinValueValidator(0)])

    notes = MarkdownxField(
        blank=True, null=True,
        verbose_name=_("Notes"),
        help_text=_('Stock Item Notes')
    )

    def clearAllocations(self):
        """
        Clear all order allocations for this StockItem:

        - SalesOrder allocations
        - Build allocations
        """

        # Delete outstanding SalesOrder allocations
        self.sales_order_allocations.all().delete()

        # Delete outstanding BuildOrder allocations
        self.allocations.all().delete()

    def allocateToCustomer(self, customer, quantity=None, order=None, user=None, notes=None):
        """
        Allocate a StockItem to a customer.

        This action can be called by the following processes:
        - Completion of a SalesOrder
        - User manually assigns a StockItem to the customer

        Args:
            customer: The customer (Company) to assign the stock to
            quantity: Quantity to assign (if not supplied, total quantity is used)
            order: SalesOrder reference
            user: User that performed the action
            notes: Notes field
        """

        if quantity is None:
            quantity = self.quantity

        if quantity >= self.quantity:
            item = self
        else:
            item = self.splitStock(quantity, None, user)

        # Update StockItem fields with new information
        item.sales_order = order
        item.customer = customer
        item.location = None

        item.save()

        # TODO - Remove any stock item allocations from this stock item

        item.addTransactionNote(
            _("Assigned to Customer"),
            user,
            notes=_("Manually assigned to customer") + " " + customer.name,
            system=True
        )

        # Return the reference to the stock item
        return item

    def returnFromCustomer(self, location, user=None):
        """
        Return stock item from customer, back into the specified location.
        """

        self.addTransactionNote(
            _("Returned from customer") + " " + self.customer.name,
            user,
            notes=_("Returned to location") + " " + location.name,
            system=True
        )

        self.customer = None
        self.location = location

        self.save()

    # If stock item is incoming, an (optional) ETA field
    # expected_arrival = models.DateField(null=True, blank=True)

    infinite = models.BooleanField(default=False)

    def is_allocated(self):
        """
        Return True if this StockItem is allocated to a SalesOrder or a Build
        """

        # TODO - For now this only checks if the StockItem is allocated to a SalesOrder
        # TODO - In future, once the "build" is working better, check this too

        if self.allocations.count() > 0:
            return True

        if self.sales_order_allocations.count() > 0:
            return True

        return False

    def build_allocation_count(self):
        """
        Return the total quantity allocated to builds
        """

        query = self.allocations.aggregate(q=Coalesce(Sum('quantity'), Decimal(0)))

        return query['q']

    def sales_order_allocation_count(self):
        """
        Return the total quantity allocated to SalesOrders
        """

        query = self.sales_order_allocations.aggregate(q=Coalesce(Sum('quantity'), Decimal(0)))

        return query['q']

    def allocation_count(self):
        """
        Return the total quantity allocated to builds or orders
        """

        return self.build_allocation_count() + self.sales_order_allocation_count()

    def unallocated_quantity(self):
        """
        Return the quantity of this StockItem which is *not* allocated
        """

        return max(self.quantity - self.allocation_count(), 0)

    def can_delete(self):
        """ Can this stock item be deleted? It can NOT be deleted under the following circumstances:

        - Has child StockItems
        - Has a serial number and is tracked
        - Is installed inside another StockItem
        - It has been assigned to a SalesOrder
        - It has been assigned to a BuildOrder
        """

        if self.child_count > 0:
            return False

        if self.part.trackable and self.serial is not None:
            return False

        if self.sales_order is not None:
            return False

        if self.build_order is not None:
            return False

        return True

    @property
    def children(self):
        """ Return a list of the child items which have been split from this stock item """
        return self.get_descendants(include_self=False)

    @property
    def child_count(self):
        """ Return the number of 'child' items associated with this StockItem.
        A child item is one which has been split from this one.
        """
        return self.children.count()

    @property
    def in_stock(self):

        # Not 'in stock' if it has been installed inside another StockItem
        if self.belongs_to is not None:
            return False
            
        # Not 'in stock' if it has been sent to a customer
        if self.sales_order is not None:
            return False

        # Not 'in stock' if it has been allocated to a BuildOrder
        if self.build_order is not None:
            return False

        # Not 'in stock' if it has been assigned to a customer
        if self.customer is not None:
            return False

        # Not 'in stock' if the status code makes it unavailable
        if self.status in StockStatus.UNAVAILABLE_CODES:
            return False

        return True

    @property
    def tracking_info_count(self):
        return self.tracking_info.count()

    @property
    def has_tracking_info(self):
        return self.tracking_info_count > 0

    def addTransactionNote(self, title, user, notes='', url='', system=True):
        """ Generation a stock transaction note for this item.

        Brief automated note detailing a movement or quantity change.
        """
        
        track = StockItemTracking.objects.create(
            item=self,
            title=title,
            user=user,
            quantity=self.quantity,
            date=datetime.now().date(),
            notes=notes,
            link=url,
            system=system
        )

        track.save()

    @transaction.atomic
    def serializeStock(self, quantity, serials, user, notes='', location=None):
        """ Split this stock item into unique serial numbers.

        - Quantity can be less than or equal to the quantity of the stock item
        - Number of serial numbers must match the quantity
        - Provided serial numbers must not already be in use

        Args:
            quantity: Number of items to serialize (integer)
            serials: List of serial numbers (list<int>)
            user: User object associated with action
            notes: Optional notes for tracking
            location: If specified, serialized items will be placed in the given location
        """

        # Cannot serialize stock that is already serialized!
        if self.serialized:
            return

        if not self.part.trackable:
            raise ValidationError({"part": _("Part is not set as trackable")})

        # Quantity must be a valid integer value
        try:
            quantity = int(quantity)
        except ValueError:
            raise ValidationError({"quantity": _("Quantity must be integer")})

        if quantity <= 0:
            raise ValidationError({"quantity": _("Quantity must be greater than zero")})

        if quantity > self.quantity:
            raise ValidationError({"quantity": _("Quantity must not exceed available stock quantity ({n})".format(n=self.quantity))})

        if not type(serials) in [list, tuple]:
            raise ValidationError({"serial_numbers": _("Serial numbers must be a list of integers")})

        if not quantity == len(serials):
            raise ValidationError({"quantity": _("Quantity does not match serial numbers")})

        # Test if each of the serial numbers are valid
        existing = []

        for serial in serials:
            if self.part.checkIfSerialNumberExists(serial):
                existing.append(serial)

        if len(existing) > 0:
            raise ValidationError({"serial_numbers": _("Serial numbers already exist: ") + str(existing)})

        # Create a new stock item for each unique serial number
        for serial in serials:
            
            # Create a copy of this StockItem
            new_item = StockItem.objects.get(pk=self.pk)
            new_item.quantity = 1
            new_item.serial = serial
            new_item.pk = None
            new_item.parent = self

            if location:
                new_item.location = location

            # The item already has a transaction history, don't create a new note
            new_item.save(user=user, note=False)

            # Copy entire transaction history
            new_item.copyHistoryFrom(self)

            # Copy test result history
            new_item.copyTestResultsFrom(self)

            # Create a new stock tracking item
            new_item.addTransactionNote(_('Add serial number'), user, notes=notes)

        # Remove the equivalent number of items
        self.take_stock(quantity, user, notes=_('Serialized {n} items'.format(n=quantity)))

    @transaction.atomic
    def copyHistoryFrom(self, other):
        """ Copy stock history from another StockItem """

        for item in other.tracking_info.all():
            
            item.item = self
            item.pk = None
            item.save()

    @transaction.atomic
    def copyTestResultsFrom(self, other, filters={}):
        """ Copy all test results from another StockItem """

        for result in other.test_results.all().filter(**filters):

            # Create a copy of the test result by nulling-out the pk
            result.pk = None
            result.stock_item = self
            result.save()

    @transaction.atomic
    def splitStock(self, quantity, location, user):
        """ Split this stock item into two items, in the same location.
        Stock tracking notes for this StockItem will be duplicated,
        and added to the new StockItem.

        Args:
            quantity: Number of stock items to remove from this entity, and pass to the next
            location: Where to move the new StockItem to

        Notes:
            The provided quantity will be subtracted from this item and given to the new one.
            The new item will have a different StockItem ID, while this will remain the same.
        """

        # Do not split a serialized part
        if self.serialized:
            return

        try:
            quantity = Decimal(quantity)
        except (InvalidOperation, ValueError):
            return

        # Doesn't make sense for a zero quantity
        if quantity <= 0:
            return

        # Also doesn't make sense to split the full amount
        if quantity >= self.quantity:
            return

        # Create a new StockItem object, duplicating relevant fields
        # Nullify the PK so a new record is created
        new_stock = StockItem.objects.get(pk=self.pk)
        new_stock.pk = None
        new_stock.parent = self
        new_stock.quantity = quantity

        # Move to the new location if specified, otherwise use current location
        if location:
            new_stock.location = location
        else:
            new_stock.location = self.location

        new_stock.save()

        # Copy the transaction history of this part into the new one
        new_stock.copyHistoryFrom(self)

        # Copy the test results of this part to the new one
        new_stock.copyTestResultsFrom(self)

        # Add a new tracking item for the new stock item
        new_stock.addTransactionNote(
            "Split from existing stock",
            user,
            "Split {n} from existing stock item".format(n=quantity))

        # Remove the specified quantity from THIS stock item
        self.take_stock(quantity, user, 'Split {n} items into new stock item'.format(n=quantity))

        # Return a copy of the "new" stock item
        return new_stock

    @transaction.atomic
    def move(self, location, notes, user, **kwargs):
        """ Move part to a new location.

        If less than the available quantity is to be moved,
        a new StockItem is created, with the defined quantity,
        and that new StockItem is moved.
        The quantity is also subtracted from the existing StockItem.

        Args:
            location: Destination location (cannot be null)
            notes: User notes
            user: Who is performing the move
            kwargs:
                quantity: If provided, override the quantity (default = total stock quantity)
        """

        try:
            quantity = Decimal(kwargs.get('quantity', self.quantity))
        except InvalidOperation:
            return False

        if not self.in_stock:
            raise ValidationError(_("StockItem cannot be moved as it is not in stock"))

        if quantity <= 0:
            return False

        if location is None:
            # TODO - Raise appropriate error (cannot move to blank location)
            return False
        elif self.location and (location.pk == self.location.pk) and (quantity == self.quantity):
            # TODO - Raise appropriate error (cannot move to same location)
            return False

        # Test for a partial movement
        if quantity < self.quantity:
            # We need to split the stock!

            # Split the existing StockItem in two
            self.splitStock(quantity, location, user)

            return True

        msg = "Moved to {loc}".format(loc=str(location))

        if self.location:
            msg += " (from {loc})".format(loc=str(self.location))

        self.location = location

        self.addTransactionNote(
            msg,
            user,
            notes=notes,
            system=True)

        self.save()

        return True

    @transaction.atomic
    def updateQuantity(self, quantity):
        """ Update stock quantity for this item.
        
        If the quantity has reached zero, this StockItem will be deleted.

        Returns:
            - True if the quantity was saved
            - False if the StockItem was deleted
        """

        # Do not adjust quantity of a serialized part
        if self.serialized:
            return

        try:
            self.quantity = Decimal(quantity)
        except (InvalidOperation, ValueError):
            return

        if quantity < 0:
            quantity = 0

        self.quantity = quantity

        if quantity == 0 and self.delete_on_deplete and self.can_delete():
            
            # TODO - Do not actually "delete" stock at this point - instead give it a "DELETED" flag
            self.delete()
            return False
        else:
            self.save()
            return True

    @transaction.atomic
    def stocktake(self, count, user, notes=''):
        """ Perform item stocktake.
        When the quantity of an item is counted,
        record the date of stocktake
        """

        try:
            count = Decimal(count)
        except InvalidOperation:
            return False

        if count < 0 or self.infinite:
            return False

        self.stocktake_date = datetime.now().date()
        self.stocktake_user = user

        if self.updateQuantity(count):

            self.addTransactionNote('Stocktake - counted {n} items'.format(n=count),
                                    user,
                                    notes=notes,
                                    system=True)

        return True

    @transaction.atomic
    def add_stock(self, quantity, user, notes=''):
        """ Add items to stock
        This function can be called by initiating a ProjectRun,
        or by manually adding the items to the stock location
        """

        # Cannot add items to a serialized part
        if self.serialized:
            return False

        try:
            quantity = Decimal(quantity)
        except InvalidOperation:
            return False

        # Ignore amounts that do not make sense
        if quantity <= 0 or self.infinite:
            return False

        if self.updateQuantity(self.quantity + quantity):
            
            self.addTransactionNote('Added {n} items to stock'.format(n=quantity),
                                    user,
                                    notes=notes,
                                    system=True)

        return True

    @transaction.atomic
    def take_stock(self, quantity, user, notes=''):
        """ Remove items from stock
        """

        # Cannot remove items from a serialized part
        if self.serialized:
            return False

        try:
            quantity = Decimal(quantity)
        except InvalidOperation:
            return False

        if quantity <= 0 or self.infinite:
            return False

        if self.updateQuantity(self.quantity - quantity):

            self.addTransactionNote('Removed {n} items from stock'.format(n=quantity),
                                    user,
                                    notes=notes,
                                    system=True)

        return True

    def __str__(self):
        if self.part.trackable and self.serial:
            s = '{part} #{sn}'.format(
                part=self.part.full_name,
                sn=self.serial)
        else:
            s = '{n} x {part}'.format(
                n=helpers.decimal2string(self.quantity),
                part=self.part.full_name)

        if self.location:
            s += ' @ {loc}'.format(loc=self.location.name)

        return s

    def getTestResults(self, test=None, result=None, user=None):
        """
        Return all test results associated with this StockItem.

        Optionally can filter results by:
        - Test name
        - Test result
        - User
        """

        results = self.test_results

        if test:
            # Filter by test name
            results = results.filter(test=test)

        if result is not None:
            # Filter by test status
            results = results.filter(result=result)

        if user:
            # Filter by user
            results = results.filter(user=user)

        return results

    def testResultMap(self, **kwargs):
        """
        Return a map of test-results using the test name as the key.
        Where multiple test results exist for a given name,
        the *most recent* test is used.

        This map is useful for rendering to a template (e.g. a test report),
        as all named tests are accessible.
        """

        results = self.getTestResults(**kwargs).order_by('-date')

        result_map = {}

        for result in results:
            key = helpers.generateTestKey(result.test)
            result_map[key] = result

        return result_map

    def testResultList(self, **kwargs):
        """
        Return a list of test-result objects for this StockItem
        """

        return self.testResultMap(**kwargs).values()

    def requiredTestStatus(self):
        """
        Return the status of the tests required for this StockItem.

        return:
            A dict containing the following items:
            - total: Number of required tests
            - passed: Number of tests that have passed
            - failed: Number of tests that have failed
        """

        # All the tests required by the part object
        required = self.part.getRequiredTests()

        results = self.testResultMap()

        total = len(required)
        passed = 0
        failed = 0

        for test in required:
            key = helpers.generateTestKey(test.test_name)

            if key in results:
                result = results[key]

                if result.result:
                    passed += 1
                else:
                    failed += 1

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
        }

    @property
    def required_test_count(self):
        return self.part.getRequiredTests().count()

    def hasRequiredTests(self):
        return self.part.getRequiredTests().count() > 0

    def passedAllRequiredTests(self):

        status = self.requiredTestStatus()

        return status['passed'] >= status['total']


@receiver(pre_delete, sender=StockItem, dispatch_uid='stock_item_pre_delete_log')
def before_delete_stock_item(sender, instance, using, **kwargs):
    """ Receives pre_delete signal from StockItem object.

    Before a StockItem is deleted, ensure that each child object is updated,
    to point to the new parent item.
    """

    # Update each StockItem parent field
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()

    # Rebuild the MPTT tree
    StockItem.objects.rebuild()


class StockItemAttachment(InvenTreeAttachment):
    """
    Model for storing file attachments against a StockItem object.
    """

    def getSubdir(self):
        return os.path.join("stock_files", str(self.stock_item.id))

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='attachments'
    )


class StockItemTracking(models.Model):
    """ Stock tracking entry - breacrumb for keeping track of automated stock transactions

    Attributes:
        item: Link to StockItem
        date: Date that this tracking info was created
        title: Title of this tracking info (generated by system)
        notes: Associated notes (input by user)
        link: Optional URL to external page
        user: The user associated with this tracking info
        quantity: The StockItem quantity at this point in time
    """

    def get_absolute_url(self):
        return '/stock/track/{pk}'.format(pk=self.id)
        # return reverse('stock-tracking-detail', kwargs={'pk': self.id})

    item = models.ForeignKey(StockItem, on_delete=models.CASCADE,
                             related_name='tracking_info')

    date = models.DateTimeField(auto_now_add=True, editable=False)

    title = models.CharField(blank=False, max_length=250, help_text=_('Tracking entry title'))

    notes = models.CharField(blank=True, max_length=512, help_text=_('Entry notes'))

    link = InvenTreeURLField(blank=True, help_text=_('Link to external page for further information'))

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    system = models.BooleanField(default=False)

    quantity = models.DecimalField(max_digits=15, decimal_places=5, validators=[MinValueValidator(0)], default=1)

    # TODO
    # image = models.ImageField(upload_to=func, max_length=255, null=True, blank=True)

    # TODO
    # file = models.FileField()


def rename_stock_item_test_result_attachment(instance, filename):

    return os.path.join('stock_files', str(instance.stock_item.pk), os.path.basename(filename))


class StockItemTestResult(models.Model):
    """
    A StockItemTestResult records results of custom tests against individual StockItem objects.
    This is useful for tracking unit acceptance tests, and particularly useful when integrated
    with automated testing setups.

    Multiple results can be recorded against any given test, allowing tests to be run many times.
    
    Attributes:
        stock_item: Link to StockItem
        test: Test name (simple string matching)
        result: Test result value (pass / fail / etc)
        value: Recorded test output value (optional)
        attachment: Link to StockItem attachment (optional)
        notes: Extra user notes related to the test (optional)
        user: User who uploaded the test result
        date: Date the test result was recorded
    """

    def save(self, *args, **kwargs):

        super().clean()
        super().validate_unique()
        super().save(*args, **kwargs)

    def clean(self):

        super().clean()

        # If this test result corresponds to a template, check the requirements of the template
        key = self.key

        templates = self.stock_item.part.getTestTemplates()

        for template in templates:
            if key == template.key:
                
                if template.requires_value:
                    if not self.value:
                        raise ValidationError({
                            "value": _("Value must be provided for this test"),
                        })

                if template.requires_attachment:
                    if not self.attachment:
                        raise ValidationError({
                            "attachment": _("Attachment must be uploaded for this test"),
                        })

                break

    @property
    def key(self):
        return helpers.generateTestKey(self.test)

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='test_results'
    )

    test = models.CharField(
        blank=False, max_length=100,
        verbose_name=_('Test'),
        help_text=_('Test name')
    )

    result = models.BooleanField(
        default=False,
        verbose_name=_('Result'),
        help_text=_('Test result')
    )

    value = models.CharField(
        blank=True, max_length=500,
        verbose_name=_('Value'),
        help_text=_('Test output value')
    )

    attachment = models.FileField(
        null=True, blank=True,
        upload_to=rename_stock_item_test_result_attachment,
        verbose_name=_('Attachment'),
        help_text=_('Test result attachment'),
    )

    notes = models.CharField(
        blank=True, max_length=500,
        verbose_name=_('Notes'),
        help_text=_("Test notes"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True
    )

    date = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )
