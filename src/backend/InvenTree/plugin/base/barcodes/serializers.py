"""DRF serializers for barcode scanning API."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import common.models
import company.models
import order.models
import plugin.base.barcodes.helper
import stock.models
from InvenTree.serializers import UserSerializer
from order.status_codes import PurchaseOrderStatus, SalesOrderStatus


class BarcodeScanResultSerializer(serializers.ModelSerializer):
    """Serializer for barcode scan results."""

    class Meta:
        """Meta class for BarcodeScanResultSerializer."""

        model = common.models.BarcodeScanResult

        fields = [
            'pk',
            'data',
            'timestamp',
            'endpoint',
            'context',
            'response',
            'result',
            'user',
            'user_detail',
        ]

        read_only_fields = fields

    user_detail = UserSerializer(source='user', read_only=True)


class BarcodeSerializer(serializers.Serializer):
    """Generic serializer for receiving barcode data."""

    MAX_BARCODE_LENGTH = 4095

    barcode = serializers.CharField(
        required=True,
        help_text=_('Scanned barcode data'),
        max_length=MAX_BARCODE_LENGTH,
    )


class BarcodeGenerateSerializer(serializers.Serializer):
    """Serializer for generating a barcode."""

    model = serializers.CharField(
        required=True, help_text=_('Model name to generate barcode for')
    )

    pk = serializers.IntegerField(
        required=True,
        help_text=_('Primary key of model object to generate barcode for'),
    )

    def validate_model(self, model: str):
        """Validate the provided model."""
        supported_models = (
            plugin.base.barcodes.helper.get_supported_barcode_models_map()
        )

        if model not in supported_models:
            raise ValidationError(_('Model is not supported'))

        return model


class BarcodeAssignMixin(serializers.Serializer):
    """Serializer for linking and unlinking barcode to an internal class."""

    def __init__(self, *args, **kwargs):
        """Generate serializer fields for each supported model type."""
        super().__init__(*args, **kwargs)

        for model in plugin.base.barcodes.helper.get_supported_barcode_models():
            self.fields[model.barcode_model_type()] = (
                serializers.PrimaryKeyRelatedField(
                    queryset=model.objects.all(),
                    required=False,
                    allow_null=True,
                    label=model._meta.verbose_name,
                )
            )

    @staticmethod
    def get_model_fields():
        """Return a list of model fields."""
        fields = [
            model.barcode_model_type()
            for model in plugin.base.barcodes.helper.get_supported_barcode_models()
        ]

        return fields


class BarcodeAssignSerializer(BarcodeAssignMixin, BarcodeSerializer):
    """Serializer class for linking a barcode to an internal model."""

    class Meta:
        """Meta class for BarcodeAssignSerializer."""

        fields = ['barcode', *BarcodeAssignMixin.get_model_fields()]


class BarcodeUnassignSerializer(BarcodeAssignMixin):
    """Serializer class for unlinking a barcode from an internal model."""

    class Meta:
        """Meta class for BarcodeUnlinkSerializer."""

        fields = BarcodeAssignMixin.get_model_fields()


class BarcodePOAllocateSerializer(BarcodeSerializer):
    """Serializer for allocating items against a purchase order.

    The scanned barcode could be a Part, ManufacturerPart or SupplierPart object
    """

    purchase_order = serializers.PrimaryKeyRelatedField(
        queryset=order.models.PurchaseOrder.objects.all(),
        required=True,
        help_text=_('Purchase Order to allocate items against'),
    )

    def validate_purchase_order(self, order: order.models.PurchaseOrder):
        """Validate the provided order."""
        if order.status != PurchaseOrderStatus.PENDING.value:
            raise ValidationError(_('Purchase order is not pending'))

        return order


class BarcodePOReceiveSerializer(BarcodeSerializer):
    """Serializer for receiving items against a purchase order.

    The following additional fields may be specified:

    - purchase_order: PurchaseOrder object to receive items against
    - location: Location to receive items into
    """

    supplier = serializers.PrimaryKeyRelatedField(
        queryset=company.models.Company.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('Supplier to receive items from'),
    )

    purchase_order = serializers.PrimaryKeyRelatedField(
        queryset=order.models.PurchaseOrder.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('PurchaseOrder to receive items against'),
    )

    def validate_purchase_order(self, order: order.models.PurchaseOrder):
        """Validate the provided order."""
        if order and order.status != PurchaseOrderStatus.PLACED.value:
            raise ValidationError(_('Purchase order has not been placed'))

        return order

    location = serializers.PrimaryKeyRelatedField(
        queryset=stock.models.StockLocation.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('Location to receive items into'),
    )

    def validate_location(self, location: stock.models.StockLocation):
        """Validate the provided location."""
        if location and location.structural:
            raise ValidationError(_('Cannot select a structural location'))

        return location

    line_item = serializers.PrimaryKeyRelatedField(
        queryset=order.models.PurchaseOrderLineItem.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('Purchase order line item to receive items against'),
    )

    auto_allocate = serializers.BooleanField(
        required=False,
        default=True,
        help_text=_('Automatically allocate stock items to the purchase order'),
    )


class BarcodeSOAllocateSerializer(BarcodeSerializer):
    """Serializr for allocating stock items to a sales order.

    The scanned barcode must map to a StockItem object
    """

    sales_order = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrder.objects.all(),
        required=True,
        help_text=_('Sales Order to allocate items against'),
    )

    def validate_sales_order(self, order: order.models.SalesOrder):
        """Validate the provided order."""
        if order and order.status != SalesOrderStatus.PENDING.value:
            raise ValidationError(_('Sales order is not pending'))

        return order

    line = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderLineItem.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('Sales order line item to allocate items against'),
    )

    shipment = serializers.PrimaryKeyRelatedField(
        queryset=order.models.SalesOrderShipment.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('Sales order shipment to allocate items against'),
    )

    def validate_shipment(self, shipment: order.models.SalesOrderShipment):
        """Validate the provided shipment."""
        if shipment and shipment.is_delivered():
            raise ValidationError(_('Shipment has already been delivered'))

        return shipment

    quantity = serializers.IntegerField(
        required=False, help_text=_('Quantity to allocate')
    )
