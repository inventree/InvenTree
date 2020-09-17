"""
Build database model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

from django.urls import reverse
from django.db import models, transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.core.validators import MinValueValidator

from markdownx.models import MarkdownxField

from mptt.models import MPTTModel, TreeForeignKey

from InvenTree.status_codes import BuildStatus
from InvenTree.helpers import decimal2string
import InvenTree.fields

from stock import models as StockModels
from part import models as PartModels


class Build(MPTTModel):
    """ A Build object organises the creation of new parts from the component parts.

    Attributes:
        part: The part to be built (from component BOM items)
        title: Brief title describing the build (required)
        quantity: Number of units to be built
        parent: Reference to a Build object for which this Build is required
        sales_order: References to a SalesOrder object for which this Build is required (e.g. the output of this build will be used to fulfil a sales order)
        take_from: Location to take stock from to make this build (if blank, can take from anywhere)
        status: Build status code
        batch: Batch code transferred to build parts (optional)
        creation_date: Date the build was created (auto)
        completion_date: Date the build was completed
        link: External URL for extra information
        notes: Text notes
    """

    def __str__(self):
        return "{q} x {part}".format(q=decimal2string(self.quantity), part=str(self.part.full_name))

    def get_absolute_url(self):
        return reverse('build-detail', kwargs={'pk': self.id})

    def clean(self):
        """
        Validation for Build object.
        """

        super().clean()

        try:
            if self.part.trackable:
                if not self.quantity == int(self.quantity):
                    raise ValidationError({
                        'quantity': _("Build quantity must be integer value for trackable parts")
                    })
        except PartModels.Part.DoesNotExist:
            pass

    title = models.CharField(
        verbose_name=_('Build Title'),
        blank=False,
        max_length=100,
        help_text=_('Brief description of the build')
    )

    parent = TreeForeignKey(
        'self',
        on_delete=models.DO_NOTHING,
        blank=True, null=True,
        related_name='children',
        verbose_name=_('Parent Build'),
        help_text=_('Parent build to which this build is allocated'),
    )

    part = models.ForeignKey(
        'part.Part',
        verbose_name=_('Part'),
        on_delete=models.CASCADE,
        related_name='builds',
        limit_choices_to={
            'is_template': False,
            'assembly': True,
            'active': True,
            'virtual': False,
        },
        help_text=_('Select part to build'),
    )

    sales_order = models.ForeignKey(
        'order.SalesOrder',
        verbose_name=_('Sales Order Reference'),
        on_delete=models.SET_NULL,
        related_name='builds',
        null=True, blank=True,
        help_text=_('SalesOrder to which this build is allocated')
    )
    
    take_from = models.ForeignKey(
        'stock.StockLocation',
        verbose_name=_('Source Location'),
        on_delete=models.SET_NULL,
        related_name='sourcing_builds',
        null=True, blank=True,
        help_text=_('Select location to take stock from for this build (leave blank to take from any stock location)')
    )
    
    quantity = models.PositiveIntegerField(
        verbose_name=_('Build Quantity'),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_('Number of parts to build')
    )

    status = models.PositiveIntegerField(
        verbose_name=_('Build Status'),
        default=BuildStatus.PENDING,
        choices=BuildStatus.items(),
        validators=[MinValueValidator(0)],
        help_text=_('Build status code')
    )
    
    batch = models.CharField(
        verbose_name=_('Batch Code'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Batch code for this build output')
    )
    
    creation_date = models.DateField(auto_now_add=True, editable=False)
    
    completion_date = models.DateField(null=True, blank=True)

    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='builds_completed'
    )
    
    link = InvenTree.fields.InvenTreeURLField(
        verbose_name=_('External Link'),
        blank=True, help_text=_('Link to external URL')
    )

    notes = MarkdownxField(
        verbose_name=_('Notes'),
        blank=True, help_text=_('Extra build notes')
    )

    @property
    def output_count(self):
        return self.build_outputs.count()

    @transaction.atomic
    def cancelBuild(self, user):
        """ Mark the Build as CANCELLED

        - Delete any pending BuildItem objects (but do not remove items from stock)
        - Set build status to CANCELLED
        - Save the Build object
        """

        for item in self.allocated_stock.all():
            item.delete()

        # Date of 'completion' is the date the build was cancelled
        self.completion_date = datetime.now().date()
        self.completed_by = user

        self.status = BuildStatus.CANCELLED
        self.save()

    def getAutoAllocations(self):
        """ Return a list of parts which will be allocated
        using the 'AutoAllocate' function.

        For each item in the BOM for the attached Part:

        - If there is a single StockItem, use that StockItem
        - Take as many parts as available (up to the quantity required for the BOM)
        - If there are multiple StockItems available, ignore (leave up to the user)

        Returns:
            A list object containing the StockItem objects to be allocated (and the quantities)
        """

        allocations = []

        for item in self.part.bom_items.all().prefetch_related('sub_part'):

            # How many parts required for this build?
            q_required = item.quantity * self.quantity

            # Grab a list of StockItem objects which are "in stock"
            stock = StockModels.StockItem.objects.filter(StockModels.StockItem.IN_STOCK_FILTER)
            
            # Filter by part reference
            stock = stock.filter(part=item.sub_part)

            # Ensure that the available stock items are in the correct location
            if self.take_from is not None:
                # Filter for stock that is located downstream of the designated location
                stock = stock.filter(location__in=[loc for loc in self.take_from.getUniqueChildren()])

            # Only one StockItem to choose from? Default to that one!
            if len(stock) == 1:
                stock_item = stock[0]

                # Check that we have not already allocated this stock-item against this build
                build_items = BuildItem.objects.filter(build=self, stock_item=stock_item)

                if len(build_items) > 0:
                    continue

                # Are there any parts available?
                if stock_item.quantity > 0:

                    # Only take as many as are available
                    if stock_item.quantity < q_required:
                        q_required = stock_item.quantity

                    allocation = {
                        'stock_item': stock_item,
                        'quantity': q_required,
                    }

                    allocations.append(allocation)

        return allocations

    @transaction.atomic
    def unallocateStock(self):
        """ Deletes all stock allocations for this build. """

        BuildItem.objects.filter(build=self.id).delete()

    @transaction.atomic
    def autoAllocate(self):
        """ Run auto-allocation routine to allocate StockItems to this Build.

        Returns a list of dict objects with keys like:

            {
                'stock_item': item,
                'quantity': quantity,
            }

        See: getAutoAllocations()
        """

        allocations = self.getAutoAllocations()

        for item in allocations:
            # Create a new allocation
            build_item = BuildItem(
                build=self,
                stock_item=item['stock_item'],
                quantity=item['quantity'])

            build_item.save()

    @transaction.atomic
    def completeBuild(self, location, serial_numbers, user):
        """ Mark the Build as COMPLETE

        - Takes allocated items from stock
        - Delete pending BuildItem objects
        """

        # Complete the build allocation for each BuildItem
        for build_item in self.allocated_stock.all().prefetch_related('stock_item'):
            build_item.complete_allocation(user)

            # Check that the stock-item has been assigned to this build, and remove the builditem from the database
            if build_item.stock_item.build_order == self:
                build_item.delete()

        notes = 'Built {q} on {now}'.format(
            q=self.quantity,
            now=str(datetime.now().date())
        )

        # Generate the build outputs
        if self.part.trackable and serial_numbers:
            # Add new serial numbers
            for serial in serial_numbers:
                item = StockModels.StockItem.objects.create(
                    part=self.part,
                    build=self,
                    location=location,
                    quantity=1,
                    serial=serial,
                    batch=str(self.batch) if self.batch else '',
                    notes=notes
                )

                item.save()

        else:
            # Add stock of the newly created item
            item = StockModels.StockItem.objects.create(
                part=self.part,
                build=self,
                location=location,
                quantity=self.quantity,
                batch=str(self.batch) if self.batch else '',
                notes=notes
            )

            item.save()

        # Finally, mark the build as complete
        self.completion_date = datetime.now().date()
        self.completed_by = user
        self.status = BuildStatus.COMPLETE
        self.save()

        return True

    def isFullyAllocated(self):
        """
        Return True if this build has been fully allocated.
        """

        bom_items = self.part.bom_items.all()

        for item in bom_items:
            part = item.sub_part

            if not self.isPartFullyAllocated(part):
                return False

        return True

    def isPartFullyAllocated(self, part):
        """
        Check if a given Part is fully allocated for this Build
        """

        return self.getAllocatedQuantity(part) >= self.getRequiredQuantity(part)

    def getRequiredQuantity(self, part):
        """ Calculate the quantity of <part> required to make this build.
        """

        try:
            item = PartModels.BomItem.objects.get(part=self.part.id, sub_part=part.id)
            q = item.quantity
        except PartModels.BomItem.DoesNotExist:
            q = 0

        return q * self.quantity

    def getAllocatedQuantity(self, part):
        """ Calculate the total number of <part> currently allocated to this build
        """

        allocated = BuildItem.objects.filter(build=self.id, stock_item__part=part.id).aggregate(q=Coalesce(Sum('quantity'), 0))

        return allocated['q']

    def getUnallocatedQuantity(self, part):
        """ Calculate the quantity of <part> which still needs to be allocated to this build.

        Args:
            Part - the part to be tested

        Returns:
            The remaining allocated quantity
        """

        return max(self.getRequiredQuantity(part) - self.getAllocatedQuantity(part), 0)

    @property
    def required_parts(self):
        """ Returns a dict of parts required to build this part (BOM) """
        parts = []

        for item in self.part.bom_items.all().prefetch_related('sub_part'):
            part = {
                'part': item.sub_part,
                'per_build': item.quantity,
                'quantity': item.quantity * self.quantity,
                'allocated': self.getAllocatedQuantity(item.sub_part)
            }

            parts.append(part)

        return parts

    @property
    def can_build(self):
        """ Return true if there are enough parts to supply build """

        for item in self.required_parts:
            if item['part'].total_stock < item['quantity']:
                return False

        return True

    @property
    def is_active(self):
        """ Is this build active? An active build is either:

        - PENDING
        - HOLDING
        """

        return self.status in BuildStatus.ACTIVE_CODES

    @property
    def is_complete(self):
        """ Returns True if the build status is COMPLETE """
        return self.status == BuildStatus.COMPLETE


class BuildItem(models.Model):
    """ A BuildItem links multiple StockItem objects to a Build.
    These are used to allocate part stock to a build.
    Once the Build is completed, the parts are removed from stock and the
    BuildItemAllocation objects are removed.

    Attributes:
        build: Link to a Build object
        stock_item: Link to a StockItem object
        quantity: Number of units allocated
    """

    def get_absolute_url(self):
        # TODO - Fix!
        return '/build/item/{pk}/'.format(pk=self.id)
        # return reverse('build-detail', kwargs={'pk': self.id})

    class Meta:
        unique_together = [
            ('build', 'stock_item'),
        ]

    def clean(self):
        """ Check validity of the BuildItem model.
        The following checks are performed:

        - StockItem.part must be in the BOM of the Part object referenced by Build
        - Allocation quantity cannot exceed available quantity
        """
        
        super(BuildItem, self).clean()

        errors = {}

        try:
            if self.stock_item.part not in self.build.part.required_parts():
                errors['stock_item'] = [_("Selected stock item not found in BOM for part '{p}'".format(p=self.build.part.full_name))]
            
            if self.quantity > self.stock_item.quantity:
                errors['quantity'] = [_("Allocated quantity ({n}) must not exceed available quantity ({q})".format(
                    n=self.quantity,
                    q=self.stock_item.quantity
                ))]

            if self.stock_item.quantity - self.stock_item.allocation_count() + self.quantity < self.quantity:
                errors['quantity'] = _('StockItem is over-allocated')

            if self.quantity <= 0:
                errors['quantity'] = _('Allocation quantity must be greater than zero')

            if self.stock_item.serial and not self.quantity == 1:
                errors['quantity'] = _('Quantity must be 1 for serialized stock')

        except (StockModels.StockItem.DoesNotExist, PartModels.Part.DoesNotExist):
            pass

        if len(errors) > 0:
            raise ValidationError(errors)

    def complete_allocation(self, user):

        item = self.stock_item

        # Split the allocated stock if there are more available than allocated
        if item.quantity > self.quantity:
            item = item.splitStock(self.quantity, None, user)

            # Update our own reference to the new item
            self.stock_item = item
            self.save()

        # TODO - If the item__part object is not trackable, delete the stock item here
        
        item.build_order = self.build
        item.save()

    build = models.ForeignKey(
        Build,
        on_delete=models.CASCADE,
        related_name='allocated_stock',
        help_text=_('Build to allocate parts')
    )

    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='allocations',
        help_text=_('Stock Item to allocate to build'),
        limit_choices_to={
            'build_order': None,
            'sales_order': None,
            'belongs_to': None,
        }
    )

    quantity = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=1,
        validators=[MinValueValidator(0)],
        help_text=_('Stock quantity to allocate to build')
    )
