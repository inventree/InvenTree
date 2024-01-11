"""API endpoints for barcode plugins."""

import logging

from django.db.models import F
from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

import order.models
import stock.models
from InvenTree.helpers import hash_barcode
from plugin import registry
from plugin.builtin.barcodes.inventree_barcode import InvenTreeInternalBarcodePlugin
from users.models import RuleSet

from . import serializers as barcode_serializers

logger = logging.getLogger('inventree')


class BarcodeView(CreateAPIView):
    """Custom view class for handling a barcode scan"""

    # Default serializer class (can be overridden)
    serializer_class = barcode_serializers.BarcodeSerializer

    def queryset(self):
        """This API view does not have a queryset"""
        return None

    # Default permission classes (can be overridden)
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Handle create method - override default create"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        barcode = str(data.pop('barcode')).strip()

        return self.handle_barcode(barcode, request, **data)

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Handle barcode scan.

        Arguments:
            barcode: Raw barcode value
            request: HTTP request object

        kwargs:
            Any custom fields passed by the specific serializer
        """
        raise NotImplementedError(
            f'handle_barcode not implemented for {self.__class__}'
        )

    def scan_barcode(self, barcode: str, request, **kwargs):
        """Perform a generic 'scan' of the provided barcode data.

        Check each loaded plugin, and return the first valid match
        """

        plugins = registry.with_mixin('barcode')

        # Look for a barcode plugin which knows how to deal with this barcode
        plugin = None
        response = {}

        for current_plugin in plugins:
            result = current_plugin.scan(barcode)

            if result is None:
                continue

            if 'error' in result:
                logger.info(
                    '%s.scan(...) returned an error: %s',
                    current_plugin.__class__.__name__,
                    result['error'],
                )
                if not response:
                    plugin = current_plugin
                    response = result
            else:
                plugin = current_plugin
                response = result
                break

        response['plugin'] = plugin.name if plugin else None
        response['barcode_data'] = barcode
        response['barcode_hash'] = hash_barcode(barcode)

        return response


class BarcodeScan(BarcodeView):
    """Endpoint for handling generic barcode scan requests.

    Barcode data are decoded by the client application,
    and sent to this endpoint (as a JSON object) for validation.

    A barcode could follow the internal InvenTree barcode format,
    or it could match to a third-party barcode format (e.g. Digikey).
    """

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Perform barcode scan action

        Arguments:
            barcode: Raw barcode value
            request: HTTP request object

        kwargs:
            Any custom fields passed by the specific serializer
        """

        result = self.scan_barcode(barcode, request, **kwargs)

        if result['plugin'] is None:
            result['error'] = _('No match found for barcode data')

            raise ValidationError(result)

        result['success'] = _('Match found for barcode data')
        return Response(result)


class BarcodeAssign(BarcodeView):
    """Endpoint for assigning a barcode to a stock item.

    - This only works if the barcode is not already associated with an object in the database
    - If the barcode does not match an object, then the barcode hash is assigned to the StockItem
    """

    serializer_class = barcode_serializers.BarcodeAssignSerializer

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Respond to a barcode assign request.

        Checks inputs and assign barcode (hash) to StockItem.
        """

        # Here we only check against 'InvenTree' plugins
        inventree_barcode_plugin = registry.get_plugin("inventreebarcode")

        # First check if the provided barcode matches an existing database entry
        if inventree_barcode_plugin:
            result = inventree_barcode_plugin.scan(barcode)

            if result is not None:
                result['error'] = _('Barcode matches existing item')
                result['plugin'] = inventree_barcode_plugin.name
                result['barcode_data'] = barcode

                raise ValidationError(result)

        barcode_hash = hash_barcode(barcode)

        valid_labels = []

        for model in InvenTreeInternalBarcodePlugin.get_supported_barcode_models():
            label = model.barcode_model_type()
            valid_labels.append(label)

            if instance := kwargs.get(label, None):
                # Check that the user has the required permission
                app_label = model._meta.app_label
                model_name = model._meta.model_name

                table = f'{app_label}_{model_name}'

                if not RuleSet.check_table_permission(request.user, table, 'change'):
                    raise PermissionDenied({
                        'error': f'You do not have the required permissions for {table}'
                    })

                instance.assign_barcode(barcode_data=barcode, barcode_hash=barcode_hash)

                return Response({
                    'success': f'Assigned barcode to {label} instance',
                    label: {'pk': instance.pk},
                    'barcode_data': barcode,
                    'barcode_hash': barcode_hash,
                })

        # If we got here, it means that no valid model types were provided
        raise ValidationError({
            'error': f"Missing data: provide one of '{valid_labels}'"
        })


class BarcodeUnassign(BarcodeView):
    """Endpoint for unlinking / unassigning a custom barcode from a database object"""

    serializer_class = barcode_serializers.BarcodeUnassignSerializer

    def create(self, request, *args, **kwargs):
        """Respond to a barcode unassign request."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        supported_models = InvenTreeInternalBarcodePlugin.get_supported_barcode_models()

        supported_labels = [model.barcode_model_type() for model in supported_models]
        model_names = ', '.join(supported_labels)

        matched_labels = []

        for label in supported_labels:
            if label in data:
                matched_labels.append(label)

        if len(matched_labels) == 0:
            raise ValidationError({
                'error': f"Missing data: Provide one of '{model_names}'"
            })

        if len(matched_labels) > 1:
            raise ValidationError({
                'error': f"Multiple conflicting fields: '{model_names}'"
            })

        # At this stage, we know that we have received a single valid field
        for model in supported_models:
            label = model.barcode_model_type()

            if instance := data.get(label, None):
                # Check that the user has the required permission
                app_label = model._meta.app_label
                model_name = model._meta.model_name

                table = f'{app_label}_{model_name}'

                if not RuleSet.check_table_permission(request.user, table, 'change'):
                    raise PermissionDenied({
                        'error': f'You do not have the required permissions for {table}'
                    })

                # Unassign the barcode data from the model instance
                instance.unassign_barcode()

                return Response({
                    'success': f'Barcode unassigned from {label} instance'
                })

        # If we get to this point, something has gone wrong!
        raise ValidationError({'error': 'Could not unassign barcode'})


class BarcodePOAllocate(BarcodeView):
    """Endpoint for allocating parts to a purchase order by scanning their barcode

    Note that the scanned barcode may point to:

    - A Part object
    - A ManufacturerPart object
    - A SupplierPart object
    """

    role_required = ['purchase_order.add']

    serializer_class = barcode_serializers.BarcodePOAllocateSerializer

    def get_supplier_part(
        self, purchase_order, part=None, supplier_part=None, manufacturer_part=None
    ):
        """Return a single matching SupplierPart (or else raise an exception)

        Arguments:
            purchase_order: PurchaseOrder object
            part: Part object (optional)
            supplier_part: SupplierPart object (optional)
            manufacturer_part: ManufacturerPart object (optional)

        Returns:
            SupplierPart object

        Raises:
            ValidationError if no matching SupplierPart is found

        """

        import company.models

        supplier = purchase_order.supplier

        supplier_parts = company.models.SupplierPart.objects.filter(supplier=supplier)

        if not part and not supplier_part and not manufacturer_part:
            raise ValidationError({'error': _('No matching part data found')})

        if part:
            if part_id := part.get('pk', None):
                supplier_parts = supplier_parts.filter(part__pk=part_id)

        if supplier_part:
            if supplier_part_id := supplier_part.get('pk', None):
                supplier_parts = supplier_parts.filter(pk=supplier_part_id)

        if manufacturer_part:
            if manufacturer_part_id := manufacturer_part.get('pk', None):
                supplier_parts = supplier_parts.filter(
                    manufacturer_part__pk=manufacturer_part_id
                )

        if supplier_parts.count() == 0:
            raise ValidationError({'error': _('No matching supplier parts found')})

        if supplier_parts.count() > 1:
            raise ValidationError({
                'error': _('Multiple matching supplier parts found')
            })

        # At this stage, we have a single matching supplier part
        return supplier_parts.first()

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Scan the provided barcode data"""

        # The purchase order is provided as part of the request
        purchase_order = kwargs.get('purchase_order')

        result = self.scan_barcode(barcode, request, **kwargs)

        if result['plugin'] is None:
            result['error'] = _('No match found for barcode data')
            raise ValidationError(result)

        supplier_part = self.get_supplier_part(
            purchase_order,
            part=result.get('part', None),
            supplier_part=result.get('supplierpart', None),
            manufacturer_part=result.get('manufacturerpart', None),
        )

        result['success'] = _('Matched supplier part')
        result['supplierpart'] = supplier_part.format_matched_response()

        # TODO: Determine the 'quantity to order' for the supplier part

        return Response(result)


class BarcodePOReceive(BarcodeView):
    """Endpoint for handling receiving parts by scanning their barcode.

    Barcode data are decoded by the client application,
    and sent to this endpoint (as a JSON object) for validation.

    The barcode should follow a third-party barcode format (e.g. Digikey)
    and ideally contain order_number and quantity information.

    The following parameters are available:

    - barcode: The raw barcode data (required)
    - purchase_order: The purchase order containing the item to receive (optional)
    - location: The destination location for the received item (optional)
    """

    role_required = ['purchase_order.add']

    serializer_class = barcode_serializers.BarcodePOReceiveSerializer

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Handle a barcode scan for a purchase order item."""

        logger.debug("BarcodePOReceive: scanned barcode - '%s'", barcode)

        # Extract optional fields from the dataset
        purchase_order = kwargs.get('purchase_order', None)
        location = kwargs.get('location', None)

        plugins = registry.with_mixin('barcode')

        # Look for a barcode plugin which knows how to deal with this barcode
        plugin = None

        response = {'barcode_data': barcode, 'barcode_hash': hash_barcode(barcode)}

        internal_barcode_plugin = next(
            filter(lambda plugin: plugin.name == 'InvenTreeBarcode', plugins)
        )

        if result := internal_barcode_plugin.scan(barcode):
            if 'stockitem' in result:
                response['error'] = _('Item has already been received')
                raise ValidationError(response)

        # Now, look just for "supplier-barcode" plugins
        plugins = registry.with_mixin('supplier-barcode')

        plugin_response = None

        for current_plugin in plugins:
            result = current_plugin.scan_receive_item(
                barcode, request.user, purchase_order=purchase_order, location=location
            )

            if result is None:
                continue

            if 'error' in result:
                logger.info(
                    '%s.scan_receive_item(...) returned an error: %s',
                    current_plugin.__class__.__name__,
                    result['error'],
                )
                if not plugin_response:
                    plugin = current_plugin
                    plugin_response = result
            else:
                plugin = current_plugin
                plugin_response = result
                break

        response['plugin'] = plugin.name if plugin else None

        if plugin_response:
            response = {**response, **plugin_response}

        # A plugin has not been found!
        if plugin is None:
            response['error'] = _('No match for supplier barcode')
            raise ValidationError(response)
        elif 'error' in response:
            raise ValidationError(response)
        else:
            return Response(response)


class BarcodeSOAllocate(BarcodeView):
    """Endpoint for allocating stock to a sales order, by scanning barcode.

    The scanned barcode should map to a StockItem object.

    Additional fields can be passed to the endpoint:

    - SalesOrder (Required)
    - Line Item
    - Shipment
    - Quantity
    """

    role_required = ['sales_order.add']

    serializer_class = barcode_serializers.BarcodeSOAllocateSerializer

    def get_line_item(self, stock_item, **kwargs):
        """Return the matching line item for the provided stock item"""

        # Extract sales order object (required field)
        sales_order = kwargs['sales_order']

        # Next, check if a line-item is provided (optional field)
        if line_item := kwargs.get('line', None):
            return line_item

        # If not provided, we need to find the correct line item
        parts = stock_item.part.get_ancestors(include_self=True)

        # Find any matching line items for the stock item
        lines = order.models.SalesOrderLineItem.objects.filter(
            order=sales_order, part__in=parts, shipped__lte=F('quantity')
        )

        if lines.count() > 1:
            raise ValidationError({'error': _('Multiple matching line items found')})

        if lines.count() == 0:
            raise ValidationError({'error': _('No matching line item found')})

        return lines.first()

    def get_shipment(self, **kwargs):
        """Extract the shipment from the provided kwargs, or guess"""

        sales_order = kwargs['sales_order']

        if shipment := kwargs.get('shipment', None):
            if shipment.order != sales_order:
                raise ValidationError({
                    'error': _('Shipment does not match sales order')
                })

            return shipment

        shipments = order.models.SalesOrderShipment.objects.filter(
            order=sales_order, delivery_date=None
        )

        if shipments.count() == 1:
            return shipments.first()

        # If shipment cannot be determined, return None
        return None

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Handle barcode scan for sales order allocation."""

        logger.debug("BarcodeSOAllocate: scanned barcode - '%s'", barcode)

        result = self.scan_barcode(barcode, request, **kwargs)

        if result['plugin'] is None:
            result['error'] = _('No match found for barcode data')
            raise ValidationError(result)

        # Check that the scanned barcode was a StockItem
        if 'stockitem' not in result:
            result['error'] = _('Barcode does not match an existing stock item')
            raise ValidationError(result)

        try:
            stock_item_id = result['stockitem'].get('pk', None)
            stock_item = stock.models.StockItem.objects.get(pk=stock_item_id)
        except (ValueError, stock.models.StockItem.DoesNotExist):
            result['error'] = _('Barcode does not match an existing stock item')
            raise ValidationError(result)

        # At this stage, we have a valid StockItem object
        # Extract any other data from the kwargs
        line_item = self.get_line_item(stock_item, **kwargs)
        sales_order = kwargs['sales_order']
        shipment = self.get_shipment(**kwargs)

        if stock_item is not None and line_item is not None:
            if stock_item.part != line_item.part:
                result['error'] = _('Stock item does not match line item')
                raise ValidationError(result)

        quantity = kwargs.get('quantity', None)

        # Override quantity for serialized items
        if stock_item.serialized:
            quantity = 1

        if quantity is None:
            quantity = line_item.quantity - line_item.shipped
            quantity = min(quantity, stock_item.unallocated_quantity())

        response = {
            'stock_item': stock_item.pk if stock_item else None,
            'part': stock_item.part.pk if stock_item else None,
            'sales_order': sales_order.pk if sales_order else None,
            'line_item': line_item.pk if line_item else None,
            'shipment': shipment.pk if shipment else None,
            'quantity': quantity,
        }

        if stock_item is not None and quantity is not None:
            if stock_item.unallocated_quantity() < quantity:
                response['error'] = _('Insufficient stock available')
                raise ValidationError(response)

        # If we have sufficient information, we can allocate the stock item
        if all((x is not None for x in [line_item, sales_order, shipment, quantity])):
            order.models.SalesOrderAllocation.objects.create(
                line=line_item, shipment=shipment, item=stock_item, quantity=quantity
            )

            response['success'] = _('Stock item allocated to sales order')

            return Response(response)

        response['error'] = _('Not enough information')
        response['action_required'] = True

        raise ValidationError(response)


barcode_api_urls = [
    # Link a third-party barcode to an item (e.g. Part / StockItem / etc)
    path('link/', BarcodeAssign.as_view(), name='api-barcode-link'),
    # Unlink a third-party barcode from an item
    path('unlink/', BarcodeUnassign.as_view(), name='api-barcode-unlink'),
    # Receive a purchase order item by scanning its barcode
    path('po-receive/', BarcodePOReceive.as_view(), name='api-barcode-po-receive'),
    # Allocate parts to a purchase order by scanning their barcode
    path('po-allocate/', BarcodePOAllocate.as_view(), name='api-barcode-po-allocate'),
    # Allocate stock to a sales order by scanning barcode
    path('so-allocate/', BarcodeSOAllocate.as_view(), name='api-barcode-so-allocate'),
    # Catch-all performs barcode 'scan'
    re_path(r'^.*$', BarcodeScan.as_view(), name='api-barcode-scan'),
]
