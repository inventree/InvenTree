"""JSON serializers for Build API."""

from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from django.db import models
from django.db.models import ExpressionWrapper, F, FloatField
from django.db.models import Case, Sum, When, Value
from django.db.models import BooleanField, Q
from django.db.models.functions import Coalesce

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from sql_util.utils import SubquerySum

from InvenTree.serializers import InvenTreeModelSerializer, InvenTreeAttachmentSerializer
from InvenTree.serializers import UserSerializer

import InvenTree.helpers
from InvenTree.serializers import InvenTreeDecimalField
from InvenTree.status_codes import BuildStatusGroups, StockStatus

from stock.models import generate_batch_code, StockItem, StockLocation
from stock.serializers import StockItemSerializerBrief, LocationSerializer

from common.serializers import ProjectCodeSerializer
import part.filters
from part.serializers import BomItemSerializer, PartSerializer, PartBriefSerializer
from users.serializers import OwnerSerializer

from .models import Build, BuildLine, BuildItem, BuildOrderAttachment


class BuildSerializer(InvenTreeModelSerializer):
    """Serializes a Build object."""

    class Meta:
        """Serializer metaclass"""
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
            'part_detail',
            'project_code',
            'project_code_detail',
            'overdue',
            'reference',
            'sales_order',
            'quantity',
            'status',
            'status_text',
            'target_date',
            'take_from',
            'notes',
            'link',
            'issued_by',
            'issued_by_detail',
            'responsible',
            'responsible_detail',
            'priority',
        ]

        read_only_fields = [
            'completed',
            'creation_date',
            'completion_data',
            'status',
            'status_text',
        ]

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    quantity = InvenTreeDecimalField()

    overdue = serializers.BooleanField(required=False, read_only=True)

    issued_by_detail = UserSerializer(source='issued_by', read_only=True)

    responsible_detail = OwnerSerializer(source='responsible', read_only=True)

    barcode_hash = serializers.CharField(read_only=True)

    project_code_detail = ProjectCodeSerializer(source='project_code', many=False, read_only=True)

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
                    Build.OVERDUE_FILTER, then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField())
            )
        )

        return queryset

    def __init__(self, *args, **kwargs):
        """Determine if extra serializer fields are required"""
        part_detail = kwargs.pop('part_detail', True)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

    reference = serializers.CharField(required=True)

    def validate_reference(self, reference):
        """Custom validation for the Build reference field"""
        # Ensure the reference matches the required pattern
        Build.validate_reference_field(reference)

        return reference


class BuildOutputSerializer(serializers.Serializer):
    """Serializer for a "BuildOutput".

    Note that a "BuildOutput" is really just a StockItem which is "in production"!
    """

    class Meta:
        """Serializer metaclass"""
        fields = [
            'output',
        ]

    output = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Build Output'),
    )

    def validate_output(self, output):
        """Perform validation for the output (StockItem) provided to the serializer"""
        build = self.context['build']

        # As this serializer can be used in multiple contexts, we need to work out why we are here
        to_complete = self.context.get('to_complete', False)

        # The stock item must point to the build
        if output.build != build:
            raise ValidationError(_("Build output does not match the parent build"))

        # The part must match!
        if output.part != build.part:
            raise ValidationError(_("Output part does not match BuildOrder part"))

        # The build output must be "in production"
        if not output.is_building:
            raise ValidationError(_("This build output has already been completed"))

        if to_complete:

            # The build output must have all tracked parts allocated
            if not build.is_output_fully_allocated(output):

                # Check if the user has specified that incomplete allocations are ok
                accept_incomplete = InvenTree.helpers.str2bool(self.context['request'].data.get('accept_incomplete_allocation', False))

                if not accept_incomplete:
                    raise ValidationError(_("This build output is not fully allocated"))

        return output


class BuildOutputQuantitySerializer(BuildOutputSerializer):
    """Serializer for a single build output, with additional quantity field"""

    class Meta:
        """Serializer metaclass"""
        fields = BuildOutputSerializer.Meta.fields + [
            'quantity',
        ]

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=0,
        required=True,
        label=_('Quantity'),
        help_text=_('Enter quantity for build output'),
    )

    def validate(self, data):
        """Validate the serializer data"""
        data = super().validate(data)

        output = data.get('output')
        quantity = data.get('quantity')

        if quantity <= 0:
            raise ValidationError({
                'quantity': _('Quantity must be greater than zero')
            })

        if quantity > output.quantity:
            raise ValidationError({
                'quantity': _("Quantity cannot be greater than the output quantity")
            })

        return data


class BuildOutputCreateSerializer(serializers.Serializer):
    """Serializer for creating a new BuildOutput against a BuildOrder.

    URL pattern is "/api/build/<pk>/create-output/", where <pk> is the PK of a Build.

    The Build object is provided to the serializer context.
    """

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=0,
        required=True,
        label=_('Quantity'),
        help_text=_('Enter quantity for build output'),
    )

    def get_build(self):
        """Return the Build instance associated with this serializer"""
        return self.context["build"]

    def get_part(self):
        """Return the Part instance associated with the build"""
        return self.get_build().part

    def validate_quantity(self, quantity):
        """Validate the provided quantity field"""
        if quantity <= 0:
            raise ValidationError(_("Quantity must be greater than zero"))

        part = self.get_part()

        if int(quantity) != quantity:
            # Quantity must be an integer value if the part being built is trackable
            if part.trackable:
                raise ValidationError(_("Integer quantity required for trackable parts"))

            if part.has_trackable_parts:
                raise ValidationError(_("Integer quantity required, as the bill of materials contains trackable parts"))

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

    def validate_serial_numbers(self, serial_numbers):
        """Clean the provided serial number string"""
        serial_numbers = serial_numbers.strip()

        return serial_numbers

    auto_allocate = serializers.BooleanField(
        required=False,
        default=False,
        allow_null=True,
        label=_('Auto Allocate Serial Numbers'),
        help_text=_('Automatically allocate required items with matching serial numbers'),
    )

    def validate(self, data):
        """Perform form validation."""
        part = self.get_part()

        # Cache a list of serial numbers (to be used in the "save" method)
        self.serials = None

        quantity = data['quantity']
        serial_numbers = data.get('serial_numbers', '')

        if serial_numbers:

            try:
                self.serials = InvenTree.helpers.extract_serial_numbers(
                    serial_numbers,
                    quantity,
                    part.get_latest_serial_number()
                )
            except DjangoValidationError as e:
                raise ValidationError({
                    'serial_numbers': e.messages,
                })

            # Check for conflicting serial numbesr
            existing = []

            for serial in self.serials:
                if not part.validate_serial_number(serial):
                    existing.append(serial)

            if len(existing) > 0:

                msg = _("The following serial numbers already exist or are invalid")
                msg += " : "
                msg += ",".join([str(e) for e in existing])

                raise ValidationError({
                    'serial_numbers': msg,
                })

        return data

    def save(self):
        """Generate the new build output(s)"""
        data = self.validated_data

        quantity = data['quantity']
        batch_code = data.get('batch_code', '')
        auto_allocate = data.get('auto_allocate', False)

        build = self.get_build()
        user = self.context['request'].user

        build.create_build_output(
            quantity,
            serials=self.serials,
            batch=batch_code,
            auto_allocate=auto_allocate,
            user=user,
        )


class BuildOutputDeleteSerializer(serializers.Serializer):
    """DRF serializer for deleting (cancelling) one or more build outputs."""

    class Meta:
        """Serializer metaclass"""
        fields = [
            'outputs',
        ]

    outputs = BuildOutputSerializer(
        many=True,
        required=True,
    )

    def validate(self, data):
        """Perform data validation for this serializer"""
        data = super().validate(data)

        outputs = data.get('outputs', [])

        if len(outputs) == 0:
            raise ValidationError(_("A list of build outputs must be provided"))

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
    """DRF serializer for scrapping one or more build outputs"""

    class Meta:
        """Serializer metaclass"""
        fields = [
            'outputs',
            'location',
            'notes',
        ]

    outputs = BuildOutputQuantitySerializer(
        many=True,
        required=True,
    )

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
        """Perform validation on the serializer data"""
        super().validate(data)
        outputs = data.get('outputs', [])

        if len(outputs) == 0:
            raise ValidationError(_("A list of build outputs must be provided"))

        return data

    def save(self):
        """Save the serializer to scrap the build outputs"""
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
                    discard_allocations=data.get('discard_allocations', False)
                )


class BuildOutputCompleteSerializer(serializers.Serializer):
    """DRF serializer for completing one or more build outputs."""

    class Meta:
        """Serializer metaclass"""
        fields = [
            'outputs',
            'location',
            'status',
            'accept_incomplete_allocation',
            'notes',
        ]

    outputs = BuildOutputSerializer(
        many=True,
        required=True,
    )

    location = serializers.PrimaryKeyRelatedField(
        queryset=StockLocation.objects.all(),
        required=True,
        many=False,
        label=_("Location"),
        help_text=_("Location for completed build outputs"),
    )

    status = serializers.ChoiceField(
        choices=StockStatus.items(),
        default=StockStatus.OK.value,
        label=_("Status"),
    )

    accept_incomplete_allocation = serializers.BooleanField(
        default=False,
        required=False,
        label=_('Accept Incomplete Allocation'),
        help_text=_('Complete outputs if stock has not been fully allocated'),
    )

    notes = serializers.CharField(
        label=_("Notes"),
        required=False,
        allow_blank=True,
    )

    def validate(self, data):
        """Perform data validation for this serializer"""
        super().validate(data)

        outputs = data.get('outputs', [])

        if len(outputs) == 0:
            raise ValidationError(_("A list of build outputs must be provided"))

        return data

    def save(self):
        """Save the serializer to complete the build outputs."""
        build = self.context['build']
        request = self.context['request']

        data = self.validated_data

        location = data['location']
        status = data['status']
        notes = data.get('notes', '')

        outputs = data.get('outputs', [])

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
                )


class BuildCancelSerializer(serializers.Serializer):
    """DRF serializer class for cancelling an active BuildOrder"""

    class Meta:
        """Serializer metaclass"""
        fields = [
            'remove_allocated_stock',
            'remove_incomplete_outputs',
        ]

    def get_context_data(self):
        """Retrieve extra context data from this serializer"""
        build = self.context['build']

        return {
            'has_allocated_stock': build.is_partially_allocated(),
            'incomplete_outputs': build.incomplete_count,
            'completed_outputs': build.complete_count,
        }

    remove_allocated_stock = serializers.BooleanField(
        label=_('Remove Allocated Stock'),
        help_text=_('Subtract any stock which has already been allocated to this build'),
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
        """Cancel the specified build"""
        build = self.context['build']
        request = self.context['request']

        data = self.validated_data

        build.cancel_build(
            request.user,
            remove_allocated_stock=data.get('remove_unallocated_stock', False),
            remove_incomplete_outputs=data.get('remove_incomplete_outputs', False),
        )


class OverallocationChoice():
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
        help_text=_('How do you want to handle extra stock items assigned to the build order'),
        required=False,
        default=OverallocationChoice.REJECT,
    )

    def validate_accept_overallocated(self, value):
        """Check if the 'accept_overallocated' field is required"""
        build = self.context['build']

        if build.is_overallocated() and value == OverallocationChoice.REJECT:
            raise ValidationError(_('Some stock items have been overallocated'))

        return value

    accept_unallocated = serializers.BooleanField(
        label=_('Accept Unallocated'),
        help_text=_('Accept that stock items have not been fully allocated to this build order'),
        required=False,
        default=False,
    )

    def validate_accept_unallocated(self, value):
        """Check if the 'accept_unallocated' field is required"""
        build = self.context['build']

        if not build.are_untracked_parts_allocated and not value:
            raise ValidationError(_('Required stock has not been fully allocated'))

        return value

    accept_incomplete = serializers.BooleanField(
        label=_('Accept Incomplete'),
        help_text=_('Accept that the required number of build outputs have not been completed'),
        required=False,
        default=False,
    )

    def validate_accept_incomplete(self, value):
        """Check if the 'accept_incomplete' field is required"""
        build = self.context['build']

        if build.remaining > 0 and not value:
            raise ValidationError(_('Required build quantity has not been completed'))

        return value

    def validate(self, data):
        """Perform validation of this serializer prior to saving"""
        build = self.context['build']

        if build.incomplete_count > 0:
            raise ValidationError(_("Build order has incomplete outputs"))

        return data

    def save(self):
        """Complete the specified build output"""
        request = self.context['request']
        build = self.context['build']

        data = self.validated_data
        if data.get('accept_overallocated', OverallocationChoice.REJECT) == OverallocationChoice.TRIM:
            build.trim_allocated_stock()

        build.complete_build(request.user)


class BuildUnallocationSerializer(serializers.Serializer):
    """DRF serializer for unallocating stock from a BuildOrder.

    Allocated stock can be unallocated with a number of filters:

    - output: Filter against a particular build output (blank = untracked stock)
    - bom_item: Filter against a particular BOM line item
    """

    build_line = serializers.PrimaryKeyRelatedField(
        queryset=BuildLine.objects.all(),
        many=False,
        allow_null=True,
        required=False,
        label=_('Build Line'),
    )

    output = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.filter(
            is_building=True,
        ),
        many=False,
        allow_null=True,
        required=False,
        label=_("Build output"),
    )

    def validate_output(self, stock_item):
        """Validation for the output StockItem instance. Stock item must point to the same build order!"""
        build = self.context['build']

        if stock_item and stock_item.build != build:
            raise ValidationError(_("Build output must point to the same build"))

        return stock_item

    def save(self):
        """Save the serializer data.

        This performs the actual unallocation against the build order
        """
        build = self.context['build']

        data = self.validated_data

        build.deallocate_stock(
            build_line=data['build_line'],
            output=data['output']
        )


class BuildAllocationItemSerializer(serializers.Serializer):
    """A serializer for allocating a single stock item against a build order."""

    class Meta:
        """Serializer metaclass"""
        fields = [
            'build_item',
            'stock_item',
            'quantity',
            'output',
        ]

    build_line = serializers.PrimaryKeyRelatedField(
        queryset=BuildLine.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Build Line Item'),
    )

    def validate_build_line(self, build_line):
        """Check if the parts match"""
        build = self.context['build']

        # BomItem should point to the same 'part' as the parent build
        if build.part != build_line.bom_item.part:

            # If not, it may be marked as "inherited" from a parent part
            if build_line.bom_item.inherited and build.part in build_line.bom_item.part.get_descendants(include_self=False):
                pass
            else:
                raise ValidationError(_("bom_item.part must point to the same part as the build order"))

        return build_line

    stock_item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    def validate_stock_item(self, stock_item):
        """Perform validation of the stock_item field"""
        if not stock_item.in_stock:
            raise ValidationError(_("Item must be in stock"))

        return stock_item

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=0,
        required=True
    )

    def validate_quantity(self, quantity):
        """Perform validation of the 'quantity' field"""
        if quantity <= 0:
            raise ValidationError(_("Quantity must be greater than zero"))

        return quantity

    output = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.filter(is_building=True),
        many=False,
        allow_null=True,
        required=False,
        label=_('Build Output'),
    )

    def validate(self, data):
        """Perform data validation for this item"""
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

            raise ValidationError({
                'quantity': _(f"Available quantity ({q}) exceeded")
            })

        # Output *must* be set for trackable parts
        if output is None and build_line.bom_item.sub_part.trackable:
            raise ValidationError({
                'output': _('Build output must be specified for allocation of tracked parts'),
            })

        # Output *cannot* be set for un-tracked parts
        if output is not None and not build_line.bom_item.sub_part.trackable:

            raise ValidationError({
                'output': _('Build output cannot be specified for allocation of untracked parts'),
            })

        return data


class BuildAllocationSerializer(serializers.Serializer):
    """DRF serializer for allocation stock items against a build order."""

    class Meta:
        """Serializer metaclass"""
        fields = [
            'items',
        ]

    items = BuildAllocationItemSerializer(many=True)

    def validate(self, data):
        """Validation."""
        data = super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('Allocation items must be provided'))

        return data

    def save(self):
        """Perform the allocation"""
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

                try:
                    # Create a new BuildItem to allocate stock
                    build_item, created = BuildItem.objects.get_or_create(
                        build_line=build_line,
                        stock_item=stock_item,
                        install_into=output,
                    )
                    if created:
                        build_item.quantity = quantity
                    else:
                        build_item.quantity += quantity
                    build_item.save()
                except (ValidationError, DjangoValidationError) as exc:
                    # Catch model errors and re-throw as DRF errors
                    raise ValidationError(detail=serializers.as_serializer_error(exc))


class BuildAutoAllocationSerializer(serializers.Serializer):
    """DRF serializer for auto allocating stock items against a build order."""

    class Meta:
        """Serializer metaclass"""
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
        help_text=_('Stock location where parts are to be sourced (leave blank to take from any location)'),
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
        """Perform the auto-allocation step"""
        data = self.validated_data

        build = self.context['build']

        build.auto_allocate_stock(
            location=data.get('location', None),
            exclude_location=data.get('exclude_location', None),
            interchangeable=data['interchangeable'],
            substitutes=data['substitutes'],
            optional_items=data['optional_items'],
        )


class BuildItemSerializer(InvenTreeModelSerializer):
    """Serializes a BuildItem object."""

    class Meta:
        """Serializer metaclass"""
        model = BuildItem
        fields = [
            'pk',
            'build',
            'build_line',
            'install_into',
            'stock_item',
            'quantity',
            'location_detail',
            'part_detail',
            'stock_item_detail',
            'build_detail',
        ]

    # Annotated fields
    build = serializers.PrimaryKeyRelatedField(source='build_line.build', many=False, read_only=True)

    # Extra (optional) detail fields
    part_detail = PartBriefSerializer(source='stock_item.part', many=False, read_only=True, pricing=False)
    stock_item_detail = StockItemSerializerBrief(source='stock_item', read_only=True)
    location_detail = LocationSerializer(source='stock_item.location', read_only=True)
    build_detail = BuildSerializer(source='build_line.build', many=False, read_only=True)

    quantity = InvenTreeDecimalField()

    def __init__(self, *args, **kwargs):
        """Determine which extra details fields should be included"""
        part_detail = kwargs.pop('part_detail', True)
        location_detail = kwargs.pop('location_detail', True)
        stock_detail = kwargs.pop('stock_detail', False)
        build_detail = kwargs.pop('build_detail', False)

        super().__init__(*args, **kwargs)

        if not part_detail:
            self.fields.pop('part_detail')

        if not location_detail:
            self.fields.pop('location_detail')

        if not stock_detail:
            self.fields.pop('stock_item_detail')

        if not build_detail:
            self.fields.pop('build_detail')


class BuildLineSerializer(InvenTreeModelSerializer):
    """Serializer for a BuildItem object."""

    class Meta:
        """Serializer metaclass"""

        model = BuildLine
        fields = [
            'pk',
            'build',
            'bom_item',
            'bom_item_detail',
            'part_detail',
            'quantity',
            'allocations',

            # Annotated fields
            'allocated',
            'in_production',
            'on_order',
            'available_stock',
            'available_substitute_stock',
            'available_variant_stock',
            'total_available_stock',
        ]

        read_only_fields = [
            'build',
            'bom_item',
            'allocations',
        ]

    quantity = serializers.FloatField()

    bom_item = serializers.PrimaryKeyRelatedField(label=_('Bom Item'), read_only=True)

    # Foreign key fields
    bom_item_detail = BomItemSerializer(source='bom_item', many=False, read_only=True, pricing=False)
    part_detail = PartSerializer(source='bom_item.sub_part', many=False, read_only=True, pricing=False)
    allocations = BuildItemSerializer(many=True, read_only=True)

    # Annotated (calculated) fields
    allocated = serializers.FloatField(
        label=_('Allocated Stock'),
        read_only=True
    )

    on_order = serializers.FloatField(
        label=_('On Order'),
        read_only=True
    )

    in_production = serializers.FloatField(
        label=_('In Production'),
        read_only=True
    )

    available_stock = serializers.FloatField(
        label=_('Available Stock'),
        read_only=True
    )

    available_substitute_stock = serializers.FloatField(read_only=True)
    available_variant_stock = serializers.FloatField(read_only=True)
    total_available_stock = serializers.FloatField(read_only=True)

    @staticmethod
    def annotate_queryset(queryset):
        """Add extra annotations to the queryset:

        - allocated: Total stock quantity allocated against this build line
        - available: Total stock available for allocation against this build line
        - on_order: Total stock on order for this build line
        - in_production: Total stock currently in production for this build line
        """
        queryset = queryset.select_related(
            'build', 'bom_item',
        )

        # Pre-fetch related fields
        queryset = queryset.prefetch_related(
            'bom_item__sub_part',
            'bom_item__sub_part__stock_items',
            'bom_item__sub_part__stock_items__allocations',
            'bom_item__sub_part__stock_items__sales_order_allocations',
            'bom_item__sub_part__tags',

            'bom_item__substitutes',
            'bom_item__substitutes__part__stock_items',
            'bom_item__substitutes__part__stock_items__allocations',
            'bom_item__substitutes__part__stock_items__sales_order_allocations',

            'allocations',
            'allocations__stock_item',
            'allocations__stock_item__part',
            'allocations__stock_item__location',
            'allocations__stock_item__location__tags',
        )

        # Annotate the "allocated" quantity
        # Difficulty: Easy
        queryset = queryset.annotate(
            allocated=Coalesce(
                Sum('allocations__quantity'), 0,
                output_field=models.DecimalField()
            ),
        )

        ref = 'bom_item__sub_part__'

        # Annotate the "in_production" quantity
        queryset = queryset.annotate(
            in_production=part.filters.annotate_in_production_quantity(reference=ref)
        )

        # Annotate the "on_order" quantity
        # Difficulty: Medium
        queryset = queryset.annotate(
            on_order=part.filters.annotate_on_order_quantity(reference=ref),
        )

        # Annotate the "available" quantity
        # TODO: In the future, this should be refactored.
        # TODO: Note that part.serializers.BomItemSerializer also has a similar annotation
        queryset = queryset.alias(
            total_stock=part.filters.annotate_total_stock(reference=ref),
            allocated_to_sales_orders=part.filters.annotate_sales_order_allocations(reference=ref),
            allocated_to_build_orders=part.filters.annotate_build_order_allocations(reference=ref),
        )

        # Calculate 'available_stock' based on previously annotated fields
        queryset = queryset.annotate(
            available_stock=ExpressionWrapper(
                F('total_stock') - F('allocated_to_sales_orders') - F('allocated_to_build_orders'),
                output_field=models.DecimalField(),
            )
        )

        ref = 'bom_item__substitutes__part__'

        # Extract similar information for any 'substitute' parts
        queryset = queryset.alias(
            substitute_stock=part.filters.annotate_total_stock(reference=ref),
            substitute_build_allocations=part.filters.annotate_build_order_allocations(reference=ref),
            substitute_sales_allocations=part.filters.annotate_sales_order_allocations(reference=ref)
        )

        # Calculate 'available_substitute_stock' field
        queryset = queryset.annotate(
            available_substitute_stock=ExpressionWrapper(
                F('substitute_stock') - F('substitute_build_allocations') - F('substitute_sales_allocations'),
                output_field=models.DecimalField(),
            )
        )

        # Annotate the queryset with 'available variant stock' information
        variant_stock_query = part.filters.variant_stock_query(reference='bom_item__sub_part__')

        queryset = queryset.alias(
            variant_stock_total=part.filters.annotate_variant_quantity(variant_stock_query, reference='quantity'),
            variant_bo_allocations=part.filters.annotate_variant_quantity(variant_stock_query, reference='sales_order_allocations__quantity'),
            variant_so_allocations=part.filters.annotate_variant_quantity(variant_stock_query, reference='allocations__quantity'),
        )

        queryset = queryset.annotate(
            available_variant_stock=ExpressionWrapper(
                F('variant_stock_total') - F('variant_bo_allocations') - F('variant_so_allocations'),
                output_field=FloatField(),
            )
        )

        # Annotate with the 'total available stock'
        queryset = queryset.annotate(
            total_available_stock=ExpressionWrapper(
                F('available_stock') + F('available_substitute_stock') + F('available_variant_stock'),
                output_field=FloatField(),
            )
        )

        return queryset


class BuildAttachmentSerializer(InvenTreeAttachmentSerializer):
    """Serializer for a BuildAttachment."""

    class Meta:
        """Serializer metaclass"""
        model = BuildOrderAttachment

        fields = InvenTreeAttachmentSerializer.attachment_fields([
            'build',
        ])
