"""JSON serializers for Build API."""

from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from django.db.models import Case, When, Value
from django.db.models import BooleanField

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from InvenTree.serializers import InvenTreeModelSerializer, InvenTreeAttachmentSerializer
from InvenTree.serializers import ReferenceIndexingSerializerMixin, UserSerializer

import InvenTree.helpers
from InvenTree.helpers import extract_serial_numbers
from InvenTree.serializers import InvenTreeDecimalField
from InvenTree.status_codes import StockStatus

from stock.models import StockItem, StockLocation
from stock.serializers import StockItemSerializerBrief, LocationSerializer

from part.models import BomItem
from part.serializers import PartSerializer, PartBriefSerializer
from users.serializers import OwnerSerializer

from .models import Build, BuildItem, BuildOrderAttachment


class BuildSerializer(ReferenceIndexingSerializerMixin, InvenTreeModelSerializer):
    """Serializes a Build object."""

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    quantity = InvenTreeDecimalField()

    overdue = serializers.BooleanField(required=False, read_only=True)

    issued_by_detail = UserSerializer(source='issued_by', read_only=True)

    responsible_detail = OwnerSerializer(source='responsible', read_only=True)

    @staticmethod
    def annotate_queryset(queryset):
        """Add custom annotations to the BuildSerializer queryset, performing database queries as efficiently as possible.

        The following annoted fields are added:

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

    class Meta:
        """Serializer metaclass"""
        model = Build
        fields = [
            'pk',
            'url',
            'title',
            'batch',
            'creation_date',
            'completed',
            'completion_date',
            'destination',
            'parent',
            'part',
            'part_detail',
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
        ]

        read_only_fields = [
            'completed',
            'creation_date',
            'completion_data',
            'status',
            'status_text',
        ]


class BuildOutputSerializer(serializers.Serializer):
    """Serializer for a "BuildOutput".

    Note that a "BuildOutput" is really just a StockItem which is "in production"!
    """

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
            if not build.is_fully_allocated(output):

                # Check if the user has specified that incomplete allocations are ok
                accept_incomplete = InvenTree.helpers.str2bool(self.context['request'].data.get('accept_incomplete_allocation', False))

                if not accept_incomplete:
                    raise ValidationError(_("This build output is not fully allocated"))

        return output

    class Meta:
        """Serializer metaclass"""
        fields = [
            'output',
        ]


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
                self.serials = extract_serial_numbers(serial_numbers, quantity, part.getLatestSerialNumberInt())
            except DjangoValidationError as e:
                raise ValidationError({
                    'serial_numbers': e.messages,
                })

            # Check for conflicting serial numbesr
            existing = []

            for serial in self.serials:
                if part.checkIfSerialNumberExists(serial):
                    existing.append(serial)

            if len(existing) > 0:

                msg = _("The following serial numbers already exist")
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

        build.create_build_output(
            quantity,
            serials=self.serials,
            batch=batch_code,
            auto_allocate=auto_allocate,
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
        choices=list(StockStatus.items()),
        default=StockStatus.OK,
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
            'has_allocated_stock': build.is_partially_allocated(None),
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


class BuildCompleteSerializer(serializers.Serializer):
    """DRF serializer for marking a BuildOrder as complete."""

    accept_overallocated = serializers.BooleanField(
        label=_('Accept Overallocated'),
        help_text=_('Accept stock items which have been overallocated to this build order'),
        required=False,
        default=False,
    )

    def validate_accept_overallocated(self, value):
        """Check if the 'accept_overallocated' field is required"""
        build = self.context['build']

        if build.has_overallocated_parts(output=None) and not value:
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

        if not build.are_untracked_parts_allocated() and not value:
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

        if not build.has_build_outputs():
            raise ValidationError(_("No build outputs have been created for this build order"))

        return data

    def save(self):
        """Complete the specified build output"""
        request = self.context['request']
        build = self.context['build']

        build.complete_build(request.user)


class BuildUnallocationSerializer(serializers.Serializer):
    """DRF serializer for unallocating stock from a BuildOrder.

    Allocated stock can be unallocated with a number of filters:

    - output: Filter against a particular build output (blank = untracked stock)
    - bom_item: Filter against a particular BOM line item
    """

    bom_item = serializers.PrimaryKeyRelatedField(
        queryset=BomItem.objects.all(),
        many=False,
        allow_null=True,
        required=False,
        label=_('BOM Item'),
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

        build.unallocateStock(
            bom_item=data['bom_item'],
            output=data['output']
        )


class BuildAllocationItemSerializer(serializers.Serializer):
    """A serializer for allocating a single stock item against a build order."""

    bom_item = serializers.PrimaryKeyRelatedField(
        queryset=BomItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('BOM Item'),
    )

    def validate_bom_item(self, bom_item):
        """Check if the parts match"""
        build = self.context['build']

        # BomItem should point to the same 'part' as the parent build
        if build.part != bom_item.part:

            # If not, it may be marked as "inherited" from a parent part
            if bom_item.inherited and build.part in bom_item.part.get_descendants(include_self=False):
                pass
            else:
                raise ValidationError(_("bom_item.part must point to the same part as the build order"))

        return bom_item

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

    class Meta:
        """Serializer metaclass"""
        fields = [
            'bom_item',
            'stock_item',
            'quantity',
            'output',
        ]

    def validate(self, data):
        """Perfofrm data validation for this item"""
        super().validate(data)

        build = self.context['build']
        bom_item = data['bom_item']
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
        if output is None and bom_item.sub_part.trackable:
            raise ValidationError({
                'output': _('Build output must be specified for allocation of tracked parts'),
            })

        # Output *cannot* be set for un-tracked parts
        if output is not None and not bom_item.sub_part.trackable:

            raise ValidationError({
                'output': _('Build output cannot be specified for allocation of untracked parts'),
            })

        # Check if this allocation would be unique
        if BuildItem.objects.filter(build=build, stock_item=stock_item, install_into=output).exists():
            raise ValidationError(_('This stock item has already been allocated to this build output'))

        return data


class BuildAllocationSerializer(serializers.Serializer):
    """DRF serializer for allocation stock items against a build order."""

    items = BuildAllocationItemSerializer(many=True)

    class Meta:
        """Serializer metaclass"""
        fields = [
            'items',
        ]

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

        build = self.context['build']

        with transaction.atomic():
            for item in items:
                bom_item = item['bom_item']
                stock_item = item['stock_item']
                quantity = item['quantity']
                output = item.get('output', None)

                try:
                    # Create a new BuildItem to allocate stock
                    BuildItem.objects.create(
                        build=build,
                        bom_item=bom_item,
                        stock_item=stock_item,
                        quantity=quantity,
                        install_into=output
                    )
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

    def save(self):
        """Perform the auto-allocation step"""
        data = self.validated_data

        build = self.context['build']

        build.auto_allocate_stock(
            location=data.get('location', None),
            exclude_location=data.get('exclude_location', None),
            interchangeable=data['interchangeable'],
            substitutes=data['substitutes'],
        )


class BuildItemSerializer(InvenTreeModelSerializer):
    """Serializes a BuildItem object."""

    bom_part = serializers.IntegerField(source='bom_item.sub_part.pk', read_only=True)
    part = serializers.IntegerField(source='stock_item.part.pk', read_only=True)
    location = serializers.IntegerField(source='stock_item.location.pk', read_only=True)

    # Extra (optional) detail fields
    part_detail = PartSerializer(source='stock_item.part', many=False, read_only=True)
    build_detail = BuildSerializer(source='build', many=False, read_only=True)
    stock_item_detail = StockItemSerializerBrief(source='stock_item', read_only=True)
    location_detail = LocationSerializer(source='stock_item.location', read_only=True)

    quantity = InvenTreeDecimalField()

    def __init__(self, *args, **kwargs):
        """Determine which extra details fields should be included"""
        build_detail = kwargs.pop('build_detail', False)
        part_detail = kwargs.pop('part_detail', False)
        location_detail = kwargs.pop('location_detail', False)

        super().__init__(*args, **kwargs)

        if not build_detail:
            self.fields.pop('build_detail')

        if not part_detail:
            self.fields.pop('part_detail')

        if not location_detail:
            self.fields.pop('location_detail')

    class Meta:
        """Serializer metaclass"""
        model = BuildItem
        fields = [
            'pk',
            'bom_part',
            'build',
            'build_detail',
            'install_into',
            'location',
            'location_detail',
            'part',
            'part_detail',
            'stock_item',
            'stock_item_detail',
            'quantity'
        ]


class BuildAttachmentSerializer(InvenTreeAttachmentSerializer):
    """Serializer for a BuildAttachment."""

    class Meta:
        """Serializer metaclass"""
        model = BuildOrderAttachment

        fields = [
            'pk',
            'build',
            'attachment',
            'link',
            'filename',
            'comment',
            'upload_date',
            'user',
            'user_detail',
        ]

        read_only_fields = [
            'upload_date',
        ]
