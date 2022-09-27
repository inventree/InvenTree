"""API endpoints for barcode plugins."""


from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from InvenTree.helpers import hash_barcode
from plugin import registry
from plugin.builtin.barcodes.inventree_barcode import (
    InvenTreeExternalBarcodePlugin, InvenTreeInternalBarcodePlugin)


class BarcodeScan(APIView):
    """Endpoint for handling generic barcode scan requests.

    Barcode data are decoded by the client application,
    and sent to this endpoint (as a JSON object) for validation.

    A barcode could follow the internal InvenTree barcode format,
    or it could match to a third-party barcode format (e.g. Digikey).

    When a barcode is sent to the server, the following parameters must be provided:

    - barcode: The raw barcode data

    plugins:
    Third-party barcode formats may be supported using 'plugins'
    (more information to follow)

    hashing:
    Barcode hashes are calculated using MD5
    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        """Respond to a barcode POST request.

        Check if required info was provided and then run though the plugin steps or try to match up-
        """
        data = request.data

        if 'barcode' not in data:
            raise ValidationError({'barcode': _('Must provide barcode_data parameter')})

        # Ensure that the default barcode handlers are run first
        plugins = [
            InvenTreeInternalBarcodePlugin(),
            InvenTreeExternalBarcodePlugin(),
        ] + registry.with_mixin('barcode')

        barcode_data = data.get('barcode')
        barcode_hash = hash_barcode(barcode_data)

        # Look for a barcode plugin which knows how to deal with this barcode
        plugin = None
        response = {}

        for current_plugin in plugins:

            result = current_plugin.scan(barcode_data)

            if result is not None:
                plugin = current_plugin
                response = result
                break

        response['plugin'] = plugin.name if plugin else None
        response['barcode_data'] = barcode_data
        response['barcode_hash'] = barcode_hash

        # A plugin has not been found!
        if plugin is None:
            response['error'] = _('No match found for barcode data')

            raise ValidationError(response)
        else:
            response['success'] = _('Match found for barcode data')
            return Response(response)


class BarcodeAssign(APIView):
    """Endpoint for assigning a barcode to a stock item.

    - This only works if the barcode is not already associated with an object in the database
    - If the barcode does not match an object, then the barcode hash is assigned to the StockItem
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request, *args, **kwargs):
        """Respond to a barcode assign POST request.

        Checks inputs and assign barcode (hash) to StockItem.
        """

        data = request.data

        if 'barcode' not in data:
            raise ValidationError({'barcode': _('Must provide barcode_data parameter')})

        barcode_data = data['barcode']

        # Here we only check against 'InvenTree' plugins
        plugins = [
            InvenTreeInternalBarcodePlugin(),
            InvenTreeExternalBarcodePlugin(),
        ]

        # First check if the provided barcode matches an existing database entry
        for plugin in plugins:
            result = plugin.scan(barcode_data)

            if result is not None:
                result["error"] = _("Barcode matches existing item")
                result["plugin"] = plugin.name
                result["barcode_data"] = barcode_data

                raise ValidationError(result)

        barcode_hash = hash_barcode(barcode_data)

        valid_labels = []

        for model in InvenTreeExternalBarcodePlugin.get_supported_barcode_models():
            label = model.barcode_model_type()
            valid_labels.append(label)

            if label in data:
                try:
                    instance = model.objects.get(pk=data[label])

                    instance.assign_barcode(
                        barcode_data=barcode_data,
                        barcode_hash=barcode_hash,
                    )

                    return Response({
                        'success': f"Assigned barcode to {label} instance",
                        label: {
                            'pk': instance.pk,
                        },
                        "barcode_data": barcode_data,
                        "barcode_hash": barcode_hash,
                    })

                except (ValueError, model.DoesNotExist):
                    raise ValidationError({
                        'error': f"No matching {label} instance found in database",
                    })

        # If we got here, it means that no valid model types were provided
        raise ValidationError({
            'error': f"Missing data: provide one of '{valid_labels}'",
        })


class BarcodeUnassign(APIView):
    """Endpoint for unlinking / unassigning a custom barcode from a database object"""

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        """Respond to a barcode unassign POST request"""

        # The following database models support assignment of third-party barcodes
        supported_models = InvenTreeExternalBarcodePlugin.get_supported_barcode_models()

        supported_labels = [model.barcode_model_type() for model in supported_models]
        model_names = ', '.join(supported_labels)

        data = request.data

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
                'error': f"Multiple conflicting fields: '{model_names}'",
            })

        # At this stage, we know that we have received a single valid field
        for model in supported_models:
            label = model.barcode_model_type()

            if label in data:
                try:
                    instance = model.objects.get(pk=data[label])
                except (ValueError, model.DoesNotExist):
                    raise ValidationError({
                        label: _('No match found for provided value')
                    })

                # Unassign the barcode data from the model instance
                instance.unassign_barcode()

                return Response({
                    'success': 'Barcode unassigned from {label} instance',
                })

        # If we get to this point, something has gone wrong!
        raise ValidationError({
            'error': 'Could not unassign barcode',
        })


barcode_api_urls = [
    # Link a third-party barcode to an item (e.g. Part / StockItem / etc)
    path('link/', BarcodeAssign.as_view(), name='api-barcode-link'),

    # Unlink a third-pary barcode from an item
    path('unlink/', BarcodeUnassign.as_view(), name='api-barcode-unlink'),

    # Catch-all performs barcode 'scan'
    re_path(r'^.*$', BarcodeScan.as_view(), name='api-barcode-scan'),
]
