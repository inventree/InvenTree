"""Main JSON interface views."""

import json
import sys
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

import structlog
from django_q.models import OrmQ
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

import InvenTree.version
import users.models
from InvenTree.mixins import ListCreateAPI
from InvenTree.templatetags.inventree_extras import plugins_info
from part.models import Part
from plugin.serializers import MetadataSerializer
from users.models import ApiToken

from .helpers_email import is_email_configured
from .mixins import ListAPI, RetrieveUpdateAPI
from .status import check_system_health, is_worker_running
from .version import inventreeApiText

logger = structlog.get_logger('inventree')


class LicenseViewSerializer(serializers.Serializer):
    """Serializer for license information."""

    backend = serializers.CharField(help_text='Backend licenses texts', read_only=True)
    frontend = serializers.CharField(
        help_text='Frontend licenses texts', read_only=True
    )


class LicenseView(APIView):
    """Simple JSON endpoint for InvenTree license information."""

    permission_classes = [permissions.IsAuthenticated]

    def read_license_file(self, path: Path) -> list:
        """Extract license information from the provided file.

        Arguments:
            path: Path to the license file

        Returns: A list of items containing the license information
        """
        # Check if the file exists
        if not path.exists():
            logger.error("License file not found at '%s'", path)
            return []

        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse license file '%s': %s", path, e)
            return []
        except Exception as e:
            logger.exception("Exception while reading license file '%s': %s", path, e)
            return []

        output = []
        names = set()

        # Ensure we do not have any duplicate 'name' values in the list
        for entry in data:
            name = None
            for key in entry:
                if key.lower() == 'name':
                    name = entry[key]
                    break

            if name is None or name in names:
                continue

            names.add(name)
            output.append({key.lower(): value for key, value in entry.items()})

        return output

    @extend_schema(responses={200: OpenApiResponse(response=LicenseViewSerializer)})
    def get(self, request, *args, **kwargs):
        """Return information about the InvenTree server."""
        backend = Path(__file__).parent.joinpath('licenses.txt')
        frontend = Path(__file__).parent.parent.joinpath(
            'web/static/web/.vite/dependencies.json'
        )
        return JsonResponse({
            'backend': self.read_license_file(backend),
            'frontend': self.read_license_file(frontend),
        })


class VersionViewSerializer(serializers.Serializer):
    """Serializer for a single version."""

    class VersionSerializer(serializers.Serializer):
        """Serializer for server version."""

        server = serializers.CharField()
        api = serializers.IntegerField()
        commit_hash = serializers.CharField()
        commit_date = serializers.CharField()
        commit_branch = serializers.CharField()
        python = serializers.CharField()
        django = serializers.CharField()

    class LinkSerializer(serializers.Serializer):
        """Serializer for all possible links."""

        doc = serializers.URLField()
        code = serializers.URLField()
        credit = serializers.URLField()
        app = serializers.URLField()
        bug = serializers.URLField()

    dev = serializers.BooleanField()
    up_to_date = serializers.BooleanField()
    version = VersionSerializer()
    links = LinkSerializer()


class VersionView(APIView):
    """Simple JSON endpoint for InvenTree version information."""

    permission_classes = [permissions.IsAdminUser]

    @extend_schema(responses={200: OpenApiResponse(response=VersionViewSerializer)})
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
                'django': InvenTree.version.inventreeDjangoVersion(),
            },
            'links': {
                'doc': InvenTree.version.inventreeDocUrl(),
                'code': InvenTree.version.inventreeGithubUrl(),
                'credit': InvenTree.version.inventreeCreditsUrl(),
                'app': InvenTree.version.inventreeAppUrl(),
                'bug': f'{InvenTree.version.inventreeGithubUrl()}issues',
            },
        })


class VersionInformationSerializer(serializers.Serializer):
    """Serializer for a single version."""

    version = serializers.CharField()
    date = serializers.CharField()
    gh = serializers.CharField()
    text = serializers.CharField()
    latest = serializers.BooleanField()

    class Meta:
        """Meta class for VersionInformationSerializer."""

        fields = '__all__'


class VersionApiSerializer(serializers.Serializer):
    """Serializer for the version api endpoint."""

    VersionInformationSerializer(many=True)


class VersionTextView(ListAPI):
    """Simple JSON endpoint for InvenTree version text."""

    serializer_class = VersionInformationSerializer

    permission_classes = [permissions.IsAdminUser]

    @extend_schema(responses={200: OpenApiResponse(response=VersionApiSerializer)})
    def list(self, request, *args, **kwargs):
        """Return information about the InvenTree server."""
        return JsonResponse(inventreeApiText())


class InfoApiSerializer(serializers.Serializer):
    """InvenTree server information - some information might be blanked if called without elevated credentials."""

    server = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    instance = serializers.CharField(read_only=True)
    apiVersion = serializers.IntegerField(read_only=True)  # noqa: N815
    worker_running = serializers.BooleanField(read_only=True)
    worker_count = serializers.IntegerField(read_only=True)
    worker_pending_tasks = serializers.IntegerField(read_only=True)
    plugins_enabled = serializers.BooleanField(read_only=True)
    plugins_install_disabled = serializers.BooleanField(read_only=True)
    active_plugins = serializers.JSONField(read_only=True)
    email_configured = serializers.BooleanField(read_only=True)
    debug_mode = serializers.BooleanField(read_only=True)
    docker_mode = serializers.BooleanField(read_only=True)
    default_locale = serializers.ChoiceField(
        choices=settings.LOCALE_CODES, read_only=True
    )
    system_health = serializers.BooleanField(read_only=True)
    database = serializers.CharField(read_only=True)
    platform = serializers.CharField(read_only=True)
    installer = serializers.CharField(read_only=True)
    target = serializers.CharField(read_only=True)
    django_admin = serializers.CharField(read_only=True)


class InfoView(APIView):
    """JSON endpoint for InvenTree server information.

    Use to confirm that the server is running, etc.
    """

    permission_classes = [permissions.AllowAny]

    def worker_pending_tasks(self):
        """Return the current number of outstanding background tasks."""
        return OrmQ.objects.count()

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=InfoApiSerializer, description='InvenTree server information'
            )
        }
    )
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
            'worker_count': settings.BACKGROUND_WORKER_COUNT,
            'worker_pending_tasks': self.worker_pending_tasks(),
            'plugins_enabled': settings.PLUGINS_ENABLED,
            'plugins_install_disabled': settings.PLUGINS_INSTALL_DISABLED,
            'active_plugins': plugins_info(),
            'email_configured': is_email_configured(),
            'debug_mode': settings.DEBUG,
            'docker_mode': settings.DOCKER,
            'default_locale': settings.LANGUAGE_CODE,
            # Following fields are only available to staff users
            'system_health': check_system_health() if is_staff else None,
            'database': InvenTree.version.inventreeDatabase() if is_staff else None,
            'platform': InvenTree.version.inventreePlatform() if is_staff else None,
            'installer': InvenTree.version.inventreeInstaller() if is_staff else None,
            'target': InvenTree.version.inventreeTarget() if is_staff else None,
            'django_admin': settings.INVENTREE_ADMIN_URL
            if (is_staff and settings.INVENTREE_ADMIN_ENABLED)
            else None,
        }

        return JsonResponse(data)

    def check_auth_header(self, request):
        """Check if user is authenticated via a token in the header."""
        from InvenTree.middleware import get_token_from_request

        if token := get_token_from_request(request):
            # Does the provided token match a valid user?
            try:
                token = ApiToken.objects.get(key=token)

                # Check if the token is active and the user is a staff member
                if token.active and token.user and token.user.is_staff:
                    return True
            except ApiToken.DoesNotExist:
                pass

        return False


class NotFoundView(APIView):
    """Simple JSON view when accessing an invalid API view."""

    permission_classes = [permissions.AllowAny]

    def not_found(self, request):
        """Return a 404 error."""
        return JsonResponse(
            {
                'detail': _('API endpoint not found'),
                'url': request.build_absolute_uri(),
            },
            status=404,
        )

    def options(self, request, *args, **kwargs):
        """Return 404."""
        return self.not_found(request)

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        """Return 404."""
        return self.not_found(request)

    @extend_schema(exclude=True)
    def post(self, request, *args, **kwargs):
        """Return 404."""
        return self.not_found(request)

    @extend_schema(exclude=True)
    def patch(self, request, *args, **kwargs):
        """Return 404."""
        return self.not_found(request)

    @extend_schema(exclude=True)
    def put(self, request, *args, **kwargs):
        """Return 404."""
        return self.not_found(request)

    @extend_schema(exclude=True)
    def delete(self, request, *args, **kwargs):
        """Return 404."""
        return self.not_found(request)


class BulkDeleteMixin:
    """Mixin class for enabling 'bulk delete' operations for various models.

    Bulk delete allows for multiple items to be deleted in a single API query,
    rather than using multiple API calls to the various detail endpoints.

    This is implemented for two major reasons:
    - Atomicity (guaranteed that either *all* items are deleted, or *none*)
    - Speed (single API call and DB query)
    """

    def validate_delete(self, queryset, request) -> None:
        """Perform validation right before deletion.

        Arguments:
            queryset: The queryset to be deleted
            request: The request object

        Returns:
            None

        Raises:
            ValidationError: If the deletion should not proceed
        """

    def filter_delete_queryset(self, queryset, request):
        """Provide custom filtering for the queryset *before* it is deleted.

        The default implementation does nothing, just returns the queryset.
        """
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
                'non_field_errors': [
                    'List of items or filters must be provided for bulk deletion'
                ]
            })

        if items and type(items) is not list:
            raise ValidationError({
                'items': ["'items' must be supplied as a list object"]
            })

        if filters and type(filters) is not dict:
            raise ValidationError({
                'filters': ["'filters' must be supplied as a dict object"]
            })

        # Keep track of how many items we deleted
        n_deleted = 0

        with transaction.atomic():
            # Start with *all* models and perform basic filtering
            queryset = model.objects.all()
            queryset = self.filter_delete_queryset(queryset, request)

            # Filter by provided item ID values
            if items:
                try:
                    queryset = queryset.filter(id__in=items)
                except Exception:
                    raise ValidationError({
                        'non_field_errors': _('Invalid items list provided')
                    })

            # Filter by provided filters
            if filters:
                try:
                    queryset = queryset.filter(**filters)
                except Exception:
                    raise ValidationError({
                        'non_field_errors': _('Invalid filters provided')
                    })

            if queryset.count() == 0:
                raise ValidationError({
                    'non_field_errors': _('No items found to delete')
                })

            # Run a final validation step (should raise an error if the deletion should not proceed)
            self.validate_delete(queryset, request)

            n_deleted = queryset.count()
            queryset.delete()

        return Response({'success': f'Deleted {n_deleted} items'}, status=204)


class ListCreateDestroyAPIView(BulkDeleteMixin, ListCreateAPI):
    """Custom API endpoint which provides BulkDelete functionality in addition to List and Create."""


class APISearchViewSerializer(serializers.Serializer):
    """Serializer for the APISearchView."""

    search = serializers.CharField()
    search_regex = serializers.BooleanField(default=False, required=False)
    search_whole = serializers.BooleanField(default=False, required=False)
    limit = serializers.IntegerField(default=1, required=False)
    offset = serializers.IntegerField(default=0, required=False)


class APISearchView(GenericAPIView):
    """A general-purpose 'search' API endpoint.

    Returns hits against a number of different models simultaneously,
    to consolidate multiple API requests into a single query.

    Is much more efficient and simplifies code!
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = APISearchViewSerializer

    def get_result_types(self):
        """Construct a list of search types we can return."""
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
        """Perform search query against available models."""
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
            raise ValidationError({'search': 'Search term must be provided'})

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
                    if users.models.RuleSet.check_table_permission(
                        request.user, table, 'view'
                    ):
                        results[key] = view.list(request, *args, **kwargs).data
                    else:
                        results[key] = {
                            'error': _(
                                'User does not have permission to view this model'
                            )
                        }
                except Exception as exc:
                    results[key] = {'error': str(exc)}

        return Response(results)


class MetadataView(RetrieveUpdateAPI):
    """Generic API endpoint for reading and editing metadata for a model."""

    MODEL_REF = 'model'

    def get_model_type(self):
        """Return the model type associated with this API instance."""
        model = self.kwargs.get(self.MODEL_REF, None)

        if 'lookup_field' in self.kwargs:
            # Set custom lookup field (instead of default 'pk' value) if supplied
            self.lookup_field = self.kwargs.pop('lookup_field')

        if model is None:
            raise ValidationError(
                f"MetadataView called without '{self.MODEL_REF}' parameter"
            )

        return model

    def get_permission_model(self):
        """Return the 'permission' model associated with this view."""
        return self.get_model_type()

    def get_queryset(self):
        """Return the queryset for this endpoint."""
        return self.get_model_type().objects.all()

    def get_serializer(self, *args, **kwargs):
        """Return MetadataSerializer instance."""
        # Detect if we are currently generating the OpenAPI schema
        if 'spectacular' in sys.argv:
            return MetadataSerializer(Part, *args, **kwargs)
        return MetadataSerializer(self.get_model_type(), *args, **kwargs)
