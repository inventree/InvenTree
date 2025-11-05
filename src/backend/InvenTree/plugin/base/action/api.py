"""APIs for action plugins."""

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

import InvenTree.permissions
from InvenTree.exceptions import log_error
from plugin import PluginMixinEnum, registry


class ActionPluginSerializer(serializers.Serializer):
    """Serializer for the ActionPluginView responses."""

    action = serializers.CharField()
    data = serializers.DictField()


class ActionPluginErrorSerializer(serializers.Serializer):
    """Serializer for the ActionPluginView error responses."""

    error = serializers.CharField()
    action = serializers.CharField(required=False)


class ActionPluginView(GenericAPIView):
    """Endpoint for running custom action plugins."""

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = ActionPluginSerializer

    @extend_schema(
        responses={
            200: ActionPluginSerializer,
            400: OpenApiResponse(
                description='No action specified',
                response=ActionPluginErrorSerializer(),
            ),
            404: OpenApiResponse(
                description='No matching action found',
                response=ActionPluginErrorSerializer(),
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        """This function checks if all required info was submitted and then performs a plugin_action or returns an error."""
        action = request.data.get('action', None)

        data = request.data.get('data', None)

        if action is None:
            return Response(
                {'error': _('No action specified')}, status=status.HTTP_400_BAD_REQUEST
            )

        action_plugins = registry.with_mixin(PluginMixinEnum.ACTION)
        for plugin in action_plugins:
            try:
                if plugin.action_name() == action:
                    plugin.perform_action(request.user, data=data)
                    return Response(plugin.get_response(request.user, data=data))
            except Exception:
                log_error('perform_action', plugin=plugin.slug)

        # If we got to here, no matching action was found
        return Response(
            {'error': _('No matching action found'), 'action': action},
            status=status.HTTP_404_NOT_FOUND,
        )
