"""
Build database model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from datetime import datetime

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

from django.urls import reverse
from django.db import models, transaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.core.validators import MinValueValidator

from markdownx.models import MarkdownxField

from mptt.models import MPTTModel, TreeForeignKey

from InvenTree.status_codes import BuildStatus
from InvenTree.helpers import increment, getSetting, normalize
from InvenTree.validators import validate_build_order_reference
from InvenTree.models import InvenTreeAttachment

import common.models

import InvenTree.fields

from stock import models as StockModels
from part import models as PartModels


class Build(MPTTModel):
    """ A Build object organises the creation of new StockItem objects from other existing StockItem objects.

    Attributes:
        part: The part to be built (from component BOM items)
        reference: Build order reference (required, must be unique)
        title: Brief title describing the build (required)
        quantity: Number of units to be built
        parent: Reference to a Build object for which this Build is required
        sales_order: References to a SalesOrder object for which this Build is required (e.g. the output of this build will be used to fulfil a sales order)
        take_from: Location to take stock from to make this build (if blank, can take from anywhere)
        status: Build status code
        batch: Batch code transferred to build parts (optional)
        creation_date: Date the build was created (auto)
        target_date: Date the build will be overdue
        completion_date: Date the build was completed (or, if incomplete, the expected date of completion)
        link: External URL for extra information
        notes: Text notes
    """

    OVERDUE_FILTER = Q(status__in=BuildStatus.ACTIVE_CODES) & ~Q(target_date=None) & Q(target_date__lte=datetime.now().date())

    class Meta:
        verbose_name = _("Build Order")
        verbose_name_plural = _("Build Orders")

    @staticmethod
    def filterByDate(queryset, min_date, max_date):
        """
        Filter by 'minimum and maximum date range'

        - Specified as min_date, max_date
        - Both must be specified for filter to be applied
        """

        date_fmt = '%Y-%m-%d'  # ISO format date string

        # Ensure that both dates are valid
        try:
            min_date = datetime.strptime(str(min_date), date_fmt).date()
            max_date = datetime.strptime(str(max_date), date_fmt).date()
        except (ValueError, TypeError):
            # Date processing error, return queryset unchanged
            return queryset

        # Order was completed within the specified range
        completed = Q(status=BuildStatus.COMPLETE) & Q(completion_date__gte=min_date) & Q(completion_date__lte=max_date)

        # Order target date falls witin specified range
        pending = Q(status__in=BuildStatus.ACTIVE_CODES) & ~Q(target_date=None) & Q(target_date__gte=min_date) & Q(target_date__lte=max_date)

        # TODO - Construct a queryset for "overdue" orders

        queryset = queryset.filter(completed | pending)

        return queryset

    def __str__(self):

        prefix = getSetting("BUILDORDER_REFERENCE_PREFIX")

        return f"{prefix}{self.reference}"

    def get_absolute_url(self):
        return reverse('build-detail', kwargs={'pk': self.id})
        
    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        help_text=_('Build Order Reference'),
        verbose_name=_('Reference'),
        validators=[
            validate_build_order_reference
        ]
    )

    title = models.CharField(
        verbose_name=_('Description'),
        blank=False,
        max_length=100,
        help_text=_('Brief description of the build')
    )

    # TODO - Perhaps delete the build "tree"
    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='children',
        verbose_name=_('Parent Build'),
        help_text=_('BuildOrder to which this build is allocated'),
    )

    part = models.ForeignKey(
        'part.Part',
        verbose_name=_('Part'),
        on_delete=models.CASCADE,
        related_name='builds',
        limit_choices_to={
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
    
    destination = models.ForeignKey(
        'stock.StockLocation',
        verbose_name=_('Destination Location'),
        on_delete=models.SET_NULL,
        related_name='incoming_builds',
        null=True, blank=True,
        help_text=_('Select location where the completed items will be stored'),
    )

    quantity = models.PositiveIntegerField(
        verbose_name=_('Build Quantity'),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_('Number of stock items to build')
    )

    completed = models.PositiveIntegerField(
        verbose_name=_('Completed items'),
        default=0,
        help_text=_('Number of stock items which have been completed')
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
    
    target_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Target completion date'),
        help_text=_('Target date for build completion. Build will be overdue after this date.')
    )

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

    def is_overdue(self):
        """
        Returns true if this build is "overdue":

        - Not completed
        - Target date is "in the past"
        """

        # Cannot be deemed overdue if target_date is not set
        if self.target_date is None:
            return False

        today = datetime.now().date()

        return self.active and self.target_date < today

    @property
    def active(self):
        """
        Return True if this build is active
        """

        return self.status in BuildStatus.ACTIVE_CODES

    @property
    def bom_items(self):
        """
        Returns the BOM items for the part referenced by this BuildOrder
        """

        return self.part.bom_items.all().prefetch_related(
            'sub_part'
        )

    @property
    def remaining(self):
        """
        Return the number of outputs remaining to be completed.
        """

        return max(0, self.quantity - self.completed)

    @property
    def output_count(self):
        return self.build_outputs.count()

    def get_build_outputs(self, **kwargs):
        """
        Return a list of build outputs.

        kwargs:
            complete = (True / False) - If supplied, filter by completed status
            in_stock = (True / False) - If supplied, filter by 'in-stock' status
        """

        outputs = self.build_outputs.all()

        # Filter by 'in stock' status
        in_stock = kwargs.get('in_stock', None)

        if in_stock is not None:
            if in_stock:
                outputs = outputs.filter(StockModels.StockItem.IN_STOCK_FILTER)
            else:
                outputs = outputs.exclude(StockModels.StockItem.IN_STOCK_FILTER)

        # Filter by 'complete' status
        complete = kwargs.get('complete', None)

        if complete is not None:
            if complete:
                outputs = outputs.filter(is_building=False)
            else:
                outputs = outputs.filter(is_building=True)

        return outputs

    @property
    def complete_outputs(self):
        """
        Return all the "completed" build outputs
        """

        outputs = self.get_build_outputs(complete=True)

        # TODO - Ordering?

        return outputs

    @property
    def incomplete_outputs(self):
        """
        Return all the "incomplete" build outputs
        """

        outputs = self.get_build_outputs(complete=False)

        # TODO - Order by how "complete" they are?

        return outputs

    @property
    def incomplete_count(self):
        """
        Return the total number of "incomplete" outputs
        """

        quantity = 0

        for output in self.incomplete_outputs:
            quantity += output.quantity

        return quantity

    @classmethod
    def getNextBuildNumber(cls):
        """
        Try to predict the next Build Order reference:
        """

        if cls.objects.count() == 0:
            return None

        build = cls.objects.last()
        ref = build.reference

        if not ref:
            return None

        tries = set()

        while 1:
            new_ref = increment(ref)

            if new_ref in tries:
                # We are potentially stuck in a loop - simply return the original reference
                return ref

            if cls.objects.filter(reference=new_ref).exists():
                tries.add(new_ref)
                new_ref = increment(new_ref)
            else:
                break

        return new_ref

    @property
    def can_complete(self):
        """
        Returns True if this build can be "completed"

        - Must not have any outstanding build outputs
        - 'completed' value must meet (or exceed) the 'quantity' value
        """

        if self.incomplete_count > 0:
            return False

        if self.completed < self.quantity:
            return False

        # No issues!
        return True

    @transaction.atomic
    def complete_build(self, user):
        """
        Mark this build as complete
        """

        if not self.can_complete:
            return

        self.completion_date = datetime.now().date()
        self.completed_by = user
        self.status = BuildStatus.COMPLETE
        self.save()

        # Ensure that there are no longer any BuildItem objects
        # which point to thie Build Order
        self.allocated_stock.all().delete()

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

    def getAutoAllocations(self, output):
        """
        Return a list of StockItem objects which will be allocated
        using the 'AutoAllocate' function.

        For each item in the BOM for the attached Part,
        the following tests must *all* evaluate to True,
        for the part to be auto-allocated:

        - The sub_item in the BOM line must *not* be trackable
        - There is only a single stock item available (which has not already been allocated to this build)
        - The stock item has an availability greater than zero
        
        Returns:
            A list object containing the StockItem objects to be allocated (and the quantities).
            Each item in the list is a dict as follows:
            {
                'stock_item': stock_item,
                'quantity': stock_quantity,
            }
        """

        allocations = []

        """
        Iterate through each item in the BOM
        """

        for bom_item in self.bom_items:

            part = bom_item.sub_part

            # Skip any parts which are already fully allocated
            if self.isPartFullyAllocated(part, output):
                continue

            # How many parts are required to complete the output?
            required = self.unallocatedQuantity(part, output)

            # Grab a list of stock items which are available
            stock_items = self.availableStockItems(part, output)

            # Ensure that the available stock items are in the correct location
            if self.take_from is not None:
                # Filter for stock that is located downstream of the designated location
                stock_items = stock_items.filter(location__in=[loc for loc in self.take_from.getUniqueChildren()])

            # Only one StockItem to choose from? Default to that one!
            if stock_items.count() == 1:
                stock_item = stock_items[0]

                # Double check that we have not already allocated this stock-item against this build
                build_items = BuildItem.objects.filter(
                    build=self,
                    stock_item=stock_item,
                    install_into=output
                )

                if len(build_items) > 0:
                    continue

                # How many items are actually available?
                if stock_item.quantity > 0:

                    # Only take as many as are available
                    if stock_item.quantity < required:
                        required = stock_item.quantity

                    allocation = {
                        'stock_item': stock_item,
                        'quantity': required,
                    }

                    allocations.append(allocation)

        return allocations

    @transaction.atomic
    def unallocateStock(self, output=None, part=None):
        """
        Deletes all stock allocations for this build.
        
        Args:
            output: Specify which build output to delete allocations (optional)

        """

        allocations = BuildItem.objects.filter(build=self.pk)

        if output:
            allocations = allocations.filter(install_into=output.pk)

        if part:
            allocations = allocations.filter(stock_item__part=part)

        # Remove all the allocations
        allocations.delete()

    @transaction.atomic
    def create_build_output(self, quantity, **kwargs):
        """
        Create a new build output against this BuildOrder.

        args:
            quantity: The quantity of the item to produce

        kwargs:
            batch: Override batch code
            serials: Serial numbers
            location: Override location
        """

        batch = kwargs.get('batch', self.batch)
        location = kwargs.get('location', self.destination)
        serials = kwargs.get('serials', None)

        """
        Determine if we can create a single output (with quantity > 0),
        or multiple outputs (with quantity = 1)
        """

        multiple = False

        # Serial numbers are provided? We need to split!
        if serials:
            multiple = True

        # BOM has trackable parts, so we must split!
        if self.part.has_trackable_parts:
            multiple = True

        if multiple:
            """
            Create multiple build outputs with a single quantity of 1
            """

            for ii in range(quantity):

                if serials:
                    serial = serials[ii]
                else:
                    serial = None

                StockModels.StockItem.objects.create(
                    quantity=1,
                    location=location,
                    part=self.part,
                    build=self,
                    batch=batch,
                    serial=serial,
                    is_building=True,
                )

        else:
            """
            Create a single build output of the given quantity
            """

            StockModels.StockItem.objects.create(
                quantity=quantity,
                location=location,
                part=self.part,
                build=self,
                batch=batch,
                is_building=True
            )

        if self.status == BuildStatus.PENDING:
            self.status = BuildStatus.PRODUCTION
            self.save()

    @transaction.atomic
    def deleteBuildOutput(self, output):
        """
        Remove a build output from the database:

        - Unallocate any build items against the output
        - Delete the output StockItem
        """

        if not output:
            raise ValidationError(_("No build output specified"))

        if not output.is_building:
            raise ValidationError(_("Build output is already completed"))

        if not output.build == self:
            raise ValidationError(_("Build output does not match Build Order"))

        # Unallocate all build items against the output
        self.unallocateStock(output)

        # Remove the build output from the database
        output.delete()

    @transaction.atomic
    def autoAllocate(self, output):
        """
        Run auto-allocation routine to allocate StockItems to this Build.

        Args:
            output: If specified, only auto-allocate against the given built output

        Returns a list of dict objects with keys like:

            {
                'stock_item': item,
                'quantity': quantity,
            }

        See: getAutoAllocations()
        """

        allocations = self.getAutoAllocations(output)

        for item in allocations:
            # Create a new allocation
            build_item = BuildItem(
                build=self,
                stock_item=item['stock_item'],
                quantity=item['quantity'],
                install_into=output,
            )

            build_item.save()

    @transaction.atomic
    def completeBuildOutput(self, output, user, **kwargs):
        """
        Complete a particular build output

        - Remove allocated StockItems
        - Mark the output as complete
        """

        # Select the location for the build output
        location = kwargs.get('location', self.destination)

        # List the allocated BuildItem objects for the given output
        allocated_items = output.items_to_install.all()

        for build_item in allocated_items:

            # TODO: This is VERY SLOW as each deletion from the database takes ~1 second to complete
            # TODO: Use celery / redis to offload the actual object deletion...
            # REF: https://www.botreetechnologies.com/blog/implementing-celery-using-django-for-background-task-processing
            # REF: https://code.tutsplus.com/tutorials/using-celery-with-django-for-background-task-processing--cms-28732

            # Complete the allocation of stock for that item
            build_item.complete_allocation(user)

        # Delete the BuildItem objects from the database
        allocated_items.all().delete()

        # Ensure that the output is updated correctly
        output.build = self
        output.is_building = False
        output.location = location

        output.save()

        output.addTransactionNote(
            _('Completed build output'),
            user,
            system=True
        )

        # Increase the completed quantity for this build
        self.completed += output.quantity
        self.save()

    def requiredQuantity(self, part, output):
        """
        Get the quantity of a part required to complete the particular build output.

        Args:
            part: The Part object
            output - The particular build output (StockItem)
        """

        # Extract the BOM line item from the database
        try:
            bom_item = PartModels.BomItem.objects.get(part=self.part.pk, sub_part=part.pk)
            quantity = bom_item.quantity
        except (PartModels.BomItem.DoesNotExist):
            quantity = 0

        if output:
            quantity *= output.quantity
        else:
            quantity *= self.remaining

        return quantity

    def allocatedItems(self, part, output):
        """
        Return all BuildItem objects which allocate stock of <part> to <output>

        Args:
            part - The part object
            output - Build output (StockItem).
        """

        allocations = BuildItem.objects.filter(
            build=self,
            stock_item__part=part,
            install_into=output,
        )

        return allocations

    def allocatedQuantity(self, part, output):
        """
        Return the total quantity of given part allocated to a given build output.
        """

        allocations = self.allocatedItems(part, output)

        allocated = allocations.aggregate(q=Coalesce(Sum('quantity'), 0))

        return allocated['q']

    def unallocatedQuantity(self, part, output):
        """
        Return the total unallocated (remaining) quantity of a part against a particular output.
        """

        required = self.requiredQuantity(part, output)
        allocated = self.allocatedQuantity(part, output)

        return max(required - allocated, 0)

    def isPartFullyAllocated(self, part, output):
        """
        Returns True if the part has been fully allocated to the particular build output
        """

        return self.unallocatedQuantity(part, output) == 0

    def isFullyAllocated(self, output):
        """
        Returns True if the particular build output is fully allocated.
        """

        for bom_item in self.bom_items:
            part = bom_item.sub_part

            if not self.isPartFullyAllocated(part, output):
                return False

        # All parts must be fully allocated!
        return True

    def allocatedParts(self, output):
        """
        Return a list of parts which have been fully allocated against a particular output
        """

        allocated = []

        for bom_item in self.bom_items:
            part = bom_item.sub_part

            if self.isPartFullyAllocated(part, output):
                allocated.append(part)

        return allocated

    def unallocatedParts(self, output):
        """
        Return a list of parts which have *not* been fully allocated against a particular output
        """

        unallocated = []

        for bom_item in self.bom_items:
            part = bom_item.sub_part

            if not self.isPartFullyAllocated(part, output):
                unallocated.append(part)

        return unallocated

    @property
    def required_parts(self):
        """ Returns a dict of parts required to build this part (BOM) """
        parts = []

        for item in self.part.bom_items.all().prefetch_related('sub_part'):
            parts.append(item.sub_part)

        return parts

    def availableStockItems(self, part, output):
        """
        Returns stock items which are available for allocation to this build.

        Args:
            part - Part object
            output - The particular build output
        """

        # Grab initial query for items which are "in stock" and match the part
        items = StockModels.StockItem.objects.filter(
            StockModels.StockItem.IN_STOCK_FILTER
        )

        items = items.filter(part=part)

        # Exclude any items which have already been allocated
        allocated = BuildItem.objects.filter(
            build=self,
            stock_item__part=part,
            install_into=output,
        )

        items = items.exclude(
            id__in=[item.stock_item.id for item in allocated.all()]
        )

        # Limit query to stock items which are "downstream" of the source location
        if self.take_from is not None:
            items = items.filter(
                location__in=[loc for loc in self.take_from.getUniqueChildren()]
            )

        # Exclude expired stock items
        if not common.models.InvenTreeSetting.get_setting('STOCK_ALLOW_EXPIRED_BUILD'):
            items = items.exclude(StockModels.StockItem.EXPIRED_FILTER)

        return items

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


class BuildOrderAttachment(InvenTreeAttachment):
    """
    Model for storing file attachments against a BuildOrder object
    """

    def getSubdir(self):
        return os.path.join('bo_files', str(self.build.id))

    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name='attachments')


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
            ('build', 'stock_item', 'install_into'),
        ]

    def save(self, *args, **kwargs):

        self.validate_unique()
        self.clean()

        super().save()

    def validate_unique(self, exclude=None):
        """
        Test that this BuildItem object is "unique".
        Essentially we do not want a stock_item being allocated to a Build multiple times.
        """

        super().validate_unique(exclude)

        items = BuildItem.objects.exclude(id=self.id).filter(
            build=self.build,
            stock_item=self.stock_item,
            install_into=self.install_into
        )

        if items.exists():
            msg = _("BuildItem must be unique for build, stock_item and install_into")
            raise ValidationError({
                'build': msg,
                'stock_item': msg,
                'install_into': msg
            })

    def clean(self):
        """ Check validity of the BuildItem model.
        The following checks are performed:

        - StockItem.part must be in the BOM of the Part object referenced by Build
        - Allocation quantity cannot exceed available quantity
        """

        self.validate_unique()
        
        super().clean()

        errors = {}

        if not self.install_into:
            raise ValidationError(_('Build item must specify a build output'))

        try:
            # Allocated part must be in the BOM for the master part
            if self.stock_item.part not in self.build.part.getRequiredParts(recursive=False):
                errors['stock_item'] = [_("Selected stock item not found in BOM for part '{p}'".format(p=self.build.part.full_name))]
            
            # Allocated quantity cannot exceed available stock quantity
            if self.quantity > self.stock_item.quantity:
                errors['quantity'] = [_("Allocated quantity ({n}) must not exceed available quantity ({q})".format(
                    n=normalize(self.quantity),
                    q=normalize(self.stock_item.quantity)
                ))]

            # Allocated quantity cannot cause the stock item to be over-allocated
            if self.stock_item.quantity - self.stock_item.allocation_count() + self.quantity < self.quantity:
                errors['quantity'] = _('StockItem is over-allocated')

            # Allocated quantity must be positive
            if self.quantity <= 0:
                errors['quantity'] = _('Allocation quantity must be greater than zero')

            # Quantity must be 1 for serialized stock
            if self.stock_item.serialized and not self.quantity == 1:
                errors['quantity'] = _('Quantity must be 1 for serialized stock')

        except (StockModels.StockItem.DoesNotExist, PartModels.Part.DoesNotExist):
            pass

        if len(errors) > 0:
            raise ValidationError(errors)

    @transaction.atomic
    def complete_allocation(self, user):
        """
        Complete the allocation of this BuildItem into the output stock item.

        - If the referenced part is trackable, the stock item will be *installed* into the build output
        - If the referenced part is *not* trackable, the stock item will be removed from stock
        """

        item = self.stock_item

        # For a trackable part, special consideration needed!
        if item.part.trackable:
            # Split the allocated stock if there are more available than allocated
            if item.quantity > self.quantity:
                item = item.splitStock(self.quantity, None, user)

                # Make sure we are pointing to the new item
                self.stock_item = item
                self.save()

            # Install the stock item into the output
            item.belongs_to = self.install_into
            item.save()
        else:
            # Simply remove the items from stock
            item.take_stock(self.quantity, user)

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
        help_text=_('Source stock item'),
        limit_choices_to={
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

    install_into = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='items_to_install',
        help_text=_('Destination stock item'),
        limit_choices_to={
            'is_building': True,
        }
    )
