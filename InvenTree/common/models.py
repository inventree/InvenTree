"""Common database model definitions.

These models are 'generic' and do not fit a particular business logic object.
"""

import base64
import decimal
import hashlib
import hmac
import json
import logging
import math
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from secrets import compare_digest
from typing import Any, Callable, TypedDict, Union

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.cache import cache
from django.core.exceptions import AppRegistryNotReady, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models, transaction
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.settings import CURRENCY_CHOICES
from rest_framework.exceptions import PermissionDenied

import build.validators
import InvenTree.fields
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import InvenTree.validators
import order.validators
import report.helpers
import users.models
from plugin import registry

logger = logging.getLogger('inventree')


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


class BaseURLValidator(URLValidator):
    """Validator for the InvenTree base URL.

    Rules:
    - Allow empty value
    - Allow value without specified TLD (top level domain)
    """

    def __init__(self, schemes=None, **kwargs):
        """Custom init routine."""
        super().__init__(schemes, **kwargs)

        # Override default host_re value - allow optional tld regex
        self.host_re = (
            '('
            + self.hostname_re
            + self.domain_re
            + f'({self.tld_re})?'
            + '|localhost)'
        )

    def __call__(self, value):
        """Make sure empty values pass."""
        value = str(value).strip()

        # If a configuration level value has been specified, prevent change
        if settings.SITE_URL:
            raise ValidationError(_('Site URL is locked by configuration'))

        if len(value) == 0:
            pass

        else:
            super().__call__(value)


class ProjectCode(InvenTree.models.InvenTreeMetadataModel):
    """A ProjectCode is a unique identifier for a project."""

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


class SettingsKeyType(TypedDict, total=False):
    """Type definitions for a SettingsKeyType.

    Attributes:
        name: Translatable string name of the setting (required)
        description: Translatable string description of the setting (required)
        units: Units of the particular setting (optional)
        validator: Validation function/list of functions for the setting (optional, default: None, e.g: bool, int, str, MinValueValidator, ...)
        default: Default value or function that returns default value (optional)
        choices: Function that returns or value of list[tuple[str: key, str: display value]] (optional)
        hidden: Hide this setting from settings page (optional)
        before_save: Function that gets called after save with *args, **kwargs (optional)
        after_save: Function that gets called after save with *args, **kwargs (optional)
        protected: Protected values are not returned to the client, instead "***" is returned (optional, default: False)
        required: Is this setting required to work, can be used in combination with .check_all_settings(...) (optional, default: False)
        model: Auto create a dropdown menu to select an associated model instance (e.g. 'company.company', 'auth.user' and 'auth.group' are possible too, optional)
    """

    name: str
    description: str
    units: str
    validator: Union[Callable, list[Callable], tuple[Callable]]
    default: Union[Callable, Any]
    choices: Union[list[tuple[str, str]], Callable[[], list[tuple[str, str]]]]
    hidden: bool
    before_save: Callable[..., None]
    after_save: Callable[..., None]
    protected: bool
    required: bool
    model: str


class BaseInvenTreeSetting(models.Model):
    """An base InvenTreeSetting object is a key:value pair used for storing single values (e.g. one-off settings values).

    Attributes:
        SETTINGS: definition of all available settings
        extra_unique_fields: List of extra fields used to be unique, e.g. for PluginConfig -> plugin
    """

    SETTINGS: dict[str, SettingsKeyType] = {}

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

        # Execute after_save action
        self._call_settings_function('after_save', args, kwargs)

    @classmethod
    def build_default_values(cls, **kwargs):
        """Ensure that all values defined in SETTINGS are present in the database.

        If a particular setting is not present, create it with the default value
        """
        cache_key = f'BUILD_DEFAULT_VALUES:{str(cls.__name__)}'

        if InvenTree.helpers.str2bool(cache.get(cache_key, False)):
            # Already built default values
            return

        try:
            existing_keys = cls.objects.filter(**kwargs).values_list('key', flat=True)
            settings_keys = cls.SETTINGS.keys()

            missing_keys = set(settings_keys) - set(existing_keys)

            if len(missing_keys) > 0:
                logger.info(
                    'Building %s default values for %s', len(missing_keys), str(cls)
                )
                cls.objects.bulk_create([
                    cls(key=key, value=cls.get_setting_default(key), **kwargs)
                    for key in missing_keys
                    if not key.startswith('_')
                ])
        except Exception as exc:
            logger.exception(
                'Failed to build default values for %s (%s)', str(cls), str(type(exc))
            )
            pass

        cache.set(cache_key, True, timeout=3600)

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
        ckey = self.cache_key

        # skip saving to cache if no pk is set
        if self.pk is None:
            return

        logger.debug("Saving setting '%s' to cache", ckey)

        try:
            cache.set(ckey, self, timeout=3600)
        except TypeError:
            # Some characters cause issues with caching; ignore and move on
            pass

    @classmethod
    def create_cache_key(cls, setting_key, **kwargs):
        """Create a unique cache key for a particular setting object.

        The cache key uses the following elements to ensure the key is 'unique':
        - The name of the class
        - The unique KEY string
        - Any key:value kwargs associated with the particular setting type (e.g. user-id)
        """
        key = f'{str(cls.__name__)}:{setting_key}'

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
        settings_definition: Union[dict[str, SettingsKeyType], None] = None,
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
        settings_definition: Union[dict[str, SettingsKeyType], None] = None,
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
        settings_definition: Union[dict[str, SettingsKeyType], None] = None,
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

        First checks the cache to see if this object has recently been accessed,
        and returns the cached version if so.
        """
        key = str(key).strip().upper()

        filters = {
            'key__iexact': key,
            # Optionally filter by other keys
            **cls.get_filters(**kwargs),
        }

        # Unless otherwise specified, attempt to create the setting
        create = kwargs.pop('create', True)

        # Prevent saving to the database during data import
        if InvenTree.ready.isImportingData():
            create = False

        # Prevent saving to the database during migrations
        if InvenTree.ready.isRunningMigrations():
            create = False

        # Perform cache lookup by default
        do_cache = kwargs.pop('cache', True)

        ckey = cls.create_cache_key(key, **kwargs)

        if do_cache:
            try:
                # First attempt to find the setting object in the cache
                cached_setting = cache.get(ckey)

                if cached_setting is not None:
                    return cached_setting

            except AppRegistryNotReady:
                # Cache is not ready yet
                do_cache = False

        try:
            settings = cls.objects.all()
            setting = settings.filter(**filters).first()
        except (ValueError, cls.DoesNotExist):
            setting = None
        except (IntegrityError, OperationalError, ProgrammingError):
            setting = None

        # Setting does not exist! (Try to create it)
        if not setting:
            # Prevent creation of new settings objects when importing data
            if (
                InvenTree.ready.isImportingData()
                or not InvenTree.ready.canAppAccessDatabase(
                    allow_test=True, allow_shell=True
                )
            ):
                create = False

            if create:
                # Attempt to create a new settings object

                default_value = cls.get_setting_default(key, **kwargs)

                setting = cls(key=key, value=default_value, **kwargs)

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

        if setting and do_cache:
            # Cache this setting object
            setting.save_to_cache()

        return setting

    @classmethod
    def get_setting(cls, key, backup_value=None, **kwargs):
        """Get the value of a particular setting.

        If it does not exist, return the backup value (default = None)
        """
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
        if change_user is not None and not change_user.is_staff:
            return

        attempts = int(kwargs.get('attempts', 3))

        filters = {
            'key__iexact': key,
            # Optionally filter by other keys
            **cls.get_filters(**kwargs),
        }

        try:
            setting = cls.objects.get(**filters)
        except cls.DoesNotExist:
            if create:
                setting = cls(key=key, **kwargs)
            else:
                return
        except (OperationalError, ProgrammingError):
            if not key.startswith('_'):
                logger.warning("Database is locked, cannot set setting '%s'", key)
            # Likely the DB is locked - not much we can do here
            return
        except Exception as exc:
            logger.exception(
                "Error setting setting '%s' for %s: %s", key, str(cls), str(type(exc))
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
                    "Duplicate setting key '%s' for %s - trying again", key, str(cls)
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
            pass
        except Exception as exc:
            # Some other error
            logger.exception(
                "Error setting setting '%s' for %s: %s", key, str(cls), str(type(exc))
            )
            pass

    key = models.CharField(
        max_length=50,
        blank=False,
        unique=False,
        help_text=_('Settings key (must be unique - case insensitive)'),
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
            self.value = self.as_int()

        elif self.is_bool():
            self.value = self.as_bool()

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

        # If a list of validators is supplied, iterate through each one
        if type(validator) in [list, tuple]:
            for v in validator:
                self.run_validator(v)

        if callable(validator):
            # We can accept function validators with a single argument

            if self.is_bool():
                value = self.as_bool()

            if self.is_int():
                value = self.as_int()

            validator(value)

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

    def model_name(self):
        """Return the model name associated with this setting."""
        setting = self.get_setting_definition(
            self.key, **self.get_filters_for_instance()
        )

        return setting.get('model', None)

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

    def as_int(self):
        """Return the value of this setting converted to a boolean value.

        If an error occurs, return the default value
        """
        try:
            value = int(self.value)
        except (ValueError, TypeError):
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


def settings_group_options():
    """Build up group tuple for settings based on your choices."""
    return [('', _('No group')), *[(str(a.id), str(a)) for a in Group.objects.all()]]


def update_instance_url(setting):
    """Update the first site objects domain to url."""
    if not settings.SITE_MULTI:
        return

    try:
        from django.contrib.sites.models import Site
    except (ImportError, RuntimeError):
        # Multi-site support not enabled
        return

    site_obj = Site.objects.all().order_by('id').first()
    site_obj.domain = setting.value
    site_obj.save()


def update_instance_name(setting):
    """Update the first site objects name to instance name."""
    if not settings.SITE_MULTI:
        return

    try:
        from django.contrib.sites.models import Site
    except (ImportError, RuntimeError):
        # Multi-site support not enabled
        return

    site_obj = Site.objects.all().order_by('id').first()
    site_obj.name = setting.value
    site_obj.save()


def validate_email_domains(setting):
    """Validate the email domains setting."""
    if not setting.value:
        return

    domains = setting.value.split(',')
    for domain in domains:
        if not domain:
            raise ValidationError(_('An empty domain is not allowed.'))
        if not re.match(r'^@[a-zA-Z0-9\.\-_]+$', domain):
            raise ValidationError(_(f'Invalid domain name: {domain}'))


def currency_exchange_plugins():
    """Return a set of plugin choices which can be used for currency exchange."""
    try:
        from plugin import registry

        plugs = registry.with_mixin('currencyexchange', active=True)
    except Exception:
        plugs = []

    return [('', _('No plugin'))] + [(plug.slug, plug.human_name) for plug in plugs]


def after_change_currency(setting):
    """Callback function when base currency is changed.

    - Update exchange rates
    - Recalculate prices for all parts
    """
    if InvenTree.ready.isImportingData():
        return

    if not InvenTree.ready.canAppAccessDatabase():
        return

    from part import tasks as part_tasks

    # Immediately update exchange rates
    InvenTree.tasks.update_exchange_rates(force=True)

    # Offload update of part prices to a background task
    InvenTree.tasks.offload_task(part_tasks.check_missing_pricing, force_async=True)


def reload_plugin_registry(setting):
    """When a core plugin setting is changed, reload the plugin registry."""
    from plugin import registry

    logger.info("Reloading plugin registry due to change in setting '%s'", setting.key)

    registry.reload_plugins(full_reload=True, force_reload=True, collect=True)


class InvenTreeSettingsKeyType(SettingsKeyType):
    """InvenTreeSettingsKeyType has additional properties only global settings support.

    Attributes:
        requires_restart: If True, a server restart is required after changing the setting
    """

    requires_restart: bool


class InvenTreeSetting(BaseInvenTreeSetting):
    """An InvenTreeSetting object is a key:value pair used for storing single values (e.g. one-off settings values).

    The class provides a way of retrieving the value for a particular key,
    even if that key does not exist.
    """

    SETTINGS: dict[str, InvenTreeSettingsKeyType]

    class Meta:
        """Meta options for InvenTreeSetting."""

        verbose_name = 'InvenTree Setting'
        verbose_name_plural = 'InvenTree Settings'

    def save(self, *args, **kwargs):
        """When saving a global setting, check to see if it requires a server restart.

        If so, set the "SERVER_RESTART_REQUIRED" setting to True
        """
        super().save()

        if self.requires_restart() and not InvenTree.ready.isImportingData():
            InvenTreeSetting.set_setting('SERVER_RESTART_REQUIRED', True, None)

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

    SETTINGS = {
        'SERVER_RESTART_REQUIRED': {
            'name': _('Restart required'),
            'description': _(
                'A setting has been changed which requires a server restart'
            ),
            'default': False,
            'validator': bool,
            'hidden': True,
        },
        '_PENDING_MIGRATIONS': {
            'name': _('Pending migrations'),
            'description': _('Number of pending database migrations'),
            'default': 0,
            'validator': int,
        },
        'INVENTREE_INSTANCE': {
            'name': _('Server Instance Name'),
            'default': 'InvenTree',
            'description': _('String descriptor for the server instance'),
            'after_save': update_instance_name,
        },
        'INVENTREE_INSTANCE_TITLE': {
            'name': _('Use instance name'),
            'description': _('Use the instance name in the title-bar'),
            'validator': bool,
            'default': False,
        },
        'INVENTREE_RESTRICT_ABOUT': {
            'name': _('Restrict showing `about`'),
            'description': _('Show the `about` modal only to superusers'),
            'validator': bool,
            'default': False,
        },
        'INVENTREE_COMPANY_NAME': {
            'name': _('Company name'),
            'description': _('Internal company name'),
            'default': 'My company name',
        },
        'INVENTREE_BASE_URL': {
            'name': _('Base URL'),
            'description': _('Base URL for server instance'),
            'validator': BaseURLValidator(),
            'default': '',
            'after_save': update_instance_url,
        },
        'INVENTREE_DEFAULT_CURRENCY': {
            'name': _('Default Currency'),
            'description': _('Select base currency for pricing calculations'),
            'default': 'USD',
            'choices': CURRENCY_CHOICES,
            'after_save': after_change_currency,
        },
        'CURRENCY_UPDATE_INTERVAL': {
            'name': _('Currency Update Interval'),
            'description': _(
                'How often to update exchange rates (set to zero to disable)'
            ),
            'default': 1,
            'units': _('days'),
            'validator': [int, MinValueValidator(0)],
        },
        'CURRENCY_UPDATE_PLUGIN': {
            'name': _('Currency Update Plugin'),
            'description': _('Currency update plugin to use'),
            'choices': currency_exchange_plugins,
            'default': 'inventreecurrencyexchange',
        },
        'INVENTREE_DOWNLOAD_FROM_URL': {
            'name': _('Download from URL'),
            'description': _(
                'Allow download of remote images and files from external URL'
            ),
            'validator': bool,
            'default': False,
        },
        'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE': {
            'name': _('Download Size Limit'),
            'description': _('Maximum allowable download size for remote image'),
            'units': 'MB',
            'default': 1,
            'validator': [int, MinValueValidator(1), MaxValueValidator(25)],
        },
        'INVENTREE_DOWNLOAD_FROM_URL_USER_AGENT': {
            'name': _('User-agent used to download from URL'),
            'description': _(
                'Allow to override the user-agent used to download images and files from external URL (leave blank for the default)'
            ),
            'default': '',
        },
        'INVENTREE_STRICT_URLS': {
            'name': _('Strict URL Validation'),
            'description': _('Require schema specification when validating URLs'),
            'validator': bool,
            'default': True,
        },
        'INVENTREE_REQUIRE_CONFIRM': {
            'name': _('Require confirm'),
            'description': _('Require explicit user confirmation for certain action.'),
            'validator': bool,
            'default': True,
        },
        'INVENTREE_TREE_DEPTH': {
            'name': _('Tree Depth'),
            'description': _(
                'Default tree depth for treeview. Deeper levels can be lazy loaded as they are needed.'
            ),
            'default': 1,
            'validator': [int, MinValueValidator(0)],
        },
        'INVENTREE_UPDATE_CHECK_INTERVAL': {
            'name': _('Update Check Interval'),
            'description': _('How often to check for updates (set to zero to disable)'),
            'validator': [int, MinValueValidator(0)],
            'default': 7,
            'units': _('days'),
        },
        'INVENTREE_BACKUP_ENABLE': {
            'name': _('Automatic Backup'),
            'description': _('Enable automatic backup of database and media files'),
            'validator': bool,
            'default': False,
        },
        'INVENTREE_BACKUP_DAYS': {
            'name': _('Auto Backup Interval'),
            'description': _('Specify number of days between automated backup events'),
            'validator': [int, MinValueValidator(1)],
            'default': 1,
            'units': _('days'),
        },
        'INVENTREE_DELETE_TASKS_DAYS': {
            'name': _('Task Deletion Interval'),
            'description': _(
                'Background task results will be deleted after specified number of days'
            ),
            'default': 30,
            'units': _('days'),
            'validator': [int, MinValueValidator(7)],
        },
        'INVENTREE_DELETE_ERRORS_DAYS': {
            'name': _('Error Log Deletion Interval'),
            'description': _(
                'Error logs will be deleted after specified number of days'
            ),
            'default': 30,
            'units': _('days'),
            'validator': [int, MinValueValidator(7)],
        },
        'INVENTREE_DELETE_NOTIFICATIONS_DAYS': {
            'name': _('Notification Deletion Interval'),
            'description': _(
                'User notifications will be deleted after specified number of days'
            ),
            'default': 30,
            'units': _('days'),
            'validator': [int, MinValueValidator(7)],
        },
        'BARCODE_ENABLE': {
            'name': _('Barcode Support'),
            'description': _('Enable barcode scanner support in the web interface'),
            'default': True,
            'validator': bool,
        },
        'BARCODE_INPUT_DELAY': {
            'name': _('Barcode Input Delay'),
            'description': _('Barcode input processing delay time'),
            'default': 50,
            'validator': [int, MinValueValidator(1)],
            'units': 'ms',
        },
        'BARCODE_WEBCAM_SUPPORT': {
            'name': _('Barcode Webcam Support'),
            'description': _('Allow barcode scanning via webcam in browser'),
            'default': True,
            'validator': bool,
        },
        'PART_ENABLE_REVISION': {
            'name': _('Part Revisions'),
            'description': _('Enable revision field for Part'),
            'validator': bool,
            'default': True,
        },
        'PART_IPN_REGEX': {
            'name': _('IPN Regex'),
            'description': _('Regular expression pattern for matching Part IPN'),
        },
        'PART_ALLOW_DUPLICATE_IPN': {
            'name': _('Allow Duplicate IPN'),
            'description': _('Allow multiple parts to share the same IPN'),
            'default': True,
            'validator': bool,
        },
        'PART_ALLOW_EDIT_IPN': {
            'name': _('Allow Editing IPN'),
            'description': _('Allow changing the IPN value while editing a part'),
            'default': True,
            'validator': bool,
        },
        'PART_COPY_BOM': {
            'name': _('Copy Part BOM Data'),
            'description': _('Copy BOM data by default when duplicating a part'),
            'default': True,
            'validator': bool,
        },
        'PART_COPY_PARAMETERS': {
            'name': _('Copy Part Parameter Data'),
            'description': _('Copy parameter data by default when duplicating a part'),
            'default': True,
            'validator': bool,
        },
        'PART_COPY_TESTS': {
            'name': _('Copy Part Test Data'),
            'description': _('Copy test data by default when duplicating a part'),
            'default': True,
            'validator': bool,
        },
        'PART_CATEGORY_PARAMETERS': {
            'name': _('Copy Category Parameter Templates'),
            'description': _('Copy category parameter templates when creating a part'),
            'default': True,
            'validator': bool,
        },
        'PART_TEMPLATE': {
            'name': _('Template'),
            'description': _('Parts are templates by default'),
            'default': False,
            'validator': bool,
        },
        'PART_ASSEMBLY': {
            'name': _('Assembly'),
            'description': _('Parts can be assembled from other components by default'),
            'default': False,
            'validator': bool,
        },
        'PART_COMPONENT': {
            'name': _('Component'),
            'description': _('Parts can be used as sub-components by default'),
            'default': True,
            'validator': bool,
        },
        'PART_PURCHASEABLE': {
            'name': _('Purchaseable'),
            'description': _('Parts are purchaseable by default'),
            'default': True,
            'validator': bool,
        },
        'PART_SALABLE': {
            'name': _('Salable'),
            'description': _('Parts are salable by default'),
            'default': False,
            'validator': bool,
        },
        'PART_TRACKABLE': {
            'name': _('Trackable'),
            'description': _('Parts are trackable by default'),
            'default': False,
            'validator': bool,
        },
        'PART_VIRTUAL': {
            'name': _('Virtual'),
            'description': _('Parts are virtual by default'),
            'default': False,
            'validator': bool,
        },
        'PART_SHOW_IMPORT': {
            'name': _('Show Import in Views'),
            'description': _('Display the import wizard in some part views'),
            'default': False,
            'validator': bool,
        },
        'PART_SHOW_RELATED': {
            'name': _('Show related parts'),
            'description': _('Display related parts for a part'),
            'default': True,
            'validator': bool,
        },
        'PART_CREATE_INITIAL': {
            'name': _('Initial Stock Data'),
            'description': _('Allow creation of initial stock when adding a new part'),
            'default': False,
            'validator': bool,
        },
        'PART_CREATE_SUPPLIER': {
            'name': _('Initial Supplier Data'),
            'description': _(
                'Allow creation of initial supplier data when adding a new part'
            ),
            'default': True,
            'validator': bool,
        },
        'PART_NAME_FORMAT': {
            'name': _('Part Name Display Format'),
            'description': _('Format to display the part name'),
            'default': "{{ part.IPN if part.IPN }}{{ ' | ' if part.IPN }}{{ part.name }}{{ ' | ' if part.revision }}"
            '{{ part.revision if part.revision }}',
            'validator': InvenTree.validators.validate_part_name_format,
        },
        'PART_CATEGORY_DEFAULT_ICON': {
            'name': _('Part Category Default Icon'),
            'description': _('Part category default icon (empty means no icon)'),
            'default': '',
        },
        'PART_PARAMETER_ENFORCE_UNITS': {
            'name': _('Enforce Parameter Units'),
            'description': _(
                'If units are provided, parameter values must match the specified units'
            ),
            'default': True,
            'validator': bool,
        },
        'PRICING_DECIMAL_PLACES_MIN': {
            'name': _('Minimum Pricing Decimal Places'),
            'description': _(
                'Minimum number of decimal places to display when rendering pricing data'
            ),
            'default': 0,
            'validator': [int, MinValueValidator(0), MaxValueValidator(4)],
        },
        'PRICING_DECIMAL_PLACES': {
            'name': _('Maximum Pricing Decimal Places'),
            'description': _(
                'Maximum number of decimal places to display when rendering pricing data'
            ),
            'default': 6,
            'validator': [int, MinValueValidator(2), MaxValueValidator(6)],
        },
        'PRICING_USE_SUPPLIER_PRICING': {
            'name': _('Use Supplier Pricing'),
            'description': _(
                'Include supplier price breaks in overall pricing calculations'
            ),
            'default': True,
            'validator': bool,
        },
        'PRICING_PURCHASE_HISTORY_OVERRIDES_SUPPLIER': {
            'name': _('Purchase History Override'),
            'description': _(
                'Historical purchase order pricing overrides supplier price breaks'
            ),
            'default': False,
            'validator': bool,
        },
        'PRICING_USE_STOCK_PRICING': {
            'name': _('Use Stock Item Pricing'),
            'description': _(
                'Use pricing from manually entered stock data for pricing calculations'
            ),
            'default': True,
            'validator': bool,
        },
        'PRICING_STOCK_ITEM_AGE_DAYS': {
            'name': _('Stock Item Pricing Age'),
            'description': _(
                'Exclude stock items older than this number of days from pricing calculations'
            ),
            'default': 0,
            'units': _('days'),
            'validator': [int, MinValueValidator(0)],
        },
        'PRICING_USE_VARIANT_PRICING': {
            'name': _('Use Variant Pricing'),
            'description': _('Include variant pricing in overall pricing calculations'),
            'default': True,
            'validator': bool,
        },
        'PRICING_ACTIVE_VARIANTS': {
            'name': _('Active Variants Only'),
            'description': _(
                'Only use active variant parts for calculating variant pricing'
            ),
            'default': False,
            'validator': bool,
        },
        'PRICING_UPDATE_DAYS': {
            'name': _('Pricing Rebuild Interval'),
            'description': _(
                'Number of days before part pricing is automatically updated'
            ),
            'units': _('days'),
            'default': 30,
            'validator': [int, MinValueValidator(10)],
        },
        'PART_INTERNAL_PRICE': {
            'name': _('Internal Prices'),
            'description': _('Enable internal prices for parts'),
            'default': False,
            'validator': bool,
        },
        'PART_BOM_USE_INTERNAL_PRICE': {
            'name': _('Internal Price Override'),
            'description': _(
                'If available, internal prices override price range calculations'
            ),
            'default': False,
            'validator': bool,
        },
        'LABEL_ENABLE': {
            'name': _('Enable label printing'),
            'description': _('Enable label printing from the web interface'),
            'default': True,
            'validator': bool,
        },
        'LABEL_DPI': {
            'name': _('Label Image DPI'),
            'description': _(
                'DPI resolution when generating image files to supply to label printing plugins'
            ),
            'default': 300,
            'validator': [int, MinValueValidator(100)],
        },
        'REPORT_ENABLE': {
            'name': _('Enable Reports'),
            'description': _('Enable generation of reports'),
            'default': False,
            'validator': bool,
        },
        'REPORT_DEBUG_MODE': {
            'name': _('Debug Mode'),
            'description': _('Generate reports in debug mode (HTML output)'),
            'default': False,
            'validator': bool,
        },
        'REPORT_DEFAULT_PAGE_SIZE': {
            'name': _('Page Size'),
            'description': _('Default page size for PDF reports'),
            'default': 'A4',
            'choices': report.helpers.report_page_size_options,
        },
        'REPORT_ENABLE_TEST_REPORT': {
            'name': _('Enable Test Reports'),
            'description': _('Enable generation of test reports'),
            'default': True,
            'validator': bool,
        },
        'REPORT_ATTACH_TEST_REPORT': {
            'name': _('Attach Test Reports'),
            'description': _(
                'When printing a Test Report, attach a copy of the Test Report to the associated Stock Item'
            ),
            'default': False,
            'validator': bool,
        },
        'SERIAL_NUMBER_GLOBALLY_UNIQUE': {
            'name': _('Globally Unique Serials'),
            'description': _('Serial numbers for stock items must be globally unique'),
            'default': False,
            'validator': bool,
        },
        'SERIAL_NUMBER_AUTOFILL': {
            'name': _('Autofill Serial Numbers'),
            'description': _('Autofill serial numbers in forms'),
            'default': False,
            'validator': bool,
        },
        'STOCK_DELETE_DEPLETED_DEFAULT': {
            'name': _('Delete Depleted Stock'),
            'description': _(
                'Determines default behaviour when a stock item is depleted'
            ),
            'default': True,
            'validator': bool,
        },
        'STOCK_BATCH_CODE_TEMPLATE': {
            'name': _('Batch Code Template'),
            'description': _(
                'Template for generating default batch codes for stock items'
            ),
            'default': '',
        },
        'STOCK_ENABLE_EXPIRY': {
            'name': _('Stock Expiry'),
            'description': _('Enable stock expiry functionality'),
            'default': False,
            'validator': bool,
        },
        'STOCK_ALLOW_EXPIRED_SALE': {
            'name': _('Sell Expired Stock'),
            'description': _('Allow sale of expired stock'),
            'default': False,
            'validator': bool,
        },
        'STOCK_STALE_DAYS': {
            'name': _('Stock Stale Time'),
            'description': _(
                'Number of days stock items are considered stale before expiring'
            ),
            'default': 0,
            'units': _('days'),
            'validator': [int],
        },
        'STOCK_ALLOW_EXPIRED_BUILD': {
            'name': _('Build Expired Stock'),
            'description': _('Allow building with expired stock'),
            'default': False,
            'validator': bool,
        },
        'STOCK_OWNERSHIP_CONTROL': {
            'name': _('Stock Ownership Control'),
            'description': _('Enable ownership control over stock locations and items'),
            'default': False,
            'validator': bool,
        },
        'STOCK_LOCATION_DEFAULT_ICON': {
            'name': _('Stock Location Default Icon'),
            'description': _('Stock location default icon (empty means no icon)'),
            'default': '',
        },
        'STOCK_SHOW_INSTALLED_ITEMS': {
            'name': _('Show Installed Stock Items'),
            'description': _('Display installed stock items in stock tables'),
            'default': False,
            'validator': bool,
        },
        'BUILDORDER_REFERENCE_PATTERN': {
            'name': _('Build Order Reference Pattern'),
            'description': _(
                'Required pattern for generating Build Order reference field'
            ),
            'default': 'BO-{ref:04d}',
            'validator': build.validators.validate_build_order_reference_pattern,
        },
        'RETURNORDER_ENABLED': {
            'name': _('Enable Return Orders'),
            'description': _('Enable return order functionality in the user interface'),
            'validator': bool,
            'default': False,
        },
        'RETURNORDER_REFERENCE_PATTERN': {
            'name': _('Return Order Reference Pattern'),
            'description': _(
                'Required pattern for generating Return Order reference field'
            ),
            'default': 'RMA-{ref:04d}',
            'validator': order.validators.validate_return_order_reference_pattern,
        },
        'RETURNORDER_EDIT_COMPLETED_ORDERS': {
            'name': _('Edit Completed Return Orders'),
            'description': _(
                'Allow editing of return orders after they have been completed'
            ),
            'default': False,
            'validator': bool,
        },
        'SALESORDER_REFERENCE_PATTERN': {
            'name': _('Sales Order Reference Pattern'),
            'description': _(
                'Required pattern for generating Sales Order reference field'
            ),
            'default': 'SO-{ref:04d}',
            'validator': order.validators.validate_sales_order_reference_pattern,
        },
        'SALESORDER_DEFAULT_SHIPMENT': {
            'name': _('Sales Order Default Shipment'),
            'description': _('Enable creation of default shipment with sales orders'),
            'default': False,
            'validator': bool,
        },
        'SALESORDER_EDIT_COMPLETED_ORDERS': {
            'name': _('Edit Completed Sales Orders'),
            'description': _(
                'Allow editing of sales orders after they have been shipped or completed'
            ),
            'default': False,
            'validator': bool,
        },
        'PURCHASEORDER_REFERENCE_PATTERN': {
            'name': _('Purchase Order Reference Pattern'),
            'description': _(
                'Required pattern for generating Purchase Order reference field'
            ),
            'default': 'PO-{ref:04d}',
            'validator': order.validators.validate_purchase_order_reference_pattern,
        },
        'PURCHASEORDER_EDIT_COMPLETED_ORDERS': {
            'name': _('Edit Completed Purchase Orders'),
            'description': _(
                'Allow editing of purchase orders after they have been shipped or completed'
            ),
            'default': False,
            'validator': bool,
        },
        'PURCHASEORDER_AUTO_COMPLETE': {
            'name': _('Auto Complete Purchase Orders'),
            'description': _(
                'Automatically mark purchase orders as complete when all line items are received'
            ),
            'default': True,
            'validator': bool,
        },
        # login / SSO
        'LOGIN_ENABLE_PWD_FORGOT': {
            'name': _('Enable password forgot'),
            'description': _('Enable password forgot function on the login pages'),
            'default': True,
            'validator': bool,
        },
        'LOGIN_ENABLE_REG': {
            'name': _('Enable registration'),
            'description': _('Enable self-registration for users on the login pages'),
            'default': False,
            'validator': bool,
        },
        'LOGIN_ENABLE_SSO': {
            'name': _('Enable SSO'),
            'description': _('Enable SSO on the login pages'),
            'default': False,
            'validator': bool,
        },
        'LOGIN_ENABLE_SSO_REG': {
            'name': _('Enable SSO registration'),
            'description': _(
                'Enable self-registration via SSO for users on the login pages'
            ),
            'default': False,
            'validator': bool,
        },
        'LOGIN_MAIL_REQUIRED': {
            'name': _('Email required'),
            'description': _('Require user to supply mail on signup'),
            'default': False,
            'validator': bool,
        },
        'LOGIN_SIGNUP_SSO_AUTO': {
            'name': _('Auto-fill SSO users'),
            'description': _(
                'Automatically fill out user-details from SSO account-data'
            ),
            'default': True,
            'validator': bool,
        },
        'LOGIN_SIGNUP_MAIL_TWICE': {
            'name': _('Mail twice'),
            'description': _('On signup ask users twice for their mail'),
            'default': False,
            'validator': bool,
        },
        'LOGIN_SIGNUP_PWD_TWICE': {
            'name': _('Password twice'),
            'description': _('On signup ask users twice for their password'),
            'default': True,
            'validator': bool,
        },
        'LOGIN_SIGNUP_MAIL_RESTRICTION': {
            'name': _('Allowed domains'),
            'description': _(
                'Restrict signup to certain domains (comma-separated, starting with @)'
            ),
            'default': '',
            'before_save': validate_email_domains,
        },
        'SIGNUP_GROUP': {
            'name': _('Group on signup'),
            'description': _('Group to which new users are assigned on registration'),
            'default': '',
            'choices': settings_group_options,
        },
        'LOGIN_ENFORCE_MFA': {
            'name': _('Enforce MFA'),
            'description': _('Users must use multifactor security.'),
            'default': False,
            'validator': bool,
        },
        'PLUGIN_ON_STARTUP': {
            'name': _('Check plugins on startup'),
            'description': _(
                'Check that all plugins are installed on startup - enable in container environments'
            ),
            'default': str(os.getenv('INVENTREE_DOCKER', False)).lower()
            in ['1', 'true'],
            'validator': bool,
            'requires_restart': True,
        },
        'PLUGIN_UPDATE_CHECK': {
            'name': _('Check for plugin updates'),
            'description': _('Enable periodic checks for updates to installed plugins'),
            'default': True,
            'validator': bool,
        },
        # Settings for plugin mixin features
        'ENABLE_PLUGINS_URL': {
            'name': _('Enable URL integration'),
            'description': _('Enable plugins to add URL routes'),
            'default': False,
            'validator': bool,
            'after_save': reload_plugin_registry,
        },
        'ENABLE_PLUGINS_NAVIGATION': {
            'name': _('Enable navigation integration'),
            'description': _('Enable plugins to integrate into navigation'),
            'default': False,
            'validator': bool,
            'after_save': reload_plugin_registry,
        },
        'ENABLE_PLUGINS_APP': {
            'name': _('Enable app integration'),
            'description': _('Enable plugins to add apps'),
            'default': False,
            'validator': bool,
            'after_save': reload_plugin_registry,
        },
        'ENABLE_PLUGINS_SCHEDULE': {
            'name': _('Enable schedule integration'),
            'description': _('Enable plugins to run scheduled tasks'),
            'default': False,
            'validator': bool,
            'after_save': reload_plugin_registry,
        },
        'ENABLE_PLUGINS_EVENTS': {
            'name': _('Enable event integration'),
            'description': _('Enable plugins to respond to internal events'),
            'default': False,
            'validator': bool,
            'after_save': reload_plugin_registry,
        },
        'PROJECT_CODES_ENABLED': {
            'name': _('Enable project codes'),
            'description': _('Enable project codes for tracking projects'),
            'default': False,
            'validator': bool,
        },
        'STOCKTAKE_ENABLE': {
            'name': _('Stocktake Functionality'),
            'description': _(
                'Enable stocktake functionality for recording stock levels and calculating stock value'
            ),
            'validator': bool,
            'default': False,
        },
        'STOCKTAKE_EXCLUDE_EXTERNAL': {
            'name': _('Exclude External Locations'),
            'description': _(
                'Exclude stock items in external locations from stocktake calculations'
            ),
            'validator': bool,
            'default': False,
        },
        'STOCKTAKE_AUTO_DAYS': {
            'name': _('Automatic Stocktake Period'),
            'description': _(
                'Number of days between automatic stocktake recording (set to zero to disable)'
            ),
            'validator': [int, MinValueValidator(0)],
            'default': 0,
        },
        'STOCKTAKE_DELETE_REPORT_DAYS': {
            'name': _('Report Deletion Interval'),
            'description': _(
                'Stocktake reports will be deleted after specified number of days'
            ),
            'default': 30,
            'units': _('days'),
            'validator': [int, MinValueValidator(7)],
        },
        'DISPLAY_FULL_NAMES': {
            'name': _('Display Users full names'),
            'description': _('Display Users full names instead of usernames'),
            'default': False,
            'validator': bool
        },

        'PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS': {
            'name': _('Block Until Tests Pass'),
            'description': _('Prevent build outputs from being completed until all required tests pass'),
            'default': False,
            'validator': bool,
        },
    }

    typ = 'inventree'

    key = models.CharField(
        max_length=50,
        blank=False,
        unique=True,
        help_text=_('Settings key (must be unique - case insensitive'),
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


def label_printer_options():
    """Build a list of available label printer options."""
    printers = []
    label_printer_plugins = registry.with_mixin('labels')
    if label_printer_plugins:
        printers.extend([
            (p.slug, p.name + ' - ' + p.human_name) for p in label_printer_plugins
        ])
    return printers


class InvenTreeUserSetting(BaseInvenTreeSetting):
    """An InvenTreeSetting object with a usercontext."""

    class Meta:
        """Meta options for InvenTreeUserSetting."""

        verbose_name = 'InvenTree User Setting'
        verbose_name_plural = 'InvenTree User Settings'
        constraints = [
            models.UniqueConstraint(fields=['key', 'user'], name='unique key and user')
        ]

    SETTINGS = {
        'HOMEPAGE_HIDE_INACTIVE': {
            'name': _('Hide inactive parts'),
            'description': _(
                'Hide inactive parts in results displayed on the homepage'
            ),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_PART_STARRED': {
            'name': _('Show subscribed parts'),
            'description': _('Show subscribed parts on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_CATEGORY_STARRED': {
            'name': _('Show subscribed categories'),
            'description': _('Show subscribed part categories on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_PART_LATEST': {
            'name': _('Show latest parts'),
            'description': _('Show latest parts on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_BOM_REQUIRES_VALIDATION': {
            'name': _('Show unvalidated BOMs'),
            'description': _('Show BOMs that await validation on the homepage'),
            'default': False,
            'validator': bool,
        },
        'HOMEPAGE_STOCK_RECENT': {
            'name': _('Show recent stock changes'),
            'description': _('Show recently changed stock items on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_STOCK_LOW': {
            'name': _('Show low stock'),
            'description': _('Show low stock items on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_SHOW_STOCK_DEPLETED': {
            'name': _('Show depleted stock'),
            'description': _('Show depleted stock items on the homepage'),
            'default': False,
            'validator': bool,
        },
        'HOMEPAGE_BUILD_STOCK_NEEDED': {
            'name': _('Show needed stock'),
            'description': _('Show stock items needed for builds on the homepage'),
            'default': False,
            'validator': bool,
        },
        'HOMEPAGE_STOCK_EXPIRED': {
            'name': _('Show expired stock'),
            'description': _('Show expired stock items on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_STOCK_STALE': {
            'name': _('Show stale stock'),
            'description': _('Show stale stock items on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_BUILD_PENDING': {
            'name': _('Show pending builds'),
            'description': _('Show pending builds on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_BUILD_OVERDUE': {
            'name': _('Show overdue builds'),
            'description': _('Show overdue builds on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_PO_OUTSTANDING': {
            'name': _('Show outstanding POs'),
            'description': _('Show outstanding POs on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_PO_OVERDUE': {
            'name': _('Show overdue POs'),
            'description': _('Show overdue POs on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_SO_OUTSTANDING': {
            'name': _('Show outstanding SOs'),
            'description': _('Show outstanding SOs on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_SO_OVERDUE': {
            'name': _('Show overdue SOs'),
            'description': _('Show overdue SOs on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_SO_SHIPMENTS_PENDING': {
            'name': _('Show pending SO shipments'),
            'description': _('Show pending SO shipments on the homepage'),
            'default': True,
            'validator': bool,
        },
        'HOMEPAGE_NEWS': {
            'name': _('Show News'),
            'description': _('Show news on the homepage'),
            'default': False,
            'validator': bool,
        },
        'LABEL_INLINE': {
            'name': _('Inline label display'),
            'description': _(
                'Display PDF labels in the browser, instead of downloading as a file'
            ),
            'default': True,
            'validator': bool,
        },
        'LABEL_DEFAULT_PRINTER': {
            'name': _('Default label printer'),
            'description': _(
                'Configure which label printer should be selected by default'
            ),
            'default': '',
            'choices': label_printer_options,
        },
        'REPORT_INLINE': {
            'name': _('Inline report display'),
            'description': _(
                'Display PDF reports in the browser, instead of downloading as a file'
            ),
            'default': False,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_PARTS': {
            'name': _('Search Parts'),
            'description': _('Display parts in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS': {
            'name': _('Search Supplier Parts'),
            'description': _('Display supplier parts in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS': {
            'name': _('Search Manufacturer Parts'),
            'description': _('Display manufacturer parts in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_HIDE_INACTIVE_PARTS': {
            'name': _('Hide Inactive Parts'),
            'description': _('Excluded inactive parts from search preview window'),
            'default': False,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_CATEGORIES': {
            'name': _('Search Categories'),
            'description': _('Display part categories in search preview window'),
            'default': False,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_STOCK': {
            'name': _('Search Stock'),
            'description': _('Display stock items in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_HIDE_UNAVAILABLE_STOCK': {
            'name': _('Hide Unavailable Stock Items'),
            'description': _(
                'Exclude stock items which are not available from the search preview window'
            ),
            'validator': bool,
            'default': False,
        },
        'SEARCH_PREVIEW_SHOW_LOCATIONS': {
            'name': _('Search Locations'),
            'description': _('Display stock locations in search preview window'),
            'default': False,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_COMPANIES': {
            'name': _('Search Companies'),
            'description': _('Display companies in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_BUILD_ORDERS': {
            'name': _('Search Build Orders'),
            'description': _('Display build orders in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS': {
            'name': _('Search Purchase Orders'),
            'description': _('Display purchase orders in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS': {
            'name': _('Exclude Inactive Purchase Orders'),
            'description': _(
                'Exclude inactive purchase orders from search preview window'
            ),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_SHOW_SALES_ORDERS': {
            'name': _('Search Sales Orders'),
            'description': _('Display sales orders in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_EXCLUDE_INACTIVE_SALES_ORDERS': {
            'name': _('Exclude Inactive Sales Orders'),
            'description': _(
                'Exclude inactive sales orders from search preview window'
            ),
            'validator': bool,
            'default': True,
        },
        'SEARCH_PREVIEW_SHOW_RETURN_ORDERS': {
            'name': _('Search Return Orders'),
            'description': _('Display return orders in search preview window'),
            'default': True,
            'validator': bool,
        },
        'SEARCH_PREVIEW_EXCLUDE_INACTIVE_RETURN_ORDERS': {
            'name': _('Exclude Inactive Return Orders'),
            'description': _(
                'Exclude inactive return orders from search preview window'
            ),
            'validator': bool,
            'default': True,
        },
        'SEARCH_PREVIEW_RESULTS': {
            'name': _('Search Preview Results'),
            'description': _(
                'Number of results to show in each section of the search preview window'
            ),
            'default': 10,
            'validator': [int, MinValueValidator(1)],
        },
        'SEARCH_REGEX': {
            'name': _('Regex Search'),
            'description': _('Enable regular expressions in search queries'),
            'default': False,
            'validator': bool,
        },
        'SEARCH_WHOLE': {
            'name': _('Whole Word Search'),
            'description': _('Search queries return results for whole word matches'),
            'default': False,
            'validator': bool,
        },
        'PART_SHOW_QUANTITY_IN_FORMS': {
            'name': _('Show Quantity in Forms'),
            'description': _('Display available part quantity in some forms'),
            'default': True,
            'validator': bool,
        },
        'FORMS_CLOSE_USING_ESCAPE': {
            'name': _('Escape Key Closes Forms'),
            'description': _('Use the escape key to close modal forms'),
            'default': False,
            'validator': bool,
        },
        'STICKY_HEADER': {
            'name': _('Fixed Navbar'),
            'description': _('The navbar position is fixed to the top of the screen'),
            'default': False,
            'validator': bool,
        },
        'DATE_DISPLAY_FORMAT': {
            'name': _('Date Format'),
            'description': _('Preferred format for displaying dates'),
            'default': 'YYYY-MM-DD',
            'choices': [
                ('YYYY-MM-DD', '2022-02-22'),
                ('YYYY/MM/DD', '2022/22/22'),
                ('DD-MM-YYYY', '22-02-2022'),
                ('DD/MM/YYYY', '22/02/2022'),
                ('MM-DD-YYYY', '02-22-2022'),
                ('MM/DD/YYYY', '02/22/2022'),
                ('MMM DD YYYY', 'Feb 22 2022'),
            ],
        },
        'DISPLAY_SCHEDULE_TAB': {
            'name': _('Part Scheduling'),
            'description': _('Display part scheduling information'),
            'default': True,
            'validator': bool,
        },
        'DISPLAY_STOCKTAKE_TAB': {
            'name': _('Part Stocktake'),
            'description': _(
                'Display part stocktake information (if stocktake functionality is enabled)'
            ),
            'default': True,
            'validator': bool,
        },
        'TABLE_STRING_MAX_LENGTH': {
            'name': _('Table String Length'),
            'description': _(
                'Maximum length limit for strings displayed in table views'
            ),
            'validator': [int, MinValueValidator(0)],
            'default': 100,
        },
        'DEFAULT_PART_LABEL_TEMPLATE': {
            'name': _('Default part label template'),
            'description': _('The part label template to be automatically selected'),
            'validator': [int],
            'default': '',
        },
        'DEFAULT_ITEM_LABEL_TEMPLATE': {
            'name': _('Default stock item template'),
            'description': _(
                'The stock item label template to be automatically selected'
            ),
            'validator': [int],
            'default': '',
        },
        'DEFAULT_LOCATION_LABEL_TEMPLATE': {
            'name': _('Default stock location label template'),
            'description': _(
                'The stock location label template to be automatically selected'
            ),
            'validator': [int],
            'default': '',
        },
        'NOTIFICATION_ERROR_REPORT': {
            'name': _('Receive error reports'),
            'description': _('Receive notifications for system errors'),
            'default': True,
            'validator': bool,
        },
        'LAST_USED_PRINTING_MACHINES': {
            'name': _('Last used printing machines'),
            'description': _('Save the last used printing machines for a user'),
            'default': '',
        },
    }

    typ = 'user'
    extra_unique_fields = ['user']

    key = models.CharField(
        max_length=50,
        blank=False,
        unique=False,
        help_text=_('Settings key (must be unique - case insensitive'),
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


def get_price(
    instance,
    quantity,
    moq=True,
    multiples=True,
    currency=None,
    break_name: str = 'price_breaks',
):
    """Calculate the price based on quantity price breaks.

    - Don't forget to add in flat-fee cost (base_cost field)
    - If MOQ (minimum order quantity) is required, bump quantity
    - If order multiples are to be observed, then we need to calculate based on that, too
    """
    from common.settings import currency_code_default

    if hasattr(instance, break_name):
        price_breaks = getattr(instance, break_name).all()
    else:
        price_breaks = []

    # No price break information available?
    if len(price_breaks) == 0:
        return None

    # Check if quantity is fraction and disable multiples
    multiples = quantity % 1 == 0

    # Order multiples
    if multiples:
        quantity = int(math.ceil(quantity / instance.multiple) * instance.multiple)

    pb_found = False
    pb_quantity = -1
    pb_cost = 0.0

    if currency is None:
        # Default currency selection
        currency = currency_code_default()

    pb_min = None
    for pb in price_breaks:
        # Store smallest price break
        if not pb_min:
            pb_min = pb

        # Ignore this pricebreak (quantity is too high)
        if pb.quantity > quantity:
            continue

        pb_found = True

        # If this price-break quantity is the largest so far, use it!
        if pb.quantity > pb_quantity:
            pb_quantity = pb.quantity

            # Convert everything to the selected currency
            pb_cost = pb.convert_to(currency)

    # Use smallest price break
    if not pb_found and pb_min:
        # Update price break information
        pb_quantity = pb_min.quantity
        pb_cost = pb_min.convert_to(currency)
        # Trigger cost calculation using smallest price break
        pb_found = True

    # Convert quantity to decimal.Decimal format
    quantity = decimal.Decimal(f'{quantity}')

    if pb_found:
        cost = pb_cost * quantity
        return InvenTree.helpers.normalize(cost + instance.base_cost)
    return None


class ColorTheme(models.Model):
    """Color Theme Setting."""

    name = models.CharField(max_length=20, default='', blank=True)

    user = models.CharField(max_length=150, unique=True)

    @classmethod
    def get_color_themes_choices(cls):
        """Get all color themes from static folder."""
        if not settings.STATIC_COLOR_THEMES_DIR.exists():
            logger.error('Theme directory does not exist')
            return []

        # Get files list from css/color-themes/ folder
        files_list = []

        for file in settings.STATIC_COLOR_THEMES_DIR.iterdir():
            files_list.append([file.stem, file.suffix])

        # Get color themes choices (CSS sheets)
        choices = [
            (file_name.lower(), _(file_name.replace('-', ' ').title()))
            for file_name, file_ext in files_list
            if file_ext == '.css'
        ]

        return choices

    @classmethod
    def is_valid_choice(cls, user_color_theme):
        """Check if color theme is valid choice."""
        try:
            user_color_theme_name = user_color_theme.name
        except AttributeError:
            return False

        for color_theme in cls.get_color_themes_choices():
            if user_color_theme_name == color_theme[0]:
                return True

        return False


class VerificationMethod(Enum):
    """Class to hold method references."""

    NONE = 0
    TOKEN = 1
    HMAC = 2


class WebhookEndpoint(models.Model):
    """Defines a Webhook entdpoint.

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
            host=request.get_host(),
            header=json.dumps(dict(headers.items())),
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
        since = datetime.now().date() - delta

        entries = cls.objects.filter(key=key, uid=uid, updated__gte=since)

        return entries.exists()

    @classmethod
    def notify(cls, key: str, uid: int):
        """Notify the database that a particular notification has been sent out."""
        entry, created = cls.objects.get_or_create(key=key, uid=uid)

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
            if settings.USE_TZ
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
    - read: Was this iteam already by a superuser?
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

    Simply stores the image file, for use in the 'notes' field (of any models which support markdown)
    """

    image = models.ImageField(
        upload_to=rename_notes_image, verbose_name=_('Image'), help_text=_('Image file')
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)


class CustomUnit(models.Model):
    """Model for storing custom physical unit definitions.

    Model Attributes:
        name: Name of the unit
        definition: Definition of the unit
        symbol: Symbol for the unit (e.g. 'm' for 'metre') (optional)

    Refer to the pint documentation for further information on unit definitions.
    https://pint.readthedocs.io/en/stable/advanced/defining.html
    """

    def fmt_string(self):
        """Construct a unit definition string e.g. 'dog_year = 52 * day = dy'."""
        fmt = f'{self.name} = {self.definition}'

        if self.symbol:
            fmt += f' = {self.symbol}'

        return fmt

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
        unique=True,
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
