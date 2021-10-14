"""
Build database model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import decimal

import os
from datetime import datetime

from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from django.urls import reverse
from django.db import models, transaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.core.validators import MinValueValidator

from markdownx.models import MarkdownxField

from mptt.models import MPTTModel, TreeForeignKey
from mptt.exceptions import InvalidMove

from InvenTree.status_codes import BuildStatus, StockStatus, StockHistoryCode
from InvenTree.helpers import increment, getSetting, normalize, MakeBarcode
from InvenTree.validators import validate_build_order_reference
from InvenTree.models import InvenTreeAttachment

import common.models

import InvenTree.fields
import InvenTree.helpers

from stock import models as StockModels
from part import models as PartModels
from users import models as UserModels


def get_next_build_number():
    """
    Returns the next available BuildOrder reference number
    """

    if Build.objects.count() == 0:
        return

    build = Build.objects.exclude(reference=None).last()

    attempts = set([build.reference])

    reference = build.reference

    while 1:
        reference = increment(reference)

        if reference in attempts:
            # Escape infinite recursion
            return reference

        if Build.objects.filter(reference=reference).exists():
            attempts.add(reference)
        else:
            break
    
    return reference


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
        completed_by: User that completed the build
        issued_by: User that issued the build
        responsible: User (or group) responsible for completing the build
    """

    OVERDUE_FILTER = Q(status__in=BuildStatus.ACTIVE_CODES) & ~Q(target_date=None) & Q(target_date__lte=datetime.now().date())
    
    @staticmethod
    def get_api_url():
        return reverse('api-build-list')

    def api_instance_filters(self):

        return {
            'parent': {
                'exclude_tree': self.pk,
            }
        }

    def save(self, *args, **kwargs):

        try:
            super().save(*args, **kwargs)
        except InvalidMove:
            raise ValidationError({
                'parent': _('Invalid choice for parent build'),
            })

    class Meta:
        verbose_name = _("Build Order")
        verbose_name_plural = _("Build Orders")

    def format_barcode(self, **kwargs):
        """
        Return a JSON string to represent this build as a barcode
        """

        return MakeBarcode(
            "buildorder",
            self.pk,
            {
                "reference": self.title,
                "url": self.get_absolute_url(),
            }
        )

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
        default=get_next_build_number,
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

    creation_date = models.DateField(auto_now_add=True, editable=False, verbose_name=_('Creation Date'))

    target_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Target completion date'),
        help_text=_('Target date for build completion. Build will be overdue after this date.')
    )

    completion_date = models.DateField(null=True, blank=True, verbose_name=_('Completion Date'))

    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('completed by'),
        related_name='builds_completed'
    )

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Issued by'),
        help_text=_('User who issued this build order'),
        related_name='builds_issued',
    )

    responsible = models.ForeignKey(
        UserModels.Owner,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Responsible'),
        help_text=_('User responsible for this build order'),
        related_name='builds_responsible',
    )

    link = InvenTree.fields.InvenTreeURLField(
        verbose_name=_('External Link'),
        blank=True, help_text=_('Link to external URL')
    )

    notes = MarkdownxField(
        verbose_name=_('Notes'),
        blank=True, help_text=_('Extra build notes')
    )

    def sub_builds(self, cascade=True):
        """
        Return all Build Order objects under this one.
        """

        if cascade:
            return Build.objects.filter(parent=self.pk)
        else:
            descendants = self.get_descendants(include_self=True)
            Build.objects.filter(parent__pk__in=[d.pk for d in descendants])

    def sub_build_count(self, cascade=True):
        """
        Return the number of sub builds under this one.

        Args:
            cascade: If True (defualt), include cascading builds under sub builds
        """

        return self.sub_builds(cascade=cascade).count()

    @property
    def is_overdue(self):
        """
        Returns true if this build is "overdue":

        Makes use of the OVERDUE_FILTER to avoid code duplication
        """

        query = Build.objects.filter(pk=self.pk)
        query = query.filter(Build.OVERDUE_FILTER)

        return query.exists()

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
    def tracked_bom_items(self):
        """
        Returns the "trackable" BOM items for this BuildOrder
        """

        items = self.bom_items
        items = items.filter(sub_part__trackable=True)

        return items

    def has_tracked_bom_items(self):
        """
        Returns True if this BuildOrder has trackable BomItems
        """

        return self.tracked_bom_items.count() > 0

    @property
    def untracked_bom_items(self):
        """
        Returns the "non trackable" BOM items for this BuildOrder
        """

        items = self.bom_items
        items = items.filter(sub_part__trackable=False)

        return items

    def has_untracked_bom_items(self):
        """
        Returns True if this BuildOrder has non trackable BomItems
        """

        return self.untracked_bom_items.count() > 0

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

        # Extract the "most recent" build order reference
        builds = cls.objects.exclude(reference=None)

        if not builds.exists():
            return None

        build = builds.last()
        ref = build.reference

        if not ref:
            return None

        tries = set(ref)

        new_ref = ref

        while 1:
            new_ref = increment(new_ref)

            if new_ref in tries:
                # We are potentially stuck in a loop - simply return the original reference
                return ref

            # Check if the existing build reference exists
            if cls.objects.filter(reference=new_ref).exists():
                tries.add(new_ref)
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

        if not self.areUntrackedPartsFullyAllocated():
            return False

        # No issues!
        return True

    @transaction.atomic
    def complete_build(self, user):
        """
        Mark this build as complete
        """

        if self.incomplete_count > 0:
            return

        self.completion_date = datetime.now().date()
        self.completed_by = user
        self.status = BuildStatus.COMPLETE
        self.save()

        # Remove untracked allocated stock
        self.subtractUntrackedStock(user)

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

    @transaction.atomic
    def unallocateStock(self, bom_item=None, output=None):
        """
        Unallocate stock from this Build

        arguments:
            - bom_item: Specify a particular BomItem to unallocate stock against
            - output: Specify a particular StockItem (output) to unallocate stock against
        """

        allocations = BuildItem.objects.filter(
            build=self,
            install_into=output
        )

        if bom_item:
            allocations = allocations.filter(bom_item=bom_item)

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
        self.unallocateStock(output=output)

        # Remove the build output from the database
        output.delete()

    @transaction.atomic
    def subtractUntrackedStock(self, user):
        """
        Called when the Build is marked as "complete",
        this function removes the allocated untracked items from stock.
        """

        items = self.allocated_stock.filter(
            stock_item__part__trackable=False
        )

        # Remove stock
        for item in items:
            item.complete_allocation(user)

        # Delete allocation
        items.all().delete()

    @transaction.atomic
    def completeBuildOutput(self, output, user, **kwargs):
        """
        Complete a particular build output

        - Remove allocated StockItems
        - Mark the output as complete
        """

        # Select the location for the build output
        location = kwargs.get('location', self.destination)
        status = kwargs.get('status', StockStatus.OK)
        notes = kwargs.get('notes', '')

        # List the allocated BuildItem objects for the given output
        allocated_items = output.items_to_install.all()

        for build_item in allocated_items:

            # TODO: This is VERY SLOW as each deletion from the database takes ~1 second to complete
            # TODO: Use the background worker process to handle this task!

            # Complete the allocation of stock for that item
            build_item.complete_allocation(user)

        # Delete the BuildItem objects from the database
        allocated_items.all().delete()

        # Ensure that the output is updated correctly
        output.build = self
        output.is_building = False
        output.location = location
        output.status = status

        output.save()

        output.add_tracking_entry(
            StockHistoryCode.BUILD_OUTPUT_COMPLETED,
            user,
            notes=notes,
            deltas={
                'status': status,
            }
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
            quantity *= self.quantity

        return quantity

    def allocatedItems(self, part, output):
        """
        Return all BuildItem objects which allocate stock of <part> to <output>

        Args:
            part - The part object
            output - Build output (StockItem).
        """

        # Remember, if 'variant' stock is allowed to be allocated, it becomes more complicated!
        variants = part.get_descendants(include_self=True)

        allocations = BuildItem.objects.filter(
            build=self,
            stock_item__part__pk__in=[p.pk for p in variants],
            install_into=output,
        )

        return allocations

    def allocatedQuantity(self, part, output):
        """
        Return the total quantity of given part allocated to a given build output.
        """

        allocations = self.allocatedItems(part, output)

        allocated = allocations.aggregate(
            q=Coalesce(
                Sum('quantity'),
                0,
                output_field=models.DecimalField(),
            )
        )

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

    def isFullyAllocated(self, output, verbose=False):
        """
        Returns True if the particular build output is fully allocated.
        """

        # If output is not specified, we are talking about "untracked" items
        if output is None:
            bom_items = self.untracked_bom_items
        else:
            bom_items = self.tracked_bom_items

        fully_allocated = True

        for bom_item in bom_items:
            part = bom_item.sub_part

            if not self.isPartFullyAllocated(part, output):
                fully_allocated = False

                if verbose:
                    print(f"Part {part} is not fully allocated for output {output}")
                else:
                    break

        # All parts must be fully allocated!
        return fully_allocated

    def areUntrackedPartsFullyAllocated(self):
        """
        Returns True if the un-tracked parts are fully allocated for this BuildOrder
        """

        return self.isFullyAllocated(None)

    def allocatedParts(self, output):
        """
        Return a list of parts which have been fully allocated against a particular output
        """

        allocated = []

        # If output is not specified, we are talking about "untracked" items
        if output is None:
            bom_items = self.untracked_bom_items
        else:
            bom_items = self.tracked_bom_items

        for bom_item in bom_items:
            part = bom_item.sub_part

            if self.isPartFullyAllocated(part, output):
                allocated.append(part)

        return allocated

    def unallocatedParts(self, output):
        """
        Return a list of parts which have *not* been fully allocated against a particular output
        """

        unallocated = []

        # If output is not specified, we are talking about "untracked" items
        if output is None:
            bom_items = self.untracked_bom_items
        else:
            bom_items = self.tracked_bom_items

        for bom_item in bom_items:
            part = bom_item.sub_part

            if not self.isPartFullyAllocated(part, output):
                unallocated.append(part)

        return unallocated

    @property
    def required_parts(self):
        """ Returns a list of parts required to build this part (BOM) """
        parts = []

        for item in self.bom_items:
            parts.append(item.sub_part)

        return parts

    @property
    def required_parts_to_complete_build(self):
        """ Returns a list of parts required to complete the full build """
        parts = []

        for bom_item in self.bom_items:
            # Get remaining quantity needed
            required_quantity_to_complete_build = self.remaining * bom_item.quantity
            # Compare to net stock
            if bom_item.sub_part.net_stock < required_quantity_to_complete_build:
                parts.append(bom_item.sub_part)

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

        # Check if variants are allowed for this part
        try:
            bom_item = PartModels.BomItem.objects.get(part=self.part, sub_part=part)
            allow_part_variants = bom_item.allow_variants
        except PartModels.BomItem.DoesNotExist:
            allow_part_variants = False

        if allow_part_variants:
            parts = part.get_descendants(include_self=True)
            items = items.filter(part__pk__in=[p.pk for p in parts])

        else:
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
        bom_item: Link to a BomItem object (may or may not point to the same part as the build)
        stock_item: Link to a StockItem object
        quantity: Number of units allocated
        install_into: Destination stock item (or None)
    """

    @staticmethod
    def get_api_url():
        return reverse('api-build-item-list')

    def get_absolute_url(self):
        # TODO - Fix!
        return '/build/item/{pk}/'.format(pk=self.id)
        # return reverse('build-detail', kwargs={'pk': self.id})

    class Meta:
        unique_together = [
            ('build', 'stock_item', 'install_into'),
        ]

    def save(self, *args, **kwargs):

        self.clean()

        super().save()

    def clean(self):
        """
        Check validity of this BuildItem instance.
        The following checks are performed:

        - StockItem.part must be in the BOM of the Part object referenced by Build
        - Allocation quantity cannot exceed available quantity
        """

        self.validate_unique()

        super().clean()

        try:

            # If the 'part' is trackable, then the 'install_into' field must be set!
            if self.stock_item.part and self.stock_item.part.trackable and not self.install_into:
                raise ValidationError(_('Build item must specify a build output, as master part is marked as trackable'))

            # Allocated quantity cannot exceed available stock quantity
            if self.quantity > self.stock_item.quantity:

                q = normalize(self.quantity)
                a = normalize(self.stock_item.quantity)

                raise ValidationError({
                    'quantity': _(f'Allocated quantity ({q}) must not execed available stock quantity ({a})')
                })

            # Allocated quantity cannot cause the stock item to be over-allocated
            available = decimal.Decimal(self.stock_item.quantity)
            allocated = decimal.Decimal(self.stock_item.allocation_count())
            quantity = decimal.Decimal(self.quantity)

            if available - allocated + quantity < quantity:
                raise ValidationError({
                    'quantity': _('Stock item is over-allocated')
                })

            # Allocated quantity must be positive
            if self.quantity <= 0:
                raise ValidationError({
                    'quantity': _('Allocation quantity must be greater than zero'),
                })

            # Quantity must be 1 for serialized stock
            if self.stock_item.serialized and not self.quantity == 1:
                raise ValidationError({
                    'quantity': _('Quantity must be 1 for serialized stock')
                })

        except (StockModels.StockItem.DoesNotExist, PartModels.Part.DoesNotExist):
            pass

        """
        Attempt to find the "BomItem" which links this BuildItem to the build.

        - If a BomItem is already set, and it is valid, then we are ok!
        """

        bom_item_valid = False

        if self.bom_item:
            """
            A BomItem object has already been assigned. This is valid if:

            a) It points to the same "part" as the referenced build
            b) Either:
                i) The sub_part points to the same part as the referenced StockItem
                ii) The BomItem allows variants and the part referenced by the StockItem
                    is a variant of the sub_part referenced by the BomItem
                iii) The Part referenced by the StockItem is a valid substitute for the BomItem
            """

            if self.build and self.build.part == self.bom_item.part:

                bom_item_valid = self.bom_item.is_stock_item_valid(self.stock_item)

        # If the existing BomItem is *not* valid, try to find a match
        if not bom_item_valid:

            if self.build and self.stock_item:
                ancestors = self.stock_item.part.get_ancestors(include_self=True, ascending=True)

                for idx, ancestor in enumerate(ancestors):

                    try:
                        bom_item = PartModels.BomItem.objects.get(part=self.build.part, sub_part=ancestor)
                    except PartModels.BomItem.DoesNotExist:
                        continue
                    
                    # A matching BOM item has been found!
                    if idx == 0 or bom_item.allow_variants:
                        bom_item_valid = True
                        self.bom_item = bom_item
                        break

        # BomItem did not exist or could not be validated.
        # Search for a new one
        if not bom_item_valid:

            raise ValidationError({
                'stock_item': _("Selected stock item not found in BOM")
            })

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

    def getStockItemThumbnail(self):
        """
        Return qualified URL for part thumbnail image
        """

        thumb_url = None

        if self.stock_item and self.stock_item.part:
            try:
                # Try to extract the thumbnail
                thumb_url = self.stock_item.part.image.thumbnail.url
            except:
                pass
        
        if thumb_url is None and self.bom_item and self.bom_item.sub_part:
            try:
                thumb_url = self.bom_item.sub_part.image.thumbnail.url
            except:
                pass

        if thumb_url is not None:
            return InvenTree.helpers.getMediaUrl(thumb_url)
        else:
            return InvenTree.helpers.getBlankThumbnail()

    build = models.ForeignKey(
        Build,
        on_delete=models.CASCADE,
        related_name='allocated_stock',
        verbose_name=_('Build'),
        help_text=_('Build to allocate parts')
    )

    # Internal model which links part <-> sub_part
    # We need to track this separately, to allow for "variant' stock
    bom_item = models.ForeignKey(
        PartModels.BomItem,
        on_delete=models.CASCADE,
        related_name='allocate_build_items',
        blank=True, null=True,
    )

    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='allocations',
        verbose_name=_('Stock Item'),
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
        verbose_name=_('Quantity'),
        help_text=_('Stock quantity to allocate to build')
    )

    install_into = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='items_to_install',
        verbose_name=_('Install into'),
        help_text=_('Destination stock item'),
        limit_choices_to={
            'is_building': True,
        }
    )
