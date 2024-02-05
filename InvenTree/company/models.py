"""Company database model definitions."""

import os
from datetime import datetime
from decimal import Decimal

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum, UniqueConstraint
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy as __

from moneyed import CURRENCIES
from stdimage.models import StdImageField
from taggit.managers import TaggableManager

import common.models
import common.settings
import InvenTree.conversion
import InvenTree.fields
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import InvenTree.validators
from common.settings import currency_code_default
from InvenTree.fields import InvenTreeURLField, RoundingDecimalField
from InvenTree.status_codes import PurchaseOrderStatusGroups


def rename_company_image(instance, filename):
    """Function to rename a company image after upload.

    Args:
        instance: Company object
        filename: uploaded image filename

    Returns:
        New image filename
    """
    base = 'company_images'

    if filename.count('.') > 0:
        ext = filename.split('.')[-1]
    else:
        ext = ''

    fn = f'company_{instance.pk}_img'

    if ext:
        fn += '.' + ext

    return os.path.join(base, fn)


class Company(
    InvenTree.models.InvenTreeNotesMixin, InvenTree.models.InvenTreeModelBase
):
    """A Company object represents an external company.

    It may be a supplier or a customer or a manufacturer (or a combination)

    - A supplier is a company from which parts can be purchased
    - A customer is a company to which parts can be sold
    - A manufacturer is a company which manufactures a raw good (they may or may not be a "supplier" also)


    Attributes:
        name: Brief name of the company
        description: Longer form description
        website: URL for the company website
        address: One-line string representation of primary address
        phone: contact phone number
        email: contact email address
        link: Secondary URL e.g. for link to internal Wiki page
        image: Company image / logo
        notes: Extra notes about the company
        is_customer: boolean value, is this company a customer
        is_supplier: boolean value, is this company a supplier
        is_manufacturer: boolean value, is this company a manufacturer
        currency_code: Specifies the default currency for the company
    """

    class Meta:
        """Metaclass defines extra model options."""

        ordering = ['name']
        constraints = [
            UniqueConstraint(fields=['name', 'email'], name='unique_name_email_pair')
        ]
        verbose_name_plural = 'Companies'

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the Company model."""
        return reverse('api-company-list')

    name = models.CharField(
        max_length=100,
        blank=False,
        help_text=_('Company name'),
        verbose_name=_('Company name'),
    )

    description = models.CharField(
        max_length=500,
        verbose_name=_('Company description'),
        help_text=_('Description of the company'),
        blank=True,
    )

    website = InvenTreeURLField(
        blank=True, verbose_name=_('Website'), help_text=_('Company website URL')
    )

    phone = models.CharField(
        max_length=50,
        verbose_name=_('Phone number'),
        blank=True,
        help_text=_('Contact phone number'),
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email'),
        help_text=_('Contact email address'),
    )

    contact = models.CharField(
        max_length=100,
        verbose_name=_('Contact'),
        blank=True,
        help_text=_('Point of contact'),
    )

    link = InvenTreeURLField(
        blank=True,
        verbose_name=_('Link'),
        help_text=_('Link to external company information'),
    )

    image = StdImageField(
        upload_to=rename_company_image,
        null=True,
        blank=True,
        variations={'thumbnail': (128, 128), 'preview': (256, 256)},
        delete_orphans=True,
        verbose_name=_('Image'),
    )

    is_customer = models.BooleanField(
        default=False,
        verbose_name=_('is customer'),
        help_text=_('Do you sell items to this company?'),
    )

    is_supplier = models.BooleanField(
        default=True,
        verbose_name=_('is supplier'),
        help_text=_('Do you purchase items from this company?'),
    )

    is_manufacturer = models.BooleanField(
        default=False,
        verbose_name=_('is manufacturer'),
        help_text=_('Does this company manufacture parts?'),
    )

    currency = models.CharField(
        max_length=3,
        verbose_name=_('Currency'),
        blank=True,
        default=currency_code_default,
        help_text=_('Default currency used for this company'),
        validators=[InvenTree.validators.validate_currency_code],
    )

    @property
    def address(self):
        """Return the string representation for the primary address.

        This property exists for backwards compatibility
        """
        addr = self.primary_address

        return str(addr) if addr is not None else None

    @property
    def primary_address(self):
        """Returns address object of primary address. Parsed by serializer."""
        return Address.objects.filter(company=self.id).filter(primary=True).first()

    @property
    def currency_code(self):
        """Return the currency code associated with this company.

        - If the currency code is invalid, use the default currency
        - If the currency code is not specified, use the default currency
        """
        code = self.currency

        if code not in CURRENCIES:
            code = common.settings.currency_code_default()

        return code

    def __str__(self):
        """Get string representation of a Company."""
        return f'{self.name} - {self.description}'

    def get_absolute_url(self):
        """Get the web URL for the detail view for this Company."""
        return reverse('company-detail', kwargs={'pk': self.id})

    def get_image_url(self):
        """Return the URL of the image for this company."""
        if self.image:
            return InvenTree.helpers.getMediaUrl(self.image.url)
        return InvenTree.helpers.getBlankImage()

    def get_thumbnail_url(self):
        """Return the URL for the thumbnail image for this Company."""
        if self.image:
            return InvenTree.helpers.getMediaUrl(self.image.thumbnail.url)
        return InvenTree.helpers.getBlankThumbnail()

    @property
    def parts(self):
        """Return SupplierPart objects which are supplied or manufactured by this company."""
        return SupplierPart.objects.filter(
            Q(supplier=self.id) | Q(manufacturer_part__manufacturer=self.id)
        ).distinct()

    @property
    def stock_items(self):
        """Return a list of all stock items supplied or manufactured by this company."""
        stock = apps.get_model('stock', 'StockItem')
        return stock.objects.filter(
            Q(supplier_part__supplier=self.id)
            | Q(supplier_part__manufacturer_part__manufacturer=self.id)
        ).distinct()


class CompanyAttachment(InvenTree.models.InvenTreeAttachment):
    """Model for storing file or URL attachments against a Company object."""

    @staticmethod
    def get_api_url():
        """Return the API URL associated with this model."""
        return reverse('api-company-attachment-list')

    def getSubdir(self):
        """Return the subdirectory where these attachments are uploaded."""
        return os.path.join('company_files', str(self.company.pk))

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_('Company'),
        related_name='attachments',
    )


class Contact(InvenTree.models.InvenTreeModelBase):
    """A Contact represents a person who works at a particular company. A Company may have zero or more associated Contact objects.

    Attributes:
        company: Company link for this contact
        name: Name of the contact
        phone: contact phone number
        email: contact email
        role: position in company
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the Contcat model."""
        return reverse('api-contact-list')

    company = models.ForeignKey(
        Company, related_name='contacts', on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)

    phone = models.CharField(max_length=100, blank=True)

    email = models.EmailField(blank=True)

    role = models.CharField(max_length=100, blank=True)


class Address(InvenTree.models.InvenTreeModelBase):
    """An address represents a physical location where the company is located. It is possible for a company to have multiple locations.

    Attributes:
        company: Company link for this address
        title: Human-readable name for the address
        primary: True if this is the company's primary address
        line1: First line of address
        line2: Optional line two for address
        postal_code: Postal code, city and state
        country: Location country
        shipping_notes: Notes for couriers transporting shipments to this address
        internal_shipping_notes: Internal notes regarding shipping to this address
        link: External link to additional address information
    """

    class Meta:
        """Metaclass defines extra model options."""

        verbose_name_plural = 'Addresses'

    def __init__(self, *args, **kwargs):
        """Custom init function."""
        super().__init__(*args, **kwargs)

    def __str__(self):
        """Defines string representation of address to supple a one-line to API calls."""
        available_lines = [
            self.line1,
            self.line2,
            self.postal_code,
            self.postal_city,
            self.province,
            self.country,
        ]

        populated_lines = []
        for line in available_lines:
            if len(line) > 0:
                populated_lines.append(line)

        return ', '.join(populated_lines)

    def save(self, *args, **kwargs):
        """Run checks when saving an address.

        Rules:
        - If this address is marked as "primary", ensure that all other addresses for this company are marked as non-primary
        """
        others = list(
            Address.objects.filter(company=self.company).exclude(pk=self.pk).all()
        )

        # If this is the *only* address for this company, make it the primary one
        if len(others) == 0:
            self.primary = True

        super().save(*args, **kwargs)

        # Once this address is saved, check others
        if self.primary:
            for addr in others:
                if addr.primary:
                    addr.primary = False
                    addr.save()

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the Contcat model."""
        return reverse('api-address-list')

    company = models.ForeignKey(
        Company,
        related_name='addresses',
        on_delete=models.CASCADE,
        verbose_name=_('Company'),
        help_text=_('Select company'),
    )

    title = models.CharField(
        max_length=100,
        verbose_name=_('Address title'),
        help_text=_('Title describing the address entry'),
        blank=False,
    )

    primary = models.BooleanField(
        default=False,
        verbose_name=_('Primary address'),
        help_text=_('Set as primary address'),
    )

    line1 = models.CharField(
        max_length=50,
        verbose_name=_('Line 1'),
        help_text=_('Address line 1'),
        blank=True,
    )

    line2 = models.CharField(
        max_length=50,
        verbose_name=_('Line 2'),
        help_text=_('Address line 2'),
        blank=True,
    )

    postal_code = models.CharField(
        max_length=10,
        verbose_name=_('Postal code'),
        help_text=_('Postal code'),
        blank=True,
    )

    postal_city = models.CharField(
        max_length=50,
        verbose_name=_('City/Region'),
        help_text=_('Postal code city/region'),
        blank=True,
    )

    province = models.CharField(
        max_length=50,
        verbose_name=_('State/Province'),
        help_text=_('State or province'),
        blank=True,
    )

    country = models.CharField(
        max_length=50,
        verbose_name=_('Country'),
        help_text=_('Address country'),
        blank=True,
    )

    shipping_notes = models.CharField(
        max_length=100,
        verbose_name=_('Courier shipping notes'),
        help_text=_('Notes for shipping courier'),
        blank=True,
    )

    internal_shipping_notes = models.CharField(
        max_length=100,
        verbose_name=_('Internal shipping notes'),
        help_text=_('Shipping notes for internal use'),
        blank=True,
    )

    link = InvenTreeURLField(
        blank=True,
        verbose_name=_('Link'),
        help_text=_('Link to address information (external)'),
    )


class ManufacturerPart(
    InvenTree.models.InvenTreeBarcodeMixin, InvenTree.models.InvenTreeModelBase
):
    """Represents a unique part as provided by a Manufacturer Each ManufacturerPart is identified by a MPN (Manufacturer Part Number) Each ManufacturerPart is also linked to a Part object. A Part may be available from multiple manufacturers.

    Attributes:
        part: Link to the master Part
        manufacturer: Company that manufactures the ManufacturerPart
        MPN: Manufacture part number
        link: Link to external website for this manufacturer part
        description: Descriptive notes field
    """

    class Meta:
        """Metaclass defines extra model options."""

        unique_together = ('part', 'manufacturer', 'MPN')

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the ManufacturerPart instance."""
        return reverse('api-manufacturer-part-list')

    part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='manufacturer_parts',
        verbose_name=_('Base Part'),
        limit_choices_to={'purchaseable': True},
        help_text=_('Select part'),
    )

    manufacturer = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        related_name='manufactured_parts',
        limit_choices_to={'is_manufacturer': True},
        verbose_name=_('Manufacturer'),
        help_text=_('Select manufacturer'),
    )

    MPN = models.CharField(
        null=True,
        max_length=100,
        verbose_name=_('MPN'),
        help_text=_('Manufacturer Part Number'),
    )

    link = InvenTreeURLField(
        blank=True,
        null=True,
        verbose_name=_('Link'),
        help_text=_('URL for external manufacturer part link'),
    )

    description = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Manufacturer part description'),
    )

    tags = TaggableManager(blank=True)

    @classmethod
    def create(cls, part, manufacturer, mpn, description, link=None):
        """Check if ManufacturerPart instance does not already exist then create it."""
        manufacturer_part = None

        try:
            manufacturer_part = ManufacturerPart.objects.get(
                part=part, manufacturer=manufacturer, MPN=mpn
            )
        except ManufacturerPart.DoesNotExist:
            pass

        if not manufacturer_part:
            manufacturer_part = ManufacturerPart(
                part=part,
                manufacturer=manufacturer,
                MPN=mpn,
                description=description,
                link=link,
            )
            manufacturer_part.save()

        return manufacturer_part

    def __str__(self):
        """Format a string representation of a ManufacturerPart."""
        s = ''

        if self.manufacturer:
            s += f'{self.manufacturer.name}'
            s += ' | '

        s += f'{self.MPN}'

        return s


class ManufacturerPartAttachment(InvenTree.models.InvenTreeAttachment):
    """Model for storing file attachments against a ManufacturerPart object."""

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the ManufacturerPartAttachment model."""
        return reverse('api-manufacturer-part-attachment-list')

    def getSubdir(self):
        """Return the subdirectory where attachment files for the ManufacturerPart model are located."""
        return os.path.join('manufacturer_part_files', str(self.manufacturer_part.id))

    manufacturer_part = models.ForeignKey(
        ManufacturerPart,
        on_delete=models.CASCADE,
        verbose_name=_('Manufacturer Part'),
        related_name='attachments',
    )


class ManufacturerPartParameter(InvenTree.models.InvenTreeModelBase):
    """A ManufacturerPartParameter represents a key:value parameter for a MnaufacturerPart.

    This is used to represent parameters / properties for a particular manufacturer part.

    Each parameter is a simple string (text) value.
    """

    class Meta:
        """Metaclass defines extra model options."""

        unique_together = ('manufacturer_part', 'name')

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the ManufacturerPartParameter model."""
        return reverse('api-manufacturer-part-parameter-list')

    manufacturer_part = models.ForeignKey(
        ManufacturerPart,
        on_delete=models.CASCADE,
        related_name='parameters',
        verbose_name=_('Manufacturer Part'),
    )

    name = models.CharField(
        max_length=500,
        blank=False,
        verbose_name=_('Name'),
        help_text=_('Parameter name'),
    )

    value = models.CharField(
        max_length=500,
        blank=False,
        verbose_name=_('Value'),
        help_text=_('Parameter value'),
    )

    units = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=_('Units'),
        help_text=_('Parameter units'),
    )


class SupplierPartManager(models.Manager):
    """Define custom SupplierPart objects manager.

    The main purpose of this manager is to improve database hit as the
    SupplierPart model involves A LOT of foreign keys lookups
    """

    def get_queryset(self):
        """Prefetch related fields when querying against the SupplierPart model."""
        # Always prefetch related models
        return (
            super()
            .get_queryset()
            .prefetch_related('part', 'supplier', 'manufacturer_part__manufacturer')
        )


class SupplierPart(
    InvenTree.models.MetadataMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    common.models.MetaMixin,
    InvenTree.models.InvenTreeModelBase,
):
    """Represents a unique part as provided by a Supplier Each SupplierPart is identified by a SKU (Supplier Part Number) Each SupplierPart is also linked to a Part or ManufacturerPart object. A Part may be available from multiple suppliers.

    Attributes:
        part: Link to the master Part (Obsolete)
        source_item: The sourcing item linked to this SupplierPart instance
        supplier: Company that supplies this SupplierPart object
        SKU: Stock keeping unit (supplier part number)
        link: Link to external website for this supplier part
        description: Descriptive notes field
        note: Longer form note field
        base_cost: Base charge added to order independent of quantity e.g. "Reeling Fee"
        multiple: Multiple that the part is provided in
        lead_time: Supplier lead time
        packaging: packaging that the part is supplied in, e.g. "Reel"
        pack_quantity: Quantity of item supplied in a single pack (e.g. 30ml in a single tube)
        pack_quantity_native: Pack quantity, converted to "native" units of the referenced part
        updated: Date that the SupplierPart was last updated
    """

    class Meta:
        """Metaclass defines extra model options."""

        unique_together = ('part', 'supplier', 'SKU')

        # This model was moved from the 'Part' app
        db_table = 'part_supplierpart'

    objects = SupplierPartManager()

    tags = TaggableManager(blank=True)

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SupplierPart model."""
        return reverse('api-supplier-part-list')

    def get_absolute_url(self):
        """Return the web URL of the detail view for this SupplierPart."""
        return reverse('supplier-part-detail', kwargs={'pk': self.id})

    def api_instance_filters(self):
        """Return custom API filters for this particular instance."""
        return {'manufacturer_part': {'part': self.part.pk}}

    def clean(self):
        """Custom clean action for the SupplierPart model.

        Rules:
        - Ensure that manufacturer_part.part and part are the same!
        """
        super().clean()

        self.pack_quantity = self.pack_quantity.strip()

        # An empty 'pack_quantity' value is equivalent to '1'
        if self.pack_quantity == '':
            self.pack_quantity = '1'

        # Validate that the UOM is compatible with the base part
        if self.pack_quantity and self.part:
            try:
                # Attempt conversion to specified unit
                native_value = InvenTree.conversion.convert_physical_value(
                    self.pack_quantity, self.part.units, strip_units=False
                )

                # If part units are not provided, value must be dimensionless
                if not self.part.units and not InvenTree.conversion.is_dimensionless(
                    native_value
                ):
                    raise ValidationError({
                        'pack_quantity': _(
                            'Pack units must be compatible with the base part units'
                        )
                    })

                # Native value must be greater than zero
                if float(native_value.magnitude) <= 0:
                    raise ValidationError({
                        'pack_quantity': _('Pack units must be greater than zero')
                    })

                # Update native pack units value
                self.pack_quantity_native = Decimal(native_value.magnitude)

            except ValidationError as e:
                raise ValidationError({'pack_quantity': e.messages})

        # Ensure that the linked manufacturer_part points to the same part!
        if self.manufacturer_part and self.part:
            if self.manufacturer_part.part != self.part:
                raise ValidationError({
                    'manufacturer_part': _(
                        'Linked manufacturer part must reference the same base part'
                    )
                })

    def save(self, *args, **kwargs):
        """Overriding save method to connect an existing ManufacturerPart."""
        manufacturer_part = None

        if all(key in kwargs for key in ('manufacturer', 'MPN')):
            manufacturer_name = kwargs.pop('manufacturer')
            MPN = kwargs.pop('MPN')

            # Retrieve manufacturer part
            try:
                manufacturer_part = ManufacturerPart.objects.get(
                    manufacturer__name=manufacturer_name, MPN=MPN
                )
            except (ValueError, Company.DoesNotExist):
                # ManufacturerPart does not exist
                pass

        if manufacturer_part:
            if not self.manufacturer_part:
                # Connect ManufacturerPart to SupplierPart
                self.manufacturer_part = manufacturer_part
            else:
                raise ValidationError(
                    f'SupplierPart {self.__str__} is already linked to {self.manufacturer_part}'
                )

        self.clean()
        self.validate_unique()

        super().save(*args, **kwargs)

    part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        related_name='supplier_parts',
        verbose_name=_('Base Part'),
        limit_choices_to={'purchaseable': True},
        help_text=_('Select part'),
    )

    supplier = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='supplied_parts',
        limit_choices_to={'is_supplier': True},
        verbose_name=_('Supplier'),
        help_text=_('Select supplier'),
    )

    SKU = models.CharField(
        max_length=100,
        verbose_name=__('SKU = Stock Keeping Unit (supplier part number)', 'SKU'),
        help_text=_('Supplier stock keeping unit'),
    )

    manufacturer_part = models.ForeignKey(
        ManufacturerPart,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='supplier_parts',
        verbose_name=_('Manufacturer Part'),
        help_text=_('Select manufacturer part'),
    )

    link = InvenTreeURLField(
        blank=True,
        null=True,
        verbose_name=_('Link'),
        help_text=_('URL for external supplier part link'),
    )

    description = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Supplier part description'),
    )

    note = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Note'),
        help_text=_('Notes'),
    )

    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('base cost'),
        help_text=_('Minimum charge (e.g. stocking fee)'),
    )

    packaging = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Packaging'),
        help_text=_('Part packaging'),
    )

    pack_quantity = models.CharField(
        max_length=25,
        verbose_name=_('Pack Quantity'),
        help_text=_(
            'Total quantity supplied in a single pack. Leave empty for single items.'
        ),
        blank=True,
    )

    pack_quantity_native = RoundingDecimalField(
        max_digits=20, decimal_places=10, default=1, null=True
    )

    def base_quantity(self, quantity=1) -> Decimal:
        """Calculate the base unit quantiy for a given quantity."""
        q = Decimal(quantity) * Decimal(self.pack_quantity_native)
        q = round(q, 10).normalize()

        return q

    multiple = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('multiple'),
        help_text=_('Order multiple'),
    )

    # TODO - Reimplement lead-time as a charfield with special validation (pattern matching).
    # lead_time = models.DurationField(blank=True, null=True)

    available = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Available'),
        help_text=_('Quantity available from supplier'),
    )

    availability_updated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Availability Updated'),
        help_text=_('Date of last update of availability data'),
    )

    def update_available_quantity(self, quantity):
        """Update the available quantity for this SupplierPart."""
        self.available = quantity
        self.availability_updated = datetime.now()
        self.save()

    @property
    def name(self):
        """Return string representation of own name."""
        return str(self)

    @property
    def manufacturer_string(self):
        """Format a MPN string for this SupplierPart.

        Concatenates manufacture name and part number.
        """
        items = []

        if self.manufacturer_part:
            if self.manufacturer_part.manufacturer:
                items.append(self.manufacturer_part.manufacturer.name)
            if self.manufacturer_part.MPN:
                items.append(self.manufacturer_part.MPN)

        return ' | '.join(items)

    @property
    def has_price_breaks(self):
        """Return True if this SupplierPart has associated price breaks."""
        return self.price_breaks.count() > 0

    @property
    def price_breaks(self):
        """Return the associated price breaks in the correct order."""
        return self.pricebreaks.order_by('quantity').all()

    @property
    def unit_pricing(self):
        """Return the single-quantity pricing for this SupplierPart."""
        return self.get_price(1)

    def add_price_break(self, quantity, price) -> None:
        """Create a new price break for this part.

        Args:
            quantity: Numerical quantity
            price: Must be a Money object
        """
        # Check if a price break at that quantity already exists...
        if self.price_breaks.filter(quantity=quantity, part=self.pk).exists():
            return

        SupplierPriceBreak.objects.create(part=self, quantity=quantity, price=price)

    get_price = common.models.get_price

    def open_orders(self):
        """Return a database query for PurchaseOrder line items for this SupplierPart, limited to purchase orders that are open / outstanding."""
        return self.purchase_order_line_items.prefetch_related('order').filter(
            order__status__in=PurchaseOrderStatusGroups.OPEN
        )

    def on_order(self):
        """Return the total quantity of items currently on order.

        Subtract partially received stock as appropriate
        """
        totals = self.open_orders().aggregate(Sum('quantity'), Sum('received'))

        # Quantity on order
        q = totals.get('quantity__sum', 0)

        # Quantity received
        r = totals.get('received__sum', 0)

        if q is None or r is None:
            return 0
        return max(q - r, 0)

    def purchase_orders(self):
        """Returns a list of purchase orders relating to this supplier part."""
        return [
            line.order
            for line in self.purchase_order_line_items.all().prefetch_related('order')
        ]

    @property
    def pretty_name(self):
        """Format a 'pretty' name for this SupplierPart."""
        return str(self)

    def __str__(self):
        """Format a string representation of a SupplierPart."""
        s = ''

        if self.part.IPN:
            s += f'{self.part.IPN}'
            s += ' | '

        s += f'{self.supplier.name} | {self.SKU}'

        if self.manufacturer_string:
            s = s + ' | ' + self.manufacturer_string

        return s


class SupplierPriceBreak(common.models.PriceBreak):
    """Represents a quantity price break for a SupplierPart.

    - Suppliers can offer discounts at larger quantities
    - SupplierPart(s) may have zero-or-more associated SupplierPriceBreak(s)

    Attributes:
        part: Link to a SupplierPart object that this price break applies to
        updated: Automatic DateTime field that shows last time the price break was updated
        quantity: Quantity required for price break
        cost: Cost at specified quantity
        currency: Reference to the currency of this pricebreak (leave empty for base currency)
    """

    class Meta:
        """Metaclass defines extra model options."""

        unique_together = ('part', 'quantity')

        # This model was moved from the 'Part' app
        db_table = 'part_supplierpricebreak'

    def __str__(self):
        """Format a string representation of a SupplierPriceBreak instance."""
        return f'{self.part.SKU} - {self.price} @ {self.quantity}'

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SupplierPriceBreak model."""
        return reverse('api-part-supplier-price-list')

    part = models.ForeignKey(
        SupplierPart,
        on_delete=models.CASCADE,
        related_name='pricebreaks',
        verbose_name=_('Part'),
    )


@receiver(
    post_save, sender=SupplierPriceBreak, dispatch_uid='post_save_supplier_price_break'
)
def after_save_supplier_price(sender, instance, created, **kwargs):
    """Callback function when a SupplierPriceBreak is created or updated."""
    if InvenTree.ready.canAppAccessDatabase() and not InvenTree.ready.isImportingData():
        if instance.part and instance.part.part:
            instance.part.part.schedule_pricing_update(create=True)


@receiver(
    post_delete,
    sender=SupplierPriceBreak,
    dispatch_uid='post_delete_supplier_price_break',
)
def after_delete_supplier_price(sender, instance, **kwargs):
    """Callback function when a SupplierPriceBreak is deleted."""
    if InvenTree.ready.canAppAccessDatabase() and not InvenTree.ready.isImportingData():
        if instance.part and instance.part.part:
            instance.part.part.schedule_pricing_update(create=False)
