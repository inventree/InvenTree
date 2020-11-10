"""
Common database model definitions.
These models are 'generic' and do not fit a particular business logic object.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import decimal

from django.db import models
from django.conf import settings

import djmoney.settings

from django.utils.translation import ugettext as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

import InvenTree.helpers
import InvenTree.fields


class InvenTreeSetting(models.Model):
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

        'INVENTREE_COMPANY_NAME': {
            'name': _('Company name'),
            'description': _('Internal company name'),
            'default': 'My company name',
        },

        'INVENTREE_DEFAULT_CURRENCY': {
            'name': _('Default Currency'),
            'description': _('Default currency'),
            'default': 'USD',
            'choices': djmoney.settings.CURRENCY_CHOICES,
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

        'PART_COMPONENT': {
            'name': _('Component'),
            'description': _('Parts can be used as sub-components by default'),
            'default': True,
            'validator': bool,
        },

        'PART_PURCHASEABLE': {
            'name': _('Purchaseable'),
            'description': _('Parts are purchaseable by default'),
            'default': False,
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
        },

        'PURCHASEORDER_REFERENCE_PREFIX': {
            'name': _('Purchase Order Reference Prefix'),
            'description': _('Prefix value for purchase order reference'),
        },
    }

    class Meta:
        verbose_name = "InvenTree Setting"
        verbose_name_plural = "InvenTree Settings"

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
    def get_default_value(cls, key):
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

        """
        TODO:
        if type(choices) is function:
            # Evaluate the function (we expect it will return a list of tuples...)
            return choices()
        """
        
        return choices

    @classmethod
    def get_setting_object(cls, key):
        """
        Return an InvenTreeSetting object matching the given key.

        - Key is case-insensitive
        - Returns None if no match is made
        """

        key = str(key).strip().upper()

        try:
            setting = InvenTreeSetting.objects.filter(key__iexact=key).first()
        except (InvenTreeSetting.DoesNotExist):
            # Create the setting if it does not exist
            setting = InvenTreeSetting.create(
                key=key,
                value=InvenTreeSetting.get_default_value(key)
            )

        return setting

    @classmethod
    def get_setting_pk(cls, key):
        """
        Return the primary-key value for a given setting.

        If the setting does not exist, return None
        """

        setting = InvenTreeSetting.get_setting_object(cls)

        if setting:
            return setting.pk
        else:
            return None

    @classmethod
    def get_setting(cls, key, backup_value=None):
        """
        Get the value of a particular setting.
        If it does not exist, return the backup value (default = None)
        """

        # If no backup value is specified, atttempt to retrieve a "default" value
        if backup_value is None:
            backup_value = cls.get_default_value(key)

        setting = InvenTreeSetting.get_setting_object(key)

        if setting:
            value = setting.value

            # If the particular setting is defined as a boolean, cast the value to a boolean
            if setting.is_bool():
                value = InvenTree.helpers.str2bool(value)

        else:
            value = backup_value

        return value

    @classmethod
    def set_setting(cls, key, value, user, create=True):
        """
        Set the value of a particular setting.
        If it does not exist, option to create it.

        Args:
            key: settings key
            value: New value
            user: User object (must be staff member to update a core setting)
            create: If True, create a new setting if the specified key does not exist.
        """

        if not user.is_staff:
            return

        try:
            setting = InvenTreeSetting.objects.get(key__iexact=key)
        except InvenTreeSetting.DoesNotExist:

            if create:
                setting = InvenTreeSetting(key=key)
            else:
                return

        # Enforce standard boolean representation
        if setting.is_bool():
            value = InvenTree.helpers.str2bool(value)
            
        setting.value = str(value)
        setting.save()

    key = models.CharField(max_length=50, blank=False, unique=True, help_text=_('Settings key (must be unique - case insensitive'))

    value = models.CharField(max_length=200, blank=True, unique=False, help_text=_('Settings value'))

    @property
    def name(self):
        return InvenTreeSetting.get_setting_name(self.key)

    @property
    def default_value(self):
        return InvenTreeSetting.get_default_value(self.key)

    @property
    def description(self):
        return InvenTreeSetting.get_setting_description(self.key)

    @property
    def units(self):
        return InvenTreeSetting.get_setting_units(self.key)

    def clean(self):
        """
        If a validator (or multiple validators) are defined for a particular setting key,
        run them against the 'value' field.
        """

        super().clean()

        validator = InvenTreeSetting.get_setting_validator(self.key)

        if validator is not None:
            self.run_validator(validator)

    def run_validator(self, validator):
        """
        Run a validator against the 'value' field for this InvenTreeSetting object.
        """

        if validator is None:
            return

        # If a list of validators is supplied, iterate through each one
        if type(validator) in [list, tuple]:
            for v in validator:
                self.run_validator(v)
            
            return

        # Check if a 'type' has been specified for this value
        if type(validator) == type:

            if validator == bool:
                # Value must "look like" a boolean value
                if InvenTree.helpers.is_bool(self.value):
                    # Coerce into either "True" or "False"
                    self.value = str(InvenTree.helpers.str2bool(self.value))
                else:
                    raise ValidationError({
                        'value': _('Value must be a boolean value')
                    })

    def validate_unique(self, exclude=None):
        """ Ensure that the key:value pair is unique.
        In addition to the base validators, this ensures that the 'key'
        is unique, using a case-insensitive comparison.
        """

        super().validate_unique(exclude)

        try:
            setting = InvenTreeSetting.objects.exclude(id=self.id).filter(key__iexact=self.key)
            if setting.exists():
                raise ValidationError({'key': _('Key string must be unique')})
        except InvenTreeSetting.DoesNotExist:
            pass

    def choices(self):
        """
        Return the available choices for this setting (or None if no choices are defined)
        """

        return InvenTreeSetting.get_setting_choices(self.key)

    def is_bool(self):
        """
        Check if this setting is required to be a boolean value
        """

        validator = InvenTreeSetting.get_setting_validator(self.key)

        return validator == bool

    def as_bool(self):
        """
        Return the value of this setting converted to a boolean value.

        Warning: Only use on values where is_bool evaluates to true!
        """

        return InvenTree.helpers.str2bool(self.value)


class Currency(models.Model):
    """
    A Currency object represents a particular unit of currency.
    Each Currency has a scaling factor which relates it to the base currency.
    There must be one (and only one) currency which is selected as the base currency,
    and each other currency is calculated relative to it.

    Attributes:
        symbol: Currency symbol e.g. $
        suffix: Currency suffix e.g. AUD
        description: Long-form description e.g. "Australian Dollars"
        value: The value of this currency compared to the base currency.
        base: True if this currency is the base currency

    """

    symbol = models.CharField(max_length=10, blank=False, unique=False, help_text=_('Currency Symbol e.g. $'))

    suffix = models.CharField(max_length=10, blank=False, unique=True, help_text=_('Currency Suffix e.g. AUD'))

    description = models.CharField(max_length=100, blank=False, help_text=_('Currency Description'))

    value = models.DecimalField(default=1.0, max_digits=10, decimal_places=5, validators=[MinValueValidator(0.00001), MaxValueValidator(100000)], help_text=_('Currency Value'))

    base = models.BooleanField(default=False, help_text=_('Use this currency as the base currency'))

    class Meta:
        verbose_name_plural = 'Currencies'

    def __str__(self):
        """ Format string for currency representation """
        s = "{sym} {suf} - {desc}".format(
            sym=self.symbol,
            suf=self.suffix,
            desc=self.description
        )

        if self.base:
            s += " (Base)"
        
        else:
            s += " = {v}".format(v=self.value)

        return s

    def save(self, *args, **kwargs):
        """ Validate the model before saving

        - Ensure that there is only one base currency!
        """

        # If this currency is set as the base currency, ensure no others are
        if self.base:
            for cur in Currency.objects.filter(base=True).exclude(pk=self.pk):
                cur.base = False
                cur.save()

        # If there are no currencies set as the base currency, set this as base
        if not Currency.objects.exclude(pk=self.pk).filter(base=True).exists():
            self.base = True

        # If this is the base currency, ensure value is set to unity
        if self.base:
            self.value = 1.0

        super().save(*args, **kwargs)


class PriceBreak(models.Model):
    """
    Represents a PriceBreak model
    """

    class Meta:
        abstract = True

    quantity = InvenTree.fields.RoundingDecimalField(max_digits=15, decimal_places=5, default=1, validators=[MinValueValidator(1)])

    cost = InvenTree.fields.RoundingDecimalField(max_digits=10, decimal_places=5, validators=[MinValueValidator(0)])

    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.SET_NULL)

    @property
    def symbol(self):
        return self.currency.symbol if self.currency else ''

    @property
    def suffix(self):
        return self.currency.suffix if self.currency else ''

    @property
    def converted_cost(self):
        """
        Return the cost of this price break, converted to the base currency
        """

        scaler = decimal.Decimal(1.0)

        if self.currency:
            scaler = self.currency.value

        return self.cost * scaler


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
