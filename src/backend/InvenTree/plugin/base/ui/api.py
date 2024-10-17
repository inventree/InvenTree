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

                try:
                    plugin_features = _plugin.get_ui_features(
                        feature, request.query_params, request
                    )
                except Exception:
                    # Custom features could not load for this plugin
                    # Log the error and continue
                    log_error(f'{_plugin.slug}.get_ui_features')
                    continue

                if plugin_features and type(plugin_features) is list:
                    for _feature in plugin_features:
                        try:
                            # Ensure that the required fields are present
                            _feature['plugin_name'] = _plugin.slug
                            _feature['feature_type'] = str(feature)

                            # Ensure base fields are strings
                            for field in ['key', 'title', 'description', 'source']:
                                if field in _feature:
                                    _feature[field] = str(_feature[field])

                            # Add the feature to the list (serialize)
                            features.append(
                                UIPluginSerializers.PluginUIFeatureSerializer(
                                    _feature, many=False
                                ).data
                            )

                        except Exception:
                            # Custom features could not load
                            # Log the error and continue
                            log_error(f'{_plugin.slug}.get_ui_features')
                            continue

        return Response(features)


ui_plugins_api_urls = [
    path(
        'features/<str:feature>/',
        PluginUIFeatureList.as_view(),
        name='api-plugin-ui-feature-list',
    )
]
