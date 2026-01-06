"""Stock database model definitions."""

from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError, OperationalError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from djmoney.contrib.exchange.models import convert_money
from mptt.managers import TreeManager
from mptt.models import TreeForeignKey
from taggit.managers import TaggableManager

import build.models
import common.models
import InvenTree.exceptions
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import order.models
import report.mixins
import stock.tasks
from common.icons import validate_icon
from common.settings import get_global_setting
from company import models as CompanyModels
from generic.states import StatusCodeMixin
from generic.states.fields import InvenTreeCustomStatusModelField
from InvenTree.fields import InvenTreeModelMoneyField, InvenTreeURLField
from InvenTree.status_codes import (
    SalesOrderStatusGroups,
    StockHistoryCode,
    StockStatus,
    StockStatusGroups,
)
from part import models as PartModels
from plugin.events import trigger_event
from stock.events import StockEvents
from stock.generators import generate_batch_code
from users.models import Owner

logger = structlog.get_logger('inventree')


class StockLocationType(InvenTree.models.MetadataMixin, models.Model):
    """A type of stock location like Warehouse, room, shelf, drawer.

    Attributes:
        name: brief name
        description: longer form description
        icon: icon class
    """

    class Meta:
        """Metaclass defines extra model properties."""

        verbose_name = _('Stock Location type')
        verbose_name_plural = _('Stock Location types')

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-location-type-list')

    def __str__(self):
        """String representation of a StockLocationType."""
        return self.name

    name = models.CharField(
        blank=False, max_length=100, verbose_name=_('Name'), help_text=_('Name')
    )

    description = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Description (optional)'),
    )

    icon = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Icon'),
        help_text=_('Default icon for all locations that have no icon set (optional)'),
        validators=[validate_icon],
    )


class StockLocationReportContext(report.mixins.BaseReportContext):
    """Report context for the StockLocation model.

    Attributes:
        location: The StockLocation object itself
        qr_data: Formatted QR code data for the StockLocation
        parent: The parent StockLocation object
        stock_location: The StockLocation object itself (shadow of 'location')
        stock_items: Query set of all StockItem objects which are located in the StockLocation
    """

    location: StockLocation
    qr_data: str
    parent: StockLocation | None
    stock_location: StockLocation
    stock_items: report.mixins.QuerySet[StockItem]


class StockLocation(
    InvenTree.models.PluginValidationMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    report.mixins.InvenTreeReportMixin,
    InvenTree.models.PathStringMixin,
    InvenTree.models.MetadataMixin,
    InvenTree.models.InvenTreeTree,
):
    """Organization tree for StockItem objects.

    A "StockLocation" can be considered a warehouse, or storage location
    Stock locations can be hierarchical as required
    """

    ITEM_PARENT_KEY = 'location'

    EXTRA_PATH_FIELDS = ['icon']

    objects = TreeManager()

    class Meta:
        """Metaclass defines extra model properties."""

        verbose_name = _('Stock Location')
        verbose_name_plural = _('Stock Locations')

    tags = TaggableManager(blank=True)

    def delete(self, *args, **kwargs):
        """Custom model deletion routine, which updates any child locations or items.

        This must be handled within a transaction.atomic(), otherwise the tree structure is damaged
        """
        super().delete(
            delete_children=kwargs.get('delete_sub_locations', False),
            delete_items=kwargs.get('delete_stock_items', False),
        )

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-location-list')

    @classmethod
    def barcode_model_type_code(cls):
        """Return the associated barcode model type code for this model."""
        return 'SL'

    def report_context(self) -> StockLocationReportContext:
        """Return report context data for this StockLocation."""
        return {
            'location': self,
            'qr_data': self.barcode,
            'parent': self.parent,
            'stock_location': self,
            'stock_items': self.get_stock_items(),
        }

    custom_icon = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        verbose_name=_('Icon'),
        help_text=_('Icon (optional)'),
        db_column='icon',
        validators=[validate_icon],
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Owner'),
        help_text=_('Select Owner'),
        related_name='stock_locations',
    )

    structural = models.BooleanField(
        default=False,
        verbose_name=_('Structural'),
        help_text=_(
            'Stock items may not be directly located into a structural stock locations, '
            'but may be located to child locations.'
        ),
    )

    external = models.BooleanField(
        default=False,
        verbose_name=_('External'),
        help_text=_('This is an external stock location'),
    )

    location_type = models.ForeignKey(
        StockLocationType,
        on_delete=models.SET_NULL,
        verbose_name=_('Location type'),
        related_name='stock_locations',
        null=True,
        blank=True,
        help_text=_('Stock location type of this location'),
    )

    @property
    def icon(self) -> str:
        """Get the current icon used for this location.

        The icon field on this model takes precedences over the possibly assigned stock location type
        """
        if self.custom_icon:
            return self.custom_icon

        if self.location_type:
            return self.location_type.icon

        if default_icon := get_global_setting(
            'STOCK_LOCATION_DEFAULT_ICON', cache=True
        ):
            return default_icon

        return ''

    @icon.setter
    def icon(self, value):
        """Setter to keep model API compatibility.

        But be careful:
        If the field gets loaded as default value by any form which is later saved,
        the location no longer inherits its icon from the location type.
        """
        self.custom_icon = value

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

        ownership_enabled = get_global_setting('STOCK_OWNERSHIP_CONTROL')

        if not ownership_enabled:
            # Location ownership function is not enabled, so return True
            return True

        owner = self.get_location_owner()

        if owner is None:
            # No owner set, for this location or any location above
            # So, no ownership checks to perform!
            return True

        return owner.is_user_allowed(user, include_group=True)

    def clean(self):
        """Custom clean action for the StockLocation model.

        Ensure stock location can't be made structural if stock items already located to them
        """
        if self.pk and self.structural and self.stock_item_count(False) > 0:
            raise ValidationError(
                _(
                    'You cannot make this stock location structural because some stock items '
                    'are already located into it!'
                )
            )
        super().clean()

    def get_absolute_url(self):
        """Return url for instance."""
        return InvenTree.helpers.pui_url(f'/stock/location/{self.id}')

    def get_stock_items(self, cascade=True):
        """Return a queryset for all stock items under this category.

        Args:
            cascade: If True, also look under sublocations (default = True)
        """
        if cascade:
            query = StockItem.objects.filter(
                location__in=self.getUniqueChildren(include_self=True)
            )
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

    def get_items(self, cascade=False):
        """Return a queryset for all stock items under this category."""
        return self.get_stock_items(cascade=cascade)


def default_delete_on_deplete():
    """Return a default value for the 'delete_on_deplete' field.

    Prior to 2022-12-24, this field was set to True by default.
    Now, there is a user-configurable setting to govern default behavior.
    """
    try:
        return get_global_setting('STOCK_DELETE_DEPLETED_DEFAULT', True)
    except (IntegrityError, OperationalError):
        # Revert to original default behavior
        return True


class StockItemReportContext(report.mixins.BaseReportContext):
    """Report context for the StockItem model.

    Attributes:
        barcode_data: Generated barcode data for the StockItem
        barcode_hash: Hash of the barcode data
        batch: The batch code for the StockItem
        child_items: Query set of all StockItem objects which are children of this StockItem
        ipn: The IPN (internal part number) of the associated Part
        installed_items: Query set of all StockItem objects which are installed in this StockItem
        item: The StockItem object itself
        name: The name of the associated Part
        part: The Part object which is associated with the StockItem
        qr_data: Generated QR code data for the StockItem
        qr_url: Generated URL for embedding in a QR code
        parameters: Dict object containing the parameters associated with the base Part
        quantity: The quantity of the StockItem
        result_list: FLattened list of TestResult data associated with the stock item
        results: Dict object of TestResult data associated with the StockItem
        serial: The serial number of the StockItem
        stock_item: The StockItem object itself (shadow of 'item')
        tests: Dict object of TestResult data associated with the StockItem (shadow of 'results')
        test_keys: List of test keys associated with the StockItem
        test_template_list: List of test templates associated with the StockItem
        test_templates: Dict object of test templates associated with the StockItem
    """

    barcode_data: str
    barcode_hash: str
    batch: str
    child_items: report.mixins.QuerySet[StockItem]
    ipn: str | None
    installed_items: set[StockItem]
    item: StockItem
    name: str
    part: PartModels.Part
    qr_data: str
    qr_url: str
    parameters: dict[str, str]
    quantity: Decimal
    result_list: list[StockItemTestResult]
    results: dict[str, StockItemTestResult]
    serial: str | None
    stock_item: StockItem
    tests: dict[str, StockItemTestResult]
    test_keys: list[str]
    test_template_list: report.mixins.QuerySet[PartModels.PartTestTemplate]
    test_templates: dict[str, PartModels.PartTestTemplate]


class StockItem(
    InvenTree.models.PluginValidationMixin,
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    InvenTree.models.InvenTreeNotesMixin,
    StatusCodeMixin,
    report.mixins.InvenTreeReportMixin,
    common.models.MetaMixin,
    InvenTree.models.MetadataMixin,
    InvenTree.models.InvenTreeTree,
):
    """A StockItem object represents a quantity of physical instances of a part.

    Attributes:
        parent: Link to another StockItem from which this StockItem was created
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
        status: Status of this StockItem (ref: stock.status_codes.StockStatus)
        notes: Extra notes field
        build: Link to a Build (if this stock item was created from a build)
        is_building: Boolean field indicating if this stock item is currently being built (or is "in production")
        purchase_order: Link to a PurchaseOrder (if this stock item was created from a PurchaseOrder)
        sales_order: Link to a SalesOrder object (if the StockItem has been assigned to a SalesOrder)
        purchase_price: The unit purchase price for this StockItem - this is the unit price at time of purchase (if this item was purchased from an external supplier)
        packaging: Description of how the StockItem is packaged (e.g. "reel", "loose", "tape" etc)
    """

    STATUS_CLASS = StockStatus

    class Meta:
        """Model meta options."""

        verbose_name = _('Stock Item')

    class MPTTMeta:
        """MPTT metaclass options."""

        order_insertion_by = ['part']

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-stock-list')

    def api_instance_filters(self):
        """Custom API instance filters."""
        return {'parent': {'exclude_tree': self.pk}}

    @classmethod
    def barcode_model_type_code(cls):
        """Return the associated barcode model type code for this model."""
        return 'SI'

    def get_test_keys(self, include_installed=True):
        """Construct a flattened list of test 'keys' for this StockItem."""
        keys = []

        for test in self.part.getTestTemplates(required=True):
            if test.key not in keys:
                keys.append(test.key)

        for test in self.part.getTestTemplates(required=False):
            if test.key not in keys:
                keys.append(test.key)

        for result in self.testResultList(include_installed=include_installed):
            if result.key not in keys:
                keys.append(result.key)

        return list(keys)

    def report_context(self) -> StockItemReportContext:
        """Generate custom report context data for this StockItem."""
        return {
            'barcode_data': self.barcode_data,
            'barcode_hash': self.barcode_hash,
            'batch': self.batch,
            'child_items': self.get_children(),
            'ipn': self.part.IPN,
            'installed_items': self.get_installed_items(cascade=True),
            'item': self,
            'name': self.part.full_name,
            'part': self.part,
            'qr_data': self.barcode,
            'qr_url': self.get_absolute_url(),
            'parameters': self.part.parameters_map(),
            'quantity': InvenTree.helpers.normalize(self.quantity),
            'result_list': self.testResultList(include_installed=True),
            'results': self.testResultMap(include_installed=True, cascade=True),
            'serial': self.serial,
            'stock_item': self,
            'tests': self.testResultMap(),
            'test_keys': self.get_test_keys(),
            'test_template_list': self.part.getTestTemplates(),
            'test_templates': self.part.getTestTemplateMap(),
        }

    tags = TaggableManager(blank=True)

    # A Query filter which will be reused in multiple places to determine if a StockItem is actually "in stock"
    # See also: StockItem.in_stock() method
    IN_STOCK_FILTER = Q(
        quantity__gt=0,
        sales_order=None,
        belongs_to=None,
        customer=None,
        consumed_by=None,
        is_building=False,
        status__in=StockStatusGroups.AVAILABLE_CODES,
    )

    # A query filter which can be used to filter StockItem objects which have expired
    EXPIRED_FILTER = (
        IN_STOCK_FILTER
        & ~Q(expiry_date=None)
        & Q(expiry_date__lt=InvenTree.helpers.current_date())
    )

    @classmethod
    def _create_serial_numbers(cls, serials: list, **kwargs) -> QuerySet:
        """Create multiple stock items with the provided serial numbers.

        Arguments:
            serials: List of serial numbers to create
            **kwargs: Additional keyword arguments to pass to the StockItem creation function

        Returns:
            QuerySet: The created StockItem objects

        Raises:
            ValidationError: If any of the provided serial numbers are invalid

        This method uses bulk_create to create multiple StockItem objects in a single query,
        which is much more efficient than creating them one-by-one.

        However, it does not perform any validation checks on the provided serial numbers,
        and also does not generate any "stock tracking entries".

        Note: This is an 'internal' function and should not be used by external code / plugins.
        """
        # Ensure the primary-key field is not provided
        kwargs.pop('id', None)
        kwargs.pop('pk', None)

        # Create a list of StockItem objects
        items = []

        # Provide some default field values
        data = {**kwargs}

        # Extract foreign-key fields from the provided data
        fk_relations = {
            'parent': StockItem,
            'part': PartModels.Part,
            'build': build.models.Build,
            'purchase_order': order.models.PurchaseOrder,
            'supplier_part': CompanyModels.SupplierPart,
            'location': StockLocation,
            'belongs_to': StockItem,
            'customer': CompanyModels.Company,
            'consumed_by': build.models.Build,
            'sales_order': order.models.SalesOrder,
        }

        for field, model in fk_relations.items():
            if instance_id := data.pop(f'{field}_id', None):
                try:
                    instance = model.objects.get(pk=instance_id)
                    data[field] = instance
                except (ValueError, model.DoesNotExist):
                    raise ValidationError({field: _(f'{field} does not exist')})

        # Remove some fields which we do not want copied across
        for field in [
            'barcode_data',
            'barcode_hash',
            'stocktake_date',
            'stocktake_user',
            'stocktake_user_id',
        ]:
            data.pop(field, None)

        if 'part' not in data:
            raise ValidationError({'part': _('Part must be specified')})

        part = data['part']

        parent = kwargs.pop('parent', None) or data.get('parent')
        tree_id = kwargs.pop('tree_id', StockItem.getNextTreeID())

        if parent:
            # Override with parent's tree_id if provided
            tree_id = parent.tree_id

        # Pre-calculate MPTT fields
        data['parent'] = parent if parent else None
        data['level'] = parent.level + 1 if parent else 0
        data['lft'] = 0 if parent else 1
        data['rght'] = 0 if parent else 2

        # Force single quantity for each item
        data['quantity'] = 1

        for serial in serials:
            data['serial'] = serial

            if serial is not None:
                data['serial_int'] = StockItem.convert_serial_to_int(serial) or 0
            else:
                data['serial_int'] = 0

            data['tree_id'] = tree_id

            if not parent:
                # No parent, this is a top-level item, so increment the tree_id
                # This is because each new item is a "top-level" node in the StockItem tree
                tree_id += 1

            # Construct a new StockItem from the provided dict
            items.append(StockItem(**data))

        # Create the StockItem objects in bulk
        StockItem.objects.bulk_create(items)

        # We will need to rebuild the stock item tree manually, due to the bulk_create operation
        if parent and parent.tree_id:
            # Rebuild the tree structure for this StockItem tree
            logger.info(
                'Rebuilding StockItem tree structure for tree_id: %s', parent.tree_id
            )
            stock.tasks.rebuild_stock_item_tree(parent.tree_id)

        # Fetch the new StockItem objects from the database
        items = StockItem.objects.filter(part=part, serial__in=serials)

        # Trigger a 'created' event for the new items
        # Note that instead of a single event for each item,
        # we trigger a single event for all items created
        stock_ids = list(items.values_list('id', flat=True).distinct())
        trigger_event(StockEvents.ITEMS_CREATED, ids=stock_ids)

        # Return the newly created StockItem objects
        return items

    @staticmethod
    def convert_serial_to_int(serial: str) -> int | None:
        """Convert the provided serial number to an integer value.

        This function hooks into the plugin system to allow for custom serial number conversion.
        """
        from plugin import PluginMixinEnum, registry

        # First, let any plugins convert this serial number to an integer value
        # If a non-null value is returned (by any plugin) we will use that

        for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
            try:
                serial_int = plugin.convert_serial_to_int(serial)
            except Exception:
                InvenTree.exceptions.log_error(
                    'convert_serial_to_int', plugin=plugin.slug
                )
                serial_int = None

            # Save the first returned result
            if serial_int is not None:
                # Ensure that it is clipped within a range allowed in the database schema
                clip = 0x7FFFFFFF
                serial_int = abs(serial_int)
                serial_int = min(serial_int, clip)
                # Return the first non-null value
                return serial_int

        # None of the plugins provided a valid integer value
        if serial not in [None, '']:
            return InvenTree.helpers.extract_int(serial)
        else:
            return None

    def update_serial_number(self):
        """Update the 'serial_int' field, to be an integer representation of the serial number.

        This is used for efficient numerical sorting
        """
        serial = str(getattr(self, 'serial', '')).strip()

        if not serial:
            self.serial_int = 0
            return

        serial_int = self.convert_serial_to_int(serial)

        try:
            serial_int = int(serial_int)

            if serial_int <= 0:
                serial_int = 0
        except (ValueError, TypeError):
            serial_int = 0

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

    @property
    def get_next_stock_item(self):
        """Return the 'next' stock item (based on serial number)."""
        return self.get_next_serialized_item()

    @property
    def get_previous_stock_item(self):
        """Return the 'previous' stock item (based on serial number)."""
        return self.get_next_serialized_item(reverse=True)

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

                if add_note and len(deltas) > 0:
                    self.add_tracking_entry(
                        StockHistoryCode.EDITED, user, deltas=deltas, notes=notes
                    )

            except (ValueError, StockItem.DoesNotExist):
                pass

        super().save(*args, **kwargs)

        # If user information is provided, and no existing note exists, create one!
        if add_note and self.tracking_info.count() == 0:
            tracking_info = {'status': self.status}

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
        return (
            self.serial is not None
            and len(str(self.serial).strip()) > 0
            and self.quantity == 1
        )

    def validate_unique(self, exclude=None):
        """Test that this StockItem is "unique".

        If the StockItem is serialized, the same serial number.
        cannot exist for the same part (or part tree).
        """
        super().validate_unique(exclude)

        # If the serial number is set, make sure it is not a duplicate
        if self.serial:
            self.serial = str(self.serial).strip()

            try:
                self.part.validate_serial_number(self.serial, self, raise_error=True)
            except ValidationError as exc:
                raise ValidationError({'serial': exc.message})

    def validate_batch_code(self):
        """Ensure that the batch code is valid for this StockItem.

        - Validation is performed by custom plugins.
        - By default, no validation checks are performed
        """
        from plugin import PluginMixinEnum, registry

        for plugin in registry.with_mixin(PluginMixinEnum.VALIDATION):
            try:
                plugin.validate_batch_code(self.batch, self)
            except ValidationError as exc:
                raise ValidationError({'batch': exc.message})
            except Exception:
                InvenTree.exceptions.log_error(
                    'validate_batch_code', plugin=plugin.slug
                )

    def clean(self):
        """Validate the StockItem object (separate to field validation).

        The following validation checks are performed:
        - The 'part' and 'supplier_part.part' fields cannot point to the same Part object
        - The 'part' is not virtual
        - The 'part' does not belong to itself
        - The location is not structural
        - Quantity must be 1 if the StockItem has a serial number
        """
        if self.location is not None and self.location.structural:
            raise ValidationError({
                'location': _(
                    'Stock items cannot be located into structural stock locations!'
                )
            })

        super().clean()

        # Strip serial number field
        if type(self.serial) is str:
            self.serial = self.serial.strip()

        # Strip batch code field
        if type(self.batch) is str:
            self.batch = self.batch.strip()

        # Custom validation of batch code
        self.validate_batch_code()

        try:
            # Trackable parts must have integer values for quantity field!
            if self.part.trackable and self.quantity != int(self.quantity):
                raise ValidationError({
                    'quantity': _('Quantity must be integer value for trackable parts')
                })

            # Virtual parts cannot have stock items created against them
            if self.part.virtual:
                raise ValidationError({
                    'part': _('Stock item cannot be created for virtual parts')
                })
        except PartModels.Part.DoesNotExist:
            # For some reason the 'clean' process sometimes throws errors because self.part does not exist
            # It *seems* that this only occurs in unit testing, though.
            # Probably should investigate this at some point.
            pass

        if self.quantity < 0:
            raise ValidationError({'quantity': _('Quantity must be greater than zero')})

        # The 'supplier_part' field must point to the same part!
        try:
            if self.supplier_part is not None:
                if self.supplier_part.part != self.part:
                    raise ValidationError({
                        'supplier_part': _(
                            f"Part type ('{self.supplier_part.part}') must be {self.part}"
                        )
                    })

            if self.part is not None:
                # A part with a serial number MUST have the quantity set to 1
                if self.serial:
                    if self.quantity > 1:
                        raise ValidationError({
                            'quantity': _(
                                'Quantity must be 1 for item with a serial number'
                            ),
                            'serial': _(
                                'Serial number cannot be set if quantity greater than 1'
                            ),
                        })

                    if self.quantity == 0:
                        self.quantity = 1

                    elif self.quantity > 1:
                        raise ValidationError({
                            'quantity': _(
                                'Quantity must be 1 for item with a serial number'
                            )
                        })

                    # Serial numbered items cannot be deleted on depletion
                    self.delete_on_deplete = False

        except PartModels.Part.DoesNotExist:
            pass

        # Ensure that the item cannot be assigned to itself
        if self.belongs_to and self.belongs_to.pk == self.pk:
            raise ValidationError({'belongs_to': _('Item cannot belong to itself')})

        # If the item is marked as "is_building", it must point to a build!
        if self.is_building and not self.build:
            raise ValidationError({
                'build': _('Item must have a build reference if is_building=True')
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
                    'build': _('Build reference does not point to the same part object')
                })

    def get_absolute_url(self):
        """Return url for instance."""
        return InvenTree.helpers.pui_url(f'/stock/item/{self.id}')

    def get_part_name(self):
        """Returns part name."""
        return self.part.full_name

    # Note: When a StockItem is deleted, a pre_delete signal handles the parent/child relationship
    parent = TreeForeignKey(
        'self',
        verbose_name=_('Parent Stock Item'),
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='children',
    )

    part = models.ForeignKey(
        'part.Part',
        on_delete=models.CASCADE,
        verbose_name=_('Base Part'),
        related_name='stock_items',
        help_text=_('Base part'),
        limit_choices_to={'virtual': False},
    )

    supplier_part = models.ForeignKey(
        'company.SupplierPart',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Supplier Part'),
        help_text=_('Select a matching supplier part for this stock item'),
        related_name='stock_items',
    )

    # Note: When a StockLocation is deleted, stock items are updated via a signal
    location = TreeForeignKey(
        StockLocation,
        on_delete=models.DO_NOTHING,
        verbose_name=_('Stock Location'),
        related_name='stock_items',
        blank=True,
        null=True,
        help_text=_('Where is this stock item located?'),
    )

    packaging = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Packaging'),
        help_text=_('Packaging this stock item is stored in'),
    )

    # When deleting a stock item with installed items, those installed items are also installed
    belongs_to = models.ForeignKey(
        'self',
        verbose_name=_('Installed In'),
        on_delete=models.CASCADE,
        related_name='installed_parts',
        blank=True,
        null=True,
        help_text=_('Is this item installed in another item?'),
    )

    customer = models.ForeignKey(
        CompanyModels.Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_customer': True},
        related_name='assigned_stock',
        help_text=_('Customer'),
        verbose_name=_('Customer'),
    )

    serial = models.CharField(
        verbose_name=_('Serial Number'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Serial number for this item'),
    )

    serial_int = models.IntegerField(default=0)

    link = InvenTreeURLField(
        verbose_name=_('External Link'),
        blank=True,
        help_text=_('Link to external URL'),
        max_length=2000,
    )

    batch = models.CharField(
        verbose_name=_('Batch Code'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Batch code for this stock item'),
        default=generate_batch_code,
    )

    quantity = models.DecimalField(
        verbose_name=_('Stock Quantity'),
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        default=1,
    )

    build = models.ForeignKey(
        'build.Build',
        on_delete=models.SET_NULL,
        verbose_name=_('Source Build'),
        blank=True,
        null=True,
        help_text=_('Build for this stock item'),
        related_name='build_outputs',
    )

    consumed_by = models.ForeignKey(
        'build.Build',
        on_delete=models.CASCADE,
        verbose_name=_('Consumed By'),
        blank=True,
        null=True,
        help_text=_('Build order which consumed this stock item'),
        related_name='consumed_stock',
    )

    is_building = models.BooleanField(default=False)

    purchase_order = models.ForeignKey(
        'order.PurchaseOrder',
        on_delete=models.SET_NULL,
        verbose_name=_('Source Purchase Order'),
        related_name='stock_items',
        blank=True,
        null=True,
        help_text=_('Purchase order for this stock item'),
    )

    sales_order = models.ForeignKey(
        'order.SalesOrder',
        on_delete=models.SET_NULL,
        verbose_name=_('Destination Sales Order'),
        related_name='stock_items',
        null=True,
        blank=True,
    )

    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Expiry Date'),
        help_text=_(
            'Expiry date for stock item. Stock will be considered expired after this date'
        ),
    )

    stocktake_date = models.DateField(blank=True, null=True)

    stocktake_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='stocktake_stock',
    )

    review_needed = models.BooleanField(default=False)

    delete_on_deplete = models.BooleanField(
        default=default_delete_on_deplete,
        verbose_name=_('Delete on deplete'),
        help_text=_('Delete this Stock Item when stock is depleted'),
    )

    status = InvenTreeCustomStatusModelField(
        default=StockStatus.OK.value,
        status_class=StockStatus,
        choices=StockStatus.items(),
        validators=[MinValueValidator(0)],
    )

    @property
    def status_text(self):
        """Return the text representation of the status field."""
        return StockStatus.text(self.status)

    purchase_price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_('Purchase Price'),
        help_text=_('Single unit purchase price at time of purchase'),
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Owner'),
        help_text=_('Select Owner'),
        related_name='stock_items',
    )

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
            deltas={'part': variant.pk},
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

        ownership_enabled = get_global_setting('STOCK_OWNERSHIP_CONTROL')

        if not ownership_enabled:
            # Location ownership function is not enabled, so return True
            return True

        owner = self.get_item_owner()

        if owner is None:
            return True

        return owner.is_user_allowed(user, include_group=True)

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

        today = InvenTree.helpers.current_date()

        stale_days = get_global_setting('STOCK_STALE_DAYS')

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

        today = InvenTree.helpers.current_date()

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

    def allocateToCustomer(
        self, customer, quantity=None, order=None, user=None, notes=None
    ):
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

        item.save(add_note=False)

        code = StockHistoryCode.SENT_TO_CUSTOMER
        deltas = {}

        if customer is not None:
            deltas['customer'] = customer.pk
            deltas['customer_name'] = customer.name

        # If an order is provided, we are shipping against a SalesOrder, not manually!
        if order:
            code = StockHistoryCode.SHIPPED_AGAINST_SALES_ORDER
            deltas['salesorder'] = order.pk

        item.add_tracking_entry(code, user, deltas, notes=notes)

        trigger_event(
            StockEvents.ITEM_ASSIGNED_TO_CUSTOMER,
            id=self.id,
            customer=customer.id if customer else None,
        )

        # Return the reference to the stock item
        return item

    @transaction.atomic
    def return_from_customer(self, location, user=None, **kwargs):
        """Return stock item from customer, back into the specified location.

        Arguments:
            location: The location to return the stock item to
            user: The user performing the action

        Keyword Arguments:
            notes: Additional notes to add to the tracking entry
            status: Optionally set the status of the stock item

        If the selected location is the same as the parent, merge stock back into the parent.
        Otherwise create the stock in the new location.

        Note that this function is provided for legacy compatibility,
        and the 'return_to_stock' function should be used instead.
        """
        self.return_to_stock(
            location,
            user,
            tracking_code=StockHistoryCode.RETURNED_FROM_CUSTOMER,
            **kwargs,
        )

    @transaction.atomic
    def return_to_stock(
        self, location, user=None, quantity=None, merge: bool = True, **kwargs
    ):
        """Return stock item into stock, removing any consumption status.

        Arguments:
            location: The location to return the stock item to
            user: The user performing the action
            quantity: If specified, the quantity to return to stock (default is the full quantity)
            merge: If True, attempt to merge this stock item back into the parent stock item
        """
        notes = kwargs.get('notes', '')

        tracking_code = kwargs.get('tracking_code', StockHistoryCode.RETURNED_TO_STOCK)

        item = self

        if quantity is not None and not self.serialized:
            # If quantity is specified, we are splitting the stock item
            if quantity <= 0:
                raise ValidationError({
                    'quantity': _('Quantity must be greater than zero')
                })

            if quantity > self.quantity:
                raise ValidationError({
                    'quantity': _('Quantity exceeds available stock')
                })

            if quantity < self.quantity:
                # Split the stock item
                item = self.splitStock(quantity, None, user)

        tracking_info = {}

        if location:
            tracking_info['location'] = location.pk

        if item.customer:
            tracking_info['customer'] = item.customer.id
            tracking_info['customer_name'] = item.customer.name

        if item.consumed_by:
            tracking_info['build_order'] = item.consumed_by.id

        # Clear out allocation information for the stock item
        item.consumed_by = None
        item.customer = None
        item.belongs_to = None
        item.sales_order = None
        item.location = location

        if status := kwargs.pop('status', None):
            if not item.compare_status(status):
                item.set_status(status)
                tracking_info['status'] = status

        item.save()

        item.clearAllocations()

        item.add_tracking_entry(
            tracking_code, user, notes=notes, deltas=tracking_info, location=location
        )

        trigger_event(StockEvents.ITEM_RETURNED_TO_STOCK, id=item.id)

        # Attempt to merge returned item into parent item:
        # - 'merge' parameter is True
        # - The parent location is the same as the current location
        # - The item does not have a serial number

        if (
            merge
            and not item.serialized
            and self.parent
            and item.location == self.parent.location
        ):
            self.parent.merge_stock_items(
                {item}, user=user, location=location, notes=notes
            )
        else:
            item.save(add_note=False)

    def is_allocated(self):
        """Return True if this StockItem is allocated to a SalesOrder or a Build."""
        return self.allocation_count() > 0

    def build_allocation_count(self, **kwargs):
        """Return the total quantity allocated to builds, with optional filters."""
        query = self.allocations.all()

        if filter_allocations := kwargs.get('filter_allocations'):
            query = query.filter(**filter_allocations)

        if exclude_allocations := kwargs.get('exclude_allocations'):
            query = query.exclude(**exclude_allocations)

        query = query.aggregate(q=Coalesce(Sum('quantity'), Decimal(0)))

        total = query['q']

        if total is None:
            total = Decimal(0)

        return total

    def get_sales_order_allocations(self, active=True, **kwargs):
        """Return a queryset for SalesOrderAllocations against this StockItem, with optional filters.

        Arguments:
            active: Filter by 'active' status of the allocation
        """
        query = self.sales_order_allocations.all()

        if filter_allocations := kwargs.get('filter_allocations'):
            query = query.filter(**filter_allocations)

        if exclude_allocations := kwargs.get('exclude_allocations'):
            query = query.exclude(**exclude_allocations)

        if active is True:
            query = query.filter(
                line__order__status__in=SalesOrderStatusGroups.OPEN,
                shipment__shipment_date=None,
            )
        elif active is False:
            query = query.exclude(
                line__order__status__in=SalesOrderStatusGroups.OPEN
            ).exclude(shipment__shipment_date=None)

        return query

    def sales_order_allocation_count(self, active=True, **kwargs):
        """Return the total quantity allocated to SalesOrders."""
        query = self.get_sales_order_allocations(active=active, **kwargs)
        query = query.aggregate(q=Coalesce(Sum('quantity'), Decimal(0)))

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

        return self.sales_order is None

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
    def installStockItem(self, other_item, quantity, user, notes, build=None):
        """Install another stock item into this stock item.

        Args:
            other_item: The stock item to install into this stock item
            quantity: The quantity of stock to install
            user: The user performing the operation
            notes: Any notes associated with the operation
            build: The BuildOrder to associate with the operation (optional)
        """
        # If the quantity is less than the stock item, split the stock!
        stock_item = other_item.splitStock(quantity, None, user)

        if stock_item is None:
            stock_item = other_item

        # Assign the other stock item into this one
        stock_item.belongs_to = self

        if build is not None:
            stock_item.consumed_by = build

        stock_item.location = None
        stock_item.save(add_note=False)

        deltas = {'stockitem': self.pk}

        if build is not None:
            deltas['buildorder'] = build.pk

        # Add a transaction note to the other item
        stock_item.add_tracking_entry(
            StockHistoryCode.INSTALLED_INTO_ASSEMBLY, user, notes=notes, deltas=deltas
        )

        # Add a transaction note to this item (the assembly)
        self.add_tracking_entry(
            StockHistoryCode.INSTALLED_CHILD_ITEM,
            user,
            notes=notes,
            deltas={'stockitem': stock_item.pk},
        )

        trigger_event(
            StockEvents.ITEM_INSTALLED_INTO_ASSEMBLY,
            id=stock_item.pk,
            assembly_id=self.pk,
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

        # Add a transaction note to the parent item
        self.belongs_to.add_tracking_entry(
            StockHistoryCode.REMOVED_CHILD_ITEM,
            user,
            deltas={'stockitem': self.pk},
            notes=notes,
        )

        tracking_info = {'stockitem': self.belongs_to.pk}

        self.add_tracking_entry(
            StockHistoryCode.REMOVED_FROM_ASSEMBLY,
            user,
            notes=notes,
            deltas=tracking_info,
            location=location,
        )

        # Mark this stock item as *not* belonging to anyone
        self.belongs_to = None
        self.consumed_by = None
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

    def is_in_stock(
        self,
        check_status: bool = True,
        check_quantity: bool = True,
        check_in_production: bool = True,
    ) -> bool:
        """Return True if this StockItem is "in stock".

        Arguments:
            check_status: If True, check the status of the StockItem. Defaults to True.
            check_quantity: If True, check the quantity of the StockItem. Defaults to True.
            check_in_production: If True, check if the item is in production. Defaults to True.
        """
        if check_status and self.status not in StockStatusGroups.AVAILABLE_CODES:
            return False

        if check_quantity and self.quantity <= 0:
            return False

        if check_in_production and self.is_building:
            return False

        return all([
            self.sales_order is None,  # Not assigned to a SalesOrder
            self.belongs_to is None,  # Not installed inside another StockItem
            self.customer is None,  # Not assigned to a customer
            self.consumed_by is None,  # Not consumed by a build
        ])

    @property
    def in_stock(self) -> bool:
        """Returns True if this item is in stock.

        See also: StockItem.IN_STOCK_FILTER for the db optimized version of this check.
        """
        return self.is_in_stock(check_status=True)

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

        return self.sales_order is None

    @property
    def tracking_info_count(self):
        """How many tracking entries are available?"""
        return self.tracking_info.count()

    @property
    def has_tracking_info(self):
        """Is tracking info available?"""
        return self.tracking_info_count > 0

    def add_tracking_entry(
        self,
        entry_type: int,
        user: User,
        deltas: dict | None = None,
        notes: str = '',
        commit: bool = True,
        **kwargs,
    ):
        """Add a history tracking entry for this StockItem.

        Args:
            entry_type (int): Code describing the "type" of historical action (see StockHistoryCode)
            user (User): The user performing this action
            deltas (dict, optional): A map of the changes made to the model. Defaults to None.
            notes (str, optional): URL associated with this tracking entry. Defaults to ''.
            commit (boolm optional): If True, save the entry to the database. Defaults to True.

        Returns:
            StockItemTracking: The created tracking entry
        """
        if deltas is None:
            deltas = {}

        # Prevent empty entry
        if (
            entry_type == StockHistoryCode.STOCK_UPDATE
            and len(deltas) == 0
            and not notes
        ):
            return None

        # Has a location been specified?
        location = kwargs.get('location')

        if location:
            deltas['location'] = location.id

        # Quantity specified?
        quantity = kwargs.get('quantity')

        if quantity:
            deltas['quantity'] = float(quantity)

        entry = StockItemTracking(
            item=self,
            tracking_type=entry_type.value,
            user=user,
            date=InvenTree.helpers.current_time(),
            notes=notes,
            deltas=deltas,
        )

        if commit:
            entry.save()

        return entry

    @transaction.atomic
    def serializeStock(
        self,
        quantity: int,
        serials: list[str],
        user: User | None = None,
        notes: str | None = '',
        location: StockLocation | None = None,
    ):
        """Split this stock item into unique serial numbers.

        - Quantity can be less than or equal to the quantity of the stock item
        - Number of serial numbers must match the quantity
        - Provided serial numbers must not already be in use

        Arguments:
            quantity: Number of items to serialize (integer)
            serials: List of serial numbers
            user: User object associated with action
            notes: Optional notes for tracking
            location: If specified, serialized items will be placed in the given location

        Returns:
            List of newly created StockItem objects, each with a unique serial number.
        """
        # Cannot serialize stock that is already serialized!
        if self.serialized:
            return None

        if not self.part.trackable:
            raise ValidationError({'part': _('Part is not set as trackable')})

        # Quantity must be a valid integer value
        try:
            quantity = int(quantity)
        except ValueError:
            raise ValidationError({'quantity': _('Quantity must be integer')})

        if quantity <= 0:
            raise ValidationError({'quantity': _('Quantity must be greater than zero')})

        if quantity > self.quantity:
            raise ValidationError({
                'quantity': _(
                    f'Quantity must not exceed available stock quantity ({self.quantity})'
                )
            })

        if type(serials) not in [list, tuple]:
            raise ValidationError({
                'serial_numbers': _('Serial numbers must be provided as a list')
            })

        if quantity != len(serials):
            raise ValidationError({
                'quantity': _('Quantity does not match serial numbers')
            })

        # Test if each of the serial numbers are valid
        existing = self.part.find_conflicting_serial_numbers(serials)

        if len(existing) > 0:
            msg = _('The following serial numbers already exist or are invalid')
            msg += ' : '
            msg += ','.join([str(x) for x in existing])
            raise ValidationError({'serial_numbers': msg})

        # Serialize this StockItem
        data = dict(StockItem.objects.filter(pk=self.pk).values()[0])

        if location:
            if location.structural:
                raise ValidationError({
                    'location': _('Cannot assign stock to structural location')
                })

            data['location_id'] = location.pk

        # Set the parent ID correctly
        data['parent'] = self
        data['tree_id'] = self.tree_id

        # Generate a new serial number for each item
        items = StockItem._create_serial_numbers(serials, **data)

        # Create a new tracking entry for each item
        history_items = []

        for item in items:
            # Construct tracking entries for the new StockItem
            if entry := item.add_tracking_entry(
                StockHistoryCode.SPLIT_FROM_PARENT,
                user,
                quantity=1,
                notes=notes,
                location=location,
                commit=False,
            ):
                history_items.append(entry)

            if entry := item.add_tracking_entry(
                StockHistoryCode.ASSIGNED_SERIAL,
                user,
                notes=notes,
                deltas={'serial': item.serial},
                location=location,
                commit=False,
            ):
                history_items.append(entry)

            # Copy any test results from this item to the new one
            item.copyTestResultsFrom(self)

        StockItemTracking.objects.bulk_create(history_items)

        # Remove the equivalent number of items
        self.take_stock(
            quantity, user, code=StockHistoryCode.STOCK_SERIZALIZED, notes=notes
        )

        return items

    @transaction.atomic
    def copyHistoryFrom(self, other):
        """Copy stock history from another StockItem."""
        for item in other.tracking_info.all():
            item.item = self
            item.pk = None
            item.save()

    @transaction.atomic
    def copyTestResultsFrom(self, other: StockItem, filters: dict | None = None):
        """Copy all test results from another StockItem."""
        # Set default - see B006

        results = other.test_results.all()

        if filters:
            results = results.filter(**filters)

        results_to_create = []

        for result in list(results):
            # Create a copy of the test result by nulling-out the pk
            result.pk = None
            result.stock_item = self
            results_to_create.append(result)

        StockItemTestResult.objects.bulk_create(results_to_create)

    def add_test_result(self, create_template=True, **kwargs):
        """Helper function to add a new StockItemTestResult.

        The main purpose of this function is to allow lookup of the template,
        based on the provided test name.

        If no template is found, a new one is created (if create_template=True).

        Args:
            create_template: If True, create a new template if it does not exist

        kwargs:
            template: The ID of the associated PartTestTemplate
            test_name: The name of the test (if the template is not provided)
            result: The result of the test
            value: The value of the test
            user: The user who performed the test
            notes: Any notes associated with the test
        """
        template = kwargs.get('template')
        test_name = kwargs.pop('test_name', None)

        test_key = InvenTree.helpers.generateTestKey(test_name)

        if template is None and test_name is not None:
            # Attempt to find a matching template

            ancestors = self.part.get_ancestors(include_self=True)

            template = PartModels.PartTestTemplate.objects.filter(
                part__tree_id=self.part.tree_id, part__in=ancestors, key=test_key
            ).first()

            if template is None:
                if create_template:
                    template = PartModels.PartTestTemplate.objects.create(
                        part=self.part, test_name=test_name
                    )
                else:
                    raise ValidationError({
                        'template': _('Test template does not exist')
                    })

        kwargs['template'] = template
        kwargs['stock_item'] = self

        return StockItemTestResult.objects.create(**kwargs)

    def can_merge(self, other=None, raise_error=False, **kwargs):
        """Check if this stock item can be merged into another stock item."""
        allow_mismatched_suppliers = kwargs.get('allow_mismatched_suppliers', False)

        allow_mismatched_status = kwargs.get('allow_mismatched_status', False)

        try:
            # Generic checks (do not rely on the 'other' part)
            if self.sales_order:
                raise ValidationError(
                    _('Stock item has been assigned to a sales order')
                )

            if self.belongs_to:
                raise ValidationError(_('Stock item is installed in another item'))

            if self.installed_item_count() > 0:
                raise ValidationError(_('Stock item contains other items'))

            if self.customer:
                raise ValidationError(_('Stock item has been assigned to a customer'))

            if self.is_building:
                raise ValidationError(_('Stock item is currently in production'))

            if self.serialized:
                raise ValidationError(_('Serialized stock cannot be merged'))

            if other:
                # Specific checks (rely on the 'other' part)

                # Prevent stock item being merged with itself
                if self == other:
                    raise ValidationError(_('Duplicate stock items'))

                # Base part must match
                if self.part != other.part:
                    raise ValidationError(_('Stock items must refer to the same part'))

                # Check if supplier part references match
                if (
                    self.supplier_part != other.supplier_part
                    and not allow_mismatched_suppliers
                ):
                    raise ValidationError(
                        _('Stock items must refer to the same supplier part')
                    )

                # Check if stock status codes match
                if self.status != other.status and not allow_mismatched_status:
                    raise ValidationError(_('Stock status codes must match'))

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
        if isinstance(other_items, StockItem):
            other_items = [other_items]

        if len(other_items) == 0:
            return

        # Keep track of the tree IDs that are being merged
        tree_ids = {self.tree_id}

        user = kwargs.get('user')
        location = kwargs.get('location', self.location)
        notes = kwargs.get('notes')

        parent_id = self.parent.pk if self.parent else None

        # Keep track of pricing data for the merged data
        pricing_data = []

        if self.purchase_price:
            pricing_data.append([self.purchase_price, self.quantity])

        for other in other_items:
            # If the stock item cannot be merged, return
            if not self.can_merge(other, raise_error=raise_error, **kwargs):
                logger.warning(
                    'Stock item <%s> could not be merge into <%s>', other.pk, self.pk
                )
                return

        for other in other_items:
            tree_ids.add(other.tree_id)

            self.quantity += other.quantity

            if other.purchase_price:
                # Only add pricing data if it is available
                pricing_data.append([other.purchase_price, other.quantity])

            # Any "build order allocations" for the other item must be assigned to this one
            for allocation in other.allocations.all():
                allocation.stock_item = self
                allocation.save()

            # Any "sales order allocations" for the other item must be assigned to this one
            for allocation in other.sales_order_allocations.all():
                allocation.stock_item = self
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
            deltas={'location': location.pk if location else None},
        )

        # Update the location of the item
        self.location = location

        # Update the unit price - calculate weighted average of available pricing data
        if len(pricing_data) > 0:
            unit_price, quantity = pricing_data[0]

            # Use the first currency as the base currency
            base_currency = unit_price.currency

            total_price = unit_price * quantity

            for price, qty in pricing_data[1:]:
                # Attempt to convert the price to the base currency
                try:
                    price = convert_money(price, base_currency)
                    total_price += price * qty
                    quantity += qty
                except Exception:
                    # Skip this entry, cannot convert to base currency
                    continue

            if quantity > 0:
                self.purchase_price = total_price / quantity

        self.save()

        # Rebuild stock trees as required
        rebuild_result = True
        for tree_id in tree_ids:
            if not stock.tasks.rebuild_stock_item_tree(tree_id, rebuild_on_fail=False):
                rebuild_result = False

        if not rebuild_result:
            # If the rebuild failed, offload the task to a background worker
            logger.warning(
                'Failed to rebuild stock item tree during merge_stock_items operation, offloading task.'
            )
            InvenTree.tasks.offload_task(stock.tasks.rebuild_stock_items, group='stock')

    @transaction.atomic
    def splitStock(self, quantity, location=None, user=None, **kwargs):
        """Split this stock item into two items, in the same location.

        Stock tracking notes for this StockItem will be duplicated,
        and added to the new StockItem.

        Args:
            quantity: Number of stock items to remove from this entity, and pass to the next
            location: Where to move the new StockItem to
            user: User performing the action

        kwargs:
            notes: Optional notes for tracking
            batch: If provided, override the batch (default = existing batch)
            status: If provided, override the status (default = existing status)
            packaging: If provided, override the packaging (default = existing packaging)
            allow_production: If True, allow splitting of stock which is in production (default = False)

        Returns:
            The new StockItem object

        Raises:
            ValidationError: If the stock item cannot be split

        - The provided quantity will be subtracted from this item and given to the new one.
        - The new item will have a different StockItem ID, while this will remain the same.
        """
        # Run initial checks to test if the stock item can actually be "split"
        allow_production = kwargs.get('allow_production', False)

        # Cannot split a stock item which is in production
        if self.is_building and not allow_production:
            raise ValidationError(_('Stock item is currently in production'))

        notes = kwargs.get('notes', '')

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
        new_stock.quantity = quantity

        # Update the new stock item to ensure the tree structure is observed
        new_stock.parent = self
        new_stock.tree_id = None

        # Move to the new location if specified, otherwise use current location
        if location:
            new_stock.location = location
        else:
            new_stock.location = self.location

        deltas = {'stockitem': self.pk}

        # Optional fields which can be supplied in a 'move' call
        for field in StockItem.optional_transfer_fields():
            if field in kwargs:
                setattr(new_stock, field, kwargs[field])
                deltas[field] = kwargs[field]

        new_stock.save(add_note=False)

        # Add a stock tracking entry for the newly created item
        new_stock.add_tracking_entry(
            StockHistoryCode.SPLIT_FROM_PARENT,
            user,
            quantity=quantity,
            notes=notes,
            location=location,
            deltas=deltas,
        )

        # Copy the test results of this part to the new one
        new_stock.copyTestResultsFrom(self)

        # Remove the specified quantity from THIS stock item
        self.take_stock(
            quantity,
            user,
            code=StockHistoryCode.SPLIT_CHILD_ITEM,
            notes=notes,
            location=location,
            stockitem=new_stock,
        )

        # Rebuild the tree for this parent item
        stock.tasks.rebuild_stock_item_tree(self.tree_id)

        # Attempt to reload the new item from the database
        try:
            new_stock.refresh_from_db()
        except Exception:
            pass

        trigger_event(StockEvents.ITEM_SPLIT, id=new_stock.id, parent=self.id)

        # Return a copy of the "new" stock item
        return new_stock

    @classmethod
    def optional_transfer_fields(cls):
        """Returns a list of optional fields for a stock transfer."""
        return ['batch', 'status', 'packaging']

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
            batch: If provided, override the batch (default = existing batch)
            status: If provided, override the status (default = existing status)
            packaging: If provided, override the packaging (default = existing packaging)
        """
        current_location = self.location

        try:
            quantity = Decimal(kwargs.pop('quantity', self.quantity))
        except InvalidOperation:
            return False

        allow_out_of_stock_transfer = get_global_setting(
            'STOCK_ALLOW_OUT_OF_STOCK_TRANSFER', backup_value=False, cache=False
        )

        if not allow_out_of_stock_transfer and not self.is_in_stock(
            check_status=False, check_in_production=False
        ):
            raise ValidationError(_('StockItem cannot be moved as it is not in stock'))

        if quantity <= 0:
            return False

        if location is None:
            return False

        # Test for a partial movement
        if quantity < self.quantity:
            # We need to split the stock!

            kwargs['notes'] = notes

            # Split the existing StockItem in two
            self.splitStock(quantity, location, user, allow_production=True, **kwargs)

            return True

        # Moving into the same location triggers a different history code
        same_location = location == self.location

        self.location = location

        tracking_info = {}

        tracking_code = StockHistoryCode.STOCK_MOVE

        if same_location:
            tracking_code = StockHistoryCode.STOCK_UPDATE
        else:
            tracking_info['location'] = location.pk

        status = kwargs.pop('status', None) or kwargs.pop('status_custom_key', None)

        if status and not self.compare_status(status):
            self.set_status(status)
            tracking_info['status'] = status

        # Optional fields which can be supplied in a 'move' call
        for field in StockItem.optional_transfer_fields():
            if field in kwargs:
                setattr(self, field, kwargs[field])
                tracking_info[field] = kwargs[field]

        self.add_tracking_entry(tracking_code, user, notes=notes, deltas=tracking_info)

        self.save(add_note=False)

        # Trigger event for the plugin system
        trigger_event(
            StockEvents.ITEM_MOVED,
            id=self.id,
            old_location=current_location.id if current_location else None,
            new_location=location.id if location else None,
            quantity=quantity,
        )

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

        quantity = max(quantity, 0)

        self.quantity = quantity

        if quantity == 0 and self.delete_on_deplete and self.can_delete():
            self.delete()

            return False

        self.save()

        trigger_event(
            StockEvents.ITEM_QUANTITY_UPDATED, id=self.id, quantity=float(self.quantity)
        )

        return True

    @transaction.atomic
    def stocktake(self, count, user, **kwargs):
        """Perform item stocktake.

        Arguments:
            count: The new quantity of the item
            user: The user performing the stocktake

        Keyword Arguments:
            notes: Optional notes for the stocktake
            status: Optionally adjust the stock status
        """
        try:
            count = Decimal(count)
        except InvalidOperation:
            return False

        if count < 0:
            return False

        tracking_info = {}

        status = kwargs.pop('status', None) or kwargs.pop('status_custom_key', None)

        if status and not self.compare_status(status):
            self.set_status(status)
            tracking_info['status'] = status

        if self.updateQuantity(count):
            tracking_info['quantity'] = float(count)

            self.stocktake_date = InvenTree.helpers.current_date()
            self.stocktake_user = user

            # Optional fields which can be supplied in a 'stocktake' call
            for field in StockItem.optional_transfer_fields():
                if field in kwargs:
                    setattr(self, field, kwargs[field])
                    tracking_info[field] = kwargs[field]

            self.save(add_note=False)

            self.add_tracking_entry(
                StockHistoryCode.STOCK_COUNT,
                user,
                notes=kwargs.get('notes', ''),
                deltas=tracking_info,
            )

        trigger_event(
            StockEvents.ITEM_COUNTED,
            'stockitem.counted',
            id=self.id,
            quantity=float(self.quantity),
        )

        return True

    @transaction.atomic
    def add_stock(self, quantity, user, **kwargs):
        """Add a specified quantity of stock to this item.

        Arguments:
            quantity: The quantity to add
            user: The user performing the action

        Keyword Arguments:
            notes: Optional notes for the stock addition
            status: Optionally adjust the stock status
        """
        # Cannot add items to a serialized part
        if self.serialized:
            return False

        try:
            quantity = Decimal(quantity)
        except InvalidOperation:
            return False

        # Ignore amounts that do not make sense
        if quantity <= 0:
            return False

        tracking_info = {}

        status = kwargs.pop('status', None) or kwargs.pop('status_custom_key', None)

        if status and not self.compare_status(status):
            self.set_status(status)
            tracking_info['status'] = status

        if self.updateQuantity(self.quantity + quantity):
            tracking_info['added'] = float(quantity)
            tracking_info['quantity'] = float(self.quantity)

            # Optional fields which can be supplied in a 'stocktake' call
            for field in StockItem.optional_transfer_fields():
                if field in kwargs:
                    setattr(self, field, kwargs[field])
                    tracking_info[field] = kwargs[field]

            self.save(add_note=False)

            self.add_tracking_entry(
                StockHistoryCode.STOCK_ADD,
                user,
                notes=kwargs.get('notes', ''),
                deltas=tracking_info,
            )

        return True

    @transaction.atomic
    def take_stock(self, quantity, user, code=StockHistoryCode.STOCK_REMOVE, **kwargs):
        """Remove the specified quantity from this StockItem.

        Arguments:
            quantity: The quantity to remove
            user: The user performing the action

        Keyword Arguments:
            code: The stock history code to use
            notes: Optional notes for the stock removal
            status: Optionally adjust the stock status
        """
        # Cannot remove items from a serialized part
        if self.serialized:
            return False

        try:
            quantity = Decimal(quantity)
        except InvalidOperation:
            return False

        if quantity <= 0:
            return False

        deltas = {}

        status = kwargs.pop('status', None) or kwargs.pop('status_custom_key', None)

        if status and not self.compare_status(status):
            self.set_status(status)
            deltas['status'] = status

        if self.updateQuantity(self.quantity - quantity):
            deltas['removed'] = float(quantity)
            deltas['quantity'] = float(self.quantity)

            if location := kwargs.get('location'):
                deltas['location'] = location.pk

            if stockitem := kwargs.get('stockitem'):
                deltas['stockitem'] = stockitem.pk

            # Optional fields which can be supplied in a 'stocktake' call
            for field in StockItem.optional_transfer_fields():
                if field in kwargs:
                    setattr(self, field, kwargs[field])
                    deltas[field] = kwargs[field]

            self.save(add_note=False)

            self.add_tracking_entry(
                code, user, notes=kwargs.get('notes', ''), deltas=deltas
            )

        return True

    def __str__(self):
        """Human friendly name."""
        if self.part.trackable and self.serial:
            s = f'{self.part.full_name} #{self.serial}'
        else:
            s = f'{InvenTree.helpers.decimal2string(self.quantity)} x {self.part.full_name}'

        if self.location:
            s += f' @ {self.location.name}'

        if self.purchase_order:
            s += f' ({self.purchase_order})'

        return s

    @transaction.atomic
    def clear_test_results(self, **kwargs):
        """Remove all test results."""
        # All test results
        results = self.test_results.all()
        results.delete()

    def getTestResults(self, template=None, test=None, result=None, user=None):
        """Return all test results associated with this StockItem.

        Optionally can filter results by:
        - Test template ID
        - Test name
        - Test result
        - User
        """
        results = self.test_results

        if template:
            results = results.filter(template=template)

        if test:
            # Filter by test name
            test_key = InvenTree.helpers.generateTestKey(test)
            results = results.filter(template__key=test_key)

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
        cascade = kwargs.pop('cascade', False)

        # Filter results by "date", so that newer results
        # will override older ones.
        results = self.getTestResults(**kwargs).order_by('date')

        result_map = {}

        for result in results:
            result_map[result.key] = result

        if include_installed:
            installed_items = self.get_installed_items(cascade=cascade)

            for item in installed_items:
                item_results = item.testResultMap()

                for key in item_results:
                    # Results from sub items should not override master ones
                    if key not in result_map:
                        result_map[key] = item_results[key]

        return result_map

    def testResultList(self, **kwargs):
        """Return a list of test-result objects for this StockItem."""
        return list(self.testResultMap(**kwargs).values())

    def requiredTestStatus(self, required_tests=None):
        """Return the status of the tests required for this StockItem.

        Return:
            A dict containing the following items:
            - total: Number of required tests
            - passed: Number of tests that have passed
            - failed: Number of tests that have failed
        """
        # All the tests required by the part object

        if required_tests is None:
            required_tests = self.part.getRequiredTests()

        results = self.testResultMap()

        total = len(required_tests)
        passed = 0
        failed = 0

        for test in required_tests:
            key = InvenTree.helpers.generateTestKey(test.test_name)

            if key in results:
                result = results[key]

                if result.result:
                    passed += 1
                else:
                    failed += 1

        return {'total': total, 'passed': passed, 'failed': failed}

    @property
    def required_test_count(self):
        """Return the number of 'required tests' for this StockItem."""
        return self.part.getRequiredTests().count()

    def hasRequiredTests(self):
        """Return True if there are any 'required tests' associated with this StockItem."""
        return self.required_test_count > 0

    def passedAllRequiredTests(self, required_tests=None):
        """Returns True if this StockItem has passed all required tests."""
        status = self.requiredTestStatus(required_tests=required_tests)

        return status['passed'] >= status['total']


@receiver(post_delete, sender=StockItem, dispatch_uid='stock_item_post_delete_log')
def after_delete_stock_item(sender, instance: StockItem, **kwargs):
    """Function to be executed after a StockItem object is deleted."""
    from part import tasks as part_tasks

    if InvenTree.ready.isImportingData():
        return

    if InvenTree.ready.canAppAccessDatabase(allow_test=True):
        # Run this check in the background
        InvenTree.tasks.offload_task(
            part_tasks.notify_low_stock_if_required,
            instance.part.pk,
            group='notification',
            force_async=True,
        )

    if InvenTree.ready.canAppAccessDatabase(allow_test=settings.TESTING_PRICING):
        # Schedule an update on parent part pricing
        if instance.part:
            instance.part.schedule_pricing_update(create=False)


@receiver(post_save, sender=StockItem, dispatch_uid='stock_item_post_save_log')
def after_save_stock_item(sender, instance: StockItem, created, **kwargs):
    """Hook function to be executed after StockItem object is saved/updated."""
    from part import tasks as part_tasks

    if not InvenTree.ready.isImportingData():
        if InvenTree.ready.canAppAccessDatabase(allow_test=True):
            InvenTree.tasks.offload_task(
                part_tasks.notify_low_stock_if_required,
                instance.part.pk,
                group='notification',
                force_async=True,
            )

        if InvenTree.ready.canAppAccessDatabase(allow_test=settings.TESTING_PRICING):
            if instance.part:
                instance.part.schedule_pricing_update(create=True)


class StockItemTracking(InvenTree.models.InvenTreeModel):
    """Stock tracking entry - used for tracking history of a particular StockItem.

    Note: 2021-05-11
    The legacy StockTrackingItem model contained very little information about the "history" of the item.
    In fact, only the "quantity" of the item was recorded at each interaction.
    Also, the "title" was translated at time of generation, and thus was not really translatable.
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

    class Meta:
        """Meta data for the StockItemTracking class."""

        verbose_name = _('Stock Item Tracking')

    @staticmethod
    def get_api_url():
        """Return API url."""
        return reverse('api-stock-tracking-list')

    def get_absolute_url(self):
        """Return url for instance."""
        return InvenTree.helpers.pui_url(f'/stock/item/{self.item.id}')

    def label(self):
        """Return label."""
        if self.tracking_type in StockHistoryCode.keys():  # noqa: SIM118
            return StockHistoryCode.label(self.tracking_type)

        return getattr(self, 'title', '')

    tracking_type = models.IntegerField(default=StockHistoryCode.LEGACY)

    item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name='tracking_info'
    )

    date = models.DateTimeField(auto_now_add=True, editable=False)

    notes = models.CharField(
        blank=True,
        null=True,
        max_length=512,
        verbose_name=_('Notes'),
        help_text=_('Entry notes'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    deltas = models.JSONField(null=True, blank=True)


def rename_stock_item_test_result_attachment(instance, filename):
    """Rename test result."""
    return os.path.join(
        'stock_files', str(instance.stock_item.pk), os.path.basename(filename)
    )


class StockItemTestResult(InvenTree.models.InvenTreeMetadataModel):
    """A StockItemTestResult records results of custom tests against individual StockItem objects.

    This is useful for tracking unit acceptance tests, and particularly useful when integrated
    with automated testing setups.

    Multiple results can be recorded against any given test, allowing tests to be run many times.

    Attributes:
        stock_item: Link to StockItem
        template: Link to TestTemplate
        result: Test result value (pass / fail / etc)
        value: Recorded test output value (optional)
        attachment: Link to StockItem attachment (optional)
        notes: Extra user notes related to the test (optional)
        test_station: the name of the test station where the test was performed
        started_datetime: Date when the test was started
        finished_datetime: Date when the test was finished
        user: User who uploaded the test result
        date: Date the test result was recorded
    """

    class Meta:
        """Meta data for the StockItemTestResult class."""

        verbose_name = _('Stock Item Test Result')

    def __str__(self):
        """Return string representation."""
        return f'{self.test_name} - {self.result}'

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
        try:
            template = self.template
        except PartModels.PartTestTemplate.DoesNotExist:
            template = None

        if not template:
            raise ValidationError({'template': _('Test template does not exist')})

        if template.requires_value and not self.value:
            raise ValidationError({'value': _('Value must be provided for this test')})

        if template.requires_attachment and not self.attachment:
            raise ValidationError({
                'attachment': _('Attachment must be uploaded for this test')
            })

        if choices := template.get_choices():
            if self.value not in choices:
                raise ValidationError({'value': _('Invalid value for this test')})

    @property
    def key(self):
        """Return key for test."""
        return InvenTree.helpers.generateTestKey(self.test_name)

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name='test_results'
    )

    @property
    def test_name(self):
        """Return the test name of the associated test template."""
        return self.template.test_name

    template = models.ForeignKey(
        'part.parttesttemplate',
        on_delete=models.CASCADE,
        blank=False,
        related_name='test_results',
    )

    result = models.BooleanField(
        default=False, verbose_name=_('Result'), help_text=_('Test result')
    )

    value = models.CharField(
        blank=True,
        max_length=500,
        verbose_name=_('Value'),
        help_text=_('Test output value'),
    )

    attachment = models.FileField(
        null=True,
        blank=True,
        upload_to=rename_stock_item_test_result_attachment,
        verbose_name=_('Attachment'),
        help_text=_('Test result attachment'),
    )

    notes = models.CharField(
        blank=True, max_length=500, verbose_name=_('Notes'), help_text=_('Test notes')
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    test_station = models.CharField(
        blank=True,
        max_length=500,
        verbose_name=_('Test station'),
        help_text=_('The identifier of the test station where the test was performed'),
    )

    started_datetime = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Started'),
        help_text=_('The timestamp of the test start'),
    )

    finished_datetime = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Finished'),
        help_text=_('The timestamp of the test finish'),
    )

    date = models.DateTimeField(auto_now_add=True, editable=False)
