"""JSON serializers for the Order API."""

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.db.models import (
    BooleanField,
    Case,
    ExpressionWrapper,
    F,
    Prefetch,
    Q,
    Value,
    When,
)
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from sql_util.utils import SubqueryCount

import order.models
import part.filters as part_filters
import part.models as part_models
import stock.models
import stock.serializers
from common.serializers import ProjectCodeSerializer
from company.serializers import (
    AddressBriefSerializer,
    CompanyBriefSerializer,
    ContactSerializer,
    SupplierPartSerializer,
)
from generic.states.fields import InvenTreeCustomStatusSerializerMixin
from importer.mixins import DataImportExportSerializerMixin
from importer.registry import register_importer
from InvenTree.helpers import (
    current_date,
    extract_serial_numbers,
    hash_barcode,
    normalize,
    str2bool,
)
from InvenTree.serializers import (
    InvenTreeCurrencySerializer,
    InvenTreeDecimalField,
    InvenTreeModelSerializer,
    InvenTreeMoneySerializer,
    NotesFieldMixin,
)
from order.status_codes import (
    PurchaseOrderStatusGroups,
    ReturnOrderLineStatus,
    ReturnOrderStatus,
    SalesOrderStatusGroups,
)
from part.serializers import PartBriefSerializer
from stock.status_codes import StockStatus
from users.serializers import OwnerSerializer


class TotalPriceMixin(serializers.Serializer):
    """Serializer mixin which provides total price fields."""

    total_price = InvenTreeMoneySerializer(allow_null=True, read_only=True)

    order_currency = InvenTreeCurrencySerializer(
        allow_blank=True,
        allow_null=True,
        required=False,
        label=_('Order Currency'),
        help_text=_('Currency for this order (leave blank to use company default)'),
    )


class AbstractOrderSerializer(DataImportExportSerializerMixin, serializers.Serializer):
    """Abstract serializer class which provides fields common to all order types."""

    export_exclude_fields = ['notes']

    # Number of line items in this order
    line_items = serializers.IntegerField(read_only=True, label=_('Line Items'))

    # Number of completed line items (this is an annotated field)
    completed_lines = serializers.IntegerField(
        read_only=True, label=_('Completed Lines')
    )

    # Human-readable status text (read-only)
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    # status field cannot be set directly
    status = serializers.IntegerField(read_only=True, label=_('Order Status'))

    # Reference string is *required*
    reference = serializers.CharField(required=True)

    # Detail for point-of-contact field
    contact_detail = ContactSerializer(source='contact', many=False, read_only=True)

    # Detail for responsible field
    responsible_detail = OwnerSerializer(
        source='responsible', read_only=True, many=False
    )

    project_code_label = serializers.CharField(
        source='project_code.code', read_only=True, label='Project Code Label'
    )

    # Detail for project code field
    project_code_detail = ProjectCodeSerializer(
        source='project_code', read_only=True, many=False
    )

    # Detail for address field
    address_detail = AddressBriefSerializer(
        source='address', many=False, read_only=True
    )

    # Boolean field indicating if this order is overdue (Note: must be annotated)
    overdue = serializers.BooleanField(required=False, read_only=True)

    barcode_hash = serializers.CharField(read_only=True)

    creation_date = serializers.DateField(
        required=False, allow_null=True, label=_('Creation Date')
    )

    def validate_reference(self, reference):
        """Custom validation for the reference field."""
        self.Meta.model.validate_reference_field(reference)
        return reference

    @staticmethod
    def annotate_queryset(queryset):
        """Add extra information to the queryset."""
        queryset = queryset.annotate(line_items=SubqueryCount('lines'))

        return queryset

    @staticmethod
    def order_fields(extra_fields):
        """Construct a set of fields for this serializer."""
        return [
            'pk',
            'creation_date',
            'target_date',
            'description',
            'line_items',
            'completed_lines',
            'link',
            'project_code',
            'project_code_label',
            'project_code_detail',
            'reference',
            'responsible',
            'responsible_detail',
            'contact',
            'contact_detail',
            'address',
            'address_detail',
            'status',
            'status_text',
            'status_custom_key',
            'notes',
            'barcode_hash',
            'overdue',
            *extra_fields,
        ]


class AbstractLineItemSerializer:
    """Abstract serializer for LineItem object."""

    target_date = serializers.DateField(
        required=False, allow_null=True, label=_('Target Date')
    )


class AbstractExtraLineSerializer(
    DataImportExportSerializerMixin, serializers.Serializer
):
    """Abstract Serializer for a ExtraLine object."""

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        order_detail = kwargs.pop('order_detail', False)

        super().__init__(*args, **kwargs)

        if order_detail is not True:
            self.fields.pop('order_detail', None)

    quantity = serializers.FloatField()

    price = InvenTreeMoneySerializer(allow_null=True)

    price_currency = InvenTreeCurrencySerializer()


class AbstractExtraLineMeta:
    """Abstract Meta for ExtraLine."""

    fields = [
        'pk',
        'description',
        'quantity',
        'reference',
        'notes',
        'context',
        'order',
        'order_detail',
        'price',
        'price_currency',
        'link',
    ]


@register_importer()
class PurchaseOrderSerializer(
    NotesFieldMixin,
    TotalPriceMixin,
    InvenTreeCustomStatusSerializerMixin,
    AbstractOrderSerializer,
    InvenTreeModelSerializer,
):
    """Serializer for a PurchaseOrder object."""

    class Meta:
        """Metaclass options."""

        model = order.models.PurchaseOrder

        fields = AbstractOrderSerializer.order_fields([
            'issue_date',
            'complete_date',
            'supplier',
            'supplier_detail',
            'supplier_reference',
            'supplier_name',
            'total_price',
            'order_currency',
        ])

        read_only_fields = ['issue_date', 'complete_date', 'creation_date']

        extra_kwargs = {
            'supplier': {'required': True},
            'order_currency': {'required': False},
        }

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        supplier_detail = kwargs.pop('supplier_detail', False)

        super().__init__(*args, **kwargs)

        if supplier_detail is not True:
            self.fields.pop('supplier_detail', None)

    @staticmethod
    def annotate_queryset(queryset):
        """Add extra information to the queryset.

        - Number of lines in the PurchaseOrder
        - Overdue status of the PurchaseOrder
        """
        queryset = AbstractOrderSerializer.annotate_queryset(queryset)

        queryset = queryset.annotate(
            completed_lines=SubqueryCount(
                'lines', filter=Q(quantity__lte=F('received'))
            )
        )

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    order.models.PurchaseOrder.overdue_filter(),
                    then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        return queryset

    supplier_name = serializers.CharField(
        source='supplier.name', read_only=True, label=_('Supplier Name')
    )

    supplier_detail = CompanyBriefSerializer(
        source='supplier', many=False, read_only=True
    )


class OrderAdjustSerializer(serializers.Serializer):
    """Generic serializer class for adjusting the status of an order."""

    class Meta:
        """Metaclass options.

        By default, there are no fields required for this serializer type.
        """

        fields = []

    @property
    def order(self):
        """Return the order object associated with this serializer.

        Note: It is passed in via the serializer context data.
        """
        return self.context['order']


class PurchaseOrderHoldSerializer(OrderAdjustSerializer):
    """Serializer for placing a PurchaseOrder on hold."""

    def save(self):
        """Save the serializer to 'hold' the order."""
        self.order.hold_order()


class PurchaseOrderCancelSerializer(OrderAdjustSerializer):
    """Serializer for cancelling a PurchaseOrder."""

    def save(self):
        """Save the serializer to 'cancel' the order."""
        if not self.order.can_cancel:
            raise ValidationError(_('Order cannot be cancelled'))

        self.order.cancel_order()


class PurchaseOrderCompleteSerializer(OrderAdjustSerializer):
    """Serializer for completing a purchase order."""

    class Meta:
        """Metaclass options."""

        fields = ['accept_incomplete']

    accept_incomplete = serializers.BooleanField(
        label=_('Accept Incomplete'),
        help_text=_('Allow order to be closed with incomplete line items'),
        required=False,
        default=False,
    )

    def validate_accept_incomplete(self, value):
        """Check if the 'accept_incomplete' field is required."""
        order = self.context['order']

        if not value and not order.is_complete:
            raise ValidationError(_('Order has incomplete line items'))

        return value

    def get_context_data(self):
        """Custom context information for this serializer."""
        order = self.context['order']

        return {'is_complete': order.is_complete}

    def save(self):
        """Save the serializer to 'complete' the order."""
        self.order.complete_order()


class PurchaseOrderIssueSerializer(OrderAdjustSerializer):
    """Serializer for issuing (sending) a purchase order."""

    def save(self):
        """Save the serializer to 'place' the order."""
        self.order.place_order()


@register_importer()
class PurchaseOrderLineItemSerializer(
    DataImportExportSerializerMixin,
    AbstractLineItemSerializer,
    InvenTreeModelSerializer,
):
    """Serializer class for the PurchaseOrderLineItem model."""

    class Meta:
        """Metaclass options."""

        model = order.models.PurchaseOrderLineItem

        fields = [
            'pk',
            'part',
            'quantity',
            'reference',
            'notes',
            'order',
            'order_detail',
            'overdue',
            'part_detail',
            'supplier_part_detail',
            'received',
            'purchase_price',
            'purchase_price_currency',
            'auto_pricing',
            'destination',
            'destination_detail',
            'target_date',
            'total_price',
            'link',
            'merge_items',
            'sku',
            'mpn',
            'ipn',
            'internal_part',
            'internal_part_name',
        ]

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        part_detail = kwargs.pop('part_detail', False)
        order_detail = kwargs.pop('order_detail', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail', None)
            self.fields.pop('supplier_part_detail', None)

        if order_detail is not True:
            self.fields.pop('order_detail', None)

    def skip_create_fields(self):
        """Return a list of fields to skip when creating a new object."""
        return ['auto_pricing', 'merge_items', *super().skip_create_fields()]

    @staticmethod
    def annotate_queryset(queryset):
        """Add some extra annotations to this queryset.

        - "total_price" = purchase_price * quantity
        - "overdue" status (boolean field)
        """
        queryset = queryset.prefetch_related(
            Prefetch(
                'part__part',
                queryset=part_models.Part.objects.annotate(
                    category_default_location=part_filters.annotate_default_location(
                        'category__'
                    )
                ).prefetch_related(None),
            )
        )

        queryset = queryset.prefetch_related(
            'order',
            'order__responsible',
            'order__stock_items',
            'part__tags',
            'part__supplier',
            'part__manufacturer_part',
            'part__manufacturer_part__manufacturer',
            'part__part__pricing_data',
            'part__part__tags',
        )

        queryset = queryset.annotate(
            total_price=ExpressionWrapper(
                F('purchase_price') * F('quantity'), output_field=models.DecimalField()
            )
        )

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    order.models.PurchaseOrderLineItem.OVERDUE_FILTER,
                    then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        return queryset

    part = serializers.PrimaryKeyRelatedField(
        queryset=part_models.SupplierPart.objects.all(),
        many=False,
        required=True,
        allow_null=True,
        label=_('Supplier Part'),
    )

    quantity = serializers.FloatField(min_value=0, required=True)

    def validate_quantity(self, quantity):
        """Validation for the 'quantity' field."""
        if quantity <= 0:
            raise ValidationError(_('Quantity must be greater than zero'))

        return quantity

    def validate_purchase_order(self, purchase_order):
        """Validation for the 'purchase_order' field."""
        if purchase_order.status not in PurchaseOrderStatusGroups.OPEN:
            raise ValidationError(_('Order is not open'))

        return purchase_order

    received = serializers.FloatField(default=0, read_only=True)

    overdue = serializers.BooleanField(required=False, read_only=True)

    total_price = serializers.FloatField(read_only=True)

    part_detail = PartBriefSerializer(
        source='get_base_part', many=False, read_only=True
    )

    supplier_part_detail = SupplierPartSerializer(
        source='part', brief=True, many=False, read_only=True
    )

    purchase_price = InvenTreeMoneySerializer(allow_null=True)

    auto_pricing = serializers.BooleanField(
        label=_('Auto Pricing'),
        help_text=_(
            'Automatically calculate purchase price based on supplier part data'
        ),
        default=True,
    )

    destination_detail = stock.serializers.LocationBriefSerializer(
        source='get_destination', read_only=True
    )

    purchase_price_currency = InvenTreeCurrencySerializer(
        help_text=_('Purchase price currency')
    )

    order_detail = PurchaseOrderSerializer(source='order', read_only=True, many=False)

    merge_items = serializers.BooleanField(
        label=_('Merge Items'),
        help_text=_(
            'Merge items with the same part, destination and target date into one line item'
        ),
        default=True,
        write_only=True,
    )

    sku = serializers.CharField(source='part.SKU', read_only=True, label=_('SKU'))

    mpn = serializers.CharField(
        source='part.manufacturer_part.MPN', read_only=True, label=_('MPN')
    )

    ipn = serializers.CharField(
        source='part.part.IPN', read_only=True, label=_('Internal Part Number')
    )

    internal_part = serializers.PrimaryKeyRelatedField(
        source='part.part', read_only=True, many=False, label=_('Internal Part')
    )

    internal_part_name = serializers.CharField(
        source='part.part.name', read_only=True, label=_('Internal Part Name')
    )

    def validate(self, data):
        """Custom validation for the serializer.

        - Ensure the supplier_part field is supplied
        - Ensure the purchase_order field is supplied
        - Ensure that the supplier_part and supplier references match
        """
        data = super().validate(data)

        supplier_part = data.get('part', None)
        purchase_order = data.get('order', None)

        if not supplier_part:
            raise ValidationError({'part': _('Supplier part must be specified')})

        if not purchase_order:
            raise ValidationError({'order': _('Purchase order must be specified')})

        # Check that the supplier part and purchase order match
        if (
            supplier_part is not None
            and supplier_part.supplier != purchase_order.supplier
        ):
            raise ValidationError({
                'part': _('Supplier must match purchase order'),
                'order': _('Purchase order must match supplier'),
            })

        return data


@register_importer()
class PurchaseOrderExtraLineSerializer(
    AbstractExtraLineSerializer, InvenTreeModelSerializer
):
    """Serializer for a PurchaseOrderExtraLine object."""

    order_detail = PurchaseOrderSerializer(source='order', many=False, read_only=True)

    class Meta(AbstractExtraLineMeta):
        """Metaclass options."""

        model = order.models.PurchaseOrderExtraLine


class PurchaseOrderLineItemReceiveSerializer(serializers.Serializer):
    """A serializer for receiving a single purchase order line item against a purchase order."""

    class Meta:
        """Metaclass options."""

        fields = [
            'barcode',
            'line_item',
            'location',
            'quantity',
            'status',
            'batch_code',
            'serial_numbers',
            'packaging',
            'note',
        ]

    line_item = serializers.PrimaryKeyRelatedField(
        queryset=order.models.PurchaseOrderLineItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Line Item'),
    )

    def validate_line_item(self, item):
        """Validation for the 'line_item' field."""
        if item.order != self.context['order']:
            raise ValidationError(_('Line item does not match purchase order'))

        return item

    location = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockLocation.objects.all(),
        many=False,
        allow_null=True,
        required=False,
        label=_('Location'),
        help_text=_('Select destination location for received items'),
    )

    quantity = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal(0), required=True
    )

    def validate_quantity(self, quantity):
        """Validation for the 'quantity' field."""
        if quantity <= 0:
            raise ValidationError(_('Quantity must be greater than zero'))

        return quantity

    batch_code = serializers.CharField(
        label=_('Batch Code'),
        help_text=_('Enter batch code for incoming stock items'),
        required=False,
        default='',
        allow_blank=True,
    )

    serial_numbers = serializers.CharField(
        label=_('Serial Numbers'),
        help_text=_('Enter serial numbers for incoming stock items'),
        required=False,
        default='',
        allow_blank=True,
    )

    status = serializers.ChoiceField(
        choices=StockStatus.items(), default=StockStatus.OK.value, label=_('Status')
    )

    packaging = serializers.CharField(
        label=_('Packaging'),
        help_text=_('Override packaging information for incoming stock items'),
        required=False,
        default='',
        allow_blank=True,
    )

    note = serializers.CharField(
        label=_('Note'),
        help_text=_('Additional note for incoming stock items'),
        required=False,
        default='',
        allow_blank=True,
    )

    barcode = serializers.CharField(
        label=_('Barcode'),
        help_text=_('Scanned barcode'),
        default='',
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    def validate_barcode(self, barcode):
        """Cannot check in a LineItem with a barcode that is already assigned."""
        # Ignore empty barcode values
        if not barcode or barcode.strip() == '':
            return None

        barcode_hash = hash_barcode(barcode)

        if stock.models.StockItem.lookup_barcode(barcode_hash) is not None:
            raise ValidationError(_('Barcode is already in use'))

        return barcode

    def validate(self, data):
        """Custom validation for the serializer.

        - Integer quantity must be provided for serialized stock
        - Validate serial numbers (if provided)
        """
        data = super().validate(data)

        line_item = data['line_item']
        quantity = data['quantity']
        serial_numbers = data.get('serial_numbers', '').strip()

        base_part = line_item.part.part
        base_quantity = line_item.part.base_quantity(quantity)

        # Does the quantity need to be "integer" (for trackable parts?)
        if base_part.trackable and Decimal(base_quantity) != int(base_quantity):
            raise ValidationError({
                'quantity': _(
                    'An integer quantity must be provided for trackable parts'
                )
            })

        # If serial numbers are provided
        if serial_numbers:
            try:
                # Pass the serial numbers through to the parent serializer once validated
                data['serials'] = extract_serial_numbers(
                    serial_numbers, base_quantity, base_part.get_latest_serial_number()
                )
            except DjangoValidationError as e:
                raise ValidationError({'serial_numbers': e.messages})

        return data


class PurchaseOrderReceiveSerializer(serializers.Serializer):
    """Serializer for receiving items against a PurchaseOrder."""

    class Meta:
        """Metaclass options."""

        fields = ['items', 'location']

    items = PurchaseOrderLineItemReceiveSerializer(many=True)

    location = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockLocation.objects.all(),
        many=False,
        allow_null=True,
        label=_('Location'),
        help_text=_('Select destination location for received items'),
    )

    def validate(self, data):
        """Custom validation for the serializer.

        - Ensure line items are provided
        - Check that a location is specified
        """
        super().validate(data)

        items = data.get('items', [])

        location = data.get('location', None)

        if len(items) == 0:
            raise ValidationError(_('Line items must be provided'))

        # Check if the location is not specified for any particular item
        for item in items:
            line = item['line_item']

            if not item.get('location', None):
                # If a global location is specified, use that
                item['location'] = location

            if not item['location']:
                # The line item specifies a location?
                item['location'] = line.get_destination()

            if not item['location']:
                raise ValidationError({
                    'location': _('Destination location must be specified')
                })

        # Ensure barcodes are unique
        unique_barcodes = set()

        for item in items:
            barcode = item.get('barcode', '')

            if barcode:
                if barcode in unique_barcodes:
                    raise ValidationError(_('Supplied barcode values must be unique'))
                else:
                    unique_barcodes.add(barcode)

        return data

    def save(self):
        """Perform the actual database transaction to receive purchase order items."""
        data = self.validated_data

        request = self.context['request']
        order = self.context['order']

        items = data['items']
        location = data.get('location', None)

        # Now we can actually receive the items into stock
        with transaction.atomic():
            for item in items:
                # Select location (in descending order of priority)
                loc = (
                    location
                    or item.get('location', None)
                    or item['line_item'].get_destination()
                )

                try:
                    order.receive_line_item(
                        item['line_item'],
                        loc,
                        item['quantity'],
                        request.user,
                        status=item['status'],
                        barcode=item.get('barcode', ''),
                        batch_code=item.get('batch_code', ''),
                        packaging=item.get('packaging', ''),
                        serials=item.get('serials', None),
                        notes=item.get('note', None),
                    )
                except (ValidationError, DjangoValidationError) as exc:
                    # Catch model errors and re-throw as DRF errors
                    raise ValidationError(detail=serializers.as_serializer_error(exc))


@register_importer()
class SalesOrderSerializer(
    NotesFieldMixin,
    TotalPriceMixin,
    InvenTreeCustomStatusSerializerMixin,
    AbstractOrderSerializer,
    InvenTreeModelSerializer,
):
    """Serializer for the SalesOrder model class."""

    class Meta:
        """Metaclass options."""

        model = order.models.SalesOrder

        fields = AbstractOrderSerializer.order_fields([
            'customer',
            'customer_detail',
            'customer_reference',
            'shipment_date',
            'total_price',
            'order_currency',
        ])

        read_only_fields = ['status', 'creation_date', 'shipment_date']

        extra_kwargs = {'order_currency': {'required': False}}

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        customer_detail = kwargs.pop('customer_detail', False)

        super().__init__(*args, **kwargs)

        if customer_detail is not True:
            self.fields.pop('customer_detail', None)

    @staticmethod
    def annotate_queryset(queryset):
        """Add extra information to the queryset.

        - Number of line items in the SalesOrder
        - Number of completed line items in the SalesOrder
        - Overdue status of the SalesOrder
        """
        queryset = AbstractOrderSerializer.annotate_queryset(queryset)

        queryset = queryset.annotate(
            completed_lines=SubqueryCount('lines', filter=Q(quantity__lte=F('shipped')))
        )

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    order.models.SalesOrder.overdue_filter(),
                    then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        return queryset

    customer_detail = CompanyBriefSerializer(
        source='customer', many=False, read_only=True
    )


class SalesOrderIssueSerializer(OrderAdjustSerializer):
    """Serializer for issuing a SalesOrder."""

    def save(self):
        """Save the serializer to 'issue' the order."""
        self.order.issue_order()


class SalesOrderAllocationSerializer(InvenTreeModelSerializer):
    """Serializer for the SalesOrderAllocation model.

    This includes some fields from the related model objects.
    """

    class Meta:
        """Metaclass options."""

        model = order.models.SalesOrderAllocation

        fields = [
            'pk',
            'line',
            'customer_detail',
            'serial',
            'quantity',
            'location',
            'location_detail',
            'item',
            'item_detail',
            'order',
            'order_detail',
            'part',
            'part_detail',
            'shipment',
            'shipment_date',
        ]

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        order_detail = kwargs.pop('order_detail', False)
        part_detail = kwargs.pop('part_detail', True)
        item_detail = kwargs.pop('item_detail', True)
        location_detail = kwargs.pop('location_detail', False)
        customer_detail = kwargs.pop('customer_detail', False)

        super().__init__(*args, **kwargs)

        if not order_detail:
            self.fields.pop('order_detail', None)

        if not part_detail:
            self.fields.pop('part_detail', None)

        if not item_detail:
            self.fields.pop('item_detail', None)

        if not location_detail:
            self.fields.pop('location_detail', None)

        if not customer_detail:
            self.fields.pop('customer_detail', None)

    part = serializers.PrimaryKeyRelatedField(source='item.part', read_only=True)
    order = serializers.PrimaryKeyRelatedField(
        source='line.order', many=False, read_only=True
    )
    serial = serializers.CharField(source='get_serial', read_only=True)
    quantity = serializers.FloatField(read_only=False)
    location = serializers.PrimaryKeyRelatedField(
        source='item.location', many=False, read_only=True
    )

    # Extra detail fields
    order_detail = SalesOrderSerializer(source='line.order', many=False, read_only=True)
    part_detail = PartBriefSerializer(source='item.part', many=False, read_only=True)
    item_detail = stock.serializers.StockItemSerializer(
        source='item', many=False, read_only=True
    )
    location_detail = stock.serializers.LocationSerializer(
        source='item.location', many=False, read_only=True
    )
    customer_detail = CompanyBriefSerializer(
        source='line.order.customer', many=False, read_only=True
    )

    shipment_date = serializers.DateField(
        source='shipment.shipment_date', read_only=True
    )


@register_importer()
class SalesOrderLineItemSerializer(
    DataImportExportSerializerMixin,
    AbstractLineItemSerializer,
    InvenTreeModelSerializer,
):
    """Serializer for a SalesOrderLineItem object."""

    class Meta:
        """Metaclass options."""

        model = order.models.SalesOrderLineItem

        fields = [
            'pk',
            'allocated',
            'allocations',
            'customer_detail',
            'quantity',
            'reference',
            'notes',
            'order',
            'order_detail',
            'overdue',
            'part',
            'part_detail',
            'sale_price',
            'sale_price_currency',
            'shipped',
            'target_date',
            'link',
            # Annotated fields for part stocking information
            'available_stock',
            'available_variant_stock',
            'building',
            'on_order',
        ]

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer.

        - Add extra related serializer information if required
        """
        part_detail = kwargs.pop('part_detail', False)
        order_detail = kwargs.pop('order_detail', False)
        allocations = kwargs.pop('allocations', False)
        customer_detail = kwargs.pop('customer_detail', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail', None)

        if order_detail is not True:
            self.fields.pop('order_detail', None)

        if allocations is not True:
            self.fields.pop('allocations', None)

        if customer_detail is not True:
            self.fields.pop('customer_detail', None)

    @staticmethod
    def annotate_queryset(queryset):
        """Add some extra annotations to this queryset.

        - "overdue" status (boolean field)
        - "available_quantity"
        - "building"
        - "on_order"
        """
        queryset = queryset.annotate(
            overdue=Case(
                When(
                    Q(order__status__in=SalesOrderStatusGroups.OPEN)
                    & order.models.SalesOrderLineItem.OVERDUE_FILTER,
                    then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        # Annotate each line with the available stock quantity
        # To do this, we need to look at the total stock and any allocations
        queryset = queryset.alias(
            total_stock=part_filters.annotate_total_stock(reference='part__'),
            allocated_to_sales_orders=part_filters.annotate_sales_order_allocations(
                reference='part__'
            ),
            allocated_to_build_orders=part_filters.annotate_build_order_allocations(
                reference='part__'
            ),
        )

        queryset = queryset.annotate(
            available_stock=ExpressionWrapper(
                F('total_stock')
                - F('allocated_to_sales_orders')
                - F('allocated_to_build_orders'),
                output_field=models.DecimalField(),
            )
        )

        # Filter for "variant" stock: Variant stock items must be salable and active
        variant_stock_query = part_filters.variant_stock_query(
            reference='part__'
        ).filter(part__salable=True, part__active=True)

        # Also add in available "variant" stock
        queryset = queryset.alias(
            variant_stock_total=part_filters.annotate_variant_quantity(
                variant_stock_query, reference='quantity'
            ),
            variant_bo_allocations=part_filters.annotate_variant_quantity(
                variant_stock_query, reference='sales_order_allocations__quantity'
            ),
            variant_so_allocations=part_filters.annotate_variant_quantity(
                variant_stock_query, reference='allocations__quantity'
            ),
        )

        queryset = queryset.annotate(
            available_variant_stock=ExpressionWrapper(
                F('variant_stock_total')
                - F('variant_bo_allocations')
                - F('variant_so_allocations'),
                output_field=models.DecimalField(),
            )
        )

        # Add information about the quantity of parts currently on order
        queryset = queryset.annotate(
            on_order=part_filters.annotate_on_order_quantity(reference='part__')
        )

        # Add information about the quantity of parts currently in production
        queryset = queryset.annotate(
            building=part_filters.annotate_in_production_quantity(reference='part__')
        )

        return queryset

    customer_detail = CompanyBriefSerializer(
        source='order.customer', many=False, read_only=True
    )
    order_detail = SalesOrderSerializer(source='order', many=False, read_only=True)
    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    allocations = SalesOrderAllocationSerializer(
        many=True, read_only=True, location_detail=True
    )

    # Annotated fields
    overdue = serializers.BooleanField(required=False, read_only=True)
    available_stock = serializers.FloatField(read_only=True)
    available_variant_stock = serializers.FloatField(read_only=True)
    on_order = serializers.FloatField(label=_('On Order'), read_only=True)
    building = serializers.FloatField(label=_('In Production'), read_only=True)

    quantity = InvenTreeDecimalField()

    allocated = serializers.FloatField(source='allocated_quantity', read_only=True)

    shipped = InvenTreeDecimalField(read_only=True)

    sale_price = InvenTreeMoneySerializer(allow_null=True)

    sale_price_currency = InvenTreeCurrencySerializer(
        help_text=_('Sale price currency')
    )


@register_importer()
class SalesOrderShipmentSerializer(NotesFieldMixin, InvenTreeModelSerializer):
    """Serializer for the SalesOrderShipment class."""

    class Meta:
        """Metaclass options."""

        model = order.models.SalesOrderShipment

        fields = [
            'pk',
            'order',
            'order_detail',
            'allocations',
            'shipment_date',
            'delivery_date',
            'checked_by',
            'reference',
            'tracking_number',
            'invoice_number',
            'link',
            'notes',
        ]

    allocations = SalesOrderAllocationSerializer(
        many=True, read_only=True, location_detail=True
    )

    order_detail = SalesOrderSerializer(source='order', read_only=True, many=False)


class SalesOrderShipmentCompleteSerializer(serializers.ModelSerializer):
    """Serializer for completing (shipping) a SalesOrderShipment."""

    class Meta:
        """Metaclass options."""

        model = order.models.SalesOrderShipment

        fields = [
            'shipment_date',
            'delivery_date',
            'tracking_number',
            'invoice_number',
            'link',
        ]

    def validate(self, data):
        """Custom validation for the serializer.

        - Ensure the shipment reference is provided
        """
        data = super().validate(data)

        shipment = self.context.get('shipment', None)

        if not shipment:
            raise ValidationError(_('No shipment details provided'))

        shipment.check_can_complete(raise_error=True)

        return data

    def save(self):
        """Save the serializer to complete the SalesOrderShipment."""
        shipment = self.context.get('shipment', None)

        if not shipment:
            return

        data = self.validated_data

        request = self.context['request']
        user = request.user

        # Extract shipping date (defaults to today's date)
        now = current_date()
        shipment_date = data.get('shipment_date', now)
        if shipment_date is None:
            # Shipment date should not be None - check above only
            # checks if shipment_date exists in data
            shipment_date = now

        shipment.complete_shipment(
            user,
            tracking_number=data.get('tracking_number', shipment.tracking_number),
            invoice_number=data.get('invoice_number', shipment.invoice_number),
            link=data.get('link', shipment.link),
            shipment_date=shipment_date,
            delivery_date=data.get('delivery_date', shipment.delivery_date),
        )


class SalesOrderShipmentAllocationItemSerializer(serializers.Serializer):
    """A serializer for allocating a single stock-item against a SalesOrder shipment."""

    class Meta:
        """Metaclass options."""

        fields = ['line_item', 'stock_item', 'quantity']

    line_item = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderLineItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    def validate_line_item(self, line_item):
        """Custom validation for the 'line_item' field.

        - Ensure the line_item is associated with the particular SalesOrder
        """
        order = self.context['order']

        # Ensure that the line item points to the correct order
        if line_item.order != order:
            raise ValidationError(_('Line item is not associated with this order'))

        return line_item

    stock_item = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    quantity = serializers.DecimalField(
        max_digits=15, decimal_places=5, min_value=Decimal(0), required=True
    )

    def validate_quantity(self, quantity):
        """Custom validation for the 'quantity' field."""
        if quantity <= 0:
            raise ValidationError(_('Quantity must be positive'))

        return quantity

    def validate(self, data):
        """Custom validation for the serializer.

        - Ensure that the quantity is 1 for serialized stock
        - Quantity cannot exceed the available amount
        """
        data = super().validate(data)

        stock_item = data['stock_item']
        quantity = data['quantity']

        if stock_item.serialized and quantity != 1:
            raise ValidationError({
                'quantity': _('Quantity must be 1 for serialized stock item')
            })

        q = normalize(stock_item.unallocated_quantity())

        if quantity > q:
            raise ValidationError({'quantity': _(f'Available quantity ({q}) exceeded')})

        return data


class SalesOrderCompleteSerializer(OrderAdjustSerializer):
    """DRF serializer for manually marking a sales order as complete."""

    class Meta:
        """Serializer metaclass options."""

        fields = ['accept_incomplete']

    accept_incomplete = serializers.BooleanField(
        label=_('Accept Incomplete'),
        help_text=_('Allow order to be closed with incomplete line items'),
        required=False,
        default=False,
    )

    def validate_accept_incomplete(self, value):
        """Check if the 'accept_incomplete' field is required."""
        order = self.context['order']

        if not value and not order.is_completed():
            raise ValidationError(_('Order has incomplete line items'))

        return value

    def get_context_data(self):
        """Custom context data for this serializer."""
        order = self.context['order']

        return {
            'is_complete': order.is_completed(),
            'pending_shipments': order.pending_shipment_count,
        }

    def validate(self, data):
        """Custom validation for the serializer."""
        data = super().validate(data)
        self.order.can_complete(
            raise_error=True,
            allow_incomplete_lines=str2bool(data.get('accept_incomplete', False)),
        )

        return data

    def save(self):
        """Save the serializer to complete the SalesOrder."""
        request = self.context['request']
        data = self.validated_data

        user = getattr(request, 'user', None)

        self.order.ship_order(
            user, allow_incomplete_lines=str2bool(data.get('accept_incomplete', False))
        )


class SalesOrderHoldSerializer(OrderAdjustSerializer):
    """Serializer for placing a SalesOrder on hold."""

    def save(self):
        """Save the serializer to place the SalesOrder on hold."""
        self.order.hold_order()


class SalesOrderCancelSerializer(OrderAdjustSerializer):
    """Serializer for marking a SalesOrder as cancelled."""

    def get_context_data(self):
        """Add extra context data to the serializer."""
        order = self.context['order']

        return {'can_cancel': order.can_cancel}

    def save(self):
        """Save the serializer to cancel the order."""
        self.order.cancel_order()


class SalesOrderSerialAllocationSerializer(serializers.Serializer):
    """DRF serializer for allocation of serial numbers against a sales order / shipment."""

    class Meta:
        """Metaclass options."""

        fields = ['line_item', 'quantity', 'serial_numbers', 'shipment']

    line_item = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderLineItem.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Line Item'),
    )

    def validate_line_item(self, line_item):
        """Ensure that the line_item is valid."""
        order = self.context['order']

        # Ensure that the line item points to the correct order
        if line_item.order != order:
            raise ValidationError(_('Line item is not associated with this order'))

        return line_item

    quantity = serializers.IntegerField(
        min_value=1, required=True, allow_null=False, label=_('Quantity')
    )

    serial_numbers = serializers.CharField(
        label=_('Serial Numbers'),
        help_text=_('Enter serial numbers to allocate'),
        required=True,
        allow_blank=False,
    )

    shipment = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderShipment.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Shipment'),
    )

    def validate_shipment(self, shipment):
        """Validate the shipment.

        - Must point to the same order
        - Must not be shipped
        """
        order = self.context['order']

        if shipment.shipment_date is not None:
            raise ValidationError(_('Shipment has already been shipped'))

        if shipment.order != order:
            raise ValidationError(_('Shipment is not associated with this order'))

        return shipment

    def validate(self, data):
        """Validation for the serializer.

        - Ensure the serial_numbers and quantity fields match
        - Check that all serial numbers exist
        - Check that the serial numbers are not yet allocated
        """
        data = super().validate(data)

        line_item = data['line_item']
        quantity = data['quantity']
        serial_numbers = data['serial_numbers']

        part = line_item.part

        try:
            data['serials'] = extract_serial_numbers(
                serial_numbers, quantity, part.get_latest_serial_number()
            )
        except DjangoValidationError as e:
            raise ValidationError({'serial_numbers': e.messages})

        serials_not_exist = []
        serials_allocated = []
        stock_items_to_allocate = []

        for serial in data['serials']:
            items = stock.models.StockItem.objects.filter(
                part=part, serial=serial, quantity=1
            )

            if not items.exists():
                serials_not_exist.append(str(serial))
                continue

            stock_item = items[0]

            if stock_item.unallocated_quantity() == 1:
                stock_items_to_allocate.append(stock_item)
            else:
                serials_allocated.append(str(serial))

        if len(serials_not_exist) > 0:
            error_msg = _('No match found for the following serial numbers')
            error_msg += ': '
            error_msg += ','.join(serials_not_exist)

            raise ValidationError({'serial_numbers': error_msg})

        if len(serials_allocated) > 0:
            error_msg = _('The following serial numbers are already allocated')
            error_msg += ': '
            error_msg += ','.join(serials_allocated)

            raise ValidationError({'serial_numbers': error_msg})

        data['stock_items'] = stock_items_to_allocate

        return data

    def save(self):
        """Allocate stock items against the sales order."""
        data = self.validated_data

        line_item = data['line_item']
        stock_items = data['stock_items']
        shipment = data['shipment']

        with transaction.atomic():
            for stock_item in stock_items:
                # Create a new SalesOrderAllocation
                order.models.SalesOrderAllocation.objects.create(
                    line=line_item, item=stock_item, quantity=1, shipment=shipment
                )


class SalesOrderShipmentAllocationSerializer(serializers.Serializer):
    """DRF serializer for allocation of stock items against a sales order / shipment."""

    class Meta:
        """Metaclass options."""

        fields = ['items', 'shipment']

    items = SalesOrderShipmentAllocationItemSerializer(many=True)

    shipment = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderShipment.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Shipment'),
    )

    def validate_shipment(self, shipment):
        """Run validation against the provided shipment instance."""
        order = self.context['order']

        if shipment.shipment_date is not None:
            raise ValidationError(_('Shipment has already been shipped'))

        if shipment.order != order:
            raise ValidationError(_('Shipment is not associated with this order'))

        return shipment

    def validate(self, data):
        """Serializer validation."""
        data = super().validate(data)

        # Extract SalesOrder from serializer context
        # order = self.context['order']

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('Allocation items must be provided'))

        return data

    def save(self):
        """Perform the allocation of items against this order."""
        data = self.validated_data

        items = data['items']
        shipment = data['shipment']

        with transaction.atomic():
            for entry in items:
                # Create a new SalesOrderAllocation
                allocation = order.models.SalesOrderAllocation(
                    line=entry.get('line_item'),
                    item=entry.get('stock_item'),
                    quantity=entry.get('quantity'),
                    shipment=shipment,
                )

                allocation.full_clean()
                allocation.save()


@register_importer()
class SalesOrderExtraLineSerializer(
    AbstractExtraLineSerializer, InvenTreeModelSerializer
):
    """Serializer for a SalesOrderExtraLine object."""

    class Meta(AbstractExtraLineMeta):
        """Metaclass options."""

        model = order.models.SalesOrderExtraLine

    order_detail = SalesOrderSerializer(source='order', many=False, read_only=True)


@register_importer()
class ReturnOrderSerializer(
    NotesFieldMixin,
    InvenTreeCustomStatusSerializerMixin,
    AbstractOrderSerializer,
    TotalPriceMixin,
    InvenTreeModelSerializer,
):
    """Serializer for the ReturnOrder model class."""

    class Meta:
        """Metaclass options."""

        model = order.models.ReturnOrder

        fields = AbstractOrderSerializer.order_fields([
            'customer',
            'customer_detail',
            'customer_reference',
            'order_currency',
            'total_price',
        ])

        read_only_fields = ['creation_date']

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        customer_detail = kwargs.pop('customer_detail', False)

        super().__init__(*args, **kwargs)

        if customer_detail is not True:
            self.fields.pop('customer_detail', None)

    @staticmethod
    def annotate_queryset(queryset):
        """Custom annotation for the serializer queryset."""
        queryset = AbstractOrderSerializer.annotate_queryset(queryset)

        queryset = queryset.annotate(
            completed_lines=SubqueryCount(
                'lines', filter=~Q(outcome=ReturnOrderLineStatus.PENDING.value)
            )
        )

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    order.models.ReturnOrder.overdue_filter(),
                    then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

        return queryset

    customer_detail = CompanyBriefSerializer(
        source='customer', many=False, read_only=True
    )


class ReturnOrderHoldSerializer(OrderAdjustSerializer):
    """Serializers for holding a ReturnOrder."""

    def save(self):
        """Save the serializer to 'hold' the order."""
        self.order.hold_order()


class ReturnOrderIssueSerializer(OrderAdjustSerializer):
    """Serializer for issuing a ReturnOrder."""

    def save(self):
        """Save the serializer to 'issue' the order."""
        self.order.issue_order()


class ReturnOrderCancelSerializer(OrderAdjustSerializer):
    """Serializer for cancelling a ReturnOrder."""

    def save(self):
        """Save the serializer to 'cancel' the order."""
        self.order.cancel_order()


class ReturnOrderCompleteSerializer(OrderAdjustSerializer):
    """Serializer for completing a ReturnOrder."""

    def save(self):
        """Save the serializer to 'complete' the order."""
        self.order.complete_order()


class ReturnOrderLineItemReceiveSerializer(serializers.Serializer):
    """Serializer for receiving a single line item against a ReturnOrder."""

    class Meta:
        """Metaclass options."""

        fields = ['item']

    item = serializers.PrimaryKeyRelatedField(
        queryset=order.models.ReturnOrderLineItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Return order line item'),
    )

    def validate_line_item(self, item):
        """Validation for a single line item."""
        if item.order != self.context['order']:
            raise ValidationError(_('Line item does not match return order'))

        if item.received:
            raise ValidationError(_('Line item has already been received'))

        return item


class ReturnOrderReceiveSerializer(serializers.Serializer):
    """Serializer for receiving items against a ReturnOrder."""

    class Meta:
        """Metaclass options."""

        fields = ['items', 'location']

    items = ReturnOrderLineItemReceiveSerializer(many=True)

    location = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockLocation.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Location'),
        help_text=_('Select destination location for received items'),
    )

    def validate(self, data):
        """Perform data validation for this serializer."""
        order = self.context['order']
        if order.status != ReturnOrderStatus.IN_PROGRESS:
            raise ValidationError(
                _('Items can only be received against orders which are in progress')
            )

        data = super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('Line items must be provided'))

        return data

    @transaction.atomic
    def save(self):
        """Saving this serializer marks the returned items as received."""
        order = self.context['order']
        request = self.context['request']

        data = self.validated_data
        items = data['items']
        location = data['location']

        with transaction.atomic():
            for item in items:
                line_item = item['item']
                order.receive_line_item(line_item, location, request.user)


@register_importer()
class ReturnOrderLineItemSerializer(
    DataImportExportSerializerMixin,
    AbstractLineItemSerializer,
    InvenTreeModelSerializer,
):
    """Serializer for a ReturnOrderLineItem object."""

    class Meta:
        """Metaclass options."""

        model = order.models.ReturnOrderLineItem

        fields = [
            'pk',
            'order',
            'order_detail',
            'item',
            'item_detail',
            'received_date',
            'outcome',
            'part_detail',
            'price',
            'price_currency',
            'link',
            'reference',
            'notes',
            'target_date',
            'link',
        ]

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        order_detail = kwargs.pop('order_detail', False)
        item_detail = kwargs.pop('item_detail', False)
        part_detail = kwargs.pop('part_detail', False)

        super().__init__(*args, **kwargs)

        if not order_detail:
            self.fields.pop('order_detail', None)

        if not item_detail:
            self.fields.pop('item_detail', None)

        if not part_detail:
            self.fields.pop('part_detail', None)

    order_detail = ReturnOrderSerializer(source='order', many=False, read_only=True)
    item_detail = stock.serializers.StockItemSerializer(
        source='item', many=False, read_only=True
    )
    part_detail = PartBriefSerializer(source='item.part', many=False, read_only=True)

    price = InvenTreeMoneySerializer(allow_null=True)
    price_currency = InvenTreeCurrencySerializer(help_text=_('Line price currency'))


@register_importer()
class ReturnOrderExtraLineSerializer(
    AbstractExtraLineSerializer, InvenTreeModelSerializer
):
    """Serializer for a ReturnOrderExtraLine object."""

    class Meta(AbstractExtraLineMeta):
        """Metaclass options."""

        model = order.models.ReturnOrderExtraLine

    order_detail = ReturnOrderSerializer(source='order', many=False, read_only=True)
