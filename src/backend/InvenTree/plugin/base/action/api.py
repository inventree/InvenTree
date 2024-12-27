"""APIs for action plugins."""

from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from InvenTree.exceptions import log_error
from plugin import registry


class ActionPluginSerializer(serializers.Serializer):
    """Serializer for the ActionPluginView responses."""

    action = serializers.CharField()
    data = serializers.DictField()


class ActionPluginView(GenericAPIView):
    """Endpoint for running custom action plugins."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ActionPluginSerializer

    def post(self, request, *args, **kwargs):
        """This function checks if all required info was submitted and then performs a plugin_action or returns an error."""
        action = request.data.get('action', None)

        data = request.data.get('data', None)

        if action is None:
            return Response({'error': _('No action specified')})

        action_plugins = registry.with_mixin('action')
        for plugin in action_plugins:
            try:
                if plugin.action_name() == action:
                    plugin.perform_action(request.user, data=data)
                    return Response(plugin.get_response(request.user, data=data))
            except Exception:
                log_error('action_plugin')

        # If we got to here, no matching action was found
        return Response({'error': _('No matching action found'), 'action': action})
