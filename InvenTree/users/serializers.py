"""DRF API serializers for the 'users' app."""

from django.contrib.auth.models import Group, User

from rest_framework import serializers

from InvenTree.serializers import InvenTreeModelSerializer

from .models import Owner, RuleSet, check_user_role


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
        fields = ['pk', 'name']


class RoleSerializer(InvenTreeModelSerializer):
    """Serializer for a roles associated with a given user."""

    class Meta:
        """Metaclass options."""

        model = User
        fields = ['user', 'username', 'is_staff', 'is_superuser', 'roles']

    user = serializers.IntegerField(source='pk')
    username = serializers.CharField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    roles = serializers.SerializerMethodField()

    def get_roles(self, user: User) -> dict:
        """Return roles associated with the specified User."""
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
