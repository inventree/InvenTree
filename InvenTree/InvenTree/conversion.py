"""Helper functions for converting between units."""

import logging

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import pint

_unit_registry = None


logger = logging.getLogger('inventree')


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

    reg = pint.UnitRegistry()

    # Define some "standard" additional units
    reg.define('piece = 1')
    reg.define('each = 1 = ea')
    reg.define('dozen = 12 = dz')
    reg.define('hundred = 100')
    reg.define('thousand = 1000')

    # Temperature units
    reg.define('degreeC = °C = degC = celsius = Celsius')
    reg.define('degreeF = °F = degF = fahrenheit = Fahrenheit')
    reg.define('degreeK = °K = degK = kelvin = Kelvin')

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


def convert_physical_value(value: str, unit: str = None, strip_units=True):
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
    original = str(value).strip()

    # Ensure that the value is a string
    value = str(value).strip() if value else ''
    unit = str(unit).strip() if unit else ''

    # Error on blank values
    if not value:
        raise ValidationError(_('No value provided'))

    # Create a "backup" value which be tried if the first value fails
    # e.g. value = "10k" and unit = "ohm" -> "10kohm"
    # e.g. value = "10m" and unit = "F" -> "10mF"
    if unit:
        backup_value = value + unit
    else:
        backup_value = None

    ureg = get_unit_registry()

    try:
        value = ureg.Quantity(value)

        if unit:
            if is_dimensionless(value):
                magnitude = value.to_base_units().magnitude
                value = ureg.Quantity(magnitude, unit)
            else:
                value = value.to(unit)

    except Exception:
        if backup_value:
            try:
                value = ureg.Quantity(backup_value)
            except Exception:
                value = None
        else:
            value = None

    if value is None:
        if unit:
            raise ValidationError(_(f'Could not convert {original} to {unit}'))
        else:
            raise ValidationError(_('Invalid quantity supplied'))

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
        raise ValidationError(_(f'Invalid quantity supplied ({exc})'))

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

    if value.to_base_units().units == ureg.dimensionless:
        return True

    # At this point, the value is not dimensionless
    return False
