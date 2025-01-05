"""Helper functions for converting between units."""

import re
from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import pint

_unit_registry = None

import structlog

logger = structlog.get_logger('inventree')


def get_unit_registry():
    """Return a custom instance of the Pint UnitRegistry."""
    global _unit_registry

    # Cache the unit registry for speedier access
    if _unit_registry is None:
        return reload_unit_registry()
    return _unit_registry


def reload_unit_registry():
    """Reload the unit registry from the database.

    This function is called at startup, and whenever the database is updated.
    """
    import time

    t_start = time.time()

    global _unit_registry

    _unit_registry = None

    reg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)

    # Aliases for temperature units
    reg.define('@alias degC = Celsius')
    reg.define('@alias degF = Fahrenheit')
    reg.define('@alias degK = Kelvin')

    # Define some "standard" additional units
    reg.define('piece = 1')
    reg.define('each = 1 = ea')
    reg.define('dozen = 12 = dz')
    reg.define('hundred = 100')
    reg.define('thousand = 1000')

    # Allow for custom units to be defined in the database
    try:
        from common.models import CustomUnit

        for cu in CustomUnit.objects.all():
            try:
                reg.define(cu.fmt_string())
            except Exception as e:
                logger.exception(
                    'Failed to load custom unit: %s - %s', cu.fmt_string(), e
                )

        # Once custom units are loaded, save registry
        _unit_registry = reg

    except Exception:
        # Database is not ready, or CustomUnit model is not available
        pass

    dt = time.time() - t_start
    logger.debug('Loaded unit registry in %.3f s', dt)

    return reg


def from_engineering_notation(value):
    """Convert a provided value to 'natural' representation from 'engineering' notation.

    Ref: https://en.wikipedia.org/wiki/Engineering_notation

    In "engineering notation", the unit (or SI prefix) is often combined with the value,
    and replaces the decimal point.

    Examples:
    - 1K2 -> 1.2K
    - 3n05 -> 3.05n
    - 8R6 -> 8.6R

    And, we should also take into account any provided trailing strings:

    - 1K2 ohm -> 1.2K ohm
    - 10n005F -> 10.005nF
    """
    value = str(value).strip()

    pattern = r'(\d+)([a-zA-Z]+)(\d+)(.*)'

    if match := re.match(pattern, value):
        left, prefix, right, suffix = match.groups()
        return f'{left}.{right}{prefix}{suffix}'

    return value


def convert_value(value, unit):
    """Attempt to convert a value to a specified unit.

    Arguments:
        value: The value to convert
        unit: The target unit to convert to

    Returns:
        The converted value (ideally a pint.Quantity value)

    Raises:
        Exception if the value cannot be converted to the specified unit
    """
    ureg = get_unit_registry()

    # Convert the provided value to a pint.Quantity object
    value = ureg.Quantity(value)

    # Convert to the specified unit
    if unit:
        if is_dimensionless(value):
            magnitude = value.to_base_units().magnitude
            value = ureg.Quantity(magnitude, unit)
        else:
            value = value.to(unit)

    return value


def convert_physical_value(value: str, unit: Optional[str] = None, strip_units=True):
    """Validate that the provided value is a valid physical quantity.

    Arguments:
        value: Value to validate (str)
        unit: Optional unit to convert to, and validate against
        strip_units: If True, strip units from the returned value, and return only the dimension

    Raises:
        ValidationError: If the value is invalid or cannot be converted to the specified unit

    Returns:
        The converted quantity, in the specified units
    """
    ureg = get_unit_registry()

    # Check that the provided unit is available in the unit registry
    if unit:
        try:
            valid = unit in ureg
        except Exception:
            valid = False

        if not valid:
            raise ValidationError(_(f'Invalid unit provided ({unit})'))

    original = str(value).strip()

    # Ensure that the value is a string
    value = str(value).strip() if value else ''
    unit = str(unit).strip() if unit else ''

    # Handle imperial length measurements
    if value.count("'") == 1 and value.endswith("'"):
        value = value.replace("'", ' feet')

    if value.count('"') == 1 and value.endswith('"'):
        value = value.replace('"', ' inches')

    # Error on blank values
    if not value:
        raise ValidationError(_('No value provided'))

    # Construct a list of values to "attempt" to convert
    attempts = [value]

    # Attempt to convert from engineering notation
    eng = from_engineering_notation(value)
    attempts.append(eng)

    # Append the unit, if provided
    # These are the "final" attempts to convert the value, and *must* appear after previous attempts
    if unit:
        attempts.append(f'{value}{unit}')
        attempts.append(f'{eng}{unit}')

    value = None

    # Run through the available "attempts", take the first successful result
    for attempt in attempts:
        try:
            value = convert_value(attempt, unit)
            break
        except Exception:
            value = None

    if value is None:
        if unit:
            raise ValidationError(_(f'Could not convert {original} to {unit}'))
        else:
            raise ValidationError(_('Invalid quantity provided'))

    # Calculate the "magnitude" of the value, as a float
    # If the value is specified strangely (e.g. as a fraction or a dozen), this can cause issues
    # So, we ensure that it is converted to a floating point value
    # If we wish to return a "raw" value, some trickery is required
    try:
        if unit:
            magnitude = ureg.Quantity(value.to(ureg.Unit(unit))).magnitude
        else:
            magnitude = ureg.Quantity(value.to_base_units()).magnitude

        magnitude = float(ureg.Quantity(magnitude).to_base_units().magnitude)
    except Exception as exc:
        raise ValidationError(_('Invalid quantity provided') + f': ({exc})')

    if strip_units:
        return magnitude
    elif unit or value.units:
        return ureg.Quantity(magnitude, unit or value.units)
    return ureg.Quantity(magnitude)


def is_dimensionless(value):
    """Determine if the provided value is 'dimensionless'.

    A dimensionless value might look like:

    0.1
    1/2 dozen
    three thousand
    1.2 dozen
    (etc)
    """
    ureg = get_unit_registry()

    # Ensure the provided value is in the right format
    value = ureg.Quantity(value)

    if value.units == ureg.dimensionless:
        return True

    return value.to_base_units().units == ureg.dimensionless
