"""Permission set for InvenTree."""

from functools import wraps
from typing import Optional

from oauth2_provider.contrib.rest_framework import TokenMatchesOASRequirements
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework import permissions

import users.models
from users.oauth2_scopes import (
    DEFAULT_READ,
    DEFAULT_STAFF,
    DEFAULT_SUPERUSER,
    get_granular_scope,
)

ACTION_MAP = {
    'GET': 'view',
    'POST': 'add',
    'PUT': 'change',
    'PATCH': 'change',
    'DELETE': 'delete',
    'OPTIONS': DEFAULT_READ,
}


def get_model_for_view(view):
    """Attempt to introspect the 'model' type for an API view."""
    if hasattr(view, 'get_permission_model'):
        return view.get_permission_model()

    if hasattr(view, 'serializer_class'):
        return view.serializer_class.Meta.model

    if hasattr(view, 'get_serializer_class'):
        return view.get_serializer_class().Meta.model

    raise AttributeError(f'Serializer class not specified for {view.__class__}')


class RolePermission(permissions.BasePermission):
    """Role mixin for API endpoints, allowing us to specify the user "role" which is required for certain operations.

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
        """Determine if the current user has the specified permissions."""
        user = request.user

        # Superuser can do it all
        if user.is_superuser:
            return True

        # Map the request method to a permission type
        rolemap = {**ACTION_MAP, 'OPTIONS': 'view'}

        # let the view define a custom rolemap
        if hasattr(view, 'rolemap'):
            rolemap.update(view.rolemap)

        permission = rolemap[request.method]

        # The required role may be defined for the view class
        if role := getattr(view, 'role_required', None):
            # If the role is specified as "role.permission", split it
            if '.' in role:
                role, permission = role.split('.')

            return users.models.check_user_role(user, role, permission)

        try:
            # Extract the model name associated with this request
            model = get_model_for_view(view)

            if model is None:
                return True

            app_label = model._meta.app_label
            model_name = model._meta.model_name

            table = f'{app_label}_{model_name}'
        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta,
            # then we don't need a permission
            return True

        return users.models.RuleSet.check_table_permission(user, table, permission)


def map_scope(
    roles: Optional[list[str]] = None,
    only_read=False,
    read_name=DEFAULT_READ,
    map_read: Optional[list[str]] = None,
    map_read_name=DEFAULT_READ,
) -> dict:
    """Generate the required scopes for OAS permission views.

    Args:
        roles (Optional[list[str]]): A list of roles or tables to generate granular scopes for.
        only_read (bool): If True, only the read scope will be returned for all actions.
        read_name (str): The read scope name to use when `only_read` is True.
        map_read (Optional[list[str]]): A list of HTTP methods that should map to the default read scope (use if some actions requirea differing role).
        map_read_name (str): The read scope name to use for methods specified in `map_read` when `map_read` is specified.

    Returns:
        dict: A dictionary mapping HTTP methods to their corresponding scopes.
              Each scope is represented as a list of lists of strings.
    """

    def scope_name(action):
        if only_read:
            return [[read_name]]
        if roles:
            return [[get_granular_scope(action, table) for table in roles]]
        return [[action]]

    def get_scope(method, action):
        if map_read and method in map_read:
            return [[map_read_name]]
        return scope_name(action)

    return {
        method: get_scope(method, action) if method != 'OPTIONS' else [[DEFAULT_READ]]
        for method, action in ACTION_MAP.items()
    }


# Precalculate the roles mapping
roles = users.models.RuleSet.get_ruleset_models()
precalculated_roles = {}
for role, tables in roles.items():
    for table in tables:
        if table not in precalculated_roles:
            precalculated_roles[table] = []
        precalculated_roles[table].append(role)


class OASTokenMatcher(TokenMatchesOASRequirements):
    """Mixin that combines the permissions of normal classes and token classes."""

    def has_permission(self, request, view):
        """Check if the user has the required scopes or was authenticated another way."""
        is_authenticated = permissions.IsAuthenticated().has_permission(request, view)
        oauth2authenticated = False
        if is_authenticated:
            oauth2authenticated = isinstance(
                request.successful_authenticator, OAuth2Authentication
            )

        return (is_authenticated and not oauth2authenticated) or super().has_permission(
            request, view
        )


class InvenTreeTokenMatchesOASRequirements(OASTokenMatcher):
    """Permission that discovers the required scopes from the OpenAPI schema."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        if hasattr(view, 'required_alternate_scopes'):
            return view.required_alternate_scopes
        try:
            # Extract the model name associated with this request
            model = get_model_for_view(view)
            calc = precalculated_roles.get(
                f'{model._meta.app_label}_{model._meta.model_name}', []
            )

            if model is None or not calc:
                return map_scope(only_read=True)
            return map_scope(roles=calc)
        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta,
            # then we don't need a permission
            return map_scope(only_read=True)
        except Exception:
            return map_scope(only_read=True)


class IsSuperuserOrSuperScope(OASTokenMatcher, permissions.IsAdminUser):
    """Allows access only to superuser users."""

    def has_permission(self, request, view):
        """Check if the user is a superuser."""
        return bool(request.user and request.user.is_superuser)

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True, read_name=DEFAULT_SUPERUSER)


class IsSuperuserOrReadOnlyOrScope(OASTokenMatcher, permissions.IsAdminUser):
    """Allow read-only access to any user, but write access is restricted to superuser users."""

    def has_permission(self, request, view):
        """Check if the user is a superuser."""
        return bool(
            (request.user and request.user.is_superuser)
            or request.method in permissions.SAFE_METHODS
        )

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(
            only_read=True,
            read_name=DEFAULT_SUPERUSER,
            map_read=permissions.SAFE_METHODS,
        )


class IsAuthenticatedOrReadScope(OASTokenMatcher, permissions.IsAuthenticated):
    """Allows access only to authenticated users or read scope tokens."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True)


class IsStaffOrReadOnlyScope(OASTokenMatcher, permissions.IsAuthenticated):
    """Allows read-only access to any authenticated user, but write access is restricted to staff users."""

    def has_permission(self, request, view):
        """Check if the user is a staff."""
        return bool(permissions.IsAuthenticated().has_permission(request, view)) and (
            (request.user and request.user.is_staff)
            or request.method in permissions.SAFE_METHODS
        )

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(
            only_read=True, read_name=DEFAULT_STAFF, map_read=permissions.SAFE_METHODS
        )


class IsAdminOrAdminScope(OASTokenMatcher, permissions.IsAdminUser):
    """Allows access only to admin users or admin scope tokens."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True, read_name=DEFAULT_STAFF)


class AllowAnyOrReadScope(TokenMatchesOASRequirements, permissions.AllowAny):
    """Allows access to any user or read scope tokens."""

    def has_permission(self, request, view):
        """Anyone is allowed."""
        return True

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True)


def auth_exempt(view_func):
    """Mark a view function as being exempt from auth requirements."""

    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.auth_exempt = True
    return wraps(view_func)(wrapped_view)


class UserSettingsPermissionsOrScope(OASTokenMatcher, permissions.BasePermission):
    """Special permission class to determine if the user can view / edit a particular setting."""

    def has_object_permission(self, request, view, obj):
        """Check if the user that requested is also the object owner."""
        try:
            user = request.user
        except AttributeError:  # pragma: no cover
            return False

        return user == obj.user

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True)


class GlobalSettingsPermissions(OASTokenMatcher, permissions.BasePermission):
    """Special permission class to determine if the user is "staff"."""

    def has_permission(self, request, view):
        """Check that the requesting user is 'admin'."""
        try:
            user = request.user

            if request.method in permissions.SAFE_METHODS:
                return True
            # Any other methods require staff access permissions
            return user.is_staff

        except AttributeError:  # pragma: no cover
            return False

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(
            only_read=True, read_name=DEFAULT_STAFF, map_read=permissions.SAFE_METHODS
        )
