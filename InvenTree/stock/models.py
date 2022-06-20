"""Stock database model definitions."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.core.exceptions import FieldError, ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from jinja2 import Template
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey

import common.models
import InvenTree.helpers
import InvenTree.ready
import InvenTree.tasks
import label.models
import report.models
from company import models as CompanyModels
from InvenTree.fields import (InvenTreeModelMoneyField, InvenTreeNotesField,
                              InvenTreeURLField)
from InvenTree.models import InvenTreeAttachment, InvenTreeTree
from InvenTree.serializers import extract_int
from InvenTree.status_codes import StockHistoryCode, StockStatus
from part import models as PartModels
from plugin.events import trigger_event
from plugin.models import MetadataMixin
from users.models import Owner


class StockLocation(MetadataMixin, InvenTreeTree):
    """Organization tree for StockItem objects.

    A "StockLocation" can be considered a warehouse, or storage location
    Stock locations can be heirarchical as required
    """

    def delete(self, *args, **kwargs):
        """Custom model deletion routine, which updates any child locations or items.

        This must be handled within a transaction.atomic(), otherwise the tree structure is damaged
        """
        with transaction.atomic():

            parent = self.parent
            tree_id = self.tree_id

            # Update each stock item in the stock location
            for item in self.stock_items.all():
                item.location = self.parent
                item.save()

            # Update each child category
            for child in self.children.all():
                child.parent = self.parent
                child.save()

            super().delete(*args, **kwargs)

            if parent is not None:
                # Partially rebuild the tree (cheaper than a complete rebuild)
                StockLocation.objects.partial_rebuild(tree_id)
            else:
                StockLocation.objects.rebuild()

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-location-list')

    owner = models.ForeignKey(Owner, on_delete=models.SET_NULL, blank=True, null=True,
                              verbose_name=_('Owner'),
                              help_text=_('Select Owner'),
                              related_name='stock_locations')

    def get_location_owner(self):
        """Get the closest "owner" for this location.

        Start at this location, and traverse "up" the location tree until we find an owner
        """
        for loc in self.get_ancestors(include_self=True, ascending=True):
            if loc.owner is not None:
                return loc.owner

        return None

    def check_ownership(self, user):
        """Check if the user "owns" (is one of the owners of) the location."""
        # Superuser accounts automatically "own" everything
        if user.is_superuser:
            return True

        ownership_enabled = common.models.InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if not ownership_enabled:
            # Location ownership function is not enabled, so return True
            return True

        owner = self.get_location_owner()

        if owner is None:
            # No owner set, for this location or any location above
            # So, no ownership checks to perform!
            return True

        return user in owner.get_related_owners(include_group=True)

    def get_absolute_url(self):
        """Return url for instance."""
        return reverse('stock-location-detail', kwargs={'pk': self.id})

    def format_barcode(self, **kwargs):
        """Return a JSON string for formatting a barcode for this StockLocation object."""
        return InvenTree.helpers.MakeBarcode(
            'stocklocation',
            self.pk,
            {
                "name": self.name,
                "url": reverse('api-location-detail', kwargs={'pk': self.id}),
            },
            **kwargs
        )

    @property
    def barcode(self) -> str:
        """Get Brief payload data (e.g. for labels).

        Returns:
            str: Brief pyload data
        """
        return self.format_barcode(brief=True)

    def get_stock_items(self, cascade=True):
        """Return a queryset for all stock items under this category.

        Args:
            cascade: If True, also look under sublocations (default = True)
        """
        if cascade:
            query = StockItem.objects.filter(location__in=self.getUniqueChildren(include_self=True))
        else:
            query = StockItem.objects.filter(location=self.pk)

        return query

    def stock_item_count(self, cascade=True):
        """Return the number of StockItem objects which live in or under this category."""
        return self.get_stock_items(cascade).count()

    @property
    def item_count(self):
        """Simply returns the number of stock items in this location.

        Required for tree view serializer.
        """
        return self.stock_item_count()


class StockItemManager(TreeManager):
    """Custom database manager for the StockItem class.

    StockItem querysets will automatically prefetch related fields.
    """

    def get_queryset(self):
        """Prefetch queryset to optimise db hits."""
        return super().get_queryset().prefetch_related(
            'belongs_to',
            'build',
            'customer',
            'purchase_order',
            'sales_order',
            'supplier_part',
            'supplier_part__supplier',
            'allocations',
            'sales_order_allocations',
            'location',
            'part',
            'tracking_info'
        )


def generate_batch_code():
    """Generate a default 'batch code' for a new StockItem.

    This uses the value of the 'STOCK_BATCH_CODE_TEMPLATE' setting (if configured),
    which can be passed through a simple template.
    """
    batch_template = common.models.InvenTreeSetting.get_setting('STOCK_BATCH_CODE_TEMPLATE', '')

    now = datetime.now()

    # Pass context data through to the template randering.
    # The folowing context variables are availble for custom batch code generation
    context = {
        'date': now,
        'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.minute,
        'minute': now.minute,
    }

    return Template(batch_template).render(context)


class StockItem(MetadataMixin, MPTTModel):
    """A StockItem object represents a quantity of physical instances of a part.

    Attributes:
        parent: Link to another StockItem from which this StockItem was created
        uid: Field containing a unique-id which is mapped to a third-party identifier (e.g. a barcode)
        part: Link to the master abstract part that this StockItem is an instance of
        supplier_part: Link to a specific SupplierPart (optional)
        location: Where this StockItem is located
        quantity: Number of stocked units
        batch: Batch number for this StockItem
        serial: Unique serial number for this StockItem
        link: Optional URL to link to external resource
        updated: Date that this stock item was last updated (auto)
        expiry_date: Expiry date of the StockItem (optional)
        stocktake_date: Date of last stocktake for this item
        stocktake_user: User that performed the most recent stocktake
        review_needed: Flag if StockItem needs review
        delete_on_deplete: If True, StockItem will be deleted when the stock level gets to zero
        status: Status of this StockItem (ref: InvenTree.status_codes.StockStatus)
        notes: Extra notes field
        build: Link to a Build (if this stock item was created from a build)
        is_building: Boolean field indicating if this stock item is currently being built (or is "in production")
        purchase_order: Link to a PurchaseOrder (if this stock item was created from a PurchaseOrder)
        infinite: If True this StockItem can never be exhausted
        sales_order: Link to a SalesOrder object (if the StockItem has been assigned to a SalesOrder)
        purchase_price: The unit purchase price for this StockItem - this is the unit price at time of purchase (if this item was purchased from an external supplier)
        packaging: Description of how the StockItem is packaged (e.g. "reel", "loose", "tape" etc)
    """

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-stock-list')

    def api_instance_filters(self):
        """Custom API instance filters."""
        return {
            'parent': {
                'exclude_tree': self.pk,
            }
        }

    # A Query filter which will be re-used in multiple places to determine if a StockItem is actually "in stock"
    IN_STOCK_FILTER = Q(
        quantity__gt=0,
        sales_order=None,
        belongs_to=None,
        customer=None,
        is_building=False,
        status__in=StockStatus.AVAILABLE_CODES
    )

    # A query filter which can be used to filter StockItem objects which have expired
    EXPIRED_FILTER = IN_STOCK_FILTER & ~Q(expiry_date=None) & Q(expiry_date__lt=datetime.now().date())

    def update_serial_number(self):
        """Update the 'serial_int' field, to be an integer representation of the serial number.

        This is used for efficient numerical sorting
        """
        serial = getattr(self, 'serial', '')

        # Default value if we cannot convert to an integer
        serial_int = 0

        if serial is not None:

            serial = str(serial).strip()

            serial_int = extract_int(serial)

        self.serial_int = serial_int

    def get_next_serialized_item(self, include_variants=True, reverse=False):
        """Get the "next" serial number for the part this stock item references.

        e.g. if this stock item has a serial number 100, we may return the stock item with serial number 101

        Note that this only works for "serialized" stock items with integer values

        Args:
            include_variants: True if we wish to include stock for variant parts
            reverse: True if we want to return the "previous" (lower) serial number

        Returns:
            A StockItem object matching the requirements, or None
        """
        if not self.serialized:
            return None

        # Find only serialized stock items
        items = StockItem.objects.exclude(serial=None).exclude(serial='')

        if include_variants:
            # Match against any part within the variant tree
            items = items.filter(part__tree_id=self.part.tree_id)
        else:
            # Match only against the specific part
            items = items.filter(part=self.part)

        serial = self.serial_int

        if reverse:
            # Select only stock items with lower serial numbers, in decreasing order
            items = items.filter(serial_int__lt=serial)
            items = items.order_by('-serial_int')
        else:
            # Select only stock items with higher serial numbers, in increasing order
            items = items.filter(serial_int__gt=serial)
            items = items.order_by('serial_int')

        if items.count() > 0:
            item = items.first()

            if item.serialized:
                return item

        return None

    def save(self, *args, **kwargs):
        """Save this StockItem to the database.

        Performs a number of checks:
        - Unique serial number requirement
        - Adds a transaction note when the item is first created.
        """
        self.validate_unique()
        self.clean()

        self.update_serial_number()

        user = kwargs.pop('user', None)

        if user is None:
            user = getattr(self, '_user', None)

        # If 'add_note = False' specified, then no tracking note will be added for item creation
        add_note = kwargs.pop('add_note', True)

        notes = kwargs.pop('notes', '')

        if self.pk:
            # StockItem has already been saved

            # Check if "interesting" fields have been changed
            # (we wish to record these as historical records)

            try:
                old = StockItem.objects.get(pk=self.pk)

                deltas = {}

                # Status changed?
                if old.status != self.status:
                    deltas['status'] = self.status

                # TODO - Other interesting changes we are interested in...

                if add_note and len(deltas) > 0:
                    self.add_tracking_entry(
                        StockHistoryCode.EDITED,
                        user,
                        deltas=deltas,
                        notes=notes,
                    )

            except (ValueError, StockItem.DoesNotExist):
                pass

        super(StockItem, self).save(*args, **kwargs)

        # If user information is provided, and no existing note exists, create one!
        if user and self.tracking_info.count() == 0:

            tracking_info = {
                'status': self.status,
            }

            self.add_tracking_entry(
                StockHistoryCode.CREATED,
                user,
                deltas=tracking_info,
                notes=notes,
                location=self.location,
                quantity=float(self.quantity),
            )

    @property
    def status_label(self):
        """Return label."""
        return StockStatus.label(self.status)

    @property
    def serialized(self):
        """Return True if this StockItem is serialized."""
        return self.serial is not None and len(str(self.serial).strip()) > 0 and self.quantity == 1

    def validate_unique(self, exclude=None):
        """Test that this StockItem is "unique".

        If the StockItem is serialized, the same serial number.
        cannot exist for the same part (or part tree).
        """
        super(StockItem, self).validate_unique(exclude)

        # If the serial number is set, make sure it is not a duplicate
        if self.serial:
            # Query to look for duplicate serial numbers
            parts = PartModels.Part.objects.filter(tree_id=self.part.tree_id)
            stock = StockItem.objects.filter(part__in=parts, serial=self.serial)

            # Exclude myself from the search
            if self.pk is not None:
                stock = stock.exclude(pk=self.pk)

            if stock.exists():
                raise ValidationError({"serial": _("StockItem with this serial number already exists")})

    def clean(self):
        """Validate the StockItem object (separate to field validation).

        The following validation checks are performed:
        - The 'part' and 'supplier_part.part' fields cannot point to the same Part object
        - The 'part' does not belong to itself
        - Quantity must be 1 if the StockItem has a serial number
        """
        super().clean()

        # Strip serial number field
        if type(self.serial) is str:
            self.serial = self.serial.strip()

        # Strip batch code field
        if type(self.batch) is str:
            self.batch = self.batch.strip()

        try:
            if self.part.trackable:
                # Trackable parts must have integer values for quantity field!
                if self.quantity != int(self.quantity):
                    raise ValidationError({
                        'quantity': _('Quantity must be integer value for trackable parts')
                    })
        except PartModels.Part.DoesNotExist:
            # For some reason the 'clean' process sometimes throws errors because self.part does not exist
            # It *seems* that this only occurs in unit testing, though.
            # Probably should investigate this at some point.
            pass

        if self.quantity < 0:
            raise ValidationError({
                'quantity': _('Quantity must be greater than zero')
            })

        # The 'supplier_part' field must point to the same part!
        try:
            if self.supplier_part is not None:
                if self.supplier_part.part != self.part:
                    raise ValidationError({'supplier_part': _("Part type ('{pf}') must be {pe}").format(
                                           pf=str(self.supplier_part.part),
                                           pe=str(self.part))
                                           })

            if self.part is not None:
                # A part with a serial number MUST have the quantity set to 1
                if self.serial:
                    if self.quantity > 1:
                        raise ValidationError({
                            'quantity': _('Quantity must be 1 for item with a serial number'),
                            'serial': _('Serial number cannot be set if quantity greater than 1')
                        })

                    if self.quantity == 0:
                        self.quantity = 1

                    elif self.quantity > 1:
                        raise ValidationError({
                            'quantity': _('Quantity must be 1 for item with a serial number')
                        })

                    # Serial numbered items cannot be deleted on depletion
                    self.delete_on_deplete = False

        except PartModels.Part.DoesNotExist:
            # This gets thrown if self.supplier_part is null
            # TODO - Find a test than can be perfomed...
            pass

        # Ensure that the item cannot be assigned to itself
        if self.belongs_to and self.belongs_to.pk == self.pk:
            raise ValidationError({
                'belongs_to': _('Item cannot belong to itself')
            })

        # If the item is marked as "is_building", it must point to a build!
        if self.is_building and not self.build:
            raise ValidationError({
                'build': _("Item must have a build reference if is_building=True")
            })

        # If the item points to a build, check that the Part references match
        if self.build:

            if self.part == self.build.part:
                # Part references match exactly
                pass
            elif self.part in self.build.part.get_conversion_options():
                # Part reference is one of the valid conversion options for the build output
                pass
            else:
                raise ValidationError({
                    'build': _("Build reference does not point to the same part object")
                })

    def get_absolute_url(self):
        """Return url for instance."""
        return reverse('stock-item-detail', kwargs={'pk': self.id})

    def get_part_name(self):
        """Returns part name."""
        return self.part.full_name

    def format_barcode(self, **kwargs):
        """Return a JSON string for formatting a barcode for this StockItem.

        Can be used to perform lookup of a stockitem using barcode.

        Contains the following data:
        `{ type: 'StockItem', stock_id: <pk>, part_id: <part_pk> }`

        Voltagile data (e.g. stock quantity) should be looked up using the InvenTree API (as it may change)
        """
        return InvenTree.helpers.MakeBarcode(
            "stockitem",
            self.id,
            {
                "request": kwargs.get('request', None),
                "item_url": reverse('stock-item-detail', kwargs={'pk': self.id}),
                "url": reverse('api-stock-detail', kwargs={'pk': self.id}),
            },
            **kwargs
        )

    @property
    def barcode(self):
        """Get Brief payload data (e.g. for labels).

        Returns:
            str: Brief pyload data
        """
        return self.format_barcode(brief=True)

    uid = models.CharField(blank=True, max_length=128, help_text=("Unique identifier field"))

    # Note: When a StockItem is deleted, a pre_delete signal handles the parent/child relationship
    parent = TreeForeignKey(
        'self',
        verbose_name=_('Parent Stock Item'),
        on_delete=models.DO_NOTHING,
        blank=True, null=True,
        related_name='children'
    )

    part = models.ForeignKey(
        'part.Part', on_delete=models.CASCADE,
        verbose_name=_('Base Part'),
        related_name='stock_items', help_text=_('Base part'),
        limit_choices_to={
            'virtual': False
        })

    supplier_part = models.ForeignKey(
        'company.SupplierPart', blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_('Supplier Part'),
        help_text=_('Select a matching supplier part for this stock item')
    )

    # Note: When a StockLocation is deleted, stock items are updated via a signal
    location = TreeForeignKey(
        StockLocation, on_delete=models.DO_NOTHING,
        verbose_name=_('Stock Location'),
        related_name='stock_items',
        blank=True, null=True,
        help_text=_('Where is this stock item located?')
    )

    packaging = models.CharField(
        max_length=50,
        blank=True, null=True,
        verbose_name=_('Packaging'),
        help_text=_('Packaging this stock item is stored in')
    )

    # When deleting a stock item with installed items, those installed items are also installed
    belongs_to = models.ForeignKey(
        'self',
        verbose_name=_('Installed In'),
        on_delete=models.CASCADE,
        related_name='installed_parts', blank=True, null=True,
        help_text=_('Is this item installed in another item?')
    )

    customer = models.ForeignKey(
        CompanyModels.Company,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'is_customer': True},
        related_name='assigned_stock',
        help_text=_("Customer"),
        verbose_name=_("Customer"),
    )

    serial = models.CharField(
        verbose_name=_('Serial Number'),
        max_length=100, blank=True, null=True,
        help_text=_('Serial number for this item')
    )

    serial_int = models.IntegerField(default=0)

    link = InvenTreeURLField(
        verbose_name=_('External Link'),
        max_length=125, blank=True,
        help_text=_("Link to external URL")
    )

    batch = models.CharField(
        verbose_name=_('Batch Code'),
        max_length=100, blank=True, null=True,
        help_text=_('Batch code for this stock item'),
        default=generate_batch_code,
    )

    quantity = models.DecimalField(
        verbose_name=_("Stock Quantity"),
        max_digits=15, decimal_places=5, validators=[MinValueValidator(0)],
        default=1
    )

    updated = models.DateField(auto_now=True, null=True)

    build = models.ForeignKey(
        'build.Build', on_delete=models.SET_NULL,
        verbose_name=_('Source Build'),
        blank=True, null=True,
        help_text=_('Build for this stock item'),
        related_name='build_outputs',
    )

    is_building = models.BooleanField(
        default=False,
    )

    purchase_order = models.ForeignKey(
        'order.PurchaseOrder',
        on_delete=models.SET_NULL,
        verbose_name=_('Source Purchase Order'),
        related_name='stock_items',
        blank=True, null=True,
        help_text=_('Purchase order for this stock item')
    )

    sales_order = models.ForeignKey(
        'order.SalesOrder',
        on_delete=models.SET_NULL,
        verbose_name=_("Destination Sales Order"),
        related_name='stock_items',
        null=True, blank=True)

    expiry_date = models.DateField(
        blank=True, null=True,
        verbose_name=_('Expiry Date'),
        help_text=_('Expiry date for stock item. Stock will be considered expired after this date'),
    )

    stocktake_date = models.DateField(blank=True, null=True)

    stocktake_user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='stocktake_stock'
    )

    review_needed = models.BooleanField(default=False)

    delete_on_deplete = models.BooleanField(default=True, verbose_name=_('Delete on deplete'), help_text=_('Delete this Stock Item when stock is depleted'))

    status = models.PositiveIntegerField(
        default=StockStatus.OK,
        choices=StockStatus.items(),
        validators=[MinValueValidator(0)])

    notes = InvenTreeNotesField(help_text=_('Stock Item Notes'))

    purchase_price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name=_('Purchase Price'),
        help_text=_('Single unit purchase price at time of purchase'),
    )

    owner = models.ForeignKey(Owner, on_delete=models.SET_NULL, blank=True, null=True,
                              verbose_name=_('Owner'),
                              help_text=_('Select Owner'),
                              related_name='stock_items')

    @transaction.atomic
    def convert_to_variant(self, variant, user, notes=None):
        """Convert this StockItem instance to a "variant", i.e. change the "part" reference field."""
        if not variant:
            # Ignore null values
            return

        if variant == self.part:
            # Variant is the same as the current part
            return

        self.part = variant
        self.save()

        self.add_tracking_entry(
            StockHistoryCode.CONVERTED_TO_VARIANT,
            user,
            deltas={
                'part': variant.pk,
            },
            notes=_('Converted to part') + ': ' + variant.full_name,
        )

    def get_item_owner(self):
        """Return the closest "owner" for this StockItem.

        - If the item has an owner set, return that
        - If the item is "in stock", check the StockLocation
        - Otherwise, return None
        """
        if self.owner is not None:
            return self.owner

        if self.in_stock and self.location is not None:
            loc_owner = self.location.get_location_owner()

            if loc_owner:
                return loc_owner

        return None

    def check_ownership(self, user):
        """Check if the user "owns" (or is one of the owners of) the item."""
        # Superuser accounts automatically "own" everything
        if user.is_superuser:
            return True

        ownership_enabled = common.models.InvenTreeSetting.get_setting('STOCK_OWNERSHIP_CONTROL')

        if not ownership_enabled:
            # Location ownership function is not enabled, so return True
            return True

        owner = self.get_item_owner()

        if owner is None:
            return True

        return user in owner.get_related_owners(include_group=True)

    def is_stale(self):
        """Returns True if this Stock item is "stale".

        To be "stale", the following conditions must be met:
        - Expiry date is not None
        - Expiry date will "expire" within the configured stale date
        - The StockItem is otherwise "in stock"
        """
        if self.expiry_date is None:
            return False

        if not self.in_stock:
            return False

        today = datetime.now().date()

        stale_days = common.models.InvenTreeSetting.get_setting('STOCK_STALE_DAYS')

        if stale_days <= 0:
            return False

        expiry_date = today + timedelta(days=stale_days)

        return self.expiry_date < expiry_date

    def is_expired(self):
        """Returns True if this StockItem is "expired".

        To be "expired", the following conditions must be met:
        - Expiry date is not None
        - Expiry date is "in the past"
        - The StockItem is otherwise "in stock"
        """
        if self.expiry_date is None:
            return False

        if not self.in_stock:
            return False

        today = datetime.now().date()

        return self.expiry_date < today

    def clearAllocations(self):
        """Clear all order allocations for this StockItem.

        Clears:
        - SalesOrder allocations
        - Build allocations
        """
        # Delete outstanding SalesOrder allocations
        self.sales_order_allocations.all().delete()

        # Delete outstanding BuildOrder allocations
        self.allocations.all().delete()

    def allocateToCustomer(self, customer, quantity=None, order=None, user=None, notes=None):
        """Allocate a StockItem to a customer.

        This action can be called by the following processes:
        - Completion of a SalesOrder
        - User manually assigns a StockItem to the customer

        Args:
            customer: The customer (Company) to assign the stock to
            quantity: Quantity to assign (if not supplied, total quantity is used)
            order: SalesOrder reference
            user: User that performed the action
            notes: Notes field
        """
        if quantity is None:
            quantity = self.quantity

        if quantity >= self.quantity:
            item = self
        else:
            item = self.splitStock(quantity, None, user)

        # Update StockItem fields with new information
        item.sales_order = order
        item.customer = customer
        item.location = None

        item.save()

        # TODO - Remove any stock item allocations from this stock item

        item.add_tracking_entry(
            StockHistoryCode.SENT_TO_CUSTOMER,
            user,
            {
                'customer': customer.id,
                'customer_name': customer.name,
            },
            notes=notes,
        )

        trigger_event(
            'stockitem.assignedtocustomer',
            id=self.id,
            customer=customer.id,
        )

        # Return the reference to the stock item
        return item

    @transaction.atomic
    def return_from_customer(self, location, user=None, **kwargs):
        """Return stock item from customer, back into the specified location."""
        notes = kwargs.get('notes', '')

        tracking_info = {}

        if self.customer:
            tracking_info['customer'] = self.customer.id
            tracking_info['customer_name'] = self.customer.name

        self.add_tracking_entry(
            StockHistoryCode.RETURNED_FROM_CUSTOMER,
            user,
            notes=notes,
            deltas=tracking_info,
            location=location
        )

        self.customer = None
        self.location = location

        trigger_event(
            'stockitem.returnedfromcustomer',
            id=self.id,
        )

        self.save()

    # If stock item is incoming, an (optional) ETA field
    # expected_arrival = models.DateField(null=True, blank=True)

    infinite = models.BooleanField(default=False)

    def is_allocated(self):
        """Return True if this StockItem is allocated to a SalesOrder or a Build."""
        # TODO - For now this only checks if the StockItem is allocated to a SalesOrder
        # TODO - In future, once the "build" is working better, check this too

        if self.allocations.count() > 0:
            return True

        if self.sales_order_allocations.count() > 0:
            return True

        return False

    def build_allocation_count(self):
        """Return the total quantity allocated to builds."""
        query = self.allocations.aggregate(q=Coalesce(Sum('quantity'), Decimal(0)))

        total = query['q']

        if total is None:
            total = Decimal(0)

        return total

    def sales_order_allocation_count(self):
        """Return the total quantity allocated to SalesOrders."""
        query = self.sales_order_allocations.aggregate(q=Coalesce(Sum('quantity'), Decimal(0)))

        total = query['q']

        if total is None:
            total = Decimal(0)

        return total

    def allocation_count(self):
        """Return the total quantity allocated to builds or orders."""
        bo = self.build_allocation_count()
        so = self.sales_order_allocation_count()

        return bo + so

    def unallocated_quantity(self):
        """Return the quantity of this StockItem which is *not* allocated."""
        return max(self.quantity - self.allocation_count(), 0)

    def can_delete(self):
        """Can this stock item be deleted?

        It can NOT be deleted under the following circumstances:
        - Has installed stock items
        - Is installed inside another StockItem
        - It has been assigned to a SalesOrder
        - It has been assigned to a BuildOrder
        """
        if self.installed_item_count() > 0:
            return False

        if self.sales_order is not None:
            return False

        return True

    def get_installed_items(self, cascade: bool = False) -> set[StockItem]:
        """Return all stock items which are *installed* in this one!

        Note: This function is recursive, and may result in a number of database hits!

        Args:
            cascade (bool, optional): Include items which are installed in items which are installed in items. Defaults to False.

        Returns:
            set[StockItem]: Sll stock items which are installed
        """
        installed = set()

        items = StockItem.objects.filter(belongs_to=self)

        for item in items:

            # Prevent duplication or recursion
            if item == self or item in installed:
                continue

            installed.add(item)

            if cascade:
                sub_items = item.get_installed_items(cascade=True)

                for sub_item in sub_items:

                    # Prevent recursion
                    if sub_item == self or sub_item in installed:
                        continue

                    installed.add(sub_item)

        return installed

    def installed_item_count(self):
        """Return the number of stock items installed inside this one."""
        return self.installed_parts.count()

    @transaction.atomic
    def installStockItem(self, other_item, quantity, user, notes):
        """Install another stock item into this stock item.

        Args:
            other_item: The stock item to install into this stock item
            quantity: The quantity of stock to install
            user: The user performing the operation
            notes: Any notes associated with the operation
        """
        # Cannot be already installed in another stock item!
        if self.belongs_to is not None:
            return False

        # If the quantity is less than the stock item, split the stock!
        stock_item = other_item.splitStock(quantity, None, user)

        if stock_item is None:
            stock_item = other_item

        # Assign the other stock item into this one
        stock_item.belongs_to = self
        stock_item.save()

        # Add a transaction note to the other item
        stock_item.add_tracking_entry(
            StockHistoryCode.INSTALLED_INTO_ASSEMBLY,
            user,
            notes=notes,
            deltas={
                'stockitem': self.pk,
            }
        )

        # Add a transaction note to this item (the assembly)
        self.add_tracking_entry(
            StockHistoryCode.INSTALLED_CHILD_ITEM,
            user,
            notes=notes,
            deltas={
                'stockitem': stock_item.pk,
            }
        )

    @transaction.atomic
    def uninstall_into_location(self, location, user, notes):
        """Uninstall this stock item from another item, into a location.

        Args:
            location: The stock location where the item will be moved
            user: The user performing the operation
            notes: Any notes associated with the operation
        """
        # If the stock item is not installed in anything, ignore
        if self.belongs_to is None:
            return False

        # TODO - Are there any other checks that need to be performed at this stage?

        # Add a transaction note to the parent item
        self.belongs_to.add_tracking_entry(
            StockHistoryCode.REMOVED_CHILD_ITEM,
            user,
            deltas={
                'stockitem': self.pk,
            },
            notes=notes,
        )

        tracking_info = {
            'stockitem': self.belongs_to.pk
        }

        self.add_tracking_entry(
            StockHistoryCode.REMOVED_FROM_ASSEMBLY,
            user,
            notes=notes,
            deltas=tracking_info,
            location=location,
        )

        # Mark this stock item as *not* belonging to anyone
        self.belongs_to = None
        self.location = location

        self.save()

    @property
    def children(self):
        """Return a list of the child items which have been split from this stock item."""
        return self.get_descendants(include_self=False)

    @property
    def child_count(self):
        """Return the number of 'child' items associated with this StockItem.

        A child item is one which has been split from this one.
        """
        return self.children.count()

    @property
    def in_stock(self):
        """Returns True if this item is in stock.

        See also: IN_STOCK_FILTER
        """
        query = StockItem.objects.filter(pk=self.pk)

        query = query.filter(StockItem.IN_STOCK_FILTER)

        return query.exists()

    @property
    def can_adjust_location(self):
        """Returns True if the stock location can be "adjusted" for this part.

        Cannot be adjusted if:
        - Has been delivered to a customer
        - Has been installed inside another StockItem
        """
        if self.customer is not None:
            return False

        if self.belongs_to is not None:
            return False

        if self.sales_order is not None:
            return False

        return True

    @property
    def tracking_info_count(self):
        """How many tracking entries are available?"""
        return self.tracking_info.count()

    @property
    def has_tracking_info(self):
        """Is tracking info available?"""
        return self.tracking_info_count > 0

    def add_tracking_entry(self, entry_type: int, user: User, deltas: dict = None, notes: str = '', **kwargs):
        """Add a history tracking entry for this StockItem.

        Args:
            entry_type (int): Code describing the "type" of historical action (see StockHistoryCode)
            user (User): The user performing this action
            deltas (dict, optional): A map of the changes made to the model. Defaults to None.
            notes (str, optional): URL associated with this tracking entry. Defaults to ''.
        """
        if deltas is None:
            deltas = {}

        # Has a location been specified?
        location = kwargs.get('location', None)

        if location:
            deltas['location'] = location.id

        # Quantity specified?
        quantity = kwargs.get('quantity', None)

        if quantity:
            deltas['quantity'] = float(quantity)

        entry = StockItemTracking.objects.create(
            item=self,
            tracking_type=entry_type,
            user=user,
            date=datetime.now(),
            notes=notes,
            deltas=deltas,
        )

        entry.save()

    @transaction.atomic
    def serializeStock(self, quantity, serials, user, notes='', location=None):
        """Split this stock item into unique serial numbers.

        - Quantity can be less than or equal to the quantity of the stock item
        - Number of serial numbers must match the quantity
        - Provided serial numbers must not already be in use

        Args:
            quantity: Number of items to serialize (integer)
            serials: List of serial numbers
            user: User object associated with action
            notes: Optional notes for tracking
            location: If specified, serialized items will be placed in the given location
        """
        # Cannot serialize stock that is already serialized!
        if self.serialized:
            return

        if not self.part.trackable:
            raise ValidationError({"part": _("Part is not set as trackable")})

        # Quantity must be a valid integer value
        try:
            quantity = int(quantity)
        except ValueError:
            raise ValidationError({"quantity": _("Quantity must be integer")})

        if quantity <= 0:
            raise ValidationError({"quantity": _("Quantity must be greater than zero")})

        if quantity > self.quantity:
            raise ValidationError({"quantity": _("Quantity must not exceed available stock quantity ({n})").format(n=self.quantity)})

        if type(serials) not in [list, tuple]:
            raise ValidationError({"serial_numbers": _("Serial numbers must be a list of integers")})

        if quantity != len(serials):
            raise ValidationError({"quantity": _("Quantity does not match serial numbers")})

        # Test if each of the serial numbers are valid
        existing = self.part.find_conflicting_serial_numbers(serials)

        if len(existing) > 0:
            exists = ','.join([str(x) for x in existing])
            raise ValidationError({"serial_numbers": _("Serial numbers already exist: {exists}").format(exists=exists)})

        # Create a new stock item for each unique serial number
        for serial in serials:

            # Create a copy of this StockItem
            new_item = StockItem.objects.get(pk=self.pk)
            new_item.quantity = 1
            new_item.serial = serial
            new_item.pk = None
            new_item.parent = self

            if location:
                new_item.location = location

            # The item already has a transaction history, don't create a new note
            new_item.save(user=user, notes=notes)

            # Copy entire transaction history
            new_item.copyHistoryFrom(self)

            # Copy test result history
            new_item.copyTestResultsFrom(self)

            # Create a new stock tracking item
            new_item.add_tracking_entry(
                StockHistoryCode.ASSIGNED_SERIAL,
                user,
                notes=notes,
                deltas={
                    'serial': serial,
                },
                location=location
            )

        # Remove the equivalent number of items
        self.take_stock(quantity, user, notes=notes)

    @transaction.atomic
    def copyHistoryFrom(self, other):
        """Copy stock history from another StockItem."""
        for item in other.tracking_info.all():

            item.item = self
            item.pk = None
            item.save()

    @transaction.atomic
    def copyTestResultsFrom(self, other, filters=None):
        """Copy all test results from another StockItem."""
        # Set default - see B006
        if filters is None:
            filters = {}

        for result in other.test_results.all().filter(**filters):

            # Create a copy of the test result by nulling-out the pk
            result.pk = None
            result.stock_item = self
            result.save()

    def can_merge(self, other=None, raise_error=False, **kwargs):
        """Check if this stock item can be merged into another stock item."""
        allow_mismatched_suppliers = kwargs.get('allow_mismatched_suppliers', False)

        allow_mismatched_status = kwargs.get('allow_mismatched_status', False)

        try:
            # Generic checks (do not rely on the 'other' part)
            if self.sales_order:
                raise ValidationError(_('Stock item has been assigned to a sales order'))

            if self.belongs_to:
                raise ValidationError(_('Stock item is installed in another item'))

            if self.installed_item_count() > 0:
                raise ValidationError(_('Stock item contains other items'))

            if self.customer:
                raise ValidationError(_('Stock item has been assigned to a customer'))

            if self.is_building:
                raise ValidationError(_('Stock item is currently in production'))

            if self.serialized:
                raise ValidationError(_("Serialized stock cannot be merged"))

            if other:
                # Specific checks (rely on the 'other' part)

                # Prevent stock item being merged with itself
                if self == other:
                    raise ValidationError(_('Duplicate stock items'))

                # Base part must match
                if self.part != other.part:
                    raise ValidationError(_("Stock items must refer to the same part"))

                # Check if supplier part references match
                if self.supplier_part != other.supplier_part and not allow_mismatched_suppliers:
                    raise ValidationError(_("Stock items must refer to the same supplier part"))

                # Check if stock status codes match
                if self.status != other.status and not allow_mismatched_status:
                    raise ValidationError(_("Stock status codes must match"))

        except ValidationError as e:
            if raise_error:
                raise e
            else:
                return False

        return True

    @transaction.atomic
    def merge_stock_items(self, other_items, raise_error=False, **kwargs):
        """Merge another stock item into this one; the two become one!

        *This* stock item subsumes the other, which is essentially deleted:

        - The quantity of this StockItem is increased
        - Tracking history for the *other* item is deleted
        - Any allocations (build order, sales order) are moved to this StockItem
        """
        if len(other_items) == 0:
            return

        user = kwargs.get('user', None)
        location = kwargs.get('location', None)
        notes = kwargs.get('notes', None)

        parent_id = self.parent.pk if self.parent else None

        for other in other_items:
            # If the stock item cannot be merged, return
            if not self.can_merge(other, raise_error=raise_error, **kwargs):
                return

        for other in other_items:

            self.quantity += other.quantity

            # Any "build order allocations" for the other item must be assigned to this one
            for allocation in other.allocations.all():

                allocation.stock_item = self
                allocation.save()

            # Any "sales order allocations" for the other item must be assigned to this one
            for allocation in other.sales_order_allocations.all():

                allocation.stock_item = self()
                allocation.save()

            # Prevent atomicity issues when we are merging our own "parent" part in
            if parent_id and parent_id == other.pk:
                self.parent = None
                self.save()

            other.delete()

        self.add_tracking_entry(
            StockHistoryCode.MERGED_STOCK_ITEMS,
            user,
            quantity=self.quantity,
            notes=notes,
            deltas={
                'location': location.pk,
            }
        )

        self.location = location
        self.save()

    @transaction.atomic
    def splitStock(self, quantity, location, user, **kwargs):
        """Split this stock item into two items, in the same location.

        Stock tracking notes for this StockItem will be duplicated,
        and added to the new StockItem.

        Args:
            quantity: Number of stock items to remove from this entity, and pass to the next
            location: Where to move the new StockItem to

        Notes:
            The provided quantity will be subtracted from this item and given to the new one.
            The new item will have a different StockItem ID, while this will remain the same.
        """
        notes = kwargs.get('notes', '')
        code = kwargs.get('code', StockHistoryCode.SPLIT_FROM_PARENT)

        # Do not split a serialized part
        if self.serialized:
            return self

        try:
            quantity = Decimal(quantity)
        except (InvalidOperation, ValueError):
            return self

        # Doesn't make sense for a zero quantity
        if quantity <= 0:
            return self

        # Also doesn't make sense to split the full amount
        if quantity >= self.quantity:
            return self

        # Create a new StockItem object, duplicating relevant fields
        # Nullify the PK so a new record is created
        new_stock = StockItem.objects.get(pk=self.pk)
        new_stock.pk = None
        new_stock.parent = self
        new_stock.quantity = quantity

        # Move to the new location if specified, otherwise use current location
        if location:
            new_stock.location = location
        else:
            new_stock.location = self.location

        new_stock.save()

        # Copy the transaction history of this part into the new one
        new_stock.copyHistoryFrom(self)

        # Copy the test results of this part to the new one
        new_stock.copyTestResultsFrom(self)

        # Add a new tracking item for the new stock item
        new_stock.add_tracking_entry(
            code,
            user,
            notes=notes,
            deltas={
                'stockitem': self.pk,
            },
            location=location,
        )

        # Remove the specified quantity from THIS stock item
        self.take_stock(
            quantity,
            user,
            notes=notes
        )

        # Return a copy of the "new" stock item
        return new_stock

    @transaction.atomic
    def move(self, location, notes, user, **kwargs):
        """Move part to a new location.

        If less than the available quantity is to be moved,
        a new StockItem is created, with the defined quantity,
        and that new StockItem is moved.
        The quantity is also subtracted from the existing StockItem.

        Args:
            location: Destination location (cannot be null)
            notes: User notes
            user: Who is performing the move
            kwargs:
                quantity: If provided, override the quantity (default = total stock quantity)
        """
        try:
            quantity = Decimal(kwargs.get('quantity', self.quantity))
        except InvalidOperation:
            return False

        if not self.in_stock:
            raise ValidationError(_("StockItem cannot be moved as it is not in stock"))

        if quantity <= 0:
            return False

        if location is None:
            # TODO - Raise appropriate error (cannot move to blank location)
            return False
        elif self.location and (location.pk == self.location.pk) and (quantity == self.quantity):
            # TODO - Raise appropriate error (cannot move to same location)
            return False

        # Test for a partial movement
        if quantity < self.quantity:
            # We need to split the stock!

            # Split the existing StockItem in two
            self.splitStock(quantity, location, user, **{'notes': notes})

            return True

        self.location = location

        tracking_info = {}

        self.add_tracking_entry(
            StockHistoryCode.STOCK_MOVE,
            user,
            notes=notes,
            deltas=tracking_info,
            location=location,
        )

        self.save()

        return True

    @transaction.atomic
    def updateQuantity(self, quantity):
        """Update stock quantity for this item.

        If the quantity has reached zero, this StockItem will be deleted.

        Returns:
            - True if the quantity was saved
            - False if the StockItem was deleted
        """
        # Do not adjust quantity of a serialized part
        if self.serialized:
            return

        try:
            self.quantity = Decimal(quantity)
        except (InvalidOperation, ValueError):
            return

        if quantity < 0:
            quantity = 0

        self.quantity = quantity

        if quantity == 0 and self.delete_on_deplete and self.can_delete():
            self.delete()

            return False
        else:
            self.save()
            return True

    @transaction.atomic
    def stocktake(self, count, user, notes=''):
        """Perform item stocktake.

        When the quantity of an item is counted,
        record the date of stocktake
        """
        try:
            count = Decimal(count)
        except InvalidOperation:
            return False

        if count < 0 or self.infinite:
            return False

        self.stocktake_date = datetime.now().date()
        self.stocktake_user = user

        if self.updateQuantity(count):

            self.add_tracking_entry(
                StockHistoryCode.STOCK_COUNT,
                user,
                notes=notes,
                deltas={
                    'quantity': float(self.quantity),
                }
            )

        return True

    @transaction.atomic
    def add_stock(self, quantity, user, notes=''):
        """Add items to stock.

        This function can be called by initiating a ProjectRun,
        or by manually adding the items to the stock location
        """
        # Cannot add items to a serialized part
        if self.serialized:
            return False

        try:
            quantity = Decimal(quantity)
        except InvalidOperation:
            return False

        # Ignore amounts that do not make sense
        if quantity <= 0 or self.infinite:
            return False

        if self.updateQuantity(self.quantity + quantity):

            self.add_tracking_entry(
                StockHistoryCode.STOCK_ADD,
                user,
                notes=notes,
                deltas={
                    'added': float(quantity),
                    'quantity': float(self.quantity),
                }
            )

        return True

    @transaction.atomic
    def take_stock(self, quantity, user, notes='', code=StockHistoryCode.STOCK_REMOVE):
        """Remove items from stock."""
        # Cannot remove items from a serialized part
        if self.serialized:
            return False

        try:
            quantity = Decimal(quantity)
        except InvalidOperation:
            return False

        if quantity <= 0 or self.infinite:
            return False

        if self.updateQuantity(self.quantity - quantity):

            self.add_tracking_entry(
                code,
                user,
                notes=notes,
                deltas={
                    'removed': float(quantity),
                    'quantity': float(self.quantity),
                }
            )

        return True

    def __str__(self):
        """Human friendly name."""
        if self.part.trackable and self.serial:
            s = '{part} #{sn}'.format(
                part=self.part.full_name,
                sn=self.serial)
        else:
            s = '{n} x {part}'.format(
                n=InvenTree.helpers.decimal2string(self.quantity),
                part=self.part.full_name)

        if self.location:
            s += ' @ {loc}'.format(loc=self.location.name)

        if self.purchase_order:
            s += " ({pre}{po})".format(
                pre=InvenTree.helpers.getSetting("PURCHASEORDER_REFERENCE_PREFIX"),
                po=self.purchase_order,
            )

        return s

    @transaction.atomic
    def clear_test_results(self, **kwargs):
        """Remove all test results."""
        # All test results
        results = self.test_results.all()

        # TODO - Perhaps some filtering options supplied by kwargs?

        results.delete()

    def getTestResults(self, test=None, result=None, user=None):
        """Return all test results associated with this StockItem.

        Optionally can filter results by:
        - Test name
        - Test result
        - User
        """
        results = self.test_results

        if test:
            # Filter by test name
            results = results.filter(test=test)

        if result is not None:
            # Filter by test status
            results = results.filter(result=result)

        if user:
            # Filter by user
            results = results.filter(user=user)

        return results

    def testResultMap(self, **kwargs):
        """Return a map of test-results using the test name as the key.

        Where multiple test results exist for a given name,
        the *most recent* test is used.

        This map is useful for rendering to a template (e.g. a test report),
        as all named tests are accessible.
        """
        # Do we wish to include test results from installed items?
        include_installed = kwargs.pop('include_installed', False)

        # Filter results by "date", so that newer results
        # will override older ones.
        results = self.getTestResults(**kwargs).order_by('date')

        result_map = {}

        for result in results:
            key = InvenTree.helpers.generateTestKey(result.test)
            result_map[key] = result

        # Do we wish to "cascade" and include test results from installed stock items?
        cascade = kwargs.get('cascade', False)

        if include_installed:
            installed_items = self.get_installed_items(cascade=cascade)

            for item in installed_items:
                item_results = item.testResultMap()

                for key in item_results.keys():
                    # Results from sub items should not override master ones
                    if key not in result_map.keys():
                        result_map[key] = item_results[key]

        return result_map

    def testResultList(self, **kwargs):
        """Return a list of test-result objects for this StockItem."""
        return self.testResultMap(**kwargs).values()

    def requiredTestStatus(self):
        """Return the status of the tests required for this StockItem.

        Return:
            A dict containing the following items:
            - total: Number of required tests
            - passed: Number of tests that have passed
            - failed: Number of tests that have failed
        """
        # All the tests required by the part object
        required = self.part.getRequiredTests()

        results = self.testResultMap()

        total = len(required)
        passed = 0
        failed = 0

        for test in required:
            key = InvenTree.helpers.generateTestKey(test.test_name)

            if key in results:
                result = results[key]

                if result.result:
                    passed += 1
                else:
                    failed += 1

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
        }

    @property
    def required_test_count(self):
        """Return the number of 'required tests' for this StockItem."""
        return self.part.getRequiredTests().count()

    def hasRequiredTests(self):
        """Return True if there are any 'required tests' associated with this StockItem."""
        return self.part.getRequiredTests().count() > 0

    def passedAllRequiredTests(self):
        """Returns True if this StockItem has passed all required tests."""
        status = self.requiredTestStatus()

        return status['passed'] >= status['total']

    def available_test_reports(self):
        """Return a list of TestReport objects which match this StockItem."""
        reports = []

        item_query = StockItem.objects.filter(pk=self.pk)

        for test_report in report.models.TestReport.objects.filter(enabled=True):

            # Attempt to validate report filter (skip if invalid)
            try:
                filters = InvenTree.helpers.validateFilterString(test_report.filters)
                if item_query.filter(**filters).exists():
                    reports.append(test_report)
            except (ValidationError, FieldError):
                continue

        return reports

    @property
    def has_test_reports(self):
        """Return True if there are test reports available for this stock item."""
        return len(self.available_test_reports()) > 0

    def available_labels(self):
        """Return a list of Label objects which match this StockItem."""
        labels = []

        item_query = StockItem.objects.filter(pk=self.pk)

        for lbl in label.models.StockItemLabel.objects.filter(enabled=True):

            try:
                filters = InvenTree.helpers.validateFilterString(lbl.filters)

                if item_query.filter(**filters).exists():
                    labels.append(lbl)
            except (ValidationError, FieldError):
                continue

        return labels

    @property
    def has_labels(self):
        """Return True if there are any label templates available for this stock item."""
        return len(self.available_labels()) > 0


@receiver(pre_delete, sender=StockItem, dispatch_uid='stock_item_pre_delete_log')
def before_delete_stock_item(sender, instance, using, **kwargs):
    """Receives pre_delete signal from StockItem object.

    Before a StockItem is deleted, ensure that each child object is updated,
    to point to the new parent item.
    """
    # Update each StockItem parent field
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()


@receiver(post_delete, sender=StockItem, dispatch_uid='stock_item_post_delete_log')
def after_delete_stock_item(sender, instance: StockItem, **kwargs):
    """Function to be executed after a StockItem object is deleted."""
    from part import tasks as part_tasks

    if not InvenTree.ready.isImportingData():
        # Run this check in the background
        InvenTree.tasks.offload_task(part_tasks.notify_low_stock_if_required, instance.part)


@receiver(post_save, sender=StockItem, dispatch_uid='stock_item_post_save_log')
def after_save_stock_item(sender, instance: StockItem, created, **kwargs):
    """Hook function to be executed after StockItem object is saved/updated."""
    from part import tasks as part_tasks

    if not InvenTree.ready.isImportingData():
        # Run this check in the background
        InvenTree.tasks.offload_task(part_tasks.notify_low_stock_if_required, instance.part)


class StockItemAttachment(InvenTreeAttachment):
    """Model for storing file attachments against a StockItem object."""

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-stock-attachment-list')

    def getSubdir(self):
        """Override attachment location."""
        return os.path.join("stock_files", str(self.stock_item.id))

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='attachments'
    )


class StockItemTracking(models.Model):
    """Stock tracking entry - used for tracking history of a particular StockItem.

    Note: 2021-05-11
    The legacy StockTrackingItem model contained very litle information about the "history" of the item.
    In fact, only the "quantity" of the item was recorded at each interaction.
    Also, the "title" was translated at time of generation, and thus was not really translateable.
    The "new" system tracks all 'delta' changes to the model,
    and tracks change "type" which can then later be translated


    Attributes:
        item: ForeignKey reference to a particular StockItem
        date: Date that this tracking info was created
        tracking_type: The type of tracking information
        notes: Associated notes (input by user)
        user: The user associated with this tracking info
        deltas: The changes associated with this history item
    """

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-stock-tracking-list')

    def get_absolute_url(self):
        """Return url for instance."""
        return '/stock/track/{pk}'.format(pk=self.id)

    def label(self):
        """Return label."""
        if self.tracking_type in StockHistoryCode.keys():
            return StockHistoryCode.label(self.tracking_type)
        else:
            return self.title

    tracking_type = models.IntegerField(
        default=StockHistoryCode.LEGACY,
    )

    item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='tracking_info'
    )

    date = models.DateTimeField(auto_now_add=True, editable=False)

    notes = models.CharField(
        blank=True, null=True,
        max_length=512,
        verbose_name=_('Notes'),
        help_text=_('Entry notes')
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    deltas = models.JSONField(null=True, blank=True)


def rename_stock_item_test_result_attachment(instance, filename):
    """Rename test result."""
    return os.path.join('stock_files', str(instance.stock_item.pk), os.path.basename(filename))


class StockItemTestResult(models.Model):
    """A StockItemTestResult records results of custom tests against individual StockItem objects.

    This is useful for tracking unit acceptance tests, and particularly useful when integrated
    with automated testing setups.

    Multiple results can be recorded against any given test, allowing tests to be run many times.

    Attributes:
        stock_item: Link to StockItem
        test: Test name (simple string matching)
        result: Test result value (pass / fail / etc)
        value: Recorded test output value (optional)
        attachment: Link to StockItem attachment (optional)
        notes: Extra user notes related to the test (optional)
        user: User who uploaded the test result
        date: Date the test result was recorded
    """

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-stock-test-result-list')

    def save(self, *args, **kwargs):
        """Validate result is unique before saving."""
        super().clean()
        super().validate_unique()
        super().save(*args, **kwargs)

    def clean(self):
        """Make sure all values - including for templates - are provided."""
        super().clean()

        # If this test result corresponds to a template, check the requirements of the template
        key = self.key

        templates = self.stock_item.part.getTestTemplates()

        for template in templates:
            if key == template.key:

                if template.requires_value:
                    if not self.value:
                        raise ValidationError({
                            "value": _("Value must be provided for this test"),
                        })

                if template.requires_attachment:
                    if not self.attachment:
                        raise ValidationError({
                            "attachment": _("Attachment must be uploaded for this test"),
                        })

                break

    @property
    def key(self):
        """Return key for test."""
        return InvenTree.helpers.generateTestKey(self.test)

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='test_results'
    )

    test = models.CharField(
        blank=False, max_length=100,
        verbose_name=_('Test'),
        help_text=_('Test name')
    )

    result = models.BooleanField(
        default=False,
        verbose_name=_('Result'),
        help_text=_('Test result')
    )

    value = models.CharField(
        blank=True, max_length=500,
        verbose_name=_('Value'),
        help_text=_('Test output value')
    )

    attachment = models.FileField(
        null=True, blank=True,
        upload_to=rename_stock_item_test_result_attachment,
        verbose_name=_('Attachment'),
        help_text=_('Test result attachment'),
    )

    notes = models.CharField(
        blank=True, max_length=500,
        verbose_name=_('Notes'),
        help_text=_("Test notes"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True
    )

    date = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )
