"""Order model definitions."""

from decimal import Decimal
from typing import Any, Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money
from mptt.models import TreeForeignKey

import common.models as common_models
import InvenTree.helpers
import InvenTree.models
import InvenTree.ready
import InvenTree.tasks
import InvenTree.validators
import order.validators
import report.mixins
import stock.models
import users.models as UserModels
from build.status_codes import BuildStatus
from common.currency import currency_code_default
from common.notifications import InvenTreeNotificationBodies
from common.settings import get_global_setting
from company.models import Address, Company, Contact, SupplierPart
from generic.states import StateTransitionMixin, StatusCodeMixin
from generic.states.fields import InvenTreeCustomStatusModelField
from InvenTree.exceptions import log_error
from InvenTree.fields import (
    InvenTreeModelMoneyField,
    InvenTreeURLField,
    RoundingDecimalField,
)
from InvenTree.helpers import decimal2string, pui_url
from InvenTree.helpers_model import notify_responsible
from order.events import PurchaseOrderEvents, ReturnOrderEvents, SalesOrderEvents
from order.status_codes import (
    PurchaseOrderStatus,
    PurchaseOrderStatusGroups,
    ReturnOrderLineStatus,
    ReturnOrderStatus,
    ReturnOrderStatusGroups,
    SalesOrderStatus,
    SalesOrderStatusGroups,
)
from part import models as PartModels
from plugin.events import trigger_event
from stock.status_codes import StockHistoryCode, StockStatus

logger = structlog.get_logger('inventree')


class TotalPriceMixin(models.Model):
    """Mixin which provides 'total_price' field for an order."""

    class Meta:
        """Meta for MetadataMixin."""

        abstract = True

    def save(self, *args, **kwargs):
        """Update the total_price field when saved."""
        # Recalculate total_price for this order
        self.update_total_price(commit=False)

        if hasattr(self, '_SAVING_TOTAL_PRICE') and self._SAVING_TOTAL_PRICE:
            # Avoid recursion on save
            return super().save(*args, **kwargs)
        self._SAVING_TOTAL_PRICE = True

        # Save the object as we can not access foreign/m2m fields before saving
        self.update_total_price(commit=True)

    total_price = InvenTreeModelMoneyField(
        null=True,
        blank=True,
        allow_negative=False,
        verbose_name=_('Total Price'),
        help_text=_('Total price for this order'),
    )

    order_currency = models.CharField(
        max_length=3,
        verbose_name=_('Order Currency'),
        blank=True,
        null=True,
        help_text=_('Currency for this order (leave blank to use company default)'),
        validators=[InvenTree.validators.validate_currency_code],
    )

    @property
    def currency(self):
        """Return the currency associated with this order instance.

        Rules:
        - If the order_currency field is set, return that
        - Otherwise, return the currency associated with the company
        - Finally, return the default currency code
        """
        if self.order_currency:
            return self.order_currency

        if self.company:
            return self.company.currency_code

        # Return default currency code
        return currency_code_default()

    def update_total_price(self, commit=True):
        """Recalculate and save the total_price for this order."""
        self.total_price = self.calculate_total_price(target_currency=self.currency)

        if commit:
            self.save()

    def calculate_total_price(self, target_currency=None):
        """Calculates the total price of all order lines, and converts to the specified target currency.

        If not specified, the default system currency is used.

        If currency conversion fails (e.g. there are no valid conversion rates),
        then we simply return zero, rather than attempting some other calculation.
        """
        # Set default - see B008
        if target_currency is None:
            target_currency = currency_code_default()

        total = Money(0, target_currency)

        # Check if the order has been saved (otherwise we can't calculate the total price)
        if self.pk is None:
            return total

        # order items
        for line in self.lines.all():
            if not line.price:
                continue

            try:
                total += line.quantity * convert_money(line.price, target_currency)
            except MissingRate:
                log_error('order.calculate_total_price')
                logger.exception("Missing exchange rate for '%s'", target_currency)

                # Return None to indicate the calculated price is invalid
                return None

        # extra items
        for line in self.extra_lines.all():
            if not line.price:
                continue

            try:
                total += line.quantity * convert_money(line.price, target_currency)
            except MissingRate:
                # Record the error, try to press on

                log_error('order.calculate_total_price')
                logger.exception("Missing exchange rate for '%s'", target_currency)

                # Return None to indicate the calculated price is invalid
                return None

        # set decimal-places
        total.decimal_places = 4

        return total


class BaseOrderReportContext(report.mixins.BaseReportContext):
    """Base context for all order models.

    Attributes:
        description: The description field of the order
        extra_lines: Query set of all extra lines associated with the order
        lines: Query set of all line items associated with the order
        order: The order instance itself
        reference: The reference field of the order
        title: The title (string representation) of the order
    """

    description: str
    extra_lines: Any
    lines: Any
    order: Any
    reference: str
    title: str


class PurchaseOrderReportContext(report.mixins.BaseReportContext):
    """Context for the purchase order model.

    Attributes:
        description: The description field of the PurchaseOrder
        reference: The reference field of the PurchaseOrder
        title: The title (string representation) of the PurchaseOrder
        extra_lines: Query set of all extra lines associated with the PurchaseOrder
        lines: Query set of all line items associated with the PurchaseOrder
        order: The PurchaseOrder instance itself
        supplier: The supplier object associated with the PurchaseOrder
    """

    description: str
    reference: str
    title: str
    extra_lines: report.mixins.QuerySet['PurchaseOrderExtraLine']
    lines: report.mixins.QuerySet['PurchaseOrderLineItem']
    order: 'PurchaseOrder'
    supplier: Optional[Company]


class SalesOrderReportContext(report.mixins.BaseReportContext):
    """Context for the sales order model.

    Attributes:
        description: The description field of the SalesOrder
        reference: The reference field of the SalesOrder
        title: The title (string representation) of the SalesOrder
        extra_lines: Query set of all extra lines associated with the SalesOrder
        lines: Query set of all line items associated with the SalesOrder
        order: The SalesOrder instance itself
        customer: The customer object associated with the SalesOrder
    """

    description: str
    reference: str
    title: str
    extra_lines: report.mixins.QuerySet['SalesOrderExtraLine']
    lines: report.mixins.QuerySet['SalesOrderLineItem']
    order: 'SalesOrder'
    customer: Optional[Company]


class ReturnOrderReportContext(report.mixins.BaseReportContext):
    """Context for the return order model.

    Attributes:
        description: The description field of the ReturnOrder
        reference: The reference field of the ReturnOrder
        title: The title (string representation) of the ReturnOrder
        extra_lines: Query set of all extra lines associated with the ReturnOrder
        lines: Query set of all line items associated with the ReturnOrder
        order: The ReturnOrder instance itself
        customer: The customer object associated with the ReturnOrder
    """

    description: str
    reference: str
    title: str
    extra_lines: report.mixins.QuerySet['ReturnOrderExtraLine']
    lines: report.mixins.QuerySet['ReturnOrderLineItem']
    order: 'ReturnOrder'
    customer: Optional[Company]


class Order(
    StatusCodeMixin,
    StateTransitionMixin,
    InvenTree.models.InvenTreeParameterMixin,
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    InvenTree.models.InvenTreeNotesMixin,
    report.mixins.InvenTreeReportMixin,
    InvenTree.models.MetadataMixin,
    InvenTree.models.ReferenceIndexingMixin,
    InvenTree.models.InvenTreeModel,
):
    """Abstract model for an order.

    Instances of this class:

    - PurchaseOrder
    - SalesOrder

    Attributes:
        reference: Unique order number / reference / code
        description: Long form description (required)
        notes: Extra note field (optional)
        creation_date: Automatic date of order creation
        created_by: User who created this order (automatically captured)
        issue_date: Date the order was issued
        start_date: Date the order is scheduled to be started
        target_date: Expected or desired completion date
        complete_date: Date the order was completed
        responsible: User (or group) responsible for managing the order
    """

    REQUIRE_RESPONSIBLE_SETTING = None
    UNLOCK_SETTING = None

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    def save(self, *args, **kwargs):
        """Custom save method for the order models.

        Enforces various business logics:
        - Ensures the object is not locked
        - Ensures that the reference field is rebuilt whenever the instance is saved.
        """
        # check if we are updating the model, not adding it
        update = self.pk is not None

        # Locking
        if update and self.check_locked(True):
            # Ensure that order status can be changed still
            if self.get_db_instance().status != self.status:
                pass
            else:
                raise ValidationError({
                    'reference': _('This order is locked and cannot be modified')
                })

        # Reference calculations
        self.reference_int = self.rebuild_reference_field(self.reference)
        if not self.creation_date:
            self.creation_date = InvenTree.helpers.current_date()

        super().save(*args, **kwargs)

    def check_locked(self, db: bool = False) -> bool:
        """Check if this order is 'locked'.

        A locked order cannot be modified after it has been completed.

        Arguments:
            db: If True, check with the database. If False, check the instance (default False).
        """
        if not self.check_complete(db=db):
            # If the order is not complete, it is not locked
            return False

        if self.UNLOCK_SETTING:
            return get_global_setting(self.UNLOCK_SETTING, backup_value=False) is False

        return False

    def check_complete(self, db: bool = False) -> bool:
        """Check if this order is 'complete'.

        Arguments:
            db: If True, check with the database. If False, check the instance (default False).
        """
        status = self.get_db_instance().status if db else self.status
        return status in self.get_status_class().COMPLETE

    def clean(self):
        """Custom clean method for the generic order class."""
        super().clean()

        # Check if a responsible owner is required for this order type
        if self.REQUIRE_RESPONSIBLE_SETTING:
            if get_global_setting(self.REQUIRE_RESPONSIBLE_SETTING, backup_value=False):
                if not self.responsible:
                    raise ValidationError({
                        'responsible': _('Responsible user or group must be specified')
                    })

        # Check that the referenced 'contact' matches the correct 'company'
        if self.company and self.contact:
            if self.contact.company != self.company:
                raise ValidationError({
                    'contact': _('Contact does not match selected company')
                })

        # Target date should be *after* the start date
        if self.start_date and self.target_date and self.start_date > self.target_date:
            raise ValidationError({
                'target_date': _('Target date must be after start date'),
                'start_date': _('Start date must be before target date'),
            })

        # Check that the referenced 'address' matches the correct 'company'
        if self.company and self.address:
            if self.address.company != self.company:
                raise ValidationError({
                    'address': _('Address does not match selected company')
                })

    def clean_line_item(self, line):
        """Clean a line item for this order.

        Used when duplicating an existing line item,
        to ensure it is 'fresh'.
        """
        line.pk = None
        line.target_date = None
        line.order = self

    def report_context(self) -> BaseOrderReportContext:
        """Generate context data for the reporting interface."""
        return {
            'description': self.description,
            'extra_lines': self.extra_lines,
            'lines': self.lines,
            'order': self,
            'reference': self.reference,
            'title': str(self),
        }

    @classmethod
    def overdue_filter(cls):
        """A generic implementation of an 'overdue' filter for the Model class.

        It requires any subclasses to implement the get_status_class() class method
        """
        today = InvenTree.helpers.current_date()
        return (
            Q(status__in=cls.get_status_class().OPEN)
            & ~Q(target_date=None)
            & Q(target_date__lt=today)
        )

    @property
    def is_overdue(self):
        """Method to determine if this order is overdue.

        Makes use of the overdue_filter() method to avoid code duplication
        """
        return (
            self.__class__.objects.filter(pk=self.pk)
            .filter(self.__class__.overdue_filter())
            .exists()
        )

    description = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Order description (optional)'),
    )

    project_code = models.ForeignKey(
        common_models.ProjectCode,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Project Code'),
        help_text=_('Select project code for this order'),
    )

    link = InvenTreeURLField(
        blank=True,
        verbose_name=_('Link'),
        help_text=_('Link to external page'),
        max_length=2000,
    )

    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Start date'),
        help_text=_('Scheduled start date for this order'),
    )

    target_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Target Date'),
        help_text=_(
            'Expected date for order delivery. Order will be overdue after this date.'
        ),
    )

    creation_date = models.DateField(
        blank=True, null=True, verbose_name=_('Creation Date')
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('Created By'),
    )

    issue_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Issue Date'),
        help_text=_('Date order was issued'),
    )

    responsible = models.ForeignKey(
        UserModels.Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_('User or group responsible for this order'),
        verbose_name=_('Responsible'),
        related_name='+',
    )

    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Contact'),
        help_text=_('Point of contact for this order'),
        related_name='+',
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Address'),
        help_text=_('Company address for this order'),
        related_name='+',
    )

    @classmethod
    def get_status_class(cls):
        """Return the enumeration class which represents the 'status' field for this model."""
        raise NotImplementedError(f'get_status_class() not implemented for {__class__}')


class PurchaseOrder(TotalPriceMixin, Order):
    """A PurchaseOrder represents goods shipped inwards from an external supplier.

    Attributes:
        supplier: Reference to the company supplying the goods in the order
        supplier_reference: Optional field for supplier order reference code
        received_by: User that received the goods
        target_date: Expected delivery target date for PurchaseOrder completion (optional)
    """

    REFERENCE_PATTERN_SETTING = 'PURCHASEORDER_REFERENCE_PATTERN'
    REQUIRE_RESPONSIBLE_SETTING = 'PURCHASEORDER_REQUIRE_RESPONSIBLE'
    STATUS_CLASS = PurchaseOrderStatus
    UNLOCK_SETTING = 'PURCHASEORDER_EDIT_COMPLETED_ORDERS'

    class Meta:
        """Model meta options."""

        verbose_name = _('Purchase Order')

    def clean_line_item(self, line):
        """Clean a line item for this PurchaseOrder."""
        super().clean_line_item(line)
        line.received = 0

    def report_context(self) -> PurchaseOrderReportContext:
        """Return report context data for this PurchaseOrder."""
        return {**super().report_context(), 'supplier': self.supplier}

    def get_absolute_url(self) -> str:
        """Get the 'web' URL for this order."""
        return pui_url(f'/purchasing/purchase-order/{self.pk}')

    @staticmethod
    def get_api_url() -> str:
        """Return the API URL associated with the PurchaseOrder model."""
        return reverse('api-po-list')

    @classmethod
    def get_status_class(cls):
        """Return the PurchaseOrderStatus class."""
        return PurchaseOrderStatusGroups

    @classmethod
    def api_defaults(cls, request=None):
        """Return default values for this model when issuing an API OPTIONS request."""
        defaults = {
            'reference': order.validators.generate_next_purchase_order_reference()
        }

        return defaults

    @classmethod
    def barcode_model_type_code(cls) -> str:
        """Return the associated barcode model type code for this model."""
        return 'PO'

    def subscribed_users(self) -> list[User]:
        """Return a list of users subscribed to this PurchaseOrder.

        By this, we mean users to are interested in any of the parts associated with this order.
        """
        subscribed_users = set()

        for line in self.lines.all():
            if line.part and line.part.part:
                # Add the part to the list of subscribed users
                for user in line.part.part.get_subscribers():
                    subscribed_users.add(user)

        return list(subscribed_users)

    def __str__(self):
        """Render a string representation of this PurchaseOrder."""
        return f'{self.reference} - {self.supplier.name if self.supplier else _("deleted")}'

    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        verbose_name=_('Reference'),
        help_text=_('Order reference'),
        default=order.validators.generate_next_purchase_order_reference,
        validators=[order.validators.validate_purchase_order_reference],
    )

    status = InvenTreeCustomStatusModelField(
        default=PurchaseOrderStatus.PENDING.value,
        choices=PurchaseOrderStatus.items(),
        status_class=PurchaseOrderStatus,
        verbose_name=_('Status'),
        help_text=_('Purchase order status'),
    )

    @property
    def status_text(self):
        """Return the text representation of the status field."""
        return PurchaseOrderStatus.text(self.status)

    supplier = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_supplier': True},
        related_name='purchase_orders',
        verbose_name=_('Supplier'),
        help_text=_('Company from which the items are being ordered'),
    )

    @property
    def company(self):
        """Accessor helper for Order base class."""
        return self.supplier

    supplier_reference = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Supplier Reference'),
        help_text=_('Supplier order reference code'),
    )

    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('received by'),
    )

    complete_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Completion Date'),
        help_text=_('Date order was completed'),
    )

    destination = TreeForeignKey(
        'stock.StockLocation',
        on_delete=models.SET_NULL,
        related_name='purchase_orders',
        blank=True,
        null=True,
        verbose_name=_('Destination'),
        help_text=_('Destination for received items'),
    )

    @transaction.atomic
    def add_line_item(
        self,
        supplier_part,
        quantity,
        group: bool = True,
        reference: str = '',
        purchase_price=None,
        destination=None,
    ):
        """Add a new line item to this purchase order.

        This function will check that:
        * The supplier part matches the supplier specified for this purchase order
        * The quantity is greater than zero

        Arguments:
            supplier_part: The supplier_part to add
            quantity : The number of items to add
            group (bool, optional): If True, this new quantity will be added to an existing line item for the same supplier_part (if it exists). Defaults to True.
            reference (str, optional): Reference to item. Defaults to ''.
            purchase_price (optional): Price of item. Defaults to None.
            destination (optional): Destination for item. Defaults to None.

        Returns:
            The newly created PurchaseOrderLineItem instance

        Raises:
            ValidationError: quantity is smaller than 0
            ValidationError: quantity is not type int
            ValidationError: supplier is not supplier of purchase order
        """
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValidationError({
                    'quantity': _('Quantity must be greater than zero')
                })
        except ValueError:
            raise ValidationError({'quantity': _('Invalid quantity provided')})

        if supplier_part.supplier != self.supplier:
            raise ValidationError({
                'supplier': _('Part supplier must match PO supplier')
            })

        if group:
            # Check if there is already a matching line item (for this PurchaseOrder)
            matches = self.lines.filter(part=supplier_part)

            if matches.count() > 0:
                line = matches.first()

                # update quantity and price
                quantity_new = line.quantity + quantity
                line.quantity = quantity_new
                supplier_price = supplier_part.get_price(quantity_new)

                if line.purchase_price and supplier_price:
                    line.purchase_price = supplier_price / quantity_new

                line.save()

                return line

        line = PurchaseOrderLineItem(
            order=self,
            part=supplier_part,
            quantity=quantity,
            reference=reference,
            purchase_price=purchase_price,
            destination=destination,
        )

        line.save()

        return line

    # region state changes
    def _action_place(self, *args, **kwargs):
        """Marks the PurchaseOrder as PLACED.

        Order must be currently PENDING.
        """
        if self.can_issue:
            self.status = PurchaseOrderStatus.PLACED.value
            self.issue_date = InvenTree.helpers.current_date()
            self.save()

            trigger_event(PurchaseOrderEvents.PLACED, id=self.pk)

            # Notify users that the order has been placed
            notify_responsible(
                self,
                PurchaseOrder,
                exclude=self.created_by,
                content=InvenTreeNotificationBodies.NewOrder,
                extra_users=self.subscribed_users(),
            )

    def _action_complete(self, *args, **kwargs):
        """Marks the PurchaseOrder as COMPLETE.

        Order must be currently PLACED.
        """
        if self.status == PurchaseOrderStatus.PLACED:
            self.status = PurchaseOrderStatus.COMPLETE.value
            self.complete_date = InvenTree.helpers.current_date()

            self.save()

            unique_parts = set()

            # Schedule pricing update for any referenced parts
            for line in self.lines.all().prefetch_related('part__part'):
                # Ensure we only check 'unique' parts
                if line.part and line.part.part:
                    unique_parts.add(line.part.part)

            for part in unique_parts:
                part.schedule_pricing_update(create=True, refresh=False)

            trigger_event(PurchaseOrderEvents.COMPLETED, id=self.pk)

    @transaction.atomic
    def issue_order(self):
        """Equivalent to 'place_order'."""
        return self.place_order()

    @property
    def can_issue(self) -> bool:
        """Return True if this order can be issued."""
        return self.status in [
            PurchaseOrderStatus.PENDING.value,
            PurchaseOrderStatus.ON_HOLD.value,
        ]

    @transaction.atomic
    def place_order(self):
        """Attempt to transition to PLACED status."""
        return self.handle_transition(
            self.status, PurchaseOrderStatus.PLACED.value, self, self._action_place
        )

    @transaction.atomic
    def complete_order(self):
        """Attempt to transition to COMPLETE status."""
        return self.handle_transition(
            self.status, PurchaseOrderStatus.COMPLETE.value, self, self._action_complete
        )

    @transaction.atomic
    def hold_order(self):
        """Attempt to transition to ON_HOLD status."""
        return self.handle_transition(
            self.status, PurchaseOrderStatus.ON_HOLD.value, self, self._action_hold
        )

    @transaction.atomic
    def cancel_order(self):
        """Attempt to transition to CANCELLED status."""
        return self.handle_transition(
            self.status, PurchaseOrderStatus.CANCELLED.value, self, self._action_cancel
        )

    @property
    def is_pending(self) -> bool:
        """Return True if the PurchaseOrder is 'pending'."""
        return self.status == PurchaseOrderStatus.PENDING.value

    @property
    def is_open(self) -> bool:
        """Return True if the PurchaseOrder is 'open'."""
        return self.status in PurchaseOrderStatusGroups.OPEN

    @property
    def can_cancel(self) -> bool:
        """A PurchaseOrder can only be cancelled under the following circumstances.

        - Status is PLACED
        - Status is PENDING (or ON_HOLD)
        """
        return self.status in PurchaseOrderStatusGroups.OPEN

    def _action_cancel(self, *args, **kwargs):
        """Marks the PurchaseOrder as CANCELLED."""
        if self.can_cancel:
            self.status = PurchaseOrderStatus.CANCELLED.value
            self.save()

            trigger_event(PurchaseOrderEvents.CANCELLED, id=self.pk)

            # Notify users that the order has been canceled
            notify_responsible(
                self,
                PurchaseOrder,
                exclude=self.created_by,
                content=InvenTreeNotificationBodies.OrderCanceled,
                extra_users=self.subscribed_users(),
            )

    @property
    def can_hold(self) -> bool:
        """Return True if this order can be placed on hold."""
        return self.status in [
            PurchaseOrderStatus.PENDING.value,
            PurchaseOrderStatus.PLACED.value,
        ]

    def _action_hold(self, *args, **kwargs):
        """Mark this purchase order as 'on hold'."""
        if self.can_hold:
            self.status = PurchaseOrderStatus.ON_HOLD.value
            self.save()

            trigger_event(PurchaseOrderEvents.HOLD, id=self.pk)

    # endregion

    def pending_line_items(self) -> QuerySet:
        """Return a list of pending line items for this order.

        Any line item where 'received' < 'quantity' will be returned.
        """
        return self.lines.filter(quantity__gt=F('received'))

    def completed_line_items(self) -> QuerySet:
        """Return a list of completed line items against this order."""
        return self.lines.filter(quantity__lte=F('received'))

    @property
    def line_count(self) -> int:
        """Return the total number of line items associated with this order."""
        return self.lines.count()

    @property
    def completed_line_count(self) -> int:
        """Return the number of complete line items associated with this order."""
        return self.completed_line_items().count()

    @property
    def pending_line_count(self) -> int:
        """Return the number of pending line items associated with this order."""
        return self.pending_line_items().count()

    @property
    def is_complete(self) -> bool:
        """Return True if all line items have been received."""
        return self.pending_line_items().count() == 0

    @transaction.atomic
    def receive_line_items(
        self, location, items: list, user: User, **kwargs
    ) -> QuerySet:
        """Receive multiple line items against this PurchaseOrder.

        Arguments:
            location: The StockLocation to receive the items into
            items: A list of line item IDs and quantities to receive
            user: The User performing the action

        Returns:
            A QuerySet of the newly created StockItem objects

        The 'items' list values contain:
            line_item: The PurchaseOrderLineItem instance
            quantity: The quantity of items to receive
            location: The location to receive the item into (optional)
            status: The 'status' of the item
            barcode: Optional barcode for the item (optional)
            batch_code: Optional batch code for the item (optional)
            expiry_date: Optional expiry date for the item (optional)
            serials: Optional list of serial numbers (optional)
            note: Optional notes for the item (optional)
        """
        if self.status != PurchaseOrderStatus.PLACED:
            raise ValidationError(
                "Lines can only be received against an order marked as 'PLACED'"
            )

        # List of stock items which have been created
        stock_items: list[stock.models.StockItem] = []

        # List of stock items to bulk create
        bulk_create_items: list[stock.models.StockItem] = []

        # List of tracking entries to create
        tracking_entries: list[stock.models.StockItemTracking] = []

        # List of line items to update
        line_items_to_update: list[PurchaseOrderLineItem] = []

        convert_purchase_price = get_global_setting('PURCHASEORDER_CONVERT_CURRENCY')
        default_currency = currency_code_default()

        # Prefetch line item objects for DB efficiency
        line_items_ids = [item['line_item'].pk for item in items]

        # Cache the custom status options for the StockItem model
        custom_stock_status_values = stock.models.StockItem.STATUS_CLASS.custom_values()

        line_items = PurchaseOrderLineItem.objects.filter(
            pk__in=line_items_ids
        ).prefetch_related('part', 'part__part', 'order')

        # Map order line items to their corresponding stock items
        line_item_map = {line.pk: line for line in line_items}

        # Before we continue, validate that each line item is valid
        # We validate this here because it is far more efficient,
        # after we have fetched *all* line items in a single DB query
        for line_item in line_item_map.values():
            if line_item.order != self:
                raise ValidationError({_('Line item does not match purchase order')})

            if not line_item.part or not line_item.part.part:
                raise ValidationError({_('Line item is missing a linked part')})

        for item in items:
            # Extract required information
            line_item_id = item['line_item'].pk

            line = line_item_map[line_item_id]

            quantity = item['quantity']
            barcode = item.get('barcode', '')

            try:
                if quantity < 0:
                    raise ValidationError({
                        'quantity': _('Quantity must be a positive number')
                    })
                quantity = InvenTree.helpers.clean_decimal(quantity)
            except TypeError:
                raise ValidationError({'quantity': _('Invalid quantity provided')})

            supplier_part = line.part

            if not supplier_part:
                logger.warning(
                    'Line item %s is missing a linked supplier part', line.pk
                )
                continue

            base_part = supplier_part.part

            stock_location = item.get('location', location) or line.get_destination()

            # Calculate the received quantity in base part units
            stock_quantity = supplier_part.base_quantity(quantity)

            # Calculate unit purchase price (in base units)
            if line.purchase_price:
                purchase_price = line.purchase_price / supplier_part.base_quantity(1)

                if convert_purchase_price:
                    purchase_price = convert_money(purchase_price, default_currency)
            else:
                purchase_price = None

            # Extract optional serial numbers
            serials = item.get('serials', None)

            if serials and type(serials) is list and len(serials) > 0:
                serialize = True
            else:
                serialize = False
                serials = [None]

            # Construct dataset for creating a new StockItem instances
            stock_data = {
                'part': supplier_part.part,
                'supplier_part': supplier_part,
                'purchase_order': self,
                'purchase_price': purchase_price,
                'location': stock_location,
                'quantity': 1 if serialize else stock_quantity,
                'batch': item.get('batch_code', ''),
                'expiry_date': item.get('expiry_date', None),
                'notes': item.get('note', '') or item.get('notes', ''),
                'packaging': item.get('packaging') or supplier_part.packaging,
            }

            # Extract the "status" field
            status = item.get('status', StockStatus.OK.value)

            # Check linked build order
            # This is for receiving against an *external* build order
            if build_order := line.build_order:
                if not build_order.external:
                    raise ValidationError(
                        'Cannot receive items against an internal build order'
                    )

                if build_order.part != base_part:
                    raise ValidationError(
                        'Cannot receive items against a build order for a different part'
                    )

                if not stock_location and build_order.destination:
                    # Override with the build order destination (if not specified)
                    stock_data['location'] = stock_location = build_order.destination

                if build_order.active:
                    # An 'active' build order marks the items as "in production"
                    stock_data['build'] = build_order
                    stock_data['is_building'] = True
                elif build_order.status == BuildStatus.COMPLETE:
                    # A 'completed' build order marks the items as "completed"
                    stock_data['build'] = build_order
                    stock_data['is_building'] = False

                    # Increase the 'completed' quantity for the build order
                    build_order.completed += stock_quantity
                    build_order.save()
                elif build_order.status == BuildStatus.CANCELLED:
                    # A 'cancelled' build order is ignored
                    pass
                else:
                    # Un-handled state - raise an error
                    raise ValidationError(
                        "Cannot receive items against a build order in state '{build_order.status}'"
                    )

            # Now, create the new stock items
            if serialize:
                new_items = stock.models.StockItem._create_serial_numbers(
                    serials=serials, **stock_data
                )

                for item in new_items:
                    item.set_status(status, custom_values=custom_stock_status_values)
                    stock_items.append(item)

            else:
                new_item = stock.models.StockItem(
                    **stock_data,
                    serial='',
                    tree_id=stock.models.StockItem.getNextTreeID(),
                    parent=None,
                    level=0,
                    lft=1,
                    rght=2,
                )

                new_item.set_status(status, custom_values=custom_stock_status_values)

                if barcode:
                    new_item.assign_barcode(barcode_data=barcode, save=False)

                bulk_create_items.append(new_item)

            # Update the line item quantity
            line.received += quantity
            line_items_to_update.append(line)

        # Bulk create new stock items
        if len(bulk_create_items) > 0:
            stock.models.StockItem.objects.bulk_create(bulk_create_items)

            # Fetch them back again
            tree_ids = [item.tree_id for item in bulk_create_items]

            created_items = stock.models.StockItem.objects.filter(
                tree_id__in=tree_ids, level=0, lft=1, rght=2, purchase_order=self
            ).prefetch_related('location')

            stock_items.extend(created_items)

        # Generate a new tracking entry for each stock item
        for item in stock_items:
            tracking_entries.append(
                item.add_tracking_entry(
                    StockHistoryCode.RECEIVED_AGAINST_PURCHASE_ORDER,
                    user,
                    deltas={
                        'location': item.location.pk if item.location else None,
                        'purchaseorder': self.pk,
                        'quantity': float(item.quantity),
                    },
                    commit=False,
                )
            )

        # Bulk create new tracking entries for each item
        stock.models.StockItemTracking.objects.bulk_create(tracking_entries)

        # Update received quantity for each line item
        PurchaseOrderLineItem.objects.bulk_update(line_items_to_update, ['received'])

        # Trigger an event for any interested plugins
        trigger_event(
            PurchaseOrderEvents.ITEM_RECEIVED,
            order_id=self.pk,
            item_ids=[item.pk for item in stock_items],
        )

        # Check to auto-complete the PurchaseOrder
        if (
            get_global_setting('PURCHASEORDER_AUTO_COMPLETE', True)
            and self.pending_line_count == 0
        ):
            self.received_by = user
            self.complete_order()

        # Send notification
        notify_responsible(
            self,
            PurchaseOrder,
            exclude=user,
            content=InvenTreeNotificationBodies.ItemsReceived,
            extra_users=line.part.part.get_subscribers(),
        )

        # Return a list of the created stock items
        return stock.models.StockItem.objects.filter(
            pk__in=[item.pk for item in stock_items]
        )

    @transaction.atomic
    def receive_line_item(
        self, line, location, quantity, user, status=StockStatus.OK.value, **kwargs
    ):
        """Receive a line item (or partial line item) against this PurchaseOrder.

        Arguments:
            line: The PurchaseOrderLineItem to receive against
            location: The StockLocation to receive the item into
            quantity: The quantity to receive
            user: The User performing the action
            status: The StockStatus to assign to the item (default: StockStatus.OK)

        Keyword Arguments:
            batch_code: Optional batch code for the new StockItem
            serials: Optional list of serial numbers to assign to the new StockItem(s)
            notes: Optional notes field for the StockItem
            packaging: Optional packaging field for the StockItem
            barcode: Optional barcode field for the StockItem
            notify: If true, notify users of received items

        Raises:
            ValidationError: If the quantity is negative or otherwise invalid
            ValidationError: If the order is not in the 'PLACED' state
        """
        self.receive_line_items(
            location,
            [
                {
                    'line_item': line,
                    'quantity': quantity,
                    'location': location,
                    'status': status,
                    **kwargs,
                }
            ],
            user,
        )


class SalesOrder(TotalPriceMixin, Order):
    """A SalesOrder represents a list of goods shipped outwards to a customer."""

    REFERENCE_PATTERN_SETTING = 'SALESORDER_REFERENCE_PATTERN'
    REQUIRE_RESPONSIBLE_SETTING = 'SALESORDER_REQUIRE_RESPONSIBLE'
    STATUS_CLASS = SalesOrderStatus
    UNLOCK_SETTING = 'SALESORDER_EDIT_COMPLETED_ORDERS'

    class Meta:
        """Model meta options."""

        verbose_name = _('Sales Order')

    def clean_line_item(self, line):
        """Clean a line item for this SalesOrder."""
        super().clean_line_item(line)
        line.shipped = 0

    def report_context(self) -> SalesOrderReportContext:
        """Generate report context data for this SalesOrder."""
        return {**super().report_context(), 'customer': self.customer}

    def get_absolute_url(self) -> str:
        """Get the 'web' URL for this order."""
        return pui_url(f'/sales/sales-order/{self.pk}')

    @staticmethod
    def get_api_url() -> str:
        """Return the API URL associated with the SalesOrder model."""
        return reverse('api-so-list')

    @classmethod
    def get_status_class(cls):
        """Return the SalesOrderStatus class."""
        return SalesOrderStatusGroups

    @classmethod
    def api_defaults(cls, request=None) -> dict:
        """Return default values for this model when issuing an API OPTIONS request."""
        defaults = {'reference': order.validators.generate_next_sales_order_reference()}

        return defaults

    @classmethod
    def barcode_model_type_code(cls) -> str:
        """Return the associated barcode model type code for this model."""
        return 'SO'

    def subscribed_users(self) -> list[User]:
        """Return a list of users subscribed to this SalesOrder.

        By this, we mean users to are interested in any of the parts associated with this order.
        """
        subscribed_users = set()

        for line in self.lines.all():
            if line.part:
                # Add the part to the list of subscribed users
                for user in line.part.get_subscribers():
                    subscribed_users.add(user)

        return list(subscribed_users)

    def __str__(self):
        """Render a string representation of this SalesOrder."""
        return f'{self.reference} - {self.customer.name if self.customer else _("deleted")}'

    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        verbose_name=_('Reference'),
        help_text=_('Order reference'),
        default=order.validators.generate_next_sales_order_reference,
        validators=[order.validators.validate_sales_order_reference],
    )

    customer = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_customer': True},
        related_name='return_orders',
        verbose_name=_('Customer'),
        help_text=_('Company to which the items are being sold'),
    )

    @property
    def company(self):
        """Accessor helper for Order base."""
        return self.customer

    status = InvenTreeCustomStatusModelField(
        default=SalesOrderStatus.PENDING.value,
        choices=SalesOrderStatus.items(),
        status_class=SalesOrderStatus,
        verbose_name=_('Status'),
        help_text=_('Sales order status'),
    )

    @property
    def status_text(self) -> str:
        """Return the text representation of the status field."""
        return SalesOrderStatus.text(self.status)

    customer_reference = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Customer Reference '),
        help_text=_('Customer order reference code'),
    )

    shipment_date = models.DateField(
        blank=True, null=True, verbose_name=_('Shipment Date')
    )

    shipped_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('shipped by'),
    )

    @property
    def is_pending(self) -> bool:
        """Return True if this order is 'pending'."""
        return self.status == SalesOrderStatus.PENDING

    @property
    def is_open(self) -> bool:
        """Return True if this order is 'open' (either 'pending' or 'in_progress')."""
        return self.status in SalesOrderStatusGroups.OPEN

    @property
    def stock_allocations(self) -> QuerySet:
        """Return a queryset containing all allocations for this order."""
        return SalesOrderAllocation.objects.filter(
            line__in=[line.pk for line in self.lines.all()]
        )

    def is_fully_allocated(self) -> bool:
        """Return True if all line items are fully allocated."""
        return all(line.is_fully_allocated() for line in self.lines.all())

    def is_overallocated(self) -> bool:
        """Return true if any lines in the order are over-allocated."""
        return any(line.is_overallocated() for line in self.lines.all())

    def is_completed(self) -> bool:
        """Check if this order is "shipped" (all line items delivered).

        Note: Any "virtual" parts are ignored in this calculation.
        """
        lines = self.lines.all().filter(part__virtual=False)

        return all(line.is_completed() for line in lines)

    def can_complete(
        self, raise_error: bool = False, allow_incomplete_lines: bool = False
    ) -> bool:
        """Test if this SalesOrder can be completed.

        Arguments:
            raise_error: If True, raise ValidationError if the order cannot be completed
            allow_incomplete_lines: If True, allow incomplete line items when completing the order

        Raises:
            ValidationError: If the order cannot be completed, and raise_error is True
        """
        try:
            if self.status == SalesOrderStatus.COMPLETE.value:
                raise ValidationError(_('Order is already complete'))

            if self.status == SalesOrderStatus.CANCELLED.value:
                raise ValidationError(_('Order is already cancelled'))

            # Only an open order can be marked as shipped
            if self.is_open and not self.is_completed:
                raise ValidationError(_('Only an open order can be marked as complete'))

            if self.pending_shipment_count > 0:
                raise ValidationError(
                    _('Order cannot be completed as there are incomplete shipments')
                )

            if self.pending_allocation_count > 0:
                raise ValidationError(
                    _('Order cannot be completed as there are incomplete allocations')
                )

            if not allow_incomplete_lines:
                pending_lines = self.pending_line_items().exclude(part__virtual=True)

                if pending_lines.count() > 0:
                    raise ValidationError(
                        _(
                            'Order cannot be completed as there are incomplete line items'
                        )
                    )

        except ValidationError as e:
            if raise_error:
                raise e
            else:
                return False

        return True

    # region state changes
    def place_order(self):
        """Deprecated version of 'issue_order'."""
        self.issue_order()

    @property
    def can_issue(self) -> bool:
        """Return True if this order can be issued."""
        return self.status in [
            SalesOrderStatus.PENDING.value,
            SalesOrderStatus.ON_HOLD.value,
        ]

    def _action_place(self, *args, **kwargs):
        """Change this order from 'PENDING' to 'IN_PROGRESS'."""
        if self.can_issue:
            self.status = SalesOrderStatus.IN_PROGRESS.value
            self.issue_date = InvenTree.helpers.current_date()
            self.save()

            trigger_event(SalesOrderEvents.ISSUED, id=self.pk)

            # Notify users that the order has been placed
            notify_responsible(
                self,
                SalesOrder,
                exclude=self.created_by,
                content=InvenTreeNotificationBodies.NewOrder,
                extra_users=self.subscribed_users(),
            )

    @property
    def can_hold(self) -> bool:
        """Return True if this order can be placed on hold."""
        return self.status in [
            SalesOrderStatus.PENDING.value,
            SalesOrderStatus.IN_PROGRESS.value,
        ]

    def _action_hold(self, *args, **kwargs):
        """Mark this sales order as 'on hold'."""
        if self.can_hold:
            self.status = SalesOrderStatus.ON_HOLD.value
            self.save()

            trigger_event(SalesOrderEvents.HOLD, id=self.pk)

    @transaction.atomic
    def _action_complete(self, *args, **kwargs):
        """Mark this order as "complete."""
        user = kwargs.pop('user', None)

        if not self.can_complete(**kwargs):
            return False

        bypass_shipped = InvenTree.helpers.str2bool(
            get_global_setting('SALESORDER_SHIP_COMPLETE')
        )

        # Update line items
        for line in self.lines.all():
            # Mark any "virtual" parts as shipped at this point
            if line.part and line.part.virtual and line.shipped != line.quantity:
                line.shipped = line.quantity
                line.save()

            if line.part:
                line.part.schedule_pricing_update(create=True)

        if bypass_shipped or self.status == SalesOrderStatus.SHIPPED:
            self.status = SalesOrderStatus.COMPLETE.value
        else:
            self.status = SalesOrderStatus.SHIPPED.value

        if self.shipment_date is None:
            self.shipped_by = user
            self.shipment_date = InvenTree.helpers.current_date()

        self.save()

        trigger_event(SalesOrderEvents.COMPLETED, id=self.pk)

        return True

    @property
    def can_cancel(self) -> bool:
        """Return True if this order can be cancelled."""
        return self.is_open

    def _action_cancel(self, *args, **kwargs):
        """Cancel this order (only if it is "open").

        Executes:
        - Mark the order as 'cancelled'
        - Delete any StockItems which have been allocated
        """
        if not self.can_cancel:
            return False

        self.status = SalesOrderStatus.CANCELLED.value
        self.save()

        for line in self.lines.all():
            for allocation in line.allocations.all():
                allocation.delete()

        trigger_event(SalesOrderEvents.CANCELLED, id=self.pk)

        # Notify users that the order has been canceled
        notify_responsible(
            self,
            SalesOrder,
            exclude=self.created_by,
            content=InvenTreeNotificationBodies.OrderCanceled,
            extra_users=self.subscribed_users(),
        )

        return True

    @transaction.atomic
    def issue_order(self):
        """Attempt to transition to IN_PROGRESS status."""
        return self.handle_transition(
            self.status, SalesOrderStatus.IN_PROGRESS.value, self, self._action_place
        )

    @transaction.atomic
    def ship_order(self, user, **kwargs):
        """Attempt to transition to SHIPPED status."""
        return self.handle_transition(
            self.status,
            SalesOrderStatus.SHIPPED.value,
            self,
            self._action_complete,
            user=user,
            **kwargs,
        )

    @transaction.atomic
    def complete_order(self, user, **kwargs):
        """Attempt to transition to COMPLETED status."""
        return self.handle_transition(
            self.status,
            SalesOrderStatus.COMPLETE.value,
            self,
            self._action_complete,
            user=user,
            **kwargs,
        )

    @transaction.atomic
    def hold_order(self):
        """Attempt to transition to ON_HOLD status."""
        return self.handle_transition(
            self.status, SalesOrderStatus.ON_HOLD.value, self, self._action_hold
        )

    @transaction.atomic
    def cancel_order(self):
        """Attempt to transition to CANCELLED status."""
        return self.handle_transition(
            self.status, SalesOrderStatus.CANCELLED.value, self, self._action_cancel
        )

    # endregion

    @property
    def line_count(self) -> int:
        """Return the total number of lines associated with this order."""
        return self.lines.count()

    def completed_line_items(self) -> QuerySet:
        """Return a queryset of the completed line items for this order."""
        return self.lines.filter(shipped__gte=F('quantity'))

    def pending_line_items(self) -> QuerySet:
        """Return a queryset of the pending line items for this order.

        Note: We exclude "virtual" parts here, as they do not get allocated
        """
        return self.lines.filter(shipped__lt=F('quantity')).exclude(part__virtual=True)

    @property
    def completed_line_count(self) -> int:
        """Return the number of completed lines for this order."""
        return self.completed_line_items().count()

    @property
    def pending_line_count(self) -> int:
        """Return the number of pending (incomplete) lines associated with this order."""
        return self.pending_line_items().count()

    def completed_shipments(self) -> QuerySet:
        """Return a queryset of the completed shipments for this order."""
        return self.shipments.exclude(shipment_date=None)

    def pending_shipments(self) -> QuerySet:
        """Return a queryset of the pending shipments for this order."""
        return self.shipments.filter(shipment_date=None)

    def allocations(self) -> QuerySet:
        """Return a queryset of all allocations for this order."""
        return SalesOrderAllocation.objects.filter(line__order=self)

    def pending_allocations(self) -> QuerySet:
        """Return a queryset of any pending allocations for this order.

        Allocations are pending if:

        a) They are not associated with a SalesOrderShipment
        b) The linked SalesOrderShipment has not been shipped
        """
        Q1 = Q(shipment=None)
        Q2 = Q(shipment__shipment_date=None)

        return self.allocations().filter(Q1 | Q2).distinct()

    @property
    def shipment_count(self) -> int:
        """Return the total number of shipments associated with this order."""
        return self.shipments.count()

    @property
    def completed_shipment_count(self) -> int:
        """Return the number of completed shipments associated with this order."""
        return self.completed_shipments().count()

    @property
    def pending_shipment_count(self) -> int:
        """Return the number of pending shipments associated with this order."""
        return self.pending_shipments().count()

    @property
    def pending_allocation_count(self) -> int:
        """Return the number of pending (non-shipped) allocations."""
        return self.pending_allocations().count()


@receiver(post_save, sender=SalesOrder, dispatch_uid='sales_order_post_save')
def after_save_sales_order(sender, instance: SalesOrder, created: bool, **kwargs):
    """Callback function to be executed after a SalesOrder is saved.

    - If the SALESORDER_DEFAULT_SHIPMENT setting is enabled, create a default shipment
    - Ignore if the database is not ready for access
    - Ignore if data import is active
    """
    if (
        not InvenTree.ready.canAppAccessDatabase(allow_test=True)
        or InvenTree.ready.isImportingData()
    ):
        return

    if created:
        # A new SalesOrder has just been created

        if get_global_setting('SALESORDER_DEFAULT_SHIPMENT'):
            # Create default shipment
            SalesOrderShipment.objects.create(order=instance, reference='1')


class OrderLineItem(InvenTree.models.InvenTreeMetadataModel):
    """Abstract model for an order line item.

    Attributes:
        quantity: Number of items
        reference: Reference text (e.g. customer reference) for this line item
        project_code: Project code associated with this line item (optional)
        note: Annotation for the item
        target_date: An (optional) date for expected shipment of this line item.
    """

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    def save(self, *args, **kwargs):
        """Custom save method for the OrderLineItem model.

        Calls save method on the linked order
        """
        if self.order and self.order.check_locked():
            raise ValidationError({
                'non_field_errors': _('The order is locked and cannot be modified')
            })

        update_order = kwargs.pop('update_order', True)

        super().save(*args, **kwargs)
        if update_order and self.order:
            self.order.save()

    def delete(self, *args, **kwargs):
        """Custom delete method for the OrderLineItem model.

        Calls save method on the linked order
        """
        if self.order and self.order.check_locked():
            raise ValidationError({
                'non_field_errors': _('The order is locked and cannot be modified')
            })

        super().delete(*args, **kwargs)
        self.order.save()

    quantity = RoundingDecimalField(
        verbose_name=_('Quantity'),
        help_text=_('Item quantity'),
        default=1,
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
    )

    @property
    def total_line_price(self):
        """Return the total price for this line item."""
        if self.price:
            return self.quantity * self.price

    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Reference'),
        help_text=_('Line item reference'),
    )

    notes = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Line item notes'),
    )

    link = InvenTreeURLField(
        blank=True,
        verbose_name=_('Link'),
        help_text=_('Link to external page'),
        max_length=2000,
    )

    target_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Target Date'),
        help_text=_(
            'Target date for this line item (leave blank to use the target date from the order)'
        ),
    )

    project_code = models.ForeignKey(
        common_models.ProjectCode,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Project Code'),
        help_text=_('Select project code for this order'),
    )


class OrderExtraLine(OrderLineItem):
    """Abstract Model for a single ExtraLine in a Order.

    Attributes:
        price: The unit sale price for this OrderLineItem
    """

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    description = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Line item description (optional)'),
    )

    context = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Context'),
        help_text=_('Additional context for this line'),
    )

    price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=6,
        null=True,
        blank=True,
        allow_negative=True,
        verbose_name=_('Price'),
        help_text=_('Unit price'),
    )


class PurchaseOrderLineItem(OrderLineItem):
    """Model for a purchase order line item.

    Attributes:
        order: Reference to a PurchaseOrder object
        part: Reference to a SupplierPart object
        received: Number of items received
        purchase_price: Unit purchase price for this line item
        build_order: Link to an external BuildOrder to be fulfilled by this line item
        destination: Destination for received items
    """

    class Meta:
        """Model meta options."""

        verbose_name = _('Purchase Order Line Item')

    # Filter for determining if a particular PurchaseOrderLineItem is overdue
    OVERDUE_FILTER = (
        Q(received__lt=F('quantity'))
        & ~Q(target_date=None)
        & Q(target_date__lt=InvenTree.helpers.current_date())
    )

    @staticmethod
    def get_api_url() -> str:
        """Return the API URL associated with the PurchaseOrderLineItem model."""
        return reverse('api-po-line-list')

    def clean(self) -> None:
        """Custom clean method for the PurchaseOrderLineItem model.

        Raises:
            ValidationError: If the SupplierPart does not match the PurchaseOrder supplier
            ValidationError: If the linked BuildOrder is not marked as external
            ValidationError: If the linked BuildOrder part does not match the line item part
        """
        super().clean()

        if self.order.supplier and self.part:
            # Supplier part *must* point to the same supplier!
            if self.part.supplier != self.order.supplier:
                raise ValidationError({'part': _('Supplier part must match supplier')})

        if self.build_order:
            if not self.build_order.external:
                raise ValidationError({
                    'build_order': _('Build order must be marked as external')
                })

            if part := self.part.part:
                if not part.assembly:
                    raise ValidationError({
                        'build_order': _(
                            'Build orders can only be linked to assembly parts'
                        )
                    })

                if self.build_order.part != self.part.part:
                    raise ValidationError({
                        'build_order': _('Build order part must match line item part')
                    })

    def __str__(self):
        """Render a string representation of a PurchaseOrderLineItem instance."""
        return '{n} x {part} - {po}'.format(
            n=decimal2string(self.quantity),
            part=self.part.SKU if self.part else 'unknown part',
            po=self.order,
        )

    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('Order'),
        help_text=_('Purchase Order'),
    )

    def get_base_part(self):
        """Return the base part.Part object for the line item.

        Note: Returns None if the SupplierPart is not set!
        """
        if self.part is None:
            return None
        return self.part.part

    part = models.ForeignKey(
        SupplierPart,
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        related_name='purchase_order_line_items',
        verbose_name=_('Part'),
        help_text=_('Supplier part'),
    )

    received = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=0,
        verbose_name=_('Received'),
        help_text=_('Number of items received'),
    )

    purchase_price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Purchase Price'),
        help_text=_('Unit purchase price'),
    )

    @property
    def price(self):
        """Return the 'purchase_price' field as 'price'."""
        return self.purchase_price

    build_order = models.ForeignKey(
        'build.Build',
        on_delete=models.SET_NULL,
        blank=True,
        related_name='external_line_items',
        limit_choices_to={'external': True},
        null=True,
        verbose_name=_('Build Order'),
        help_text=_('External Build Order to be fulfilled by this line item'),
    )

    destination = TreeForeignKey(
        'stock.StockLocation',
        on_delete=models.SET_NULL,
        verbose_name=_('Destination'),
        related_name='po_lines',
        blank=True,
        null=True,
        help_text=_('Destination for received items'),
    )

    def get_destination(self):
        """Show where the line item is or should be placed.

        1. If a destination is specified against this line item, return that.
        2. If a destination is specified against the PurchaseOrderPart, return that.
        3. If a default location is specified against the linked Part, return that.
        """
        if self.destination:
            return self.destination

        if self.order.destination:
            return self.order.destination

        if self.part and self.part.part and self.part.part.default_location:
            return self.part.part.default_location

    def remaining(self):
        """Calculate the number of items remaining to be received."""
        r = self.quantity - self.received
        return max(r, 0)

    def is_completed(self) -> bool:
        """Determine if this line item has been fully received."""
        return self.received >= self.quantity

    def update_pricing(self) -> None:
        """Update pricing information based on the supplier part data."""
        if self.part:
            price = self.part.get_price(
                self.quantity, currency=self.purchase_price_currency
            )

            if price is None or self.quantity == 0:
                return

            self.purchase_price = Decimal(price) / Decimal(self.quantity)
            self.save()


class PurchaseOrderExtraLine(OrderExtraLine):
    """Model for a single ExtraLine in a PurchaseOrder.

    Attributes:
        order: Link to the PurchaseOrder that this line belongs to
    """

    class Meta:
        """Model meta options."""

        verbose_name = _('Purchase Order Extra Line')

    @staticmethod
    def get_api_url() -> str:
        """Return the API URL associated with the PurchaseOrderExtraLine model."""
        return reverse('api-po-extra-line-list')

    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='extra_lines',
        verbose_name=_('Order'),
        help_text=_('Purchase Order'),
    )


class SalesOrderLineItem(OrderLineItem):
    """Model for a single LineItem in a SalesOrder.

    Attributes:
        order: Link to the SalesOrder that this line item belongs to
        part: Link to a Part object (may be null)
        sale_price: The unit sale price for this OrderLineItem
        shipped: The number of items which have actually shipped against this line item
    """

    class Meta:
        """Model meta options."""

        verbose_name = _('Sales Order Line Item')

    # Filter for determining if a particular SalesOrderLineItem is overdue
    OVERDUE_FILTER = (
        Q(shipped__lt=F('quantity'))
        & ~Q(target_date=None)
        & Q(target_date__lt=InvenTree.helpers.current_date())
    )

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderLineItem model."""
        return reverse('api-so-line-list')

    def clean(self) -> None:
        """Perform extra validation steps for this SalesOrderLineItem instance.

        Raises:
            ValidationError: If the linked part is not salable
        """
        super().clean()

        if self.part:
            if not self.part.salable:
                raise ValidationError({
                    'part': _('Only salable parts can be assigned to a sales order')
                })

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('Order'),
        help_text=_('Sales Order'),
    )

    part = models.ForeignKey(
        'part.Part',
        on_delete=models.SET_NULL,
        related_name='sales_order_line_items',
        null=True,
        verbose_name=_('Part'),
        help_text=_('Part'),
        limit_choices_to={'salable': True},
    )

    sale_price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Sale Price'),
        help_text=_('Unit sale price'),
    )

    @property
    def price(self):
        """Return the 'sale_price' field as 'price'."""
        return self.sale_price

    shipped = RoundingDecimalField(
        verbose_name=_('Shipped'),
        help_text=_('Shipped quantity'),
        default=0,
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
    )

    def fulfilled_quantity(self):
        """Return the total stock quantity fulfilled against this line item."""
        if not self.pk:
            return 0

        query = self.order.stock_items.filter(part=self.part).aggregate(
            fulfilled=Coalesce(Sum('quantity'), Decimal(0))
        )

        return query['fulfilled']

    def allocated_quantity(self):
        """Return the total stock quantity allocated to this LineItem.

        This is a summation of the quantity of each attached StockItem
        """
        if not self.pk:
            return 0

        query = self.allocations.aggregate(
            allocated=Coalesce(Sum('quantity'), Decimal(0))
        )

        return query['allocated']

    def is_fully_allocated(self) -> bool:
        """Return True if this line item is fully allocated."""
        # If the linked part is "virtual", then we cannot allocate stock against it
        if self.part and self.part.virtual:
            return True

        if self.order.status == SalesOrderStatus.SHIPPED:
            return self.fulfilled_quantity() >= self.quantity

        return self.allocated_quantity() >= self.quantity

    def is_overallocated(self) -> bool:
        """Return True if this line item is over allocated."""
        return self.allocated_quantity() > self.quantity

    def is_completed(self) -> bool:
        """Return True if this line item is completed (has been fully shipped)."""
        # A "virtual" part is always considered to be "completed"
        if self.part and self.part.virtual:
            return True

        return self.shipped >= self.quantity


class SalesOrderShipmentReportContext(report.mixins.BaseReportContext):
    """Context for the SalesOrderShipment model.

    Attributes:
        allocations: QuerySet of SalesOrderAllocation objects
        address: The shipping address for this shipment (or order)
        order: The associated SalesOrder object
        reference: Shipment reference string
        shipment: The SalesOrderShipment object itself
        tracking_number: Shipment tracking number string
        title: Title for the report
    """

    allocations: report.mixins.QuerySet['SalesOrderAllocation']
    order: 'SalesOrder'
    reference: str
    address: 'Address'
    shipment: 'SalesOrderShipment'
    tracking_number: str
    title: str


class SalesOrderShipment(
    InvenTree.models.InvenTreeAttachmentMixin,
    InvenTree.models.InvenTreeBarcodeMixin,
    InvenTree.models.InvenTreeNotesMixin,
    report.mixins.InvenTreeReportMixin,
    InvenTree.models.MetadataMixin,
    InvenTree.models.InvenTreeModel,
):
    """The SalesOrderShipment model represents a physical shipment made against a SalesOrder.

    - Points to a single SalesOrder object
    - Multiple SalesOrderAllocation objects point to a particular SalesOrderShipment
    - When a given SalesOrderShipment is "shipped", stock items are removed from stock

    Attributes:
        order: SalesOrder reference
        shipment_address: Shipping address for this shipment (optional)
        shipment_date: Date this shipment was "shipped" (or null)
        checked_by: User reference field indicating who checked this order
        reference: Custom reference text for this shipment (e.g. consignment number?)
        notes: Custom notes field for this shipment
    """

    @classmethod
    def barcode_model_type_code(cls):
        """Return the associated barcode model type code for this model."""
        return 'SS'

    class Meta:
        """Metaclass defines extra model options."""

        # Shipment reference must be unique for a given sales order
        unique_together = ['order', 'reference']
        verbose_name = _('Sales Order Shipment')

    def clean(self) -> None:
        """Custom clean method for the SalesOrderShipment class.

        Raises:
            ValidationError: If the shipment address does not match the customer
        """
        super().clean()

        if self.order and self.shipment_address:
            if self.shipment_address.company != self.order.customer:
                raise ValidationError({
                    'shipment_address': _('Shipment address must match the customer')
                })

    @staticmethod
    def get_api_url() -> str:
        """Return the API URL associated with the SalesOrderShipment model."""
        return reverse('api-so-shipment-list')

    def report_context(self) -> SalesOrderShipmentReportContext:
        """Generate context data for the reporting interface."""
        return {
            'allocations': self.allocations,
            'order': self.order,
            'address': self.address,
            'reference': self.reference,
            'shipment': self,
            'tracking_number': self.tracking_number,
            'title': str(self),
        }

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name='shipments',
        verbose_name=_('Order'),
        help_text=_('Sales Order'),
    )

    shipment_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Address'),
        help_text=_('Shipping address for this shipment'),
        related_name='+',
    )

    shipment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Shipment Date'),
        help_text=_('Date of shipment'),
    )

    delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Delivery Date'),
        help_text=_('Date of delivery of shipment'),
    )

    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Checked By'),
        help_text=_('User who checked this shipment'),
        related_name='+',
    )

    reference = models.CharField(
        max_length=100,
        blank=False,
        verbose_name=_('Shipment'),
        help_text=_('Shipment number'),
        default='1',
    )

    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        unique=False,
        verbose_name=_('Tracking Number'),
        help_text=_('Shipment tracking information'),
    )

    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        unique=False,
        verbose_name=_('Invoice Number'),
        help_text=_('Reference number for associated invoice'),
    )

    link = InvenTreeURLField(
        blank=True,
        verbose_name=_('Link'),
        help_text=_('Link to external page'),
        max_length=2000,
    )

    @property
    def address(self) -> Address:
        """Return the shipping address for this shipment.

        If no specific shipment address is assigned, return the address from the order.
        """
        return self.shipment_address or self.order.address

    def is_checked(self) -> bool:
        """Return True if this shipment has been checked."""
        return self.checked_by is not None

    def is_complete(self) -> bool:
        """Return True if this shipment has already been completed."""
        return self.shipment_date is not None

    def is_delivered(self) -> bool:
        """Return True if this shipment has already been delivered."""
        return self.delivery_date is not None

    def check_can_complete(self, raise_error: bool = True) -> bool:
        """Check if this shipment is able to be completed.

        Arguments:
            raise_error: If True, raise ValidationError if cannot complete
        """
        try:
            if self.shipment_date:
                # Shipment has already been sent!
                raise ValidationError(_('Shipment has already been sent'))

            if self.allocations.count() == 0:
                raise ValidationError(_('Shipment has no allocated stock items'))

            if (
                get_global_setting('SALESORDER_SHIPMENT_REQUIRES_CHECK')
                and not self.is_checked()
            ):
                raise ValidationError(
                    _('Shipment must be checked before it can be completed')
                )

        except ValidationError as e:
            if raise_error:
                raise e
            else:
                return False

        return True

    @transaction.atomic
    def complete_shipment(self, user, **kwargs):
        """Complete this particular shipment.

        Executes:
        1. Update any stock items associated with this shipment
        2. Update the "shipped" quantity of all associated line items
        3. Set the "shipment_date" to now
        """
        import order.tasks

        # Check if the shipment can be completed (throw error if not)
        self.check_can_complete()

        # Update the "shipment" date
        self.shipment_date = kwargs.get(
            'shipment_date', InvenTree.helpers.current_date()
        )
        self.shipped_by = user

        # Was a tracking number provided?
        tracking_number = kwargs.get('tracking_number')

        if tracking_number is not None:
            self.tracking_number = tracking_number

        # Was an invoice number provided?
        invoice_number = kwargs.get('invoice_number')

        if invoice_number is not None:
            self.invoice_number = invoice_number

        # Was a link provided?
        link = kwargs.get('link')

        if link is not None:
            self.link = link

        # Was a delivery date provided?
        delivery_date = kwargs.get('delivery_date')

        if delivery_date is not None:
            self.delivery_date = delivery_date

        self.save()

        # Offload the "completion" of each line item to the background worker
        # This may take some time, and we don't want to block the main thread
        InvenTree.tasks.offload_task(
            order.tasks.complete_sales_order_shipment,
            shipment_id=self.pk,
            user_id=user.pk if user else None,
            group='sales_order',
        )

        trigger_event(SalesOrderEvents.SHIPMENT_COMPLETE, id=self.pk)


class SalesOrderExtraLine(OrderExtraLine):
    """Model for a single ExtraLine in a SalesOrder.

    Attributes:
        order: Link to the SalesOrder that this line belongs to
    """

    class Meta:
        """Model meta options."""

        verbose_name = _('Sales Order Extra Line')

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderExtraLine model."""
        return reverse('api-so-extra-line-list')

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='extra_lines',
        verbose_name=_('Order'),
        help_text=_('Sales Order'),
    )


class SalesOrderAllocation(models.Model):
    """This model is used to 'allocate' stock items to a SalesOrder. Items that are "allocated" to a SalesOrder are not yet "attached" to the order, but they will be once the order is fulfilled.

    Attributes:
        line: SalesOrderLineItem reference
        shipment: SalesOrderShipment reference
        item: StockItem reference
        quantity: Quantity to take from the StockItem
    """

    class Meta:
        """Model meta options."""

        verbose_name = _('Sales Order Allocation')

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderAllocation model."""
        return reverse('api-so-allocation-list')

    def clean(self):
        """Validate the SalesOrderAllocation object.

        Executes:
        - Cannot allocate stock to a line item without a part reference
        - The referenced part must match the part associated with the line item
        - Allocated quantity cannot exceed the quantity of the stock item
        - Allocation quantity must be "1" if the StockItem is serialized
        - Allocation quantity cannot be zero
        """
        super().clean()

        errors = {}

        try:
            if not self.item:
                raise ValidationError({'item': _('Stock item has not been assigned')})
        except stock.models.StockItem.DoesNotExist:
            raise ValidationError({'item': _('Stock item has not been assigned')})

        try:
            if self.line.part != self.item.part:
                variants = self.line.part.get_descendants(include_self=True)
                if self.line.part not in variants:
                    errors['item'] = _(
                        'Cannot allocate stock item to a line with a different part'
                    )
        except PartModels.Part.DoesNotExist:
            errors['line'] = _('Cannot allocate stock to a line without a part')

        if self.quantity > self.item.quantity:
            errors['quantity'] = _('Allocation quantity cannot exceed stock quantity')

        # Ensure that we do not 'over allocate' a stock item
        build_allocation_count = self.item.build_allocation_count()
        sales_allocation_count = self.item.sales_order_allocation_count(
            exclude_allocations={'pk': self.pk}
        )

        total_allocation = (
            build_allocation_count + sales_allocation_count + self.quantity
        )

        if total_allocation > self.item.quantity:
            errors['quantity'] = _('Stock item is over-allocated')

        if self.quantity <= 0:
            errors['quantity'] = _('Allocation quantity must be greater than zero')

        if self.item.serial and self.quantity != 1:
            errors['quantity'] = _('Quantity must be 1 for serialized stock item')

        if self.shipment and self.line.order != self.shipment.order:
            errors['line'] = _('Sales order does not match shipment')
            errors['shipment'] = _('Shipment does not match sales order')

        if len(errors) > 0:
            raise ValidationError(errors)

    line = models.ForeignKey(
        SalesOrderLineItem,
        on_delete=models.CASCADE,
        verbose_name=_('Line'),
        related_name='allocations',
    )

    shipment = models.ForeignKey(
        SalesOrderShipment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='allocations',
        verbose_name=_('Shipment'),
        help_text=_('Sales order shipment reference'),
    )

    item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='sales_order_allocations',
        limit_choices_to={
            'part__salable': True,
            'part__virtual': False,
            'belongs_to': None,
            'sales_order': None,
        },
        verbose_name=_('Item'),
        help_text=_('Select stock item to allocate'),
    )

    quantity = RoundingDecimalField(
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        default=1,
        verbose_name=_('Quantity'),
        help_text=_('Enter stock allocation quantity'),
    )

    def get_location(self):
        """Return the <pk> value of the location associated with this allocation."""
        return self.item.location.id if self.item.location else None

    def get_po(self):
        """Return the PurchaseOrder associated with this allocation."""
        return self.item.purchase_order

    def complete_allocation(self, user):
        """Complete this allocation (called when the parent SalesOrder is marked as "shipped").

        Executes:
        - Determine if the referenced StockItem needs to be "split" (if allocated quantity != stock quantity)
        - Mark the StockItem as belonging to the Customer (this will remove it from stock)
        """
        order = self.line.order

        item = self.item.allocateToCustomer(
            order.customer, quantity=self.quantity, order=order, user=user
        )

        # Update the 'shipped' quantity
        self.line.shipped += self.quantity
        self.line.save()

        # Update our own reference to the StockItem
        # (It may have changed if the stock was split)
        self.item = item
        self.save()


class ReturnOrder(TotalPriceMixin, Order):
    """A ReturnOrder represents goods returned from a customer, e.g. an RMA or warranty.

    Attributes:
        customer: Reference to the customer
        sales_order: Reference to an existing SalesOrder (optional)
        status: The status of the order (refer to status_codes.ReturnOrderStatus)
    """

    REFERENCE_PATTERN_SETTING = 'RETURNORDER_REFERENCE_PATTERN'
    REQUIRE_RESPONSIBLE_SETTING = 'RETURNORDER_REQUIRE_RESPONSIBLE'
    STATUS_CLASS = ReturnOrderStatus
    UNLOCK_SETTING = 'RETURNORDER_EDIT_COMPLETED_ORDERS'

    class Meta:
        """Model meta options."""

        verbose_name = _('Return Order')

    def clean_line_item(self, line):
        """Clean a line item for this ReturnOrder."""
        super().clean_line_item(line)
        line.received_date = None
        line.outcome = ReturnOrderLineStatus.PENDING.value

    def report_context(self) -> ReturnOrderReportContext:
        """Generate report context data for this ReturnOrder."""
        return {**super().report_context(), 'customer': self.customer}

    def get_absolute_url(self):
        """Get the 'web' URL for this order."""
        return pui_url(f'/sales/return-order/{self.pk}')

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the ReturnOrder model."""
        return reverse('api-return-order-list')

    @classmethod
    def get_status_class(cls):
        """Return the ReturnOrderStatus class."""
        return ReturnOrderStatusGroups

    @classmethod
    def api_defaults(cls, request=None):
        """Return default values for this model when issuing an API OPTIONS request."""
        defaults = {
            'reference': order.validators.generate_next_return_order_reference()
        }

        return defaults

    @classmethod
    def barcode_model_type_code(cls):
        """Return the associated barcode model type code for this model."""
        return 'RO'

    def subscribed_users(self) -> list[User]:
        """Return a list of users subscribed to this ReturnOrder.

        By this, we mean users to are interested in any of the parts associated with this order.
        """
        subscribed_users = set()

        for line in self.lines.all():
            if line.item and line.item.part:
                # Add the part to the list of subscribed users
                for user in line.item.part.get_subscribers():
                    subscribed_users.add(user)

        return list(subscribed_users)

    def __str__(self):
        """Render a string representation of this ReturnOrder."""
        return f'{self.reference} - {self.customer.name if self.customer else _("no customer")}'

    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        verbose_name=_('Reference'),
        help_text=_('Return Order reference'),
        default=order.validators.generate_next_return_order_reference,
        validators=[order.validators.validate_return_order_reference],
    )

    customer = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_customer': True},
        related_name='sales_orders',
        verbose_name=_('Customer'),
        help_text=_('Company from which items are being returned'),
    )

    @property
    def company(self):
        """Accessor helper for Order base class."""
        return self.customer

    status = InvenTreeCustomStatusModelField(
        default=ReturnOrderStatus.PENDING.value,
        choices=ReturnOrderStatus.items(),
        status_class=ReturnOrderStatus,
        verbose_name=_('Status'),
        help_text=_('Return order status'),
    )

    customer_reference = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Customer Reference '),
        help_text=_('Customer order reference code'),
    )

    complete_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Completion Date'),
        help_text=_('Date order was completed'),
    )

    # region state changes
    @property
    def is_pending(self):
        """Return True if this order is pending."""
        return self.status == ReturnOrderStatus.PENDING

    @property
    def is_open(self):
        """Return True if this order is outstanding."""
        return self.status in ReturnOrderStatusGroups.OPEN

    @property
    def is_received(self):
        """Return True if this order is fully received."""
        return not self.lines.filter(received_date=None).exists()

    @property
    def can_hold(self):
        """Return True if this order can be placed on hold."""
        return self.status in [
            ReturnOrderStatus.PENDING.value,
            ReturnOrderStatus.IN_PROGRESS.value,
        ]

    def _action_hold(self, *args, **kwargs):
        """Mark this order as 'on hold' (if allowed)."""
        if self.can_hold:
            self.status = ReturnOrderStatus.ON_HOLD.value
            self.save()

            trigger_event(ReturnOrderEvents.HOLD, id=self.pk)

    @property
    def can_cancel(self):
        """Return True if this order can be cancelled."""
        return self.status in ReturnOrderStatusGroups.OPEN

    def _action_cancel(self, *args, **kwargs):
        """Cancel this ReturnOrder (if not already cancelled)."""
        if self.can_cancel:
            self.status = ReturnOrderStatus.CANCELLED.value
            self.save()

            trigger_event(ReturnOrderEvents.CANCELLED, id=self.pk)

            # Notify users that the order has been canceled
            notify_responsible(
                self,
                ReturnOrder,
                exclude=self.created_by,
                content=InvenTreeNotificationBodies.OrderCanceled,
                extra_users=self.subscribed_users(),
            )

    def _action_complete(self, *args, **kwargs):
        """Complete this ReturnOrder (if not already completed)."""
        if self.status == ReturnOrderStatus.IN_PROGRESS.value:
            self.status = ReturnOrderStatus.COMPLETE.value
            self.complete_date = InvenTree.helpers.current_date()
            self.save()

            trigger_event(ReturnOrderEvents.COMPLETED, id=self.pk)

    def place_order(self):
        """Deprecated version of 'issue_order."""
        self.issue_order()

    @property
    def can_issue(self):
        """Return True if this order can be issued."""
        return self.status in [
            ReturnOrderStatus.PENDING.value,
            ReturnOrderStatus.ON_HOLD.value,
        ]

    def _action_place(self, *args, **kwargs):
        """Issue this ReturnOrder (if currently pending)."""
        if self.can_issue:
            self.status = ReturnOrderStatus.IN_PROGRESS.value
            self.issue_date = InvenTree.helpers.current_date()
            self.save()

            trigger_event(ReturnOrderEvents.ISSUED, id=self.pk)

            # Notify users that the order has been placed
            notify_responsible(
                self,
                ReturnOrder,
                exclude=self.created_by,
                content=InvenTreeNotificationBodies.NewOrder,
                extra_users=self.subscribed_users(),
            )

    @transaction.atomic
    def hold_order(self):
        """Attempt to transition to ON_HOLD status."""
        return self.handle_transition(
            self.status, ReturnOrderStatus.ON_HOLD.value, self, self._action_hold
        )

    @transaction.atomic
    def issue_order(self):
        """Attempt to transition to IN_PROGRESS status."""
        return self.handle_transition(
            self.status, ReturnOrderStatus.IN_PROGRESS.value, self, self._action_place
        )

    @transaction.atomic
    def complete_order(self):
        """Attempt to transition to COMPLETE status."""
        return self.handle_transition(
            self.status, ReturnOrderStatus.COMPLETE.value, self, self._action_complete
        )

    @transaction.atomic
    def cancel_order(self):
        """Attempt to transition to CANCELLED status."""
        return self.handle_transition(
            self.status, ReturnOrderStatus.CANCELLED.value, self, self._action_cancel
        )

    # endregion

    @transaction.atomic
    def receive_line_item(self, line, location, user, **kwargs):
        """Receive a line item against this ReturnOrder.

        Arguments:
            line: ReturnOrderLineItem to receive
            location: StockLocation to receive the item to
            user: User performing the action

        Keyword Arguments:
            note: Additional notes to add to the tracking entry
            status: Status to set the StockItem to (default: StockStatus.QUARANTINED)

        Performs the following actions:
            - Transfers the StockItem to the specified location
            - Marks the StockItem as "quarantined"
            - Adds a tracking entry to the StockItem
            - Removes the 'customer' reference from the StockItem
        """
        # Prevent an item from being "received" multiple times
        if line.received_date is not None:
            logger.warning('receive_line_item called with item already returned')
            return

        stock_item = line.item

        if not stock_item.serialized and line.quantity < stock_item.quantity:
            # Split the stock item if we are returning less than the full quantity
            stock_item = stock_item.splitStock(line.quantity, user=user)

            # Update the line item to point to the *new* stock item
            line.item = stock_item
            line.save()

        status = kwargs.get('status')

        if status is None:
            status = StockStatus.QUARANTINED.value

        deltas = {'status': status, 'returnorder': self.pk, 'location': location.pk}

        if stock_item.customer:
            deltas['customer'] = stock_item.customer.pk

        # Update the StockItem
        stock_item.status = status
        stock_item.location = location
        stock_item.customer = None
        stock_item.sales_order = None
        stock_item.save(add_note=False)
        stock_item.clearAllocations()

        # Add a tracking entry to the StockItem
        stock_item.add_tracking_entry(
            StockHistoryCode.RETURNED_AGAINST_RETURN_ORDER,
            user,
            notes=kwargs.get('note', ''),
            deltas=deltas,
            location=location,
            returnorder=self,
        )

        # Update the LineItem
        line.received_date = InvenTree.helpers.current_date()
        line.save()

        trigger_event(ReturnOrderEvents.RECEIVED, id=self.pk, line_item_id=line.pk)

        # Notify responsible users
        notify_responsible(
            self,
            ReturnOrder,
            exclude=user,
            content=InvenTreeNotificationBodies.ReturnOrderItemsReceived,
            extra_users=line.item.part.get_subscribers(),
        )


class ReturnOrderLineItem(StatusCodeMixin, OrderLineItem):
    """Model for a single LineItem in a ReturnOrder."""

    STATUS_CLASS = ReturnOrderLineStatus
    STATUS_FIELD = 'outcome'

    class Meta:
        """Metaclass options for this model."""

        verbose_name = _('Return Order Line Item')
        unique_together = [('order', 'item')]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with this model."""
        return reverse('api-return-order-line-list')

    def clean(self):
        """Perform extra validation steps for the ReturnOrderLineItem model."""
        super().clean()

        if not self.item:
            raise ValidationError({'item': _('Stock item must be specified')})

        if self.quantity > self.item.quantity:
            raise ValidationError({
                'quantity': _('Return quantity exceeds stock quantity')
            })

        if self.quantity <= 0:
            raise ValidationError({
                'quantity': _('Return quantity must be greater than zero')
            })

        if self.item.serialized and self.quantity != 1:
            raise ValidationError({
                'quantity': _('Invalid quantity for serialized stock item')
            })

    order = models.ForeignKey(
        ReturnOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('Order'),
        help_text=_('Return Order'),
    )

    item = models.ForeignKey(
        stock.models.StockItem,
        on_delete=models.CASCADE,
        related_name='return_order_lines',
        verbose_name=_('Item'),
        help_text=_('Select item to return from customer'),
    )

    quantity = models.DecimalField(
        verbose_name=('Quantity'),
        help_text=('Quantity to return'),
        max_digits=15,
        decimal_places=5,
        validators=[MinValueValidator(0)],
        default=1,
    )

    received_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Received Date'),
        help_text=_('The date this this return item was received'),
    )

    @property
    def received(self):
        """Return True if this item has been received."""
        return self.received_date is not None

    outcome = InvenTreeCustomStatusModelField(
        default=ReturnOrderLineStatus.PENDING.value,
        choices=ReturnOrderLineStatus.items(),
        status_class=ReturnOrderLineStatus,
        verbose_name=_('Outcome'),
        help_text=_('Outcome for this line item'),
    )

    price = InvenTreeModelMoneyField(
        null=True,
        blank=True,
        verbose_name=_('Price'),
        help_text=_('Cost associated with return or repair for this line item'),
    )


class ReturnOrderExtraLine(OrderExtraLine):
    """Model for a single ExtraLine in a ReturnOrder."""

    class Meta:
        """Metaclass options for this model."""

        verbose_name = _('Return Order Extra Line')

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the ReturnOrderExtraLine model."""
        return reverse('api-return-order-extra-line-list')

    order = models.ForeignKey(
        ReturnOrder,
        on_delete=models.CASCADE,
        related_name='extra_lines',
        verbose_name=_('Order'),
        help_text=_('Return Order'),
    )
