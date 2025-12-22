"""Permission set for InvenTree."""

from functools import wraps
from typing import Optional

from oauth2_provider.contrib.rest_framework import TokenMatchesOASRequirements
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework import permissions

import users.permissions
import users.ruleset
from users.oauth2_scopes import (
    DEFAULT_READ,
    DEFAULT_STAFF,
    DEFAULT_SUPERUSER,
    _roles,
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


def map_scope(
    roles: Optional[list[str]] = None,
    only_read=False,
    read_name=DEFAULT_READ,
    map_read: Optional[list[str]] = None,
    map_read_name=DEFAULT_READ,
    override_all_actions: Optional[str] = None,
) -> dict:
    """Generate the required scopes for OAS permission views.

    Args:
        roles (Optional[list[str]]): A list of roles or tables to generate granular scopes for.
        only_read (bool): If True, only the read scope will be returned for all actions.
        read_name (str): The read scope name to use when `only_read` is True.
        map_read (Optional[list[str]]): A list of HTTP methods that should map to the default read scope (use if some actions requirea differing role).
        map_read_name (str): The read scope name to use for methods specified in `map_read` when `map_read` is specified.
        override_all_actions (Optional[str]): If specified, all actions will be overridden to use the provided action name instead of the default action names.

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
        return scope_name(override_all_actions if override_all_actions else action)

    return {
        method: get_scope(method, action) if method != 'OPTIONS' else [[DEFAULT_READ]]
        for method, action in ACTION_MAP.items()
    }


# Precalculate the roles mapping
roles = users.ruleset.get_ruleset_models()
precalculated_roles = {}
for role, tables in roles.items():
    for table in tables:
        if table not in precalculated_roles:
            precalculated_roles[table] = []
        precalculated_roles[table].append(role)


class OASTokenMixin:
    """Mixin that combines the permissions of normal classes and token classes."""

    ENFORCE_USER_PERMS: bool = False

    def has_permission(self, request, view):
        """Check if the user has the required scopes or was authenticated another way."""
        if self.ENFORCE_USER_PERMS:
            return super().has_permission(request, view)
        return self.check_oauth2_authentication(
            request, view
        ) or super().has_permission(request, view)

    def check_oauth2_authentication(self, request, view):
        """Check if the user is authenticated using OAuth2 and has the required scopes."""
        return self.is_oauth2ed(
            request
        ) and TokenMatchesOASRequirements().has_permission(request, view)

    def is_oauth2ed(self, request):
        """Check if the user is authenticated using OAuth2."""
        oauth2authenticated = False
        if bool(request.user and request.user.is_authenticated):
            oauth2authenticated = isinstance(
                request.successful_authenticator, OAuth2Authentication
            )
        return oauth2authenticated


class InvenTreeRoleScopeMixin(OASTokenMixin):
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


class InvenTreeTokenMatchesOASRequirements(InvenTreeRoleScopeMixin):
    """Combines InvenTree role-based scope handling with OpenAPI schema token requirements.

    Used as default permission class.
    """

    def has_permission(self, request, view):
        """Check if the user has the required scopes or was authenticated another way."""
        if self.is_oauth2ed(request):
            # Check if the user is authenticated using OAuth2 and has the required scopes
            return super().has_permission(request, view)

        # If the user is authenticated using another method, check if they have the required permissions
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Return `True` if permission is granted, `False` otherwise."""
        return True


class ModelPermission(permissions.DjangoModelPermissions):
    """Custom ModelPermission implementation which provides cached lookup of queryset.

    This is entirely for optimization purposes.
    """

    def _queryset(self, view):
        """Return the queryset associated with this view, with caching.

        This is because in a metadata OPTIONS request, the view is copied multiple times.
        We can cache the queryset to avoid repeated calculation.
        """
        if getattr(view, '_cached_queryset', None) is not None:
            return view._cached_queryset

        queryset = super()._queryset(view)

        if queryset is not None:
            view._cached_queryset = queryset

        return queryset


class RolePermission(InvenTreeRoleScopeMixin, permissions.BasePermission):
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

            return users.permissions.check_user_role(user, role, permission)

        try:
            # Extract the model name associated with this request
            model = get_model_for_view(view)

            if model is None:
                return True

        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta,
            # then we don't need a permission
            return True

        return users.permissions.check_user_permission(user, model, permission)


class RolePermissionOrReadOnly(RolePermission):
    """RolePermission which also allows read access for any authenticated user."""

    REQUIRE_STAFF = False

    def has_permission(self, request, view):
        """Determine if the current user has the specified permissions.

        - If the user does have the required role, then allow the request
        - If the user does not have the required role, but is authenticated, then allow read-only access
        """
        user = getattr(request, 'user', None)

        if not user or not user.is_active or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if not self.REQUIRE_STAFF or user.is_staff:
            if super().has_permission(request, view):
                return True

        return request.method in permissions.SAFE_METHODS

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        scopes = map_scope(
            only_read=True,
            read_name=DEFAULT_STAFF,
            map_read=list(permissions.SAFE_METHODS),
        )
        return scopes


class StaffRolePermissionOrReadOnly(RolePermissionOrReadOnly):
    """RolePermission which requires staff AND role access, or read-only."""

    REQUIRE_STAFF = True


class IsSuperuserOrSuperScope(OASTokenMixin, permissions.IsAdminUser):
    """Allows access only to superuser users."""

    def has_permission(self, request, view):
        """Check if the user is a superuser."""
        return bool(request.user and request.user.is_superuser)

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True, read_name=DEFAULT_SUPERUSER)


class IsSuperuserOrReadOnlyOrScope(OASTokenMixin, permissions.IsAdminUser):
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
            map_read=list(permissions.SAFE_METHODS),
        )


class IsAuthenticatedOrReadScope(OASTokenMixin, permissions.IsAuthenticated):
    """Allows access only to authenticated users or read scope tokens."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True)


class IsStaffOrReadOnlyScope(OASTokenMixin, permissions.IsAuthenticated):
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
            only_read=True,
            read_name=DEFAULT_STAFF,
            map_read=list(permissions.SAFE_METHODS),
        )


class IsAdminOrAdminScope(OASTokenMixin, permissions.IsAdminUser):
    """Allows access only to admin users or admin scope tokens."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True, read_name=DEFAULT_STAFF)


class AllowAnyOrReadScope(OASTokenMixin, permissions.AllowAny):
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

    wrapped_view.auth_exempt = True  # type:ignore[unresolved-attribute]
    return wraps(view_func)(wrapped_view)


class UserSettingsPermissionsOrScope(OASTokenMixin, permissions.BasePermission):
    """Special permission class to determine if the user can view / edit a particular setting."""

    def has_object_permission(self, request, view, obj):
        """Check if the user that requested is also the object owner."""
        try:
            user = request.user
        except AttributeError:  # pragma: no cover
            return False

        if not user.is_authenticated:
            return False

        return user == obj.user

    def has_permission(self, request, view):
        """Check that the requesting user is authenticated."""
        try:
            user = request.user
            return user.is_authenticated
        except AttributeError:
            return False

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(only_read=True)


class GlobalSettingsPermissions(OASTokenMixin, permissions.BasePermission):
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
            only_read=True,
            read_name=DEFAULT_STAFF,
            map_read=list(permissions.SAFE_METHODS),
        )


class DataImporterPermission(OASTokenMixin, permissions.BasePermission):
    """Mixin class for determining if the user has correct permissions."""

    ENFORCE_USER_PERMS = True

    def has_permission(self, request, view):
        """Class level permission checks are handled via InvenTree.permissions.IsAuthenticatedOrReadScope."""
        return request.user and request.user.is_authenticated

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(
            roles=_roles,
            map_read=permissions.SAFE_METHODS,
            override_all_actions='change',  # this is done to match the custom has_object_permission method
        )

    def has_object_permission(self, request, view, obj):
        """Check if the user has permission to access the imported object."""
        import importer.models

        # For safe methods (GET, HEAD, OPTIONS), allow access
        if request.method in permissions.SAFE_METHODS:
            return True

        if isinstance(obj, importer.models.DataImportSession):
            session = obj
        else:
            session = getattr(obj, 'session', None)

        if session:
            if model_class := session.model_class:
                return users.permissions.check_user_permission(
                    request.user, model_class, 'change'
                )

        return True
