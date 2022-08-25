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
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from secrets import compare_digest
from typing import List

from django.apps import apps
from django.conf import settings as dj_settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import AppRegistryNotReady, ValidationError
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    URLValidator)
from django.db import models, transaction
from django.db.utils import IntegrityError, OperationalError
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
import InvenTree.ready
import InvenTree.validators
import order.validators
from users.models import Owner

logger = logging.getLogger('inventree')


class EmptyURLValidator(URLValidator):
    """Validator for filed with url - that can be empty."""

    def __call__(self, value):
        """Make sure empty values pass."""
        value = str(value).strip()

        if len(value) == 0:
            pass

        else:
            super().__call__(value)


class BaseInvenTreeSetting(models.Model):
    """An base InvenTreeSetting object is a key:value pair used for storing single values (e.g. one-off settings values)."""

    SETTINGS = {}

    class Meta:
        """Meta options for BaseInvenTreeSetting -> abstract stops creation of database entry."""

        abstract = True

    def save(self, *args, **kwargs):
        """Enforce validation and clean before saving."""
        self.key = str(self.key).upper()

        do_cache = kwargs.pop('cache', True)

        self.clean(**kwargs)
        self.validate_unique(**kwargs)

        # Update this setting in the cache
        if do_cache:
            self.save_to_cache()

        super().save()

        # Get after_save action
        setting = self.get_setting_definition(self.key, *args, **kwargs)
        after_save = setting.get('after_save', None)

        # Execute if callable
        if callable(after_save):
            after_save(self)

    @property
    def cache_key(self):
        """Generate a unique cache key for this settings object"""
        return self.__class__.create_cache_key(self.key, **self.get_kwargs())

    def save_to_cache(self):
        """Save this setting object to cache"""

        ckey = self.cache_key

        logger.debug(f"Saving setting '{ckey}' to cache")

        try:
            cache.set(
                ckey,
                self,
                timeout=3600
            )
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

        key = f"{str(cls.__name__)}:{setting_key}"

        for k, v in kwargs.items():
            key += f"_{k}:{v}"

        return key.replace(" ", "")

    @classmethod
    def allValues(cls, user=None, exclude_hidden=False):
        """Return a dict of "all" defined global settings.

        This performs a single database lookup,
        and then any settings which are not *in* the database
        are assigned their default values
        """
        results = cls.objects.all()

        # Optionally filter by user
        if user is not None:
            results = results.filter(user=user)

        # Query the database
        settings = {}

        for setting in results:
            if setting.key:
                settings[setting.key.upper()] = setting.value

        # Specify any "default" values which are not in the database
        for key in cls.SETTINGS.keys():

            if key.upper() not in settings:
                settings[key.upper()] = cls.get_setting_default(key)

            if exclude_hidden:
                hidden = cls.SETTINGS[key].get('hidden', False)

                if hidden:
                    # Remove hidden items
                    del settings[key.upper()]

        for key, value in settings.items():
            validator = cls.get_setting_validator(key)

            if cls.is_protected(key):
                value = '***'
            elif cls.validator_is_bool(validator):
                value = InvenTree.helpers.str2bool(value)
            elif cls.validator_is_int(validator):
                try:
                    value = int(value)
                except ValueError:
                    value = cls.get_setting_default(key)

            settings[key] = value

        return settings

    def get_kwargs(self):
        """Construct kwargs for doing class-based settings lookup, depending on *which* class we are.

        This is necessary to abtract the settings object
        from the implementing class (e.g plugins)

        Subclasses should override this function to ensure the kwargs are correctly set.
        """
        return {}

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
        else:
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

        return setting.get('default', '')

    @classmethod
    def get_setting_choices(cls, key, **kwargs):
        """Return the validator choices available for a particular setting."""
        setting = cls.get_setting_definition(key, **kwargs)

        choices = setting.get('choices', None)

        if callable(choices):
            # Evaluate the function (we expect it will return a list of tuples...)
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
        }

        # Filter by user
        user = kwargs.get('user', None)

        if user is not None:
            filters['user'] = user

        # Filter by plugin
        plugin = kwargs.get('plugin', None)

        if plugin is not None:
            from plugin import InvenTreePlugin

            if issubclass(plugin.__class__, InvenTreePlugin):
                plugin = plugin.plugin_config()

            filters['plugin'] = plugin
            kwargs['plugin'] = plugin

        # Filter by connection_key
        connection_key = kwargs.get('connection_key', None)

        if connection_key is not None:
            filters['connection_key'] = connection_key

        # Filter by method
        method = kwargs.get('method', None)

        if method is not None:
            filters['method'] = method

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
        except (IntegrityError, OperationalError):
            setting = None

        # Setting does not exist! (Try to create it)
        if not setting:

            # Unless otherwise specified, attempt to create the setting
            create = kwargs.get('create', True)

            # Prevent creation of new settings objects when importing data
            if InvenTree.ready.isImportingData() or not InvenTree.ready.canAppAccessDatabase(allow_test=True):
                create = False

            if create:
                # Attempt to create a new settings object
                setting = cls(
                    key=key,
                    value=cls.get_setting_default(key, **kwargs),
                    **kwargs
                )

                try:
                    # Wrap this statement in "atomic", so it can be rolled back if it fails
                    with transaction.atomic():
                        setting.save(**kwargs)
                except (IntegrityError, OperationalError):
                    # It might be the case that the database isn't created yet
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
        # If no backup value is specified, atttempt to retrieve a "default" value
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
    def set_setting(cls, key, value, change_user, create=True, **kwargs):
        """Set the value of a particular setting. If it does not exist, option to create it.

        Args:
            key: settings key
            value: New value
            change_user: User object (must be staff member to update a core setting)
            create: If True, create a new setting if the specified key does not exist.
        """
        if change_user is not None and not change_user.is_staff:
            return

        filters = {
            'key__iexact': key,
        }

        user = kwargs.get('user', None)
        plugin = kwargs.get('plugin', None)

        if user is not None:
            filters['user'] = user

        if plugin is not None:
            from plugin import InvenTreePlugin

            if issubclass(plugin.__class__, InvenTreePlugin):
                filters['plugin'] = plugin.plugin_config()
            else:
                filters['plugin'] = plugin

        try:
            setting = cls.objects.get(**filters)
        except cls.DoesNotExist:

            if create:
                setting = cls(key=key, **kwargs)
            else:
                return

        # Enforce standard boolean representation
        if setting.is_bool():
            value = InvenTree.helpers.str2bool(value)

        setting.value = str(value)
        setting.save()

    key = models.CharField(max_length=50, blank=False, unique=False, help_text=_('Settings key (must be unique - case insensitive)'))

    value = models.CharField(max_length=200, blank=True, unique=False, help_text=_('Settings value'))

    @property
    def name(self):
        """Return name for setting."""
        return self.__class__.get_setting_name(self.key, **self.get_kwargs())

    @property
    def default_value(self):
        """Return default_value for setting."""
        return self.__class__.get_setting_default(self.key, **self.get_kwargs())

    @property
    def description(self):
        """Return description for setting."""
        return self.__class__.get_setting_description(self.key, **self.get_kwargs())

    @property
    def units(self):
        """Return units for setting."""
        return self.__class__.get_setting_units(self.key, **self.get_kwargs())

    def clean(self, **kwargs):
        """If a validator (or multiple validators) are defined for a particular setting key, run them against the 'value' field."""
        super().clean()

        # Encode as native values
        if self.is_int():
            self.value = self.as_int()

        elif self.is_bool():
            self.value = self.as_bool()

        validator = self.__class__.get_setting_validator(self.key, **kwargs)

        if validator is not None:
            self.run_validator(validator)

        options = self.valid_options()

        if options and self.value not in options:
            raise ValidationError(_("Chosen value is not a valid option"))

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
                raise ValidationError({
                    'value': _('Value must be a boolean value')
                })

        # Integer validator
        if validator is int:

            try:
                # Coerce into an integer value
                value = int(value)
            except (ValueError, TypeError):
                raise ValidationError({
                    'value': _('Value must be an integer value'),
                })

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

    def validate_unique(self, exclude=None, **kwargs):
        """Ensure that the key:value pair is unique. In addition to the base validators, this ensures that the 'key' is unique, using a case-insensitive comparison.

        Note that sub-classes (UserSetting, PluginSetting) use other filters
        to determine if the setting is 'unique' or not
        """
        super().validate_unique(exclude)

        filters = {
            'key__iexact': self.key,
        }

        user = getattr(self, 'user', None)
        plugin = getattr(self, 'plugin', None)

        if user is not None:
            filters['user'] = user

        if plugin is not None:
            filters['plugin'] = plugin

        try:
            # Check if a duplicate setting already exists
            setting = self.__class__.objects.filter(**filters).exclude(id=self.id)

            if setting.exists():
                raise ValidationError({'key': _('Key string must be unique')})

        except self.DoesNotExist:
            pass

    def choices(self):
        """Return the available choices for this setting (or None if no choices are defined)."""
        return self.__class__.get_setting_choices(self.key, **self.get_kwargs())

    def valid_options(self):
        """Return a list of valid options for this setting."""
        choices = self.choices()

        if not choices:
            return None

        return [opt[0] for opt in choices]

    def is_choice(self):
        """Check if this setting is a "choice" field."""
        return self.__class__.get_setting_choices(self.key, **self.get_kwargs()) is not None

    def as_choice(self):
        """Render this setting as the "display" value of a choice field.

        E.g. if the choices are:
        [('A4', 'A4 paper'), ('A3', 'A3 paper')],
        and the value is 'A4',
        then display 'A4 paper'
        """
        choices = self.get_setting_choices(self.key, **self.get_kwargs())

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
        setting = self.get_setting_definition(self.key, **self.get_kwargs())

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
            logger.error(f"Invalid 'model' parameter for setting {self.key} : '{model_name}'")
            return None

        app_models = apps.all_models.get(app, None)

        if app_models is None:
            logger.error(f"Error retrieving model class '{model_name}' for setting '{self.key}' - no app named '{app}'")
            return None

        model = app_models.get(mdl, None)

        if model is None:
            logger.error(f"Error retrieving model class '{model_name}' for setting '{self.key}' - no model named '{mdl}'")
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

        return None

    def is_bool(self):
        """Check if this setting is required to be a boolean value."""
        validator = self.__class__.get_setting_validator(self.key, **self.get_kwargs())

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

        else:
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

    def is_int(self,):
        """Check if the setting is required to be an integer value."""
        validator = self.__class__.get_setting_validator(self.key, **self.get_kwargs())

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
        setting = cls.get_setting_definition(key, **kwargs)

        return setting.get('protected', False)

    @property
    def protected(self):
        """Returns if setting is protected from rendering."""
        return self.__class__.is_protected(self.key, **self.get_kwargs())


def settings_group_options():
    """Build up group tuple for settings based on your choices."""
    return [('', _('No group')), *[(str(a.id), str(a)) for a in Group.objects.all()]]


def update_instance_url(setting):
    """Update the first site objects domain to url."""
    site_obj = Site.objects.all().order_by('id').first()
    site_obj.domain = setting.value
    site_obj.save()


def update_instance_name(setting):
    """Update the first site objects name to instance name."""
    site_obj = Site.objects.all().order_by('id').first()
    site_obj.name = setting.value
    site_obj.save()


class InvenTreeSetting(BaseInvenTreeSetting):
    """An InvenTreeSetting object is a key:value pair used for storing single values (e.g. one-off settings values).

    The class provides a way of retrieving the value for a particular key,
    even if that key does not exist.
    """

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
            'description': _('A setting has been changed which requires a server restart'),
            'default': False,
            'validator': bool,
            'hidden': True,
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
            'validator': EmptyURLValidator(),
            'default': '',
            'after_save': update_instance_url,
        },

        'INVENTREE_DEFAULT_CURRENCY': {
            'name': _('Default Currency'),
            'description': _('Default currency'),
            'default': 'USD',
            'choices': CURRENCY_CHOICES,
        },

        'INVENTREE_DOWNLOAD_FROM_URL': {
            'name': _('Download from URL'),
            'description': _('Allow download of remote images and files from external URL'),
            'validator': bool,
            'default': False,
        },

        'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE': {
            'name': _('Download Size Limit'),
            'description': _('Maximum allowable download size for remote image'),
            'units': 'MB',
            'default': 1,
            'validator': [
                int,
                MinValueValidator(1),
                MaxValueValidator(25),
            ]
        },

        'INVENTREE_REQUIRE_CONFIRM': {
            'name': _('Require confirm'),
            'description': _('Require explicit user confirmation for certain action.'),
            'validator': bool,
            'default': True,
        },

        'INVENTREE_TREE_DEPTH': {
            'name': _('Tree Depth'),
            'description': _('Default tree depth for treeview. Deeper levels can be lazy loaded as they are needed.'),
            'default': 1,
            'validator': [
                int,
                MinValueValidator(0),
            ]
        },

        'BARCODE_ENABLE': {
            'name': _('Barcode Support'),
            'description': _('Enable barcode scanner support'),
            'default': True,
            'validator': bool,
        },

        'BARCODE_WEBCAM_SUPPORT': {
            'name': _('Barcode Webcam Support'),
            'description': _('Allow barcode scanning via webcam in browser'),
            'default': True,
            'validator': bool,
        },

        'PART_IPN_REGEX': {
            'name': _('IPN Regex'),
            'description': _('Regular expression pattern for matching Part IPN')
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
            'validator': bool
        },

        'PART_CATEGORY_PARAMETERS': {
            'name': _('Copy Category Parameter Templates'),
            'description': _('Copy category parameter templates when creating a part'),
            'default': True,
            'validator': bool
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

        'PART_SHOW_PRICE_IN_FORMS': {
            'name': _('Show Price in Forms'),
            'description': _('Display part price in some forms'),
            'default': True,
            'validator': bool,
        },

        # 2021-10-08
        # This setting exists as an interim solution for https://github.com/inventree/InvenTree/issues/2042
        # The BOM API can be extremely slow when calculating pricing information "on the fly"
        # A future solution will solve this properly,
        # but as an interim step we provide a global to enable / disable BOM pricing
        'PART_SHOW_PRICE_IN_BOM': {
            'name': _('Show Price in BOM'),
            'description': _('Include pricing information in BOM tables'),
            'default': True,
            'validator': bool,
        },

        # 2022-02-03
        # This setting exists as an interim solution for extremely slow part page load times when the part has a complex BOM
        # In an upcoming release, pricing history (and BOM pricing) will be cached,
        # rather than having to be re-calculated every time the page is loaded!
        # For now, we will simply hide part pricing by default
        'PART_SHOW_PRICE_HISTORY': {
            'name': _('Show Price History'),
            'description': _('Display historical pricing for Part'),
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
            'name': _('Create initial stock'),
            'description': _('Create initial stock on part creation'),
            'default': False,
            'validator': bool,
        },

        'PART_INTERNAL_PRICE': {
            'name': _('Internal Prices'),
            'description': _('Enable internal prices for parts'),
            'default': False,
            'validator': bool
        },

        'PART_BOM_USE_INTERNAL_PRICE': {
            'name': _('Internal Price as BOM-Price'),
            'description': _('Use the internal price (if set) in BOM-price calculations'),
            'default': False,
            'validator': bool
        },

        'PART_NAME_FORMAT': {
            'name': _('Part Name Display Format'),
            'description': _('Format to display the part name'),
            'default': "{{ part.IPN if part.IPN }}{{ ' | ' if part.IPN }}{{ part.name }}{{ ' | ' if part.revision }}"
                       "{{ part.revision if part.revision }}",
            'validator': InvenTree.validators.validate_part_name_format
        },

        'PART_CATEGORY_DEFAULT_ICON': {
            'name': _('Part Category Default Icon'),
            'description': _('Part category default icon (empty means no icon)'),
            'default': '',
        },

        'LABEL_ENABLE': {
            'name': _('Enable label printing'),
            'description': _('Enable label printing from the web interface'),
            'default': True,
            'validator': bool,
        },

        'LABEL_DPI': {
            'name': _('Label Image DPI'),
            'description': _('DPI resolution when generating image files to supply to label printing plugins'),
            'default': 300,
            'validator': [
                int,
                MinValueValidator(100),
            ]
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
            'choices': [
                ('A4', 'A4'),
                ('Legal', 'Legal'),
                ('Letter', 'Letter')
            ],
        },

        'REPORT_ENABLE_TEST_REPORT': {
            'name': _('Enable Test Reports'),
            'description': _('Enable generation of test reports'),
            'default': True,
            'validator': bool,
        },

        'REPORT_ATTACH_TEST_REPORT': {
            'name': _('Attach Test Reports'),
            'description': _('When printing a Test Report, attach a copy of the Test Report to the associated Stock Item'),
            'default': False,
            'validator': bool,
        },

        'STOCK_BATCH_CODE_TEMPLATE': {
            'name': _('Batch Code Template'),
            'description': _('Template for generating default batch codes for stock items'),
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
            'description': _('Number of days stock items are considered stale before expiring'),
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

        'BUILDORDER_REFERENCE_PATTERN': {
            'name': _('Build Order Reference Pattern'),
            'description': _('Required pattern for generating Build Order reference field'),
            'default': 'BO-{ref:04d}',
            'validator': build.validators.validate_build_order_reference_pattern,
        },

        'SALESORDER_REFERENCE_PATTERN': {
            'name': _('Sales Order Reference Pattern'),
            'description': _('Required pattern for generating Sales Order reference field'),
            'default': 'SO-{ref:04d}',
            'validator': order.validators.validate_sales_order_reference_pattern,
        },

        'SALESORDER_DEFAULT_SHIPMENT': {
            'name': _('Sales Order Default Shipment'),
            'description': _('Enable creation of default shipment with sales orders'),
            'default': False,
            'validator': bool,
        },

        'PURCHASEORDER_REFERENCE_PATTERN': {
            'name': _('Purchase Order Reference Pattern'),
            'description': _('Required pattern for generating Purchase Order reference field'),
            'default': 'PO-{ref:04d}',
            'validator': order.validators.validate_purchase_order_reference_pattern,
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

        'LOGIN_MAIL_REQUIRED': {
            'name': _('Email required'),
            'description': _('Require user to supply mail on signup'),
            'default': False,
            'validator': bool,
        },

        'LOGIN_SIGNUP_SSO_AUTO': {
            'name': _('Auto-fill SSO users'),
            'description': _('Automatically fill out user-details from SSO account-data'),
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

        'SIGNUP_GROUP': {
            'name': _('Group on signup'),
            'description': _('Group to which new users are assigned on registration'),
            'default': '',
            'choices': settings_group_options
        },

        'LOGIN_ENFORCE_MFA': {
            'name': _('Enforce MFA'),
            'description': _('Users must use multifactor security.'),
            'default': False,
            'validator': bool,
        },

        'PLUGIN_ON_STARTUP': {
            'name': _('Check plugins on startup'),
            'description': _('Check that all plugins are installed on startup - enable in container enviroments'),
            'default': False,
            'validator': bool,
            'requires_restart': True,
        },

        'PLUGIN_CHECK_SIGNATURES': {
            'name': _('Check plugin signatures'),
            'description': _('Check and show signatures for plugins'),
            'default': False,
            'validator': bool,
        },

        # Settings for plugin mixin features
        'ENABLE_PLUGINS_URL': {
            'name': _('Enable URL integration'),
            'description': _('Enable plugins to add URL routes'),
            'default': False,
            'validator': bool,
            'requires_restart': True,
        },

        'ENABLE_PLUGINS_NAVIGATION': {
            'name': _('Enable navigation integration'),
            'description': _('Enable plugins to integrate into navigation'),
            'default': False,
            'validator': bool,
            'requires_restart': True,
        },

        'ENABLE_PLUGINS_APP': {
            'name': _('Enable app integration'),
            'description': _('Enable plugins to add apps'),
            'default': False,
            'validator': bool,
            'requires_restart': True,
        },

        'ENABLE_PLUGINS_SCHEDULE': {
            'name': _('Enable schedule integration'),
            'description': _('Enable plugins to run scheduled tasks'),
            'default': False,
            'validator': bool,
            'requires_restart': True,
        },

        'ENABLE_PLUGINS_EVENTS': {
            'name': _('Enable event integration'),
            'description': _('Enable plugins to respond to internal events'),
            'default': False,
            'validator': bool,
            'requires_restart': True,
        },
    }

    class Meta:
        """Meta options for InvenTreeSetting."""

        verbose_name = "InvenTree Setting"
        verbose_name_plural = "InvenTree Settings"

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
        else:
            return False


class InvenTreeUserSetting(BaseInvenTreeSetting):
    """An InvenTreeSetting object with a usercontext."""

    SETTINGS = {
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

        'PART_RECENT_COUNT': {
            'name': _('Recent Part Count'),
            'description': _('Number of recent parts to display on index page'),
            'default': 10,
            'validator': [int, MinValueValidator(1)]
        },

        'HOMEPAGE_BOM_VALIDATION': {
            'name': _('Show unvalidated BOMs'),
            'description': _('Show BOMs that await validation on the homepage'),
            'default': True,
            'validator': bool,
        },

        'HOMEPAGE_STOCK_RECENT': {
            'name': _('Show recent stock changes'),
            'description': _('Show recently changed stock items on the homepage'),
            'default': True,
            'validator': bool,
        },

        'STOCK_RECENT_COUNT': {
            'name': _('Recent Stock Count'),
            'description': _('Number of recent stock items to display on index page'),
            'default': 10,
            'validator': [int, MinValueValidator(1)]
        },

        'HOMEPAGE_STOCK_LOW': {
            'name': _('Show low stock'),
            'description': _('Show low stock items on the homepage'),
            'default': True,
            'validator': bool,
        },

        'HOMEPAGE_STOCK_DEPLETED': {
            'name': _('Show depleted stock'),
            'description': _('Show depleted stock items on the homepage'),
            'default': True,
            'validator': bool,
        },

        'HOMEPAGE_STOCK_NEEDED': {
            'name': _('Show needed stock'),
            'description': _('Show stock items needed for builds on the homepage'),
            'default': True,
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

        "LABEL_INLINE": {
            'name': _('Inline label display'),
            'description': _('Display PDF labels in the browser, instead of downloading as a file'),
            'default': True,
            'validator': bool,
        },

        "REPORT_INLINE": {
            'name': _('Inline report display'),
            'description': _('Display PDF reports in the browser, instead of downloading as a file'),
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
            'name': _('Seach Supplier Parts'),
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
            'name': _("Hide Inactive Parts"),
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
            'description': _('Exclude stock items which are not available from the search preview window'),
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

        'SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS': {
            'name': _('Search Purchase Orders'),
            'description': _('Display purchase orders in search preview window'),
            'default': True,
            'validator': bool,
        },

        'SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS': {
            'name': _('Exclude Inactive Purchase Orders'),
            'description': _('Exclude inactive purchase orders from search preview window'),
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
            'description': _('Exclude inactive sales orders from search preview window'),
            'validator': bool,
            'default': True,
        },

        'SEARCH_PREVIEW_RESULTS': {
            'name': _('Search Preview Results'),
            'description': _('Number of results to show in each section of the search preview window'),
            'default': 10,
            'validator': [int, MinValueValidator(1)]
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
            ]
        },

        'DISPLAY_SCHEDULE_TAB': {
            'name': _('Part Scheduling'),
            'description': _('Display part scheduling information'),
            'default': True,
            'validator': bool,
        },
    }

    class Meta:
        """Meta options for InvenTreeUserSetting."""

        verbose_name = "InvenTree User Setting"
        verbose_name_plural = "InvenTree User Settings"
        constraints = [
            models.UniqueConstraint(fields=['key', 'user'], name='unique key and user')
        ]

    key = models.CharField(
        max_length=50,
        blank=False,
        unique=False,
        help_text=_('Settings key (must be unique - case insensitive'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    def validate_unique(self, exclude=None, **kwargs):
        """Return if the setting (including key) is unique."""
        return super().validate_unique(exclude=exclude, user=self.user)

    def to_native_value(self):
        """Return the "pythonic" value, e.g. convert "True" to True, and "1" to 1."""
        return self.__class__.get_setting(self.key, user=self.user)

    def get_kwargs(self):
        """Explicit kwargs required to uniquely identify a particular setting object, in addition to the 'key' parameter."""
        return {
            'user': self.user,
        }


class PriceBreak(models.Model):
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
        decimal_places=4,
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
            logger.warning(f"No currency conversion rate available for {self.price_currency} -> {currency_code}")
            return self.price.amount

        return converted.amount


def get_price(instance, quantity, moq=True, multiples=True, currency=None, break_name: str = 'price_breaks'):
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
    multiples = (quantity % 1 == 0)

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
    else:
        return None


class ColorTheme(models.Model):
    """Color Theme Setting."""
    name = models.CharField(max_length=20,
                            default='',
                            blank=True)

    user = models.CharField(max_length=150,
                            unique=True)

    @classmethod
    def get_color_themes_choices(cls):
        """Get all color themes from static folder."""
        if not dj_settings.STATIC_COLOR_THEMES_DIR.exists():
            logger.error('Theme directory does not exsist')
            return []

        # Get files list from css/color-themes/ folder
        files_list = []

        for file in dj_settings.STATIC_COLOR_THEMES_DIR.iterdir():
            files_list.append([file.stem, file.suffix])

        # Get color themes choices (CSS sheets)
        choices = [(file_name.lower(), _(file_name.replace('-', ' ').title()))
                   for file_name, file_ext in files_list
                   if file_ext == '.css']

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


class GenericWebTransaction(models.Model):
    """Generic web transaction model.

    Attributes:
        message_id: Unique identifier for this message,
        host: Host from which this message was received,
        header: Header of this message,
        body: Body of this message,
        endpoint: Endpoint on which this message was received,
        worked_on: Was the work on this message finished?
    """
    class Meta:
        """Define this as abstract -> no DB entry is created."""

        abstract = True

    message_id = models.UUIDField(
        verbose_name=_('Message ID'),
        help_text=_('Unique identifier for this transaction'),
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
        blank=True, null=True,
        verbose_name=_('Header'),
        help_text=_('Header of this message'),
        editable=False,
    )

    body = models.JSONField(
        blank=True, null=True,
        verbose_name=_('Body'),
        help_text=_('Body of this message'),
        editable=False,
    )


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
    TOKEN_NAME = "Token"
    VERIFICATION_METHOD = VerificationMethod.NONE

    MESSAGE_OK = "Message was received."
    MESSAGE_TOKEN_ERROR = "Incorrect token in header."

    endpoint_id = models.CharField(
        max_length=255,
        verbose_name=_('Endpoint'),
        help_text=_('Endpoint at which this webhook is received'),
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=255,
        blank=True, null=True,
        verbose_name=_('Name'),
        help_text=_('Name for this webhook')
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Is this webhook active')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    token = models.CharField(
        max_length=255,
        blank=True, null=True,
        verbose_name=_('Token'),
        help_text=_('Token for access'),
        default=uuid.uuid4,
    )

    secret = models.CharField(
        max_length=255,
        blank=True, null=True,
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
        """Process the webhook incomming.

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
        token = headers.get(self.TOKEN_NAME, "")

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
            digest = hmac.new(self.secret.encode('utf-8'), request.body, hashlib.sha256).digest()
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
            header=json.dumps({key: val for key, val in headers.items()}),
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


class WebhookMessage(GenericWebTransaction):
    """Defines a webhook message.

    Attributes:
        message_id: Unique identifier for this message,
        host: Host from which this message was received,
        header: Header of this message,
        body: Body of this message,
        endpoint: Endpoint on which this message was received,
        worked_on: Was the work on this message finished?
    """

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Endpoint'),
        help_text=_('Endpoint on which this message was received'),
    )

    worked_on = models.BooleanField(
        default=False,
        verbose_name=_('Worked on'),
        help_text=_('Was the work on this message finished?'),
    )


class NotificationEntry(models.Model):
    """A NotificationEntry records the last time a particular notifaction was sent out.

    It is recorded to ensure that notifications are not sent out "too often" to users.

    Attributes:
    - key: A text entry describing the notification e.g. 'part.notify_low_stock'
    - uid: An (optional) numerical ID for a particular instance
    - date: The last time this notification was sent
    """

    class Meta:
        """Meta options for NotificationEntry."""

        unique_together = [
            ('key', 'uid'),
        ]

    key = models.CharField(
        max_length=250,
        blank=False,
    )

    uid = models.IntegerField(
    )

    updated = models.DateTimeField(
        auto_now=True,
        null=False,
    )

    @classmethod
    def check_recent(cls, key: str, uid: int, delta: timedelta):
        """Test if a particular notification has been sent in the specified time period."""
        since = datetime.now().date() - delta

        entries = cls.objects.filter(
            key=key,
            uid=uid,
            updated__gte=since
        )

        return entries.exists()

    @classmethod
    def notify(cls, key: str, uid: int):
        """Notify the database that a particular notification has been sent out."""
        entry, created = cls.objects.get_or_create(
            key=key,
            uid=uid
        )

        entry.save()


class NotificationMessage(models.Model):
    """A NotificationEntry records the last time a particular notifaction was sent out.

    It is recorded to ensure that notifications are not sent out "too often" to users.

    Attributes:
    - key: A text entry describing the notification e.g. 'part.notify_low_stock'
    - uid: An (optional) numerical ID for a particular instance
    - date: The last time this notification was sent
    """

    # generic link to target
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='notification_target',
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

    source_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

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

    category = models.CharField(
        max_length=250,
        blank=False,
    )

    name = models.CharField(
        max_length=250,
        blank=False,
    )

    message = models.CharField(
        max_length=250,
        blank=True,
        null=True,
    )

    creation = models.DateTimeField(
        auto_now_add=True,
    )

    read = models.BooleanField(
        default=False,
    )

    @staticmethod
    def get_api_url():
        """Return API endpoint."""
        return reverse('api-notifications-list')

    def age(self):
        """Age of the message in seconds."""
        delta = now() - self.creation
        return delta.seconds

    def age_human(self):
        """Humanized age."""
        return naturaltime(self.creation)


class WebConnection(models.Model):
    """Defines a Connection for a plugin or the core code base..

    Attributes:
        name: TODO,
        active: TODO,
        creator: TODO,
        creation: TODO,
        owner: TODO,
        updated: TODO,
    """

    name = models.CharField(
        max_length=255,
        blank=True, null=True,
        verbose_name=_('Name'),
        help_text=_('Name for this webhook')
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Is this webhook active')
    )

    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('User'),
        help_text=_('User'),
    )

    creation = models.DateTimeField(
        auto_now_add=True,
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Owner'),
        help_text=_('Select Owner')
    )

    updated = models.DateTimeField(
        auto_now=True,
        null=False,
    )


@dataclass()
class WebConnectionData:
    """Type definition for a WebConnection."""
    name: str
    description: str
    settings: List[dict]
    multiple: bool = False


class WebConnectionTransaction(GenericWebTransaction):
    """Records a webtransaction.

    Attributes:
        message_id: Unique identifier for this message,
        host: Host for which this message was processed,
        header: Header of this message,
        body: Body of this message,
        connection: Connection for which this message was processed,
        processed: Was the work on this transaction finished?
    """

    connection = models.ForeignKey(
        WebConnection,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Connection'),
        help_text=_('Connection for which this message was processed'),
    )

    processed = models.BooleanField(
        default=False,
        verbose_name=_('Processed'),
        help_text=_('Was the work on this transaction finished?'),
    )
