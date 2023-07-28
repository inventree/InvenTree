"""Main JSON interface views."""

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from django_q.models import OrmQ
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

import users.models
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListCreateAPI
from InvenTree.permissions import RolePermission
from part.templatetags.inventree_extras import plugins_info
from plugin.serializers import MetadataSerializer

from .mixins import RetrieveUpdateAPI
from .status import is_worker_running
from .version import (inventreeApiVersion, inventreeInstanceName,
                      inventreeVersion)
from .views import AjaxView


class InfoView(AjaxView):
    """Simple JSON endpoint for InvenTree information.

    Use to confirm that the server is running, etc.
    """

    permission_classes = [permissions.AllowAny]

    def worker_pending_tasks(self):
        """Return the current number of outstanding background tasks"""

        return OrmQ.objects.count()

    def get(self, request, *args, **kwargs):
        """Serve current server information."""
        data = {
            'server': 'InvenTree',
            'version': inventreeVersion(),
            'instance': inventreeInstanceName(),
            'apiVersion': inventreeApiVersion(),
            'worker_running': is_worker_running(),
            'worker_pending_tasks': self.worker_pending_tasks(),
            'plugins_enabled': settings.PLUGINS_ENABLED,
            'active_plugins': plugins_info(),
        }

        return JsonResponse(data)


class NotFoundView(AjaxView):
    """Simple JSON view when accessing an invalid API view."""

    permission_classes = [permissions.AllowAny]

    def not_found(self, request):
        """Return a 404 error"""
        return JsonResponse(
            {
                'detail': _('API endpoint not found'),
                'url': request.build_absolute_uri(),
            },
            status=404
        )

    def options(self, request, *args, **kwargs):
        """Return 404"""
        return self.not_found(request)

    def get(self, request, *args, **kwargs):
        """Return 404"""
        return self.not_found(request)

    def post(self, request, *args, **kwargs):
        """Return 404"""
        return self.not_found(request)

    def patch(self, request, *args, **kwargs):
        """Return 404"""
        return self.not_found(request)

    def put(self, request, *args, **kwargs):
        """Return 404"""
        return self.not_found(request)

    def delete(self, request, *args, **kwargs):
        """Return 404"""
        return self.not_found(request)


class BulkDeleteMixin:
    """Mixin class for enabling 'bulk delete' operations for various models.

    Bulk delete allows for multiple items to be deleted in a single API query,
    rather than using multiple API calls to the various detail endpoints.

    This is implemented for two major reasons:
    - Atomicity (guaranteed that either *all* items are deleted, or *none*)
    - Speed (single API call and DB query)
    """

    def filter_delete_queryset(self, queryset, request):
        """Provide custom filtering for the queryset *before* it is deleted"""
        return queryset

    def delete(self, request, *args, **kwargs):
        """Perform a DELETE operation against this list endpoint.

        We expect a list of primary-key (ID) values to be supplied as a JSON object, e.g.
        {
            items: [4, 8, 15, 16, 23, 42]
        }

        """
        model = self.serializer_class.Meta.model

        # Extract the items from the request body
        try:
            items = request.data.getlist('items', None)
        except AttributeError:
            items = request.data.get('items', None)

        # Extract the filters from the request body
        try:
            filters = request.data.getlist('filters', None)
        except AttributeError:
            filters = request.data.get('filters', None)

        if not items and not filters:
            raise ValidationError({
                "non_field_errors": ["List of items or filters must be provided for bulk deletion"],
            })

        if items and type(items) is not list:
            raise ValidationError({
                "items": ["'items' must be supplied as a list object"]
            })

        if filters and type(filters) is not dict:
            raise ValidationError({
                "filters": ["'filters' must be supplied as a dict object"]
            })

        # Keep track of how many items we deleted
        n_deleted = 0

        with transaction.atomic():

            # Start with *all* models and perform basic filtering
            queryset = model.objects.all()
            queryset = self.filter_delete_queryset(queryset, request)

            # Filter by provided item ID values
            if items:
                queryset = queryset.filter(id__in=items)

            # Filter by provided filters
            if filters:
                queryset = queryset.filter(**filters)

            n_deleted = queryset.count()
            queryset.delete()

        return Response(
            {
                'success': f"Deleted {n_deleted} items",
            },
            status=204
        )


class ListCreateDestroyAPIView(BulkDeleteMixin, ListCreateAPI):
    """Custom API endpoint which provides BulkDelete functionality in addition to List and Create"""
    ...


class APIDownloadMixin:
    """Mixin for enabling a LIST endpoint to be downloaded a file.

    To download the data, add the ?export=<fmt> to the query string.

    The implementing class must provided a download_queryset method,
    e.g.

    def download_queryset(self, queryset, export_format):
        dataset = StockItemResource().export(queryset=queryset)

        filedata = dataset.export(export_format)

        filename = 'InvenTree_Stocktake_{date}.{fmt}'.format(
            date=datetime.now().strftime("%d-%b-%Y"),
            fmt=export_format
        )

        return DownloadFile(filedata, filename)
    """

    def get(self, request, *args, **kwargs):
        """Generic handler for a download request."""
        export_format = request.query_params.get('export', None)

        if export_format and export_format in ['csv', 'tsv', 'xls', 'xlsx']:
            queryset = self.filter_queryset(self.get_queryset())
            return self.download_queryset(queryset, export_format)

        else:
            # Default to the parent class implementation
            return super().get(request, *args, **kwargs)

    def download_queryset(self, queryset, export_format):
        """This function must be implemented to provide a downloadFile request."""
        raise NotImplementedError("download_queryset method not implemented!")


class AttachmentMixin:
    """Mixin for creating attachment objects, and ensuring the user information is saved correctly."""

    permission_classes = [
        permissions.IsAuthenticated,
        RolePermission,
    ]

    filter_backends = SEARCH_ORDER_FILTER

    def perform_create(self, serializer):
        """Save the user information when a file is uploaded."""
        attachment = serializer.save()
        attachment.user = self.request.user
        attachment.save()


class APISearchView(APIView):
    """A general-purpose 'search' API endpoint

    Returns hits against a number of different models simultaneously,
    to consolidate multiple API requests into a single query.

    Is much more efficient and simplifies code!
    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_result_types(self):
        """Construct a list of search types we can return"""

        import build.api
        import company.api
        import order.api
        import part.api
        import stock.api

        return {
            'build': build.api.BuildList,
            'company': company.api.CompanyList,
            'manufacturerpart': company.api.ManufacturerPartList,
            'supplierpart': company.api.SupplierPartList,
            'part': part.api.PartList,
            'partcategory': part.api.CategoryList,
            'purchaseorder': order.api.PurchaseOrderList,
            'returnorder': order.api.ReturnOrderList,
            'salesorder': order.api.SalesOrderList,
            'stockitem': stock.api.StockList,
            'stocklocation': stock.api.StockLocationList,
        }

    def post(self, request, *args, **kwargs):
        """Perform search query against available models"""

        data = request.data

        results = {}

        # These parameters are passed through to the individual queries, with optional default values
        pass_through_params = {
            'search': '',
            'search_regex': False,
            'search_whole': False,
            'limit': 1,
            'offset': 0,
        }

        for key, cls in self.get_result_types().items():
            # Only return results which are specifically requested
            if key in data:

                params = data[key]

                for k, v in pass_through_params.items():
                    params[k] = request.data.get(k, v)

                # Enforce json encoding
                params['format'] = 'json'

                # Ignore if the params are wrong
                if type(params) is not dict:
                    continue

                view = cls()

                # Override regular query params with specific ones for this search request
                request._request.GET = params
                view.request = request
                view.format_kwarg = 'format'

                # Check permissions and update results dict with particular query
                model = view.serializer_class.Meta.model
                app_label = model._meta.app_label
                model_name = model._meta.model_name
                table = f'{app_label}_{model_name}'

                try:
                    if users.models.RuleSet.check_table_permission(request.user, table, 'view'):
                        results[key] = view.list(request, *args, **kwargs).data
                    else:
                        results[key] = {
                            'error': _('User does not have permission to view this model')
                        }
                except Exception as exc:
                    results[key] = {
                        'error': str(exc)
                    }

        return Response(results)


class MetadataView(RetrieveUpdateAPI):
    """Generic API endpoint for reading and editing metadata for a model"""

    MODEL_REF = 'model'

    def get_model_type(self):
        """Return the model type associated with this API instance"""
        model = self.kwargs.get(self.MODEL_REF, None)

        if model is None:
            raise ValidationError(f"MetadataView called without '{self.MODEL_REF}' parameter")

        return model

    def get_permission_model(self):
        """Return the 'permission' model associated with this view"""
        return self.get_model_type()

    def get_queryset(self):
        """Return the queryset for this endpoint"""
        return self.get_model_type().objects.all()

    def get_serializer(self, *args, **kwargs):
        """Return MetadataSerializer instance"""
        return MetadataSerializer(self.get_model_type(), *args, **kwargs)
