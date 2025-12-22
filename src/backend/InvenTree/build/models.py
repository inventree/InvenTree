"""Build database model definitions."""

import decimal
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from mptt.models import TreeForeignKey
from rest_framework import serializers

import generic.states
import InvenTree.fields
import InvenTree.helpers
import InvenTree.helpers_model
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import part.models
import report.mixins
import stock.models
import users.models
from build.events import BuildEvents
from build.filters import annotate_allocated_quantity, annotate_required_quantity
from build.status_codes import BuildStatus, BuildStatusGroups
from build.validators import (
    generate_next_build_reference,
    validate_build_order_reference,
)
from common.models import ProjectCode
from common.notifications import InvenTreeNotificationBodies, trigger_notification
from common.settings import (
    get_global_setting,
    prevent_build_output_complete_on_incompleted_tests,
)
from generic.states import StateTransitionMixin, StatusCodeMixin
from plugin.events import trigger_event
from stock.status_codes import StockHistoryCode, StockStatus

logger = structlog.get_logger('inventree')


class BuildReportContext(report.mixins.BaseReportContext):
    """Context for the Build model.

    Attributes:
        bom_items: Query set of all BuildItem objects associated with the BuildOrder
        build: The BuildOrder instance itself
        build_outputs: Query set of all BuildItem objects associated with the BuildOrder
        line_items: Query set of all build line items associated with the BuildOrder
        part: The Part object which is being assembled in the build order
        quantity: The total quantity of the part being assembled
        reference: The reference field of the BuildOrder
        title: The title field of the BuildOrder
    """

    bom_items: report.mixins.QuerySet[part.models.BomItem]
    build: 'Build'
    build_outputs: report.mixins.QuerySet[stock.models.StockItem]
    line_items: report.mixins.QuerySet['BuildLine']
    part: part.models.Part
    quantity: int
    reference: str
    title: str


class Build(
    InvenTree.models.PluginValidationMixin,
    report.mixins.InvenTreeReportMixin,
    InvenTree.models.InvenTreeParameterMixin,
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    InvenTree.models.InvenTreeNotesMixin,
    InvenTree.models.ReferenceIndexingMixin,
    StateTransitionMixin,
    StatusCodeMixin,
    InvenTree.models.MetadataMixin,
    InvenTree.models.InvenTreeTree,
):
    """A Build object organizes the creation of new StockItem objects from other existing StockItem objects.

    Attributes:
        part: The part to be built (from component BOM items)
        reference: Build order reference (required, must be unique)
        title: Brief title describing the build (optional)
        quantity: Number of units to be built
        parent: Reference to a Build object for which this Build is required
        sales_order: References to a SalesOrder object for which this Build is required (e.g. the output of this build will be used to fulfil a sales order)
        take_from: Location to take stock from to make this build (if blank, can take from anywhere)
        status: Build status code
        external: Set to indicate that this build order is fulfilled externally
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

    STATUS_CLASS = BuildStatus

    class Meta:
        """Metaclass options for the BuildOrder model."""

        verbose_name = _('Build Order')
        verbose_name_plural = _('Build Orders')

    class MPTTMeta:
        """MPTT options for the BuildOrder model."""

        order_insertion_by = ['reference']

    OVERDUE_FILTER = (
        Q(status__in=BuildStatusGroups.ACTIVE_CODES)
        & ~Q(target_date=None)
        & Q(target_date__lte=InvenTree.helpers.current_date())
    )

    # Global setting for specifying reference pattern
    REFERENCE_PATTERN_SETTING = 'BUILDORDER_REFERENCE_PATTERN'

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the BuildOrder model."""
        return reverse('api-build-list')

    def api_instance_filters(self):
        """Returns custom API filters for the particular BuildOrder instance."""
        return {'parent': {'exclude_tree': self.pk}}

    @classmethod
    def api_defaults(cls, request=None):
        """Return default values for this model when issuing an API OPTIONS request."""
        defaults = {'reference': generate_next_build_reference()}

        if request and request.user:
            defaults['issued_by'] = request.user.pk

        return defaults

    @classmethod
    def barcode_model_type_code(cls):
        """Return the associated barcode model type code for this model."""
        return 'BO'

    def save(self, *args, **kwargs):
        """Custom save method for the BuildOrder model."""
        self.reference_int = self.validate_reference_field(self.reference)

        # Check part when initially creating the build order
        if not self.pk or self.has_field_changed('part'):
            if get_global_setting('BUILDORDER_REQUIRE_VALID_BOM'):
                # Check that the BOM is valid
                if not self.part.is_bom_valid():
                    raise ValidationError({
                        'part': _('Assembly BOM has not been validated')
                    })

            if get_global_setting('BUILDORDER_REQUIRE_ACTIVE_PART'):
                # Check that the part is active
                if not self.part.active:
                    raise ValidationError({
                        'part': _('Build order cannot be created for an inactive part')
                    })

            if get_global_setting('BUILDORDER_REQUIRE_LOCKED_PART'):
                # Check that the part is locked
                if not self.part.locked:
                    raise ValidationError({
                        'part': _('Build order cannot be created for an unlocked part')
                    })

        # On first save (i.e. creation), run some extra checks
        if self.pk is None:
            # Set the destination location (if not specified)
            if not self.destination:
                self.destination = self.part.get_default_location()

        super().save(*args, **kwargs)

    def clean(self):
        """Validate the BuildOrder model."""
        super().clean()

        if self.external and not self.part.purchaseable:
            raise ValidationError({
                'external': _(
                    'Build orders can only be externally fulfilled for purchaseable parts'
                )
            })

        if get_global_setting('BUILDORDER_REQUIRE_RESPONSIBLE'):
            if not self.responsible:
                raise ValidationError({
                    'responsible': _('Responsible user or group must be specified')
                })

        # Prevent changing target part after creation
        if self.has_field_changed('part'):
            raise ValidationError({'part': _('Build order part cannot be changed')})

        # Target date should be *after* the start date
        if self.start_date and self.target_date and self.start_date > self.target_date:
            raise ValidationError({
                'target_date': _('Target date must be after start date')
            })

    def report_context(self) -> BuildReportContext:
        """Generate custom report context data."""
        return {
            'bom_items': self.part.get_bom_items(),
            'build': self,
            'build_outputs': self.build_outputs.all(),
            'line_items': self.build_lines.all(),
            'part': self.part,
            'quantity': self.quantity,
            'reference': self.reference,
            'title': str(self),
        }

    def __str__(self):
        """String representation of a BuildOrder."""
        return self.reference

    def get_absolute_url(self):
        """Return the web URL associated with this BuildOrder."""
        return InvenTree.helpers.pui_url(f'/manufacturing/build-order/{self.id}')

    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        help_text=_('Build Order Reference'),
        verbose_name=_('Reference'),
        default=generate_next_build_reference,
        validators=[validate_build_order_reference],
    )

    title = models.CharField(
        verbose_name=_('Description'),
        blank=True,
        max_length=100,
        help_text=_('Brief description of the build (optional)'),
    )

    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='children',
        verbose_name=_('Parent Build'),
        help_text=_('BuildOrder to which this build is allocated'),
    )

    part = models.ForeignKey(
        'part.Part',
        verbose_name=_('Part'),
        on_delete=models.CASCADE,
        related_name='builds',
        limit_choices_to={'assembly': True},
        help_text=_('Select part to build'),
    )

    sales_order = models.ForeignKey(
        'order.SalesOrder',
        verbose_name=_('Sales Order Reference'),
        on_delete=models.SET_NULL,
        related_name='builds',
        null=True,
        blank=True,
        help_text=_('SalesOrder to which this build is allocated'),
    )

    take_from = models.ForeignKey(
        'stock.StockLocation',
        verbose_name=_('Source Location'),
        on_delete=models.SET_NULL,
        related_name='sourcing_builds',
        null=True,
        blank=True,
        help_text=_(
            'Select location to take stock from for this build (leave blank to take from any stock location)'
        ),
    )

    external = models.BooleanField(
        default=False,
        verbose_name=_('External Build'),
        help_text=_('This build order is fulfilled externally'),
    )

    destination = models.ForeignKey(
        'stock.StockLocation',
        verbose_name=_('Destination Location'),
        on_delete=models.SET_NULL,
        related_name='incoming_builds',
        null=True,
        blank=True,
        help_text=_('Select location where the completed items will be stored'),
    )

    quantity = models.PositiveIntegerField(
        verbose_name=_('Build Quantity'),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_('Number of stock items to build'),
    )

    completed = models.PositiveIntegerField(
        verbose_name=_('Completed items'),
        default=0,
        help_text=_('Number of stock items which have been completed'),
    )

    status = generic.states.fields.InvenTreeCustomStatusModelField(
        verbose_name=_('Build Status'),
        default=BuildStatus.PENDING.value,
        choices=BuildStatus.items(),
        status_class=BuildStatus,
        validators=[MinValueValidator(0)],
        help_text=_('Build status code'),
    )

    @property
    def status_text(self):
        """Return the text representation of the status field."""
        return BuildStatus.text(self.status)

    batch = models.CharField(
        verbose_name=_('Batch Code'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Batch code for this build output'),
    )

    creation_date = models.DateField(
        auto_now_add=True, editable=False, verbose_name=_('Creation Date')
    )

    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Build start date'),
        help_text=_('Scheduled start date for this build order'),
    )

    target_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Target completion date'),
        help_text=_(
            'Target date for build completion. Build will be overdue after this date.'
        ),
    )

    completion_date = models.DateField(
        null=True, blank=True, verbose_name=_('Completion Date')
    )

    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('completed by'),
        related_name='builds_completed',
    )

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Issued by'),
        help_text=_('User who issued this build order'),
        related_name='builds_issued',
    )

    responsible = models.ForeignKey(
        users.models.Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Responsible'),
        help_text=_('User or group responsible for this build order'),
        related_name='builds_responsible',
    )

    link = InvenTree.fields.InvenTreeURLField(
        verbose_name=_('External Link'),
        blank=True,
        help_text=_('Link to external URL'),
        max_length=2000,
    )

    priority = models.PositiveIntegerField(
        verbose_name=_('Build Priority'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Priority of this build order'),
    )

    project_code = models.ForeignKey(
        ProjectCode,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Project Code'),
        help_text=_('Project code for this build order'),
    )

    def sub_builds(self, cascade: bool = True) -> QuerySet:
        """Return all Build Order objects under this one."""
        if cascade:
            return self.get_descendants(include_self=False)
        else:
            return self.get_children()

    def sub_build_count(self, cascade: bool = True) -> int:
        """Return the number of sub builds under this one.

        Args:
            cascade: If True (default), include cascading builds under sub builds
        """
        return self.sub_builds(cascade=cascade).count()

    @property
    def has_open_child_builds(self) -> bool:
        """Return True if this build order has any open child builds."""
        return (
            self.sub_builds().filter(status__in=BuildStatusGroups.ACTIVE_CODES).exists()
        )

    @property
    def is_overdue(self) -> bool:
        """Returns true if this build is "overdue".

        Makes use of the OVERDUE_FILTER to avoid code duplication

        Returns:
            bool: Is the build overdue
        """
        query = Build.objects.filter(pk=self.pk)
        query = query.filter(Build.OVERDUE_FILTER)

        return query.exists()

    @property
    def active(self) -> bool:
        """Return True if this build is active."""
        return self.status in BuildStatusGroups.ACTIVE_CODES

    @property
    def tracked_line_items(self) -> QuerySet:
        """Returns the "trackable" BOM lines for this BuildOrder."""
        return self.build_lines.filter(bom_item__sub_part__trackable=True)

    def has_tracked_line_items(self) -> bool:
        """Returns True if this BuildOrder has trackable BomItems."""
        return self.tracked_line_items.count() > 0

    @property
    def untracked_line_items(self) -> QuerySet:
        """Returns the "non trackable" BOM items for this BuildOrder."""
        return self.build_lines.filter(bom_item__sub_part__trackable=False)

    @property
    def are_untracked_parts_allocated(self) -> bool:
        """Returns True if all untracked parts are allocated for this BuildOrder."""
        return self.is_fully_allocated(tracked=False)

    def has_untracked_line_items(self) -> bool:
        """Returns True if this BuildOrder has non trackable BomItems."""
        return self.has_untracked_line_items.count() > 0

    @property
    def remaining(self):
        """Return the number of outputs remaining to be completed."""
        return max(0, self.quantity - self.completed)

    @property
    def output_count(self) -> int:
        """Return the number of build outputs (StockItem) associated with this build order."""
        return self.build_outputs.count()

    def has_build_outputs(self) -> bool:
        """Returns True if this build has more than zero build outputs."""
        return self.output_count > 0

    def get_build_outputs(self, **kwargs) -> QuerySet:
        """Return a list of build outputs.

        kwargs:
            complete = (True / False) - If supplied, filter by completed status
            in_stock = (True / False) - If supplied, filter by 'in-stock' status
        """
        outputs = self.build_outputs.all()

        # Filter by 'in stock' status
        in_stock = kwargs.get('in_stock')

        if in_stock is not None:
            if in_stock:
                outputs = outputs.filter(stock.models.StockItem.IN_STOCK_FILTER)
            else:
                outputs = outputs.exclude(stock.models.StockItem.IN_STOCK_FILTER)

        # Filter by 'complete' status
        complete = kwargs.get('complete')

        if complete is not None:
            if complete:
                outputs = outputs.filter(is_building=False)
            else:
                outputs = outputs.filter(is_building=True)

        return outputs

    @property
    def complete_outputs(self) -> QuerySet:
        """Return all the "completed" build outputs."""
        outputs = self.get_build_outputs(complete=True)

        return outputs

    @property
    def complete_count(self):
        """Return the total quantity of completed outputs."""
        quantity = 0

        for output in self.complete_outputs:
            quantity += output.quantity

        return quantity

    def is_partially_allocated(self) -> bool:
        """Test is this build order has any stock allocated against it."""
        return self.allocated_stock.count() > 0

    @property
    def incomplete_outputs(self) -> QuerySet:
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
    def can_complete(self) -> bool:
        """Returns True if this BuildOrder is ready to be completed.

        - Must not have any outstanding build outputs
        - Completed count must meet the required quantity
        - Untracked parts must be allocated
        """
        if (
            get_global_setting('BUILDORDER_REQUIRE_CLOSED_CHILDS')
            and self.has_open_child_builds
        ):
            return False

        if self.status != BuildStatus.PRODUCTION.value:
            return False

        if self.incomplete_count > 0:
            return False

        if self.remaining > 0:
            return False

        return self.is_fully_allocated(tracked=False)

    @transaction.atomic
    def complete_allocations(self, user) -> None:
        """Complete all stock allocations for this build order.

        - This function is called when a build order is completed
        """
        # Remove untracked allocated stock
        self.subtract_allocated_stock(user)

        # Ensure that there are no longer any BuildItem objects
        # which point to this Build Order
        self.allocated_stock.delete()

    @transaction.atomic
    def complete_build(self, user: User, trim_allocated_stock: bool = False):
        """Mark this build as complete.

        Arguments:
            user: The user who is completing the build
            trim_allocated_stock: If True, trim any allocated stock
        """
        return self.handle_transition(
            self.status,
            BuildStatus.COMPLETE.value,
            self,
            self._action_complete,
            user=user,
            trim_allocated_stock=trim_allocated_stock,
        )

    def _action_complete(self, *args, **kwargs):
        """Action to be taken when a build is completed."""
        import build.tasks

        trim_allocated_stock = kwargs.pop('trim_allocated_stock', False)
        user = kwargs.pop('user', None)

        # Prevent completion if there are open child builds
        if (
            get_global_setting('BUILDORDER_REQUIRE_CLOSED_CHILDS')
            and self.has_open_child_builds
        ):
            raise ValidationError(
                _('Cannot complete build order with open child builds')
            )

        if self.incomplete_count > 0:
            raise ValidationError(
                _('Cannot complete build order with incomplete outputs')
            )

        if trim_allocated_stock:
            self.trim_allocated_stock()

        self.completion_date = InvenTree.helpers.current_date()
        self.completed_by = user
        self.status = BuildStatus.COMPLETE.value
        self.save()

        # Offload task to complete build allocations
        if not InvenTree.tasks.offload_task(
            build.tasks.complete_build_allocations,
            self.pk,
            user.pk if user else None,
            group='build',
        ):
            raise ValidationError(
                _('Failed to offload task to complete build allocations')
            )

        # Register an event
        trigger_event(BuildEvents.COMPLETED, id=self.pk)

        # Notify users that this build has been completed
        targets = [self.issued_by, self.responsible]

        # Also inform anyone subscribed to the assembly part
        targets.extend(self.part.get_subscribers())

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
            'link': InvenTree.helpers_model.construct_absolute_url(
                self.get_absolute_url()
            ),
            'template': {'html': 'email/build_order_completed.html', 'subject': name},
        }

        trigger_notification(
            build,
            'build.completed',
            targets=targets,
            context=context,
            target_exclude=[user],
        )

    @transaction.atomic
    def issue_build(self):
        """Mark the Build as IN PRODUCTION.

        Args:
            user: The user who is issuing the build
        """
        return self.handle_transition(
            self.status, BuildStatus.PENDING.value, self, self._action_issue
        )

    @property
    def can_issue(self) -> bool:
        """Returns True if this BuildOrder can be issued."""
        return self.status in [BuildStatus.PENDING.value, BuildStatus.ON_HOLD.value]

    def _action_issue(self, *args, **kwargs):
        """Perform the action to mark this order as PRODUCTION."""
        if self.can_issue:
            self.status = BuildStatus.PRODUCTION.value
            self.save()

            trigger_event(BuildEvents.ISSUED, id=self.pk)

            from build.tasks import check_build_stock

            # Run checks on required parts
            InvenTree.tasks.offload_task(
                check_build_stock, self, group='build', force_async=True
            )

    @transaction.atomic
    def hold_build(self):
        """Mark the Build as ON HOLD."""
        return self.handle_transition(
            self.status, BuildStatus.ON_HOLD.value, self, self._action_hold
        )

    @property
    def can_hold(self) -> bool:
        """Returns True if this BuildOrder can be placed on hold."""
        return self.status in [BuildStatus.PENDING.value, BuildStatus.PRODUCTION.value]

    def _action_hold(self, *args, **kwargs):
        """Action to be taken when a build is placed on hold."""
        if self.can_hold:
            self.status = BuildStatus.ON_HOLD.value
            self.save()

            trigger_event(BuildEvents.HOLD, id=self.pk)

    @transaction.atomic
    def cancel_build(self, user, **kwargs):
        """Mark the Build as CANCELLED.

        - Delete any pending BuildItem objects (but do not remove items from stock)
        - Set build status to CANCELLED
        - Save the Build object
        """
        return self.handle_transition(
            self.status,
            BuildStatus.CANCELLED.value,
            self,
            self._action_cancel,
            user=user,
            **kwargs,
        )

    def _action_cancel(self, *args, **kwargs):
        """Action to be taken when a build is cancelled."""
        import build.tasks

        user = kwargs.pop('user', None)

        remove_allocated_stock = kwargs.get('remove_allocated_stock', False)
        remove_incomplete_outputs = kwargs.get('remove_incomplete_outputs', False)

        if remove_allocated_stock:
            # Offload task to remove allocated stock
            if not InvenTree.tasks.offload_task(
                build.tasks.complete_build_allocations,
                self.pk,
                user.pk if user else None,
                group='build',
            ):
                raise ValidationError(
                    _('Failed to offload task to complete build allocations')
                )

        else:
            self.allocated_stock.all().delete()

        # Remove incomplete outputs (if required)
        if remove_incomplete_outputs:
            outputs = self.build_outputs.filter(is_building=True)

            outputs.delete()

        # Date of 'completion' is the date the build was cancelled
        self.completion_date = InvenTree.helpers.current_date()
        self.completed_by = user

        self.status = BuildStatus.CANCELLED.value
        self.save()

        # Notify users that the order has been canceled
        InvenTree.helpers_model.notify_responsible(
            self,
            Build,
            exclude=self.issued_by,
            content=InvenTreeNotificationBodies.OrderCanceled,
            extra_users=self.part.get_subscribers(),
        )

        trigger_event(BuildEvents.CANCELLED, id=self.pk)

    @transaction.atomic
    def deallocate_stock(self, build_line=None, output=None):
        """Deallocate stock from this Build.

        Args:
            build_line: Specify a particular BuildLine instance to un-allocate stock against
            output: Specify a particular StockItem (output) to un-allocate stock against
        """
        allocations = self.allocated_stock.filter(install_into=output)

        if build_line:
            allocations = allocations.filter(build_line=build_line)

        allocations.delete()

    @transaction.atomic
    def create_build_output(self, quantity, **kwargs) -> QuerySet:
        """Create a new build output against this BuildOrder.

        Arguments:
            quantity: The quantity of the item to produce

        Kwargs:
            batch: Override batch code
            serials: Serial numbers
            location: Override location
            auto_allocate: Automatically allocate stock with matching serial numbers

        Returns:
            A QuerySet of the created output (StockItem) objects.
        """
        trackable_parts = self.part.get_trackable_parts()

        # Create (and cache) a map of valid parts for allocation
        valid_parts = {}

        for bom_item in trackable_parts:
            parts = bom_item.get_valid_parts_for_allocation()
            valid_parts[bom_item.pk] = [part.pk for part in parts]

        user = kwargs.get('user')
        batch = kwargs.get('batch', self.batch)
        location = kwargs.get('location')
        serials = kwargs.get('serials')
        auto_allocate = kwargs.get('auto_allocate', False)

        if location is None:
            location = self.destination or self.part.get_default_location()

        if self.part.has_trackable_parts and not serials:
            raise ValidationError({
                'serials': _('Serial numbers must be provided for trackable parts')
            })

        outputs = []

        # We are generating multiple serialized outputs
        if serials:
            """Create multiple build outputs with a single quantity of 1."""

            # Create tracking entries for each item
            tracking = []
            allocations = []

            outputs = stock.models.StockItem._create_serial_numbers(
                serials,
                part=self.part,
                build=self,
                batch=batch,
                location=location,
                is_building=True,
            )

            for output in outputs:
                # Generate a new historical tracking entry
                if entry := output.add_tracking_entry(
                    StockHistoryCode.BUILD_OUTPUT_CREATED,
                    user,
                    deltas={
                        'quantity': 1,
                        'buildorder': self.pk,
                        'batch': output.batch,
                        'serial': output.serial,
                        'location': location.pk if location else None,
                    },
                    commit=False,
                ):
                    tracking.append(entry)

                # Auto-allocate stock based on serial number
                if auto_allocate:
                    for bom_item in trackable_parts:
                        valid_part_ids = valid_parts.get(bom_item.pk, [])

                        # Find all matching stock items, based on serial number
                        stock_items = list(
                            stock.models.StockItem.objects.filter(
                                part__pk__in=valid_part_ids,
                                serial=output.serial,
                                quantity=1,
                            )
                        )

                        # Filter stock items to only those which are in stock
                        # Note that we can accept "in production" items here
                        available_items = list(
                            filter(
                                lambda item: item.is_in_stock(
                                    check_in_production=False
                                ),
                                stock_items,
                            )
                        )

                        if len(available_items) == 1:
                            stock_item = available_items[0]

                            # Find the 'BuildLine' object which points to this BomItem
                            try:
                                build_line = BuildLine.objects.get(
                                    build=self, bom_item=bom_item
                                )

                                # Allocate the stock items against the BuildLine
                                allocations.append(
                                    BuildItem(
                                        build_line=build_line,
                                        stock_item=stock_item,
                                        quantity=1,
                                        install_into=output,
                                    )
                                )
                            except BuildLine.DoesNotExist:
                                pass

            # Bulk create tracking entries
            stock.models.StockItemTracking.objects.bulk_create(tracking)

            # Generate stock allocations
            BuildItem.objects.bulk_create(allocations)

        else:
            """Create a single build output of the given quantity."""

            output = stock.models.StockItem.objects.create(
                quantity=quantity,
                location=location,
                part=self.part,
                build=self,
                batch=batch,
                is_building=True,
            )

            output.add_tracking_entry(
                StockHistoryCode.BUILD_OUTPUT_CREATED,
                user,
                deltas={
                    'quantity': float(quantity),
                    'buildorder': self.pk,
                    'batch': batch,
                    'location': location.pk if location else None,
                },
            )

            # Ensure we return a QuerySet object here, too
            outputs = stock.models.StockItem.objects.filter(pk=output.pk)

        if self.status == BuildStatus.PENDING:
            self.status = BuildStatus.PRODUCTION.value
            self.save()

        return outputs

    @transaction.atomic
    def delete_output(self, output):
        """Remove a build output from the database.

        Executes:
        - Deallocate any build items against the output
        - Delete the output StockItem
        """
        if not output:
            raise ValidationError(_('No build output specified'))

        if not output.is_building:
            raise ValidationError(_('Build output is already completed'))

        if output.build != self:
            raise ValidationError(_('Build output does not match Build Order'))

        # Deallocate all build items against the output
        self.deallocate_stock(output=output)

        # Remove the build output from the database
        output.delete()

    @transaction.atomic
    def trim_allocated_stock(self):
        """Called after save to reduce allocated stock if the build order is now overallocated."""
        # Only need to worry about untracked stock here

        items_to_save = []
        items_to_delete = []

        lines = self.untracked_line_items.all()
        lines = lines.exclude(bom_item__consumable=True)
        lines = lines.annotate(allocated=annotate_allocated_quantity())

        for build_line in lines:  # type: ignore[non-iterable]
            reduce_by = build_line.allocated - build_line.quantity

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
                    items_to_save.append(item)
                    break

                # Harder case, this item needs to be deleted, and any remainder
                # taken from the next items in the list.
                reduce_by -= item.quantity
                items_to_delete.append(item)

        # Save the updated BuildItem objects
        BuildItem.objects.bulk_update(items_to_save, ['quantity'])

        # Delete the remaining BuildItem objects
        BuildItem.objects.filter(pk__in=[item.pk for item in items_to_delete]).delete()

    @property
    def allocated_stock(self) -> QuerySet:
        """Returns a QuerySet object of all BuildItem objects which point back to this Build."""
        return BuildItem.objects.filter(build_line__build=self)

    @transaction.atomic
    def subtract_allocated_stock(self, user) -> None:
        """Removes the allocated untracked items from stock."""
        # Find all BuildItem objects which point to this build
        items = self.allocated_stock.filter(
            build_line__bom_item__sub_part__trackable=False
        )

        # Remove stock
        for item in items:
            item.complete_allocation(user=user)

        # Delete allocation
        items.all().delete()

    @transaction.atomic
    def scrap_build_output(
        self, output: stock.models.StockItem, quantity, location, **kwargs
    ):
        """Mark a particular build output as scrapped / rejected.

        - Mark the output as "complete"
        - *Do Not* update the "completed" count for this order
        - Set the item status to "scrapped"
        - Add a transaction entry to the stock item history
        """
        if not output:
            raise ValidationError(_('No build output specified'))

        # If quantity is not specified, assume the entire output quantity
        if quantity is None:
            quantity = output.quantity

        if quantity <= 0:
            raise ValidationError({'quantity': _('Quantity must be greater than zero')})

        if quantity > output.quantity:
            raise ValidationError({
                'quantity': _('Quantity cannot be greater than the output quantity')
            })

        user = kwargs.get('user')
        notes = kwargs.get('notes', '')
        discard_allocations = kwargs.get('discard_allocations', False)

        if quantity < output.quantity:
            # Split output into two items
            output = output.splitStock(
                quantity, location=location, user=user, allow_production=True
            )
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
                build_item.complete_allocation(user=user)

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
            },
        )

    @transaction.atomic
    def complete_build_output(
        self,
        output: stock.models.StockItem,
        user: User,
        quantity: Optional[decimal.Decimal] = None,
        **kwargs,
    ):
        """Complete a particular build output.

        Arguments:
            output: The StockItem instance (build output) to complete
            user: The user who is completing the build output
            quantity: The quantity to complete (defaults to entire output quantity)

        Notes:
            - Remove allocated StockItems
            - Mark the output as complete
        """
        # Select the location for the build output
        location = kwargs.get('location', self.destination)
        status = kwargs.get('status', StockStatus.OK.value)
        notes = kwargs.get('notes', '')

        required_tests = kwargs.get('required_tests', output.part.getRequiredTests())
        prevent_on_incomplete = kwargs.get(
            'prevent_on_incomplete',
            prevent_build_output_complete_on_incompleted_tests(),
        )

        if prevent_on_incomplete and not output.passedAllRequiredTests(
            required_tests=required_tests
        ):
            msg = _('Build output has not passed all required tests')

            if serial := output.serial:
                msg = _(f'Build output {serial} has not passed all required tests')

            raise ValidationError(msg)

        # List the allocated BuildItem objects for the given output
        allocated_items = output.items_to_install.all()

        # If a partial quantity is provided, split the stock output
        if quantity is not None and quantity != output.quantity:
            # Cannot split a build output with allocated items
            if allocated_items.count() > 0:
                raise ValidationError(
                    _('Cannot partially complete a build output with allocated items')
                )

            if quantity <= 0:
                raise ValidationError({
                    'quantity': _('Quantity must be greater than zero')
                })

            if quantity > output.quantity:
                raise ValidationError({
                    'quantity': _('Quantity cannot be greater than the output quantity')
                })

            # Split the stock item
            output = output.splitStock(quantity, user=user, allow_production=True)

        for build_item in allocated_items:
            # Complete the allocation of stock for that item
            build_item.complete_allocation(user=user)

        # Delete the BuildItem objects from the database
        allocated_items.all().delete()

        # Ensure that the output is updated correctly
        output.build = self
        output.is_building = False
        output.location = location
        output.status = status

        output.save(add_note=False)

        deltas = {'status': status, 'buildorder': self.pk}

        if location:
            deltas['location'] = location.pk

        output.add_tracking_entry(
            StockHistoryCode.BUILD_OUTPUT_COMPLETED, user, notes=notes, deltas=deltas
        )

        trigger_event(BuildEvents.OUTPUT_COMPLETED, id=output.pk, build_id=self.pk)

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
        location = kwargs.get('location')
        exclude_location = kwargs.get('exclude_location')
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
                allow_variants=True, allow_substitutes=substitutes
            )

            # Look for available stock items
            available_stock = stock.models.StockItem.objects.filter(
                stock.models.StockItem.IN_STOCK_FILTER
            )

            # Filter by list of available parts
            available_stock = available_stock.filter(part__in=list(available_parts))

            # Filter out "serialized" stock items, these cannot be auto-allocated
            available_stock = available_stock.filter(
                Q(serial=None) | Q(serial='')
            ).distinct()

            if location:
                # Filter only stock items located "below" the specified location
                sublocations = location.get_descendants(include_self=True)
                available_stock = available_stock.filter(
                    location__in=list(sublocations)
                )

            if exclude_location:
                # Exclude any stock items from the provided location
                sublocations = exclude_location.get_descendants(include_self=True)
                available_stock = available_stock.exclude(
                    location__in=list(sublocations)
                )

            """
            Next, we sort the available stock items with the following priority:
            1. Direct part matches (+1)
            2. Variant part matches (+2)
            3. Substitute part matches (+3)

            This ensures that allocation priority is first given to "direct" parts
            """
            available_stock = sorted(
                available_stock,
                key=lambda item, b=bom_item, v=variant_parts: stock_sort(item, b, v),
            )

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
                    quantity = min(
                        unallocated_quantity, stock_item.unallocated_quantity()
                    )

                    if quantity > 0:
                        try:
                            new_items.append(
                                BuildItem(
                                    build_line=line_item,
                                    stock_item=stock_item,
                                    quantity=quantity,
                                )
                            )

                            # Subtract the required quantity
                            unallocated_quantity -= quantity

                        except (ValidationError, serializers.ValidationError) as exc:
                            # Catch model errors and re-throw as DRF errors
                            raise ValidationError(
                                exc.message, detail=serializers.as_serializer_error(exc)
                            )

                    if unallocated_quantity <= 0:
                        # We have now fully-allocated this BomItem - no need to continue!
                        break

        # Bulk-create the new BuildItem objects
        BuildItem.objects.bulk_create(new_items)

    def unallocated_lines(self, tracked: Optional[bool] = None) -> QuerySet:
        """Returns a list of BuildLine objects which have not been fully allocated."""
        lines = self.build_lines.all()

        # Remove any 'consumable' line items
        lines = lines.exclude(bom_item__consumable=True)

        if tracked is True:
            lines = lines.filter(bom_item__sub_part__trackable=True)
        elif tracked is False:
            lines = lines.filter(bom_item__sub_part__trackable=False)

        lines = lines.prefetch_related('allocations')

        lines = lines.annotate(
            allocated=annotate_allocated_quantity(),
            required=annotate_required_quantity(),
        ).filter(allocated__lt=F('required'))

        return lines

    def is_fully_allocated(self, tracked: Optional[bool] = None) -> bool:
        """Test if the BuildOrder has been fully allocated.

        Arguments:
            tracked: If True, only consider tracked BuildLine items. If False, only consider untracked BuildLine items.

        Returns:
            True if the BuildOrder has been fully allocated, otherwise False
        """
        return self.unallocated_lines(tracked=tracked).count() == 0

    def is_output_fully_allocated(self, output) -> bool:
        """Determine if the specified output (StockItem) has been fully allocated for this build.

        Arguments:
            output: StockItem object (the "in production" output to test against)

        To determine if the output has been fully allocated,
        we need to test all "trackable" BuildLine objects
        """
        lines = self.build_lines.filter(bom_item__sub_part__trackable=True)
        lines = lines.exclude(bom_item__consumable=True)

        # Find any lines which have not been fully allocated
        for line in lines:
            # Grab all BuildItem objects which point to this output
            allocations = BuildItem.objects.filter(build_line=line, install_into=output)

            allocated = allocations.aggregate(
                q=Coalesce(Sum('quantity'), 0, output_field=models.DecimalField())
            )

            # The amount allocated against an output must at least equal the BOM quantity
            if allocated['q'] < line.bom_item.quantity:
                return False

        # At this stage, we can assume that the output is fully allocated
        return True

    def is_overallocated(self) -> bool:
        """Test if the BuildOrder has been over-allocated.

        Returns:
            True if any BuildLine has been over-allocated.
        """
        lines = self.build_lines.all().exclude(bom_item__consumable=True)

        lines = lines.prefetch_related('allocations')

        # Find any lines which have been over-allocated
        lines = lines.annotate(
            allocated=annotate_allocated_quantity(),
            required=annotate_required_quantity(),
        ).filter(allocated__gt=F('required'))

        return lines.count() > 0

    @property
    def is_active(self) -> bool:
        """Is this build active?

        An active build is either:
        - PENDING
        - HOLDING
        """
        return self.status in BuildStatusGroups.ACTIVE_CODES

    @property
    def is_complete(self) -> bool:
        """Returns True if the build status is COMPLETE."""
        return self.status == BuildStatus.COMPLETE.value

    @transaction.atomic
    def create_build_line_items(self, prevent_duplicates: bool = True) -> None:
        """Create BuildLine objects for each BOM line in this BuildOrder."""
        lines = []

        # Find all non-virtual BOM items for the parent part
        bom_items = self.part.get_bom_items(include_virtual=False)

        logger.info(
            'Creating BuildLine objects for BuildOrder %s (%s items)',
            self.pk,
            len(bom_items),
        )

        # Iterate through each part required to build the parent part
        for bom_item in bom_items:
            if prevent_duplicates:
                if BuildLine.objects.filter(build=self, bom_item=bom_item).exists():
                    logger.info(
                        'BuildLine already exists for BuildOrder %s and BomItem %s',
                        self.pk,
                        bom_item.pk,
                    )
                    continue

            # Calculate required quantity
            quantity = bom_item.get_required_quantity(self.quantity)

            lines.append(BuildLine(build=self, bom_item=bom_item, quantity=quantity))

        BuildLine.objects.bulk_create(lines)

        if len(lines) > 0:
            logger.info('Created %s BuildLine objects for BuildOrder', len(lines))

    @transaction.atomic
    def update_build_line_items(self) -> None:
        """Rebuild required quantity field for each BuildLine object."""
        lines_to_update = []

        for line in self.build_lines.all():
            line.quantity = line.bom_item.get_required_quantity(self.quantity)
            lines_to_update.append(line)

        BuildLine.objects.bulk_update(lines_to_update, ['quantity'])

        logger.info('Updated %s BuildLine objects for BuildOrder', len(lines_to_update))


@receiver(post_save, sender=Build, dispatch_uid='build_post_save_log')
def after_save_build(sender, instance: Build, created: bool, **kwargs):
    """Callback function to be executed after a Build instance is saved."""
    # Escape if we are importing data
    if InvenTree.ready.isImportingData() or not InvenTree.ready.canAppAccessDatabase(
        allow_test=True
    ):
        return

    if instance:
        if created:
            # A new Build has just been created

            # Generate initial BuildLine objects for the Build
            instance.create_build_line_items()

            # Notify the responsible users that the build order has been created
            InvenTree.helpers_model.notify_responsible(
                instance,
                sender,
                exclude=instance.issued_by,
                extra_users=instance.part.get_subscribers(),
            )

        else:
            # Update BuildLine objects if the Build quantity has changed
            instance.update_build_line_items()


class BuildLineReportContext(report.mixins.BaseReportContext):
    """Context for the BuildLine model.

    Attributes:
        allocated_quantity: The quantity of the part which has been allocated to this build
        allocations: A query set of all StockItem objects which have been allocated to this build line
        bom_item: The BomItem associated with this line item
        build: The BuildOrder instance associated with this line item
        build_line: The build line instance itself
        part: The sub-part (component) associated with the linked BomItem instance
        quantity: The quantity required for this line item
    """

    allocated_quantity: decimal.Decimal
    allocations: report.mixins.QuerySet['BuildItem']
    bom_item: part.models.BomItem
    build: Build
    build_line: 'BuildLine'
    part: part.models.Part
    quantity: decimal.Decimal


class BuildLine(report.mixins.InvenTreeReportMixin, InvenTree.models.InvenTreeModel):
    """A BuildLine object links a BOMItem to a Build.

    When a new Build is created, the BuildLine objects are created automatically.
    - A BuildLine entry is created for each BOM item associated with the part
    - The quantity is set to the quantity required to build the part
    - BuildItem objects are associated with a particular BuildLine

    Once a build has been created, BuildLines can (optionally) be removed from the Build

    Attributes:
        build: Link to a Build object
        bom_item: Link to a BomItem object
        quantity: Number of units required for the Build
        consumed: Number of units which have been consumed against this line item
    """

    class Meta:
        """Model meta options."""

        verbose_name = _('Build Order Line Item')
        unique_together = [('build', 'bom_item')]

    @staticmethod
    def get_api_url():
        """Return the API URL used to access this model."""
        return reverse('api-build-line-list')

    def report_context(self) -> BuildLineReportContext:
        """Generate custom report context for this BuildLine object."""
        return {
            'allocated_quantity': self.allocated_quantity,
            'allocations': self.allocations,
            'bom_item': self.bom_item,
            'build': self.build,
            'build_line': self,
            'part': self.bom_item.sub_part,
            'quantity': self.quantity,
        }

    build = models.ForeignKey(
        Build,
        on_delete=models.CASCADE,
        related_name='build_lines',
        help_text=_('Build object'),
    )

    bom_item = models.ForeignKey(
        part.models.BomItem, on_delete=models.CASCADE, related_name='build_lines'
    )

    quantity = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name=_('Quantity'),
        help_text=_('Required quantity for build order'),
    )

    consumed = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Consumed'),
        help_text=_('Quantity of consumed stock'),
    )

    @property
    def part(self):
        """Return the sub_part reference from the link bom_item."""
        return self.bom_item.sub_part

    def allocated_quantity(self):
        """Calculate the total allocated quantity for this BuildLine."""
        # Queryset containing all BuildItem objects allocated against this BuildLine
        allocations = self.allocations.all()

        allocated = allocations.aggregate(
            q=Coalesce(Sum('quantity'), 0, output_field=models.DecimalField())
        )

        return allocated['q']

    def unallocated_quantity(self):
        """Return the unallocated quantity for this BuildLine.

        - Start with the required quantity
        - Subtract the consumed quantity
        - Subtract the allocated quantity

        Return the remaining quantity (or zero if negative)
        """
        return max(self.quantity - self.consumed - self.allocated_quantity(), 0)

    def is_fully_allocated(self) -> bool:
        """Return True if this BuildLine is fully allocated."""
        if self.bom_item.consumable:
            return True

        required = max(0, self.quantity - self.consumed)

        return self.allocated_quantity() >= required

    def is_overallocated(self):
        """Return True if this BuildLine is over-allocated."""
        required = max(0, self.quantity - self.consumed)

        return self.allocated_quantity() > required

    def is_fully_consumed(self) -> bool:
        """Return True if this BuildLine is fully consumed."""
        return self.consumed >= self.quantity


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
        """Model meta options."""

        unique_together = [('build_line', 'stock_item', 'install_into')]

    @staticmethod
    def get_api_url():
        """Return the API URL used to access this model."""
        return reverse('api-build-item-list')

    def save(self, *args, **kwargs):
        """Custom save method for the BuildItem model."""
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
            if (
                self.stock_item.part
                and self.stock_item.part.trackable
                and not self.install_into
            ):
                raise ValidationError(
                    _(
                        'Build item must specify a build output, as master part is marked as trackable'
                    )
                )

            # Allocated quantity cannot exceed available stock quantity
            if self.quantity > self.stock_item.quantity:
                q = InvenTree.helpers.normalize(self.quantity)
                a = InvenTree.helpers.normalize(self.stock_item.quantity)

                raise ValidationError({
                    'quantity': _(
                        f'Allocated quantity ({q}) must not exceed available stock quantity ({a})'
                    )
                })

            # Ensure that we do not 'over allocate' a stock item
            available = decimal.Decimal(self.stock_item.quantity)
            quantity = decimal.Decimal(self.quantity)
            build_allocation_count = decimal.Decimal(
                self.stock_item.build_allocation_count(
                    exclude_allocations={'pk': self.pk}
                )
            )
            sales_allocation_count = decimal.Decimal(
                self.stock_item.sales_order_allocation_count()
            )

            total_allocation = (
                build_allocation_count + sales_allocation_count + quantity
            )

            if total_allocation > available:
                raise ValidationError({'quantity': _('Stock item is over-allocated')})

            # Allocated quantity must be positive
            if self.quantity <= 0:
                raise ValidationError({
                    'quantity': _('Allocation quantity must be greater than zero')
                })

            # Quantity must be 1 for serialized stock
            if self.stock_item.serialized and self.quantity != 1:
                raise ValidationError({
                    'quantity': _('Quantity must be 1 for serialized stock')
                })

        except stock.models.StockItem.DoesNotExist:
            raise ValidationError('Stock item must be specified')
        except part.models.Part.DoesNotExist:
            raise ValidationError('Part must be specified')

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
                if self.build.part in self.bom_item.part.get_descendants(
                    include_self=False
                ):
                    valid = self.bom_item.is_stock_item_valid(self.stock_item)

        # If the existing BomItem is *not* valid, try to find a match
        if not valid and self.build and self.stock_item:
            ancestors = self.stock_item.part.get_ancestors(
                include_self=True, ascending=True
            )

            for idx, ancestor in enumerate(ancestors):
                build_line = BuildLine.objects.filter(
                    build=self.build, bom_item__part=ancestor
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
                'stock_item': _('Selected stock item does not match BOM line')
            })

    @property
    def build(self):
        """Return the BuildOrder associated with this BuildItem."""
        return self.build_line.build if self.build_line else None

    @property
    def bom_item(self):
        """Return the BomItem associated with this BuildItem."""
        return self.build_line.bom_item if self.build_line else None

    @transaction.atomic
    def complete_allocation(self, quantity=None, notes='', user=None) -> None:
        """Complete the allocation of this BuildItem into the output stock item.

        Arguments:
            quantity: The quantity to allocate (default is the full quantity)
            notes: Additional notes to add to the transaction
            user: The user completing the allocation

        - If the referenced part is trackable, the stock item will be *installed* into the build output
        - If the referenced part is *not* trackable, the stock item will be *consumed* by the build order

        TODO: This is quite expensive (in terms of number of database hits) - and requires some thought
        TODO: Revisit, and refactor!

        """
        # If the quantity is not provided, use the quantity of this BuildItem
        if quantity is None:
            quantity = self.quantity

        item = self.stock_item

        # Ensure we are not allocating more than available
        if quantity > item.quantity:
            raise ValidationError({
                'quantity': _('Allocated quantity exceeds available stock quantity')
            })

        # Split the allocated stock if there are more available than allocated
        if item.quantity > quantity:
            item = item.splitStock(quantity, None, user, notes=notes)

        # For a trackable part, special consideration needed!
        if item.part.trackable:
            # Make sure we are pointing to the new item
            self.stock_item = item
            self.save()

            # Install the stock item into the output
            self.install_into.installStockItem(
                item, quantity, user, notes, build=self.build
            )

        else:
            # Mark the item as "consumed" by the build order
            item.consumed_by = self.build
            item.location = None
            item.save(add_note=False)

            item.add_tracking_entry(
                StockHistoryCode.BUILD_CONSUMED,
                user,
                notes=notes,
                deltas={'buildorder': self.build.pk, 'quantity': float(item.quantity)},
            )

        # Increase the "consumed" count for the associated BuildLine
        self.build_line.consumed += quantity
        self.build_line.save()

        # Decrease the allocated quantity
        self.quantity = max(0, self.quantity - quantity)

        if self.quantity <= 0:
            self.delete()
        else:
            self.save()

    build_line = models.ForeignKey(
        BuildLine, on_delete=models.CASCADE, null=True, related_name='allocations'
    )

    stock_item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='allocations',
        verbose_name=_('Stock Item'),
        help_text=_('Source stock item'),
        limit_choices_to={'sales_order': None, 'belongs_to': None},
    )

    quantity = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=1,
        validators=[MinValueValidator(0)],
        verbose_name=_('Quantity'),
        help_text=_('Stock quantity to allocate to build'),
    )

    install_into = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='items_to_install',
        verbose_name=_('Install into'),
        help_text=_('Destination stock item'),
        limit_choices_to={'is_building': True},
    )
