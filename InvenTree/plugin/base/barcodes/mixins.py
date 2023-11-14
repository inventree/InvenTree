"""Plugin mixin classes for barcode plugin."""

from __future__ import annotations

import logging
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


class SupplierBarcodeMixin(BarcodeMixin):
    """Mixin that provides default implementations for scan functions for supplier barcodes.

    Custom supplier barcode plugins should use this mixin and implement the
    parse_supplier_barcode_data function.
    """

    # Following are the "standard" field names for supplier barcodes
    # Note that some manufacturers use different codes,
    # and there are other fields which can be included in the barcode
    CUSTOMER_ORDER_NUMBER = "K"
    SUPPLIER_ORDER_NUMBER = "1K"
    QUANTITY = "Q"
    SUPPLIER_PART_NUMBER = "P"
    MANUFACTURER_PART_NUMBER = "1P"

    def __init__(self):
        """Register this mixin"""
        super().__init__()
        self.add_mixin('supplier_barcode', True, __class__)

    def parse_supplier_barcode_data(self, barcode_data) -> None:
        """Parse the supplied barcode data.

        It is expected that the resulting fields are extracted,
        and stored (as a list of strings) in the 'barcode_fields' attribute.
        """

        if not isinstance(barcode_data, str):
            return

        return self.parse_isoiec_15434_barcode2d(barcode_data)

    def scan(self, barcode_data):
        """Try to match a supplier barcode to a supplier part."""

        self.barcode_fields = self.parse_supplier_barcode_data(barcode_data)

        if self.SKU is None and self.MPN is None:
            return None

        supplier_parts = self.get_supplier_parts(self.SKU, self.get_supplier(), self.MPN)

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

        return {
            SupplierPart.barcode_model_type(): data
        }

    def scan_receive_item(self, barcode_data, user, purchase_order=None, location=None):
        """Try to scan a supplier barcode to receive a purchase order item.

        - Decode the barcode data into "native" format
        - Map the decoded data to a "standard" format
        """
        self.barcode_fields = self.parse_supplier_barcode_data(barcode_data)

        if self.SKU is None and self.MPN is None:
            return None

        # Find matching supplier part(s)
        supplier_parts = self.get_supplier_parts(self.SKU, self.get_supplier(), self.MPN)

        if len(supplier_parts) > 1:
            return {
                "error": _("Found multiple matching supplier parts for barcode")
            }

        if len(supplier_parts) == 0:
            return None

        # Extract the first supplier part
        supplier_part = supplier_parts[0]

        if self.quantity is not None and self.quantity <= 0:
            return {
                "error": _("Quantity must be greater than zero")
            }

        # Find matching purchase order (if not supplied)
        if not purchase_order:
            matching_orders = self.get_purchase_orders(
                purchase_order=purchase_order,
                customer_order_number=self.customer_order_number,
                supplier_order_number=self.supplier_order_number,
                supplier=self.get_supplier(),
            )

            if len(matching_orders) == 1:
                purchase_order = matching_orders[0]

            elif len(matching_orders) > 1:
                return {
                    "error": _("Found multiple matching purchase orders for barcode")
                }

            elif len(matching_orders) == 0:
                return {
                    "error": _("No matching purchase orders found for barcode")
                }

        return self.receive_purchase_order_item(
            supplier_part,
            purchase_order,
            user,
            quantity=self.quantity,
            location=location,
            barcode=barcode_data,
        )

    @property
    def SKU(self):
        """Return the SKU field data."""
        return self.get_field_data(self.SUPPLIER_PART_NUMBER)

    @property
    def MPN(self):
        """Return the MPN field data"""
        return self.get_field_data(self.MANUFACTURER_PART_NUMBER)

    @property
    def quantity(self):
        """Return the quantity field data."""
        q = self.get_field_data(self.QUANTITY)

        if q is not None:
            try:
                return Decimal(q)
            except InvalidOperation:
                pass

    @property
    def customer_order_number(self):
        """Return the customer (internal) order number"""
        return self.get_field_data(self.CUSTOMER_ORDER_NUMBER)

    @property
    def supplier_order_number(self):
        """Return the supplier's order number"""
        return self.get_field_data(self.SUPPLIER_ORDER_NUMBER)

    def get_field_data(self, code):
        """Return the field data for a given field code."""

        fields = getattr(self, 'barcode_fields') or []

        # Return the first "match" for the given code
        for field in fields:
            if field.startswith(code):
                return field[len(code):]

        return None

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

    @staticmethod
    def parse_isoiec_15434_barcode2d(barcode_data: str) -> list[str]:
        """Parse a ISO/IEC 15434 bardode, returning the split data section."""
        HEADER = "[)>\x1E06\x1D"
        TRAILER = "\x1E\x04"

        barcode = str(barcode_data).strip()

        # some old mouser barcodes start with this messed up header
        OLD_MOUSER_HEADER = ">[)>06\x1D"
        if barcode_data.startswith(OLD_MOUSER_HEADER):
            barcode = barcode.replace(OLD_MOUSER_HEADER, HEADER, 1)

        # most barcodes don't include the trailer, because "why would you stick to
        # the standard, right?" so we only check for the header here
        if not barcode.startswith(HEADER):
            return

        actual_data = barcode.split(HEADER, 1)[1].rsplit(TRAILER, 1)[0]

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
    def get_purchase_orders(
        purchase_order: PurchaseOrder = None,
        customer_order_number: str = None,
        supplier_order_number: str = None,
        supplier: Company = None,
    ):
        """Determine the associated purchase order.

        Arguments:
            purchase_order: A purchase order object (supplied by the client)
            customer_order_number: A customer order number (extracted from the barcode)
            supplier_order_number: A supplier order number (extracted from the barcode)
            supplier: A supplier object (supplied by the plugin)
        """

        # If a purchase order is supplied, use that
        if purchase_order is not None:
            return purchase_order

        orders = PurchaseOrder.objects.filter(
            status=PurchaseOrderStatus.PLACED.value,
        )

        if supplier:
            orders = orders.filter(supplier=supplier)

        if customer_order_number:
            orders = orders.filter(reference__iexact=customer_order_number)
        elif supplier_order_number:
            orders = orders.filter(supplier_reference__iexact=supplier_order_number)

        # Return the queryset of orders
        return orders

    @staticmethod
    def receive_purchase_order_item(
            supplier_part: SupplierPart,
            purchase_order: PurchaseOrder,
            user: User,
            quantity: Decimal | str = None,
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
