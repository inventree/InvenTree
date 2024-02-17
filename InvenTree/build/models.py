"""Build database model definitions."""

import decimal
import logging
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

from mptt.models import MPTTModel, TreeForeignKey
from mptt.exceptions import InvalidMove

from rest_framework import serializers

from InvenTree.status_codes import BuildStatus, StockStatus, StockHistoryCode, BuildStatusGroups

from build.validators import generate_next_build_reference, validate_build_order_reference

import InvenTree.fields
import InvenTree.helpers
import InvenTree.helpers_model
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks

import common.models
from common.notifications import trigger_notification, InvenTreeNotificationBodies
from plugin.events import trigger_event

import part.models
import stock.models
import users.models


logger = logging.getLogger('inventree')


class Build(InvenTree.models.InvenTreeBarcodeMixin, InvenTree.models.InvenTreeNotesMixin, InvenTree.models.MetadataMixin, InvenTree.models.PluginValidationMixin, InvenTree.models.ReferenceIndexingMixin, MPTTModel):
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
        priority: Priority of the build
    """

    class Meta:
        """Metaclass options for the BuildOrder model"""
        verbose_name = _("Build Order")
        verbose_name_plural = _("Build Orders")

    OVERDUE_FILTER = Q(status__in=BuildStatusGroups.ACTIVE_CODES) & ~Q(target_date=None) & Q(target_date__lte=datetime.now().date())

    # Global setting for specifying reference pattern
    REFERENCE_PATTERN_SETTING = 'BUILDORDER_REFERENCE_PATTERN'

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
            'reference': generate_next_build_reference(),
        }

        if request and request.user:
            defaults['issued_by'] = request.user.pk

        return defaults

    def save(self, *args, **kwargs):
        """Custom save method for the BuildOrder model"""
        self.validate_reference_field(self.reference)
        self.reference_int = self.rebuild_reference_field(self.reference)

        try:
            super().save(*args, **kwargs)
        except InvalidMove:
            raise ValidationError({
                'parent': _('Invalid choice for parent build'),
            })

    def clean(self):
        """Validate the BuildOrder model"""

        super().clean()

        # Prevent changing target part after creation
        if self.has_field_changed('part'):
            raise ValidationError({
                'part': _('Build order part cannot be changed')
            })

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
        completed = Q(status=BuildStatus.COMPLETE.value) & Q(completion_date__gte=min_date) & Q(completion_date__lte=max_date)

        # Order target date falls within specified range
        pending = Q(status__in=BuildStatusGroups.ACTIVE_CODES) & ~Q(target_date=None) & Q(target_date__gte=min_date) & Q(target_date__lte=max_date)

        # TODO - Construct a queryset for "overdue" orders

        queryset = queryset.filter(completed | pending)

        return queryset

    def __str__(self):
        """String representation of a BuildOrder"""
        return self.reference

    def get_absolute_url(self):
        """Return the web URL associated with this BuildOrder"""
        return reverse('build-detail', kwargs={'pk': self.id})

    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        help_text=_('Build Order Reference'),
        verbose_name=_('Reference'),
        default=generate_next_build_reference,
        validators=[
            validate_build_order_reference,
        ]
    )

    title = models.CharField(
        verbose_name=_('Description'),
        blank=True,
        max_length=100,
        help_text=_('Brief description of the build (optional)')
    )

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
        default=BuildStatus.PENDING.value,
        choices=BuildStatus.items(),
        validators=[MinValueValidator(0)],
        help_text=_('Build status code')
    )

    @property
    def status_text(self):
        """Return the text representation of the status field"""
        return BuildStatus.text(self.status)

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
        users.models.Owner,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Responsible'),
        help_text=_('User or group responsible for this build order'),
        related_name='builds_responsible',
    )

    link = InvenTree.fields.InvenTreeURLField(
        verbose_name=_('External Link'),
        blank=True, help_text=_('Link to external URL')
    )

    priority = models.PositiveIntegerField(
        verbose_name=_('Build Priority'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Priority of this build order')
    )

    project_code = models.ForeignKey(
        common.models.ProjectCode,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Project Code'),
        help_text=_('Project code for this build order'),
    )

    def sub_builds(self, cascade=True):
        """Return all Build Order objects under this one."""
        if cascade:
            return Build.objects.filter(parent=self.pk)
        descendants = self.get_descendants(include_self=True)
        Build.objects.filter(parent__pk__in=[d.pk for d in descendants])

    def sub_build_count(self, cascade=True):
        """Return the number of sub builds under this one.

        Args:
            cascade: If True (default), include cascading builds under sub builds
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
        return self.status in BuildStatusGroups.ACTIVE_CODES

    @property
    def tracked_line_items(self):
        """Returns the "trackable" BOM lines for this BuildOrder."""
        return self.build_lines.filter(bom_item__sub_part__trackable=True)

    def has_tracked_line_items(self):
        """Returns True if this BuildOrder has trackable BomItems."""
        return self.tracked_line_items.count() > 0

    @property
    def untracked_line_items(self):
        """Returns the "non trackable" BOM items for this BuildOrder."""
        return self.build_lines.filter(bom_item__sub_part__trackable=False)

    @property
    def are_untracked_parts_allocated(self):
        """Returns True if all untracked parts are allocated for this BuildOrder."""
        return self.is_fully_allocated(tracked=False)

    def has_untracked_line_items(self):
        """Returns True if this BuildOrder has non trackable BomItems."""
        return self.has_untracked_line_items.count() > 0

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
                outputs = outputs.filter(stock.models.StockItem.IN_STOCK_FILTER)
            else:
                outputs = outputs.exclude(stock.models.StockItem.IN_STOCK_FILTER)

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

    def is_partially_allocated(self):
        """Test is this build order has any stock allocated against it"""
        return self.allocated_stock.count() > 0

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
            new_ref = InvenTree.helpers.increment(new_ref)

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
        """Returns True if this BuildOrder is ready to be completed

        - Must not have any outstanding build outputs
        - Completed count must meet the required quantity
        - Untracked parts must be allocated
        """
        if self.incomplete_count > 0:
            return False

        if self.remaining > 0:
            return False

        if not self.is_fully_allocated(tracked=False):
            return False

        return True

    @transaction.atomic
    def complete_build(self, user):
        """Mark this build as complete."""
        if self.incomplete_count > 0:
            return

        self.completion_date = datetime.now().date()
        self.completed_by = user
        self.status = BuildStatus.COMPLETE.value
        self.save()

        # Remove untracked allocated stock
        self.subtract_allocated_stock(user)

        # Ensure that there are no longer any BuildItem objects
        # which point to this Build Order
        self.allocated_stock.delete()

        # Register an event
        trigger_event('build.completed', id=self.pk)

        # Notify users that this build has been completed
        targets = [
            self.issued_by,
            self.responsible,
        ]

        # Notify those users interested in the parent build
        if self.parent:
            targets.append(self.parent.issued_by)
            targets.append(self.parent.responsible)

        # Notify users if this build points to a sales order
        if self.sales_order:
            targets.append(self.sales_order.created_by)
            targets.append(self.sales_order.responsible)

        build = self
        name = _(f'Build order {build} has been completed')

        context = {
            'build': build,
            'name': name,
            'slug': 'build.completed',
            'message': _('A build order has been completed'),
            'link': InvenTree.helpers_model.construct_absolute_url(self.get_absolute_url()),
            'template': {
                'html': 'email/build_order_completed.html',
                'subject': name,
            }
        }

        trigger_notification(
            build,
            'build.completed',
            targets=targets,
            context=context,
            target_exclude=[user],
        )

    @transaction.atomic
    def cancel_build(self, user, **kwargs):
        """Mark the Build as CANCELLED.

        - Delete any pending BuildItem objects (but do not remove items from stock)
        - Set build status to CANCELLED
        - Save the Build object
        """
        remove_allocated_stock = kwargs.get('remove_allocated_stock', False)
        remove_incomplete_outputs = kwargs.get('remove_incomplete_outputs', False)

        # Find all BuildItem objects associated with this Build
        items = self.allocated_stock

        if remove_allocated_stock:
            for item in items:
                item.complete_allocation(user)

        items.delete()

        # Remove incomplete outputs (if required)
        if remove_incomplete_outputs:
            outputs = self.build_outputs.filter(is_building=True)

            for output in outputs:
                output.delete()

        # Date of 'completion' is the date the build was cancelled
        self.completion_date = datetime.now().date()
        self.completed_by = user

        self.status = BuildStatus.CANCELLED.value
        self.save()

        # Notify users that the order has been canceled
        InvenTree.helpers_model.notify_responsible(
            self,
            Build,
            exclude=self.issued_by,
            content=InvenTreeNotificationBodies.OrderCanceled
        )

        trigger_event('build.cancelled', id=self.pk)

    @transaction.atomic
    def deallocate_stock(self, build_line=None, output=None):
        """Deallocate stock from this Build.

        Args:
            build_line: Specify a particular BuildLine instance to un-allocate stock against
            output: Specify a particular StockItem (output) to un-allocate stock against
        """
        allocations = self.allocated_stock.filter(
            install_into=output
        )

        if build_line:
            allocations = allocations.filter(build_line=build_line)

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
        user = kwargs.get('user', None)
        batch = kwargs.get('batch', self.batch)
        location = kwargs.get('location', self.destination)
        serials = kwargs.get('serials', None)
        auto_allocate = kwargs.get('auto_allocate', False)

        """
        Determine if we can create a single output (with quantity > 0),
        or multiple outputs (with quantity = 1)
        """

        def _add_tracking_entry(output, user):
            """Helper function to add a tracking entry to the newly created output"""
            deltas = {
                'quantity': float(output.quantity),
                'buildorder': self.pk,
            }

            if output.batch:
                deltas['batch'] = output.batch

            if output.serial:
                deltas['serial'] = output.serial

            if output.location:
                deltas['location'] = output.location.pk

            output.add_tracking_entry(StockHistoryCode.BUILD_OUTPUT_CREATED, user, deltas)

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

                output = stock.models.StockItem.objects.create(
                    quantity=1,
                    location=location,
                    part=self.part,
                    build=self,
                    batch=batch,
                    serial=serial,
                    is_building=True,
                )

                _add_tracking_entry(output, user)

                if auto_allocate and serial is not None:

                    # Get a list of BomItem objects which point to "trackable" parts

                    for bom_item in self.part.get_trackable_parts():

                        parts = bom_item.get_valid_parts_for_allocation()

                        items = stock.models.StockItem.objects.filter(
                            part__in=parts,
                            serial=str(serial),
                            quantity=1,
                        ).filter(stock.models.StockItem.IN_STOCK_FILTER)

                        """
                        Test if there is a matching serial number!
                        """
                        if items.exists() and items.count() == 1:
                            stock_item = items[0]

                            # Find the 'BuildLine' object which points to this BomItem
                            try:
                                build_line = BuildLine.objects.get(
                                    build=self,
                                    bom_item=bom_item
                                )

                                # Allocate the stock items against the BuildLine
                                BuildItem.objects.create(
                                    build_line=build_line,
                                    stock_item=stock_item,
                                    quantity=1,
                                    install_into=output,
                                )
                            except BuildLine.DoesNotExist:
                                pass

        else:
            """Create a single build output of the given quantity."""

            output = stock.models.StockItem.objects.create(
                quantity=quantity,
                location=location,
                part=self.part,
                build=self,
                batch=batch,
                is_building=True
            )

            _add_tracking_entry(output, user)

        if self.status == BuildStatus.PENDING:
            self.status = BuildStatus.PRODUCTION.value
            self.save()

    @transaction.atomic
    def delete_output(self, output):
        """Remove a build output from the database.

        Executes:
        - Deallocate any build items against the output
        - Delete the output StockItem
        """
        if not output:
            raise ValidationError(_("No build output specified"))

        if not output.is_building:
            raise ValidationError(_("Build output is already completed"))

        if output.build != self:
            raise ValidationError(_("Build output does not match Build Order"))

        # Deallocate all build items against the output
        self.deallocate_stock(output=output)

        # Remove the build output from the database
        output.delete()

    @transaction.atomic
    def trim_allocated_stock(self):
        """Called after save to reduce allocated stock if the build order is now overallocated."""
        # Only need to worry about untracked stock here
        for build_line in self.untracked_line_items:

            reduce_by = build_line.allocated_quantity() - build_line.quantity

            if reduce_by <= 0:
                continue

            # Find BuildItem objects to trim
            for item in BuildItem.objects.filter(build_line=build_line):

                # Previous item completed the job
                if reduce_by <= 0:
                    break

                # Easy case - this item can just be reduced.
                if item.quantity > reduce_by:
                    item.quantity -= reduce_by
                    item.save()
                    break

                # Harder case, this item needs to be deleted, and any remainder
                # taken from the next items in the list.
                reduce_by -= item.quantity
                item.delete()

    @property
    def allocated_stock(self):
        """Returns a QuerySet object of all BuildItem objects which point back to this Build"""
        return BuildItem.objects.filter(
            build_line__build=self
        )

    @transaction.atomic
    def subtract_allocated_stock(self, user):
        """Called when the Build is marked as "complete", this function removes the allocated untracked items from stock."""
        # Find all BuildItem objects which point to this build
        items = self.allocated_stock.filter(
            build_line__bom_item__sub_part__trackable=False
        )

        # Remove stock
        for item in items:
            item.complete_allocation(user)

        # Delete allocation
        items.all().delete()

    @transaction.atomic
    def scrap_build_output(self, output, quantity, location, **kwargs):
        """Mark a particular build output as scrapped / rejected

        - Mark the output as "complete"
        - *Do Not* update the "completed" count for this order
        - Set the item status to "scrapped"
        - Add a transaction entry to the stock item history
        """
        if not output:
            raise ValidationError(_("No build output specified"))

        if quantity <= 0:
            raise ValidationError({
                'quantity': _("Quantity must be greater than zero")
            })

        if quantity > output.quantity:
            raise ValidationError({
                'quantity': _("Quantity cannot be greater than the output quantity")
            })

        user = kwargs.get('user', None)
        notes = kwargs.get('notes', '')
        discard_allocations = kwargs.get('discard_allocations', False)

        if quantity < output.quantity:
            # Split output into two items
            output = output.splitStock(quantity, location=location, user=user)
            output.build = self

        # Update build output item
        output.is_building = False
        output.status = StockStatus.REJECTED.value
        output.location = location
        output.save(add_note=False)

        allocated_items = output.items_to_install.all()

        # Complete or discard allocations
        for build_item in allocated_items:
            if not discard_allocations:
                build_item.complete_allocation(user)

        # Delete allocations
        allocated_items.delete()

        output.add_tracking_entry(
            StockHistoryCode.BUILD_OUTPUT_REJECTED,
            user,
            notes=notes,
            deltas={
                'location': location.pk,
                'status': StockStatus.REJECTED.value,
                'buildorder': self.pk,
            }
        )

    @transaction.atomic
    def complete_build_output(self, output, user, **kwargs):
        """Complete a particular build output.

        - Remove allocated StockItems
        - Mark the output as complete
        """
        # Select the location for the build output
        location = kwargs.get('location', self.destination)
        status = kwargs.get('status', StockStatus.OK.value)
        notes = kwargs.get('notes', '')

        # List the allocated BuildItem objects for the given output
        allocated_items = output.items_to_install.all()

        if (common.settings.prevent_build_output_complete_on_incompleted_tests() and output.hasRequiredTests() and not output.passedAllRequiredTests()):
            serial = output.serial
            raise ValidationError(
                _(f"Build output {serial} has not passed all required tests"))

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

        output.save(add_note=False)

        deltas = {
            'status': status,
            'buildorder': self.pk
        }

        if location:
            deltas['location'] = location.pk

        output.add_tracking_entry(
            StockHistoryCode.BUILD_OUTPUT_COMPLETED,
            user,
            notes=notes,
            deltas=deltas
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
        optional_items = kwargs.get('optional_items', False)

        def stock_sort(item, bom_item, variant_parts):
            if item.part == bom_item.sub_part:
                return 1
            elif item.part in variant_parts:
                return 2
            return 3

        new_items = []

        # Auto-allocation is only possible for "untracked" line items
        for line_item in self.untracked_line_items.all():

            # Find the referenced BomItem
            bom_item = line_item.bom_item

            if bom_item.consumable:
                # Do not auto-allocate stock to consumable BOM items
                continue

            if bom_item.optional and not optional_items:
                # User has specified that optional_items are to be ignored
                continue

            variant_parts = bom_item.sub_part.get_descendants(include_self=False)

            unallocated_quantity = line_item.unallocated_quantity()

            if unallocated_quantity <= 0:
                # This BomItem is fully allocated, we can continue
                continue

            # Check which parts we can "use" (may include variants and substitutes)
            available_parts = bom_item.get_valid_parts_for_allocation(
                allow_variants=True,
                allow_substitutes=substitutes,
            )

            # Look for available stock items
            available_stock = stock.models.StockItem.objects.filter(stock.models.StockItem.IN_STOCK_FILTER)

            # Filter by list of available parts
            available_stock = available_stock.filter(
                part__in=list(available_parts),
            )

            # Filter out "serialized" stock items, these cannot be auto-allocated
            available_stock = available_stock.filter(Q(serial=None) | Q(serial='')).distinct()

            if location:
                # Filter only stock items located "below" the specified location
                sublocations = location.get_descendants(include_self=True)
                available_stock = available_stock.filter(location__in=list(sublocations))

            if exclude_location:
                # Exclude any stock items from the provided location
                sublocations = exclude_location.get_descendants(include_self=True)
                available_stock = available_stock.exclude(location__in=list(sublocations))

            """
            Next, we sort the available stock items with the following priority:
            1. Direct part matches (+1)
            2. Variant part matches (+2)
            3. Substitute part matches (+3)

            This ensures that allocation priority is first given to "direct" parts
            """
            available_stock = sorted(available_stock, key=lambda item, b=bom_item, v=variant_parts: stock_sort(item, b, v))

            if len(available_stock) == 0:
                # No stock items are available
                continue
            elif len(available_stock) == 1 or interchangeable:
                # Either there is only a single stock item available,
                # or all items are "interchangeable" and we don't care where we take stock from

                for stock_item in available_stock:

                    # Skip inactive parts
                    if not stock_item.part.active:
                        continue

                    # How much of the stock item is "available" for allocation?
                    quantity = min(unallocated_quantity, stock_item.unallocated_quantity())

                    if quantity > 0:

                        try:
                            new_items.append(BuildItem(
                                build_line=line_item,
                                stock_item=stock_item,
                                quantity=quantity,
                            ))

                            # Subtract the required quantity
                            unallocated_quantity -= quantity

                        except (ValidationError, serializers.ValidationError) as exc:
                            # Catch model errors and re-throw as DRF errors
                            raise ValidationError(detail=serializers.as_serializer_error(exc))

                    if unallocated_quantity <= 0:
                        # We have now fully-allocated this BomItem - no need to continue!
                        break

        # Bulk-create the new BuildItem objects
        BuildItem.objects.bulk_create(new_items)

    def unallocated_lines(self, tracked=None):
        """Returns a list of BuildLine objects which have not been fully allocated."""
        lines = self.build_lines.all()

        if tracked is True:
            lines = lines.filter(bom_item__sub_part__trackable=True)
        elif tracked is False:
            lines = lines.filter(bom_item__sub_part__trackable=False)

        unallocated_lines = []

        for line in lines:
            if not line.is_fully_allocated():
                unallocated_lines.append(line)

        return unallocated_lines

    def is_fully_allocated(self, tracked=None):
        """Test if the BuildOrder has been fully allocated.

        This is *true* if *all* associated BuildLine items have sufficient allocation

        Arguments:
            tracked: If True, only consider tracked BuildLine items. If False, only consider untracked BuildLine items.

        Returns:
            True if the BuildOrder has been fully allocated, otherwise False
        """
        lines = self.unallocated_lines(tracked=tracked)
        return len(lines) == 0

    def is_output_fully_allocated(self, output):
        """Determine if the specified output (StockItem) has been fully allocated for this build

        Args:
            output: StockItem object

        To determine if the output has been fully allocated,
        we need to test all "trackable" BuildLine objects
        """
        for line in self.build_lines.filter(bom_item__sub_part__trackable=True):
            # Grab all BuildItem objects which point to this output
            allocations = BuildItem.objects.filter(
                build_line=line,
                install_into=output,
            )

            allocated = allocations.aggregate(
                q=Coalesce(Sum('quantity'), 0, output_field=models.DecimalField())
            )

            # The amount allocated against an output must at least equal the BOM quantity
            if allocated['q'] < line.bom_item.quantity:
                return False

        # At this stage, we can assume that the output is fully allocated
        return True

    def is_overallocated(self):
        """Test if the BuildOrder has been over-allocated.

        Returns:
            True if any BuildLine has been over-allocated.
        """
        for line in self.build_lines.all():
            if line.is_overallocated():
                return True

        return False

    @property
    def is_active(self):
        """Is this build active?

        An active build is either:
        - PENDING
        - HOLDING
        """
        return self.status in BuildStatusGroups.ACTIVE_CODES

    @property
    def is_complete(self):
        """Returns True if the build status is COMPLETE."""
        return self.status == BuildStatus.COMPLETE

    @transaction.atomic
    def create_build_line_items(self, prevent_duplicates=True):
        """Create BuildLine objects for each BOM line in this BuildOrder."""
        lines = []

        bom_items = self.part.get_bom_items()

        logger.info("Creating BuildLine objects for BuildOrder %s (%s items)", self.pk, len(bom_items))

        # Iterate through each part required to build the parent part
        for bom_item in bom_items:
            if prevent_duplicates:
                if BuildLine.objects.filter(build=self, bom_item=bom_item).exists():
                    logger.info("BuildLine already exists for BuildOrder %s and BomItem %s", self.pk, bom_item.pk)
                    continue

            # Calculate required quantity
            quantity = bom_item.get_required_quantity(self.quantity)

            lines.append(
                BuildLine(
                    build=self,
                    bom_item=bom_item,
                    quantity=quantity
                )
            )

        BuildLine.objects.bulk_create(lines)

        if len(lines) > 0:
            logger.info("Created %s BuildLine objects for BuildOrder", len(lines))

    @transaction.atomic
    def update_build_line_items(self):
        """Rebuild required quantity field for each BuildLine object"""
        lines_to_update = []

        for line in self.build_lines.all():
            line.quantity = line.bom_item.get_required_quantity(self.quantity)
            lines_to_update.append(line)

        BuildLine.objects.bulk_update(lines_to_update, ['quantity'])

        logger.info("Updated %s BuildLine objects for BuildOrder", len(lines_to_update))


@receiver(post_save, sender=Build, dispatch_uid='build_post_save_log')
def after_save_build(sender, instance: Build, created: bool, **kwargs):
    """Callback function to be executed after a Build instance is saved."""
    # Escape if we are importing data
    if InvenTree.ready.isImportingData() or not InvenTree.ready.canAppAccessDatabase(allow_test=True):
        return

    from . import tasks as build_tasks

    if instance:

        if created:
            # A new Build has just been created

            # Generate initial BuildLine objects for the Build
            instance.create_build_line_items()

            # Run checks on required parts
            InvenTree.tasks.offload_task(build_tasks.check_build_stock, instance)

            # Notify the responsible users that the build order has been created
            InvenTree.helpers_model.notify_responsible(instance, sender, exclude=instance.issued_by)

        else:
            # Update BuildLine objects if the Build quantity has changed
            instance.update_build_line_items()


class BuildOrderAttachment(InvenTree.models.InvenTreeAttachment):
    """Model for storing file attachments against a BuildOrder object."""

    def getSubdir(self):
        """Return the media file subdirectory for storing BuildOrder attachments"""
        return os.path.join('bo_files', str(self.build.id))

    build = models.ForeignKey(Build, on_delete=models.CASCADE, related_name='attachments')


class BuildLine(InvenTree.models.InvenTreeModel):
    """A BuildLine object links a BOMItem to a Build.

    When a new Build is created, the BuildLine objects are created automatically.
    - A BuildLine entry is created for each BOM item associated with the part
    - The quantity is set to the quantity required to build the part (including overage)
    - BuildItem objects are associated with a particular BuildLine

    Once a build has been created, BuildLines can (optionally) be removed from the Build

    Attributes:
        build: Link to a Build object
        bom_item: Link to a BomItem object
        quantity: Number of units required for the Build
    """

    class Meta:
        """Model meta options"""
        unique_together = [
            ('build', 'bom_item'),
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL used to access this model"""
        return reverse('api-build-line-list')

    build = models.ForeignKey(
        Build, on_delete=models.CASCADE,
        related_name='build_lines', help_text=_('Build object')
    )

    bom_item = models.ForeignKey(
        part.models.BomItem,
        on_delete=models.CASCADE,
        related_name='build_lines',
    )

    quantity = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name=_('Quantity'),
        help_text=_('Required quantity for build order'),
    )

    @property
    def part(self):
        """Return the sub_part reference from the link bom_item"""
        return self.bom_item.sub_part

    def allocated_quantity(self):
        """Calculate the total allocated quantity for this BuildLine"""
        # Queryset containing all BuildItem objects allocated against this BuildLine
        allocations = self.allocations.all()

        allocated = allocations.aggregate(
            q=Coalesce(Sum('quantity'), 0, output_field=models.DecimalField())
        )

        return allocated['q']

    def unallocated_quantity(self):
        """Return the unallocated quantity for this BuildLine"""
        return max(self.quantity - self.allocated_quantity(), 0)

    def is_fully_allocated(self):
        """Return True if this BuildLine is fully allocated"""
        if self.bom_item.consumable:
            return True

        return self.allocated_quantity() >= self.quantity

    def is_overallocated(self):
        """Return True if this BuildLine is over-allocated"""
        return self.allocated_quantity() > self.quantity


class BuildItem(InvenTree.models.InvenTreeMetadataModel):
    """A BuildItem links multiple StockItem objects to a Build.

    These are used to allocate part stock to a build. Once the Build is completed, the parts are removed from stock and the BuildItemAllocation objects are removed.

    Attributes:
        build: Link to a Build object
        build_line: Link to a BuildLine object (this is a "line item" within a build)
        stock_item: Link to a StockItem object
        quantity: Number of units allocated
        install_into: Destination stock item (or None)
    """

    class Meta:
        """Model meta options"""
        unique_together = [
            ('build_line', 'stock_item', 'install_into'),
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL used to access this model"""
        return reverse('api-build-item-list')

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

                q = InvenTree.helpers.normalize(self.quantity)
                a = InvenTree.helpers.normalize(self.stock_item.quantity)

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

        except stock.models.StockItem.DoesNotExist:
            raise ValidationError("Stock item must be specified")
        except part.models.Part.DoesNotExist:
            raise ValidationError("Part must be specified")

        """
        Attempt to find the "BomItem" which links this BuildItem to the build.

        - If a BomItem is already set, and it is valid, then we are ok!
        """

        valid = False

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
                valid = self.bom_item.is_stock_item_valid(self.stock_item)

            elif self.bom_item.inherited:
                if self.build.part in self.bom_item.part.get_descendants(include_self=False):
                    valid = self.bom_item.is_stock_item_valid(self.stock_item)

        # If the existing BomItem is *not* valid, try to find a match
        if not valid:

            if self.build and self.stock_item:
                ancestors = self.stock_item.part.get_ancestors(include_self=True, ascending=True)

                for idx, ancestor in enumerate(ancestors):

                    build_line = BuildLine.objects.filter(
                        build=self.build,
                        bom_item__part=ancestor,
                    )

                    if build_line.exists():
                        line = build_line.first()

                        if idx == 0 or line.bom_item.allow_variants:
                            valid = True
                            self.build_line = line
                            break

        # BomItem did not exist or could not be validated.
        # Search for a new one
        if not valid:

            raise ValidationError({
                'stock_item': _("Selected stock item does not match BOM line")
            })

    @property
    def build(self):
        """Return the BuildOrder associated with this BuildItem"""
        return self.build_line.build if self.build_line else None

    @property
    def bom_item(self):
        """Return the BomItem associated with this BuildItem"""
        return self.build_line.bom_item if self.build_line else None

    @transaction.atomic
    def complete_allocation(self, user, notes=''):
        """Complete the allocation of this BuildItem into the output stock item.

        - If the referenced part is trackable, the stock item will be *installed* into the build output
        - If the referenced part is *not* trackable, the stock item will be *consumed* by the build order
        """
        item = self.stock_item

        # Split the allocated stock if there are more available than allocated
        if item.quantity > self.quantity:
            item = item.splitStock(
                self.quantity,
                None,
                user,
                notes=notes,
            )

        # For a trackable part, special consideration needed!
        if item.part.trackable:

            # Make sure we are pointing to the new item
            self.stock_item = item
            self.save()

            # Install the stock item into the output
            self.install_into.installStockItem(
                item,
                self.quantity,
                user,
                notes,
                build=self.build,
            )

        else:
            # Mark the item as "consumed" by the build order
            item.consumed_by = self.build
            item.save(add_note=False)

            item.add_tracking_entry(
                StockHistoryCode.BUILD_CONSUMED,
                user,
                notes=notes,
                deltas={
                    'buildorder': self.build.pk,
                    'quantity': float(item.quantity),
                }
            )

    build_line = models.ForeignKey(
        BuildLine,
        on_delete=models.SET_NULL, null=True,
        related_name='allocations',
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
