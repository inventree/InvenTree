"""Fallback barcode plugin which matches barcodes against manufacturer part numbers.

This plugin is intended to catch barcodes which are not handled by any
supplier-specific plugin (e.g. DigiKey / Mouser), but which still contain
a manufacturer part number (MPN).

The following barcode formats are supported:

- ISO/IEC 15434 / ECIA 2D barcodes (e.g. DataMatrix) with GS / RS field separators,
  containing a '1P' (manufacturer part number) or 'P' data identifier field.
- A single field with a '1P' or 'P' prefix, followed by the MPN (e.g. '1PLM358' or 'PLM358').
- The raw MPN string (e.g. 'LM358').

A match is only returned if exactly one ManufacturerPart matches the MPN exactly.

This plugin has a low barcode priority, so it is only used when no other
barcode plugin is able to match the scanned barcode.
"""

import re

from django.utils.translation import gettext_lazy as _

import structlog

from company.models import ManufacturerPart
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin
from users.permissions import check_user_permission

logger = structlog.get_logger('inventree')


# ISO/IEC 15434 control characters
GS = '\x1d'  # Group separator (field separator)
RS = '\x1e'  # Record separator
EOT = '\x04'  # End of transmission

# A data identifier (DI) is an optional numeric prefix, followed by a single uppercase letter
DATA_IDENTIFIER_REGEX = re.compile(r'^(\d{0,3}[A-Z])')

# Any ASCII control character (which should never appear in an MPN)
CONTROL_CHAR_REGEX = re.compile(r'[\x00-\x1f\x7f]')

# Data identifiers which may contain a manufacturer part number, in order of preference
MPN_IDENTIFIERS = ['1P', 'P']


class ManufacturerBarcodePlugin(BarcodeMixin, InvenTreePlugin):
    """Fallback barcode plugin for matching manufacturer part numbers."""

    NAME = 'ManufacturerBarcodePlugin'
    SLUG = 'manufacturerbarcode'
    TITLE = _('Manufacturer Part Barcodes')
    DESCRIPTION = _(
        'Fallback barcode support for matching manufacturer part numbers (MPN)'
    )
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    # Fallback plugin - query after all other barcode plugins
    BARCODE_PRIORITY = -100

    @staticmethod
    def max_mpn_length() -> int:
        """Return the maximum length of a ManufacturerPart MPN."""
        return ManufacturerPart._meta.get_field('MPN').max_length or 100

    @staticmethod
    def parse_data_identifier_fields(barcode_data: str) -> dict[str, str]:
        """Split a GS / RS delimited barcode into a dict of {identifier: value}.

        Header fields (e.g. '[)>' and the '06' format code) do not match the
        data identifier pattern, and are ignored.
        If an identifier appears multiple times, the first value is used.
        """
        fields = {}

        for field in re.split(f'[{GS}{RS}{EOT}]', barcode_data):
            if match := DATA_IDENTIFIER_REGEX.match(field):
                identifier = match.group(1)
                fields.setdefault(identifier, field[match.end() :])

        return fields

    @classmethod
    def extract_mpn_candidates(cls, barcode_data: str) -> list[str]:
        """Extract a list of candidate MPN values from the provided barcode data.

        Arguments:
            barcode_data: The raw barcode data

        Returns:
            A list of candidate MPN strings (may be empty)
        """
        if not isinstance(barcode_data, str) or not barcode_data:
            return []

        candidates = []

        if GS in barcode_data or RS in barcode_data:
            # Structured (e.g. DataMatrix) barcode
            # Only the MPN fields are considered - never the raw barcode data
            fields = cls.parse_data_identifier_fields(barcode_data)

            for identifier in MPN_IDENTIFIERS:
                if value := fields.get(identifier, '').strip():
                    # Prefer '1P' over 'P' - a 'P' field is typically a
                    # customer or supplier part number when '1P' is present
                    candidates.append(value)
                    break
        else:
            data = barcode_data.strip()

            # Reject any other (unstructured) data containing control characters
            if not data or CONTROL_CHAR_REGEX.search(data):
                return []

            # Single field with a '1P' or 'P' prefix
            for identifier in MPN_IDENTIFIERS:
                if data.startswith(identifier):
                    candidates.append(data[len(identifier) :].strip())
                    break

            # The raw data may itself be the MPN (e.g. 'PIC16F84A')
            candidates.append(data)

        max_length = cls.max_mpn_length()

        result = []

        for candidate in candidates:
            if (
                candidate
                and len(candidate) <= max_length
                and not CONTROL_CHAR_REGEX.search(candidate)
                and candidate not in result
            ):
                result.append(candidate)

        return result

    def scan(self, barcode_data: str, user, **kwargs) -> dict | None:
        """Attempt to match the barcode data against a single ManufacturerPart.

        Returns:
            A dict containing the matched ManufacturerPart, or None if there is not exactly one match
        """
        candidates = self.extract_mpn_candidates(barcode_data)

        if not candidates:
            return None

        # Do not query (or reveal) manufacturer part data for users who cannot view it
        if not check_user_permission(user, ManufacturerPart, 'view'):
            return None

        # Exact match only - fetch at most two results to detect ambiguity
        matches = list(
            ManufacturerPart.objects.filter(MPN__in=candidates).order_by('pk')[:2]
        )

        if len(matches) != 1:
            if len(matches) > 1:
                logger.debug(
                    'ManufacturerBarcodePlugin: multiple ManufacturerPart matches for barcode'
                )
            return None

        manufacturer_part = matches[0]

        return {
            ManufacturerPart.barcode_model_type(): manufacturer_part.format_matched_response(
                user=user
            ),
            'success': _('Found matching manufacturer part'),
        }
