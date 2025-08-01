"""Custom field validators for InvenTree."""

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import pint
from moneyed import CURRENCIES

import InvenTree.conversion
from common.settings import get_global_setting


def validate_physical_units(unit):
    """Ensure that a given unit is a valid physical unit."""
    unit = unit.strip()

    # Ignore blank units
    if not unit:
        return

    ureg = InvenTree.conversion.get_unit_registry()

    try:
        ureg(unit)
    except (AssertionError, AttributeError, pint.errors.UndefinedUnitError):
        raise ValidationError(_('Invalid physical unit'))


def validate_currency_code(code):
    """Check that a given code is a valid currency code."""
    if code not in CURRENCIES:
        raise ValidationError(_('Not a valid currency code'))


def allowable_url_schemes():
    """Return the list of allowable URL schemes.

    In addition to the default schemes allowed by Django,
    the install configuration file (config.yaml) can specify
    extra schemas
    """
    # Default schemes
    schemes = ['http', 'https', 'ftp', 'ftps']

    extra = settings.EXTRA_URL_SCHEMES

    for e in extra:
        if e.lower() not in schemes:
            schemes.append(e.lower())

    return schemes


class AllowedURLValidator(validators.URLValidator):
    """Custom URL validator to allow for custom schemes."""

    def __call__(self, value):
        """Validate the URL."""
        self.schemes = allowable_url_schemes()

        # Determine if 'strict' URL validation is required (i.e. if the URL must have a schema prefix)
        strict_urls = get_global_setting('INVENTREE_STRICT_URLS', cache=False)

        if value is not None:
            value = str(value).strip()

        if value and not strict_urls:
            # Allow URLs which do not have a provided schema
            if '://' not in value:
                # Validate as if it were http
                value = 'http://' + value

        super().__call__(value)


def validate_purchase_order_reference(value):
    """Validate the 'reference' field of a PurchaseOrder."""
    from order.models import PurchaseOrder

    # If we get to here, run the "default" validation routine
    PurchaseOrder.validate_reference_field(value)


def validate_sales_order_reference(value):
    """Validate the 'reference' field of a SalesOrder."""
    from order.models import SalesOrder

    # If we get to here, run the "default" validation routine
    SalesOrder.validate_reference_field(value)


def validate_tree_name(value):
    """Placeholder for legacy function used in migrations."""
