"""
JSON serializers for the Order API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.db.models import Case, When, Value
from django.db.models import BooleanField, ExpressionWrapper, F

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from sql_util.utils import SubqueryCount

from common.settings import currency_code_mappings

from company.serializers import CompanyBriefSerializer, SupplierPartSerializer

from InvenTree.helpers import normalize
from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializer
from InvenTree.serializers import InvenTreeMoneySerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField
from InvenTree.status_codes import StockStatus

import order.models

from part.serializers import PartBriefSerializer

import stock.models
import stock.serializers


class POSerializer(InvenTreeModelSerializer):
    """
    Serializer for a PurchaseOrder object
    """

    def __init__(self, *args, **kwargs):

        supplier_detail = kwargs.pop('supplier_detail', False)

        super().__init__(*args, **kwargs)

        if supplier_detail is not True:
            self.fields.pop('supplier_detail')

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add extra information to the queryset

        - Number of lines in the PurchaseOrder
        - Overdue status of the PurchaseOrder
        """

        queryset = queryset.annotate(
            line_items=SubqueryCount('lines')
        )

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    order.models.PurchaseOrder.OVERDUE_FILTER, then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField())
            )
        )

        return queryset

    supplier_detail = CompanyBriefSerializer(source='supplier', many=False, read_only=True)

    line_items = serializers.IntegerField(read_only=True)

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    overdue = serializers.BooleanField(required=False, read_only=True)

    reference = serializers.CharField(required=True)

    class Meta:
        model = order.models.PurchaseOrder

        fields = [
            'pk',
            'issue_date',
            'complete_date',
            'creation_date',
            'description',
            'line_items',
            'link',
            'overdue',
            'reference',
            'responsible',
            'supplier',
            'supplier_detail',
            'supplier_reference',
            'status',
            'status_text',
            'target_date',
            'notes',
        ]

        read_only_fields = [
            'status'
            'issue_date',
            'complete_date',
            'creation_date',
        ]


class POLineItemSerializer(InvenTreeModelSerializer):

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add some extra annotations to this queryset:

        - Total price = purchase_price * quantity
        """

        queryset = queryset.annotate(
            total_price=ExpressionWrapper(
                F('purchase_price') * F('quantity'),
                output_field=models.DecimalField()
            )
        )

        return queryset

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')
            self.fields.pop('supplier_part_detail')

    quantity = serializers.FloatField(default=1)
    received = serializers.FloatField(default=0)

    total_price = serializers.FloatField(read_only=True)

    part_detail = PartBriefSerializer(source='get_base_part', many=False, read_only=True)
    supplier_part_detail = SupplierPartSerializer(source='part', many=False, read_only=True)

    purchase_price = InvenTreeMoneySerializer(
        allow_null=True
    )

    purchase_price_string = serializers.CharField(source='purchase_price', read_only=True)

    destination_detail = stock.serializers.LocationBriefSerializer(source='get_destination', read_only=True)

    purchase_price_currency = serializers.ChoiceField(
        choices=currency_code_mappings(),
        help_text=_('Purchase price currency'),
    )

    class Meta:
        model = order.models.PurchaseOrderLineItem

        fields = [
            'pk',
            'quantity',
            'reference',
            'notes',
            'order',
            'part',
            'part_detail',
            'supplier_part_detail',
            'received',
            'purchase_price',
            'purchase_price_currency',
            'purchase_price_string',
            'destination',
            'destination_detail',
            'total_price',
        ]


class POLineItemReceiveSerializer(serializers.Serializer):
    """
    A serializer for receiving a single purchase order line item against a purchase order
    """

    line_item = serializers.PrimaryKeyRelatedField(
        queryset=order.models.PurchaseOrderLineItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Line Item'),
    )

    def validate_line_item(self, item):

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
        max_digits=15,
        decimal_places=5,
        min_value=0,
        required=True,
    )

    def validate_quantity(self, quantity):

        if quantity <= 0:
            raise ValidationError(_("Quantity must be greater than zero"))

        return quantity

    status = serializers.ChoiceField(
        choices=list(StockStatus.items()),
        default=StockStatus.OK,
        label=_('Status'),
    )

    barcode = serializers.CharField(
        label=_('Barcode Hash'),
        help_text=_('Unique identifier field'),
        default='',
        required=False,
        allow_blank=True,
    )

    def validate_barcode(self, barcode):
        """
        Cannot check in a LineItem with a barcode that is already assigned
        """

        # Ignore empty barcode values
        if not barcode or barcode.strip() == '':
            return None

        if stock.models.StockItem.objects.filter(uid=barcode).exists():
            raise ValidationError(_('Barcode is already in use'))

        return barcode

    class Meta:
        fields = [
            'barcode',
            'line_item',
            'location',
            'quantity',
            'status',
        ]


class POReceiveSerializer(serializers.Serializer):
    """
    Serializer for receiving items against a purchase order
    """

    items = POLineItemReceiveSerializer(many=True)

    location = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockLocation.objects.all(),
        many=False,
        allow_null=True,
        label=_('Location'),
        help_text=_('Select destination location for received items'),
    )

    def validate(self, data):

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
                    'location': _("Destination location must be specified"),
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
        """
        Perform the actual database transaction to receive purchase order items
        """

        data = self.validated_data

        request = self.context['request']
        order = self.context['order']

        items = data['items']
        location = data.get('location', None)

        # Now we can actually receive the items into stock
        with transaction.atomic():
            for item in items:

                # Select location
                loc = item.get('location', None) or item['line_item'].get_destination() or location

                try:
                    order.receive_line_item(
                        item['line_item'],
                        loc,
                        item['quantity'],
                        request.user,
                        status=item['status'],
                        barcode=item.get('barcode', ''),
                    )
                except (ValidationError, DjangoValidationError) as exc:
                    # Catch model errors and re-throw as DRF errors
                    raise ValidationError(detail=serializers.as_serializer_error(exc))

    class Meta:
        fields = [
            'items',
            'location',
        ]


class POAttachmentSerializer(InvenTreeAttachmentSerializer):
    """
    Serializers for the PurchaseOrderAttachment model
    """

    attachment = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = order.models.PurchaseOrderAttachment

        fields = [
            'pk',
            'order',
            'attachment',
            'filename',
            'comment',
            'upload_date',
        ]

        read_only_fields = [
            'upload_date',
        ]


class SalesOrderSerializer(InvenTreeModelSerializer):
    """
    Serializers for the SalesOrder object
    """

    def __init__(self, *args, **kwargs):

        customer_detail = kwargs.pop('customer_detail', False)

        super().__init__(*args, **kwargs)

        if customer_detail is not True:
            self.fields.pop('customer_detail')

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add extra information to the queryset

        - Number of line items in the SalesOrder
        - Overdue status of the SalesOrder
        """

        queryset = queryset.annotate(
            line_items=SubqueryCount('lines')
        )

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    order.models.SalesOrder.OVERDUE_FILTER, then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField())
            )
        )

        return queryset

    customer_detail = CompanyBriefSerializer(source='customer', many=False, read_only=True)

    line_items = serializers.IntegerField(read_only=True)

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    overdue = serializers.BooleanField(required=False, read_only=True)

    reference = serializers.CharField(required=True)

    class Meta:
        model = order.models.SalesOrder

        fields = [
            'pk',
            'creation_date',
            'customer',
            'customer_detail',
            'customer_reference',
            'description',
            'line_items',
            'link',
            'notes',
            'overdue',
            'reference',
            'responsible',
            'status',
            'status_text',
            'shipment_date',
            'target_date',
        ]

        read_only_fields = [
            'status',
            'creation_date',
            'shipment_date',
        ]


class SalesOrderAllocationSerializer(InvenTreeModelSerializer):
    """
    Serializer for the SalesOrderAllocation model.
    This includes some fields from the related model objects.
    """

    part = serializers.PrimaryKeyRelatedField(source='item.part', read_only=True)
    order = serializers.PrimaryKeyRelatedField(source='line.order', many=False, read_only=True)
    serial = serializers.CharField(source='get_serial', read_only=True)
    quantity = serializers.FloatField(read_only=False)
    location = serializers.PrimaryKeyRelatedField(source='item.location', many=False, read_only=True)

    # Extra detail fields
    order_detail = SalesOrderSerializer(source='line.order', many=False, read_only=True)
    part_detail = PartBriefSerializer(source='item.part', many=False, read_only=True)
    item_detail = stock.serializers.StockItemSerializer(source='item', many=False, read_only=True)
    location_detail = stock.serializers.LocationSerializer(source='item.location', many=False, read_only=True)

    def __init__(self, *args, **kwargs):

        order_detail = kwargs.pop('order_detail', False)
        part_detail = kwargs.pop('part_detail', False)
        item_detail = kwargs.pop('item_detail', False)
        location_detail = kwargs.pop('location_detail', False)

        super().__init__(*args, **kwargs)

        if not order_detail:
            self.fields.pop('order_detail')

        if not part_detail:
            self.fields.pop('part_detail')

        if not item_detail:
            self.fields.pop('item_detail')

        if not location_detail:
            self.fields.pop('location_detail')

    class Meta:
        model = order.models.SalesOrderAllocation

        fields = [
            'pk',
            'line',
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
        ]


class SOLineItemSerializer(InvenTreeModelSerializer):
    """ Serializer for a SalesOrderLineItem object """

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)
        order_detail = kwargs.pop('order_detail', False)
        allocations = kwargs.pop('allocations', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if order_detail is not True:
            self.fields.pop('order_detail')

        if allocations is not True:
            self.fields.pop('allocations')

    order_detail = SalesOrderSerializer(source='order', many=False, read_only=True)
    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    allocations = SalesOrderAllocationSerializer(many=True, read_only=True, location_detail=True)

    quantity = serializers.FloatField()

    allocated = serializers.FloatField(source='allocated_quantity', read_only=True)
    fulfilled = serializers.FloatField(source='fulfilled_quantity', read_only=True)
    
    sale_price = InvenTreeMoneySerializer(
        allow_null=True
    )

    sale_price_string = serializers.CharField(source='sale_price', read_only=True)

    sale_price_currency = serializers.ChoiceField(
        choices=currency_code_mappings(),
        help_text=_('Sale price currency'),
    )

    class Meta:
        model = order.models.SalesOrderLineItem

        fields = [
            'pk',
            'allocated',
            'allocations',
            'quantity',
            'fulfilled',
            'reference',
            'notes',
            'order',
            'order_detail',
            'part',
            'part_detail',
            'sale_price',
            'sale_price_currency',
            'sale_price_string',
        ]


class SalesOrderShipmentSerializer(InvenTreeModelSerializer):
    """
    Serializer for the SalesOrderShipment class
    """

    allocations = SalesOrderAllocationSerializer(many=True, read_only=True, location_detail=True)

    order_detail = SalesOrderSerializer(source='order', read_only=True, many=False)

    class Meta:
        model = order.models.SalesOrderShipment

        fields = [
            'pk',
            'order',
            'order_detail',
            'allocations',
            'shipment_date',
            'checked_by',
            'reference',
            'notes',
        ]


class SOShipmentAllocationItemSerializer(serializers.Serializer):
    """
    A serializer for allocating a single stock-item against a SalesOrder shipment
    """

    class Meta:
        fields = [
            'line_item',
            'stock_item',
            'quantity',
        ]

    line_item = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderLineItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    def validate_line_item(self, line_item):

        order = self.context['order']

        # Ensure that the line item points to the correct order
        if line_item.order != order:
            raise ValidationError(_("Line item is not associated with this order"))

        return line_item

    stock_item = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=0,
        required=True
    )

    def validate_quantity(self, quantity):

        if quantity <= 0:
            raise ValidationError(_("Quantity must be positive"))

        return quantity

    def validate(self, data):

        super().validate(data)

        stock_item = data['stock_item']
        quantity = data['quantity']

        if stock_item.serialized and quantity != 1:
            raise ValidationError({
                'quantity': _("Quantity must be 1 for serialized stock item"),
            })

        q = normalize(stock_item.unallocated_quantity())

        if quantity > q:
            raise ValidationError({
                'quantity': _(f"Available quantity ({q}) exceeded")
            })

        return data


class SOShipmentAllocationSerializer(serializers.Serializer):
    """
    DRF serializer for allocation of stock items against a sales order / shipment
    """

    class Meta:
        fields = [
            'items',
            'shipment',
        ]

    items = SOShipmentAllocationItemSerializer(many=True)

    shipment = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderShipment.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Shipment'),
    )

    def validate_shipment(self, shipment):
        """
        Run validation against the provided shipment instance
        """

        order = self.context['order']

        if shipment.shipment_date is not None:
            raise ValidationError(_("Shipment has already been shipped"))

        if shipment.order != order:
            raise ValidationError(_("Shipment is not associated with this order"))

        return shipment

    def validate(self, data):
        """
        Serializer validation
        """

        data = super().validate(data)

        # Extract SalesOrder from serializer context
        # order = self.context['order']

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('Allocation items must be provided'))

        return data

    def save(self):
        """
        Perform the allocation of items against this order
        """

        data = self.validated_data

        items = data['items']
        shipment = data['shipment']

        with transaction.atomic():
            for entry in items:
                
                # Create a new SalesOrderAllocation
                order.models.SalesOrderAllocation.objects.create(
                    line=entry.get('line_item'),
                    item=entry.get('stock_item'),
                    quantity=entry.get('quantity'),
                    shipment=shipment,
                )

                try:
                    pass
                except (ValidationError, DjangoValidationError) as exc:
                    raise ValidationError(detail=serializers.as_serializer_error(exc))


class SOAttachmentSerializer(InvenTreeAttachmentSerializer):
    """
    Serializers for the SalesOrderAttachment model
    """

    attachment = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = order.models.SalesOrderAttachment

        fields = [
            'pk',
            'order',
            'attachment',
            'filename',
            'comment',
            'upload_date',
        ]

        read_only_fields = [
            'upload_date',
        ]
