"""API endpoints for barcode plugins."""

from django.db.models import F
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

import structlog
from django_filters import rest_framework as rest_filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

import common.models
import order.models
import plugin.base.barcodes.helper
import stock.models
from common.settings import get_global_setting
from InvenTree.api import BulkDeleteMixin
from InvenTree.exceptions import log_error
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.helpers import hash_barcode
from InvenTree.mixins import ListAPI, RetrieveDestroyAPI
from InvenTree.permissions import IsStaffOrReadOnly
from plugin import registry
from users.models import RuleSet

from . import serializers as barcode_serializers

logger = structlog.get_logger('inventree')


class BarcodeView(CreateAPIView):
    """Custom view class for handling a barcode scan."""

    # Default serializer class (can be overridden)
    serializer_class = barcode_serializers.BarcodeSerializer

    def log_scan(self, request, response=None, result=False):
        """Log a barcode scan to the database.

        Arguments:
            request: HTTP request object
            response: Optional response data
        """
        from common.models import BarcodeScanResult

        # Extract context data from the request
        context = {**request.GET.dict(), **request.POST.dict(), **request.data}

        barcode = context.pop('barcode', '')

        # Exit if storing barcode scans is disabled
        if not get_global_setting('BARCODE_STORE_RESULTS', backup=False, create=False):
            return

        # Ensure that the response data is stringified first, otherwise cannot be JSON encoded
        if isinstance(response, dict):
            response = {key: str(value) for key, value in response.items()}
        elif response is None:
            pass
        else:
            response = str(response)

        # Ensure that the context data is stringified first, otherwise cannot be JSON encoded
        if isinstance(context, dict):
            context = {key: str(value) for key, value in context.items()}
        elif context is None:
            pass
        else:
            context = str(context)

        # Ensure data is not too long
        if len(barcode) > BarcodeScanResult.BARCODE_SCAN_MAX_LEN:
            barcode = barcode[: BarcodeScanResult.BARCODE_SCAN_MAX_LEN]

        try:
            BarcodeScanResult.objects.create(
                data=barcode,
                user=request.user,
                endpoint=request.path,
                response=response,
                result=result,
                context=context,
            )

            # Ensure that we do not store too many scans
            max_scans = int(get_global_setting('BARCODE_RESULTS_MAX_NUM', create=False))
            num_scans = BarcodeScanResult.objects.count()

            if num_scans > max_scans:
                n = num_scans - max_scans
                old_scan_ids = list(
                    BarcodeScanResult.objects.all()
                    .order_by('timestamp')
                    .values_list('pk', flat=True)[:n]
                )
                BarcodeScanResult.objects.filter(pk__in=old_scan_ids).delete()
        except Exception:
            # Gracefully log error to database
            log_error(f'{self.__class__.__name__}.log_scan')

    def queryset(self):
        """This API view does not have a queryset."""
        return None

    # Default permission classes (can be overridden)
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Handle create method - override default create."""
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as exc:
            self.log_scan(request, response={'error': str(exc)}, result=False)
            raise exc

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
            try:
                result = current_plugin.scan(barcode)
            except Exception:
                log_error('BarcodeView.scan_barcode')
                continue

            if result is None:
                continue

            if len(result) == 0:
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
                # Return the first successful match
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
        """Perform barcode scan action.

        Arguments:
            barcode: Raw barcode value
            request: HTTP request object

        kwargs:
            Any custom fields passed by the specific serializer
        """
        response = self.scan_barcode(barcode, request, **kwargs)

        if response['plugin'] is None:
            response['error'] = _('No match found for barcode data')
            self.log_scan(request, response, False)
            raise ValidationError(response)

        response['success'] = _('Match found for barcode data')

        # Log the scan result
        self.log_scan(request, response, True)

        return Response(response)


@extend_schema_view(
    post=extend_schema(responses={200: barcode_serializers.BarcodeSerializer})
)
class BarcodeGenerate(CreateAPIView):
    """Endpoint for generating a barcode for a database object.

    The barcode is generated by the selected barcode plugin.
    """

    serializer_class = barcode_serializers.BarcodeGenerateSerializer

    def queryset(self):
        """This API view does not have a queryset."""
        return None

    # Default permission classes (can be overridden)
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Perform the barcode generation action."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        model = serializer.validated_data.get('model')
        pk = serializer.validated_data.get('pk')
        model_cls = plugin.base.barcodes.helper.get_supported_barcode_models_map().get(
            model, None
        )

        if model_cls is None:
            raise ValidationError({'error': _('Model is not supported')})

        try:
            model_instance = model_cls.objects.get(pk=pk)
        except model_cls.DoesNotExist:
            raise ValidationError({'error': _('Model instance not found')})

        barcode_data = plugin.base.barcodes.helper.generate_barcode(model_instance)

        return Response({'barcode': barcode_data}, status=status.HTTP_200_OK)


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
        inventree_barcode_plugin = registry.get_plugin('inventreebarcode')

        # First check if the provided barcode matches an existing database entry
        if inventree_barcode_plugin:
            result = inventree_barcode_plugin.scan(barcode)

            if result is not None:
                result['error'] = _('Barcode matches existing item')
                result['plugin'] = inventree_barcode_plugin.name
                result['barcode_data'] = barcode

                result.pop('success', None)

                raise ValidationError(result)

        barcode_hash = hash_barcode(barcode)

        valid_labels = []

        for model in plugin.base.barcodes.helper.get_supported_barcode_models():
            label = model.barcode_model_type()
            valid_labels.append(label)

            if instance := kwargs.get(label):
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
    """Endpoint for unlinking / unassigning a custom barcode from a database object."""

    serializer_class = barcode_serializers.BarcodeUnassignSerializer

    def create(self, request, *args, **kwargs):
        """Respond to a barcode unassign request."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        supported_models = plugin.base.barcodes.helper.get_supported_barcode_models()

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
    """Endpoint for allocating parts to a purchase order by scanning their barcode.

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
        """Return a single matching SupplierPart (or else raise an exception).

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
            raise ValidationError(_('No matching part data found'))

        if part and (part_id := part.get('pk', None)):
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
            raise ValidationError(_('No matching supplier parts found'))

        if supplier_parts.count() > 1:
            raise ValidationError(_('Multiple matching supplier parts found'))

        # At this stage, we have a single matching supplier part
        return supplier_parts.first()

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Scan the provided barcode data."""
        # The purchase order is provided as part of the request
        purchase_order = kwargs.get('purchase_order')

        response = self.scan_barcode(barcode, request, **kwargs)

        if response['plugin'] is None:
            response['error'] = _('No matching plugin found for barcode data')

        else:
            try:
                supplier_part = self.get_supplier_part(
                    purchase_order,
                    part=response.get('part', None),
                    supplier_part=response.get('supplierpart', None),
                    manufacturer_part=response.get('manufacturerpart', None),
                )
                response['success'] = _('Matched supplier part')
                response['supplierpart'] = supplier_part.format_matched_response()
            except ValidationError as e:
                response['error'] = str(e)

        # TODO: Determine the 'quantity to order' for the supplier part

        self.log_scan(request, response, 'success' in response)

        if 'error' in response:
            raise ValidationError

        return Response(response)


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
        supplier = kwargs.get('supplier')
        purchase_order = kwargs.get('purchase_order')
        location = kwargs.get('location')
        line_item = kwargs.get('line_item')
        auto_allocate = kwargs.get('auto_allocate', True)

        # Extract location from PurchaseOrder, if available
        if not location and purchase_order:
            try:
                po = order.models.PurchaseOrder.objects.get(pk=purchase_order)
                if po.destination:
                    location = po.destination.pk
            except Exception:
                pass

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
                self.log_scan(request, response, False)
                raise ValidationError(response)

        # Now, look just for "supplier-barcode" plugins
        plugins = registry.with_mixin('supplier-barcode')

        plugin_response = None

        for current_plugin in plugins:
            try:
                result = current_plugin.scan_receive_item(
                    barcode,
                    request.user,
                    supplier=supplier,
                    purchase_order=purchase_order,
                    location=location,
                    line_item=line_item,
                    auto_allocate=auto_allocate,
                )
            except Exception:
                log_error('BarcodePOReceive.handle_barcode')
                continue

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
            response['error'] = _('No plugin match for supplier barcode')

        self.log_scan(request, response, 'success' in response)

        if 'error' in response:
            raise ValidationError(response)

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
        """Return the matching line item for the provided stock item.

        Raises:
            ValidationError: If no single matching line item is found
        """
        # Extract sales order object (required field)
        sales_order = kwargs['sales_order']

        # Next, check if a line-item is provided (optional field)
        if line_item := kwargs.get('line'):
            return line_item

        # If not provided, we need to find the correct line item
        parts = stock_item.part.get_ancestors(include_self=True)

        # Find any matching line items for the stock item
        lines = order.models.SalesOrderLineItem.objects.filter(
            order=sales_order, part__in=parts, shipped__lte=F('quantity')
        )

        if lines.count() > 1:
            raise ValidationError(_('Multiple matching line items found'))

        if lines.count() == 0:
            raise ValidationError(_('No matching line item found'))

        return lines.first()

    def get_shipment(self, **kwargs):
        """Extract the shipment from the provided kwargs, or guess.

        Raises:
            ValidationError: If the shipment does not match the sales order
        """
        sales_order = kwargs['sales_order']

        if shipment := kwargs.get('shipment'):
            if shipment.order != sales_order:
                raise ValidationError(_('Shipment does not match sales order'))

            return shipment

        shipments = order.models.SalesOrderShipment.objects.filter(
            order=sales_order, delivery_date=None
        )

        if shipments.count() == 1:
            return shipments.first()

        # If shipment cannot be determined, return None
        return None

    def handle_barcode(self, barcode: str, request, **kwargs):
        """Handle barcode scan for sales order allocation.

        Arguments:
            barcode: Raw barcode data
            request: HTTP request object

        kwargs:
            sales_order: SalesOrder ID value (required)
            line: SalesOrderLineItem ID value (optional)
            shipment: SalesOrderShipment ID value (optional)
        """
        logger.debug("BarcodeSOAllocate: scanned barcode - '%s'", barcode)

        response = self.scan_barcode(barcode, request, **kwargs)

        if 'sales_order' not in kwargs:
            # SalesOrder ID *must* be provided
            response['error'] = _('No sales order provided')
        elif response['plugin'] is None:
            # Check that the barcode at least matches a plugin
            response['error'] = _('No matching plugin found for barcode data')
        else:
            try:
                stock_item_id = response['stockitem'].get('pk', None)
                stock_item = stock.models.StockItem.objects.get(pk=stock_item_id)
            except Exception:
                response['error'] = _('Barcode does not match an existing stock item')

        if 'error' in response:
            self.log_scan(request, response, False)
            raise ValidationError(response)

        # At this stage, we have a valid StockItem object

        try:
            # Extract any other data from the kwargs
            # Note: This may raise a ValidationError at some point - we break on the first error
            sales_order = kwargs['sales_order']
            line_item = self.get_line_item(stock_item, **kwargs)
            shipment = self.get_shipment(**kwargs)
            if stock_item is not None and line_item is not None:
                if stock_item.part != line_item.part:
                    response['error'] = _('Stock item does not match line item')
        except ValidationError as e:
            response['error'] = str(e)

        if 'error' in response:
            self.log_scan(request, response, False)
            raise ValidationError(response)

        quantity = kwargs.get('quantity')

        # Override quantity for serialized items
        if stock_item.serialized:
            quantity = 1

        elif quantity is None:
            quantity = line_item.quantity - line_item.shipped
            quantity = min(quantity, stock_item.unallocated_quantity())

        response = {
            **response,
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

            # If we have sufficient information, we can allocate the stock item
            elif all(
                x is not None for x in [line_item, sales_order, shipment, quantity]
            ):
                order.models.SalesOrderAllocation.objects.create(
                    line=line_item,
                    shipment=shipment,
                    item=stock_item,
                    quantity=quantity,
                )

                response['success'] = _('Stock item allocated to sales order')

        else:
            response['error'] = _('Not enough information')
            response['action_required'] = True

        self.log_scan(request, response, 'success' in response)

        if 'error' in response:
            raise ValidationError(response)
        else:
            return Response(response)


class BarcodeScanResultMixin:
    """Mixin class for BarcodeScan API endpoints."""

    queryset = common.models.BarcodeScanResult.objects.all()
    serializer_class = barcode_serializers.BarcodeScanResultSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]

    def get_queryset(self):
        """Return the queryset for the BarcodeScan API."""
        queryset = super().get_queryset()

        # Pre-fetch user data
        queryset = queryset.prefetch_related('user')

        return queryset


class BarcodeScanResultFilter(rest_filters.FilterSet):
    """Custom filterset for the BarcodeScanResult API."""

    class Meta:
        """Meta class for the BarcodeScanResultFilter."""

        model = common.models.BarcodeScanResult
        fields = ['user', 'result']


class BarcodeScanResultList(BarcodeScanResultMixin, BulkDeleteMixin, ListAPI):
    """List API endpoint for BarcodeScan objects."""

    filterset_class = BarcodeScanResultFilter
    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['user', 'plugin', 'timestamp', 'endpoint', 'result']

    ordering = '-timestamp'

    search_fields = ['plugin']


class BarcodeScanResultDetail(BarcodeScanResultMixin, RetrieveDestroyAPI):
    """Detail endpoint for a BarcodeScan object."""


barcode_api_urls = [
    # Barcode scan history
    path(
        'history/',
        include([
            path(
                '<int:pk>/',
                BarcodeScanResultDetail.as_view(),
                name='api-barcode-scan-result-detail',
            ),
            path(
                '', BarcodeScanResultList.as_view(), name='api-barcode-scan-result-list'
            ),
        ]),
    ),
    # Generate a barcode for a database object
    path('generate/', BarcodeGenerate.as_view(), name='api-barcode-generate'),
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
    path('', BarcodeScan.as_view(), name='api-barcode-scan'),
]
