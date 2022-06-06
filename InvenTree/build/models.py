"""Build database model definitions."""

import decimal

import os
from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from markdownx.models import MarkdownxField

from mptt.models import MPTTModel, TreeForeignKey
from mptt.exceptions import InvalidMove

from rest_framework import serializers

from InvenTree.status_codes import BuildStatus, StockStatus, StockHistoryCode
from InvenTree.helpers import increment, getSetting, normalize, MakeBarcode
from InvenTree.models import InvenTreeAttachment, ReferenceIndexingMixin
from InvenTree.validators import validate_build_order_reference

import common.notifications
import InvenTree.fields
import InvenTree.helpers
import InvenTree.tasks

from plugin.events import trigger_event

from part import models as PartModels
from stock import models as StockModels
from users import models as UserModels


def get_next_build_number():
    """Returns the next available BuildOrder reference number."""
    if Build.objects.count() == 0:
        return '0001'

    build = Build.objects.exclude(reference=None).last()

    attempts = {build.reference}

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


class Build(MPTTModel, ReferenceIndexingMixin):
    """A Build object organises the creation of new StockItem objects from other existing StockItem objects.

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
        """Return the API URL associated with the BuildOrder model"""
        return reverse('api-build-list')

    def api_instance_filters(self):
        """Returns custom API filters for the particular BuildOrder instance"""
        return {
            'parent': {
                'exclude_tree': self.pk,
            }
        }

    @classmethod
    def api_defaults(cls, request):
        """Return default values for this model when issuing an API OPTIONS request."""
        defaults = {
            'reference': get_next_build_number(),
        }

        if request and request.user:
            defaults['issued_by'] = request.user.pk

        return defaults

    def save(self, *args, **kwargs):
        """Custom save method for the BuildOrder model"""
        self.rebuild_reference_field()

        try:
            super().save(*args, **kwargs)
        except InvalidMove:
            raise ValidationError({
                'parent': _('Invalid choice for parent build'),
            })

    class Meta:
        """Metaclass options for the BuildOrder model"""
        verbose_name = _("Build Order")
        verbose_name_plural = _("Build Orders")

    def format_barcode(self, **kwargs):
        """Return a JSON string to represent this build as a barcode."""
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
        """Filter by 'minimum and maximum date range'.

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
        """String representation of a BuildOrder"""
        prefix = getSetting("BUILDORDER_REFERENCE_PREFIX")

        return f"{prefix}{self.reference}"

    def get_absolute_url(self):
        """Return the web URL associated with this BuildOrder"""
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
        """Return all Build Order objects under this one."""
        if cascade:
            return Build.objects.filter(parent=self.pk)
        else:
            descendants = self.get_descendants(include_self=True)
            Build.objects.filter(parent__pk__in=[d.pk for d in descendants])

    def sub_build_count(self, cascade=True):
        """Return the number of sub builds under this one.

        Args:
            cascade: If True (defualt), include cascading builds under sub builds
        """
        return self.sub_builds(cascade=cascade).count()

    @property
    def is_overdue(self):
        """Returns true if this build is "overdue".

        Makes use of the OVERDUE_FILTER to avoid code duplication

        Returns:
            bool: Is the build overdue
        """
        query = Build.objects.filter(pk=self.pk)
        query = query.filter(Build.OVERDUE_FILTER)

        return query.exists()

    @property
    def active(self):
        """Return True if this build is active."""
        return self.status in BuildStatus.ACTIVE_CODES

    @property
    def bom_items(self):
        """Returns the BOM items for the part referenced by this BuildOrder."""
        return self.part.get_bom_items()

    @property
    def tracked_bom_items(self):
        """Returns the "trackable" BOM items for this BuildOrder."""
        items = self.bom_items
        items = items.filter(sub_part__trackable=True)

        return items

    def has_tracked_bom_items(self):
        """Returns True if this BuildOrder has trackable BomItems."""
        return self.tracked_bom_items.count() > 0

    @property
    def untracked_bom_items(self):
        """Returns the "non trackable" BOM items for this BuildOrder."""
        items = self.bom_items
        items = items.filter(sub_part__trackable=False)

        return items

    def has_untracked_bom_items(self):
        """Returns True if this BuildOrder has non trackable BomItems."""
        return self.untracked_bom_items.count() > 0

    @property
    def remaining(self):
        """Return the number of outputs remaining to be completed."""
        return max(0, self.quantity - self.completed)

    @property
    def output_count(self):
        """Return the number of build outputs (StockItem) associated with this build order"""
        return self.build_outputs.count()

    def has_build_outputs(self):
        """Returns True if this build has more than zero build outputs"""
        return self.output_count > 0

    def get_build_outputs(self, **kwargs):
        """Return a list of build outputs.

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
        """Return all the "completed" build outputs."""
        outputs = self.get_build_outputs(complete=True)

        return outputs

    @property
    def complete_count(self):
        """Return the total quantity of completed outputs"""
        quantity = 0

        for output in self.complete_outputs:
            quantity += output.quantity

        return quantity

    @property
    def incomplete_outputs(self):
        """Return all the "incomplete" build outputs."""
        outputs = self.get_build_outputs(complete=False)

        return outputs

    @property
    def incomplete_count(self):
        """Return the total number of "incomplete" outputs."""
        quantity = 0

        for output in self.incomplete_outputs:
            quantity += output.quantity

        return quantity

    @classmethod
    def getNextBuildNumber(cls):
        """Try to predict the next Build Order reference."""
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
        """Returns True if this build can be "completed".

        - Must not have any outstanding build outputs
        - 'completed' value must meet (or exceed) the 'quantity' value
        """
        if self.incomplete_count > 0:
            return False

        if self.remaining > 0:
            return False

        if not self.are_untracked_parts_allocated():
            return False

        # No issues!
        return True

    @transaction.atomic
    def complete_build(self, user):
        """Mark this build as complete."""
        if self.incomplete_count > 0:
            return

        self.completion_date = datetime.now().date()
        self.completed_by = user
        self.status = BuildStatus.COMPLETE
        self.save()

        # Remove untracked allocated stock
        self.subtract_allocated_stock(user)

        # Ensure that there are no longer any BuildItem objects
        # which point to thisFcan Build Order
        self.allocated_stock.all().delete()

        # Register an event
        trigger_event('build.completed', id=self.pk)

    @transaction.atomic
    def cancel_build(self, user, **kwargs):
        """Mark the Build as CANCELLED.

        - Delete any pending BuildItem objects (but do not remove items from stock)
        - Set build status to CANCELLED
        - Save the Build object
        """
        remove_allocated_stock = kwargs.get('remove_allocated_stock', False)
        remove_incomplete_outputs = kwargs.get('remove_incomplete_outputs', False)

        # Handle stock allocations
        for build_item in self.allocated_stock.all():

            if remove_allocated_stock:
                build_item.complete_allocation(user)

            build_item.delete()

        # Remove incomplete outputs (if required)
        if remove_incomplete_outputs:
            outputs = self.build_outputs.filter(is_building=True)

            for output in outputs:
                output.delete()

        # Date of 'completion' is the date the build was cancelled
        self.completion_date = datetime.now().date()
        self.completed_by = user

        self.status = BuildStatus.CANCELLED
        self.save()

        trigger_event('build.cancelled', id=self.pk)

    @transaction.atomic
    def unallocateStock(self, bom_item=None, output=None):
        """Unallocate stock from this Build.

        Args:
            bom_item: Specify a particular BomItem to unallocate stock against
            output: Specify a particular StockItem (output) to unallocate stock against
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
        """Create a new build output against this BuildOrder.

        Args:
            quantity: The quantity of the item to produce

        Kwargs:
            batch: Override batch code
            serials: Serial numbers
            location: Override location
            auto_allocate: Automatically allocate stock with matching serial numbers
        """
        batch = kwargs.get('batch', self.batch)
        location = kwargs.get('location', self.destination)
        serials = kwargs.get('serials', None)
        auto_allocate = kwargs.get('auto_allocate', False)

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
            """Create multiple build outputs with a single quantity of 1."""

            # Quantity *must* be an integer at this point!
            quantity = int(quantity)

            for ii in range(quantity):

                if serials:
                    serial = serials[ii]
                else:
                    serial = None

                output = StockModels.StockItem.objects.create(
                    quantity=1,
                    location=location,
                    part=self.part,
                    build=self,
                    batch=batch,
                    serial=serial,
                    is_building=True,
                )

                if auto_allocate and serial is not None:

                    # Get a list of BomItem objects which point to "trackable" parts

                    for bom_item in self.part.get_trackable_parts():

                        parts = bom_item.get_valid_parts_for_allocation()

                        for part in parts:

                            items = StockModels.StockItem.objects.filter(
                                part=part,
                                serial=str(serial),
                                quantity=1,
                            ).filter(StockModels.StockItem.IN_STOCK_FILTER)

                            """
                            Test if there is a matching serial number!
                            """
                            if items.exists() and items.count() == 1:
                                stock_item = items[0]

                                # Allocate the stock item
                                BuildItem.objects.create(
                                    build=self,
                                    bom_item=bom_item,
                                    stock_item=stock_item,
                                    quantity=1,
                                    install_into=output,
                                )

        else:
            """Create a single build output of the given quantity."""

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
    def delete_output(self, output):
        """Remove a build output from the database.

        Executes:
        - Unallocate any build items against the output
        - Delete the output StockItem
        """
        if not output:
            raise ValidationError(_("No build output specified"))

        if not output.is_building:
            raise ValidationError(_("Build output is already completed"))

        if output.build != self:
            raise ValidationError(_("Build output does not match Build Order"))

        # Unallocate all build items against the output
        self.unallocateStock(output=output)

        # Remove the build output from the database
        output.delete()

    @transaction.atomic
    def subtract_allocated_stock(self, user):
        """Called when the Build is marked as "complete", this function removes the allocated untracked items from stock."""
        items = self.allocated_stock.filter(
            stock_item__part__trackable=False
        )

        # Remove stock
        for item in items:
            item.complete_allocation(user)

        # Delete allocation
        items.all().delete()

    @transaction.atomic
    def complete_build_output(self, output, user, **kwargs):
        """Complete a particular build output.

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

    @transaction.atomic
    def auto_allocate_stock(self, **kwargs):
        """Automatically allocate stock items against this build order.

        Following a number of 'guidelines':
        - Only "untracked" BOM items are considered (tracked BOM items must be manually allocated)
        - If a particular BOM item is already fully allocated, it is skipped
        - Extract all available stock items for the BOM part
            - If variant stock is allowed, extract stock for those too
            - If substitute parts are available, extract stock for those also
        - If a single stock item is found, we can allocate that and move on!
        - If multiple stock items are found, we *may* be able to allocate:
            - If the calling function has specified that items are interchangeable
        """
        location = kwargs.get('location', None)
        exclude_location = kwargs.get('exclude_location', None)
        interchangeable = kwargs.get('interchangeable', False)
        substitutes = kwargs.get('substitutes', True)

        # Get a list of all 'untracked' BOM items
        for bom_item in self.untracked_bom_items:

            variant_parts = bom_item.sub_part.get_descendants(include_self=False)

            unallocated_quantity = self.unallocated_quantity(bom_item)

            if unallocated_quantity <= 0:
                # This BomItem is fully allocated, we can continue
                continue

            # Check which parts we can "use" (may include variants and substitutes)
            available_parts = bom_item.get_valid_parts_for_allocation(
                allow_variants=True,
                allow_substitutes=substitutes,
            )

            # Look for available stock items
            available_stock = StockModels.StockItem.objects.filter(StockModels.StockItem.IN_STOCK_FILTER)

            # Filter by list of available parts
            available_stock = available_stock.filter(
                part__in=[p for p in available_parts],
            )

            # Filter out "serialized" stock items, these cannot be auto-allocated
            available_stock = available_stock.filter(Q(serial=None) | Q(serial=''))

            if location:
                # Filter only stock items located "below" the specified location
                sublocations = location.get_descendants(include_self=True)
                available_stock = available_stock.filter(location__in=[loc for loc in sublocations])

            if exclude_location:
                # Exclude any stock items from the provided location
                sublocations = exclude_location.get_descendants(include_self=True)
                available_stock = available_stock.exclude(location__in=[loc for loc in sublocations])

            """
            Next, we sort the available stock items with the following priority:
            1. Direct part matches (+1)
            2. Variant part matches (+2)
            3. Substitute part matches (+3)

            This ensures that allocation priority is first given to "direct" parts
            """
            def stock_sort(item):
                if item.part == bom_item.sub_part:
                    return 1
                elif item.part in variant_parts:
                    return 2
                else:
                    return 3

            available_stock = sorted(available_stock, key=stock_sort)

            if len(available_stock) == 0:
                # No stock items are available
                continue
            elif len(available_stock) == 1 or interchangeable:
                # Either there is only a single stock item available,
                # or all items are "interchangeable" and we don't care where we take stock from

                for stock_item in available_stock:
                    # How much of the stock item is "available" for allocation?
                    quantity = min(unallocated_quantity, stock_item.unallocated_quantity())

                    if quantity > 0:

                        try:
                            BuildItem.objects.create(
                                build=self,
                                bom_item=bom_item,
                                stock_item=stock_item,
                                quantity=quantity,
                            )

                            # Subtract the required quantity
                            unallocated_quantity -= quantity

                        except (ValidationError, serializers.ValidationError) as exc:
                            # Catch model errors and re-throw as DRF errors
                            raise ValidationError(detail=serializers.as_serializer_error(exc))

                    if unallocated_quantity <= 0:
                        # We have now fully-allocated this BomItem - no need to continue!
                        break

    def required_quantity(self, bom_item, output=None):
        """Get the quantity of a part required to complete the particular build output.

        Args:
            bom_item: The Part object
            output: The particular build output (StockItem)
        """
        quantity = bom_item.quantity

        if output:
            quantity *= output.quantity
        else:
            quantity *= self.quantity

        return quantity

    def allocated_bom_items(self, bom_item, output=None):
        """Return all BuildItem objects which allocate stock of <bom_item> to <output>.

        Note that the bom_item may allow variants, or direct substitutes,
        making things difficult.

        Args:
            bom_item: The BomItem object
            output: Build output (StockItem).
        """
        allocations = BuildItem.objects.filter(
            build=self,
            bom_item=bom_item,
            install_into=output,
        )

        return allocations

    def allocated_quantity(self, bom_item, output=None):
        """Return the total quantity of given part allocated to a given build output."""
        allocations = self.allocated_bom_items(bom_item, output)

        allocated = allocations.aggregate(
            q=Coalesce(
                Sum('quantity'),
                0,
                output_field=models.DecimalField(),
            )
        )

        return allocated['q']

    def unallocated_quantity(self, bom_item, output=None):
        """Return the total unallocated (remaining) quantity of a part against a particular output."""
        required = self.required_quantity(bom_item, output)
        allocated = self.allocated_quantity(bom_item, output)

        return max(required - allocated, 0)

    def is_bom_item_allocated(self, bom_item, output=None):
        """Test if the supplied BomItem has been fully allocated!"""
        return self.unallocated_quantity(bom_item, output) == 0

    def is_fully_allocated(self, output):
        """Returns True if the particular build output is fully allocated."""
        # If output is not specified, we are talking about "untracked" items
        if output is None:
            bom_items = self.untracked_bom_items
        else:
            bom_items = self.tracked_bom_items

        for bom_item in bom_items:

            if not self.is_bom_item_allocated(bom_item, output):
                return False

        # All parts must be fully allocated!
        return True

    def is_partially_allocated(self, output):
        """Returns True if the particular build output is (at least) partially allocated."""
        # If output is not specified, we are talking about "untracked" items
        if output is None:
            bom_items = self.untracked_bom_items
        else:
            bom_items = self.tracked_bom_items

        for bom_item in bom_items:

            if self.allocated_quantity(bom_item, output) > 0:
                return True

        return False

    def are_untracked_parts_allocated(self):
        """Returns True if the un-tracked parts are fully allocated for this BuildOrder."""
        return self.is_fully_allocated(None)

    def unallocated_bom_items(self, output):
        """Return a list of bom items which have *not* been fully allocated against a particular output."""
        unallocated = []

        # If output is not specified, we are talking about "untracked" items
        if output is None:
            bom_items = self.untracked_bom_items
        else:
            bom_items = self.tracked_bom_items

        for bom_item in bom_items:

            if not self.is_bom_item_allocated(bom_item, output):
                unallocated.append(bom_item)

        return unallocated

    @property
    def required_parts(self):
        """Returns a list of parts required to build this part (BOM)."""
        parts = []

        for item in self.bom_items:
            parts.append(item.sub_part)

        return parts

    @property
    def required_parts_to_complete_build(self):
        """Returns a list of parts required to complete the full build."""
        parts = []

        for bom_item in self.bom_items:
            # Get remaining quantity needed
            required_quantity_to_complete_build = self.remaining * bom_item.quantity
            # Compare to net stock
            if bom_item.sub_part.net_stock < required_quantity_to_complete_build:
                parts.append(bom_item.sub_part)

        return parts

    @property
    def is_active(self):
        """Is this build active?

        An active build is either:
        - PENDING
        - HOLDING
        """
        return self.status in BuildStatus.ACTIVE_CODES

    @property
    def is_complete(self):
        """Returns True if the build status is COMPLETE."""
        return self.status == BuildStatus.COMPLETE


@receiver(post_save, sender=Build, dispatch_uid='build_post_save_log')
def after_save_build(sender, instance: Build, created: bool, **kwargs):
    """Callback function to be executed after a Build instance is saved."""
    from . import tasks as build_tasks

    if created:
        # A new Build has just been created

        # Run checks on required parts
        InvenTree.tasks.offload_task(build_tasks.check_build_stock, instance)

        # Notify the responsible users that the build order has been created
        if instance.responsible is not None:

            targets = []

            for owner in instance.responsible.get_related_owners(include_group=False):
                user = owner.owner

                if user != instance.issued_by:
                    targets.append(user)

            if len(targets) > 0:
                # Notify the responsible user(s) that the new build order has been created
                name = _("New Build Order")
                context = {
                    'build': instance,
                    'name': name,
                    'message': _("A new Build Order has been created and assigned to you"),
                    'link': InvenTree.helpers.construct_absolute_url(instance.get_absolute_url()),
                    'template': {
                        'html': 'email/new_order_assigned.html',
                        'subject': name,
                    }
                }

                common.notifications.trigger_notification(
                    instance,
                    'build.new_build_order',
                    targets=targets,
                    context=context,
                )


class BuildOrderAttachment(InvenTreeAttachment):
    """Model for storing file attachments against a BuildOrder object."""

    def getSubdir(self):
        """Return the media file subdirectory for storing BuildOrder attachments"""
        return os.path.join('bo_files', str(self.build.id))

    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name='attachments')


class BuildItem(models.Model):
    """A BuildItem links multiple StockItem objects to a Build.

    These are used to allocate part stock to a build. Once the Build is completed, the parts are removed from stock and the BuildItemAllocation objects are removed.

    Attributes:
        build: Link to a Build object
        bom_item: Link to a BomItem object (may or may not point to the same part as the build)
        stock_item: Link to a StockItem object
        quantity: Number of units allocated
        install_into: Destination stock item (or None)
    """

    @staticmethod
    def get_api_url():
        """Return the API URL used to access this model"""
        return reverse('api-build-item-list')

    class Meta:
        """Serializer metaclass"""
        unique_together = [
            ('build', 'stock_item', 'install_into'),
        ]

    def save(self, *args, **kwargs):
        """Custom save method for the BuildItem model"""
        self.clean()

        super().save()

    def clean(self):
        """Check validity of this BuildItem instance.

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
                    'quantity': _(f'Allocated quantity ({q}) must not exceed available stock quantity ({a})')
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
            if self.stock_item.serialized and self.quantity != 1:
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

        if self.bom_item and self.build:
            """
            A BomItem object has already been assigned. This is valid if:

            a) It points to the same "part" as the referenced build
            b) Either:
                i) The sub_part points to the same part as the referenced StockItem
                ii) The BomItem allows variants and the part referenced by the StockItem
                    is a variant of the sub_part referenced by the BomItem
                iii) The Part referenced by the StockItem is a valid substitute for the BomItem
            """

            if self.build.part == self.bom_item.part:
                bom_item_valid = self.bom_item.is_stock_item_valid(self.stock_item)

            elif self.bom_item.inherited:
                if self.build.part in self.bom_item.part.get_descendants(include_self=False):
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
    def complete_allocation(self, user, notes=''):
        """Complete the allocation of this BuildItem into the output stock item.

        - If the referenced part is trackable, the stock item will be *installed* into the build output
        - If the referenced part is *not* trackable, the stock item will be removed from stock
        """
        item = self.stock_item

        # For a trackable part, special consideration needed!
        if item.part.trackable:
            # Split the allocated stock if there are more available than allocated
            if item.quantity > self.quantity:
                item = item.splitStock(
                    self.quantity,
                    None,
                    user,
                    code=StockHistoryCode.BUILD_CONSUMED,
                )

                # Make sure we are pointing to the new item
                self.stock_item = item
                self.save()

            # Install the stock item into the output
            self.install_into.installStockItem(
                item,
                self.quantity,
                user,
                notes
            )

        else:
            # Simply remove the items from stock
            item.take_stock(
                self.quantity,
                user,
                code=StockHistoryCode.BUILD_CONSUMED
            )

    def getStockItemThumbnail(self):
        """Return qualified URL for part thumbnail image."""
        thumb_url = None

        if self.stock_item and self.stock_item.part:
            try:
                # Try to extract the thumbnail
                thumb_url = self.stock_item.part.image.thumbnail.url
            except Exception:
                pass

        if thumb_url is None and self.bom_item and self.bom_item.sub_part:
            try:
                thumb_url = self.bom_item.sub_part.image.thumbnail.url
            except Exception:
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
