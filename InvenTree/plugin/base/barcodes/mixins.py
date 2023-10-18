"""Plugin mixin classes for barcode plugin."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from company.models import Company, SupplierPart
from order.models import PurchaseOrder, PurchaseOrderStatus
from plugin.base.integration.SettingsMixin import SettingsMixin
from stock.models import StockLocation

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

        It's recommended to use the receive_purchase_order_item method to return from this function.

        Returns:
            None if the barcode_data could not be parsed.

            A dict object containing:
                - on success:
                    a "success" message and the received "lineitem"
                - on partial success (if there's missing information):
                    an "action_required" message and the matched, but not yet received "lineitem"
                - on failure:
                    an "error" message
        """

        return None

    @staticmethod
    def parse_ecia_barcode2d(barcode_data: str | list[str]) -> dict[str, str]:
        """Parse a standard ECIA 2D barcode, according to https://www.ecianow.org/assets/docs/ECIA_Specifications.pdf"""

        if not isinstance(barcode_data, str):
            data_split = barcode_data
        elif not (data_split := BarcodeMixin.parse_isoiec_15434_barcode2d(barcode_data)):
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

    @staticmethod
    def get_supplier_parts(sku: str, supplier: Company = None, mpn: str = None):
        """Get a supplier part from SKU or by supplier and MPN."""
        if not (sku or supplier or mpn):
            return SupplierPart.objects.none()

        supplier_parts = SupplierPart.objects.all()

        if sku:
            supplier_parts = supplier_parts.filter(SKU__iexact=sku)
            if len(supplier_parts) == 1:
                return supplier_parts

        if supplier:
            supplier_parts = supplier_parts.filter(supplier=supplier.pk)
            if len(supplier_parts) == 1:
                return supplier_parts

        if mpn:
            supplier_parts = SupplierPart.objects.filter(manufacturer_part__MPN__iexact=mpn)
            if len(supplier_parts) == 1:
                return supplier_parts

        logger.warning(
            "Found %d supplier parts for SKU '%s', supplier '%s', MPN '%s'",
            supplier_parts.count(),
            sku,
            supplier.name if supplier else None,
            mpn,
        )

        return supplier_parts

    @staticmethod
    def receive_purchase_order_item(
            supplier_part: SupplierPart,
            user: User,
            quantity: Decimal | str = None,
            order_number: str = None,
            purchase_order: PurchaseOrder = None,
            location: StockLocation = None,
            barcode: str = None,
    ) -> dict:
        """Try to receive a purchase order item.

        Returns:
            A dict object containing:
                - on success: a "success" message
                - on partial success: the "lineitem" with quantity and location (both can be None)
                - on failure: an "error" message
        """

        if not purchase_order:
            # try to find a purchase order with either reference or name matching
            # the provided order_number
            if not order_number:
                return {"error": _("Supplier barcode doesn't contain order number")}

            purchase_orders = (
                PurchaseOrder.objects.filter(
                    supplier_reference__iexact=order_number,
                    status=PurchaseOrderStatus.PLACED.value,
                ) | PurchaseOrder.objects.filter(
                    reference__iexact=order_number,
                    status=PurchaseOrderStatus.PLACED.value,
                )
            )

            if len(purchase_orders) > 1:
                return {"error": _(f"Found multiple placed purchase orders for '{order_number}'")}
            elif not (purchase_order := purchase_orders.first()):
                return {"error": _(f"Failed to find placed purchase order for '{order_number}'")}

        if quantity:
            try:
                quantity = Decimal(quantity)
            except InvalidOperation:
                logger.warning("Failed to parse quantity '%s'", quantity)
                quantity = None

        #  find incomplete line_items that match the supplier_part
        line_items = purchase_order.lines.filter(
            part=supplier_part.pk, quantity__gt=F("received"))
        if len(line_items) == 1 or not quantity:
            line_item = line_items[0]
        else:
            # if there are multiple line items and the barcode contains a quantity:
            # 1. return the first line_item where line_item.quantity == quantity
            # 2. return the first line_item where line_item.quantity > quantity
            # 3. return the first line_item
            for line_item in line_items:
                if line_item.quantity == quantity:
                    break
            else:
                for line_item in line_items:
                    if line_item.quantity > quantity:
                        break
                else:
                    line_item = line_items.first()

        if not line_item:
            return {"error": _("Failed to find pending line item for supplier part")}

        no_stock_locations = False
        if not location:
            # try to guess the destination were the stock_part should go
            # 1. check if it's defined on the line_item
            # 2. check if it's defined on the part
            # 3. check if there's 1 or 0 stock locations defined in InvenTree
            #    -> assume all stock is going into that location (or no location)
            if location := line_item.destination:
                pass
            elif location := supplier_part.part.get_default_location():
                pass
            elif StockLocation.objects.count() <= 1:
                if not (location := StockLocation.objects.first()):
                    no_stock_locations = True

        response = {
            "lineitem": {
                "pk": line_item.pk,
                "purchase_order": purchase_order.pk,
            }
        }

        if quantity:
            response["lineitem"]["quantity"] = quantity
        if location:
            response["lineitem"]["location"] = location.pk

        # if either the quantity is missing or no location is defined/found
        # -> return the line_item found, so the client can gather the missing
        #    information and complete the action with an 'api-po-receive' call
        if not quantity or (not location and not no_stock_locations):
            response["action_required"] = _("Further information required to receive line item")
            return response

        purchase_order.receive_line_item(
            line_item,
            location,
            quantity,
            user,
            barcode=barcode,
        )

        response["success"] = _("Received purchase order line item")
        return response


@dataclass
class SupplierBarcodeData:
    """Data parsed from a supplier barcode."""
    SKU: str = None
    MPN: str = None
    quantity: Decimal | str = None
    order_number: str = None


class SupplierBarcodeMixin(BarcodeMixin):
    """Mixin that provides default implementations for scan functions for supplier barcodes.

    Custom supplier barcode plugins should use this mixin and implement the
    parse_supplier_barcode_data function.
    """

    def parse_supplier_barcode_data(self, barcode_data) -> SupplierBarcodeData | None:
        """Get supplier_part and other barcode_fields from barcode data.

        Returns:
            None if the barcode_data is not from a valid barcode of the supplier.

            A SupplierBarcodeData object containing the SKU, MPN, quantity and order number
            if available.
        """

        return None

    def scan(self, barcode_data):
        """Try to match a supplier barcode to a supplier part."""

        if not (parsed := self.parse_supplier_barcode_data(barcode_data)):
            return None
        if parsed.SKU is None and parsed.MPN is None:
            return None

        supplier_parts = self.get_supplier_parts(parsed.SKU, self.get_supplier(), parsed.MPN)
        if len(supplier_parts) > 1:
            return {"error": _("Found multiple matching supplier parts for barcode")}
        elif not supplier_parts:
            return None
        supplier_part = supplier_parts[0]

        data = {
            "pk": supplier_part.pk,
            "api_url": f"{SupplierPart.get_api_url()}{supplier_part.pk}/",
            "web_url": supplier_part.get_absolute_url(),
        }

        return {SupplierPart.barcode_model_type(): data}

    def scan_receive_item(self, barcode_data, user, purchase_order=None, location=None):
        """Try to scan a supplier barcode to receive a purchase order item."""

        if not (parsed := self.parse_supplier_barcode_data(barcode_data)):
            return None
        if parsed.SKU is None and parsed.MPN is None:
            return None

        supplier_parts = self.get_supplier_parts(parsed.SKU, self.get_supplier(), parsed.MPN)
        if len(supplier_parts) > 1:
            return {"error": _("Found multiple matching supplier parts for barcode")}
        elif not supplier_parts:
            return None
        supplier_part = supplier_parts[0]

        return self.receive_purchase_order_item(
            supplier_part,
            user,
            quantity=parsed.quantity,
            order_number=parsed.order_number,
            purchase_order=purchase_order,
            location=location,
            barcode=barcode_data,
        )

    def get_supplier(self) -> Company | None:
        """Get the supplier for the SUPPLIER_ID set in the plugin settings.

        If it's not defined, try to guess it and set it if possible.
        """

        if not isinstance(self, SettingsMixin):
            return None

        if supplier_pk := self.get_setting("SUPPLIER_ID"):
            if (supplier := Company.objects.get(pk=supplier_pk)):
                return supplier
            else:
                logger.error(
                    "No company with pk %d (set \"SUPPLIER_ID\" setting to a valid value)",
                    supplier_pk
                )
                return None

        if not (supplier_name := getattr(self, "DEFAULT_SUPPLIER_NAME", None)):
            return None

        suppliers = Company.objects.filter(name__icontains=supplier_name, is_supplier=True)
        if len(suppliers) != 1:
            return None
        self.set_setting("SUPPLIER_ID", suppliers.first().pk)

        return suppliers.first()


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
