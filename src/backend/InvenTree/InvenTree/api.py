"""Main JSON interface views."""

import collections
import json
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

import structlog
from django_q.models import OrmQ
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

import InvenTree.config
import InvenTree.permissions
import InvenTree.version
from common.settings import get_global_setting
from InvenTree import helpers
from InvenTree.auth_overrides import registration_enabled
from InvenTree.mixins import ListCreateAPI
from InvenTree.sso import sso_registration_enabled
from plugin.serializers import MetadataSerializer
from users.models import ApiToken
from users.permissions import check_user_permission

from .helpers import plugins_info
from .helpers_email import is_email_configured
from .mixins import ListAPI, RetrieveUpdateAPI
from .status import check_system_health, is_worker_running
from .version import inventreeApiText

logger = structlog.get_logger('inventree')


def read_license_file(path: Path) -> list:
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
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        logger.exception("Failed to parse license file '%s': %s", path, e)
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

    return sorted(output, key=lambda x: x.get('name', '').lower())


class LicenseViewSerializer(serializers.Serializer):
    """Serializer for license information."""

    backend = serializers.ListField(help_text='Backend licenses texts', read_only=True)
    frontend = serializers.ListField(
        help_text='Frontend licenses texts', read_only=True
    )


class LicenseView(APIView):
    """Simple JSON endpoint for InvenTree license information."""

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]

    @extend_schema(responses={200: OpenApiResponse(response=LicenseViewSerializer)})
    def get(self, request, *args, **kwargs):
        """Return information about the InvenTree server."""
        backend = InvenTree.config.get_base_dir().joinpath('InvenTree', 'licenses.txt')
        frontend = InvenTree.config.get_base_dir().joinpath(
            'web/static/web/.vite/dependencies.json'
        )
        return JsonResponse({
            'backend': read_license_file(backend),
            'frontend': read_license_file(frontend),
        })


class VersionViewSerializer(serializers.Serializer):
    """Serializer for a single version."""

    class VersionSerializer(serializers.Serializer):
        """Serializer for server version."""

        server = serializers.CharField()
        api = serializers.IntegerField()
        commit_hash = serializers.CharField()
        commit_date = serializers.CharField()
        commit_branch = serializers.CharField(allow_null=True)
        python = serializers.CharField()
        django = serializers.CharField()

    class LinkSerializer(serializers.Serializer):
        """Serializer for all possible links."""

        doc = serializers.URLField()
        code = serializers.URLField()
        app = serializers.URLField()
        bug = serializers.URLField()

    dev = serializers.BooleanField()
    up_to_date = serializers.BooleanField()
    version = VersionSerializer()
    links = LinkSerializer()


class VersionView(APIView):
    """Simple JSON endpoint for InvenTree version information."""

    permission_classes = [InvenTree.permissions.IsAdminOrAdminScope]

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
                'app': InvenTree.version.inventreeAppUrl(),
                'bug': f'{InvenTree.version.inventreeGithubUrl()}issues',
            },
        })


class VersionInformationSerializer(serializers.Serializer):
    """Serializer for a single version."""

    version = serializers.CharField()
    date = serializers.DateField()
    gh = serializers.CharField(allow_null=True)
    text = serializers.ListField(child=serializers.CharField())
    latest = serializers.BooleanField()

    class Meta:
        """Meta class for VersionInformationSerializer."""

        fields = '__all__'


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='versions',
            type=int,
            description='Number of versions to return.',
            default=10,
        ),
        OpenApiParameter(
            name='start_version',
            type=int,
            description='First version to report. Defaults to return the latest {versions} versions.',
        ),
    ]
)
class VersionTextView(ListAPI):
    """Simple JSON endpoint for InvenTree version text."""

    serializer_class = VersionInformationSerializer

    permission_classes = [InvenTree.permissions.IsAdminOrAdminScope]

    # Specifically disable pagination for this view
    pagination_class = None

    def list(self, request, *args, **kwargs):
        """Return information about the InvenTree server."""
        versions = request.query_params.get('versions')
        start_version = request.query_params.get('start_version')

        api_kwargs = {}
        if versions is not None:
            api_kwargs['versions'] = int(versions)
        if start_version is not None:
            api_kwargs['start_version'] = int(start_version)

        version_data = inventreeApiText(**api_kwargs)
        return JsonResponse(list(version_data.values()), safe=False)


class InfoApiSerializer(serializers.Serializer):
    """InvenTree server information - some information might be blanked if called without elevated credentials."""

    class SettingsSerializer(serializers.Serializer):
        """Serializer for InfoApiSerializer."""

        sso_registration = serializers.BooleanField()
        registration_enabled = serializers.BooleanField()
        password_forgotten_enabled = serializers.BooleanField()

    class CustomizeSerializer(serializers.Serializer):
        """Serializer for customize field."""

        logo = serializers.CharField()
        splash = serializers.CharField()
        login_message = serializers.CharField(allow_null=True)
        navbar_message = serializers.CharField(allow_null=True)

    server = serializers.CharField(read_only=True)
    id = serializers.CharField(read_only=True, allow_null=True)
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
    default_locale = serializers.CharField(read_only=True)
    customize = CustomizeSerializer(read_only=True)
    system_health = serializers.BooleanField(read_only=True)
    database = serializers.CharField(read_only=True)
    platform = serializers.CharField(read_only=True)
    installer = serializers.CharField(read_only=True)
    target = serializers.CharField(read_only=True, allow_null=True)
    django_admin = serializers.CharField(read_only=True)
    settings = SettingsSerializer(read_only=True, many=False)


class InfoView(APIView):
    """JSON endpoint for InvenTree server information.

    Use to confirm that the server is running, etc.
    """

    permission_classes = [InvenTree.permissions.AllowAnyOrReadScope]

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
            'id': InvenTree.version.inventree_identifier(),
            'version': InvenTree.version.inventreeVersion(),
            'instance': InvenTree.version.inventreeInstanceName(),
            'apiVersion': InvenTree.version.inventreeApiVersion(),
            'worker_running': is_worker_running(),
            'worker_count': settings.BACKGROUND_WORKER_COUNT,
            'worker_pending_tasks': self.worker_pending_tasks(),
            'plugins_enabled': settings.PLUGINS_ENABLED,
            'plugins_install_disabled': settings.PLUGINS_INSTALL_DISABLED,
            'email_configured': is_email_configured(),
            'debug_mode': settings.DEBUG,
            'docker_mode': settings.DOCKER,
            'default_locale': settings.LANGUAGE_CODE,
            'customize': {
                'logo': helpers.getLogoImage(),
                'splash': helpers.getSplashScreen(),
                'login_message': helpers.getCustomOption('login_message'),
                'navbar_message': helpers.getCustomOption('navbar_message'),
            },
            'active_plugins': plugins_info(),
            # Following fields are only available to staff users
            'system_health': check_system_health() if is_staff else None,
            'database': InvenTree.version.inventreeDatabase() if is_staff else None,
            'platform': InvenTree.version.inventreePlatform() if is_staff else None,
            'installer': InvenTree.config.inventreeInstaller() if is_staff else None,
            'target': InvenTree.version.inventreeTarget() if is_staff else None,
            'django_admin': settings.INVENTREE_ADMIN_URL
            if (is_staff and settings.INVENTREE_ADMIN_ENABLED)
            else None,
            'settings': {
                'sso_registration': sso_registration_enabled(),
                'registration_enabled': registration_enabled(),
                'password_forgotten_enabled': get_global_setting(
                    'LOGIN_ENABLE_PWD_FORGOT'
                ),
            },
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

    permission_classes = [InvenTree.permissions.AllowAnyOrReadScope]

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


class BulkRequestSerializer(serializers.Serializer):
    """Parameters for selecting items for bulk operations."""

    items = serializers.ListField(
        label='A list of primary key values',
        child=serializers.IntegerField(),
        required=False,
    )

    filters = serializers.DictField(
        label='A dictionary of filter values', required=False
    )


class BulkOperationMixin:
    """Mixin class for handling bulk data operations.

    Bulk operations are implemented for two major reasons:
    - Speed (single API call vs multiple API calls)
    - Atomicity (guaranteed that either *all* items are updated, or *none*)
    """

    def get_bulk_queryset(self, request):
        """Return a queryset based on the selection made in the request.

        Selection can be made by providing either:

        - items: A list of primary key values
        - filters: A dictionary of filter values
        """
        model = self.serializer_class.Meta.model

        items = request.data.pop('items', None)
        filters = request.data.pop('filters', None)
        all_filter = request.GET.get('all', None)

        queryset = model.objects.all()

        if not items and not filters and all_filter is None:
            raise ValidationError({
                'non_field_errors': _(
                    'List of items or filters must be provided for bulk operation'
                )
            })

        if items:
            if type(items) is not list:
                raise ValidationError({
                    'non_field_errors': _('Items must be provided as a list')
                })

            # Filter by primary key
            try:
                queryset = queryset.filter(pk__in=items)
            except Exception:
                raise ValidationError({
                    'non_field_errors': _('Invalid items list provided')
                })

        if filters:
            if type(filters) is not dict:
                raise ValidationError({
                    'non_field_errors': _('Filters must be provided as a dict')
                })

            try:
                queryset = queryset.filter(**filters)
            except Exception:
                raise ValidationError({
                    'non_field_errors': _('Invalid filters provided')
                })

        if all_filter and not helpers.str2bool(all_filter):
            raise ValidationError({
                'non_field_errors': _('All filter must only be used with true')
            })

        if queryset.count() == 0:
            raise ValidationError({
                'non_field_errors': _('No items match the provided criteria')
            })

        return queryset


class BulkCreateMixin:
    """Mixin class for enabling 'bulk create' operations for various models.

    Bulk create allows for multiple items to be created in a single API query,
    rather than using multiple API calls to same endpoint.
    """

    def create(self, request, *args, **kwargs):
        """Perform a POST operation against this list endpoint."""
        data = request.data

        if isinstance(data, list):
            created_items = []
            errors = []
            has_errors = False

            # If data is a list, we assume it is a bulk create request
            if len(data) == 0:
                raise ValidationError({'non_field_errors': _('No data provided')})

            # validate unique together fields
            if unique_create_fields := getattr(self, 'unique_create_fields', None):
                existing = collections.defaultdict(list)
                for idx, item in enumerate(data):
                    key = tuple(item[v] for v in unique_create_fields)
                    existing[key].append(idx)

                unique_errors = [[] for _ in range(len(data))]
                has_unique_errors = False
                for item in existing.values():
                    if len(item) > 1:
                        has_unique_errors = True
                        error = {}
                        for field_name in unique_create_fields:
                            error[field_name] = [_('This field must be unique.')]
                        for idx in item:
                            unique_errors[idx] = error
                if has_unique_errors:
                    raise ValidationError(unique_errors)

            with transaction.atomic():
                for item in data:
                    serializer = self.get_serializer(data=item)
                    if serializer.is_valid():
                        self.perform_create(serializer)
                        created_items.append(serializer.data)
                        errors.append([])
                    else:
                        errors.append(serializer.errors)
                        has_errors = True

                if has_errors:
                    raise ValidationError(errors)

            return Response(created_items, status=201)

        return super().create(request, *args, **kwargs)


class BulkUpdateMixin(BulkOperationMixin):
    """Mixin class for enabling 'bulk update' operations for various models.

    Bulk update allows for multiple items to be updated in a single API query,
    rather than using multiple API calls to the various detail endpoints.
    """

    def validate_update(self, queryset, request) -> None:
        """Perform validation right before updating.

        Arguments:
            queryset: The queryset to be updated
            request: The request object

        Returns:
            None

        Raises:
            ValidationError: If the update should not proceed
        """
        # Default implementation does nothing

    def filter_update_queryset(self, queryset, request):
        """Provide custom filtering for the queryset *before* it is updated.

        The default implementation does nothing, just returns the queryset.
        """
        return queryset

    def put(self, request, *args, **kwargs):
        """Perform a PUT operation against this list endpoint.

        Simply redirects to the PATCH method.
        """
        return self.patch(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """Perform a PATCH operation against this list endpoint.

        Note that the typical DRF list endpoint does not support PATCH,
        so this method is provided as a custom implementation.
        """
        queryset = self.get_bulk_queryset(request)
        queryset = self.filter_update_queryset(queryset, request)

        self.validate_update(queryset, request)

        # Perform the update operation
        data = request.data

        n = queryset.count()

        with transaction.atomic():
            # Perform object update
            # Note that we do not perform a bulk-update operation here,
            # as we want to trigger any custom post_save methods on the model
            for instance in queryset:
                serializer = self.get_serializer(instance, data=data, partial=True)

                serializer.is_valid(raise_exception=True)
                serializer.save()

        return Response({'success': f'Updated {n} items'}, status=200)


class ParameterListMixin:
    """Mixin class which supports filtering against parametric fields."""

    def filter_queryset(self, queryset):
        """Perform filtering against parametric fields."""
        import common.filters

        queryset = super().filter_queryset(queryset)

        # Filter by parametric data
        queryset = common.filters.filter_parametric_data(
            queryset, self.request.query_params
        )

        serializer_class = (
            getattr(self, 'serializer_class', None) or self.get_serializer_class()
        )

        model_class = serializer_class.Meta.model

        # Apply ordering based on query parameter
        queryset = common.filters.order_by_parameter(
            queryset, model_class, self.request.query_params.get('ordering', None)
        )

        return queryset


class BulkDeleteMixin(BulkOperationMixin):
    """Mixin class for enabling 'bulk delete' operations for various models.

    Bulk delete allows for multiple items to be deleted in a single API query,
    rather than using multiple API calls to the various detail endpoints.
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
        # Default implementation does nothing

    def filter_delete_queryset(self, queryset, request):
        """Provide custom filtering for the queryset *before* it is deleted.

        The default implementation does nothing, just returns the queryset.
        """
        return queryset

    @extend_schema(request=BulkRequestSerializer)
    def delete(self, request, *args, **kwargs):
        """Perform a DELETE operation against this list endpoint.

        Note that the typical DRF list endpoint does not support DELETE,
        so this method is provided as a custom implementation.
        """
        queryset = self.get_bulk_queryset(request)
        queryset = self.filter_delete_queryset(queryset, request)

        self.validate_delete(queryset, request)

        # Keep track of how many items we deleted
        n_deleted = queryset.count()

        with transaction.atomic():
            # Perform object deletion
            # Note that we do not perform a bulk-delete operation here,
            # as we want to trigger any custom post_delete methods on the model
            for item in queryset:
                item.delete()

        return Response({'success': f'Deleted {n_deleted} items'}, status=200)


class ListCreateDestroyAPIView(BulkDeleteMixin, ListCreateAPI):
    """Custom API endpoint which provides BulkDelete functionality in addition to List and Create."""


class APISearchViewSerializer(serializers.Serializer):
    """Serializer for the APISearchView."""

    search = serializers.CharField()
    search_regex = serializers.BooleanField(default=False, required=False)
    search_whole = serializers.BooleanField(default=False, required=False)
    search_notes = serializers.BooleanField(default=False, required=False)
    limit = serializers.IntegerField(default=1, required=False)
    offset = serializers.IntegerField(default=0, required=False)


class APISearchView(GenericAPIView):
    """A general-purpose 'search' API endpoint.

    Returns hits against a number of different models simultaneously,
    to consolidate multiple API requests into a single query.

    Is much more efficient and simplifies code!
    """

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
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
            'supplier': company.api.CompanyList,
            'manufacturer': company.api.CompanyList,
            'customer': company.api.CompanyList,
            'manufacturerpart': company.api.ManufacturerPartList,
            'supplierpart': company.api.SupplierPartList,
            'part': part.api.PartList,
            'partcategory': part.api.CategoryList,
            'purchaseorder': order.api.PurchaseOrderList,
            'returnorder': order.api.ReturnOrderList,
            'salesorder': order.api.SalesOrderList,
            'salesordershipment': order.api.SalesOrderShipmentList,
            'stockitem': stock.api.StockList,
            'stocklocation': stock.api.StockLocationList,
        }

    def get_result_filters(self):
        """Provide extra filtering options for particular search groups."""
        return {
            'supplier': {'is_supplier': True},
            'manufacturer': {'is_manufacturer': True},
            'customer': {'is_customer': True},
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
            'search_notes': False,
            'limit': 1,
            'offset': 0,
        }

        if 'search' not in data:
            raise ValidationError({'search': 'Search term must be provided'})

        search_filters = self.get_result_filters()

        for key, cls in self.get_result_types().items():
            # Only return results which are specifically requested
            if key in data:
                params = data[key]

                for k, v in pass_through_params.items():
                    params[k] = request.data.get(k, v)

                # Add in any extra filters for this particular search type
                if key in search_filters:
                    for k, v in search_filters[key].items():
                        params[k] = v

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

                try:
                    if check_user_permission(request.user, model, 'view'):
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

    model = None  # Placeholder for the model class

    @classmethod
    def as_view(cls, model, lookup_field=None, **initkwargs):
        """Override to ensure model specific rendering."""
        if model is None:
            raise ValidationError(
                "MetadataView defined without 'model' arg"
            )  # pragma: no cover
        initkwargs['model'] = model

        # Set custom lookup field (instead of default 'pk' value) if supplied
        if lookup_field:
            initkwargs['lookup_field'] = lookup_field

        return super().as_view(**initkwargs)

    def get_permission_model(self):
        """Return the 'permission' model associated with this view."""
        return self.model

    def get_queryset(self):
        """Return the queryset for this endpoint."""
        return self.model.objects.all()

    def get_serializer(self, *args, **kwargs):
        """Return MetadataSerializer instance."""
        # Detect if we are currently generating the OpenAPI schema
        return MetadataSerializer(self.model, *args, **kwargs)
