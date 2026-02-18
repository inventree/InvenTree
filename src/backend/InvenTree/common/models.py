"""Common database model definitions.

These models are 'generic' and do not fit a particular business logic object.
"""

import base64
import hashlib
import hmac
import json
import math
import os
import uuid
from datetime import timedelta, timezone
from email.utils import make_msgid
from enum import Enum
from io import BytesIO
from secrets import compare_digest
from typing import Any, Optional

from django.apps import apps
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.utils import DNS_NAME
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import enums
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

import structlog
from anymail.signals import inbound, tracking
from django_q.signals import post_spawn
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from opentelemetry import trace
from rest_framework.exceptions import PermissionDenied
from taggit.managers import TaggableManager

import common.validators
import InvenTree.conversion
import InvenTree.exceptions
import InvenTree.fields
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import InvenTree.validators
import users.models
from common.setting.type import InvenTreeSettingsKeyType, SettingsKeyType
from common.settings import get_global_setting, global_setting_overrides
from generic.enums import StringEnum
from generic.states import ColorEnum
from generic.states.custom import state_color_mappings
from InvenTree.cache import get_session_cache, set_session_cache
from InvenTree.sanitizer import sanitize_svg
from InvenTree.tracing import TRACE_PROC, TRACE_PROV
from InvenTree.version import inventree_identifier

logger = structlog.get_logger('inventree')


class RenderMeta(enums.ChoicesType):
    """Metaclass for rendering choices."""

    choice_fnc = None

    @property
    def choices(self):
        """Return a list of choices for the enum class."""
        fnc = getattr(self, 'choice_fnc', None)
        if fnc:
            return fnc()
        return []


class RenderChoices(models.TextChoices, metaclass=RenderMeta):  # type: ignore
    """Class for creating enumerated string choices for schema rendering."""


class MetaMixin(models.Model):
    """A base class for InvenTree models to include shared meta fields.

    Attributes:
    - updated: The last time this object was updated
    """

    class Meta:
        """Meta options for MetaMixin."""

        abstract = True

    updated = models.DateTimeField(
        verbose_name=_('Updated'),
        help_text=_('Timestamp of last update'),
        auto_now=True,
        null=True,
    )


class UpdatedUserMixin(models.Model):
    """A mixin which stores additional information about the user who created or last modified the object."""

    class Meta:
        """Meta options for MetaUserMixin."""

        abstract = True

    def save(self, *args, **kwargs):
        """Extract the user object from kwargs, if provided."""
        if updated_by := kwargs.pop('updated_by', None):
            self.updated_by = updated_by

        self.updated = InvenTree.helpers.current_time()

        super().save(*args, **kwargs)

    updated = models.DateTimeField(
        verbose_name=_('Updated'),
        help_text=_('Timestamp of last update'),
        default=None,
        blank=True,
        null=True,
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('Update By'),
        help_text=_('User who last updated this object'),
    )


class ProjectCode(InvenTree.models.InvenTreeMetadataModel):
    """A ProjectCode is a unique identifier for a project."""

    class Meta:
        """Class options for the ProjectCode model."""

        verbose_name = _('Project Code')

    @staticmethod
    def get_api_url():
        """Return the API URL for this model."""
        return reverse('api-project-code-list')

    def __str__(self):
        """String representation of a ProjectCode."""
        return self.code

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Project Code'),
        help_text=_('Unique project code'),
    )

    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Project description'),
    )

    responsible = models.ForeignKey(
        users.models.Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Responsible'),
        help_text=_('User or group responsible for this project'),
        related_name='project_codes',
    )


class BaseInvenTreeSetting(models.Model):
    """An base InvenTreeSetting object is a key:value pair used for storing single values (e.g. one-off settings values).

    Attributes:
        SETTINGS: definition of all available settings
        extra_unique_fields: List of extra fields used to be unique, e.g. for PluginConfig -> plugin
    """

    SETTINGS: dict[str, SettingsKeyType] = {}

    CHECK_SETTING_KEY = False

    extra_unique_fields: list[str] = []

    class Meta:
        """Meta options for BaseInvenTreeSetting -> abstract stops creation of database entry."""

        abstract = True

    def save(self, *args, **kwargs):
        """Enforce validation and clean before saving."""
        self.key = str(self.key).upper()

        do_cache = kwargs.pop('cache', True)

        self.clean()
        self.validate_unique()

        # Execute before_save action
        self._call_settings_function('before_save', args, kwargs)

        super().save()

        # Update this setting in the cache after it was saved so a pk exists
        if do_cache:
            self.save_to_cache()

        # Remove the setting from the request cache
        set_session_cache(self.cache_key, None)

        # Execute after_save action
        self._call_settings_function('after_save', args, kwargs)

    @classmethod
    def build_default_values(cls, **kwargs):
        """Ensure that all values defined in SETTINGS are present in the database.

        If a particular setting is not present, create it with the default value
        """
        try:
            existing_keys = cls.objects.filter(**kwargs).values_list('key', flat=True)
            settings_keys = cls.SETTINGS.keys()

            missing_keys = set(settings_keys) - set(existing_keys)

            if len(missing_keys) > 0:
                logger.info('Building %s default values for %s', len(missing_keys), cls)
                cls.objects.bulk_create([
                    cls(key=key, value=cls.get_setting_default(key), **kwargs)
                    for key in missing_keys
                    if not key.startswith('_')
                ])
        except Exception as exc:
            logger.exception(
                'Failed to build default values for %s (%s)', cls, type(exc)
            )

    def _call_settings_function(self, reference: str, args, kwargs):
        """Call a function associated with a particular setting.

        Args:
            reference (str): The name of the function to call
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
        """
        # Get action
        setting = self.get_setting_definition(
            self.key, *args, **{**self.get_filters_for_instance(), **kwargs}
        )
        settings_fnc = setting.get(reference, None)

        # Execute if callable
        if callable(settings_fnc):
            settings_fnc(self)

    @property
    def cache_key(self):
        """Generate a unique cache key for this settings object."""
        return self.__class__.create_cache_key(
            self.key, **self.get_filters_for_instance()
        )

    def save_to_cache(self):
        """Save this setting object to cache."""
        key = self.cache_key

        # skip saving to cache if no pk is set
        if self.pk is None:
            return

        logger.debug("Saving setting '%s' to cache", key)

        try:
            cache.set(key, self, timeout=3600)
        except Exception:  # pragma: no cover
            pass

    @classmethod
    def create_cache_key(cls, setting_key, **kwargs):
        """Create a unique cache key for a particular setting object.

        The cache key uses the following elements to ensure the key is 'unique':
        - The name of the class
        - The unique KEY string
        - Any key:value kwargs associated with the particular setting type (e.g. user-id)
        """
        key = f'{cls.__name__!s}:{setting_key}'

        for k, v in kwargs.items():
            key += f'_{k}:{v}'

        return key.replace(' ', '')

    @classmethod
    def get_filters(cls, **kwargs):
        """Enable to filter by other kwargs defined in cls.extra_unique_fields."""
        return {
            key: value
            for key, value in kwargs.items()
            if key in cls.extra_unique_fields
        }

    def get_filters_for_instance(self):
        """Enable to filter by other fields defined in self.extra_unique_fields."""
        return {
            key: getattr(self, key, None)
            for key in self.extra_unique_fields
            if hasattr(self, key)
        }

    @classmethod
    def all_settings(
        cls,
        *,
        exclude_hidden=False,
        settings_definition: dict[str, SettingsKeyType] | None = None,
        **kwargs,
    ):
        """Return a list of "all" defined settings.

        This performs a single database lookup,
        and then any settings which are not *in* the database
        are assigned their default values
        """
        filters = cls.get_filters(**kwargs)

        results = cls.objects.all()

        if exclude_hidden:
            # Keys which start with an underscore are used for internal functionality
            results = results.exclude(key__startswith='_')

        # Optionally filter by other keys
        results = results.filter(**filters)

        settings: dict[str, BaseInvenTreeSetting] = {}

        # Query the database
        for setting in results:
            if setting.key:
                settings[setting.key.upper()] = setting

        # Specify any "default" values which are not in the database
        settings_definition = settings_definition or cls.SETTINGS
        for key, setting in settings_definition.items():
            if key.upper() not in settings:
                settings[key.upper()] = cls(
                    key=key.upper(),
                    value=cls.get_setting_default(key, **filters),
                    **filters,
                )

            # remove any hidden settings
            if exclude_hidden and setting.get('hidden', False):
                del settings[key.upper()]

        # format settings values and remove protected
        for key, setting in settings.items():
            validator = cls.get_setting_validator(key, **filters)

            if cls.is_protected(key, **filters) and setting.value != '':
                setting.value = '***'
            elif cls.validator_is_bool(validator):
                setting.value = InvenTree.helpers.str2bool(setting.value)
            elif cls.validator_is_int(validator):
                try:
                    setting.value = int(setting.value)
                except ValueError:
                    setting.value = cls.get_setting_default(key, **filters)

        return settings

    @classmethod
    def allValues(
        cls,
        *,
        exclude_hidden=False,
        settings_definition: dict[str, SettingsKeyType] | None = None,
        **kwargs,
    ):
        """Return a dict of "all" defined global settings.

        This performs a single database lookup,
        and then any settings which are not *in* the database
        are assigned their default values
        """
        all_settings = cls.all_settings(
            exclude_hidden=exclude_hidden,
            settings_definition=settings_definition,
            **kwargs,
        )

        settings: dict[str, Any] = {}

        for key, setting in all_settings.items():
            settings[key] = setting.value

        return settings

    @classmethod
    def check_all_settings(
        cls,
        *,
        exclude_hidden=False,
        settings_definition: dict[str, SettingsKeyType] | None = None,
        **kwargs,
    ):
        """Check if all required settings are set by definition.

        Returns:
            is_valid: Are all required settings defined
            missing_settings: List of all settings that are missing (empty if is_valid is 'True')
        """
        all_settings = cls.all_settings(
            exclude_hidden=exclude_hidden,
            settings_definition=settings_definition,
            **kwargs,
        )

        missing_settings: list[str] = []

        for setting in all_settings.values():
            if setting.required:
                value = setting.value or cls.get_setting_default(setting.key, **kwargs)

                if value == '':
                    missing_settings.append(setting.key.upper())

        return len(missing_settings) == 0, missing_settings

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """Return the 'definition' of a particular settings value, as a dict object.

        - The 'settings' dict can be passed as a kwarg
        - If not passed, look for cls.SETTINGS
        - Returns an empty dict if the key is not found
        """
        settings = kwargs.get('settings', cls.SETTINGS)

        key = str(key).strip().upper()

        if settings is not None and key in settings:
            return settings[key]
        return {}

    @classmethod
    def get_setting_name(cls, key, **kwargs):
        """Return the name of a particular setting.

        If it does not exist, return an empty string.
        """
        setting = cls.get_setting_definition(key, **kwargs)
        return setting.get('name', '')

    @classmethod
    def get_setting_description(cls, key, **kwargs):
        """Return the description for a particular setting.

        If it does not exist, return an empty string.
        """
        setting = cls.get_setting_definition(key, **kwargs)

        return setting.get('description', '')

    @classmethod
    def get_setting_units(cls, key, **kwargs):
        """Return the units for a particular setting.

        If it does not exist, return an empty string.
        """
        setting = cls.get_setting_definition(key, **kwargs)

        return setting.get('units', '')

    @classmethod
    def get_setting_validator(cls, key, **kwargs):
        """Return the validator for a particular setting.

        If it does not exist, return None
        """
        setting = cls.get_setting_definition(key, **kwargs)

        return setting.get('validator', None)

    @classmethod
    def get_setting_default(cls, key, **kwargs):
        """Return the default value for a particular setting.

        If it does not exist, return an empty string
        """
        setting = cls.get_setting_definition(key, **kwargs)

        default = setting.get('default', '')

        if callable(default):
            return default()
        return default

    @classmethod
    def get_setting_choices(cls, key, **kwargs):
        """Return the validator choices available for a particular setting."""
        setting = cls.get_setting_definition(key, **kwargs)

        choices = setting.get('choices', None)

        if callable(choices):
            # Evaluate the function (we expect it will return a list of tuples...)
            try:
                # Attempt to pass the kwargs to the function, if it doesn't expect them, ignore and call without
                return choices(**kwargs)
            except TypeError:
                return choices()

        return choices

    @classmethod
    def get_setting_object(cls, key, **kwargs):
        """Return an InvenTreeSetting object matching the given key.

        - Key is case-insensitive
        - Returns None if no match is made

        As settings are accessed frequently, this function will attempt to access the cache first:

        1. Check the ephemeral request cache
        2. Check the global cache
        3. Query the database
        """
        key = str(key).strip().upper()

        # Unless otherwise specified, attempt to create the setting
        create = kwargs.pop('create', True)

        # Specify if global cache lookup should be performed
        # If not specified, determine based on whether global cache is enabled
        access_global_cache = kwargs.pop('cache', django_settings.GLOBAL_CACHE_ENABLED)

        # Prevent saving to the database during certain operations
        if (
            InvenTree.ready.isImportingData()
            or InvenTree.ready.isRunningMigrations()
            or InvenTree.ready.isRebuildingData()
            or InvenTree.ready.isRunningBackup()
        ):  # pragma: no cover
            create = False
            access_global_cache = False

        cache_key = cls.create_cache_key(key, **kwargs)

        # Fist, attempt to pull the setting from the request cache
        if setting := get_session_cache(cache_key):
            return setting

        if access_global_cache:
            try:
                # First attempt to find the setting object in the cache
                cached_setting = cache.get(cache_key)

                if cached_setting is not None:
                    # Store the cached setting into the session cache

                    set_session_cache(cache_key, cached_setting)
                    return cached_setting

            except Exception:
                # Cache is not ready yet
                access_global_cache = False

        # At this point, we need to query the database

        filters = {
            'key__iexact': key,
            # Optionally filter by other keys
            **cls.get_filters(**kwargs),
        }

        try:
            settings = cls.objects.all()
            setting = settings.filter(**filters).first()
        except (ValueError, cls.DoesNotExist):
            setting = None
        except (IntegrityError, OperationalError, ProgrammingError):
            setting = None

        # Setting does not exist! (Try to create it)
        if not setting and create:
            # Attempt to create a new settings object
            default_value = cls.get_setting_default(key, **kwargs)

            extra_fields = {}

            # Provide extra default fields
            for field in cls.extra_unique_fields:
                if field in kwargs:
                    extra_fields[field] = kwargs[field]

            setting = cls(key=key, value=default_value, **extra_fields)

            try:
                # Wrap this statement in "atomic", so it can be rolled back if it fails
                with transaction.atomic():
                    setting.save(**kwargs)
            except (IntegrityError, OperationalError, ProgrammingError):
                # It might be the case that the database isn't created yet
                pass
            except ValidationError:
                # The setting failed validation - might be due to duplicate keys
                pass

        if setting:
            # Cache this setting object to the request cache
            set_session_cache(cache_key, setting)

            if access_global_cache:
                # Cache this setting object to the global cache
                setting.save_to_cache()

        return setting

    @classmethod
    def get_setting(cls, key, backup_value=None, **kwargs):
        """Get the value of a particular setting.

        If it does not exist, return the backup value (default = None)
        """
        if (
            cls.CHECK_SETTING_KEY
            and key not in cls.SETTINGS
            and not key.startswith('_')
        ):
            logger.warning(
                "get_setting: Setting key '%s' is not defined for class %s", key, cls
            )

        # If no backup value is specified, attempt to retrieve a "default" value
        if backup_value is None:
            backup_value = cls.get_setting_default(key, **kwargs)

        setting = cls.get_setting_object(key, **kwargs)

        if setting:
            value = setting.value

            # Cast to boolean if necessary
            if setting.is_bool():
                value = InvenTree.helpers.str2bool(value)

            # Cast to integer if necessary
            if setting.is_int():
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = backup_value

        else:
            value = backup_value

        return value

    @classmethod
    def set_setting(cls, key, value, change_user=None, create=True, **kwargs):
        """Set the value of a particular setting. If it does not exist, option to create it.

        Args:
            key: settings key
            value: New value
            change_user: User object (must be staff member to update a core setting)
            create: If True, create a new setting if the specified key does not exist.
        """
        if (
            cls.CHECK_SETTING_KEY
            and key not in cls.SETTINGS
            and not key.startswith('_')
        ):
            logger.warning(
                "set_setting: Setting key '%s' is not defined for class %s", key, cls
            )

        if change_user is not None and not change_user.is_staff:
            return

        # Do not write to the database under certain conditions
        if (
            InvenTree.ready.isImportingData()
            or InvenTree.ready.isRunningMigrations()
            or InvenTree.ready.isRebuildingData()
            or InvenTree.ready.isRunningBackup()
        ):  # pragma: no cover
            return

        attempts = int(kwargs.pop('attempts', 3))

        filters = {
            'key__iexact': key,
            # Optionally filter by other keys
            **cls.get_filters(**kwargs),
        }

        try:
            setting = cls.objects.filter(**filters).first()

            if not setting:
                if create:
                    setting = cls(key=key, **kwargs)
                else:
                    return

        except (OperationalError, ProgrammingError):
            if not key.startswith('_'):
                logger.warning("Database is locked, cannot set setting '%s'", key)
            # Likely the DB is locked - not much we can do here
            return
        except Exception as exc:  # pragma: no cover
            logger.exception(
                "Error setting setting '%s' for %s: %s", key, cls, type(exc)
            )
            return

        # Enforce standard boolean representation
        if setting.is_bool():
            value = InvenTree.helpers.str2bool(value)

        try:
            setting.value = str(value)
            setting.save()
        except ValidationError as exc:
            # We need to know about validation errors
            raise exc
        except IntegrityError:
            # Likely a race condition has caused a duplicate entry to be created
            if attempts > 0:
                # Try again
                logger.info(
                    "Duplicate setting key '%s' for %s - trying again", key, cls
                )
                cls.set_setting(
                    key,
                    value,
                    change_user,
                    create=create,
                    attempts=attempts - 1,
                    **kwargs,
                )

        except (OperationalError, ProgrammingError):
            logger.warning("Database is locked, cannot set setting '%s'", key)
            # Likely the DB is locked - not much we can do here
        except Exception as exc:  # pragma: no cover
            # Some other error
            logger.exception(
                "Error setting setting '%s' for %s: %s", key, cls, type(exc)
            )

    key = models.CharField(
        max_length=50, blank=False, unique=False, help_text=_('Settings key')
    )

    value = models.CharField(
        max_length=2000, blank=True, unique=False, help_text=_('Settings value')
    )

    @property
    def name(self):
        """Return name for setting."""
        return self.__class__.get_setting_name(
            self.key, **self.get_filters_for_instance()
        )

    @property
    def default_value(self):
        """Return default_value for setting."""
        return self.__class__.get_setting_default(
            self.key, **self.get_filters_for_instance()
        )

    @property
    def description(self):
        """Return description for setting."""
        return self.__class__.get_setting_description(
            self.key, **self.get_filters_for_instance()
        )

    @property
    def units(self):
        """Return units for setting."""
        return self.__class__.get_setting_units(
            self.key, **self.get_filters_for_instance()
        )

    def clean(self):
        """If a validator (or multiple validators) are defined for a particular setting key, run them against the 'value' field."""
        super().clean()

        # Encode as native values
        if self.is_int():
            self.value = self.as_int(raise_error=True)

        elif self.is_bool():
            self.value = self.as_bool()

        elif self.is_float():
            self.value = self.as_float(raise_error=True)

        validator = self.__class__.get_setting_validator(
            self.key, **self.get_filters_for_instance()
        )

        if validator is not None:
            self.run_validator(validator)

        options = self.valid_options()

        if options and self.value not in options:
            raise ValidationError(_('Chosen value is not a valid option'))

    def run_validator(self, validator):
        """Run a validator against the 'value' field for this InvenTreeSetting object."""
        if validator is None:
            return

        value = self.value

        # Boolean validator
        if validator is bool:
            # Value must "look like" a boolean value
            if InvenTree.helpers.is_bool(value):
                # Coerce into either "True" or "False"
                value = InvenTree.helpers.str2bool(value)
            else:
                raise ValidationError({'value': _('Value must be a boolean value')})

        # Integer validator
        if validator is int:
            try:
                # Coerce into an integer value
                value = int(value)
            except (ValueError, TypeError):
                raise ValidationError({'value': _('Value must be an integer value')})

        # Floating point validator
        if validator is float:
            try:
                # Coerce into a floating point value
                value = float(value)
            except (ValueError, TypeError):
                raise ValidationError({'value': _('Value must be a valid number')})

        # If a list of validators is supplied, iterate through each one
        if type(validator) in [list, tuple]:
            for v in validator:
                self.run_validator(v)

        if callable(validator):
            # We can accept function validators with a single argument

            if self.is_bool():
                value = self.as_bool()

            elif self.is_int():
                value = self.as_int()

            elif self.is_float():
                value = self.as_float()

            try:
                validator(value)
            except ValidationError as e:
                raise e
            except Exception:
                raise ValidationError({
                    'value': _('Value does not pass validation checks')
                })

    def validate_unique(self, exclude=None):
        """Ensure that the key:value pair is unique. In addition to the base validators, this ensures that the 'key' is unique, using a case-insensitive comparison.

        Note that sub-classes (UserSetting, PluginSetting) use other filters
        to determine if the setting is 'unique' or not
        """
        super().validate_unique(exclude)

        filters = {
            'key__iexact': self.key,
            # Optionally filter by other keys
            **self.get_filters_for_instance(),
        }

        try:
            # Check if a duplicate setting already exists
            setting = self.__class__.objects.filter(**filters).exclude(id=self.id)

            if setting.exists():
                raise ValidationError({'key': _('Key string must be unique')})

        except self.DoesNotExist:
            pass

    def choices(self):
        """Return the available choices for this setting (or None if no choices are defined)."""
        return self.__class__.get_setting_choices(
            self.key, **self.get_filters_for_instance()
        )

    def valid_options(self):
        """Return a list of valid options for this setting."""
        choices = self.choices()

        if not choices:
            return None

        return [opt[0] for opt in choices]

    def is_choice(self):
        """Check if this setting is a "choice" field."""
        return (
            self.__class__.get_setting_choices(
                self.key, **self.get_filters_for_instance()
            )
            is not None
        )

    def as_choice(self):
        """Render this setting as the "display" value of a choice field.

        E.g. if the choices are:
        [('A4', 'A4 paper'), ('A3', 'A3 paper')],
        and the value is 'A4',
        then display 'A4 paper'
        """
        choices = self.get_setting_choices(self.key, **self.get_filters_for_instance())

        if not choices:
            return self.value

        for value, display in choices:
            if value == self.value:
                return display

        return self.value

    def is_model(self):
        """Check if this setting references a model instance in the database."""
        return self.model_name() is not None

    def model_name(self) -> str:
        """Return the model name associated with this setting."""
        setting = self.get_setting_definition(
            self.key, **self.get_filters_for_instance()
        )

        return setting.get('model', None)

    def confirm(self) -> bool:
        """Return if this setting requires confirmation on change."""
        setting = self.get_setting_definition(
            self.key, **self.get_filters_for_instance()
        )

        return setting.get('confirm', False)

    def confirm_text(self) -> str:
        """Return the confirmation text for this setting, if provided."""
        setting = self.get_setting_definition(
            self.key, **self.get_filters_for_instance()
        )

        return setting.get('confirm_text', '')

    def model_filters(self) -> Optional[dict]:
        """Return the model filters associated with this setting."""
        setting = self.get_setting_definition(
            self.key, **self.get_filters_for_instance()
        )

        filters = setting.get('model_filters', None)

        if filters is not None and type(filters) is not dict:
            filters = None

        return filters

    def model_class(self):
        """Return the model class associated with this setting.

        If (and only if):
        - It has a defined 'model' parameter
        - The 'model' parameter is of the form app.model
        - The 'model' parameter has matches a known app model
        """
        model_name = self.model_name()

        if not model_name:
            return None

        # Enforce lower-case model name
        model_name = str(model_name).strip().lower()

        try:
            (app, mdl) = model_name.strip().split('.')
        except ValueError:
            logger.exception(
                "Invalid 'model' parameter for setting '%s': '%s'", self.key, model_name
            )
            return None

        app_models = apps.all_models.get(app, None)

        if app_models is None:
            logger.error(
                "Error retrieving model class '%s' for setting '%s' - no app named '%s'",
                model_name,
                self.key,
                app,
            )
            return None

        model = app_models.get(mdl, None)

        if model is None:
            logger.error(
                "Error retrieving model class '%s' for setting '%s' - no model named '%s'",
                model_name,
                self.key,
                mdl,
            )
            return None

        # Looks like we have found a model!
        return model

    def api_url(self):
        """Return the API url associated with the linked model, if provided, and valid!"""
        model_class = self.model_class()

        if model_class:
            # If a valid class has been found, see if it has registered an API URL
            try:
                return model_class.get_api_url()
            except Exception:
                pass

            # Some other model types are hard-coded
            hardcoded_models = {
                'auth.user': 'api-user-list',
                'auth.group': 'api-group-list',
            }

            model_table = (
                f'{model_class._meta.app_label}.{model_class._meta.model_name}'
            )

            if url := hardcoded_models[model_table]:
                return reverse(url)

        return None

    def is_bool(self):
        """Check if this setting is required to be a boolean value."""
        validator = self.__class__.get_setting_validator(
            self.key, **self.get_filters_for_instance()
        )

        return self.__class__.validator_is_bool(validator)

    def as_bool(self):
        """Return the value of this setting converted to a boolean value.

        Warning: Only use on values where is_bool evaluates to true!
        """
        return InvenTree.helpers.str2bool(self.value)

    def setting_type(self):
        """Return the field type identifier for this setting object."""
        if self.is_bool():
            return 'boolean'

        elif self.is_int():
            return 'integer'

        elif self.is_model():
            return 'related field'
        return 'string'

    @classmethod
    def validator_is_bool(cls, validator):
        """Return if validator is for bool."""
        if validator == bool:
            return True

        if type(validator) in [list, tuple]:
            for v in validator:
                if v == bool:
                    return True

        return False

    def is_float(self):
        """Check if the setting is required to be a float value."""
        validator = self.__class__.get_setting_validator(
            self.key, **self.get_filters_for_instance()
        )

        return self.__class__.validator_is_float(validator)

    @classmethod
    def validator_is_float(cls, validator):
        """Return if validator is for float."""
        if validator == float:
            return True

        if type(validator) in [list, tuple]:
            for v in validator:
                if v == float:
                    return True

        return False

    def as_float(self, raise_error: bool = False) -> float:
        """Return the value of this setting converted to a float value.

        If an error occurs, return the default value
        """
        try:
            value = float(self.value)
        except (ValueError, TypeError):
            if raise_error:
                raise ValidationError('Provided value is not a valid float')
            value = self.default_value

        return value

    def is_int(self):
        """Check if the setting is required to be an integer value."""
        validator = self.__class__.get_setting_validator(
            self.key, **self.get_filters_for_instance()
        )

        return self.__class__.validator_is_int(validator)

    @classmethod
    def validator_is_int(cls, validator):
        """Return if validator is for int."""
        if validator == int:
            return True

        if type(validator) in [list, tuple]:
            for v in validator:
                if v == int:
                    return True

        return False

    def as_int(self, raise_error: bool = False) -> int:
        """Return the value of this setting converted to a boolean value.

        If an error occurs, return the default value
        """
        try:
            value = int(self.value)
        except (ValueError, TypeError):
            if raise_error:
                raise ValidationError('Provided value is not a valid integer')
            value = self.default_value

        return value

    @classmethod
    def is_protected(cls, key, **kwargs):
        """Check if the setting value is protected."""
        setting = cls.get_setting_definition(key, **cls.get_filters(**kwargs))

        return setting.get('protected', False)

    @property
    def protected(self):
        """Returns if setting is protected from rendering."""
        return self.__class__.is_protected(self.key, **self.get_filters_for_instance())

    @classmethod
    def is_required(cls, key, **kwargs):
        """Check if this setting value is required."""
        setting = cls.get_setting_definition(key, **cls.get_filters(**kwargs))

        return setting.get('required', False)

    @property
    def required(self):
        """Returns if setting is required."""
        return self.__class__.is_required(self.key, **self.get_filters_for_instance())


class InvenTreeSetting(BaseInvenTreeSetting):
    """An InvenTreeSetting object is a key:value pair used for storing single values (e.g. one-off settings values).

    The class provides a way of retrieving the value for a particular key,
    even if that key does not exist.
    """

    from common.setting.system import SYSTEM_SETTINGS

    SETTINGS: dict[str, InvenTreeSettingsKeyType] = SYSTEM_SETTINGS

    CHECK_SETTING_KEY = True

    class Meta:
        """Meta options for InvenTreeSetting."""

        verbose_name = 'InvenTree Setting'
        verbose_name_plural = 'InvenTree Settings'

    def save(self, *args, **kwargs):
        """When saving a global setting, check to see if it requires a server restart.

        If so, set the "SERVER_RESTART_REQUIRED" setting to True
        """
        overrides = global_setting_overrides()

        # If an override is specified for this setting, use that value
        if self.key in overrides:
            self.value = overrides[self.key]

        super().save()

        if self.requires_restart() and not InvenTree.ready.isImportingData():
            InvenTreeSetting.set_setting('SERVER_RESTART_REQUIRED', True, None)

    @classmethod
    def get_setting_default(cls, key, **kwargs):
        """Return the default value a particular setting."""
        overrides = global_setting_overrides()

        if key in overrides:
            # If an override is specified for this setting, use that value
            return overrides[key]

        return super().get_setting_default(key, **kwargs)

    @classmethod
    def get_setting(cls, key, backup_value=None, **kwargs):
        """Get the value of a particular setting.

        If it does not exist, return the backup value (default = None)
        """
        overrides = global_setting_overrides()

        if key in overrides:
            # If an override is specified for this setting, use that value
            return overrides[key]

        return super().get_setting(key, backup_value=backup_value, **kwargs)

    """
    Dict of all global settings values:

    The key of each item is the name of the value as it appears in the database.

    Each global setting has the following parameters:

    - name: Translatable string name of the setting (required)
    - description: Translatable string description of the setting (required)
    - default: Default value (optional)
    - units: Units of the particular setting (optional)
    - validator: Validation function for the setting (optional)

    The keys must be upper-case
    """

    typ = 'inventree'

    key = models.CharField(
        max_length=50, blank=False, unique=True, help_text=_('Settings key')
    )

    def to_native_value(self):
        """Return the "pythonic" value, e.g. convert "True" to True, and "1" to 1."""
        return self.__class__.get_setting(self.key)

    def requires_restart(self):
        """Return True if this setting requires a server restart after changing."""
        options = InvenTreeSetting.SETTINGS.get(self.key, None)

        if options:
            return options.get('requires_restart', False)
        return False


class InvenTreeUserSetting(BaseInvenTreeSetting):
    """An InvenTreeSetting object with a user context."""

    import common.setting.user

    SETTINGS = common.setting.user.USER_SETTINGS

    CHECK_SETTING_KEY = True

    class Meta:
        """Meta options for InvenTreeUserSetting."""

        verbose_name = 'InvenTree User Setting'
        verbose_name_plural = 'InvenTree User Settings'
        constraints = [
            models.UniqueConstraint(fields=['key', 'user'], name='unique key and user')
        ]

    typ = 'user'
    extra_unique_fields = ['user']

    key = models.CharField(
        max_length=50, blank=False, unique=False, help_text=_('Settings key')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    def to_native_value(self):
        """Return the "pythonic" value, e.g. convert "True" to True, and "1" to 1."""
        return self.__class__.get_setting(self.key, user=self.user)


class PriceBreak(MetaMixin):
    """Represents a PriceBreak model."""

    class Meta:
        """Define this as abstract -> no DB entry is created."""

        abstract = True

    quantity = InvenTree.fields.RoundingDecimalField(
        max_digits=15,
        decimal_places=5,
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity'),
        help_text=_('Price break quantity'),
    )

    price = InvenTree.fields.InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=6,
        null=True,
        verbose_name=_('Price'),
        help_text=_('Unit price at specified quantity'),
    )

    def convert_to(self, currency_code):
        """Convert the unit-price at this price break to the specified currency code.

        Args:
            currency_code: The currency code to convert to (e.g "USD" or "AUD")
        """
        try:
            converted = convert_money(self.price, currency_code)
        except MissingRate:
            logger.warning(
                'No currency conversion rate available for %s -> %s',
                self.price_currency,
                currency_code,
            )
            return self.price.amount

        return converted.amount


class VerificationMethod(Enum):
    """Class to hold method references."""

    NONE = 0
    TOKEN = 1
    HMAC = 2


class WebhookEndpoint(models.Model):
    """Defines a Webhook endpoint.

    Attributes:
        endpoint_id: Path to the webhook,
        name: Name of the webhook,
        active: Is this webhook active?,
        user: User associated with webhook,
        token: Token for sending a webhook,
        secret: Shared secret for HMAC verification,
    """

    # Token
    TOKEN_NAME = 'Token'
    VERIFICATION_METHOD = VerificationMethod.NONE

    MESSAGE_OK = 'Message was received.'
    MESSAGE_TOKEN_ERROR = 'Incorrect token in header.'

    endpoint_id = models.CharField(
        max_length=255,
        verbose_name=_('Endpoint'),
        help_text=_('Endpoint at which this webhook is received'),
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Name'),
        help_text=_('Name for this webhook'),
    )

    active = models.BooleanField(
        default=True, verbose_name=_('Active'), help_text=_('Is this webhook active')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Token'),
        help_text=_('Token for access'),
        default=uuid.uuid4,
    )

    secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Secret'),
        help_text=_('Shared secret for HMAC'),
    )

    # To be overridden

    def init(self, request, *args, **kwargs):
        """Set verification method.

        Args:
            request: Original request object.
        """
        self.verify = self.VERIFICATION_METHOD

    def process_webhook(self):
        """Process the webhook incoming.

        This does not deal with the data itself - that happens in process_payload.
        Do not touch or pickle data here - it was not verified to be safe.
        """
        if self.token:
            self.verify = VerificationMethod.TOKEN
        if self.secret:
            self.verify = VerificationMethod.HMAC
        return True

    def validate_token(self, payload, headers, request):
        """Make sure that the provided token (if any) confirms to the setting for this endpoint.

        This can be overridden to create your own token validation method.
        """
        token = headers.get(self.TOKEN_NAME, '')

        # no token
        if self.verify == VerificationMethod.NONE:
            # do nothing as no method was chosen
            pass

        # static token
        elif self.verify == VerificationMethod.TOKEN:
            if not compare_digest(token, self.token):
                raise PermissionDenied(self.MESSAGE_TOKEN_ERROR)

        # hmac token
        elif self.verify == VerificationMethod.HMAC:
            digest = hmac.new(
                self.secret.encode('utf-8'), request.body, hashlib.sha256
            ).digest()
            computed_hmac = base64.b64encode(digest)
            if not hmac.compare_digest(computed_hmac, token.encode('utf-8')):
                raise PermissionDenied(self.MESSAGE_TOKEN_ERROR)

        return True

    def save_data(self, payload=None, headers=None, request=None):
        """Safes payload to database.

        Args:
            payload  (optional): Payload that was send along. Defaults to None.
            headers (optional): Headers that were send along. Defaults to None.
            request (optional): Original request object. Defaults to None.
        """
        return WebhookMessage.objects.create(
            host=request.get_host() if request else '',
            header=json.dumps(dict(headers.items())) if headers else None,
            body=payload,
            endpoint=self,
        )

    def process_payload(self, message, payload=None, headers=None) -> bool:
        """Process a payload.

        Args:
            message: DB entry for this message mm
            payload (optional): Payload that was send along. Defaults to None.
            headers (optional): Headers that were included. Defaults to None.

        Returns:
            bool: Was the message processed
        """
        return True

    def get_return(self, payload=None, headers=None, request=None) -> str:
        """Returns the message that should be returned to the endpoint caller.

        Args:
            payload  (optional): Payload that was send along. Defaults to None.
            headers (optional): Headers that were send along. Defaults to None.
            request (optional): Original request object. Defaults to None.

        Returns:
            str: Message for caller.
        """
        return self.MESSAGE_OK


class WebhookMessage(models.Model):
    """Defines a webhook message.

    Attributes:
        message_id: Unique identifier for this message,
        host: Host from which this message was received,
        header: Header of this message,
        body: Body of this message,
        endpoint: Endpoint on which this message was received,
        worked_on: Was the work on this message finished?
    """

    message_id = models.UUIDField(
        verbose_name=_('Message ID'),
        help_text=_('Unique identifier for this message'),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    host = models.CharField(
        max_length=255,
        verbose_name=_('Host'),
        help_text=_('Host from which this message was received'),
        editable=False,
    )

    header = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Header'),
        help_text=_('Header of this message'),
        editable=False,
    )

    body = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Body'),
        help_text=_('Body of this message'),
        editable=False,
    )

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Endpoint'),
        help_text=_('Endpoint on which this message was received'),
    )

    worked_on = models.BooleanField(
        default=False,
        verbose_name=_('Worked on'),
        help_text=_('Was the work on this message finished?'),
    )


class NotificationEntry(MetaMixin):
    """A NotificationEntry records the last time a particular notification was sent out.

    It is recorded to ensure that notifications are not sent out "too often" to users.

    Attributes:
    - key: A text entry describing the notification e.g. 'part.notify_low_stock'
    - uid: An (optional) numerical ID for a particular instance
    - date: The last time this notification was sent
    """

    class Meta:
        """Meta options for NotificationEntry."""

        unique_together = [('key', 'uid')]

    key = models.CharField(max_length=250, blank=False)

    uid = models.IntegerField()

    @classmethod
    def check_recent(cls, key: str, uid: int, delta: timedelta):
        """Test if a particular notification has been sent in the specified time period."""
        since = InvenTree.helpers.current_date() - delta

        entries = cls.objects.filter(key=key, uid=uid, updated__gte=since)

        return entries.exists()

    @classmethod
    def notify(cls, key: str, uid: int):
        """Notify the database that a particular notification has been sent out."""
        entry, _ = cls.objects.get_or_create(key=key, uid=uid)

        entry.save()


class NotificationMessage(models.Model):
    """A NotificationMessage is a message sent to a particular user, notifying them of some important information.

    Notification messages can be generated by a variety of sources.

    Attributes:
        target_object: The 'target' of the notification message
        source_object: The 'source' of the notification message
    """

    # generic link to target
    target_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name='notification_target'
    )

    target_object_id = models.PositiveIntegerField()

    target_object = GenericForeignKey('target_content_type', 'target_object_id')

    # generic link to source
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name='notification_source',
        null=True,
        blank=True,
    )

    source_object_id = models.PositiveIntegerField(null=True, blank=True)

    source_object = GenericForeignKey('source_content_type', 'source_object_id')

    # user that receives the notification
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        help_text=_('User'),
        null=True,
        blank=True,
    )

    category = models.CharField(max_length=250, blank=False)

    name = models.CharField(max_length=250, blank=False)

    message = models.CharField(max_length=250, blank=True, null=True)

    creation = models.DateTimeField(auto_now_add=True)

    read = models.BooleanField(default=False)

    @staticmethod
    def get_api_url():
        """Return API endpoint."""
        return reverse('api-notifications-list')

    def age(self) -> int:
        """Age of the message in seconds."""
        # Add timezone information if TZ is enabled (in production mode mostly)
        delta = now() - (
            self.creation.replace(tzinfo=timezone.utc)
            if django_settings.USE_TZ
            else self.creation
        )
        return delta.seconds

    def age_human(self) -> str:
        """Humanized age."""
        return naturaltime(self.creation)


class NewsFeedEntry(models.Model):
    """A NewsFeedEntry represents an entry on the RSS/Atom feed that is generated for InvenTree news.

    Attributes:
    - feed_id: Unique id for the news item
    - title: Title for the news item
    - link: Link to the news item
    - published: Date of publishing of the news item
    - author: Author of news item
    - summary: Summary of the news items content
    - read: Was this item already by a superuser?
    """

    feed_id = models.CharField(verbose_name=_('Id'), unique=True, max_length=250)

    title = models.CharField(verbose_name=_('Title'), max_length=250)

    link = models.URLField(verbose_name=_('Link'), max_length=250)

    published = models.DateTimeField(verbose_name=_('Published'), max_length=250)

    author = models.CharField(verbose_name=_('Author'), max_length=250)

    summary = models.CharField(verbose_name=_('Summary'), max_length=250)

    read = models.BooleanField(
        verbose_name=_('Read'), help_text=_('Was this news item read?'), default=False
    )


def rename_notes_image(instance, filename):
    """Function for renaming uploading image file. Will store in the 'notes' directory."""
    fname = os.path.basename(filename)
    return os.path.join('notes', fname)


class NotesImage(models.Model):
    """Model for storing uploading images for the 'notes' fields of various models.

    Simply stores the image file, for use in the 'notes' field (of any models which support markdown).
    """

    image = models.ImageField(
        upload_to=rename_notes_image, verbose_name=_('Image'), help_text=_('Image file')
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)

    model_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[common.validators.validate_notes_model_type],
        help_text=_('Target model type for this image'),
    )

    model_id = models.IntegerField(
        help_text=_('Target model ID for this image'),
        blank=True,
        null=True,
        default=None,
    )


class CustomUnit(models.Model):
    """Model for storing custom physical unit definitions.

    Model Attributes:
        name: Name of the unit
        definition: Definition of the unit
        symbol: Symbol for the unit (e.g. 'm' for 'metre') (optional)

    Refer to the pint documentation for further information on unit definitions.
    https://pint.readthedocs.io/en/stable/advanced/defining.html
    """

    class Meta:
        """Class meta options."""

        verbose_name = _('Custom Unit')

    def fmt_string(self):
        """Construct a unit definition string e.g. 'dog_year = 52 * day = dy'."""
        fmt = f'{self.name} = {self.definition}'

        if self.symbol:
            fmt += f' = {self.symbol}'

        return fmt

    def validate_unique(self, exclude=None) -> None:
        """Ensure that the custom unit is unique."""
        super().validate_unique(exclude)

        if self.symbol and (
            CustomUnit.objects.filter(symbol=self.symbol).exclude(pk=self.pk).exists()
        ):
            raise ValidationError({'symbol': _('Unit symbol must be unique')})

    def clean(self):
        """Validate that the provided custom unit is indeed valid."""
        super().clean()

        from InvenTree.conversion import get_unit_registry

        registry = get_unit_registry()

        # Check that the 'name' field is valid
        self.name = self.name.strip()

        # Cannot be zero length
        if not self.name.isidentifier():
            raise ValidationError({'name': _('Unit name must be a valid identifier')})

        self.definition = self.definition.strip()

        # Check that the 'definition' is valid, by itself
        try:
            registry.Quantity(self.definition)
        except Exception as exc:
            raise ValidationError({'definition': str(exc)})

        # Finally, test that the entire custom unit definition is valid
        try:
            registry.define(self.fmt_string())
        except Exception as exc:
            raise ValidationError(str(exc))

    name = models.CharField(
        max_length=50,
        verbose_name=_('Name'),
        help_text=_('Unit name'),
        unique=True,
        blank=False,
    )

    symbol = models.CharField(
        max_length=10,
        verbose_name=_('Symbol'),
        help_text=_('Optional unit symbol'),
        blank=True,
    )

    definition = models.CharField(
        max_length=50,
        verbose_name=_('Definition'),
        help_text=_('Unit definition'),
        blank=False,
    )


@receiver(post_save, sender=CustomUnit, dispatch_uid='custom_unit_saved')
@receiver(post_delete, sender=CustomUnit, dispatch_uid='custom_unit_deleted')
def after_custom_unit_updated(sender, instance, **kwargs):
    """Callback when a custom unit is updated or deleted."""
    # Force reload of the unit registry
    from InvenTree.conversion import reload_unit_registry

    reload_unit_registry()


def rename_attachment(instance, filename: str):
    """Callback function to rename an uploaded attachment file.

    Args:
        instance (Attachment): The Attachment instance for which the file is being renamed.
        filename (str): The original filename of the uploaded file.

    Returns:
        str: The new filename for the uploaded file, e.g. 'attachments/<model_type>/<model_id>/<filename>'.
    """
    # Remove any illegal characters from the filename
    illegal_chars = '\'"\\`~#|!@#$%^&*()[]{}<>?;:+=,'

    for c in illegal_chars:
        filename = filename.replace(c, '')

    filename = os.path.basename(filename)

    # Generate a new filename for the attachment
    return os.path.join(
        'attachments', str(instance.model_type), str(instance.model_id), filename
    )


class Attachment(InvenTree.models.MetadataMixin, InvenTree.models.InvenTreeModel):
    """Class which represents an uploaded file attachment.

    An attachment can be either an uploaded file, or an external URL.

    Attributes:
        model_type: The type of model to which this attachment is linked
        model_id: The ID of the model to which this attachment is linked
        attachment: The uploaded file
        url: An external URL
        comment: A comment or description for the attachment
        user: The user who uploaded the attachment
        upload_date: The date the attachment was uploaded
        file_size: The size of the uploaded file
        metadata: Arbitrary metadata for the attachment (inherit from MetadataMixin)
        tags: Tags for the attachment
    """

    class Meta:
        """Metaclass options."""

        verbose_name = _('Attachment')

    class ModelChoices(RenderChoices):
        """Model choices for attachments."""

        choice_fnc = common.validators.attachment_model_options

    def save(self, *args, **kwargs):
        """Custom 'save' method for the Attachment model.

        - Record the file size of the uploaded attachment (if applicable)
        - Ensure that the 'content_type' and 'object_id' fields are set
        - Run extra validations
        """
        # Either 'attachment' or 'link' must be specified!
        if not self.attachment and not self.link:
            raise ValidationError({
                'attachment': _('Missing file'),
                'link': _('Missing external link'),
            })

        if self.attachment:
            if self.attachment.name.lower().endswith('.svg'):
                self.attachment.file.file = self.clean_svg(self.attachment)
        else:
            self.file_size = 0

        super().save(*args, **kwargs)

        # Update file size
        if self.file_size == 0 and self.attachment:
            # Get file size
            if default_storage.exists(self.attachment.name):
                try:
                    self.file_size = default_storage.size(self.attachment.name)
                except Exception:
                    pass

            if self.file_size != 0:
                super().save()

    def clean_svg(self, field):
        """Sanitize SVG file before saving."""
        cleaned = sanitize_svg(field.file.read())
        return BytesIO(bytes(cleaned, 'utf8'))

    def __str__(self):
        """Human name for attachment."""
        if self.attachment is not None:
            return os.path.basename(self.attachment.name)
        return str(self.link)

    model_type = models.CharField(
        max_length=100,
        validators=[common.validators.validate_attachment_model_type],
        verbose_name=_('Model type'),
        help_text=_('Target model type for image'),
    )

    model_id = models.PositiveIntegerField()

    attachment = models.FileField(
        upload_to=rename_attachment,
        verbose_name=_('Attachment'),
        help_text=_('Select file to attach'),
        blank=True,
        null=True,
    )

    link = InvenTree.fields.InvenTreeURLField(
        blank=True,
        null=True,
        verbose_name=_('Link'),
        help_text=_('Link to external URL'),
        max_length=2000,
    )

    comment = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Comment'),
        help_text=_('Attachment comment'),
    )

    upload_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    upload_date = models.DateField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name=_('Upload date'),
        help_text=_('Date the file was uploaded'),
    )

    file_size = models.PositiveIntegerField(
        default=0, verbose_name=_('File size'), help_text=_('File size in bytes')
    )

    tags = TaggableManager(blank=True)

    @property
    def basename(self):
        """Base name/path for attachment."""
        if self.attachment:
            return os.path.basename(self.attachment.name)
        return None

    def fully_qualified_url(self):
        """Return a 'fully qualified' URL for this attachment.

        - If the attachment is a link to an external resource, return the link
        - If the attachment is an uploaded file, return the fully qualified media URL
        """
        if self.link:
            return self.link

        if self.attachment:
            import InvenTree.helpers_model

            media_url = InvenTree.helpers.getMediaUrl(self.attachment)
            return InvenTree.helpers_model.construct_absolute_url(media_url)

        return ''

    def check_permission(self, permission, user):
        """Check if the user has the required permission for this attachment."""
        from InvenTree.models import InvenTreeAttachmentMixin

        model_class = common.validators.attachment_model_class_from_label(
            self.model_type
        )

        if not issubclass(model_class, InvenTreeAttachmentMixin):
            raise ValidationError(_('Invalid model type specified for attachment'))

        return model_class.check_related_permission(permission, user)


class InvenTreeCustomUserStateModel(models.Model):
    """Custom model to extends any registered state with extra custom, user defined states.

    Fields:
        reference_status: Status set that is extended with this custom state
        logical_key: State logical key that is equal to this custom state in business logic
        key: Numerical value that will be saved in the models database
        name: Name of the state (must be uppercase and a valid variable identifier)
        label: Label that will be displayed in the frontend (human readable)
        color: Color that will be displayed in the frontend

    """

    class Meta:
        """Metaclass options for this mixin."""

        verbose_name = _('Custom State')
        verbose_name_plural = _('Custom States')
        unique_together = [('reference_status', 'key'), ('reference_status', 'name')]

    reference_status = models.CharField(
        max_length=250,
        verbose_name=_('Reference Status Set'),
        help_text=_('Status set that is extended with this custom state'),
    )

    logical_key = models.IntegerField(
        verbose_name=_('Logical Key'),
        help_text=_(
            'State logical key that is equal to this custom state in business logic'
        ),
    )

    key = models.IntegerField(
        verbose_name=_('Value'),
        help_text=_('Numerical value that will be saved in the models database'),
    )

    name = models.CharField(
        max_length=250,
        verbose_name=_('Name'),
        help_text=_('Name of the state'),
        validators=[
            common.validators.validate_uppercase,
            common.validators.validate_variable_string,
        ],
    )

    label = models.CharField(
        max_length=250,
        verbose_name=_('Label'),
        help_text=_('Label that will be displayed in the frontend'),
    )

    color = models.CharField(
        max_length=10,
        choices=state_color_mappings(),
        default=ColorEnum.secondary.value,
        verbose_name=_('Color'),
        help_text=_('Color that will be displayed in the frontend'),
    )

    model = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Model'),
        help_text=_('Model this state is associated with'),
    )

    def __str__(self) -> str:
        """Return string representation of the custom state."""
        return f'{self.model.name} ({self.reference_status}): {self.name} | {self.key} ({self.logical_key})'

    def save(self, *args, **kwargs) -> None:
        """Ensure that the custom state is valid before saving."""
        self.clean()
        return super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate custom state data."""
        if self.model is None:
            raise ValidationError({'model': _('Model must be selected')})

        if self.key is None:
            raise ValidationError({'key': _('Key must be selected')})

        if self.logical_key is None:
            raise ValidationError({'logical_key': _('Logical key must be selected')})

        # Ensure that the key is not the same as the logical key
        if self.key == self.logical_key:
            raise ValidationError({'key': _('Key must be different from logical key')})

        # Check against the reference status class
        status_class = self.get_status_class()

        if not status_class:
            raise ValidationError({
                'reference_status': _('Valid reference status class must be provided')
            })

        if self.key in status_class.values():
            raise ValidationError({
                'key': _(
                    'Key must be different from the logical keys of the reference status'
                )
            })

        if self.logical_key not in status_class.values():
            raise ValidationError({
                'logical_key': _(
                    'Logical key must be in the logical keys of the reference status'
                )
            })

        if self.name in status_class.names():
            raise ValidationError({
                'name': _(
                    'Name must be different from the names of the reference status'
                )
            })

        return super().clean()

    def get_status_class(self):
        """Return the appropriate status class for this custom state."""
        from generic.states import StatusCode
        from InvenTree.helpers import inheritors

        if not self.reference_status:
            return None

        # Return the first class that matches the reference status
        for cls in inheritors(StatusCode):
            if cls.__name__ == self.reference_status:
                return cls


class SelectionList(InvenTree.models.MetadataMixin, InvenTree.models.InvenTreeModel):
    """Class which represents a list of selectable items for parameters.

    A lists selection options can be either manually defined, or sourced from a plugin.

    Attributes:
        name: The name of the selection list
        description: A description of the selection list
        locked: Is this selection list locked (i.e. cannot be modified)?
        active: Is this selection list active?
        source_plugin: The plugin which provides the selection list
        source_string: The string representation of the selection list
        default: The default value for the selection list
        created: The date/time that the selection list was created
        last_updated: The date/time that the selection list was last updated
    """

    class Meta:
        """Meta options for SelectionList."""

        verbose_name = _('Selection List')
        verbose_name_plural = _('Selection Lists')

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Name of the selection list'),
        unique=True,
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Description of the selection list'),
        blank=True,
    )

    locked = models.BooleanField(
        default=False,
        verbose_name=_('Locked'),
        help_text=_('Is this selection list locked?'),
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Can this selection list be used?'),
    )

    source_plugin = models.ForeignKey(
        'plugin.PluginConfig',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Source Plugin'),
        help_text=_('Plugin which provides the selection list'),
    )

    source_string = models.CharField(
        max_length=1000,
        verbose_name=_('Source String'),
        help_text=_('Optional string identifying the source used for this list'),
        blank=True,
    )

    default = models.ForeignKey(
        'SelectionListEntry',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Default Entry'),
        help_text=_('Default entry for this selection list'),
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created'),
        help_text=_('Date and time that the selection list was created'),
    )

    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Updated'),
        help_text=_('Date and time that the selection list was last updated'),
    )

    def __str__(self):
        """Return string representation of the selection list."""
        if not self.active:
            return f'{self.name} (Inactive)'
        return self.name

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SelectionList model."""
        return reverse('api-selectionlist-list')

    def get_choices(self):
        """Return the choices for the selection list."""
        choices = self.entries.filter(active=True)
        return [c.value for c in choices]


class SelectionListEntry(models.Model):
    """Class which represents a single entry in a SelectionList.

    Attributes:
        list: The SelectionList to which this entry belongs
        value: The value of the selection list entry
        label: The label for the selection list entry
        description: A description of the selection list entry
        active: Is this selection list entry active?
    """

    class Meta:
        """Meta options for SelectionListEntry."""

        verbose_name = _('Selection List Entry')
        verbose_name_plural = _('Selection List Entries')
        unique_together = [['list', 'value']]

    list = models.ForeignKey(
        SelectionList,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='entries',
        verbose_name=_('Selection List'),
        help_text=_('Selection list to which this entry belongs'),
    )

    value = models.CharField(
        max_length=255,
        verbose_name=_('Value'),
        help_text=_('Value of the selection list entry'),
    )

    label = models.CharField(
        max_length=255,
        verbose_name=_('Label'),
        help_text=_('Label for the selection list entry'),
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Description of the selection list entry'),
        blank=True,
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Is this selection list entry active?'),
    )

    def __str__(self):
        """Return string representation of the selection list entry."""
        if not self.active:
            return f'{self.label} (Inactive)'
        return self.label


class ParameterTemplate(
    InvenTree.models.MetadataMixin, InvenTree.models.InvenTreeModel
):
    """A ParameterTemplate provides a template for defining parameter values against various models.

    This allow for assigning arbitrary data fields against existing models,
    extending their functionality beyond the built-in fields.

    Attributes:
        name: The name (key) of the template
        description: A description of the template
        model_type: The type of model to which this template applies (e.g. 'part')
        units: The units associated with the template (if applicable)
        checkbox: Is this template a checkbox (boolean) type?
        choices: Comma-separated list of choices (if applicable)
        selectionlist: Optional link to a SelectionList for this template
        enabled: Is this template enabled?
    """

    class Meta:
        """Metaclass options for the ParameterTemplate model."""

        verbose_name = _('Parameter Template')
        verbose_name_plural = _('Parameter Templates')

        # Note: Data was migrated from the existing 'part_partparametertemplate' table
        # Ref: https://github.com/inventree/InvenTree/pull/10699
        # To avoid data loss, we retain the existing table name
        db_table = 'part_partparametertemplate'

    class ModelChoices(RenderChoices):
        """Model choices for parameters."""

        choice_fnc = common.validators.parameter_template_model_options

    @staticmethod
    def get_api_url() -> str:
        """Return the API URL associated with the ParameterTemplate model."""
        return reverse('api-parameter-template-list')

    def __str__(self):
        """Return a string representation of a ParameterTemplate instance."""
        s = str(self.name)
        if self.units:
            s += f' ({self.units})'
        return s

    def clean(self):
        """Custom cleaning step for this model.

        Checks:
        - A 'checkbox' field cannot have 'choices' set
        - A 'checkbox' field cannot have 'units' set
        """
        super().clean()

        # Check that checkbox parameters do not have units or choices
        if self.checkbox:
            if self.units:
                raise ValidationError({
                    'units': _('Checkbox parameters cannot have units')
                })

            if self.choices:
                raise ValidationError({
                    'choices': _('Checkbox parameters cannot have choices')
                })

        # Check that 'choices' are in fact valid
        if self.choices is None:
            self.choices = ''
        else:
            self.choices = str(self.choices).strip()

        if self.choices:
            choice_set = set()

            for choice in self.choices.split(','):
                choice = choice.strip()

                # Ignore empty choices
                if not choice:
                    continue

                if choice in choice_set:
                    raise ValidationError({'choices': _('Choices must be unique')})

                choice_set.add(choice)

    def validate_unique(self, exclude=None):
        """Ensure that ParameterTemplates cannot be created with the same name.

        This test should be case-insensitive (which the unique caveat does not cover).
        """
        super().validate_unique(exclude)

        try:
            others = ParameterTemplate.objects.filter(name__iexact=self.name).exclude(
                pk=self.pk
            )

            if others.exists():
                msg = _('Parameter template name must be unique')
                raise ValidationError({'name': msg})
        except ParameterTemplate.DoesNotExist:
            pass

    def get_choices(self):
        """Return a list of choices for this parameter template."""
        if self.selectionlist:
            return self.selectionlist.get_choices()

        if not self.choices:
            return []

        return [x.strip() for x in self.choices.split(',') if x.strip()]

    # TODO: Reintroduce validator for model_type
    model_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Model type'),
        help_text=_('Target model type for this parameter template'),
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Parameter Name'),
        unique=True,
    )

    units = models.CharField(
        max_length=25,
        verbose_name=_('Units'),
        help_text=_('Physical units for this parameter'),
        blank=True,
        validators=[InvenTree.validators.validate_physical_units],
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Parameter description'),
        blank=True,
    )

    checkbox = models.BooleanField(
        default=False,
        verbose_name=_('Checkbox'),
        help_text=_('Is this parameter a checkbox?'),
    )

    choices = models.CharField(
        max_length=5000,
        verbose_name=_('Choices'),
        help_text=_('Valid choices for this parameter (comma-separated)'),
        blank=True,
    )

    selectionlist = models.ForeignKey(
        SelectionList,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='templates',
        verbose_name=_('Selection List'),
        help_text=_('Selection list for this parameter'),
    )

    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
        help_text=_('Is this parameter template enabled?'),
    )


@receiver(
    post_save, sender=ParameterTemplate, dispatch_uid='post_save_parameter_template'
)
def post_save_parameter_template(sender, instance, created, **kwargs):
    """Callback function when a ParameterTemplate is created or saved."""
    import common.tasks

    if InvenTree.ready.canAppAccessDatabase() and not InvenTree.ready.isImportingData():
        if not created:
            # Schedule a background task to rebuild the parameters against this template
            InvenTree.tasks.offload_task(
                common.tasks.rebuild_parameters,
                instance.pk,
                force_async=True,
                group='part',
            )


class Parameter(
    UpdatedUserMixin, InvenTree.models.MetadataMixin, InvenTree.models.InvenTreeModel
):
    """Class which represents a parameter value assigned to a particular model instance.

    Attributes:
        model_type: The type of model to which this parameter is linked
        model_id: The ID of the model to which this parameter is linked
        template: The ParameterTemplate which defines this parameter
        data: The value of the parameter [string]
        data_numeric: Numeric value of the parameter (if applicable) [float]
        note: Optional note associated with this parameter [string]
        updated: Date/time that this parameter was last updated
        updated_by: User who last updated this parameter
    """

    class Meta:
        """Meta options for Parameter model."""

        verbose_name = _('Parameter')
        verbose_name_plural = _('Parameters')
        unique_together = [['model_type', 'model_id', 'template']]
        indexes = [models.Index(fields=['model_type', 'model_id'])]

        # Note: Data was migrated from the existing 'part_partparameter' table
        # Ref: https://github.com/inventree/InvenTree/pull/10699
        # To avoid data loss, we retain the existing table name
        db_table = 'part_partparameter'

    class ModelChoices(RenderChoices):
        """Model choices for parameters."""

        choice_fnc = common.validators.parameter_model_options

    @staticmethod
    def get_api_url() -> str:
        """Return the API URL associated with the Parameter model."""
        return reverse('api-parameter-list')

    def save(self, *args, **kwargs):
        """Custom save method for Parameter model.

        - Update the numeric data field (if applicable)
        """
        self.calculate_numeric_value()

        # Convert 'boolean' values to 'True' / 'False'
        if self.template.checkbox:
            self.data = InvenTree.helpers.str2bool(self.data)
            self.data_numeric = 1 if self.data else 0

        self.check_save()
        super().save(*args, **kwargs)

    def delete(self):
        """Perform custom delete checks before deleting a Parameter instance."""
        self.check_delete()
        super().delete()

    def clean(self):
        """Validate the Parameter before saving to the database."""
        super().clean()

        # Validate the parameter data against the template choices
        if choices := self.template.get_choices():
            if self.data not in choices:
                raise ValidationError({'data': _('Invalid choice for parameter value')})

        self.calculate_numeric_value()

        # TODO: Check that the model_type for this parameter matches the template

        # Validate the parameter data against the template units
        if (
            get_global_setting(
                'PARAMETER_ENFORCE_UNITS', True, cache=False, create=False
            )
            and self.template.units
        ):
            try:
                InvenTree.conversion.convert_physical_value(
                    self.data, self.template.units
                )
            except ValidationError as e:
                raise ValidationError({'data': e.message})

        # Finally, run custom validation checks (via plugins)
        from plugin import PluginMixinEnum, registry

        for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
            # Note: The validate_parameter function may raise a ValidationError
            try:
                if hasattr(plugin, 'validate_parameter'):
                    result = plugin.validate_parameter(self, self.data)
                    if result:
                        break
            except ValidationError as exc:
                # Re-throw the ValidationError against the 'data' field
                raise ValidationError({'data': exc.message})
            except Exception:
                InvenTree.exceptions.log_error('validate_parameter', plugin=plugin.slug)

    def calculate_numeric_value(self):
        """Calculate a numeric value for the parameter data.

        - If a 'units' field is provided, then the data will be converted to the base SI unit.
        - Otherwise, we'll try to do a simple float cast
        """
        if self.template.units:
            try:
                self.data_numeric = InvenTree.conversion.convert_physical_value(
                    self.data, self.template.units
                )
            except (ValidationError, ValueError):
                self.data_numeric = None

        # No units provided, so try to cast to a float
        else:
            try:
                self.data_numeric = float(self.data)
            except ValueError:
                self.data_numeric = None

        if self.data_numeric is not None and type(self.data_numeric) is float:
            # Prevent out of range numbers, etc
            # Ref: https://github.com/inventree/InvenTree/issues/7593
            if math.isnan(self.data_numeric) or math.isinf(self.data_numeric):
                self.data_numeric = None

    def check_permission(self, permission, user):
        """Check if the user has the required permission for this parameter."""
        from InvenTree.models import InvenTreeParameterMixin

        model_class = self.model_type.model_class()

        if not issubclass(model_class, InvenTreeParameterMixin):
            raise ValidationError(_('Invalid model type specified for parameter'))

        return model_class.check_related_permission(permission, user)

    def check_save(self):
        """Check if this parameter can be saved.

        The linked content_object can implement custom checks by overriding
        the 'check_parameter_edit' method.
        """
        from InvenTree.models import InvenTreeParameterMixin

        try:
            instance = self.content_object
        except InvenTree.models.InvenTreeModel.DoesNotExist:
            return

        if instance and isinstance(instance, InvenTreeParameterMixin):
            instance.check_parameter_save(self)

    def check_delete(self):
        """Check if this parameter can be deleted."""
        from InvenTree.models import InvenTreeParameterMixin

        try:
            instance = self.content_object
        except InvenTree.models.InvenTreeModel.DoesNotExist:
            return

        if instance and isinstance(instance, InvenTreeParameterMixin):
            instance.check_parameter_delete(self)

    # TODO: Reintroduce validator for model_type
    model_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    model_id = models.PositiveIntegerField(
        verbose_name=_('Model ID'),
        help_text=_('ID of the target model for this parameter'),
    )

    content_object = GenericForeignKey('model_type', 'model_id')

    template = models.ForeignKey(
        ParameterTemplate,
        on_delete=models.CASCADE,
        related_name='parameters',
        verbose_name=_('Template'),
        help_text=_('Parameter template'),
    )

    data = models.CharField(
        max_length=500,
        verbose_name=_('Data'),
        help_text=_('Parameter Value'),
        validators=[MinLengthValidator(1)],
    )

    data_numeric = models.FloatField(default=None, null=True, blank=True)

    note = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Note'),
        help_text=_('Optional note field'),
    )

    @property
    def units(self):
        """Return the units associated with the template."""
        return self.template.units

    @property
    def name(self):
        """Return the name of the template."""
        return self.template.name

    @property
    def description(self):
        """Return the description of the template."""
        return self.template.description


class BarcodeScanResult(InvenTree.models.InvenTreeModel):
    """Model for storing barcode scans results."""

    BARCODE_SCAN_MAX_LEN = 250

    class Meta:
        """Model meta options."""

        verbose_name = _('Barcode Scan')

    data = models.CharField(
        max_length=BARCODE_SCAN_MAX_LEN,
        verbose_name=_('Data'),
        help_text=_('Barcode data'),
        blank=False,
        null=False,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('User'),
        help_text=_('User who scanned the barcode'),
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp'),
        help_text=_('Date and time of the barcode scan'),
    )

    endpoint = models.CharField(
        max_length=250,
        verbose_name=_('Path'),
        help_text=_('URL endpoint which processed the barcode'),
        blank=True,
        null=True,
    )

    context = models.JSONField(
        max_length=1000,
        verbose_name=_('Context'),
        help_text=_('Context data for the barcode scan'),
        blank=True,
        null=True,
    )

    response = models.JSONField(
        max_length=1000,
        verbose_name=_('Response'),
        help_text=_('Response data from the barcode scan'),
        blank=True,
        null=True,
    )

    result = models.BooleanField(
        verbose_name=_('Result'),
        help_text=_('Was the barcode scan successful?'),
        default=False,
    )


class DataOutput(models.Model):
    """Model for storing generated data output from various processes.

    This model is intended for storing data files which are generated by various processes,
    and need to be retained for future use (e.g. download by the user).

    Attributes:
        created: Date and time that the data output was created
        user: User who created the data output (if applicable)
        total: Total number of items / records in the data output
        progress: Current progress of the data output generation process
        complete: Has the data output generation process completed?
        output_type: The type of data output generated (e.g. 'label', 'report', etc)
        template_name: Name of the template used to generate the data output (if applicable)
        plugin: Key for the plugin which generated the data output (if applicable)
        output: File field for storing the generated file
        errors: JSON field for storing any errors generated during the data output generation process
    """

    class DataOutputTypes(StringEnum):
        """Enum for data output types."""

        LABEL = 'label'
        REPORT = 'report'
        EXPORT = 'export'

    created = models.DateField(auto_now_add=True, editable=False)

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name='+'
    )

    total = models.PositiveIntegerField(default=1)

    progress = models.PositiveIntegerField(default=0)

    complete = models.BooleanField(default=False)

    output_type = models.CharField(max_length=100, blank=True, null=True)

    template_name = models.CharField(max_length=100, blank=True, null=True)

    plugin = models.CharField(max_length=100, blank=True, null=True)

    output = models.FileField(upload_to='data_output', blank=True, null=True)

    errors = models.JSONField(blank=True, null=True)

    def mark_complete(self, progress: int = 100, output: Optional[ContentFile] = None):
        """Mark the data output generation process as complete.

        Arguments:
            progress (int, optional): Progress percentage of the data output generation. Defaults to 100.
            output (ContentFile, optional): The generated output file. Defaults to None.
        """
        self.complete = True
        self.progress = progress
        self.output = output
        self.save()

    def mark_failure(
        self, error: Optional[str] = None, error_dict: Optional[dict] = None
    ):
        """Log an error message to the errors field.

        Arguments:
            error (str, optional): Error message to log. Defaults to None.
            error_dict (dict): Dictionary containing error messages. Defaults to None.
        """
        self.complete = False
        self.output = None

        if error_dict is not None:
            self.errors = error_dict
        elif error is not None:
            self.errors = {'error': str(error)}
        else:
            self.errors = {'error': str(_('An error occurred'))}

        self.save()


# region Email
class Priority(models.IntegerChoices):
    """Enumeration for defining email priority levels."""

    NONE = 0
    VERY_HIGH = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    VERY_LOW = 5


HEADER_PRIORITY = 'X-Priority'
HEADER_MSG_ID = 'Message-ID'

del_error_msg = _(
    'INVE-E8: Email log deletion is protected. Set INVENTREE_PROTECT_EMAIL_LOG to False to allow deletion.'
)


class NoDeleteQuerySet(models.query.QuerySet):
    """Custom QuerySet to prevent deletion of EmailLog entries."""

    def delete(self):
        """Override delete method to prevent deletion of EmailLog entries."""
        if get_global_setting('INVENTREE_PROTECT_EMAIL_LOG'):
            raise ValidationError(del_error_msg)
        super().delete()


class NoDeleteManager(models.Manager):
    """Custom Manager to use NoDeleteQuerySet."""

    def get_queryset(self):
        """Return a NoDeleteQuerySet."""
        return NoDeleteQuerySet(self.model, using=self._db)


class EmailMessage(models.Model):
    """Model for storing email messages sent or received by the system.

    Attributes:
        global_id: Unique identifier for the email message
        message_id_key: Identifier for the email message - might be supplied by external system
        thread_id_key: Identifier of thread - might be supplied by external system
        subject: Subject of the email message
        body: Body of the email message
        to: Recipient of the email message
        sender: Sender of the email message
        status: Status of the email message (e.g. 'sent', 'failed', etc)
        timestamp: Date and time that the email message left the system or was received by the system
        headers: Headers of the email message
        full_message: Full email message content
        direction: Direction of the email message (e.g. 'inbound', 'outbound')
        error_code: Error code (if applicable)
        error_message: Error message (if applicable)
        error_timestamp: Date and time of the error (if applicable)
        delivery_options: Delivery options for the email message
    """

    class Meta:
        """Meta options for EmailMessage."""

        verbose_name = _('Email Message')
        verbose_name_plural = _('Email Messages')

    class EmailStatus(models.TextChoices):
        """Machine setting config type enum."""

        ANNOUNCED = (
            'A',
            _('Announced'),
        )  # Intend to send mail was announced (saved in system, pushed to queue)
        SENT = 'S', _('Sent')  # Mail was sent to the email server
        FAILED = 'F', _('Failed')  # There was en error sending the email
        DELIVERED = (
            'D',
            _('Delivered'),
        )  # Mail was delivered to the recipient - this means we got some kind of feedback from the email server or user
        READ = (
            'R',
            _('Read'),
        )  # Mail was read by the recipient - this means we got some kind of feedback from the user
        CONFIRMED = (
            'C',
            _('Confirmed'),
        )  # Mail delivery was confirmed by the recipient explicitly

    class EmailDirection(models.TextChoices):
        """Email direction enum."""

        INBOUND = 'I', _('Inbound')
        OUTBOUND = 'O', _('Outbound')

    class DeliveryOptions(models.TextChoices):
        """Email delivery options enum."""

        NO_REPLY = 'no_reply', _('No Reply')
        TRACK_DELIVERY = 'track_delivery', _('Track Delivery')
        TRACK_READ = 'track_read', _('Track Read')
        TRACK_CLICK = 'track_click', _('Track Click')

    global_id = models.UUIDField(
        verbose_name=_('Global ID'),
        help_text=_('Unique identifier for this message'),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    message_id_key = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name=_('Message ID'),
        help_text=_(
            'Identifier for this message (might be supplied by external system)'
        ),
    )
    thread_id_key = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name=_('Thread ID'),
        help_text=_(
            'Identifier for this message thread (might be supplied by external system)'
        ),
    )
    thread = models.ForeignKey(
        'EmailThread',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='messages',
        verbose_name=_('Thread'),
        help_text=_('Linked thread for this message'),
    )
    subject = models.CharField(max_length=250, blank=False, null=False)
    body = models.TextField(blank=False, null=False)
    to = models.EmailField(blank=False, null=False)
    sender = models.EmailField(blank=False, null=False)
    status = models.CharField(
        max_length=50, blank=True, null=True, choices=EmailStatus.choices
    )
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    headers = models.JSONField(blank=True, null=True)
    # Additional info
    full_message = models.TextField(blank=True, null=True)
    direction = models.CharField(
        max_length=50, blank=True, null=True, choices=EmailDirection.choices
    )
    priority = models.IntegerField(verbose_name=_('Priority'), choices=Priority)
    delivery_options = models.JSONField(
        blank=True,
        null=True,
        # choices=DeliveryOptions.choices
    )
    # Optional tracking of delivery
    error_code = models.CharField(max_length=50, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    error_timestamp = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Ensure threads exist before saving the email message."""
        ret = super().save(*args, **kwargs)

        # Ensure thread is linked
        if not self.thread:
            thread, created = EmailThread.objects.get_or_create(
                key=self.thread_id_key, started_internal=True
            )
            self.thread = thread
            if created and not self.thread_id_key:
                self.thread_id_key = thread.global_id
            self.save()

        return ret

    objects = NoDeleteManager()

    def delete(self, *kwargs):
        """Delete entry - if not protected."""
        if get_global_setting('INVENTREE_PROTECT_EMAIL_LOG'):
            raise ValidationError(del_error_msg)
        return super().delete(*kwargs)


class EmailThread(InvenTree.models.InvenTreeMetadataModel):
    """Model for storing email threads."""

    class Meta:
        """Meta options for EmailThread."""

        verbose_name = _('Email Thread')
        verbose_name_plural = _('Email Threads')
        unique_together = [['key', 'global_id']]
        ordering = ['-updated']

    key = models.CharField(
        max_length=250,
        verbose_name=_('Key'),
        null=True,
        blank=True,
        help_text=_('Unique key for this thread (used to identify the thread)'),
    )
    global_id = models.UUIDField(
        verbose_name=_('Global ID'),
        help_text=_('Unique identifier for this thread'),
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    started_internal = models.BooleanField(
        default=False,
        verbose_name=_('Started Internal'),
        help_text=_('Was this thread started internally?'),
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created'),
        help_text=_('Date and time that the thread was created'),
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated'),
        help_text=_('Date and time that the thread was last updated'),
    )


def issue_mail(
    subject: str,
    body: str,
    from_email: str,
    recipients: str | list,
    fail_silently: bool = False,
    html_message=None,
    prio: Priority = Priority.NORMAL,
    headers: Optional[dict] = None,
):
    """Send an email with the specified subject and body, to the specified recipients list.

    Mostly used by tasks.
    """
    connection = get_connection(fail_silently=fail_silently)

    message = EmailMultiAlternatives(
        subject, body, from_email, recipients, connection=connection
    )
    if html_message:
        message.attach_alternative(html_message, 'text/html')

    # Add any extra headers
    if headers is not None:
        for key, value in headers.items():
            message.extra_headers[key] = value

    # Stabilize the message ID before creating the object
    if HEADER_MSG_ID not in message.extra_headers:
        message.extra_headers[HEADER_MSG_ID] = make_msgid(domain=DNS_NAME)

    # TODO add `References` field for the thread ID

    # Add headers for flags
    message.extra_headers[HEADER_PRIORITY] = str(prio)

    # And now send
    return message.send()


def log_email_messages(email_messages) -> list[EmailMessage]:
    """Log email messages to the database.

    Args:
        email_messages (list): List of email messages to log.
    """
    instance_id = inventree_identifier(True)

    msg_ids = []
    for msg in email_messages:
        try:
            new_obj = EmailMessage.objects.create(
                message_id_key=msg.extra_headers.get(HEADER_MSG_ID),
                subject=msg.subject,
                body=msg.body,
                to=msg.to,
                sender=msg.from_email,
                status=EmailMessage.EmailStatus.ANNOUNCED,
                direction=EmailMessage.EmailDirection.OUTBOUND,
                priority=msg.extra_headers.get(HEADER_PRIORITY, '3'),
                headers=msg.extra_headers,
                full_message=msg,
            )
            msg_ids.append(new_obj)

            # Add InvenTree specific headers to the message to help with identification if we see mails again
            msg.extra_headers['X-InvenTree-MsgId-1'] = str(new_obj.global_id)
            msg.extra_headers['X-InvenTree-ThreadId-1'] = str(new_obj.thread.global_id)
            msg.extra_headers['X-InvenTree-Instance-1'] = str(instance_id)
        except Exception as exc:  # pragma: no cover
            logger.error(f' INVE-W10: Failed to log email message: {exc}')
    return msg_ids


@receiver(inbound)
def handle_inbound(sender, event, esp_name, **kwargs):
    """Handle inbound email messages from anymail."""
    message = event.message

    r_to = message.envelope_recipient or [a.addr_spec for a in message.to]
    r_sender = message.envelope_sender or message.from_email.addr_spec

    msg = EmailMessage.objects.create(
        message_id_key=event.message[HEADER_MSG_ID],
        subject=message.subject,
        body=message.text,
        to=r_to,
        sender=r_sender,
        status=EmailMessage.EmailStatus.READ,
        direction=EmailMessage.EmailDirection.INBOUND,
        priority=Priority.NONE,
        timestamp=message.date,
        headers=message._headers,
        full_message=message.html,
    )

    # Schedule a task to process the email message
    from plugin.base.mail.mail import process_mail_in

    InvenTree.tasks.offload_task(process_mail_in, mail_id=msg.pk, group='mail')


@receiver(tracking)
def handle_event(sender, event, esp_name, **kwargs):
    """Handle tracking events from anymail."""
    try:
        email = EmailMessage.objects.get(message_id_key=event.message_id)

        if event.event_type == 'delivered':
            email.status = EmailMessage.EmailStatus.DELIVERED
        elif event.event_type == 'opened':
            email.status = EmailMessage.EmailStatus.READ
        elif event.event_type == 'clicked':
            email.status = EmailMessage.EmailStatus.CONFIRMED
        elif event.event_type == 'sent':
            email.status = EmailMessage.EmailStatus.SENT
        elif event.event_type == 'unknown':
            email.error_message = event.esp_event
        else:
            if event.event_type in ('queued', 'deferred'):
                # We ignore these
                return True
            else:
                email.status = EmailMessage.EmailStatus.FAILED
                email.error_code = event.event_type
                email.error_message = event.esp_event
                email.error_timestamp = event.timestamp
        email.save()
        return True
    except EmailMessage.DoesNotExist:
        return False
    except Exception as exc:  # pragma: no cover
        logger.error(f' INVE-W10: Failed to handle tracking event: {exc}')
        return False


# endregion Email

# region tracing for django q
if TRACE_PROC:  # pragma: no cover

    @receiver(post_spawn)
    def spawn_callback(sender, proc_name, **kwargs):
        """Callback to patch in tracing support."""
        TRACE_PROV.add_span_processor(TRACE_PROC)
        trace.set_tracer_provider(TRACE_PROV)
        trace.get_tracer(__name__)

# endregion
