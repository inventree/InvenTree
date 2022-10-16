"""Plugin for hexadecimal serial numbers"""

from django.core.exceptions import ValidationError

from plugin import InvenTreePlugin
from plugin.mixins import ValidationMixin


class HexadecimalSerialPlugin(ValidationMixin, InvenTreePlugin):
    """Plugin for generating hexadecimal serial numbers:

    - Ensures that serial numbers are valid hexadecimal values
    - Provides incrementing function to generate the next value
    """

    NAME = "Hex Serials"
    SLUG = "hexserials"
    TITLE = "Hexadecimal Serial Numbers"
    DESCRIPTION = "Plugin for generating hexadecimal serial numbers"
    VERSION = "0.1"

    def validate_serial_number(self, serial: str):
        """Ensure that the provided serial number is a valid hex string"""

        try:
            # Attempt integer conversion
            int(serial, 16)
        except ValueError:
            raise ValidationError("Serial number must be a valid hex value")

    def convert_serial_to_int(self, serial: str):
        """Convert a hex serial number to an integer"""

        try:
            val = int(serial, 16)
        except ValueError:
            val = None

        return val

    def increment_serial_number(self, serial: str):
        """Return the next hexadecimal value"""

        if serial in ['', None]:
            return "1"

        try:
            val = int(serial, 16) + 1
            val = hex(val).upper()[2:]
        except ValueError:
            val = None

        return val
