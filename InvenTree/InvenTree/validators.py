"""
Custom field validators for InvenTree
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import common.models

import re


def allowable_url_schemes():
    """ Return the list of allowable URL schemes.
    In addition to the default schemes allowed by Django,
    the install configuration file (config.yaml) can specify
    extra schemas """

    # Default schemes
    schemes = ['http', 'https', 'ftp', 'ftps']

    extra = settings.EXTRA_URL_SCHEMES

    for e in extra:
        if e.lower() not in schemes:
            schemes.append(e.lower())

    return schemes


def validate_part_name(value):
    """ Prevent some illegal characters in part names.
    """

    for c in ['|', '#', '$', '{', '}']:
        if c in str(value):
            raise ValidationError(
                _('Invalid character in part name')
            )


def validate_part_ipn(value):
    """ Validate the Part IPN against regex rule """

    pattern = common.models.InvenTreeSetting.get_setting('part_ipn_regex')

    if pattern:
        match = re.search(pattern, value)

        if match is None:
            raise ValidationError(_('IPN must match regex pattern') + " '{pat}'".format(pat=pattern))


def validate_tree_name(value):
    """ Prevent illegal characters in tree item names """

    for c in "!@#$%^&*'\"\\/[]{}<>,|+=~`\"":
        if c in str(value):
            raise ValidationError(_('Illegal character in name ({x})'.format(x=c)))


def validate_overage(value):
    """ Validate that a BOM overage string is properly formatted.

    An overage string can look like:

    - An integer number ('1' / 3 / 4)
    - A percentage ('5%' / '10 %')
    """

    value = str(value).lower().strip()

    # First look for a simple integer value
    try:
        i = int(value)

        if i < 0:
            raise ValidationError(_("Overage value must not be negative"))
        
        # Looks like an integer!
        return True
    except ValueError:
        pass

    # Now look for a percentage value
    if value.endswith('%'):
        v = value[:-1].strip()

        # Does it look like a number?
        try:
            f = float(v)

            if f < 0:
                raise ValidationError(_("Overage value must not be negative"))
            elif f > 100:
                raise ValidationError(_("Overage must not exceed 100%"))

            return True
        except ValueError:
            pass

    raise ValidationError(
        _("Overage must be an integer value or a percentage")
    )
