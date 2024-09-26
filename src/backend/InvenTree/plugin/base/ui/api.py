"""API for UI plugins."""

from django.urls import path

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import plugin.base.ui.serializers as UIPluginSerializers
from common.settings import get_global_setting
from InvenTree.exceptions import log_error
from plugin import registry


class PluginPanelList(APIView):
    """API endpoint for listing all available plugin panels."""

    permission_classes = [IsAuthenticated]
    serializer_class = UIPluginSerializers.PluginPanelSerializer

    @extend_schema(
        responses={200: UIPluginSerializers.PluginPanelSerializer(many=True)}
    )
    def get(self, request):
        """Show available plugin panels."""
        target_model = request.query_params.get('target_model', None)
        target_id = request.query_params.get('target_id', None)

        panels = []

        if get_global_setting('ENABLE_PLUGINS_INTERFACE'):
            # Extract all plugins from the registry which provide custom panels
            for _plugin in registry.with_mixin('ui', active=True):
                try:
                    # Allow plugins to fill this data out
                    plugin_panels = _plugin.get_ui_panels(
                        target_model, target_id, request
                    )

                    if plugin_panels and type(plugin_panels) is list:
                        for panel in plugin_panels:
                            panel['plugin'] = _plugin.slug

                            # TODO: Validate each panel before inserting
                            panels.append(panel)
                except Exception:
                    # Custom panels could not load
                    # Log the error and continue
                    log_error(f'{_plugin.slug}.get_ui_panels')

        return Response(
            UIPluginSerializers.PluginPanelSerializer(panels, many=True).data
        )


class PluginUIFeatureList(APIView):
    """API endpoint for listing all available plugin ui features."""

    permission_classes = [IsAuthenticated]
    serializer_class = UIPluginSerializers.PluginUIFeatureSerializer

    @extend_schema(
        responses={200: UIPluginSerializers.PluginUIFeatureSerializer(many=True)}
    )
    def get(self, request, feature):
        """Show available plugin ui features."""
        features = []

        if get_global_setting('ENABLE_PLUGINS_INTERFACE'):
            # Extract all plugins from the registry which provide custom ui features
            for _plugin in registry.with_mixin('ui', active=True):
                # Allow plugins to fill this data out
                plugin_features = _plugin.get_ui_features(
                    feature, request.query_params, request
                )

                if plugin_features and type(plugin_features) is list:
                    for _feature in plugin_features:
                        features.append(_feature)

        return Response(
            UIPluginSerializers.PluginUIFeatureSerializer(features, many=True).data
        )


ui_plugins_api_urls = [
    path('panels/', PluginPanelList.as_view(), name='api-plugin-panel-list'),
    path(
        'features/<str:feature>/',
        PluginUIFeatureList.as_view(),
        name='api-plugin-ui-feature-list',
    ),
]
