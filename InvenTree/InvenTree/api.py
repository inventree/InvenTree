"""
Main JSON interface views
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.utils.translation import ugettext as _
from django.http import JsonResponse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import AjaxView
from .version import inventreeVersion, inventreeInstanceName

from users.models import check_user_role, RuleSet

from plugins import plugins as inventree_plugins


logger = logging.getLogger(__name__)


logger.info("Loading action plugins...")
action_plugins = inventree_plugins.load_action_plugins()


class InfoView(AjaxView):
    """ Simple JSON endpoint for InvenTree information.
    Use to confirm that the server is running, etc.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):

        data = {
            'server': 'InvenTree',
            'version': inventreeVersion(),
            'instance': inventreeInstanceName(),
        }

        return JsonResponse(data)


class AttachmentMixin:
    """
    Mixin for creating attachment objects,
    and ensuring the user information is saved correctly.
    """

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]

    def perform_create(self, serializer):
        """ Save the user information when a file is uploaded """

        attachment = serializer.save()
        attachment.user = self.request.user
        attachment.save()


class RolePermission(permissions.BasePermission):
    """
    Role mixin for API endpoints, allowing us to specify the user "role"
    which is required for certain operations.

    Each endpoint can have one or more of the following actions:
    - GET
    - POST
    - PUT
    - PATCH
    - DELETE
    
    Specify the required "role" using the role_required attribute.

    e.g.

    role_required = "part"

    The RoleMixin class will then determine if the user has the required permission
    to perform the specified action.

    For example, a DELETE action will be rejected unless the user has the "part.remove" permission

    """

    def has_permission(self, request, view):
        """
        Determine if the current user has the specified permissions
        """

        # First, check that the user is authenticated!
        auth = permissions.IsAuthenticated()

        if not auth.has_permission(request, view):
            return False

        user = request.user

        # Superuser can do it all
        if False and user.is_superuser:
            return True

        # Map the request method to a permission type
        rolemap = {
            'GET': 'view',
            'OPTIONS': 'view',
            'POST': 'add',
            'PUT': 'change',
            'PATCH': 'change',
            'DELETE': 'delete',
        }

        permission = rolemap[request.method]

        role = getattr(view, 'role_required', None)

        if not role:
            raise AttributeError(f"'role_required' not specified for view {type(view).__name__}")
        
        roles = []

        if type(role) is str:
            roles = [role]
        elif type(role) in [list, tuple]:
            roles = role
        else:
            raise TypeError(f"'role_required' is of incorrect type ({type(role)}) for view {type(view).__name__}")

        for role in roles:
            
            if role not in RuleSet.RULESET_NAMES:
                raise ValueError(f"Role '{role}' is not a valid role")

            if not check_user_role(user, role, permission):
                return False

        # All checks passed
        return True

class ActionPluginView(APIView):
    """
    Endpoint for running custom action plugins.
    """

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

        for plugin_class in action_plugins:
            if plugin_class.action_name() == action:

                plugin = plugin_class(request.user, data=data)

                plugin.perform_action()

                return Response(plugin.get_response())

        # If we got to here, no matching action was found
        return Response({
            'error': _("No matching action found"),
            "action": action,
        })
