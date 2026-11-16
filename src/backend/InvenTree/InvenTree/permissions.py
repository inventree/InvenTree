"""Permission set for InvenTree."""

from functools import wraps
from typing import Optional

from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework import permissions

import users.permissions
import users.ruleset
from users.oauth2_scopes import (
    DEFAULT_READ,
    DEFAULT_STAFF,
    DEFAULT_SUPERUSER,
    DEFAULT_WRITE,
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


def get_roles_for_view(view) -> list[str]:
    """Return the user roles associated with the model of an API view."""
    try:
        model = get_model_for_view(view)
    except Exception:
        # Fall back to the model of the queryset (as checked by ModelPermission)
        model = getattr(getattr(view, 'queryset', None), 'model', None)

    if model is None:
        return []

    return precalculated_roles.get(
        f'{model._meta.app_label}_{model._meta.model_name}', []
    )


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


def enforce_oauth2_scopes(has_permission):
    """Decorate a `has_permission` method, so that OAuth2 tokens must hold the required scopes.

    Requests which are not authenticated via OAuth2 are checked by the decorated method only.
    """

    @wraps(has_permission)
    def wrapped_has_permission(self, request, view):
        if self.is_oauth2ed(request) and not self.has_scope_permission(request, view):
            return False

        return has_permission(self, request, view)

    wrapped_has_permission.enforces_oauth2_scopes = True
    return wrapped_has_permission


class OASTokenMixin:
    """Mixin that combines the permissions of normal classes and token classes."""

    def __init_subclass__(cls, **kwargs):
        """Ensure that the scope check is applied to the `has_permission` method of the subclass."""
        super().__init_subclass__(**kwargs)

        if not getattr(cls.has_permission, 'enforces_oauth2_scopes', False):
            cls.has_permission = enforce_oauth2_scopes(cls.has_permission)

    @enforce_oauth2_scopes
    def has_permission(self, request, view):
        """Check the normal permissions (the scopes are checked by the decorator)."""
        return super().has_permission(request, view)

    def has_scope_permission(self, request, view):
        """Check if the OAuth2 token holds one of the scope alternatives required for this request."""
        token = request.auth
        alternatives = self.get_required_alternate_scopes(request, view).get(
            request.method.upper(), []
        )

        return hasattr(token, 'is_valid') and any(
            scopes and token.is_valid(scopes) for scopes in alternatives
        )

    def get_required_alternate_scopes(self, request, view):
        """Return the required scope alternatives for each request method.

        By default, OAuth2 tokens can not access the view.
        """
        return {}

    def is_oauth2ed(self, request):
        """Check if the user is authenticated using OAuth2."""
        oauth2authenticated = False
        if bool(request.user and request.user.is_authenticated):
            oauth2authenticated = isinstance(
                request.successful_authenticator, OAuth2Authentication
            )
        return oauth2authenticated


class InvenTreeRoleScopeMixin(OASTokenMixin):
    """Permission that discovers the required scopes from the user roles of the view."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        if hasattr(view, 'required_alternate_scopes'):
            return view.required_alternate_scopes

        # The required role may be defined for the view class (see RolePermission)
        if role := getattr(view, 'role_required', None):
            if '.' in role:
                role, permission = role.split('.')
                return map_scope(roles=[role], override_all_actions=permission)
            return map_scope(roles=[role])

        if roles := get_roles_for_view(view):
            return map_scope(roles=roles)

        # No role is associated with this view - writing requires the general write scope
        return map_scope(
            only_read=True,
            read_name=DEFAULT_WRITE,
            map_read=list(permissions.SAFE_METHODS),
        )


class InvenTreeTokenMatchesOASRequirements(
    InvenTreeRoleScopeMixin, permissions.BasePermission
):
    """Combines InvenTree role-based scope handling with OpenAPI schema token requirements.

    Used as default permission class.
    """

    def has_permission(self, request, view):
        """Check that the user is authenticated - the user permissions are checked by the other default classes."""
        return bool(request.user and request.user.is_authenticated)


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
    """Allows access only to authenticated users or read / write scope tokens."""

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(
            only_read=True,
            read_name=DEFAULT_WRITE,
            map_read=list(permissions.SAFE_METHODS),
        )


class IsAuthenticatedNotOAuth2(OASTokenMixin, permissions.IsAuthenticated):
    """Allows access only to authenticated users - OAuth2 tokens are never allowed.

    Used for endpoints which issue or manage credentials (e.g. API tokens):
    a scoped OAuth2 token must not be able to obtain an unscoped credential.
    """

    def get_required_alternate_scopes(self, request, view):
        """No scope grants access to this endpoint."""
        return {}


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
    """Allows access to any user or read / write scope tokens."""

    def has_permission(self, request, view):
        """Anyone is allowed."""
        return True

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(
            only_read=True,
            read_name=DEFAULT_WRITE,
            map_read=list(permissions.SAFE_METHODS),
        )


def auth_exempt(view_func):
    """Mark a view function as being exempt from auth requirements."""

    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.auth_exempt = True
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
        return map_scope(
            only_read=True,
            read_name=DEFAULT_WRITE,
            map_read=list(permissions.SAFE_METHODS),
        )


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
            return session.check_import_permission(request.user)

        return True


class ContentTypePermission(OASTokenMixin, permissions.BasePermission):
    """Mixin class for determining if the user has correct permissions."""

    def has_permission(self, request, view):
        """Class level permission checks are handled via InvenTree.permissions.IsAuthenticatedOrReadScope."""
        return request.user and request.user.is_authenticated

    def get_required_alternate_scopes(self, request, view):
        """Return the required scopes for the current request."""
        return map_scope(roles=_roles)

    def has_object_permission(self, request, view, obj):
        """Check if the user has permission to access the object."""
        permission = 'view' if request.method in permissions.SAFE_METHODS else 'change'

        if hasattr(obj, 'check_permission'):
            return obj.check_permission(permission, request.user)

        if model_class := obj.__class__:
            table_name = f'{model_class._meta.app_label}_{model_class._meta.model_name}'

            if table_name in users.ruleset.get_ruleset_ignore():
                # Ignore-listed models have no RuleSet permissions of their own,
                # so check_user_permission() would grant access to every active user.
                # Without an explicit check_permission() on the model, fail safe:
                # allow read access only, and restrict writes to staff users.
                return permission == 'view' or bool(
                    request.user.is_staff or request.user.is_superuser
                )

            return users.permissions.check_user_permission(
                request.user, model_class, 'change'
            )
        return False
