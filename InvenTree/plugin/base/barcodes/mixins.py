"""Plugin mixin classes for barcode plugin."""

import logging

from company.models import Company, ManufacturerPart, SupplierPart

logger = logging.getLogger('inventree')


class BarcodeMixin:
    """Mixin that enables barcode handling.

    Custom barcode plugins should use and extend this mixin as necessary.
    """

    ACTION_NAME = ""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Barcode'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('barcode', 'has_barcode', __class__)

    @property
    def has_barcode(self):
        """Does this plugin have everything needed to process a barcode."""
        return True

    def scan(self, barcode_data):
        """Scan a barcode against this plugin.

        This method is explicitly called from the /scan/ API endpoint,
        and thus it is expected that any barcode which matches this barcode will return a result.

        If this plugin finds a match against the provided barcode, it should return a dict object
        with the intended result.

        Default return value is None
        """

        return None

    def scan_receive_item(self, barcode_data, user, purchase_order=None, location=None):
        """Scan a barcode to receive a purchase order item.

        Default return value is None
        """

        return None

    @staticmethod
    def get_supplier_part(sku: str, supplier: Company = None, mpn: str = None):
        """Get a supplier part from SKU or by supplier and MPN."""
        if sku:
            supplier_parts = SupplierPart.objects.filter(SKU__iexact=sku)
            if not supplier_parts or len(supplier_parts) > 1:
                logger.warning(
                    f"Found {len(supplier_parts)} supplier parts for SKU {sku}"
                )
                return None
            return supplier_parts[0]

        if not supplier or not mpn:
            return None

        manufacturer_parts = ManufacturerPart.objects.filter(MPN__iexact=mpn)
        if not manufacturer_parts or len(manufacturer_parts) > 1:
            logger.warning(
                f"Found {len(manufacturer_parts)} manufacturer parts for MPN {mpn}"
            )
            return None
        manufacturer_part = manufacturer_parts[0]

        supplier_parts = SupplierPart.objects.filter(
            manufacturer_part=manufacturer_part.pk, supplier=supplier.pk)
        if not supplier_parts or len(supplier_parts) > 1:
            logger.warning(
                f"Found {len(supplier_parts)} supplier parts for MPN {mpn} and "
                f"supplier '{supplier.name}'"
            )
            return None
        return supplier_parts[0]

    @staticmethod
    def parse_ecia_barcode2d(barcode_data: str) -> dict[str, str]:
        """Parse a standard ECIA 2D barcode, according to https://www.ecianow.org/assets/docs/ECIA_Specifications.pdf"""

        if not (data_split := BarcodeMixin.parse_isoiec_15434_barcode2d(barcode_data)):
            return None

        barcode_fields = {}
        for entry in data_split:
            for identifier, field_name in ECIA_DATA_IDENTIFIER_MAP.items():
                if entry.startswith(identifier):
                    barcode_fields[field_name] = entry[len(identifier):]
                    break

        return barcode_fields

    @staticmethod
    def parse_isoiec_15434_barcode2d(barcode_data: str) -> list[str]:
        """Parse a ISO/IEC 15434 bardode, returning the split data section."""
        HEADER = "[)>\x1E06\x1D"
        TRAILER = "\x1E\x04"

        # some old mouser barcodes start with this messed up header
        OLD_MOUSER_HEADER = ">[)>06\x1D"
        if barcode_data.startswith(OLD_MOUSER_HEADER):
            barcode_data = barcode_data.replace(OLD_MOUSER_HEADER, HEADER, 1)

        # most barcodes don't include the trailer, because "why would you stick to
        # the standard, right?" so we only check for the header here
        if not barcode_data.startswith(HEADER):
            return

        actual_data = barcode_data.split(HEADER, 1)[1].rsplit(TRAILER, 1)[0]

        return actual_data.split("\x1D")


# Map ECIA Data Identifier to human readable identifier
# The following identifiers haven't been implemented: 3S, 4S, 5S, S
ECIA_DATA_IDENTIFIER_MAP = {
    "K":   "purchase_order_number",     # noqa: E241
    "1K":  "purchase_order_number",     # noqa: E241  DigiKey uses 1K instead of K
    "11K": "packing_list_number",       # noqa: E241
    "6D":  "ship_date",                 # noqa: E241
    "P":   "supplier_part_number",      # noqa: E241  "Customer Part Number"
    "1P":  "manufacturer_part_number",  # noqa: E241  "Supplier Part Number"
    "4K":  "purchase_order_line",       # noqa: E241
    "14K": "purchase_order_line",       # noqa: E241  Mouser uses 14K instead of 4K
    "Q":   "quantity",                  # noqa: E241
    "9D":  "date_yyww",                 # noqa: E241
    "10D": "date_yyww",                 # noqa: E241
    "1T":  "lot_code",                  # noqa: E241
    "4L":  "country_of_origin",         # noqa: E241
    "1V":  "manufacturer"               # noqa: E241
}
