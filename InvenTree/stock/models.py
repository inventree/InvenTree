"""
Stock database model definitions
"""


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse

from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from datetime import datetime
from InvenTree import helpers

from InvenTree.models import InvenTreeTree

from part.models import Part


class StockLocation(InvenTreeTree):
    """ Organization tree for StockItem objects
    A "StockLocation" can be considered a warehouse, or storage location
    Stock locations can be heirarchical as required
    """

    def get_absolute_url(self):
        return reverse('stock-location-detail', kwargs={'pk': self.id})

    def has_items(self):
        return self.stock_items.count() > 0

    def format_barcode(self):
        """ Return a JSON string for formatting a barcode for this StockLocation object """

        return helpers.MakeBarcode(
            'StockLocation',
            self.id,
            reverse('api-location-detail', kwargs={'pk': self.id}),
            {
                'name': self.name,
            }
        )

    @property
    def stock_item_count(self):
        """ Return the number of StockItem objects which live in or under this category
        """

        return len(StockItem.objects.filter(location__in=self.getUniqueChildren()))

    @property
    def item_count(self):

        return self.stock_item_count


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


class StockItem(models.Model):
    """
    A StockItem object represents a quantity of physical instances of a part.
    
    Attributes:
        part: Link to the master abstract part that this StockItem is an instance of
        supplier_part: Link to a specific SupplierPart (optional)
        location: Where this StockItem is located
        quantity: Number of stocked units
        batch: Batch number for this StockItem
        URL: Optional URL to link to external resource
        updated: Date that this stock item was last updated (auto)
        stocktake_date: Date of last stocktake for this item
        stocktake_user: User that performed the most recent stocktake
        review_needed: Flag if StockItem needs review
        delete_on_deplete: If True, StockItem will be deleted when the stock level gets to zero
        status: Status of this StockItem (ref: ITEM_STATUS_CODES)
        notes: Extra notes field
        infinite: If True this StockItem can never be exhausted
    """

    def save(self, *args, **kwargs):
        if not self.pk:
            add_note = True
        else:
            add_note = False

        super(StockItem, self).save(*args, **kwargs)

        if add_note:
            # This StockItem is being saved for the first time
            self.addTransactionNote(
                'Created stock item',
                None,
                notes="Created new stock item for part '{p}'".format(p=str(self.part)),
                system=True
            )

    def clean(self):
        """ Validate the StockItem object (separate to field validation)

        The following validation checks are performed:

        - The 'part' and 'supplier_part.part' fields cannot point to the same Part object
        - The 'part' does not belong to itself
        - Quantity must be 1 if the StockItem has a serial number
        """

        # The 'supplier_part' field must point to the same part!
        try:
            if self.supplier_part is not None:
                if not self.supplier_part.part == self.part:
                    raise ValidationError({'supplier_part': _("Part type ('{pf}') must be {pe}").format(
                                           pf=str(self.supplier_part.part),
                                           pe=str(self.part))
                                           })

            if self.part is not None:
                if self.part.trackable and not self.serial:
                    raise ValidationError({
                        'serial': _('Serial number must be set for trackable items')
                    })

        except Part.DoesNotExist:
            # This gets thrown if self.supplier_part is null
            # TODO - Find a test than can be perfomed...
            pass

        if self.belongs_to and self.belongs_to.pk == self.pk:
            raise ValidationError({
                'belongs_to': _('Item cannot belong to itself')
            })

        # Serial number cannot be set for items with quantity greater than 1
        if not self.quantity == 1 and self.serial:
            raise ValidationError({
                'quantity': _("Quantity must be set to 1 for item with a serial number"),
                'serial': _("Serial number cannot be set if quantity > 1")
            })

    def get_absolute_url(self):
        return reverse('stock-item-detail', kwargs={'pk': self.id})

    class Meta:
        unique_together = [
            ('part', 'serial'),
        ]

    def format_barcode(self):
        """ Return a JSON string for formatting a barcode for this StockItem.
        Can be used to perform lookup of a stockitem using barcode

        Contains the following data:

        { type: 'StockItem', stock_id: <pk>, part_id: <part_pk> }

        Voltagile data (e.g. stock quantity) should be looked up using the InvenTree API (as it may change)
        """

        return helpers.MakeBarcode(
            'StockItem',
            self.id,
            reverse('api-stock-detail', kwargs={'pk': self.id}),
            {
                'part_id': self.part.id,
                'part_name': self.part.name
            }
        )

    part = models.ForeignKey('part.Part', on_delete=models.CASCADE, related_name='locations', help_text='Base part')

    supplier_part = models.ForeignKey('part.SupplierPart', blank=True, null=True, on_delete=models.SET_NULL,
                                      help_text='Select a matching supplier part for this stock item')

    location = models.ForeignKey(StockLocation, on_delete=models.DO_NOTHING,
                                 related_name='stock_items', blank=True, null=True,
                                 help_text='Where is this stock item located?')

    belongs_to = models.ForeignKey('self', on_delete=models.DO_NOTHING,
                                   related_name='owned_parts', blank=True, null=True,
                                   help_text='Is this item installed in another item?')

    customer = models.ForeignKey('company.Company', on_delete=models.SET_NULL,
                                 related_name='stockitems', blank=True, null=True,
                                 help_text='Item assigned to customer?')

    serial = models.PositiveIntegerField(blank=True, null=True,
                                         help_text='Serial number for this item')
 
    URL = models.URLField(max_length=125, blank=True)

    batch = models.CharField(max_length=100, blank=True, null=True,
                             help_text='Batch code for this stock item')

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=1)

    updated = models.DateField(auto_now=True)

    # last time the stock was checked / counted
    stocktake_date = models.DateField(blank=True, null=True)

    stocktake_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                       related_name='stocktake_stock')

    review_needed = models.BooleanField(default=False)

    delete_on_deplete = models.BooleanField(default=True, help_text='Delete this Stock Item when stock is depleted')

    ITEM_OK = 10
    ITEM_ATTENTION = 50
    ITEM_DAMAGED = 55
    ITEM_DESTROYED = 60

    ITEM_STATUS_CODES = {
        ITEM_OK: _("OK"),
        ITEM_ATTENTION: _("Attention needed"),
        ITEM_DAMAGED: _("Damaged"),
        ITEM_DESTROYED: _("Destroyed")
    }

    status = models.PositiveIntegerField(
        default=ITEM_OK,
        choices=ITEM_STATUS_CODES.items(),
        validators=[MinValueValidator(0)])

    notes = models.CharField(max_length=250, blank=True, help_text='Stock Item Notes')

    # If stock item is incoming, an (optional) ETA field
    # expected_arrival = models.DateField(null=True, blank=True)

    infinite = models.BooleanField(default=False)

    def can_delete(self):
        # TODO - Return FALSE if this item cannot be deleted!
        return True

    @property
    def in_stock(self):

        if self.belongs_to or self.customer:
            return False

        return True

    @property
    def has_tracking_info(self):
        return self.tracking_info.count() > 0

    def addTransactionNote(self, title, user, notes='', system=True):
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
            system=system
        )

        track.save()

    @transaction.atomic
    def splitStock(self, quantity, user):
        """ Split this stock item into two items, in the same location.
        Stock tracking notes for this StockItem will be duplicated,
        and added to the new StockItem.

        Args:
            quantity: Number of stock items to remove from this entity, and pass to the next

        Notes:
            The provided quantity will be subtracted from this item and given to the new one.
            The new item will have a different StockItem ID, while this will remain the same.
        """

        # Doesn't make sense for a zero quantity
        if quantity <= 0:
            return

        # Also doesn't make sense to split the full amount
        if quantity >= self.quantity:
            return

        # Create a new StockItem object, duplicating relevant fields
        new_stock = StockItem.objects.create(
            part=self.part,
            quantity=quantity,
            supplier_part=self.supplier_part,
            location=self.location,
            batch=self.batch,
            delete_on_deplete=self.delete_on_deplete
        )

        new_stock.save()

        # Add a new tracking item for the new stock item
        new_stock.addTransactionNote(
            "Split from existing stock",
            user,
            "Split {n} from existing stock item".format(n=quantity))

        # Remove the specified quantity from THIS stock item
        self.take_stock(quantity, user, 'Split {n} items into new stock item'.format(n=quantity))

    @transaction.atomic
    def move(self, location, notes, user, **kwargs):
        """ Move part to a new location.

        Args:
            location: Destination location (cannot be null)
            notes: User notes
            user: Who is performing the move
            kwargs:
                quantity: If provided, override the quantity (default = total stock quantity)
        """

        quantity = int(kwargs.get('quantity', self.quantity))

        if quantity <= 0:
            return False

        if location is None:
            # TODO - Raise appropriate error (cannot move to blank location)
            return False
        elif self.location and (location.pk == self.location.pk):
            # TODO - Raise appropriate error (cannot move to same location)
            return False

        # Test for a partial movement
        if quantity < self.quantity:
            # We need to split the stock!

            # Leave behind certain quantity
            self.splitStock(self.quantity - quantity, user)

        msg = "Moved to {loc}".format(loc=str(location))

        if self.location:
            msg += " (from {loc})".format(loc=str(self.location))

        self.location = location

        self.addTransactionNote(msg,
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

        if quantity < 0:
            quantity = 0

        self.quantity = quantity

        if quantity <= 0 and self.delete_on_deplete:
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

        count = int(count)

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

        quantity = int(quantity)

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

        if self.quantity == 0:
            return False

        quantity = int(quantity)

        if quantity <= 0 or self.infinite:
            return False

        if self.updateQuantity(self.quantity - quantity):

            self.addTransactionNote('Removed {n} items from stock'.format(n=quantity),
                                    user,
                                    notes=notes,
                                    system=True)

        return True

    def __str__(self):
        s = '{n} x {part}'.format(
            n=self.quantity,
            part=self.part.name)

        if self.location:
            s += ' @ {loc}'.format(loc=self.location.name)

        return s


class StockItemTracking(models.Model):
    """ Stock tracking entry - breacrumb for keeping track of automated stock transactions

    Attributes:
        item: Link to StockItem
        date: Date that this tracking info was created
        title: Title of this tracking info (generated by system)
        notes: Associated notes (input by user)
        user: The user associated with this tracking info
        quantity: The StockItem quantity at this point in time
    """

    def get_absolute_url(self):
        return '/stock/track/{pk}'.format(pk=self.id)
        # return reverse('stock-tracking-detail', kwargs={'pk': self.id})

    item = models.ForeignKey(StockItem, on_delete=models.CASCADE,
                             related_name='tracking_info')

    date = models.DateTimeField(auto_now_add=True, editable=False)

    title = models.CharField(blank=False, max_length=250)

    notes = models.TextField(blank=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    system = models.BooleanField(default=False)

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=1)

    # TODO
    # image = models.ImageField(upload_to=func, max_length=255, null=True, blank=True)

    # TODO
    # file = models.FileField()
