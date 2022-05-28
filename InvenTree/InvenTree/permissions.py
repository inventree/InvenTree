from rest_framework import permissions

import users.models


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

        permission = rolemap[request.method]

        try:
            # Extract the model name associated with this request
            model = view.serializer_class.Meta.model

            app_label = model._meta.app_label
            model_name = model._meta.model_name

            table = f"{app_label}_{model_name}"
        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta,
            # then we don't need a permission
            return True

        result = users.models.RuleSet.check_table_permission(user, table, permission)

        return result
