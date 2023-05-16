"""Helper functions for converting between units."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import pint


def convert_physical_value(value: str, unit: str = None):
    """Validate that the provided value is a valid physical quantity.

    Arguments:
        value: Value to validate (str)
        unit: Optional unit to convert to, and validate against

    Raises:
        ValidationError: If the value is invalid

    Returns:
        The converted quantity, in the specified units
    """

    # Ensure that the value is a string
    value = str(value).strip()

    # Ignore blank values
    if not value:
        return

    ureg = pint.UnitRegistry()

    try:
        # Convert to a quantity
        val = ureg.Quantity(value)

        if unit:

            if val.units == ureg.dimensionless:
                # If the provided value is dimensionless, assume that the unit is correct
                val = ureg.Quantity(value, unit)
            else:
                # Convert to the provided unit (may raise an exception)
                val = val.to(unit)

    except pint.errors.UndefinedUnitError:
        raise ValidationError(_('Provided value has an invalid unit'))

    except pint.errors.DimensionalityError:
        msg = _('Provided value could not be converted to the specified unit')

        if unit:
            msg += f' ({unit})'

        raise ValidationError(msg)

    # Return the converted value
    return val
