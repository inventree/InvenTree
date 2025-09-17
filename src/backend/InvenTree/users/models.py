"""Database model definitions for the 'users' app."""

import datetime

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from allauth.account.models import EmailAddress
from rest_framework.authtoken.models import Token as AuthToken

import InvenTree.helpers
import InvenTree.models
from common.settings import get_global_setting
from InvenTree.ready import isImportingData

from .ruleset import RULESET_CHOICES, get_ruleset_models

logger = structlog.get_logger('inventree')


#  OVERRIDE START
# Overrides Django User model __str__ with a custom function to be able to change
# string representation of a user
def user_model_str(self):
    """Function to override the default Django User __str__."""
    if get_global_setting('DISPLAY_FULL_NAMES', cache=True):
        if self.first_name or self.last_name:
            return f'{self.first_name} {self.last_name}'
    return self.username


User.add_to_class('__str__', user_model_str)  # Overriding User.__str__
#  OVERRIDE END


if settings.LDAP_AUTH:
    from django_auth_ldap.backend import (  # type: ignore[unresolved-import]
        populate_user,
    )

    @receiver(populate_user)
    def create_email_address(user, **kwargs):
        """If a django user is from LDAP and has an email attached to it, create an allauth email address for them automatically.

        https://django-auth-ldap.readthedocs.io/en/latest/users.html#populating-users
        https://django-auth-ldap.readthedocs.io/en/latest/reference.html#django_auth_ldap.backend.populate_user
        """
        # User must exist in the database before we can create their EmailAddress. By their recommendation,
        # we can just call .save() now
        user.save()

        # if they got an email address from LDAP, create it now and make it the primary
        if user.email:
            EmailAddress.objects.create(user=user, email=user.email, primary=True)


def default_token():
    """Generate a default value for the token."""
    return ApiToken.generate_key()


def default_token_expiry():
    """Generate an expiry date for a newly created token."""
    return InvenTree.helpers.current_date() + datetime.timedelta(days=365)


class ApiToken(AuthToken, InvenTree.models.MetadataMixin):
    """Extends the default token model provided by djangorestframework.authtoken.

    Extensions:
    - Adds an 'expiry' date - tokens can be set to expire after a certain date
    - Adds a 'name' field - tokens can be given a custom name (in addition to the user information)
    """

    class Meta:
        """Metaclass defines model properties."""

        verbose_name = _('API Token')
        verbose_name_plural = _('API Tokens')
        abstract = False

    def __str__(self):
        """String representation uses the redacted token."""
        return self.token

    @classmethod
    def generate_key(cls, prefix='inv-'):
        """Generate a new token key - with custom prefix."""
        # Suffix is the date of creation
        suffix = '-' + str(datetime.datetime.now().date().isoformat().replace('-', ''))

        return prefix + str(AuthToken.generate_key()) + suffix

    # Override the 'key' field - force it to be unique
    key = models.CharField(
        default=default_token,
        verbose_name=_('Key'),
        db_index=True,
        unique=True,
        max_length=100,
        validators=[MinLengthValidator(50)],
    )

    # Override the 'user' field, to allow multiple tokens per user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='api_tokens',
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Token Name'),
        help_text=_('Custom token name'),
    )

    expiry = models.DateField(
        default=default_token_expiry,
        verbose_name=_('Expiry Date'),
        help_text=_('Token expiry date'),
        auto_now=False,
        auto_now_add=False,
    )

    last_seen = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Last Seen'),
        help_text=_('Last time the token was used'),
    )

    revoked = models.BooleanField(
        default=False, verbose_name=_('Revoked'), help_text=_('Token has been revoked')
    )

    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize the provide name value."""
        name = str(name).strip()

        # Remove any non-printable chars
        name = InvenTree.helpers.remove_non_printable_characters(
            name, remove_newline=True
        )
        name = InvenTree.helpers.strip_html_tags(name)

        name = name.replace(' ', '-')
        # Limit to 100 characters
        name = name[:100]

        return name

    @property
    @admin.display(description=_('Token'))
    def token(self) -> str:
        """Provide a redacted version of the token.

        The *raw* key value should never be displayed anywhere!
        """
        # If the token has not yet been saved, return the raw key
        if self.pk is None:
            return self.key  # pragma: no cover

        M = len(self.key) - 20

        return self.key[:8] + '*' * M + self.key[-12:]

    @property
    @admin.display(boolean=True, description=_('Expired'))
    def expired(self) -> bool:
        """Test if this token has expired."""
        return (
            self.expiry is not None and self.expiry < InvenTree.helpers.current_date()
        )

    @property
    @admin.display(boolean=True, description=_('Active'))
    def active(self) -> bool:
        """Test if this token is active."""
        return not self.revoked and not self.expired


class RuleSet(models.Model):
    """A RuleSet is somewhat like a superset of the django permission class, in that in encapsulates a bunch of permissions.

    There are *many* apps models used within InvenTree,
    so it makes sense to group them into "roles".

    These roles translate (roughly) to the menu options available.

    Each role controls permissions for a number of database tables,
    which are then handled using the normal django permissions approach.
    """

    RULE_OPTIONS = ['can_view', 'can_add', 'can_change', 'can_delete']

    class Meta:
        """Metaclass defines additional model properties."""

        unique_together = (('name', 'group'),)

    @property
    def label(self) -> str:
        """Return the translated label for this ruleset."""
        return dict(RULESET_CHOICES).get(self.name, self.name)

    name = models.CharField(
        max_length=50,
        choices=RULESET_CHOICES,
        blank=False,
        help_text=_('Permission set'),
    )

    group = models.ForeignKey(
        Group,
        related_name='rule_sets',
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        help_text=_('Group'),
    )

    can_view = models.BooleanField(
        verbose_name=_('View'), default=False, help_text=_('Permission to view items')
    )

    can_add = models.BooleanField(
        verbose_name=_('Add'), default=False, help_text=_('Permission to add items')
    )

    can_change = models.BooleanField(
        verbose_name=_('Change'),
        default=False,
        help_text=_('Permissions to edit items'),
    )

    can_delete = models.BooleanField(
        verbose_name=_('Delete'),
        default=False,
        help_text=_('Permission to delete items'),
    )

    def __str__(self, debug=False):  # pragma: no cover
        """Ruleset string representation."""
        if debug:
            # Makes debugging easier
            return (
                f'{str(self.group).ljust(15)}: {self.name.title().ljust(15)} | '
                f'v: {str(self.can_view).ljust(5)} | a: {str(self.can_add).ljust(5)} | '
                f'c: {str(self.can_change).ljust(5)} | d: {str(self.can_delete).ljust(5)}'
            )
        return self.name

    def save(self, *args, **kwargs):
        """Intercept the 'save' functionality to make additional permission changes.

        It does not make sense to be able to change / create something,
        but not be able to view it!
        """
        if self.can_add or self.can_change or self.can_delete:
            self.can_view = True

        if self.can_add or self.can_delete:
            self.can_change = True

        super().save(*args, **kwargs)

        if self.group:
            # Update the group too!
            # Note: This will trigger the 'update_group_roles' signal
            self.group.save()

    def get_models(self):
        """Return the database tables / models that this ruleset covers."""
        return get_ruleset_models().get(self.name, [])


class Owner(models.Model):
    """The Owner class is a proxy for a Group or User instance.

    Owner can be associated to any InvenTree model (part, stock, build, etc.)

    owner_type: Model type (Group or User)
    owner_id: Group or User instance primary key
    owner: Returns the Group or User instance combining the owner_type and owner_id fields
    """

    class Meta:
        """Metaclass defines extra model properties."""

        # Ensure all owners are unique
        constraints = [
            UniqueConstraint(fields=['owner_type', 'owner_id'], name='unique_owner')
        ]

    @classmethod
    def get_owners_matching_user(cls, user):
        """Return all "owner" objects matching the provided user.

        Includes:
        - An exact match for the user
        - Any groups that the user is a part of
        """
        user_type = ContentType.objects.get(app_label='auth', model='user')
        group_type = ContentType.objects.get(app_label='auth', model='group')

        owners = []

        try:
            owners.append(cls.objects.get(owner_id=user.pk, owner_type=user_type))
        except Exception:  # pragma: no cover
            pass

        for group in user.groups.all():
            try:
                owner = cls.objects.get(owner_id=group.pk, owner_type=group_type)
                owners.append(owner)
            except Exception:  # pragma: no cover
                pass

        return owners

    @staticmethod
    def get_api_url():  # pragma: no cover
        """Returns the API endpoint URL associated with the Owner model."""
        return reverse('api-owner-list')

    owner_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )

    owner_id = models.PositiveIntegerField(null=True, blank=True)

    owner = GenericForeignKey('owner_type', 'owner_id')

    def __str__(self):
        """Defines the owner string representation."""
        if self.owner_type.name == 'user' and get_global_setting(
            'DISPLAY_FULL_NAMES', cache=True
        ):
            display_name = self.owner.get_full_name()
        else:
            display_name = str(self.owner)
        return f'{display_name} ({self.owner_type.name})'

    def name(self):
        """Return the 'name' of this owner."""
        if self.owner_type.name == 'user' and get_global_setting(
            'DISPLAY_FULL_NAMES', cache=True
        ):
            if self.owner and hasattr(self.owner, 'get_full_name'):
                # Use the get_full_name method if available
                return self.owner.get_full_name() or str(self.owner)
            else:
                return str(self.owner)
        return str(self.owner)

    def label(self):
        """Return the 'type' label of this owner i.e. 'user' or 'group'."""
        return str(self.owner_type.name)

    @classmethod
    def create(cls, obj):
        """Check if owner exist then create new owner entry."""
        # Check for existing owner
        existing_owner = cls.get_owner(obj)

        if not existing_owner:
            # Create new owner
            try:
                return cls.objects.create(owner=obj)
            except IntegrityError:  # pragma: no cover
                return None

        return existing_owner

    @classmethod
    def get_owner(cls, user_or_group):
        """Get owner instance for a group or user."""
        user_model = get_user_model()
        owner = None
        content_type_id = 0
        content_type_id_list = [
            ContentType.objects.get_for_model(Group).id,
            ContentType.objects.get_for_model(user_model).id,
        ]

        # If instance type is obvious: set content type
        if isinstance(user_or_group, Group):
            content_type_id = content_type_id_list[0]
        elif isinstance(user_or_group, get_user_model()):
            content_type_id = content_type_id_list[1]

        if content_type_id:
            try:
                owner = Owner.objects.get(
                    owner_id=user_or_group.id, owner_type=content_type_id
                )
            except Owner.DoesNotExist:
                pass

        return owner

    def get_related_owners(self, include_group=False):
        """Get all owners "related" to an owner.

        This method is useful to retrieve all "user-type" owners linked to a "group-type" owner
        """
        user_model = get_user_model()
        related_owners = None

        if type(self.owner) is Group:
            users = user_model.objects.filter(groups__name=self.owner.name)

            if include_group:
                # Include "group-type" owner in the query
                query = Q(
                    owner_id__in=users,
                    owner_type=ContentType.objects.get_for_model(user_model).id,
                ) | Q(
                    owner_id=self.owner.id,
                    owner_type=ContentType.objects.get_for_model(Group).id,
                )
            else:
                query = Q(
                    owner_id__in=users,
                    owner_type=ContentType.objects.get_for_model(user_model).id,
                )

            related_owners = Owner.objects.filter(query)

        elif type(self.owner) is user_model:
            related_owners = [self]

        return related_owners

    def is_user_allowed(self, user, include_group: bool = False):
        """Check if user is allowed to access something owned by this owner."""
        user_owner = Owner.get_owner(user)
        return user_owner in self.get_related_owners(include_group=include_group)


@receiver(post_save, sender=Group, dispatch_uid='create_owner')
@receiver(post_save, sender=get_user_model(), dispatch_uid='create_owner')
def create_owner(sender, instance, **kwargs):
    """Callback function to create a new owner instance after either a new group or user instance is saved."""
    # Ignore during data import process to avoid data duplication
    if not isImportingData():
        Owner.create(obj=instance)


@receiver(post_delete, sender=Group, dispatch_uid='delete_owner')
@receiver(post_delete, sender=get_user_model(), dispatch_uid='delete_owner')
def delete_owner(sender, instance, **kwargs):
    """Callback function to delete an owner instance after either a new group or user instance is deleted."""
    owner = Owner.get_owner(instance)
    owner.delete()


@receiver(post_save, sender=Group, dispatch_uid='create_missing_rule_sets')
def create_missing_rule_sets(sender, instance, **kwargs):
    """Called *after* a Group object is saved.

    As the linked RuleSet instances are saved *before* the Group, then we can now use these RuleSet values to update the group permissions.
    """
    from users.tasks import update_group_roles

    update_group_roles(instance)


class UserProfile(InvenTree.models.MetadataMixin):
    """Model to store additional user profile information."""

    class UserType(models.TextChoices):
        """Enumeration for user types."""

        BOT = 'bot', _('Bot')
        INTERNAL = 'internal', _('Internal')
        EXTERNAL = 'external', _('External')
        GUEST = 'guest', _('Guest')

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('User')
    )
    language = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('Language'),
        help_text=_('Preferred language for the user'),
    )
    theme = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Theme'),
        help_text=_('Settings for the web UI as JSON - do not edit manually!'),
    )
    widgets = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Widgets'),
        help_text=_(
            'Settings for the dashboard widgets as JSON - do not edit manually!'
        ),
    )
    displayname = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Display Name'),
        help_text=_('Chosen display name for the user'),
    )
    position = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Position'),
        help_text=_('Main job title or position'),
    )
    status = models.CharField(
        max_length=2000,
        blank=True,
        null=True,
        verbose_name=_('Status'),
        help_text=_('User status message'),
    )
    location = models.CharField(
        max_length=2000,
        blank=True,
        null=True,
        verbose_name=_('Location'),
        help_text=_('User location information'),
    )
    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('User is actively using the system'),
    )
    contact = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Contact'),
        help_text=_('Preferred contact information for the user'),
    )
    type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.INTERNAL,
        verbose_name=_('User Type'),
        help_text=_('Which type of user is this?'),
    )
    organisation = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Organisation'),
        help_text=_('Users primary organisation/affiliation'),
    )
    primary_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_users',
        verbose_name=_('Primary Group'),
        help_text=_('Primary group for the user'),
    )

    def __str__(self):
        """Return string representation of the user profile."""
        return f'{self.user.username} user profile'

    def save(self, *args, **kwargs):
        """Ensure primary_group is a group that the user is a member of."""
        if self.primary_group and self.primary_group not in self.user.groups.all():
            self.primary_group = None
        super().save(*args, **kwargs)


# Signal to create or update user profile when user is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when user is saved."""
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save()


# Validate groups
@receiver(post_save, sender=Group)
def validate_primary_group_on_save(sender, instance, **kwargs):
    """Validate primary_group on user profiles when a group is created or updated."""
    for user in instance.user_set.all():
        profile = user.profile
        if profile.primary_group and profile.primary_group not in user.groups.all():
            profile.primary_group = None
            profile.save()


@receiver(post_delete, sender=Group)
def validate_primary_group_on_delete(sender, instance, **kwargs):
    """Validate primary_group on user profiles when a group is deleted."""
    for user in instance.user_set.all():
        profile = user.profile
        if profile.primary_group == instance:
            profile.primary_group = None
            profile.save()


@receiver(m2m_changed, sender=User.groups.through)
def validate_primary_group_on_group_change(sender, instance, action, **kwargs):
    """Validate primary_group on user profiles when a group is added or removed."""
    if action in ['post_add', 'post_remove']:
        profile = instance.profile
        if profile.primary_group and profile.primary_group not in instance.groups.all():
            profile.primary_group = None
            profile.save()
