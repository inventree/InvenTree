"""APIs for action plugins."""

from django.utils.translation import gettext_lazy as _

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from plugin import registry


class ActionPluginView(APIView):
    """Endpoint for running custom action plugins."""

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):

        action = request.data.get('action', None)

        data = request.data.get('data', None)

        if action is None:
            return Response({
                'error': _("No action specified")
            })

        action_plugins = registry.with_mixin('action')
        for plugin in action_plugins:
            if plugin.action_name() == action:
                plugin.perform_action(request.user, data=data)
                return Response(plugin.get_response(request.user, data=data))

        # If we got to here, no matching action was found
        return Response({
            'error': _("No matching action found"),
            "action": action,
        })
