"""
Custom field validators for InvenTree
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_part_name(value):
    """ Prevent some illegal characters in part names.
    """

    for c in ['|', '#', '$', '{', '}']:
        if c in str(value):
            raise ValidationError(
                _('Invalid character in part name')
            )


def validate_tree_name(value):
    """ Prevent illegal characters in tree item names """

    for c in "!@#$%^&*'\"\\/[]{}<>,|+=~`\"":
        if c in str(value):
            raise ValidationError({'name': _('Illegal character in name')})


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
