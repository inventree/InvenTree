"""DRF API serializers for the 'users' app."""

from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import AppRegistryNotReady
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from InvenTree.serializers import InvenTreeModelSerializer

from .models import ApiToken, Owner, RuleSet, UserProfile, check_user_role


class OwnerSerializer(InvenTreeModelSerializer):
    """Serializer for an "Owner" (either a "user" or a "group")."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = Owner
        fields = ['pk', 'owner_id', 'owner_model', 'name', 'label']

    name = serializers.CharField(read_only=True)
    owner_model = serializers.CharField(read_only=True, source='owner._meta.model_name')

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


class ExtendedUserSerializer(UserSerializer):
    """Serializer for a User with a bit more info."""

    from users.serializers import GroupSerializer

    groups = GroupSerializer(read_only=True, many=True)

    class Meta(UserSerializer.Meta):
        """Metaclass defines serializer fields."""

        fields = [
            *UserSerializer.Meta.fields,
            'groups',
            'is_staff',
            'is_superuser',
            'is_active',
            'profile',
        ]

        read_only_fields = [*UserSerializer.Meta.read_only_fields, 'groups']

    is_staff = serializers.BooleanField(
        label=_('Staff'), help_text=_('Does this user have staff permissions')
    )

    is_superuser = serializers.BooleanField(
        label=_('Superuser'), help_text=_('Is this user a superuser')
    )

    is_active = serializers.BooleanField(
        label=_('Active'), help_text=_('Is this user account active')
    )

    profile = BriefUserProfileSerializer(many=False, read_only=True)

    def validate(self, attrs):
        """Expanded validation for changing user role."""
        # Check if is_staff or is_superuser is in attrs
        role_change = 'is_staff' in attrs or 'is_superuser' in attrs
        request_user = self.context['request'].user

        if role_change:
            if request_user.is_superuser:
                # Superusers can change any role
                pass
            elif request_user.is_staff and 'is_superuser' not in attrs:
                # Staff can change any role except is_superuser
                pass
            else:
                raise PermissionDenied(
                    _('You do not have permission to change this user role.')
                )
        return super().validate(attrs)


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
        # Check that the user trying to create a new user is a superuser
        if not self.context['request'].user.is_superuser:
            raise serializers.ValidationError(_('Only superusers can create new users'))

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
