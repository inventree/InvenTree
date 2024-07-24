"""DRF API serializers for the 'users' app."""

from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import AppRegistryNotReady
from django.db.models import Q

from rest_framework import serializers

from InvenTree.serializers import InvenTreeModelSerializer

from .models import ApiToken, Owner, RuleSet, check_user_role


class OwnerSerializer(InvenTreeModelSerializer):
    """Serializer for an "Owner" (either a "user" or a "group")."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = Owner
        fields = ['pk', 'owner_id', 'name', 'label']

    name = serializers.CharField(read_only=True)

    label = serializers.CharField(read_only=True)


class GroupSerializer(InvenTreeModelSerializer):
    """Serializer for a 'Group'."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = Group
        fields = ['pk', 'name', 'permissions']

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra fields as required."""
        permission_detail = kwargs.pop('permission_detail', False)

        super().__init__(*args, **kwargs)

        try:
            if not permission_detail:
                self.fields.pop('permissions', None)
        except AppRegistryNotReady:
            pass

    permissions = serializers.SerializerMethodField()

    def get_permissions(self, group: Group):
        """Return a list of permissions associated with the group."""
        return generate_permission_dict(group.permissions.all())


class RoleSerializer(InvenTreeModelSerializer):
    """Serializer for a roles associated with a given user."""

    class Meta:
        """Metaclass options."""

        model = User
        fields = [
            'user',
            'username',
            'roles',
            'permissions',
            'is_staff',
            'is_superuser',
        ]

    user = serializers.IntegerField(source='pk')
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    def get_roles(self, user: User) -> dict:
        """Roles associated with the user."""
        roles = {}

        for ruleset in RuleSet.RULESET_CHOICES:
            role, _text = ruleset

            permissions = []

            for permission in RuleSet.RULESET_PERMISSIONS:
                if check_user_role(user, role, permission):
                    permissions.append(permission)

            if len(permissions) > 0:
                roles[role] = permissions
            else:
                roles[role] = None  # pragma: no cover

        return roles

    def get_permissions(self, user: User) -> dict:
        """Permissions associated with the user."""
        if user.is_superuser:
            permissions = Permission.objects.all()
        else:
            permissions = Permission.objects.filter(
                Q(user=user) | Q(group__user=user)
            ).distinct()

        return generate_permission_dict(permissions)


def generate_permission_dict(permissions):
    """Generate a dictionary of permissions for a given set of permissions."""
    perms = {}

    for permission in permissions:
        perm, model = permission.codename.split('_')

        if model not in perms:
            perms[model] = []

        perms[model].append(perm)
    return perms


class ApiTokenSerializer(InvenTreeModelSerializer):
    """Serializer for the ApiToken model."""

    in_use = serializers.SerializerMethodField(read_only=True)

    def get_in_use(self, token: ApiToken) -> bool:
        """Return True if the token is currently used to call the endpoint."""
        from InvenTree.middleware import get_token_from_request

        request = self.context.get('request')
        rq_token = get_token_from_request(request)
        return token.key == rq_token

    class Meta:
        """Meta options for ApiTokenSerializer."""

        model = ApiToken
        fields = [
            'created',
            'expiry',
            'id',
            'last_seen',
            'name',
            'token',
            'active',
            'revoked',
            'user',
            'in_use',
        ]
