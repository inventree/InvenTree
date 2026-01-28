"""Plugin mixin classes for barcode plugin."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

import structlog

from company.models import Company, ManufacturerPart, SupplierPart
from InvenTree.exceptions import log_error
from InvenTree.models import InvenTreeBarcodeMixin
from order.models import PurchaseOrder
from part.models import Part
from plugin import PluginMixinEnum
from plugin.base.integration.SettingsMixin import SettingsMixin

logger = structlog.get_logger('inventree')


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
        self.add_mixin(PluginMixinEnum.BARCODE, 'has_barcode', __class__)

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

    @property
    def has_barcode_generation(self):
        """Does this plugin support barcode generation."""
        try:
            # Attempt to call the generate method
            self.generate(None)  # type: ignore
        except NotImplementedError:
            # If a NotImplementedError is raised, then barcode generation is not supported
            return False
        except:
            pass

        return True

    def generate(self, model_instance: InvenTreeBarcodeMixin) -> str:
        """Generate barcode data for the given model instance.

        Arguments:
            model_instance: The model instance to generate barcode data for. It is extending the InvenTreeBarcodeMixin.

        Returns: The generated barcode data.
        """
        raise NotImplementedError('Generate must be implemented by a plugin')


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
        self.add_mixin(PluginMixinEnum.SUPPLIER_BARCODE, True, __class__)

    def get_field_value(self, key, backup_value=None):
        """Return the value of a barcode field."""
        fields = getattr(self, 'barcode_fields', None) or {}

        return fields.get(key, backup_value)

    def get_part(self) -> Part | None:
        """Extract the Part object from the barcode fields."""
        # TODO: Implement this
        return None

    @property
    def quantity(self):
        """Return the quantity from the barcode fields."""
        return self.get_field_value(self.QUANTITY)

    @property
    def supplier_part_number(self):
        """Return the supplier part number from the barcode fields."""
        return self.get_field_value(self.SUPPLIER_PART_NUMBER)

    def get_supplier_part(self) -> SupplierPart | None:
        """Return the SupplierPart object for the scanned barcode.

        Returns:
            SupplierPart object or None

        - Filter by the Supplier ID associated with the plugin
        - Filter by SKU (if available)
        - If more than one match is found, filter by MPN (if available)

        """
        sku = self.supplier_part_number
        mpn = self.manufacturer_part_number

        # Require at least SKU or MPN for lookup
        if not sku and not mpn:
            return None

        supplier_parts = SupplierPart.objects.all()

        # Filter by supplier
        if supplier := self.get_supplier(cache=True):
            supplier_parts = supplier_parts.filter(supplier=supplier)

        if sku:
            supplier_parts = supplier_parts.filter(SKU=sku)

        # Attempt additional filtering by MPN if multiple matches are found
        if mpn and supplier_parts.count() > 1:
            manufacturer_parts = ManufacturerPart.objects.filter(MPN=mpn)
            if manufacturer_parts.count() > 0:
                supplier_parts = supplier_parts.filter(
                    manufacturer_part__in=manufacturer_parts
                )

        # Requires a unique match
        if len(supplier_parts) == 1:
            return supplier_parts.first()

    @property
    def manufacturer_part_number(self):
        """Return the manufacturer part number from the barcode fields."""
        return self.get_field_value(self.MANUFACTURER_PART_NUMBER)

    def get_manufacturer_part(self) -> ManufacturerPart | None:
        """Return the ManufacturerPart object for the scanned barcode.

        Returns:
            ManufacturerPart object or None
        """
        mpn = self.manufacturer_part_number

        if not mpn:
            return None

        parts = ManufacturerPart.objects.filter(MPN=mpn)

        if supplier := self.get_supplier(cache=True):
            # Manufacturer part must be associated with the supplier
            # Case 1: Manufactured by this supplier
            q1 = Q(manufacturer=supplier)
            # Case 2: Supplied by this supplier
            m = (
                SupplierPart.objects
                .filter(supplier=supplier)
                .values_list('manufacturer_part', flat=True)
                .distinct()
            )
            q2 = Q(pk__in=m)

            parts = parts.filter(q1 | q2).distinct()

        # Requires a unique match
        if len(parts) == 1:
            return parts.first()

    @property
    def customer_order_number(self):
        """Return the customer order number from the barcode fields."""
        return self.get_field_value(self.CUSTOMER_ORDER_NUMBER)

    @property
    def supplier_order_number(self):
        """Return the supplier order number from the barcode fields."""
        return self.get_field_value(self.SUPPLIER_ORDER_NUMBER)

    def get_purchase_order(self) -> PurchaseOrder | None:
        """Extract the PurchaseOrder object from the barcode fields.

        Inspect the customer_order_number and supplier_order_number fields,
        and try to find a matching PurchaseOrder object.

        Returns:
            PurchaseOrder object or None
        """
        customer_order_number = self.customer_order_number
        supplier_order_number = self.supplier_order_number

        if not (customer_order_number or supplier_order_number):
            return None

        # First, attempt lookup based on the customer_order_number

        if customer_order_number:
            orders = PurchaseOrder.objects.filter(reference=customer_order_number)
        elif supplier_order_number:
            orders = PurchaseOrder.objects.filter(
                supplier_reference=supplier_order_number
            )

        if supplier := self.get_supplier(cache=True):
            orders = orders.filter(supplier=supplier)

        # Requires a unique match
        if len(orders) == 1:
            return orders.first()

    def extract_barcode_fields(self, barcode_data: str) -> dict[str, str]:
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

    def scan(self, barcode_data: str) -> dict | None:
        """Perform a generic 'scan' operation on a supplier barcode.

        The supplier barcode may provide sufficient information to match against
        one of the following model types:

        - SupplierPart
        - ManufacturerPart
        - PurchaseOrder
        - PurchaseOrderLineItem (todo)
        - StockItem (todo)
        - Part (todo)

        If any matches are made, return a dict object containing the relevant information.
        """
        barcode_data = str(barcode_data).strip()

        self.barcode_fields = self.extract_barcode_fields(barcode_data)

        # Generate possible matches for this barcode
        # Note: Each of these functions can be overridden by the plugin (if necessary)
        matches = {
            Part.barcode_model_type(): self.get_part(),
            PurchaseOrder.barcode_model_type(): self.get_purchase_order(),
            SupplierPart.barcode_model_type(): self.get_supplier_part(),
            ManufacturerPart.barcode_model_type(): self.get_manufacturer_part(),
        }

        data = {}

        # At least one matching item was found
        has_match = False

        for k, v in matches.items():
            if v and hasattr(v, 'pk'):
                has_match = True
                data[k] = v.format_matched_response()

        if not has_match:
            return None

        # Add in supplier information (if available)
        if supplier := self.get_supplier():
            data['company'] = {'pk': supplier.pk}

        data['success'] = _('Found matching item')

        return data

    def scan_receive_item(
        self,
        barcode_data: str,
        user,
        supplier=None,
        line_item=None,
        purchase_order=None,
        location=None,
        auto_allocate: bool = True,
        **kwargs,
    ) -> dict | None:
        """Attempt to receive an item against a PurchaseOrder via barcode scanning.

        Arguments:
            barcode_data: The raw barcode data
            user: The User performing the action
            supplier: The Company object to receive against (or None)
            purchase_order: The PurchaseOrder object to receive against (or None)
            line_item: The PurchaseOrderLineItem object to receive against (or None)
            location: The StockLocation object to receive into (or None)
            auto_allocate: If True, automatically receive the item (if possible)

        Returns:
            A dict object containing the result of the action.

        The more "context" data that can be provided, the better the chances of a successful match.
        """
        barcode_data = str(barcode_data).strip()

        self.barcode_fields = self.extract_barcode_fields(barcode_data)

        # Extract supplier information
        supplier = supplier or self.get_supplier(cache=True)

        if not supplier:
            # No supplier information available
            return None

        # Extract purchase order information
        purchase_order = purchase_order or self.get_purchase_order()

        if not purchase_order or purchase_order.supplier != supplier:
            # Purchase order does not match supplier
            return None

        supplier_part = self.get_supplier_part()

        if not supplier_part:
            # No supplier part information available
            return None

        # Attempt to find matching line item
        if not line_item:
            line_items = purchase_order.lines.filter(part=supplier_part)
            if line_items.count() == 1:
                line_item = line_items.first()

        if not line_item:
            # No line item information available
            return None

        if line_item.part != supplier_part:
            return {'error': _('Supplier part does not match line item')}

        if line_item.is_completed():
            return {'error': _('Line item is already completed')}

        # Extract location information for the line item
        location = (
            location
            or line_item.destination
            or purchase_order.destination
            or line_item.part.part.get_default_location()
        )

        # Extract quantity information
        quantity = self.quantity

        # At this stage, we *should* have enough information to attempt to receive the item
        # If auto_allocate is True, attempt to receive the item automatically
        # Otherwise, return the required information to the client
        action_required = not auto_allocate or location is None or quantity is None

        if quantity is None:
            quantity = line_item.remaining()

        quantity = float(quantity)

        # Construct a response object
        response = {
            'lineitem': {
                'pk': line_item.pk,
                'quantity': quantity,
                'supplier_part': supplier_part.pk,
                'purchase_order': purchase_order.pk,
                'location': location.pk if location else None,
            }
        }

        if action_required:
            # Further information is required to receive the item
            response['action_required'] = _(
                'Further information required to receive line item'
            )
        else:
            # Use the information we have to attempt to receive the item into stock
            try:
                purchase_order.receive_line_item(
                    line_item, location, quantity, user, barcode=barcode_data
                )
                response['success'] = _('Received purchase order line item')
            except ValidationError as e:
                # Pass a ValidationError back to the client
                response['error'] = e.message
            except Exception:
                # Handle any other exceptions
                log_error('scan_receive_item', plugin=self.slug)
                response['error'] = _('Failed to receive line item')

        return response

    def get_supplier(self, cache: bool = False) -> Company | None:
        """Get the supplier for the SUPPLIER_ID set in the plugin settings.

        If it's not defined, try to guess it and set it if possible.
        """
        if not isinstance(self, SettingsMixin):
            return None

        def _cache_supplier(supplier):
            """Cache and return the supplier object."""
            if cache:
                self._supplier = supplier
            return supplier

        # Cache the supplier object, so we don't have to look it up every time
        if cache and hasattr(self, '_supplier'):
            return self._supplier

        if supplier_pk := self.get_setting('SUPPLIER_ID'):
            return _cache_supplier(Company.objects.filter(pk=supplier_pk).first())

        if not (supplier_name := getattr(self, 'DEFAULT_SUPPLIER_NAME', None)):
            return _cache_supplier(None)

        suppliers = Company.objects.filter(
            name__icontains=supplier_name, is_supplier=True
        )

        if len(suppliers) != 1:
            return _cache_supplier(None)

        supplier = suppliers.first()
        assert supplier

        self.set_setting('SUPPLIER_ID', supplier.pk)

        return _cache_supplier(supplier)

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
            return []

        return SupplierBarcodeMixin.split_fields(
            barcode_data, delimiter=DELIMITER, header=HEADER, trailer=TRAILER
        )
