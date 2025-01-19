"""Common database model definitions.

These models are 'generic' and do not fit a particular business logic object.
"""

import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import timedelta, timezone
from enum import Enum
from io import BytesIO
from secrets import compare_digest
from typing import Any, Union

from django.apps import apps
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

import structlog
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from rest_framework.exceptions import PermissionDenied
from taggit.managers import TaggableManager

import common.currency
import common.validators
import InvenTree.exceptions
import InvenTree.fields
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import InvenTree.validators
import users.models
from common.setting.type import InvenTreeSettingsKeyType, SettingsKeyType
from generic.states import ColorEnum
from generic.states.custom import state_color_mappings
from InvenTree.sanitizer import sanitize_svg

logger = structlog.get_logger('inventree')


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

        # Execute after_save action
        self._call_settings_function('after_save', args, kwargs)

    @classmethod
    def build_default_values(cls, **kwargs):
        """Ensure that all values defined in SETTINGS are present in the database.

        If a particular setting is not present, create it with the default value
        """
        cache_key = f'BUILD_DEFAULT_VALUES:{cls.__name__!s}'

        try:
            if InvenTree.helpers.str2bool(cache.get(cache_key, False)):
                # Already built default values
                return
        except Exception:
            pass

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

        try:
            cache.set(cache_key, True, timeout=3600)
        except Exception:
            pass

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
        except Exception:
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

        # Unless otherwise specified, attempt to create the setting
        create = kwargs.pop('create', True)

        # Specify if cache lookup should be performed
        do_cache = kwargs.pop('cache', django_settings.GLOBAL_CACHE_ENABLED)

        filters = {
            'key__iexact': key,
            # Optionally filter by other keys
            **cls.get_filters(**kwargs),
        }

        # Prevent saving to the database during certain operations
        if (
            InvenTree.ready.isImportingData()
            or InvenTree.ready.isRunningMigrations()
            or InvenTree.ready.isRebuildingData()
            or InvenTree.ready.isRunningBackup()
        ):
            create = False
            do_cache = False

        cache_key = cls.create_cache_key(key, **kwargs)

        if do_cache:
            try:
                # First attempt to find the setting object in the cache
                cached_setting = cache.get(cache_key)

                if cached_setting is not None:
                    return cached_setting

            except Exception:
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
        if not setting and create:
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
        if (
            cls.CHECK_SETTING_KEY
            and key not in cls.SETTINGS
            and not key.startswith('_')
        ):
            logger.warning(
                "get_setting: Setting key '%s' is not defined for class %s",
                key,
                str(cls),
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
                "set_setting: Setting key '%s' is not defined for class %s",
                key,
                str(cls),
            )

        if change_user is not None and not change_user.is_staff:
            return

        # Do not write to the database under certain conditions
        if (
            InvenTree.ready.isImportingData()
            or InvenTree.ready.isRunningMigrations()
            or InvenTree.ready.isRebuildingData()
            or InvenTree.ready.isRunningBackup()
        ):
            return

        attempts = int(kwargs.get('attempts', 3))

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
        except Exception as exc:
            # Some other error
            logger.exception(
                "Error setting setting '%s' for %s: %s", key, str(cls), str(type(exc))
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
            self.value = self.as_int()

        elif self.is_bool():
            self.value = self.as_bool()

        elif self.is_float():
            self.value = self.as_float()

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

    def as_float(self):
        """Return the value of this setting converted to a float value.

        If an error occurs, return the default value
        """
        try:
            value = float(self.value)
        except (ValueError, TypeError):
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


class InvenTreeSetting(BaseInvenTreeSetting):
    """An InvenTreeSetting object is a key:value pair used for storing single values (e.g. one-off settings values).

    The class provides a way of retrieving the value for a particular key,
    even if that key does not exist.
    """

    SETTINGS: dict[str, InvenTreeSettingsKeyType]

    CHECK_SETTING_KEY = True

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
    from common.setting.system import SYSTEM_SETTINGS

    SETTINGS = SYSTEM_SETTINGS

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

    CHECK_SETTING_KEY = True

    class Meta:
        """Meta options for InvenTreeUserSetting."""

        verbose_name = 'InvenTree User Setting'
        verbose_name_plural = 'InvenTree User Settings'
        constraints = [
            models.UniqueConstraint(fields=['key', 'user'], name='unique key and user')
        ]

    SETTINGS = common.setting.user.USER_SETTINGS

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


def rename_attachment(instance, filename):
    """Callback function to rename an uploaded attachment file.

    Arguments:
        - instance: The Attachment instance
        - filename: The original filename of the uploaded file

    Returns:
        - The new filename for the uploaded file, e.g. 'attachments/<model_type>/<model_id>/<filename>'
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
        help_text=_('Target model type for this image'),
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

            media_url = InvenTree.helpers.getMediaUrl(self.attachment.url)
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

        return model_class.check_attachment_permission(permission, user)


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
