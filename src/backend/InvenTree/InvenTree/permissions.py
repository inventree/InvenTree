"""Permission set for InvenTree."""

from functools import wraps
from typing import Optional

from oauth2_provider.contrib.rest_framework import TokenMatchesOASRequirements
from rest_framework import permissions

import users.models


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
        rolemap = {
            'GET': 'view',
            'OPTIONS': 'view',
            'POST': 'add',
            'PUT': 'change',
            'PATCH': 'change',
            'DELETE': 'delete',
        }

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


def map_scope(roles: Optional[list[str]] = None, only_read=False) -> dict:
    """Map the required scopes to the current view."""

    def scope_name(tables, action):
        if only_read:
            return ['read']
        if tables:
            return [[action, table] for table in tables]
        return [action]

    return {
        'GET': scope_name(roles, 'get'),
        'POST': scope_name(roles, 'post'),
        'PUT': scope_name(roles, 'put'),
        'PATCH': scope_name(roles, 'patch'),
        'DELETE': scope_name(roles, 'delete'),
        'OPTIONS': ['read'],
    }


# Precalculate the roles mapping
roles = users.models.RuleSet.get_ruleset_models()
precalculated_roles = {}
for role, tables in roles.items():
    for table in tables:
        if table not in precalculated_roles:
            precalculated_roles[table] = []
        precalculated_roles[table].append(role)


class InvenTreeTokenMatchesOASRequirements(TokenMatchesOASRequirements):
    """Permission that discovers the required scopes from the OpenAPI schema."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        if hasattr(view, 'required_alternate_scopes'):
            return view.required_alternate_scopes
        print(view)

        try:
            # Extract the model name associated with this request
            model = get_model_for_view(view)

            if model is None:
                return map_scope(only_read=True)

            return map_scope(
                roles=precalculated_roles.get(
                    f'{model._meta.app_label}_{model._meta.model_name}', []
                )
            )
        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta,
            # then we don't need a permission
            return map_scope(only_read=True)
        except Exception:
            return map_scope(only_read=True)


class IsSuperuser(permissions.IsAdminUser):
    """Allows access only to superuser users."""

    def has_permission(self, request, view):
        """Check if the user is a superuser."""
        return bool(request.user and request.user.is_superuser)


class IsSuperuserOrReadOnly(permissions.IsAdminUser):
    """Allow read-only access to any user, but write access is restricted to superuser users."""

    def has_permission(self, request, view):
        """Check if the user is a superuser."""
        return bool(
            (request.user and request.user.is_superuser)
            or request.method in permissions.SAFE_METHODS
        )


class IsStaffOrReadOnly(permissions.IsAdminUser):
    """Allows read-only access to any user, but write access is restricted to staff users."""

    def has_permission(self, request, view):
        """Check if the user is a superuser."""
        return bool(
            (request.user and request.user.is_staff)
            or request.method in permissions.SAFE_METHODS
        )


def auth_exempt(view_func):
    """Mark a view function as being exempt from auth requirements."""

    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.auth_exempt = True
    return wraps(view_func)(wrapped_view)
