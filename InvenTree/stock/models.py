from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

from supplier.models import SupplierPart
from part.models import Part
from InvenTree.models import InvenTreeTree

from datetime import datetime

from django.db.models.signals import pre_delete
from django.dispatch import receiver


class StockLocation(InvenTreeTree):
    """ Organization tree for StockItem objects
    A "StockLocation" can be considered a warehouse, or storage location
    Stock locations can be heirarchical as required
    """

    def get_absolute_url(self):
        return '/stock/location/{id}/'.format(id=self.id)

    @property
    def items(self):
        stock_list = self.stockitem_set.all()
        return stock_list


@receiver(pre_delete, sender=StockLocation, dispatch_uid='stocklocation_delete_log')
def before_delete_stock_location(sender, instance, using, **kwargs):

    # Update each part in the stock location
    for item in instance.items.all():
        # If this location has a parent, move the child stock items to the parent
        if instance.parent:
            item.location = instance.parent
            item.save()
        # No parent location? Delete the stock items
        else:
            item.delete()

    # Update each child category
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()


class StockItem(models.Model):

    def get_absolute_url(self):
        return '/stock/item/{id}/'.format(id=self.id)

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='locations')

    supplier_part = models.ForeignKey(SupplierPart, blank=True, null=True, on_delete=models.SET_NULL)

    location = models.ForeignKey(StockLocation, on_delete=models.DO_NOTHING,
                                 related_name='items', blank=True, null=True)

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    updated = models.DateField(auto_now=True)

    # last time the stock was checked / counted
    stocktake_date = models.DateField(blank=True, null=True)

    stocktake_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    review_needed = models.BooleanField(default=False)

    # Stock status types
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

    notes = models.CharField(max_length=100, blank=True)

    # If stock item is incoming, an (optional) ETA field
    # expected_arrival = models.DateField(null=True, blank=True)

    infinite = models.BooleanField(default=False)

    # History of this item
    history = HistoricalRecords()

    @transaction.atomic
    def stocktake(self, count, user):
        """ Perform item stocktake.
        When the quantity of an item is counted,
        record the date of stocktake
        """

        count = int(count)

        if count < 0 or self.infinite:
            return

        self.quantity = count
        self.stocktake_date = datetime.now().date()
        self.stocktake_user = user
        self.save()

    @transaction.atomic
    def add_stock(self, amount):
        """ Add items to stock
        This function can be called by initiating a ProjectRun,
        or by manually adding the items to the stock location
        """

        amount = int(amount)

        if self.infinite or amount == 0:
            return

        amount = int(amount)

        q = self.quantity + amount
        if q < 0:
            q = 0

        self.quantity = q
        self.save()

    @transaction.atomic
    def take_stock(self, amount):
        self.add_stock(-amount)

    def __str__(self):
        return "{n} x {part} @ {loc}".format(
            n=self.quantity,
            part=self.part.name,
            loc=self.location.name)
