"""Permission classes for the 'scim' app."""

from rest_framework import permissions

from scim.authentication import ScimServiceUser


class IsScimAuthenticated(permissions.BasePermission):
    """Require that the request was authenticated via the SCIM bearer secret."""

    def has_permission(self, request, view):
        """Only allow access if the request was authenticated as the SCIM service user."""
        return isinstance(request.user, ScimServiceUser)
