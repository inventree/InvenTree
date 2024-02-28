"""API for the plugin app."""

from django.core.exceptions import ValidationError
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

import plugin.serializers as PluginSerializers
from common.api import GlobalSettingsPermissions
from InvenTree.api import MetadataView
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (
    CreateAPI,
    ListAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
    UpdateAPI,
)
from InvenTree.permissions import IsSuperuser
from plugin import registry
from plugin.base.action.api import ActionPluginView
from plugin.base.barcodes.api import barcode_api_urls
from plugin.base.locate.api import LocatePluginView
from plugin.models import PluginConfig, PluginSetting
from plugin.plugin import InvenTreePlugin


class PluginFilter(rest_filters.FilterSet):
    """Filter for the PluginConfig model.

    Provides custom filtering options for the FilterList API endpoint.
    """

    class Meta:
        """Meta for the filter."""

        model = PluginConfig
        fields = ['active']

    mixin = rest_filters.CharFilter(
        field_name='mixin', method='filter_mixin', label='Mixin'
    )

    def filter_mixin(self, queryset, name, value):
        """Filter by implement mixin.

        - A comma-separated list of mixin names can be provided.
        - Only plugins which implement all of the provided mixins will be returned.
        """
        matches = []
        mixins = [x.strip().lower() for x in value.split(',') if x]

        for result in queryset:
            match = True

            for mixin in mixins:
                if mixin not in result.mixins().keys():
                    match = False
                    break

            if match:
                matches.append(result.pk)

        return queryset.filter(pk__in=matches)

    builtin = rest_filters.BooleanFilter(
        field_name='builtin', label='Builtin', method='filter_builtin'
    )

    def filter_builtin(self, queryset, name, value):
        """Filter by 'builtin' flag."""
        matches = []

        for result in queryset:
            if result.is_builtin() == value:
                matches.append(result.pk)

        return queryset.filter(pk__in=matches)

    sample = rest_filters.BooleanFilter(
        field_name='sample', label='Sample', method='filter_sample'
    )

    def filter_sample(self, queryset, name, value):
        """Filter by 'sample' flag."""
        matches = []

        for result in queryset:
            if result.is_sample() == value:
                matches.append(result.pk)

        return queryset.filter(pk__in=matches)

    installed = rest_filters.BooleanFilter(
        field_name='installed', label='Installed', method='filter_installed'
    )

    def filter_installed(self, queryset, name, value):
        """Filter by 'installed' flag."""
        matches = []

        for result in queryset:
            if result.is_installed() == value:
                matches.append(result.pk)

        return queryset.filter(pk__in=matches)


class PluginList(ListAPI):
    """API endpoint for list of PluginConfig objects.

    - GET: Return a list of all PluginConfig objects
    """

    # Allow any logged in user to read this endpoint
    # This is necessary to allow certain functionality,
    # e.g. determining which label printing plugins are available
    permission_classes = [permissions.IsAuthenticated]

    filterset_class = PluginFilter

    serializer_class = PluginSerializers.PluginConfigSerializer
    queryset = PluginConfig.objects.all()

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['active']

    ordering_fields = ['key', 'name', 'active']

    ordering = ['-active', 'name', 'key']

    search_fields = ['key', 'name']


class PluginDetail(RetrieveUpdateDestroyAPI):
    """API detail endpoint for PluginConfig object.

    get:
    Return a single PluginConfig object

    post:
    Update a PluginConfig

    delete:
    Remove a PluginConfig
    """

    queryset = PluginConfig.objects.all()
    serializer_class = PluginSerializers.PluginConfigSerializer

    def delete(self, request, *args, **kwargs):
        """Handle DELETE request for a PluginConfig instance.

        We only allow plugin deletion if the plugin is not active.
        """
        cfg = self.get_object()

        if cfg.active:
            raise ValidationError({
                'detail': _('Plugin cannot be deleted as it is currently active')
            })

        return super().delete(request, *args, **kwargs)


class PluginInstall(CreateAPI):
    """Endpoint for installing a new plugin."""

    queryset = PluginConfig.objects.none()
    serializer_class = PluginSerializers.PluginConfigInstallSerializer

    def create(self, request, *args, **kwargs):
        """Install a plugin via the API."""
        # Clean up input data
        data = self.clean_data(request.data)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        result = self.perform_create(serializer)
        result['input'] = serializer.data
        headers = self.get_success_headers(serializer.data)
        return Response(result, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Saving the serializer instance performs plugin installation."""
        return serializer.save()


class PluginUninstall(UpdateAPI):
    """Endpoint for uninstalling a single plugin."""

    queryset = PluginConfig.objects.all()
    serializer_class = PluginSerializers.PluginUninstallSerializer
    permission_classes = [IsSuperuser]

    def perform_update(self, serializer):
        """Uninstall the plugin."""
        serializer.save()


class PluginActivate(UpdateAPI):
    """Endpoint for activating a plugin.

    - PATCH: Activate a plugin

    Pass a boolean value for the 'active' field.
    If not provided, it is assumed to be True,
    and the plugin will be activated.
    """

    queryset = PluginConfig.objects.all()
    serializer_class = PluginSerializers.PluginActivateSerializer
    permission_classes = [IsSuperuser]

    def get_object(self):
        """Returns the object for the view."""
        if self.request.data.get('pk', None):
            return self.queryset.get(pk=self.request.data.get('pk'))
        return super().get_object()

    def perform_update(self, serializer):
        """Activate the plugin."""
        serializer.save()


class PluginReload(CreateAPI):
    """Endpoint for reloading all plugins."""

    queryset = PluginConfig.objects.none()
    serializer_class = PluginSerializers.PluginReloadSerializer
    permission_classes = [IsSuperuser]

    def perform_create(self, serializer):
        """Saving the serializer instance performs plugin installation."""
        return serializer.save()


class PluginSettingList(ListAPI):
    """List endpoint for all plugin related settings.

    - read only
    - only accessible by staff users
    """

    queryset = PluginSetting.objects.all()
    serializer_class = PluginSerializers.PluginSettingSerializer

    permission_classes = [GlobalSettingsPermissions]

    filter_backends = [DjangoFilterBackend]

    filterset_fields = ['plugin__active', 'plugin__key']


def check_plugin(plugin_slug: str, plugin_pk: int) -> InvenTreePlugin:
    """Check that a plugin for the provided slug exists and get the config.

    Args:
        plugin_slug (str): Slug for plugin.
        plugin_pk (int): Primary key for plugin.

    Raises:
        NotFound: If plugin is not installed
        NotFound: If plugin is not correctly registered
        NotFound: If plugin is not active

    Returns:
        InvenTreePlugin: The config object for the provided plugin.
    """
    # Make sure that a plugin reference is specified
    if plugin_slug is None and plugin_pk is None:
        raise NotFound(detail='Plugin not specified')

    # Define filter
    filter = {}
    if plugin_slug:
        filter['key'] = plugin_slug
    elif plugin_pk:
        filter['pk'] = plugin_pk
    ref = plugin_slug or plugin_pk

    # Check that the 'plugin' specified is valid
    try:
        plugin_cgf = PluginConfig.objects.filter(**filter).first()
    except PluginConfig.DoesNotExist:
        raise NotFound(detail=f"Plugin '{ref}' not installed")

    if plugin_cgf is None:
        # This only occurs if the plugin mechanism broke
        raise NotFound(detail=f"Plugin '{ref}' not installed")  # pragma: no cover

    # Check that the plugin is activated
    if not plugin_cgf.active:
        raise NotFound(detail=f"Plugin '{ref}' is not active")

    plugin = plugin_cgf.plugin

    if not plugin:
        raise NotFound(detail=f"Plugin '{ref}' not installed")

    return plugin


class PluginAllSettingList(APIView):
    """List endpoint for all plugin settings for a specific plugin.

    - GET: return all settings for a plugin config
    """

    permission_classes = [GlobalSettingsPermissions]

    @extend_schema(
        responses={200: PluginSerializers.PluginSettingSerializer(many=True)}
    )
    def get(self, request, pk):
        """Get all settings for a plugin config."""
        # look up the plugin
        plugin = check_plugin(None, pk)

        settings = getattr(plugin, 'settings', {})

        settings_dict = PluginSetting.all_settings(
            settings_definition=settings, plugin=plugin.plugin_config()
        )

        results = PluginSerializers.PluginSettingSerializer(
            list(settings_dict.values()), many=True
        ).data
        return Response(results)


class PluginSettingDetail(RetrieveUpdateAPI):
    """Detail endpoint for a plugin-specific setting.

    Note that these cannot be created or deleted via the API
    """

    queryset = PluginSetting.objects.all()
    serializer_class = PluginSerializers.PluginSettingSerializer

    def get_object(self):
        """Lookup the plugin setting object, based on the URL.

        The URL provides the 'slug' of the plugin, and the 'key' of the setting.
        Both the 'slug' and 'key' must be valid, else a 404 error is raised
        """
        key = self.kwargs['key']

        # Look up plugin
        plugin = check_plugin(
            plugin_slug=self.kwargs.get('plugin'), plugin_pk=self.kwargs.get('pk')
        )

        settings = getattr(plugin, 'settings', {})

        if key not in settings:
            raise NotFound(
                detail=f"Plugin '{plugin.slug}' has no setting matching '{key}'"
            )

        return PluginSetting.get_setting_object(key, plugin=plugin.plugin_config())

    # Staff permission required
    permission_classes = [GlobalSettingsPermissions]


class RegistryStatusView(APIView):
    """Status API endpoint for the plugin registry.

    - GET: Provide status data for the plugin registry
    """

    permission_classes = [IsSuperuser]

    serializer_class = PluginSerializers.PluginRegistryStatusSerializer

    @extend_schema(responses={200: PluginSerializers.PluginRegistryStatusSerializer()})
    def get(self, request):
        """Show registry status information."""
        error_list = []

        for stage, errors in registry.errors.items():
            for error_detail in errors:
                for name, message in error_detail.items():
                    error_list.append({
                        'stage': stage,
                        'name': name,
                        'message': message,
                    })

        result = PluginSerializers.PluginRegistryStatusSerializer({
            'registry_errors': error_list
        }).data

        return Response(result)


plugin_api_urls = [
    path('action/', ActionPluginView.as_view(), name='api-action-plugin'),
    path('barcode/', include(barcode_api_urls)),
    path('locate/', LocatePluginView.as_view(), name='api-locate-plugin'),
    path(
        'plugins/',
        include([
            # Plugin settings URLs
            path(
                'settings/',
                include([
                    re_path(
                        r'^(?P<plugin>[-\w]+)/(?P<key>\w+)/',
                        PluginSettingDetail.as_view(),
                        name='api-plugin-setting-detail',
                    ),  # Used for admin interface
                    path(
                        '', PluginSettingList.as_view(), name='api-plugin-setting-list'
                    ),
                ]),
            ),
            # Detail views for a single PluginConfig item
            path(
                '<int:pk>/',
                include([
                    path(
                        'settings/',
                        include([
                            re_path(
                                r'^(?P<key>\w+)/',
                                PluginSettingDetail.as_view(),
                                name='api-plugin-setting-detail-pk',
                            ),
                            path(
                                '',
                                PluginAllSettingList.as_view(),
                                name='api-plugin-settings',
                            ),
                        ]),
                    ),
                    path(
                        'activate/',
                        PluginActivate.as_view(),
                        name='api-plugin-detail-activate',
                    ),
                    path(
                        'uninstall/',
                        PluginUninstall.as_view(),
                        name='api-plugin-uninstall',
                    ),
                    path('', PluginDetail.as_view(), name='api-plugin-detail'),
                ]),
            ),
            # Metadata
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': PluginConfig},
                name='api-plugin-metadata',
            ),
            # Plugin management
            path('reload/', PluginReload.as_view(), name='api-plugin-reload'),
            path('install/', PluginInstall.as_view(), name='api-plugin-install'),
            path('activate/', PluginActivate.as_view(), name='api-plugin-activate'),
            # Registry status
            path(
                'status/',
                RegistryStatusView.as_view(),
                name='api-plugin-registry-status',
            ),
            # Anything else
            path('', PluginList.as_view(), name='api-plugin-list'),
        ]),
    ),
]
