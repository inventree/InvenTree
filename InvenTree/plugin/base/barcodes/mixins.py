"""Plugin mixin classes for barcode plugin."""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from company.models import Company, SupplierPart
from order.models import PurchaseOrder, PurchaseOrderStatus
from stock.models import StockLocation

from plugin.base.integration.SettingsMixin import SettingsMixin

logger = logging.getLogger('inventree')


class BarcodeMixin:
    """Mixin that enables barcode handling.

    Custom barcode plugins should use and extend this mixin as necessary.
    """

    ACTION_NAME = ''

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
    extract_barcode_fields function.
    """

    # Set of standard field names which can be extracted from the barcode
    CUSTOMER_ORDER_NUMBER = 'customer_order_number'
    SUPPLIER_ORDER_NUMBER = 'supplier_order_number'
    PACKING_LIST_NUMBER = 'packing_list_number'
    SHIP_DATE = 'ship_date'
    CUSTOMER_PART_NUMBER = 'customer_part_number'
    SUPPLIER_PART_NUMBER = 'supplier_part_number'
    PURCHASE_ORDER_LINE = 'purchase_order_line'
    QUANTITY = 'quantity'
    DATE_CODE = 'date_code'
    LOT_CODE = 'lot_code'
    COUNTRY_OF_ORIGIN = 'country_of_origin'
    MANUFACTURER = 'manufacturer'
    MANUFACTURER_PART_NUMBER = 'manufacturer_part_number'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('supplier-barcode', True, __class__)

    def get_field_value(self, key, backup_value=None):
        """Return the value of a barcode field."""
        fields = getattr(self, 'barcode_fields', None) or {}

        return fields.get(key, backup_value)

    @property
    def quantity(self):
        """Return the quantity from the barcode fields."""
        return self.get_field_value(self.QUANTITY)

    @property
    def supplier_part_number(self):
        """Return the supplier part number from the barcode fields."""
        return self.get_field_value(self.SUPPLIER_PART_NUMBER)

    @property
    def manufacturer_part_number(self):
        """Return the manufacturer part number from the barcode fields."""
        return self.get_field_value(self.MANUFACTURER_PART_NUMBER)

    @property
    def customer_order_number(self):
        """Return the customer order number from the barcode fields."""
        return self.get_field_value(self.CUSTOMER_ORDER_NUMBER)

    @property
    def supplier_order_number(self):
        """Return the supplier order number from the barcode fields."""
        return self.get_field_value(self.SUPPLIER_ORDER_NUMBER)

    def extract_barcode_fields(self, barcode_data) -> dict[str, str]:
        """Method to extract barcode fields from barcode data.

        This method should return a dict object where the keys are the field names,
        as per the "standard field names" (defined in the SuppliedBarcodeMixin class).

        This method *must* be implemented by each plugin

        Returns:
            A dict object containing the barcode fields.

        """
        raise NotImplementedError(
            'extract_barcode_fields must be implemented by each plugin'
        )

    def scan(self, barcode_data):
        """Try to match a supplier barcode to a supplier part."""
        barcode_data = str(barcode_data).strip()

        self.barcode_fields = self.extract_barcode_fields(barcode_data)

        if self.supplier_part_number is None and self.manufacturer_part_number is None:
            return None

        supplier_parts = self.get_supplier_parts(
            sku=self.supplier_part_number,
            mpn=self.manufacturer_part_number,
            supplier=self.get_supplier(),
        )

        if len(supplier_parts) > 1:
            return {'error': _('Found multiple matching supplier parts for barcode')}
        elif not supplier_parts:
            return None

        supplier_part = supplier_parts[0]

        data = {
            'pk': supplier_part.pk,
            'api_url': f'{SupplierPart.get_api_url()}{supplier_part.pk}/',
            'web_url': supplier_part.get_absolute_url(),
        }

        return {SupplierPart.barcode_model_type(): data}

    def scan_receive_item(self, barcode_data, user, purchase_order=None, location=None):
        """Try to scan a supplier barcode to receive a purchase order item."""
        barcode_data = str(barcode_data).strip()

        self.barcode_fields = self.extract_barcode_fields(barcode_data)

        if self.supplier_part_number is None and self.manufacturer_part_number is None:
            return None

        supplier = self.get_supplier()

        supplier_parts = self.get_supplier_parts(
            sku=self.supplier_part_number,
            mpn=self.manufacturer_part_number,
            supplier=supplier,
        )

        if len(supplier_parts) > 1:
            return {'error': _('Found multiple matching supplier parts for barcode')}
        elif not supplier_parts:
            return None

        supplier_part = supplier_parts[0]

        # If a purchase order is not provided, extract it from the provided data
        if not purchase_order:
            matching_orders = self.get_purchase_orders(
                self.customer_order_number,
                self.supplier_order_number,
                supplier=supplier,
            )

            order = self.customer_order_number or self.supplier_order_number

            if len(matching_orders) > 1:
                return {
                    'error': _(f"Found multiple purchase orders matching '{order}'")
                }

            if len(matching_orders) == 0:
                return {'error': _(f"No matching purchase order for '{order}'")}

            purchase_order = matching_orders.first()

        if supplier and purchase_order:
            if purchase_order.supplier != supplier:
                return {'error': _('Purchase order does not match supplier')}

        return self.receive_purchase_order_item(
            supplier_part,
            user,
            quantity=self.quantity,
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

        if supplier_pk := self.get_setting('SUPPLIER_ID'):
            if supplier := Company.objects.get(pk=supplier_pk):
                return supplier
            else:
                logger.error(
                    'No company with pk %d (set "SUPPLIER_ID" setting to a valid value)',
                    supplier_pk,
                )
                return None

        if not (supplier_name := getattr(self, 'DEFAULT_SUPPLIER_NAME', None)):
            return None

        suppliers = Company.objects.filter(
            name__icontains=supplier_name, is_supplier=True
        )

        if len(suppliers) != 1:
            return None

        self.set_setting('SUPPLIER_ID', suppliers.first().pk)

        return suppliers.first()

    @classmethod
    def ecia_field_map(cls):
        """Return a dict mapping ECIA field names to internal field names.

        Ref: https://www.ecianow.org/assets/docs/ECIA_Specifications.pdf

        Note that a particular plugin may need to reimplement this method,
        if it does not use the standard field names.
        """
        return {
            'K': cls.CUSTOMER_ORDER_NUMBER,
            '1K': cls.SUPPLIER_ORDER_NUMBER,
            '11K': cls.PACKING_LIST_NUMBER,
            '6D': cls.SHIP_DATE,
            '9D': cls.DATE_CODE,
            '10D': cls.DATE_CODE,
            '4K': cls.PURCHASE_ORDER_LINE,
            '14K': cls.PURCHASE_ORDER_LINE,
            'P': cls.SUPPLIER_PART_NUMBER,
            '1P': cls.MANUFACTURER_PART_NUMBER,
            '30P': cls.SUPPLIER_PART_NUMBER,
            '1T': cls.LOT_CODE,
            '4L': cls.COUNTRY_OF_ORIGIN,
            '1V': cls.MANUFACTURER,
            'Q': cls.QUANTITY,
        }

    @classmethod
    def parse_ecia_barcode2d(cls, barcode_data: str) -> dict[str, str]:
        """Parse a standard ECIA 2D barcode.

        Ref: https://www.ecianow.org/assets/docs/ECIA_Specifications.pdf

        Arguments:
            barcode_data: The raw barcode data

        Returns:
            A dict containing the parsed barcode fields
        """
        # Split data into separate fields
        fields = cls.parse_isoiec_15434_barcode2d(barcode_data)

        barcode_fields = {}

        if not fields:
            return barcode_fields

        for field in fields:
            for identifier, field_name in cls.ecia_field_map().items():
                if field.startswith(identifier):
                    barcode_fields[field_name] = field[len(identifier) :]
                    break

        return barcode_fields

    @staticmethod
    def split_fields(
        barcode_data: str, delimiter: str = ',', header: str = '', trailer: str = ''
    ) -> list[str]:
        """Generic method for splitting barcode data into separate fields."""
        if header and barcode_data.startswith(header):
            barcode_data = barcode_data[len(header) :]

        if trailer and barcode_data.endswith(trailer):
            barcode_data = barcode_data[: -len(trailer)]

        return barcode_data.split(delimiter)

    @staticmethod
    def parse_isoiec_15434_barcode2d(barcode_data: str) -> list[str]:
        """Parse a ISO/IEC 15434 barcode, returning the split data section."""
        OLD_MOUSER_HEADER = '>[)>06\x1d'
        HEADER = '[)>\x1e06\x1d'
        TRAILER = '\x1e\x04'
        DELIMITER = '\x1d'

        # Some old mouser barcodes start with this messed up header
        if barcode_data.startswith(OLD_MOUSER_HEADER):
            barcode_data = barcode_data.replace(OLD_MOUSER_HEADER, HEADER, 1)

        # Check that the barcode starts with the necessary header
        if not barcode_data.startswith(HEADER):
            return

        return SupplierBarcodeMixin.split_fields(
            barcode_data, delimiter=DELIMITER, header=HEADER, trailer=TRAILER
        )

    @staticmethod
    def get_purchase_orders(
        customer_order_number, supplier_order_number, supplier: Company = None
    ):
        """Attempt to find a purchase order from the extracted customer and supplier order numbers."""
        orders = PurchaseOrder.objects.filter(status=PurchaseOrderStatus.PLACED.value)

        if supplier:
            orders = orders.filter(supplier=supplier)

        # this works because reference and supplier_reference are not nullable, so if
        # customer_order_number or supplier_order_number is None, the query won't return anything
        reference_filter = Q(reference__iexact=customer_order_number)
        supplier_reference_filter = Q(supplier_reference__iexact=supplier_order_number)

        orders_union = orders.filter(reference_filter | supplier_reference_filter)
        if orders_union.count() == 1:
            return orders_union
        else:
            orders_intersection = orders.filter(
                reference_filter & supplier_reference_filter
            )
            return orders_intersection if orders_intersection else orders_union

    @staticmethod
    def get_supplier_parts(sku: str = None, supplier: Company = None, mpn: str = None):
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
            supplier_parts = supplier_parts.filter(manufacturer_part__MPN__iexact=mpn)
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
        if quantity:
            try:
                quantity = Decimal(quantity)
            except InvalidOperation:
                logger.warning("Failed to parse quantity '%s'", quantity)
                quantity = None

        #  find incomplete line_items that match the supplier_part
        line_items = purchase_order.lines.filter(
            part=supplier_part.pk, quantity__gt=F('received')
        )
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
            return {'error': _('Failed to find pending line item for supplier part')}

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
            'lineitem': {'pk': line_item.pk, 'purchase_order': purchase_order.pk}
        }

        if quantity:
            response['lineitem']['quantity'] = quantity
        if location:
            response['lineitem']['location'] = location.pk

        # if either the quantity is missing or no location is defined/found
        # -> return the line_item found, so the client can gather the missing
        #    information and complete the action with an 'api-po-receive' call
        if not quantity or (not location and not no_stock_locations):
            response['action_required'] = _(
                'Further information required to receive line item'
            )
            return response

        purchase_order.receive_line_item(
            line_item, location, quantity, user, barcode=barcode
        )

        response['success'] = _('Received purchase order line item')
        return response
