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
import uuid

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
    A 'StockItem' instance represents a quantity of physical instances of a part.
    It may exist in a StockLocation, or as part of a sub-assembly installed into another StockItem
    StockItems may be tracked using batch or serial numbers.
    If a serial number is assigned, then StockItem cannot have a quantity other than 1
    """

    def save(self, *args, **kwargs):
        if not self.pk:
            add_note = True
        else:
            add_note = False

        super(StockItem, self).save(*args, **kwargs)

        if add_note:
            # This StockItem is being saved for the first time
            self.add_transaction_note(
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

    # UUID for generating QR codes
    uuid = models.UUIDField(default=uuid.uuid4, blank=True, editable=False)

    # The 'master' copy of the part of which this stock item is an instance
    part = models.ForeignKey('part.Part', on_delete=models.CASCADE, related_name='locations')

    # The 'supplier part' used in this instance. May be null if no supplier parts are defined the master part
    supplier_part = models.ForeignKey('part.SupplierPart', blank=True, null=True, on_delete=models.SET_NULL)

    # Where the part is stored. If the part has been used to build another stock item, the location may not make sense
    location = models.ForeignKey(StockLocation, on_delete=models.DO_NOTHING,
                                 related_name='stock_items', blank=True, null=True,
                                 help_text='Where is this stock item located?')

    # If this StockItem belongs to another StockItem (e.g. as part of a sub-assembly)
    belongs_to = models.ForeignKey('self', on_delete=models.DO_NOTHING,
                                   related_name='owned_parts', blank=True, null=True,
                                   help_text='Is this item installed in another item?')

    # The StockItem may be assigned to a particular customer
    customer = models.ForeignKey('company.Company', on_delete=models.SET_NULL,
                                 related_name='stockitems', blank=True, null=True,
                                 help_text='Item assigned to customer?')

    # Optional serial number
    serial = models.PositiveIntegerField(blank=True, null=True,
                                         help_text='Serial number for this item')

    # Optional URL to link to external resource
    URL = models.URLField(max_length=125, blank=True)

    # Optional batch information
    batch = models.CharField(max_length=100, blank=True, null=True,
                             help_text='Batch code for this stock item')

    # If this part was produced by a build, point to that build here
    # build = models.ForeignKey('build.Build', on_delete=models.SET_NULL, blank=True, null=True)

    # Quantity of this stock item. Value may be overridden by other settings
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=1)

    # Last time this item was updated (set automagically)
    updated = models.DateField(auto_now=True)

    # last time the stock was checked / counted
    stocktake_date = models.DateField(blank=True, null=True)

    stocktake_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                       related_name='stocktake_stock')

    review_needed = models.BooleanField(default=False)

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

    def add_transaction_note(self, title, user, notes='', system=True):
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
    def move(self, location, notes, user):

        if location is None:
            # TODO - Raise appropriate error (cannot move to blank location)
            return False
        elif self.location and (location.pk == self.location.pk):
            # TODO - Raise appropriate error (cannot move to same location)
            return False

        msg = "Moved to {loc}".format(loc=str(location))

        if self.location:
            msg += " (from {loc})".format(loc=str(self.location))

        self.location = location
        self.save()

        self.add_transaction_note(msg,
                                  user,
                                  notes=notes,
                                  system=True)

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

        self.quantity = count
        self.stocktake_date = datetime.now().date()
        self.stocktake_user = user
        self.save()

        self.add_transaction_note('Stocktake - counted {n} items'.format(n=count),
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

        self.quantity += quantity

        self.save()

        self.add_transaction_note('Added {n} items to stock'.format(n=quantity),
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

        self.quantity -= quantity

        if self.quantity < 0:
            self.quantity = 0

        self.save()

        self.add_transaction_note('Removed {n} items from stock'.format(n=quantity),
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
    """ Stock tracking entry
    """

    def get_absolute_url(self):
        return '/stock/track/{pk}'.format(pk=self.id)
        # return reverse('stock-tracking-detail', kwargs={'pk': self.id})

    # Stock item
    item = models.ForeignKey(StockItem, on_delete=models.CASCADE,
                             related_name='tracking_info')

    # Date this entry was created (cannot be edited)
    date = models.DateTimeField(auto_now_add=True, editable=False)

    # Short-form title for this tracking entry
    title = models.CharField(max_length=250)

    # Optional longer description
    notes = models.TextField(blank=True)

    # Which user created this tracking entry?
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    # Was this tracking note auto-generated by the system?
    system = models.BooleanField(default=False)

    # Keep track of the StockItem quantity throughout the tracking history
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=1)

    # TODO
    # image = models.ImageField(upload_to=func, max_length=255, null=True, blank=True)

    # TODO
    # file = models.FileField()
