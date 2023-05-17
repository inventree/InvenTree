"""Helper functions for converting between units."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import pint

_unit_registry = None


def get_unit_registry():
    """Return a custom instance of the Pint UnitRegistry."""

    global _unit_registry

    # Cache the unit registry for speedier access
    if _unit_registry is None:
        _unit_registry = pint.UnitRegistry()

    # TODO: Allow for custom units to be defined in the database

    return _unit_registry


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

    # Error on blank values
    if not value:
        raise ValidationError(_('No value provided'))

    ureg = get_unit_registry()
    error = ''

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
        error = _('Provided value has an invalid unit')
    except pint.errors.DefinitionSyntaxError:
        error = _('Provided value has an invalid unit')
    except pint.errors.DimensionalityError:
        error = _('Provided value could not be converted to the specified unit')

    if error:
        if unit:
            error += f' ({unit})'

        raise ValidationError(error)

    # Return the converted value
    return val
