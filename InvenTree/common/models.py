"""
Common database model definitions.
These models are 'generic' and do not fit a particular business logic object.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import decimal
import math
import uuid

from django.db import models, transaction
from django.contrib.auth.models import User, Group
from django.db.utils import IntegrityError, OperationalError
from django.conf import settings

from djmoney.settings import CURRENCY_CHOICES
from djmoney.contrib.exchange.models import convert_money
from djmoney.contrib.exchange.exceptions import MissingRate

from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator, URLValidator
from django.core.exceptions import ValidationError

import InvenTree.helpers
import InvenTree.fields
import InvenTree.validators

import logging


logger = logging.getLogger('inventree')


class BaseInvenTreeSetting(models.Model):
    """
    An base InvenTreeSetting object is a key:value pair used for storing
    single values (e.g. one-off settings values).
    """

    GLOBAL_SETTINGS = {}

    class Meta:
        abstract = True

    @classmethod
    def allValues(cls, user=None):
        """
        Return a dict of "all" defined global settings.

        This performs a single database lookup,
        and then any settings which are not *in* the database
        are assigned their default values
        """

        results = cls.objects.all()

        if user is not None:
            results = results.filter(user=user)

        # Query the database
        settings = {}

        for setting in results:
            if setting.key:
                settings[setting.key.upper()] = setting.value

        # Specify any "default" values which are not in the database
        for key in cls.GLOBAL_SETTINGS.keys():

            if key.upper() not in settings:

                settings[key.upper()] = cls.get_setting_default(key)

        for key, value in settings.items():
            validator = cls.get_setting_validator(key)

            if cls.validator_is_bool(validator):
                value = InvenTree.helpers.str2bool(value)
            elif cls.validator_is_int(validator):
                try:
                    value = int(value)
                except ValueError:
                    value = cls.get_setting_default(key)

            settings[key] = value

        return settings

    @classmethod
    def get_setting_name(cls, key):
        """
        Return the name of a particular setting.

        If it does not exist, return an empty string.
        """

        key = str(key).strip().upper()

        if key in cls.GLOBAL_SETTINGS:
            setting = cls.GLOBAL_SETTINGS[key]
            return setting.get('name', '')
        else:
            return ''

    @classmethod
    def get_setting_description(cls, key):
        """
        Return the description for a particular setting.

        If it does not exist, return an empty string.
        """

        key = str(key).strip().upper()

        if key in cls.GLOBAL_SETTINGS:
            setting = cls.GLOBAL_SETTINGS[key]
            return setting.get('description', '')
        else:
            return ''

    @classmethod
    def get_setting_units(cls, key):
        """
        Return the units for a particular setting.

        If it does not exist, return an empty string.
        """

        key = str(key).strip().upper()

        if key in cls.GLOBAL_SETTINGS:
            setting = cls.GLOBAL_SETTINGS[key]
            return setting.get('units', '')
        else:
            return ''

    @classmethod
    def get_setting_validator(cls, key):
        """
        Return the validator for a particular setting.

        If it does not exist, return None
        """

        key = str(key).strip().upper()

        if key in cls.GLOBAL_SETTINGS:
            setting = cls.GLOBAL_SETTINGS[key]
            return setting.get('validator', None)
        else:
            return None

    @classmethod
    def get_setting_default(cls, key):
        """
        Return the default value for a particular setting.

        If it does not exist, return an empty string
        """

        key = str(key).strip().upper()

        if key in cls.GLOBAL_SETTINGS:
            setting = cls.GLOBAL_SETTINGS[key]
            return setting.get('default', '')
        else:
            return ''

    @classmethod
    def get_setting_choices(cls, key):
        """
        Return the validator choices available for a particular setting.
        """

        key = str(key).strip().upper()

        if key in cls.GLOBAL_SETTINGS:
            setting = cls.GLOBAL_SETTINGS[key]
            choices = setting.get('choices', None)
        else:
            choices = None

        if callable(choices):
            # Evaluate the function (we expect it will return a list of tuples...)
            return choices()

        return choices

    @classmethod
    def get_filters(cls, key, **kwargs):
        return {'key__iexact': key}

    @classmethod
    def get_setting_object(cls, key, **kwargs):
        """
        Return an InvenTreeSetting object matching the given key.

        - Key is case-insensitive
        - Returns None if no match is made
        """

        key = str(key).strip().upper()

        try:
            setting = cls.objects.filter(**cls.get_filters(key, **kwargs)).first()
        except (ValueError, cls.DoesNotExist):
            setting = None
        except (IntegrityError, OperationalError):
            setting = None

        # Setting does not exist! (Try to create it)
        if not setting:

            setting = cls(key=key, value=cls.get_setting_default(key), **kwargs)

            try:
                # Wrap this statement in "atomic", so it can be rolled back if it fails
                with transaction.atomic():
                    setting.save()
            except (IntegrityError, OperationalError):
                # It might be the case that the database isn't created yet
                pass

        return setting

    @classmethod
    def get_setting_pk(cls, key):
        """
        Return the primary-key value for a given setting.

        If the setting does not exist, return None
        """

        setting = cls.get_setting_object(cls)

        if setting:
            return setting.pk
        else:
            return None

    @classmethod
    def get_setting(cls, key, backup_value=None, **kwargs):
        """
        Get the value of a particular setting.
        If it does not exist, return the backup value (default = None)
        """

        # If no backup value is specified, atttempt to retrieve a "default" value
        if backup_value is None:
            backup_value = cls.get_setting_default(key)

        setting = cls.get_setting_object(key, **kwargs)

        if setting:
            value = setting.value

            # If the particular setting is defined as a boolean, cast the value to a boolean
            if setting.is_bool():
                value = InvenTree.helpers.str2bool(value)

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
        """
        Set the value of a particular setting.
        If it does not exist, option to create it.

        Args:
            key: settings key
            value: New value
            change_user: User object (must be staff member to update a core setting)
            create: If True, create a new setting if the specified key does not exist.
        """

        if change_user is not None and not change_user.is_staff:
            return

        try:
            setting = cls.objects.get(**cls.get_filters(key, **kwargs))
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

    key = models.CharField(max_length=50, blank=False, unique=False, help_text=_('Settings key (must be unique - case insensitive'))

    value = models.CharField(max_length=200, blank=True, unique=False, help_text=_('Settings value'))

    @property
    def name(self):
        return self.__class__.get_setting_name(self.key)

    @property
    def default_value(self):
        return self.__class__.get_setting_default(self.key)

    @property
    def description(self):
        return self.__class__.get_setting_description(self.key)

    @property
    def units(self):
        return self.__class__.get_setting_units(self.key)

    def clean(self):
        """
        If a validator (or multiple validators) are defined for a particular setting key,
        run them against the 'value' field.
        """

        super().clean()

        validator = self.__class__.get_setting_validator(self.key)

        if self.is_bool():
            self.value = InvenTree.helpers.str2bool(self.value)

        if self.is_int():
            try:
                self.value = int(self.value)
            except (ValueError):
                raise ValidationError(_('Must be an integer value'))

        if validator is not None:
            self.run_validator(validator)

    def run_validator(self, validator):
        """
        Run a validator against the 'value' field for this InvenTreeSetting object.
        """

        if validator is None:
            return

        value = self.value

        # Boolean validator
        if self.is_bool():
            # Value must "look like" a boolean value
            if InvenTree.helpers.is_bool(value):
                # Coerce into either "True" or "False"
                value = InvenTree.helpers.str2bool(value)
            else:
                raise ValidationError({
                    'value': _('Value must be a boolean value')
                })

        # Integer validator
        if self.is_int():

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
            validator(self.value)

    def validate_unique(self, exclude=None, **kwargs):
        """ Ensure that the key:value pair is unique.
        In addition to the base validators, this ensures that the 'key'
        is unique, using a case-insensitive comparison.
        """

        super().validate_unique(exclude)

        try:
            setting = self.__class__.objects.exclude(id=self.id).filter(**self.get_filters(self.key, **kwargs))
            if setting.exists():
                raise ValidationError({'key': _('Key string must be unique')})
        except self.DoesNotExist:
            pass

    def choices(self):
        """
        Return the available choices for this setting (or None if no choices are defined)
        """

        return self.__class__.get_setting_choices(self.key)

    def is_bool(self):
        """
        Check if this setting is required to be a boolean value
        """

        validator = self.__class__.get_setting_validator(self.key)

        return self.__class__.validator_is_bool(validator)

    def as_bool(self):
        """
        Return the value of this setting converted to a boolean value.

        Warning: Only use on values where is_bool evaluates to true!
        """

        return InvenTree.helpers.str2bool(self.value)

    @classmethod
    def validator_is_bool(cls, validator):

        if validator == bool:
            return True

        if type(validator) in [list, tuple]:
            for v in validator:
                if v == bool:
                    return True

        return False

    def is_int(self):
        """
        Check if the setting is required to be an integer value:
        """

        validator = self.__class__.get_setting_validator(self.key)

        return self.__class__.validator_is_int(validator)

    @classmethod
    def validator_is_int(cls, validator):

        if validator == int:
            return True

        if type(validator) in [list, tuple]:
            for v in validator:
                if v == int:
                    return True

        return False

    def as_int(self):
        """
        Return the value of this setting converted to a boolean value.

        If an error occurs, return the default value
        """

        try:
            value = int(self.value)
        except (ValueError, TypeError):
            value = self.default_value()

        return value


def settings_group_options():
    """build up group tuple for settings based on gour choices"""
    return [('', _('No group')), *[(str(a.id), str(a)) for a in Group.objects.all()]]


class InvenTreeSetting(BaseInvenTreeSetting):
    """
    An InvenTreeSetting object is a key:value pair used for storing
    single values (e.g. one-off settings values).

    The class provides a way of retrieving the value for a particular key,
    even if that key does not exist.
    """

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

    GLOBAL_SETTINGS = {

        'INVENTREE_INSTANCE': {
            'name': _('InvenTree Instance Name'),
            'default': 'InvenTree server',
            'description': _('String descriptor for the server instance'),
        },

        'INVENTREE_INSTANCE_TITLE': {
            'name': _('Use instance name'),
            'description': _('Use the instance name in the title-bar'),
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
            'validator': URLValidator(),
            'default': '',
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

        'BARCODE_ENABLE': {
            'name': _('Barcode Support'),
            'description': _('Enable barcode scanner support'),
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
            'name': _('Test Reports'),
            'description': _('Enable generation of test reports'),
            'default': True,
            'validator': bool,
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

        'STOCK_GROUP_BY_PART': {
            'name': _('Group by Part'),
            'description': _('Group stock items by part reference in table views'),
            'default': True,
            'validator': bool,
        },

        'BUILDORDER_REFERENCE_PREFIX': {
            'name': _('Build Order Reference Prefix'),
            'description': _('Prefix value for build order reference'),
            'default': 'BO',
        },

        'BUILDORDER_REFERENCE_REGEX': {
            'name': _('Build Order Reference Regex'),
            'description': _('Regular expression pattern for matching build order reference')
        },

        'SALESORDER_REFERENCE_PREFIX': {
            'name': _('Sales Order Reference Prefix'),
            'description': _('Prefix value for sales order reference'),
            'default': 'SO',
        },

        'PURCHASEORDER_REFERENCE_PREFIX': {
            'name': _('Purchase Order Reference Prefix'),
            'description': _('Prefix value for purchase order reference'),
            'default': 'PO',
        },

        # login / SSO
        'LOGIN_ENABLE_PWD_FORGOT': {
            'name': _('Enable password forgot'),
            'description': _('Enable password forgot function on the login-pages'),
            'default': True,
            'validator': bool,
        },
        'LOGIN_ENABLE_REG': {
            'name': _('Enable registration'),
            'description': _('Enable self-registration for users on the login-pages'),
            'default': False,
            'validator': bool,
        },
        'LOGIN_ENABLE_SSO': {
            'name': _('Enable SSO'),
            'description': _('Enable SSO on the login-pages'),
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
            'description': _('Group new user are asigned on registration'),
            'default': '',
            'choices': settings_group_options
        },
        'ENABLE_PLUGINS_URL': {
            'name': _('Enable URL integration'),
            'description': _('Enable plugins to add URL routes'),
            'default': False,
            'validator': bool,
        },
        'ENABLE_PLUGINS_NAVIGATION': {
            'name': _('Enable navigation integration'),
            'description': _('Enable plugins to integrate into navigation'),
            'default': False,
            'validator': bool,
        },
        'ENABLE_PLUGINS_SETTING': {
            'name': _('Enable setting integration'),
            'description': _('Enable plugins to integrate into inventree settings'),
            'default': False,
            'validator': bool,
        },
    }

    class Meta:
        verbose_name = "InvenTree Setting"
        verbose_name_plural = "InvenTree Settings"

    key = models.CharField(
        max_length=50,
        blank=False,
        unique=True,
        help_text=_('Settings key (must be unique - case insensitive'),
    )


class InvenTreeUserSetting(BaseInvenTreeSetting):
    """
    An InvenTreeSetting object with a usercontext
    """

    GLOBAL_SETTINGS = {
        'HOMEPAGE_PART_STARRED': {
            'name': _('Show starred parts'),
            'description': _('Show starred parts on the homepage'),
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

        'SEARCH_PREVIEW_RESULTS': {
            'name': _('Search Preview Results'),
            'description': _('Number of results to show in search preview window'),
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
        }
    }

    class Meta:
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

    @classmethod
    def get_setting_object(cls, key, user):
        return super().get_setting_object(key, user=user)

    def validate_unique(self, exclude=None):
        return super().validate_unique(exclude=exclude, user=self.user)

    @classmethod
    def get_filters(cls, key, **kwargs):
        return {
            'key__iexact': key,
            'user__id': kwargs['user'].id
        }


class PriceBreak(models.Model):
    """
    Represents a PriceBreak model
    """

    class Meta:
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
        """
        Convert the unit-price at this price break to the specified currency code.

        Args:
            currency_code - The currency code to convert to (e.g "USD" or "AUD")
        """

        try:
            converted = convert_money(self.price, currency_code)
        except MissingRate:
            logger.warning(f"No currency conversion rate available for {self.price_currency} -> {currency_code}")
            return self.price.amount

        return converted.amount


def get_price(instance, quantity, moq=True, multiples=True, currency=None, break_name: str = 'price_breaks'):
    """ Calculate the price based on quantity price breaks.

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
    """ Color Theme Setting """

    default_color_theme = ('', _('Default'))

    name = models.CharField(max_length=20,
                            default='',
                            blank=True)

    user = models.CharField(max_length=150,
                            unique=True)

    @classmethod
    def get_color_themes_choices(cls):
        """ Get all color themes from static folder """

        # Get files list from css/color-themes/ folder
        files_list = []
        for file in os.listdir(settings.STATIC_COLOR_THEMES_DIR):
            files_list.append(os.path.splitext(file))

        # Get color themes choices (CSS sheets)
        choices = [(file_name.lower(), _(file_name.replace('-', ' ').title()))
                   for file_name, file_ext in files_list
                   if file_ext == '.css' and file_name.lower() != 'default']

        # Add default option as empty option
        choices.insert(0, cls.default_color_theme)

        return choices

    @classmethod
    def is_valid_choice(cls, user_color_theme):
        """ Check if color theme is valid choice """
        try:
            user_color_theme_name = user_color_theme.name
        except AttributeError:
            return False

        for color_theme in cls.get_color_themes_choices():
            if user_color_theme_name == color_theme[0]:
                return True

        return False


class WebhookEndpoint(models.Model):
    """ Defines a Webhook entdpoint

    Attributes:
        endpoint_id: Path to the webhook,
        name: Name of the webhook,
        active: Is this webhook active?,
        user: User associated with webhook,
        token: Token for sending a webhook,
        secret: Shared secret for HMAC verification,
    """

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


class WebhookMessage(models.Model):
    """ Defines a webhook message

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
