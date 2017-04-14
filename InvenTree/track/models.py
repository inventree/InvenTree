from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models
from django.contrib.auth.models import User

from supplier.models import Customer
from part.models import Part, PartRevision


class UniquePart(models.Model):
    """ A unique instance of a Part object.
    Used for tracking parts based on serial numbers,
    and tracking all events in the life of a part
    """

    part = models.ForeignKey(Part, on_delete=models.CASCADE)

    revision = models.ForeignKey(PartRevision,
                                 on_delete=models.CASCADE,
                                 blank=True,
                                 null=True)

    creation_date = models.DateField(auto_now_add=True,
                                     editable=False)
    serial = models.IntegerField()

    createdBy = models.ForeignKey(User)

    customer = models.ForeignKey(Customer, blank=True, null=True)

    # Part status types
    PART_IN_PROGRESS = 0
    PART_IN_STOCK = 10
    PART_SHIPPED = 20
    PART_RETURNED = 30
    PART_DAMAGED = 40
    PART_DESTROYED = 50

    PART_STATUS_CODES = {
        PART_IN_PROGRESS: _("In progress"),
        PART_IN_STOCK: _("In stock"),
        PART_SHIPPED: _("Shipped"),
        PART_RETURNED: _("Returned"),
        PART_DAMAGED: _("Damaged"),
        PART_DESTROYED: _("Destroyed")
    }

    status = models.IntegerField(default=PART_IN_PROGRESS, choices=PART_STATUS_CODES.items())

    def __str__(self):
        return self.part.name


class PartTrackingInfo(models.Model):
    """ Single data-point in the life of a UniquePart
    Each time something happens to the UniquePart,
    a new PartTrackingInfo object should be created.
    """

    part = models.ForeignKey(UniquePart, on_delete=models.CASCADE, related_name='tracking_info')
    date = models.DateField(auto_now_add=True, editable=False)
    notes = models.CharField(max_length=500)
