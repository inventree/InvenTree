"""JSON serializers for Build API."""

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.db.models import (
    BooleanField,
    Case,
    ExpressionWrapper,
    F,
    FloatField,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.serializers import ValidationError

import build.tasks
import common.models
import company.serializers
import InvenTree.helpers
import InvenTree.tasks
import part.filters
import part.serializers as part_serializers
from common.serializers import ProjectCodeSerializer
from common.settings import get_global_setting
from generic.states.fields import InvenTreeCustomStatusSerializerMixin
from importer.mixins import DataImportExportSerializerMixin
from InvenTree.serializers import (
    InvenTreeDecimalField,
    InvenTreeModelSerializer,
    NotesFieldMixin,
    UserSerializer,
)
from stock.generators import generate_batch_code
from stock.models import StockItem, StockLocation
from stock.serializers import LocationBriefSerializer, StockItemSerializerBrief
from stock.status_codes import StockStatus
from users.serializers import OwnerSerializer

from .models import Build, BuildItem, BuildLine
from .status_codes import BuildStatus


class BuildSerializer(
    NotesFieldMixin,
    DataImportExportSerializerMixin,
    InvenTreeCustomStatusSerializerMixin,
    InvenTreeModelSerializer,
):
    """Serializes a Build object."""

    class Meta:
        """Serializer metaclass."""

        model = Build
        fields = [
            'pk',
            'url',
            'title',
            'barcode_hash',
            'batch',
            'creation_date',
            'completed',
            'completion_date',
            'destination',
            'parent',
            'part',
            'part_name',
            'part_detail',
            'project_code',
            'project_code_label',
            'project_code_detail',
            'overdue',
            'reference',
            'sales_order',
            'quantity',
            'status',
            'status_text',
            'status_custom_key',
            'target_date',
            'take_from',
            'notes',
            'link',
            'issued_by',
            'issued_by_detail',
            'responsible',
            'responsible_detail',
            'priority',
            'level',
            # Additional fields used only for build order creation
            'create_child_builds',
        ]

        read_only_fields = [
            'completed',
            'creation_date',
            'completion_data',
            'status',
            'status_text',
            'level',
        ]

    reference = serializers.CharField(required=True)

    level = serializers.IntegerField(label=_('Build Level'), read_only=True)

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    part_detail = part_serializers.PartBriefSerializer(
        source='part', many=False, read_only=True
    )

    part_name = serializers.CharField(
        source='part.name', read_only=True, label=_('Part Name')
    )

    quantity = InvenTreeDecimalField()

    overdue = serializers.BooleanField(required=False, read_only=True)

    issued_by_detail = UserSerializer(source='issued_by', read_only=True)

    responsible_detail = OwnerSerializer(source='responsible', read_only=True)

    barcode_hash = serializers.CharField(read_only=True)

    project_code_label = serializers.CharField(
        source='project_code.code', read_only=True, label=_('Project Code Label')
    )

    project_code_detail = ProjectCodeSerializer(
        source='project_code', many=False, read_only=True
    )

    create_child_builds = serializers.BooleanField(
        default=False,
        required=False,
        write_only=True,
        label=_('Create Child Builds'),
        help_text=_('Automatically generate child build orders'),
    )

    @staticmethod
    def annotate_queryset(queryset):
        """Add custom annotations to the BuildSerializer queryset, performing database queries as efficiently as possible.

        The following annotated fields are added:

        - overdue: True if the build is outstanding *and* the completion date has past
        """
        # Annotate a boolean 'overdue' flag

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    Build.OVERDUE_FILTER, then=Value(True, output_field=BooleanField())
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        return queryset

    def __init__(self, *args, **kwargs):
        """Determine if extra serializer fields are required."""
        part_detail = kwargs.pop('part_detail', True)
        create = kwargs.pop('create', False)

        super().__init__(*args, **kwargs)

        if not create:
            self.fields.pop('create_child_builds', None)

        if not part_detail:
            self.fields.pop('part_detail', None)

    def skip_create_fields(self):
        """Return a list of fields to skip during model creation."""
        return ['create_child_builds']

    def validate_reference(self, reference):
        """Custom validation for the Build reference field."""
        # Ensure the reference matches the required pattern
        Build.validate_reference_field(reference)

        return reference

    @transaction.atomic
    def create(self, validated_data):
        """Save the Build object."""
        build_order = super().create(validated_data)

        create_child_builds = self.validated_data.pop('create_child_builds', False)

        if create_child_builds:
            # Pass child build creation off to the background thread
            InvenTree.tasks.offload_task(
                build.tasks.create_child_builds, build_order.pk, group='build'
            )

        return build_order


class BuildOutputSerializer(serializers.Serializer):
    """Serializer for a "BuildOutput".

    Note that a "BuildOutput" is really just a StockItem which is "in production"!
    """

    class Meta:
        """Serializer metaclass."""

        fields = ['output']

    output = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Build Output'),
    )

    def validate_output(self, output):
        """Perform validation for the output (StockItem) provided to the serializer."""
        build = self.context['build']

        # As this serializer can be used in multiple contexts, we need to work out why we are here
        to_complete = self.context.get('to_complete', False)

        # The stock item must point to the build
        if output.build != build:
            raise ValidationError(_('Build output does not match the parent build'))

        # The part must match!
        if output.part != build.part:
            raise ValidationError(_('Output part does not match BuildOrder part'))

        # The build output must be "in production"
        if not output.is_building:
            raise ValidationError(_('This build output has already been completed'))

        if to_complete:
            # The build output must have all tracked parts allocated
            if not build.is_output_fully_allocated(output):
                # Check if the user has specified that incomplete allocations are ok
                accept_incomplete = InvenTree.helpers.str2bool(
                    self.context['request'].data.get(
                        'accept_incomplete_allocation', False
                    )
                )

                if not accept_incomplete:
                    raise ValidationError(_('This build output is not fully allocated'))

        return output


class BuildOutputQuantitySerializer(BuildOutputSerializer):
    """Build output with quantity field."""

    class Meta:
        """Serializer metaclass."""

        fields = [*BuildOutputSerializer.Meta.fields, 'quantity']

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=Decimal(0),
        required=True,
        label=_('Quantity'),
        help_text=_('Enter quantity for build output'),
    )

    def validate(self, data):
        """Validate the serializer data."""
        data = super().validate(data)

        output = data.get('output')
        quantity = data.get('quantity')

        if quantity <= 0:
            raise ValidationError({'quantity': _('Quantity must be greater than zero')})

        if quantity > output.quantity:
            raise ValidationError({
                'quantity': _('Quantity cannot be greater than the output quantity')
            })

        return data


class BuildOutputCreateSerializer(serializers.Serializer):
    """Serializer for creating a new BuildOutput against a BuildOrder.

    URL pattern is "/api/build/<pk>/create-output/", where <pk> is the PK of a Build.

    The Build object is provided to the serializer context.
    """

    class Meta:
        """Serializer metaclass."""

        fields = [
            'quantity',
            'batch_code',
            'serial_numbers',
            'location',
            'auto_allocate',
        ]

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=Decimal(0),
        required=True,
        label=_('Quantity'),
        help_text=_('Enter quantity for build output'),
    )

    def get_build(self):
        """Return the Build instance associated with this serializer."""
        return self.context['build']

    def get_part(self):
        """Return the Part instance associated with the build."""
        return self.get_build().part

    def validate_quantity(self, quantity):
        """Validate the provided quantity field."""
        if quantity <= 0:
            raise ValidationError(_('Quantity must be greater than zero'))

        part = self.get_part()

        if int(quantity) != quantity:
            # Quantity must be an integer value if the part being built is trackable
            if part.trackable:
                raise ValidationError(
                    _('Integer quantity required for trackable parts')
                )

            if part.has_trackable_parts:
                raise ValidationError(
                    _(
                        'Integer quantity required, as the bill of materials contains trackable parts'
                    )
                )

        return quantity

    batch_code = serializers.CharField(
        required=False,
        allow_blank=True,
        default=generate_batch_code,
        label=_('Batch Code'),
        help_text=_('Batch code for this build output'),
    )

    serial_numbers = serializers.CharField(
        allow_blank=True,
        required=False,
        label=_('Serial Numbers'),
        help_text=_('Enter serial numbers for build outputs'),
    )

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        label=_('Location'),
        help_text=_('Stock location for build output'),
        required=False,
        allow_null=True,
    )

    def validate_serial_numbers(self, serial_numbers):
        """Clean the provided serial number string."""
        serial_numbers = serial_numbers.strip()

        return serial_numbers

    auto_allocate = serializers.BooleanField(
        required=False,
        default=False,
        allow_null=True,
        label=_('Auto Allocate Serial Numbers'),
        help_text=_(
            'Automatically allocate required items with matching serial numbers'
        ),
    )

    def validate(self, data):
        """Perform form validation."""
        part = self.get_part()

        # Cache a list of serial numbers (to be used in the "save" method)
        self.serials = None

        quantity = data['quantity']
        serial_numbers = data.get('serial_numbers', '')

        if part.trackable and not serial_numbers:
            raise ValidationError({
                'serial_numbers': _(
                    'Serial numbers must be provided for trackable parts'
                )
            })

        if serial_numbers:
            try:
                self.serials = InvenTree.helpers.extract_serial_numbers(
                    serial_numbers, quantity, part.get_latest_serial_number(), part=part
                )
            except DjangoValidationError as e:
                raise ValidationError({'serial_numbers': e.messages})

            # Check for conflicting serial numbesr
            existing = part.find_conflicting_serial_numbers(self.serials)

            if len(existing) > 0:
                msg = _('The following serial numbers already exist or are invalid')
                msg += ' : '
                msg += ','.join([str(e) for e in existing])

                raise ValidationError({'serial_numbers': msg})

        return data

    def save(self):
        """Generate the new build output(s)."""
        data = self.validated_data

        build = self.get_build()

        build.create_build_output(
            data['quantity'],
            serials=self.serials,
            batch=data.get('batch_code', ''),
            location=data.get('location', None),
            auto_allocate=data.get('auto_allocate', False),
            user=self.context['request'].user,
        )


class BuildOutputDeleteSerializer(serializers.Serializer):
    """DRF serializer for deleting (cancelling) one or more build outputs."""

    class Meta:
        """Serializer metaclass."""

        fields = ['outputs']

    outputs = BuildOutputSerializer(many=True, required=True)

    def validate(self, data):
        """Perform data validation for this serializer."""
        data = super().validate(data)

        outputs = data.get('outputs', [])

        if len(outputs) == 0:
            raise ValidationError(_('A list of build outputs must be provided'))

        return data

    def save(self):
        """'save' the serializer to delete the build outputs."""
        data = self.validated_data
        outputs = data.get('outputs', [])

        build = self.context['build']

        with transaction.atomic():
            for item in outputs:
                output = item['output']
                build.delete_output(output)


class BuildOutputScrapSerializer(serializers.Serializer):
    """Scrapping one or more build outputs."""

    class Meta:
        """Serializer metaclass."""

        fields = ['outputs', 'location', 'notes']

    outputs = BuildOutputQuantitySerializer(many=True, required=True)

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Location'),
        help_text=_('Stock location for scrapped outputs'),
    )

    discard_allocations = serializers.BooleanField(
        required=False,
        default=False,
        label=_('Discard Allocations'),
        help_text=_('Discard any stock allocations for scrapped outputs'),
    )

    notes = serializers.CharField(
        label=_('Notes'),
        help_text=_('Reason for scrapping build output(s)'),
        required=True,
        allow_blank=False,
    )

    def validate(self, data):
        """Perform validation on the serializer data."""
        super().validate(data)
        outputs = data.get('outputs', [])

        if len(outputs) == 0:
            raise ValidationError(_('A list of build outputs must be provided'))

        return data

    def save(self):
        """Save the serializer to scrap the build outputs."""
        build = self.context['build']
        request = self.context['request']
        data = self.validated_data
        outputs = data.get('outputs', [])

        # Scrap the build outputs
        with transaction.atomic():
            for item in outputs:
                output = item['output']
                quantity = item['quantity']
                build.scrap_build_output(
                    output,
                    quantity,
                    data.get('location', None),
                    user=request.user,
                    notes=data.get('notes', ''),
                    discard_allocations=data.get('discard_allocations', False),
                )


class BuildOutputCompleteSerializer(serializers.Serializer):
    """DRF serializer for completing one or more build outputs."""

    class Meta:
        """Serializer metaclass."""

        fields = [
            'outputs',
            'location',
            'status_custom_key',
            'accept_incomplete_allocation',
            'notes',
        ]

    outputs = BuildOutputSerializer(many=True, required=True)

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        required=True,
        many=False,
        label=_('Location'),
        help_text=_('Location for completed build outputs'),
    )

    status_custom_key = serializers.ChoiceField(
        choices=StockStatus.items(custom=True),
        default=StockStatus.OK.value,
        label=_('Status'),
    )

    accept_incomplete_allocation = serializers.BooleanField(
        default=False,
        required=False,
        label=_('Accept Incomplete Allocation'),
        help_text=_('Complete outputs if stock has not been fully allocated'),
    )

    notes = serializers.CharField(label=_('Notes'), required=False, allow_blank=True)

    def validate(self, data):
        """Perform data validation for this serializer."""
        super().validate(data)

        outputs = data.get('outputs', [])

        if common.settings.prevent_build_output_complete_on_incompleted_tests():
            errors = []
            for output in outputs:
                stock_item = output['output']
                if (
                    stock_item.hasRequiredTests()
                    and not stock_item.passedAllRequiredTests()
                ):
                    serial = stock_item.serial
                    errors.append(
                        _(f'Build output {serial} has not passed all required tests')
                    )

            if errors:
                raise ValidationError(errors)

        if len(outputs) == 0:
            raise ValidationError(_('A list of build outputs must be provided'))

        return data

    def save(self):
        """Save the serializer to complete the build outputs."""
        build = self.context['build']
        request = self.context['request']

        data = self.validated_data

        location = data.get('location', None)
        status = data.get('status_custom_key', StockStatus.OK.value)
        notes = data.get('notes', '')

        outputs = data.get('outputs', [])

        # Cache some calculated values which can be passed to each output
        required_tests = outputs[0]['output'].part.getRequiredTests()
        prevent_on_incomplete = (
            common.settings.prevent_build_output_complete_on_incompleted_tests()
        )

        # Mark the specified build outputs as "complete"
        with transaction.atomic():
            for item in outputs:
                output = item['output']

                build.complete_build_output(
                    output,
                    request.user,
                    location=location,
                    status=status,
                    notes=notes,
                    required_tests=required_tests,
                    prevent_on_incomplete=prevent_on_incomplete,
                )


class BuildIssueSerializer(serializers.Serializer):
    """DRF serializer for issuing a build order."""

    class Meta:
        """Serializer metaclass."""

        fields = []

    def save(self):
        """Issue the specified build order."""
        build = self.context['build']
        build.issue_build()


class BuildHoldSerializer(serializers.Serializer):
    """DRF serializer for placing a BuildOrder on hold."""

    class Meta:
        """Serializer metaclass."""

        fields = []

    def save(self):
        """Place the specified build on hold."""
        build = self.context['build']

        build.hold_build()


class BuildCancelSerializer(serializers.Serializer):
    """Cancel an active BuildOrder."""

    class Meta:
        """Serializer metaclass."""

        fields = ['remove_allocated_stock', 'remove_incomplete_outputs']

    def get_context_data(self):
        """Retrieve extra context data from this serializer."""
        build = self.context['build']

        return {
            'has_allocated_stock': build.is_partially_allocated(),
            'incomplete_outputs': build.incomplete_count,
            'completed_outputs': build.complete_count,
        }

    remove_allocated_stock = serializers.BooleanField(
        label=_('Consume Allocated Stock'),
        help_text=_('Consume any stock which has already been allocated to this build'),
        required=False,
        default=False,
    )

    remove_incomplete_outputs = serializers.BooleanField(
        label=_('Remove Incomplete Outputs'),
        help_text=_('Delete any build outputs which have not been completed'),
        required=False,
        default=False,
    )

    def save(self):
        """Cancel the specified build."""
        build = self.context['build']
        request = self.context['request']

        data = self.validated_data

        build.cancel_build(
            request.user,
            remove_allocated_stock=data.get('remove_allocated_stock', False),
            remove_incomplete_outputs=data.get('remove_incomplete_outputs', False),
        )


class OverallocationChoice:
    """Utility class to contain options for handling over allocated stock items."""

    REJECT = 'reject'
    ACCEPT = 'accept'
    TRIM = 'trim'

    OPTIONS = {
        REJECT: _('Not permitted'),
        ACCEPT: _('Accept as consumed by this build order'),
        TRIM: _('Deallocate before completing this build order'),
    }


class BuildCompleteSerializer(serializers.Serializer):
    """DRF serializer for marking a BuildOrder as complete."""

    class Meta:
        """Serializer metaclass."""

        fields = ['accept_overallocated', 'accept_unallocated', 'accept_incomplete']

    def get_context_data(self):
        """Retrieve extra context data for this serializer.

        This is so we can determine (at run time) whether the build is ready to be completed.
        """
        build = self.context['build']

        return {
            'overallocated': build.is_overallocated(),
            'allocated': build.are_untracked_parts_allocated,
            'remaining': build.remaining,
            'incomplete': build.incomplete_count,
        }

    accept_overallocated = serializers.ChoiceField(
        label=_('Overallocated Stock'),
        choices=list(OverallocationChoice.OPTIONS.items()),
        help_text=_(
            'How do you want to handle extra stock items assigned to the build order'
        ),
        required=False,
        default=OverallocationChoice.REJECT,
    )

    def validate_accept_overallocated(self, value):
        """Check if the 'accept_overallocated' field is required."""
        build = self.context['build']

        if build.is_overallocated() and value == OverallocationChoice.REJECT:
            raise ValidationError(_('Some stock items have been overallocated'))

        return value

    accept_unallocated = serializers.BooleanField(
        label=_('Accept Unallocated'),
        help_text=_(
            'Accept that stock items have not been fully allocated to this build order'
        ),
        required=False,
        default=False,
    )

    def validate_accept_unallocated(self, value):
        """Check if the 'accept_unallocated' field is required."""
        build = self.context['build']

        if not build.are_untracked_parts_allocated and not value:
            raise ValidationError(_('Required stock has not been fully allocated'))

        return value

    accept_incomplete = serializers.BooleanField(
        label=_('Accept Incomplete'),
        help_text=_(
            'Accept that the required number of build outputs have not been completed'
        ),
        required=False,
        default=False,
    )

    def validate_accept_incomplete(self, value):
        """Check if the 'accept_incomplete' field is required."""
        build = self.context['build']

        if build.remaining > 0 and not value:
            raise ValidationError(_('Required build quantity has not been completed'))

        return value

    def validate(self, data):
        """Perform validation of this serializer prior to saving."""
        build = self.context['build']

        if (
            get_global_setting('BUILDORDER_REQUIRE_CLOSED_CHILDS')
            and build.has_open_child_builds
        ):
            raise ValidationError(_('Build order has open child build orders'))

        if build.status != BuildStatus.PRODUCTION.value:
            raise ValidationError(_('Build order must be in production state'))

        if build.incomplete_count > 0:
            raise ValidationError(_('Build order has incomplete outputs'))

        return data

    def save(self):
        """Complete the specified build output."""
        request = self.context['request']
        build = self.context['build']

        data = self.validated_data

        build.complete_build(
            request.user,
            trim_allocated_stock=data.get(
                'accept_overallocated', OverallocationChoice.REJECT
            )
            == OverallocationChoice.TRIM,
        )


class BuildUnallocationSerializer(serializers.Serializer):
    """DRF serializer for unallocating stock from a BuildOrder.

    Allocated stock can be unallocated with a number of filters:

    - output: Filter against a particular build output (blank = untracked stock)
    - bom_item: Filter against a particular BOM line item
    """

    class Meta:
        """Serializer metaclass."""

        fields = ['build_line', 'output']

    build_line = serializers.PrimaryKeyRelatedField(
        queryset=BuildLine.objects.all(),
        many=False,
        allow_null=True,
        required=False,
        label=_('Build Line'),
    )

    output = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.filter(is_building=True),
        many=False,
        allow_null=True,
        required=False,
        label=_('Build output'),
    )

    def validate_output(self, stock_item):
        """Validation for the output StockItem instance. Stock item must point to the same build order!"""
        build = self.context['build']

        if stock_item and stock_item.build != build:
            raise ValidationError(_('Build output must point to the same build'))

        return stock_item

    def save(self):
        """Save the serializer data.

        This performs the actual unallocation against the build order
        """
        build = self.context['build']

        data = self.validated_data

        build.deallocate_stock(
            build_line=data.get('build_line', None), output=data.get('output', None)
        )


class BuildAllocationItemSerializer(serializers.Serializer):
    """A serializer for allocating a single stock item against a build order."""

    class Meta:
        """Serializer metaclass."""

        fields = ['build_item', 'stock_item', 'quantity', 'output']

    build_line = serializers.PrimaryKeyRelatedField(
        queryset=BuildLine.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Build Line Item'),
    )

    def validate_build_line(self, build_line):
        """Check if the parts match."""
        build = self.context['build']

        # BomItem should point to the same 'part' as the parent build
        if build.part != build_line.bom_item.part:
            # If not, it may be marked as "inherited" from a parent part
            if (
                build_line.bom_item.inherited
                and build.part
                in build_line.bom_item.part.get_descendants(include_self=False)
            ):
                pass
            else:
                raise ValidationError(
                    _('bom_item.part must point to the same part as the build order')
                )

        return build_line

    stock_item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    def validate_stock_item(self, stock_item):
        """Perform validation of the stock_item field."""
        if not stock_item.in_stock:
            raise ValidationError(_('Item must be in stock'))

        return stock_item

    quantity = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal(0), required=True
    )

    def validate_quantity(self, quantity):
        """Perform validation of the 'quantity' field."""
        if quantity <= 0:
            raise ValidationError(_('Quantity must be greater than zero'))

        return quantity

    output = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.filter(is_building=True),
        many=False,
        allow_null=True,
        required=False,
        label=_('Build Output'),
    )

    def validate(self, data):
        """Perform data validation for this item."""
        super().validate(data)

        build_line = data['build_line']
        stock_item = data['stock_item']
        quantity = data['quantity']
        output = data.get('output', None)

        # build = self.context['build']

        # TODO: Check that the "stock item" is valid for the referenced "sub_part"
        # Note: Because of allow_variants options, it may not be a direct match!

        # Check that the quantity does not exceed the available amount from the stock item
        q = stock_item.unallocated_quantity()

        if quantity > q:
            q = InvenTree.helpers.clean_decimal(q)

            raise ValidationError({'quantity': _(f'Available quantity ({q}) exceeded')})

        # Output *must* be set for trackable parts
        if output is None and build_line.bom_item.sub_part.trackable:
            raise ValidationError({
                'output': _(
                    'Build output must be specified for allocation of tracked parts'
                )
            })

        # Output *cannot* be set for un-tracked parts
        if output is not None and not build_line.bom_item.sub_part.trackable:
            raise ValidationError({
                'output': _(
                    'Build output cannot be specified for allocation of untracked parts'
                )
            })

        return data


class BuildAllocationSerializer(serializers.Serializer):
    """DRF serializer for allocation stock items against a build order."""

    class Meta:
        """Serializer metaclass."""

        fields = ['items']

    items = BuildAllocationItemSerializer(many=True)

    def validate(self, data):
        """Validation."""
        data = super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('Allocation items must be provided'))

        return data

    def save(self):
        """Perform the allocation."""
        data = self.validated_data

        items = data.get('items', [])

        with transaction.atomic():
            for item in items:
                build_line = item['build_line']
                stock_item = item['stock_item']
                quantity = item['quantity']
                output = item.get('output', None)

                # Ignore allocation for consumable BOM items
                if build_line.bom_item.consumable:
                    continue

                params = {
                    'build_line': build_line,
                    'stock_item': stock_item,
                    'install_into': output,
                }

                try:
                    if build_item := BuildItem.objects.filter(**params).first():
                        # Find an existing BuildItem for this stock item
                        # If it exists, increase the quantity
                        build_item.quantity += quantity
                        build_item.save()
                    else:
                        # Create a new BuildItem to allocate stock
                        build_item = BuildItem.objects.create(
                            quantity=quantity, **params
                        )
                except (ValidationError, DjangoValidationError) as exc:
                    # Catch model errors and re-throw as DRF errors
                    raise ValidationError(detail=serializers.as_serializer_error(exc))


class BuildAutoAllocationSerializer(serializers.Serializer):
    """DRF serializer for auto allocating stock items against a build order."""

    class Meta:
        """Serializer metaclass."""

        fields = [
            'location',
            'exclude_location',
            'interchangeable',
            'substitutes',
            'optional_items',
        ]

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        allow_null=True,
        required=False,
        label=_('Source Location'),
        help_text=_(
            'Stock location where parts are to be sourced (leave blank to take from any location)'
        ),
    )

    exclude_location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        many=False,
        allow_null=True,
        required=False,
        label=_('Exclude Location'),
        help_text=_('Exclude stock items from this selected location'),
    )

    interchangeable = serializers.BooleanField(
        default=False,
        label=_('Interchangeable Stock'),
        help_text=_('Stock items in multiple locations can be used interchangeably'),
    )

    substitutes = serializers.BooleanField(
        default=True,
        label=_('Substitute Stock'),
        help_text=_('Allow allocation of substitute parts'),
    )

    optional_items = serializers.BooleanField(
        default=False,
        label=_('Optional Items'),
        help_text=_('Allocate optional BOM items to build order'),
    )

    def save(self):
        """Perform the auto-allocation step."""
        import build.tasks
        import InvenTree.tasks

        data = self.validated_data

        build_order = self.context['build']

        if not InvenTree.tasks.offload_task(
            build.tasks.auto_allocate_build,
            build_order.pk,
            location=data.get('location', None),
            exclude_location=data.get('exclude_location', None),
            interchangeable=data['interchangeable'],
            substitutes=data['substitutes'],
            optional_items=data['optional_items'],
            group='build',
        ):
            raise ValidationError(_('Failed to start auto-allocation task'))


class BuildItemSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializes a BuildItem object, which is an allocation of a stock item against a build order."""

    # These fields are only used for data export
    export_only_fields = [
        'bom_part_id',
        'bom_part_name',
        'build_reference',
        'sku',
        'mpn',
        'location_name',
        'part_id',
        'part_name',
        'part_ipn',
        'part_description',
        'available_quantity',
        'item_batch_code',
        'item_serial',
        'item_packaging',
    ]

    class Meta:
        """Serializer metaclass."""

        model = BuildItem
        fields = [
            'pk',
            'build',
            'build_line',
            'install_into',
            'stock_item',
            'quantity',
            'location',
            # Detail fields, can be included or excluded
            'build_detail',
            'location_detail',
            'part_detail',
            'stock_item_detail',
            'supplier_part_detail',
            # The following fields are only used for data export
            'bom_reference',
            'bom_part_id',
            'bom_part_name',
            'build_reference',
            'location_name',
            'mpn',
            'sku',
            'part_id',
            'part_name',
            'part_ipn',
            'part_description',
            'available_quantity',
            'item_batch_code',
            'item_serial_number',
            'item_packaging',
        ]

    def __init__(self, *args, **kwargs):
        """Determine which extra details fields should be included."""
        part_detail = kwargs.pop('part_detail', True)
        location_detail = kwargs.pop('location_detail', True)
        stock_detail = kwargs.pop('stock_detail', True)
        build_detail = kwargs.pop('build_detail', False)

        super().__init__(*args, **kwargs)

        if not part_detail:
            self.fields.pop('part_detail', None)

        if not location_detail:
            self.fields.pop('location_detail', None)

        if not stock_detail:
            self.fields.pop('stock_item_detail', None)

        if not build_detail:
            self.fields.pop('build_detail', None)

    # Export-only fields
    sku = serializers.CharField(
        source='stock_item.supplier_part.SKU',
        label=_('Supplier Part Number'),
        read_only=True,
    )
    mpn = serializers.CharField(
        source='stock_item.supplier_part.manufacturer_part.MPN',
        label=_('Manufacturer Part Number'),
        read_only=True,
    )
    location_name = serializers.CharField(
        source='stock_item.location.name', label=_('Location Name'), read_only=True
    )
    build_reference = serializers.CharField(
        source='build.reference', label=_('Build Reference'), read_only=True
    )
    bom_reference = serializers.CharField(
        source='build_line.bom_item.reference', label=_('BOM Reference'), read_only=True
    )
    item_packaging = serializers.CharField(
        source='stock_item.packaging', label=_('Packaging'), read_only=True
    )

    # Part detail fields
    part_id = serializers.PrimaryKeyRelatedField(
        source='stock_item.part', label=_('Part ID'), many=False, read_only=True
    )
    part_name = serializers.CharField(
        source='stock_item.part.name', label=_('Part Name'), read_only=True
    )
    part_ipn = serializers.CharField(
        source='stock_item.part.IPN', label=_('Part IPN'), read_only=True
    )
    part_description = serializers.CharField(
        source='stock_item.part.description',
        label=_('Part Description'),
        read_only=True,
    )

    # BOM Item Part ID (it may be different to the allocated part)
    bom_part_id = serializers.PrimaryKeyRelatedField(
        source='build_line.bom_item.sub_part',
        label=_('BOM Part ID'),
        many=False,
        read_only=True,
    )
    bom_part_name = serializers.CharField(
        source='build_line.bom_item.sub_part.name',
        label=_('BOM Part Name'),
        read_only=True,
    )

    item_batch_code = serializers.CharField(
        source='stock_item.batch', label=_('Batch Code'), read_only=True
    )
    item_serial_number = serializers.CharField(
        source='stock_item.serial', label=_('Serial Number'), read_only=True
    )

    # Annotated fields
    build = serializers.PrimaryKeyRelatedField(
        source='build_line.build', many=False, read_only=True
    )

    # Extra (optional) detail fields
    part_detail = part_serializers.PartBriefSerializer(
        source='stock_item.part', many=False, read_only=True, pricing=False
    )
    stock_item_detail = StockItemSerializerBrief(source='stock_item', read_only=True)
    location = serializers.PrimaryKeyRelatedField(
        source='stock_item.location', many=False, read_only=True
    )
    location_detail = LocationBriefSerializer(
        source='stock_item.location', read_only=True
    )
    build_detail = BuildSerializer(
        source='build_line.build', many=False, read_only=True
    )
    supplier_part_detail = company.serializers.SupplierPartSerializer(
        source='stock_item.supplier_part', many=False, read_only=True, brief=True
    )

    quantity = InvenTreeDecimalField(label=_('Allocated Quantity'))
    available_quantity = InvenTreeDecimalField(
        source='stock_item.quantity', read_only=True, label=_('Available Quantity')
    )


class BuildLineSerializer(DataImportExportSerializerMixin, InvenTreeModelSerializer):
    """Serializer for a BuildItem object."""

    export_exclude_fields = ['allocations']

    export_only_fields = ['part_description', 'part_category_name']

    class Meta:
        """Serializer metaclass."""

        model = BuildLine
        fields = [
            'pk',
            'build',
            'bom_item',
            'quantity',
            # Build detail fields
            'build_reference',
            # BOM item detail fields
            'reference',
            'consumable',
            'optional',
            'testable',
            'trackable',
            'inherited',
            'allow_variants',
            # Part detail fields
            'part',
            'part_name',
            'part_IPN',
            'part_category_id',
            # Annotated fields
            'allocated',
            'in_production',
            'on_order',
            'available_stock',
            'available_substitute_stock',
            'available_variant_stock',
            'external_stock',
            # Related fields
            'allocations',
            # Extra fields only for data export
            'part_description',
            'part_category_name',
            # Extra detail (related field) serializers
            'bom_item_detail',
            'part_detail',
            'build_detail',
        ]

        read_only_fields = ['build', 'bom_item', 'allocations']

    def __init__(self, *args, **kwargs):
        """Determine which extra details fields should be included."""
        part_detail = kwargs.pop('part_detail', True)
        build_detail = kwargs.pop('build_detail', False)

        super().__init__(*args, **kwargs)

        if not part_detail:
            self.fields.pop('part_detail', None)

        if not build_detail:
            self.fields.pop('build_detail', None)

    # Build info fields
    build_reference = serializers.CharField(
        source='build.reference', label=_('Build Reference'), read_only=True
    )

    # Part info fields
    part = serializers.PrimaryKeyRelatedField(
        source='bom_item.sub_part', label=_('Part'), many=False, read_only=True
    )
    part_name = serializers.CharField(
        source='bom_item.sub_part.name', label=_('Part Name'), read_only=True
    )
    part_IPN = serializers.CharField(  # noqa: N815
        source='bom_item.sub_part.IPN', label=_('Part IPN'), read_only=True
    )

    part_description = serializers.CharField(
        source='bom_item.sub_part.description',
        label=_('Part Description'),
        read_only=True,
    )
    part_category_id = serializers.PrimaryKeyRelatedField(
        source='bom_item.sub_part.category', label=_('Part Category ID'), read_only=True
    )
    part_category_name = serializers.CharField(
        source='bom_item.sub_part.category.name',
        label=_('Part Category Name'),
        read_only=True,
    )

    allocations = BuildItemSerializer(many=True, read_only=True)

    # BOM item info fields
    reference = serializers.CharField(
        source='bom_item.reference', label=_('Reference'), read_only=True
    )
    consumable = serializers.BooleanField(
        source='bom_item.consumable', label=_('Consumable'), read_only=True
    )
    optional = serializers.BooleanField(
        source='bom_item.optional', label=_('Optional'), read_only=True
    )
    testable = serializers.BooleanField(
        source='bom_item.sub_part.testable', label=_('Testable'), read_only=True
    )
    trackable = serializers.BooleanField(
        source='bom_item.sub_part.trackable', label=_('Trackable'), read_only=True
    )
    inherited = serializers.BooleanField(
        source='bom_item.inherited', label=_('Inherited'), read_only=True
    )
    allow_variants = serializers.BooleanField(
        source='bom_item.allow_variants', label=_('Allow Variants'), read_only=True
    )

    quantity = serializers.FloatField(label=_('Quantity'))

    bom_item = serializers.PrimaryKeyRelatedField(label=_('BOM Item'), read_only=True)

    # Foreign key fields
    bom_item_detail = part_serializers.BomItemSerializer(
        source='bom_item',
        many=False,
        read_only=True,
        pricing=False,
        substitutes=False,
        sub_part_detail=False,
        part_detail=False,
    )

    part_detail = part_serializers.PartBriefSerializer(
        source='bom_item.sub_part', many=False, read_only=True, pricing=False
    )
    build_detail = BuildSerializer(
        source='build', part_detail=False, many=False, read_only=True
    )

    # Annotated (calculated) fields

    # Total quantity of allocated stock
    allocated = serializers.FloatField(label=_('Allocated Stock'), read_only=True)

    on_order = serializers.FloatField(label=_('On Order'), read_only=True)

    in_production = serializers.FloatField(label=_('In Production'), read_only=True)

    external_stock = serializers.FloatField(read_only=True, label=_('External Stock'))
    available_stock = serializers.FloatField(read_only=True, label=_('Available Stock'))
    available_substitute_stock = serializers.FloatField(
        read_only=True, label=_('Available Substitute Stock')
    )
    available_variant_stock = serializers.FloatField(
        read_only=True, label=_('Available Variant Stock')
    )

    @staticmethod
    def annotate_queryset(queryset, build=None):
        """Add extra annotations to the queryset.

        Annotations:
        - allocated: Total stock quantity allocated against this build line
        - available: Total stock available for allocation against this build line
        - on_order: Total stock on order for this build line
        - in_production: Total stock currently in production for this build line

        Arguments:
            queryset: The queryset to annotate
            build: The build order to filter against (optional)

        Note: If the 'build' is provided, we can use it to filter available stock, depending on the specified location for the build

        """
        queryset = queryset.select_related(
            'build',
            'build__part',
            'build__part__pricing_data',
            'bom_item',
            'bom_item__part',
            'bom_item__part__pricing_data',
            'bom_item__sub_part',
            'bom_item__sub_part__pricing_data',
        )

        # Pre-fetch related fields
        queryset = queryset.prefetch_related(
            'allocations',
            'allocations__stock_item',
            'allocations__stock_item__part',
            'allocations__stock_item__location',
            'bom_item__sub_part__stock_items',
            'bom_item__sub_part__stock_items__allocations',
            'bom_item__sub_part__stock_items__sales_order_allocations',
            'bom_item__substitutes',
            'bom_item__substitutes__part__stock_items',
            'bom_item__substitutes__part__stock_items__allocations',
            'bom_item__substitutes__part__stock_items__sales_order_allocations',
        )

        # Defer expensive fields which we do not need for this serializer

        queryset = (
            queryset.defer(
                'build__lft',
                'build__rght',
                'build__level',
                'build__tree_id',
                'build__destination',
                'build__take_from',
                'build__completed_by',
                'build__issued_by',
                'build__sales_order',
                'build__parent',
                'build__notes',
                'build__metadata',
                'build__responsible',
                'build__barcode_data',
                'build__barcode_hash',
                'build__project_code',
            )
            .defer('bom_item__metadata')
            .defer(
                'bom_item__part__lft',
                'bom_item__part__rght',
                'bom_item__part__level',
                'bom_item__part__tree_id',
                'bom_item__part__tags',
                'bom_item__part__notes',
                'bom_item__part__variant_of',
                'bom_item__part__revision_of',
                'bom_item__part__creation_user',
                'bom_item__part__bom_checked_by',
                'bom_item__part__default_supplier',
                'bom_item__part__responsible_owner',
            )
            .defer(
                'bom_item__sub_part__lft',
                'bom_item__sub_part__rght',
                'bom_item__sub_part__level',
                'bom_item__sub_part__tree_id',
                'bom_item__sub_part__tags',
                'bom_item__sub_part__notes',
                'bom_item__sub_part__variant_of',
                'bom_item__sub_part__revision_of',
                'bom_item__sub_part__creation_user',
                'bom_item__sub_part__bom_checked_by',
                'bom_item__sub_part__default_supplier',
                'bom_item__sub_part__responsible_owner',
            )
        )

        # Annotate the "allocated" quantity
        queryset = queryset.annotate(
            allocated=Coalesce(
                Sum('allocations__quantity'), 0, output_field=models.DecimalField()
            )
        )

        ref = 'bom_item__sub_part__'

        stock_filter = None

        if build is not None and build.take_from is not None:
            location = build.take_from
            # Filter by locations below the specified location
            stock_filter = Q(
                location__tree_id=location.tree_id,
                location__lft__gte=location.lft,
                location__rght__lte=location.rght,
                location__level__gte=location.level,
            )

        # Annotate the "in_production" quantity
        queryset = queryset.annotate(
            in_production=part.filters.annotate_in_production_quantity(reference=ref)
        )

        # Annotate the "on_order" quantity
        queryset = queryset.annotate(
            on_order=part.filters.annotate_on_order_quantity(reference=ref)
        )

        # Annotate the "available" quantity
        queryset = queryset.alias(
            total_stock=part.filters.annotate_total_stock(
                reference=ref, filter=stock_filter
            ),
            allocated_to_sales_orders=part.filters.annotate_sales_order_allocations(
                reference=ref
            ),
            allocated_to_build_orders=part.filters.annotate_build_order_allocations(
                reference=ref
            ),
        )

        # Calculate 'available_stock' based on previously annotated fields
        queryset = queryset.annotate(
            available_stock=ExpressionWrapper(
                F('total_stock')
                - F('allocated_to_sales_orders')
                - F('allocated_to_build_orders'),
                output_field=models.DecimalField(),
            )
        )

        external_stock_filter = Q(location__external=True)

        if stock_filter:
            external_stock_filter &= stock_filter

        # Add 'external stock' annotations
        queryset = queryset.annotate(
            external_stock=part.filters.annotate_total_stock(
                reference=ref, filter=external_stock_filter
            )
        )

        ref = 'bom_item__substitutes__part__'

        # Extract similar information for any 'substitute' parts
        queryset = queryset.alias(
            substitute_stock=part.filters.annotate_total_stock(
                reference=ref, filter=stock_filter
            ),
            substitute_build_allocations=part.filters.annotate_build_order_allocations(
                reference=ref
            ),
            substitute_sales_allocations=part.filters.annotate_sales_order_allocations(
                reference=ref
            ),
        )

        # Calculate 'available_substitute_stock' field
        queryset = queryset.annotate(
            available_substitute_stock=ExpressionWrapper(
                F('substitute_stock')
                - F('substitute_build_allocations')
                - F('substitute_sales_allocations'),
                output_field=models.DecimalField(),
            )
        )

        # Annotate the queryset with 'available variant stock' information
        variant_stock_query = part.filters.variant_stock_query(
            reference='bom_item__sub_part__', filter=stock_filter
        )

        queryset = queryset.alias(
            variant_stock_total=part.filters.annotate_variant_quantity(
                variant_stock_query, reference='quantity'
            ),
            variant_bo_allocations=part.filters.annotate_variant_quantity(
                variant_stock_query, reference='sales_order_allocations__quantity'
            ),
            variant_so_allocations=part.filters.annotate_variant_quantity(
                variant_stock_query, reference='allocations__quantity'
            ),
        )

        queryset = queryset.annotate(
            available_variant_stock=ExpressionWrapper(
                F('variant_stock_total')
                - F('variant_bo_allocations')
                - F('variant_so_allocations'),
                output_field=FloatField(),
            )
        )

        return queryset
