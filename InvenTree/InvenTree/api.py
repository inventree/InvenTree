"""Main JSON interface views."""

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from django_q.models import OrmQ
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

import InvenTree.version
import users.models
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListCreateAPI
from InvenTree.permissions import RolePermission
from part.templatetags.inventree_extras import plugins_info
from plugin.serializers import MetadataSerializer
from users.models import ApiToken

from .email import is_email_configured
from .mixins import ListAPI, RetrieveUpdateAPI
from .status import check_system_health, is_worker_running
from .version import inventreeApiText
from .views import AjaxView


class VersionView(GenericAPIView):
    """Simple JSON endpoint for InvenTree version information."""

    permission_classes = [
        permissions.IsAdminUser,
    ]

    def get(self, request, *args, **kwargs):
        """Return information about the InvenTree server."""
        return JsonResponse({
            'dev': InvenTree.version.isInvenTreeDevelopmentVersion(),
            'up_to_date': InvenTree.version.isInvenTreeUpToDate(),
            'version': {
                'server': InvenTree.version.inventreeVersion(),
                'api': InvenTree.version.inventreeApiVersion(),
                'commit_hash': InvenTree.version.inventreeCommitHash(),
                'commit_date': InvenTree.version.inventreeCommitDate(),
                'commit_branch': InvenTree.version.inventreeBranch(),
                'python': InvenTree.version.inventreePythonVersion(),
                'django': InvenTree.version.inventreeDjangoVersion()
            },
            'links': {
                'doc': InvenTree.version.inventreeDocUrl(),
                'code': InvenTree.version.inventreeGithubUrl(),
                'credit': InvenTree.version.inventreeCreditsUrl(),
                'app': InvenTree.version.inventreeAppUrl(),
                'bug': f'{InvenTree.version.inventreeGithubUrl()}/issues'
            }
        })


class VersionSerializer(serializers.Serializer):
    """Serializer for a single version."""
    version = serializers.CharField()
    date = serializers.CharField()
    gh = serializers.CharField()
    text = serializers.CharField()
    latest = serializers.BooleanField()

    class Meta:
        """Meta class for VersionSerializer."""
        fields = ['version', 'date', 'gh', 'text', 'latest']


class VersionApiSerializer(serializers.Serializer):
    """Serializer for the version api endpoint."""
    VersionSerializer(many=True)


class VersionTextView(ListAPI):
    """Simple JSON endpoint for InvenTree version text."""
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(responses={200: OpenApiResponse(response=VersionApiSerializer)})
    def list(self, request, *args, **kwargs):
        """Return information about the InvenTree server."""
        return JsonResponse(inventreeApiText())


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
        is_staff = request.user.is_staff
        if not is_staff and request.user.is_anonymous:
            # Might be Token auth - check if so
            is_staff = self.check_auth_header(request)

        data = {
            'server': 'InvenTree',
            'version': InvenTree.version.inventreeVersion(),
            'instance': InvenTree.version.inventreeInstanceName(),
            'apiVersion': InvenTree.version.inventreeApiVersion(),
            'worker_running': is_worker_running(),
            'worker_pending_tasks': self.worker_pending_tasks(),
            'plugins_enabled': settings.PLUGINS_ENABLED,
            'active_plugins': plugins_info(),
            'email_configured': is_email_configured(),
            'debug_mode': settings.DEBUG,
            'docker_mode': settings.DOCKER,
            'system_health': check_system_health() if is_staff else None,
            'database': InvenTree.version.inventreeDatabase()if is_staff else None,
            'platform': InvenTree.version.inventreePlatform() if is_staff else None,
            'installer': InvenTree.version.inventreeInstaller() if is_staff else None,
            'target': InvenTree.version.inventreeTarget()if is_staff else None,
        }

        return JsonResponse(data)

    def check_auth_header(self, request):
        """Check if user is authenticated via a token in the header."""
        # TODO @matmair: remove after refacgtor of Token check is done
        headers = request.headers.get('Authorization', request.headers.get('authorization'))
        if not headers:
            return False

        auth = headers.strip()
        if not (auth.lower().startswith('token') and len(auth.split()) == 2):
            return False

        token_key = auth.split()[1]
        try:
            token = ApiToken.objects.get(key=token_key)
            if token.active and token.user and token.user.is_staff:
                return True
        except ApiToken.DoesNotExist:
            pass
        return False


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

    search_fields = [
        'attachment',
        'comment',
        'link',
    ]

    def perform_create(self, serializer):
        """Save the user information when a file is uploaded."""
        attachment = serializer.save()
        attachment.user = self.request.user
        attachment.save()


class APISearchView(GenericAPIView):
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

        if 'search' not in data:
            raise ValidationError({
                'search': 'Search term must be provided',
            })

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
