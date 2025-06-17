"""DRF API serializers for the 'users' app."""

from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import AppRegistryNotReady
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from InvenTree.ready import isGeneratingSchema
from InvenTree.serializers import InvenTreeModelSerializer

from .models import ApiToken, Owner, RuleSet, UserProfile
from .permissions import check_user_role
from .ruleset import RULESET_CHOICES, RULESET_PERMISSIONS, RuleSetEnum


class OwnerSerializer(InvenTreeModelSerializer):
    """Serializer for an "Owner" (either a "user" or a "group")."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = Owner
        fields = ['pk', 'owner_id', 'owner_model', 'name', 'label']

    name = serializers.CharField(read_only=True)
    owner_model = serializers.CharField(read_only=True, source='owner._meta.model_name')

    label = serializers.CharField(read_only=True)


class RuleSetSerializer(InvenTreeModelSerializer):
    """Serializer for a RuleSet."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = RuleSet
        fields = [
            'pk',
            'name',
            'label',
            'group',
            'can_view',
            'can_add',
            'can_change',
            'can_delete',
        ]
        read_only_fields = ['pk', 'name', 'label', 'group']


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
    permissions = serializers.SerializerMethodField(allow_null=True)

    def get_roles(self, user: User) -> dict:
        """Roles associated with the user."""
        roles = {}

        for ruleset in RULESET_CHOICES:
            role, _text = ruleset

            permissions = []

            for permission in RULESET_PERMISSIONS:
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


def generate_permission_dict(permissions) -> dict:
    """Generate a dictionary of permissions for a given set of permissions."""
    perms = {}

    for permission in permissions:
        perm, model = permission.codename.split('_')

        if model not in perms:
            perms[model] = []

        perms[model].append(perm)
    return perms


def generate_roles_dict(roles) -> dict:
    """Generate a dictionary of roles for a given set of roles."""
    # Build out an (initially empty) dictionary of roles
    role_dict = {name: [] for name, _ in RULESET_CHOICES}

    for role in roles:
        permissions = []

        for permission in ['view', 'add', 'change', 'delete']:
            if getattr(role, f'can_{permission}', False):
                permissions.append(permission)

        role_dict[role.name] = permissions

    return role_dict


class ApiTokenSerializer(InvenTreeModelSerializer):
    """Serializer for the ApiToken model."""

    in_use = serializers.SerializerMethodField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )

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

    def validate(self, data):
        """Validate the data for the serializer."""
        if 'user' not in data:
            data['user'] = self.context['request'].user
        return super().validate(data)


class GetAuthTokenSerializer(serializers.Serializer):
    """Serializer for the GetAuthToken API endpoint."""

    class Meta:
        """Meta options for GetAuthTokenSerializer."""

        model = ApiToken
        fields = ['token', 'name', 'expiry']

    token = serializers.CharField(read_only=True)
    name = serializers.CharField()
    expiry = serializers.DateField(read_only=True)


class BriefUserProfileSerializer(InvenTreeModelSerializer):
    """Brief serializer for the UserProfile model."""

    class Meta:
        """Meta options for BriefUserProfileSerializer."""

        model = UserProfile
        fields = [
            'displayname',
            'position',
            'status',
            'location',
            'active',
            'contact',
            'type',
            'organisation',
            'primary_group',
        ]


class UserProfileSerializer(BriefUserProfileSerializer):
    """Serializer for the UserProfile model."""

    class Meta(BriefUserProfileSerializer.Meta):
        """Meta options for UserProfileSerializer."""

        fields = [
            'language',
            'theme',
            'widgets',
            *BriefUserProfileSerializer.Meta.fields,
        ]


class UserSerializer(InvenTreeModelSerializer):
    """Serializer for a User."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = User
        fields = ['pk', 'username', 'first_name', 'last_name', 'email']

        read_only_fields = ['username', 'email']

    username = serializers.CharField(label=_('Username'), help_text=_('Username'))

    first_name = serializers.CharField(
        label=_('First Name'), help_text=_('First name of the user'), allow_blank=True
    )

    last_name = serializers.CharField(
        label=_('Last Name'), help_text=_('Last name of the user'), allow_blank=True
    )

    email = serializers.EmailField(
        label=_('Email'), help_text=_('Email address of the user'), allow_blank=True
    )


class GroupSerializer(InvenTreeModelSerializer):
    """Serializer for a 'Group'."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = Group
        fields = ['pk', 'name', 'permissions', 'roles', 'users']

    def __init__(self, *args, **kwargs):
        """Initialize this serializer with extra fields as required."""
        role_detail = kwargs.pop('role_detail', False)
        user_detail = kwargs.pop('user_detail', False)
        permission_detail = kwargs.pop('permission_detail', False)

        super().__init__(*args, **kwargs)

        try:
            if not isGeneratingSchema():
                if not permission_detail:
                    self.fields.pop('permissions', None)
                if not role_detail:
                    self.fields.pop('roles', None)
                if not user_detail:
                    self.fields.pop('users', None)

        except AppRegistryNotReady:
            pass

    permissions = serializers.SerializerMethodField(allow_null=True, read_only=True)

    def get_permissions(self, group: Group) -> dict:
        """Return a list of permissions associated with the group."""
        return generate_permission_dict(group.permissions.all())

    roles = RuleSetSerializer(
        source='rule_sets', many=True, read_only=True, allow_null=True
    )

    users = UserSerializer(
        source='user_set', many=True, read_only=True, allow_null=True
    )


class ExtendedUserSerializer(UserSerializer):
    """Serializer for a User with a bit more info."""

    from users.serializers import GroupSerializer

    class Meta(UserSerializer.Meta):
        """Metaclass defines serializer fields."""

        fields = [
            *UserSerializer.Meta.fields,
            'groups',
            'group_ids',
            'is_staff',
            'is_superuser',
            'is_active',
            'profile',
        ]

        read_only_fields = [*UserSerializer.Meta.read_only_fields, 'groups']

    groups = GroupSerializer(many=True, read_only=True)

    # Write-only field, for updating the groups associated with the user
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, write_only=True, required=False
    )

    is_staff = serializers.BooleanField(
        label=_('Staff'),
        help_text=_('Does this user have staff permissions'),
        required=False,
    )

    is_superuser = serializers.BooleanField(
        label=_('Superuser'), help_text=_('Is this user a superuser'), required=False
    )

    is_active = serializers.BooleanField(
        label=_('Active'), help_text=_('Is this user account active'), required=False
    )

    profile = BriefUserProfileSerializer(many=False, read_only=True)

    def validate_is_superuser(self, value):
        """Only a superuser account can adjust this value!"""
        request_user = self.context['request'].user

        if 'is_superuser' in self.context['request'].data:
            if not request_user.is_superuser:
                raise PermissionDenied({
                    'is_superuser': _('Only a superuser can adjust this field')
                })

        return value

    def update(self, instance, validated_data):
        """Update the user instance with the provided data."""
        # Update the groups associated with the user
        groups = validated_data.pop('group_ids', None)

        instance = super().update(instance, validated_data)

        if groups is not None:
            instance.groups.set(groups)

        return instance


class MeUserSerializer(ExtendedUserSerializer):
    """API serializer specifically for the 'me' endpoint."""

    class Meta(ExtendedUserSerializer.Meta):
        """Metaclass options.

        Extends the ExtendedUserSerializer.Meta options,
        but ensures that certain fields are read-only.
        """

        read_only_fields = [
            *ExtendedUserSerializer.Meta.read_only_fields,
            'is_active',
            'is_staff',
            'is_superuser',
        ]

    profile = UserProfileSerializer(many=False, read_only=True)


class UserCreateSerializer(ExtendedUserSerializer):
    """Serializer for creating a new User."""

    class Meta(ExtendedUserSerializer.Meta):
        """Metaclass options for the UserCreateSerializer."""

        # Prevent creation of users with superuser or staff permissions
        read_only_fields = ['groups', 'is_staff', 'is_superuser']

    def validate(self, attrs):
        """Expanded valiadation for auth."""
        user = self.context['request'].user

        # Check that the user trying to create a new user is a superuser
        if not user.is_staff:
            raise serializers.ValidationError(
                _('Only staff users can create new users')
            )

        if not check_user_role(user, RuleSetEnum.ADMIN, 'add'):
            raise serializers.ValidationError(
                _('You do not have permission to create users')
            )

        # Generate a random password
        password = User.objects.make_random_password(length=14)
        attrs.update({'password': password})
        return super().validate(attrs)

    def create(self, validated_data):
        """Send an e email to the user after creation."""
        from InvenTree.helpers_model import get_base_url
        from InvenTree.tasks import email_user, offload_task

        base_url = get_base_url()

        instance = super().create(validated_data)

        # Make sure the user cannot login until they have set a password
        instance.set_unusable_password()

        message = (
            _('Your account has been created.')
            + '\n\n'
            + _('Please use the password reset function to login')
        )

        if base_url:
            message += f'\n\nURL: {base_url}'

        subject = _('Welcome to InvenTree')

        # Send the user an onboarding email (from current site)
        offload_task(
            email_user, instance.pk, str(subject), str(message), force_async=True
        )

        return instance
