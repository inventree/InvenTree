"""Order model definitions."""

import logging
import os
import sys
import traceback
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from djmoney.money import Money
from error_report.models import Error
from markdownx.models import MarkdownxField
from mptt.models import TreeForeignKey

import InvenTree.helpers
import InvenTree.ready
from common.settings import currency_code_default
from company.models import Company, SupplierPart
from InvenTree.fields import InvenTreeModelMoneyField, RoundingDecimalField
from InvenTree.helpers import (decimal2string, getSetting, increment,
                               notify_responsible)
from InvenTree.models import InvenTreeAttachment, ReferenceIndexingMixin
from InvenTree.status_codes import (PurchaseOrderStatus, SalesOrderStatus,
                                    StockHistoryCode, StockStatus)
from part import models as PartModels
from plugin.events import trigger_event
from plugin.models import MetadataMixin
from stock import models as stock_models
from users import models as UserModels

logger = logging.getLogger('inventree')


def get_next_po_number():
    """Returns the next available PurchaseOrder reference number."""
    if PurchaseOrder.objects.count() == 0:
        return '0001'

    order = PurchaseOrder.objects.exclude(reference=None).last()

    attempts = {order.reference}

    reference = order.reference

    while 1:
        reference = increment(reference)

        if reference in attempts:
            # Escape infinite recursion
            return reference

        if PurchaseOrder.objects.filter(reference=reference).exists():
            attempts.add(reference)
        else:
            break

    return reference


def get_next_so_number():
    """Returns the next available SalesOrder reference number."""
    if SalesOrder.objects.count() == 0:
        return '0001'

    order = SalesOrder.objects.exclude(reference=None).last()

    attempts = {order.reference}

    reference = order.reference

    while 1:
        reference = increment(reference)

        if reference in attempts:
            # Escape infinite recursion
            return reference

        if SalesOrder.objects.filter(reference=reference).exists():
            attempts.add(reference)
        else:
            break

    return reference


class Order(MetadataMixin, ReferenceIndexingMixin):
    """Abstract model for an order.

    Instances of this class:

    - PuchaseOrder

    Attributes:
        reference: Unique order number / reference / code
        description: Long form description (required)
        notes: Extra note field (optional)
        creation_date: Automatic date of order creation
        created_by: User who created this order (automatically captured)
        issue_date: Date the order was issued
        complete_date: Date the order was completed
        responsible: User (or group) responsible for managing the order
    """

    def save(self, *args, **kwargs):
        """Custom save method for the order models:

        Ensures that the reference field is rebuilt whenever the instance is saved.
        """
        self.rebuild_reference_field()

        if not self.creation_date:
            self.creation_date = datetime.now().date()

        super().save(*args, **kwargs)

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    description = models.CharField(max_length=250, verbose_name=_('Description'), help_text=_('Order description'))

    link = models.URLField(blank=True, verbose_name=_('Link'), help_text=_('Link to external page'))

    creation_date = models.DateField(blank=True, null=True, verbose_name=_('Creation Date'))

    created_by = models.ForeignKey(User,
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='+',
                                   verbose_name=_('Created By')
                                   )

    responsible = models.ForeignKey(
        UserModels.Owner,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        help_text=_('User or group responsible for this order'),
        verbose_name=_('Responsible'),
        related_name='+',
    )

    notes = MarkdownxField(blank=True, verbose_name=_('Notes'), help_text=_('Order notes'))

    def get_total_price(self, target_currency=None):
        """Calculates the total price of all order lines, and converts to the specified target currency.

        If not specified, the default system currency is used.

        If currency conversion fails (e.g. there are no valid conversion rates),
        then we simply return zero, rather than attempting some other calculation.
        """
        # Set default - see B008
        if target_currency is None:
            target_currency = currency_code_default()

        total = Money(0, target_currency)

        # gather name reference
        price_ref_tag = 'sale_price' if isinstance(self, SalesOrder) else 'purchase_price'

        # order items
        for line in self.lines.all():

            price_ref = getattr(line, price_ref_tag)

            if not price_ref:
                continue

            try:
                total += line.quantity * convert_money(price_ref, target_currency)
            except MissingRate:
                # Record the error, try to press on
                kind, info, data = sys.exc_info()

                Error.objects.create(
                    kind=kind.__name__,
                    info=info,
                    data='\n'.join(traceback.format_exception(kind, info, data)),
                    path='order.get_total_price',
                )

                logger.error(f"Missing exchange rate for '{target_currency}'")

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
                kind, info, data = sys.exc_info()

                Error.objects.create(
                    kind=kind.__name__,
                    info=info,
                    data='\n'.join(traceback.format_exception(kind, info, data)),
                    path='order.get_total_price',
                )

                logger.error(f"Missing exchange rate for '{target_currency}'")

                # Return None to indicate the calculated price is invalid
                return None

        # set decimal-places
        total.decimal_places = 4

        return total


class PurchaseOrder(Order):
    """A PurchaseOrder represents goods shipped inwards from an external supplier.

    Attributes:
        supplier: Reference to the company supplying the goods in the order
        supplier_reference: Optional field for supplier order reference code
        received_by: User that received the goods
        target_date: Expected delivery target date for PurchaseOrder completion (optional)
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the PurchaseOrder model"""
        return reverse('api-po-list')

    OVERDUE_FILTER = Q(status__in=PurchaseOrderStatus.OPEN) & ~Q(target_date=None) & Q(target_date__lte=datetime.now().date())

    @staticmethod
    def filterByDate(queryset, min_date, max_date):
        """Filter by 'minimum and maximum date range'.

        - Specified as min_date, max_date
        - Both must be specified for filter to be applied
        - Determine which "interesting" orders exist bewteen these dates

        To be "interesting":
        - A "received" order where the received date lies within the date range
        - A "pending" order where the target date lies within the date range
        - TODO: An "overdue" order where the target date is in the past
        """
        date_fmt = '%Y-%m-%d'  # ISO format date string

        # Ensure that both dates are valid
        try:
            min_date = datetime.strptime(str(min_date), date_fmt).date()
            max_date = datetime.strptime(str(max_date), date_fmt).date()
        except (ValueError, TypeError):
            # Date processing error, return queryset unchanged
            return queryset

        # Construct a queryset for "received" orders within the range
        received = Q(status=PurchaseOrderStatus.COMPLETE) & Q(complete_date__gte=min_date) & Q(complete_date__lte=max_date)

        # Construct a queryset for "pending" orders within the range
        pending = Q(status__in=PurchaseOrderStatus.OPEN) & ~Q(target_date=None) & Q(target_date__gte=min_date) & Q(target_date__lte=max_date)

        # TODO - Construct a queryset for "overdue" orders within the range

        queryset = queryset.filter(received | pending)

        return queryset

    def __str__(self):
        """Render a string representation of this PurchaseOrder"""
        prefix = getSetting('PURCHASEORDER_REFERENCE_PREFIX')

        return f"{prefix}{self.reference} - {self.supplier.name if self.supplier else _('deleted')}"

    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        verbose_name=_('Reference'),
        help_text=_('Order reference'),
        default=get_next_po_number,
    )

    status = models.PositiveIntegerField(default=PurchaseOrderStatus.PENDING, choices=PurchaseOrderStatus.items(),
                                         help_text=_('Purchase order status'))

    supplier = models.ForeignKey(
        Company, on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={
            'is_supplier': True,
        },
        related_name='purchase_orders',
        verbose_name=_('Supplier'),
        help_text=_('Company from which the items are being ordered')
    )

    supplier_reference = models.CharField(max_length=64, blank=True, verbose_name=_('Supplier Reference'), help_text=_("Supplier order reference code"))

    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='+',
        verbose_name=_('received by')
    )

    issue_date = models.DateField(
        blank=True, null=True,
        verbose_name=_('Issue Date'),
        help_text=_('Date order was issued')
    )

    target_date = models.DateField(
        blank=True, null=True,
        verbose_name=_('Target Delivery Date'),
        help_text=_('Expected date for order delivery. Order will be overdue after this date.'),
    )

    complete_date = models.DateField(
        blank=True, null=True,
        verbose_name=_('Completion Date'),
        help_text=_('Date order was completed')
    )

    def get_absolute_url(self):
        """Return the web URL of the detail view for this order"""
        return reverse('po-detail', kwargs={'pk': self.id})

    @transaction.atomic
    def add_line_item(self, supplier_part, quantity, group: bool = True, reference: str = '', purchase_price=None):
        """Add a new line item to this purchase order.

        This function will check that:
        * The supplier part matches the supplier specified for this purchase order
        * The quantity is greater than zero

        Args:
            supplier_part: The supplier_part to add
            quantity : The number of items to add
            group (bool, optional): If True, this new quantity will be added to an existing line item for the same supplier_part (if it exists). Defaults to True.
            reference (str, optional): Reference to item. Defaults to ''.
            purchase_price (optional): Price of item. Defaults to None.

        Raises:
            ValidationError: quantity is smaller than 0
            ValidationError: quantity is not type int
            ValidationError: supplier is not supplier of purchase order
        """
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValidationError({
                    'quantity': _("Quantity must be greater than zero")})
        except ValueError:
            raise ValidationError({'quantity': _("Invalid quantity provided")})

        if supplier_part.supplier != self.supplier:
            raise ValidationError({'supplier': _("Part supplier must match PO supplier")})

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

                return

        line = PurchaseOrderLineItem(
            order=self,
            part=supplier_part,
            quantity=quantity,
            reference=reference,
            purchase_price=purchase_price,
        )

        line.save()

    @transaction.atomic
    def place_order(self):
        """Marks the PurchaseOrder as PLACED.

        Order must be currently PENDING.
        """
        if self.status == PurchaseOrderStatus.PENDING:
            self.status = PurchaseOrderStatus.PLACED
            self.issue_date = datetime.now().date()
            self.save()

            trigger_event('purchaseorder.placed', id=self.pk)

    @transaction.atomic
    def complete_order(self):
        """Marks the PurchaseOrder as COMPLETE.

        Order must be currently PLACED.
        """
        if self.status == PurchaseOrderStatus.PLACED:
            self.status = PurchaseOrderStatus.COMPLETE
            self.complete_date = datetime.now().date()
            self.save()

            trigger_event('purchaseorder.completed', id=self.pk)

    @property
    def is_overdue(self):
        """Returns True if this PurchaseOrder is "overdue".

        Makes use of the OVERDUE_FILTER to avoid code duplication.
        """
        query = PurchaseOrder.objects.filter(pk=self.pk)
        query = query.filter(PurchaseOrder.OVERDUE_FILTER)

        return query.exists()

    def can_cancel(self):
        """A PurchaseOrder can only be cancelled under the following circumstances.

        - Status is PLACED
        - Status is PENDING
        """
        return self.status in [
            PurchaseOrderStatus.PLACED,
            PurchaseOrderStatus.PENDING
        ]

    @transaction.atomic
    def cancel_order(self):
        """Marks the PurchaseOrder as CANCELLED."""
        if self.can_cancel():
            self.status = PurchaseOrderStatus.CANCELLED
            self.save()

            trigger_event('purchaseorder.cancelled', id=self.pk)

    def pending_line_items(self):
        """Return a list of pending line items for this order.

        Any line item where 'received' < 'quantity' will be returned.
        """
        return self.lines.filter(quantity__gt=F('received'))

    def completed_line_items(self):
        """Return a list of completed line items against this order."""
        return self.lines.filter(quantity__lte=F('received'))

    @property
    def line_count(self):
        """Return the total number of line items associated with this order"""
        return self.lines.count()

    @property
    def completed_line_count(self):
        """Return the number of complete line items associated with this order"""
        return self.completed_line_items().count()

    @property
    def pending_line_count(self):
        """Return the number of pending line items associated with this order"""
        return self.pending_line_items().count()

    @property
    def is_complete(self):
        """Return True if all line items have been received."""
        return self.lines.count() > 0 and self.pending_line_items().count() == 0

    @transaction.atomic
    def receive_line_item(self, line, location, quantity, user, status=StockStatus.OK, **kwargs):
        """Receive a line item (or partial line item) against this PurchaseOrder."""
        # Extract optional batch code for the new stock item
        batch_code = kwargs.get('batch_code', '')

        # Extract optional list of serial numbers
        serials = kwargs.get('serials', None)

        # Extract optional notes field
        notes = kwargs.get('notes', '')

        # Extract optional barcode field
        barcode = kwargs.get('barcode', None)

        # Prevent null values for barcode
        if barcode is None:
            barcode = ''

        if self.status != PurchaseOrderStatus.PLACED:
            raise ValidationError(
                "Lines can only be received against an order marked as 'PLACED'"
            )

        try:
            if quantity < 0:
                raise ValidationError({
                    "quantity": _("Quantity must be a positive number")
                })
            quantity = InvenTree.helpers.clean_decimal(quantity)
        except TypeError:
            raise ValidationError({
                "quantity": _("Invalid quantity provided")
            })

        # Create a new stock item
        if line.part and quantity > 0:

            # Determine if we should individually serialize the items, or not
            if type(serials) is list and len(serials) > 0:
                serialize = True
            else:
                serialize = False
                serials = [None]

            for sn in serials:

                stock = stock_models.StockItem(
                    part=line.part.part,
                    supplier_part=line.part,
                    location=location,
                    quantity=1 if serialize else quantity,
                    purchase_order=self,
                    status=status,
                    batch=batch_code,
                    serial=sn,
                    purchase_price=line.purchase_price,
                    uid=barcode
                )

                stock.save(add_note=False)

                tracking_info = {
                    'status': status,
                    'purchaseorder': self.pk,
                }

                stock.add_tracking_entry(
                    StockHistoryCode.RECEIVED_AGAINST_PURCHASE_ORDER,
                    user,
                    notes=notes,
                    deltas=tracking_info,
                    location=location,
                    purchaseorder=self,
                    quantity=quantity
                )

        # Update the number of parts received against the particular line item
        line.received += quantity
        line.save()

        # Has this order been completed?
        if len(self.pending_line_items()) == 0:

            self.received_by = user
            self.complete_order()  # This will save the model


@receiver(post_save, sender=PurchaseOrder, dispatch_uid='purchase_order_post_save')
def after_save_purchase_order(sender, instance: PurchaseOrder, created: bool, **kwargs):
    """Callback function to be executed after a PurchaseOrder is saved."""
    if not InvenTree.ready.canAppAccessDatabase(allow_test=True) or InvenTree.ready.isImportingData():
        return

    if created:
        # Notify the responsible users that the purchase order has been created
        notify_responsible(instance, sender, exclude=instance.created_by)


class SalesOrder(Order):
    """A SalesOrder represents a list of goods shipped outwards to a customer.

    Attributes:
        customer: Reference to the company receiving the goods in the order
        customer_reference: Optional field for customer order reference code
        target_date: Target date for SalesOrder completion (optional)
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrder model"""
        return reverse('api-so-list')

    OVERDUE_FILTER = Q(status__in=SalesOrderStatus.OPEN) & ~Q(target_date=None) & Q(target_date__lte=datetime.now().date())

    @staticmethod
    def filterByDate(queryset, min_date, max_date):
        """Filter by "minimum and maximum date range".

        - Specified as min_date, max_date
        - Both must be specified for filter to be applied
        - Determine which "interesting" orders exist between these dates

        To be "interesting":
        - A "completed" order where the completion date lies within the date range
        - A "pending" order where the target date lies within the date range
        - TODO: An "overdue" order where the target date is in the past
        """
        date_fmt = '%Y-%m-%d'  # ISO format date string

        # Ensure that both dates are valid
        try:
            min_date = datetime.strptime(str(min_date), date_fmt).date()
            max_date = datetime.strptime(str(max_date), date_fmt).date()
        except (ValueError, TypeError):
            # Date processing error, return queryset unchanged
            return queryset

        # Construct a queryset for "completed" orders within the range
        completed = Q(status__in=SalesOrderStatus.COMPLETE) & Q(shipment_date__gte=min_date) & Q(shipment_date__lte=max_date)

        # Construct a queryset for "pending" orders within the range
        pending = Q(status__in=SalesOrderStatus.OPEN) & ~Q(target_date=None) & Q(target_date__gte=min_date) & Q(target_date__lte=max_date)

        # TODO: Construct a queryset for "overdue" orders within the range

        queryset = queryset.filter(completed | pending)

        return queryset

    def __str__(self):
        """Render a string representation of this SalesOrder"""
        prefix = getSetting('SALESORDER_REFERENCE_PREFIX')

        return f"{prefix}{self.reference} - {self.customer.name if self.customer else _('deleted')}"

    def get_absolute_url(self):
        """Return the web URL for the detail view of this order"""
        return reverse('so-detail', kwargs={'pk': self.id})

    reference = models.CharField(
        unique=True,
        max_length=64,
        blank=False,
        verbose_name=_('Reference'),
        help_text=_('Order reference'),
        default=get_next_so_number,
    )

    customer = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_customer': True},
        related_name='sales_orders',
        verbose_name=_('Customer'),
        help_text=_("Company to which the items are being sold"),
    )

    status = models.PositiveIntegerField(default=SalesOrderStatus.PENDING, choices=SalesOrderStatus.items(),
                                         verbose_name=_('Status'), help_text=_('Purchase order status'))

    customer_reference = models.CharField(max_length=64, blank=True, verbose_name=_('Customer Reference '), help_text=_("Customer order reference code"))

    target_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Target completion date'),
        help_text=_('Target date for order completion. Order will be overdue after this date.')
    )

    shipment_date = models.DateField(blank=True, null=True, verbose_name=_('Shipment Date'))

    shipped_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='+',
        verbose_name=_('shipped by')
    )

    @property
    def is_overdue(self):
        """Returns true if this SalesOrder is "overdue".

        Makes use of the OVERDUE_FILTER to avoid code duplication.
        """
        query = SalesOrder.objects.filter(pk=self.pk)
        query = query.filter(SalesOrder.OVERDUE_FILTER)

        return query.exists()

    @property
    def is_pending(self):
        """Return True if this order is 'pending'"""
        return self.status == SalesOrderStatus.PENDING

    @property
    def stock_allocations(self):
        """Return a queryset containing all allocations for this order."""
        return SalesOrderAllocation.objects.filter(
            line__in=[line.pk for line in self.lines.all()]
        )

    def is_fully_allocated(self):
        """Return True if all line items are fully allocated."""
        for line in self.lines.all():
            if not line.is_fully_allocated():
                return False

        return True

    def is_over_allocated(self):
        """Return true if any lines in the order are over-allocated."""
        for line in self.lines.all():
            if line.is_over_allocated():
                return True

        return False

    def is_completed(self):
        """Check if this order is "shipped" (all line items delivered)."""
        return self.lines.count() > 0 and all([line.is_completed() for line in self.lines.all()])

    def can_complete(self, raise_error=False):
        """Test if this SalesOrder can be completed.

        Throws a ValidationError if cannot be completed.
        """
        try:

            # Order without line items cannot be completed
            if self.lines.count() == 0:
                raise ValidationError(_('Order cannot be completed as no parts have been assigned'))

            # Only a PENDING order can be marked as SHIPPED
            elif self.status != SalesOrderStatus.PENDING:
                raise ValidationError(_('Only a pending order can be marked as complete'))

            elif self.pending_shipment_count > 0:
                raise ValidationError(_("Order cannot be completed as there are incomplete shipments"))

            elif self.pending_line_count > 0:
                raise ValidationError(_("Order cannot be completed as there are incomplete line items"))

        except ValidationError as e:

            if raise_error:
                raise e
            else:
                return False

        return True

    def complete_order(self, user):
        """Mark this order as "complete."""
        if not self.can_complete():
            return False

        self.status = SalesOrderStatus.SHIPPED
        self.shipped_by = user
        self.shipment_date = datetime.now()

        self.save()

        trigger_event('salesorder.completed', id=self.pk)

        return True

    def can_cancel(self):
        """Return True if this order can be cancelled."""
        if self.status != SalesOrderStatus.PENDING:
            return False

        return True

    @transaction.atomic
    def cancel_order(self):
        """Cancel this order (only if it is "pending").

        Executes:
        - Mark the order as 'cancelled'
        - Delete any StockItems which have been allocated
        """
        if not self.can_cancel():
            return False

        self.status = SalesOrderStatus.CANCELLED
        self.save()

        for line in self.lines.all():
            for allocation in line.allocations.all():
                allocation.delete()

        trigger_event('salesorder.cancelled', id=self.pk)

        return True

    @property
    def line_count(self):
        """Return the total number of lines associated with this order"""
        return self.lines.count()

    def completed_line_items(self):
        """Return a queryset of the completed line items for this order."""
        return self.lines.filter(shipped__gte=F('quantity'))

    def pending_line_items(self):
        """Return a queryset of the pending line items for this order."""
        return self.lines.filter(shipped__lt=F('quantity'))

    @property
    def completed_line_count(self):
        """Return the number of completed lines for this order"""
        return self.completed_line_items().count()

    @property
    def pending_line_count(self):
        """Return the number of pending (incomplete) lines associated with this order"""
        return self.pending_line_items().count()

    def completed_shipments(self):
        """Return a queryset of the completed shipments for this order."""
        return self.shipments.exclude(shipment_date=None)

    def pending_shipments(self):
        """Return a queryset of the pending shipments for this order."""
        return self.shipments.filter(shipment_date=None)

    @property
    def shipment_count(self):
        """Return the total number of shipments associated with this order"""
        return self.shipments.count()

    @property
    def completed_shipment_count(self):
        """Return the number of completed shipments associated with this order"""
        return self.completed_shipments().count()

    @property
    def pending_shipment_count(self):
        """Return the number of pending shipments associated with this order"""
        return self.pending_shipments().count()


@receiver(post_save, sender=SalesOrder, dispatch_uid='sales_order_post_save')
def after_save_sales_order(sender, instance: SalesOrder, created: bool, **kwargs):
    """Callback function to be executed after a SalesOrder is saved.

    - If the SALESORDER_DEFAULT_SHIPMENT setting is enabled, create a default shipment
    - Ignore if the database is not ready for access
    - Ignore if data import is active
    """
    if not InvenTree.ready.canAppAccessDatabase(allow_test=True) or InvenTree.ready.isImportingData():
        return

    if created:
        # A new SalesOrder has just been created

        if getSetting('SALESORDER_DEFAULT_SHIPMENT'):
            # Create default shipment
            SalesOrderShipment.objects.create(
                order=instance,
                reference='1',
            )

        # Notify the responsible users that the sales order has been created
        notify_responsible(instance, sender, exclude=instance.created_by)


class PurchaseOrderAttachment(InvenTreeAttachment):
    """Model for storing file attachments against a PurchaseOrder object."""

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the PurchaseOrderAttachment model"""
        return reverse('api-po-attachment-list')

    def getSubdir(self):
        """Return the directory path where PurchaseOrderAttachment files are located"""
        return os.path.join("po_files", str(self.order.id))

    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="attachments")


class SalesOrderAttachment(InvenTreeAttachment):
    """Model for storing file attachments against a SalesOrder object."""

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderAttachment class"""
        return reverse('api-so-attachment-list')

    def getSubdir(self):
        """Return the directory path where SalesOrderAttachment files are located"""
        return os.path.join("so_files", str(self.order.id))

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='attachments')


class OrderLineItem(models.Model):
    """Abstract model for an order line item.

    Attributes:
        quantity: Number of items
        reference: Reference text (e.g. customer reference) for this line item
        note: Annotation for the item
        target_date: An (optional) date for expected shipment of this line item.
    """

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    quantity = RoundingDecimalField(
        verbose_name=_('Quantity'),
        help_text=_('Item quantity'),
        default=1,
        max_digits=15, decimal_places=5,
        validators=[MinValueValidator(0)],
    )

    reference = models.CharField(max_length=100, blank=True, verbose_name=_('Reference'), help_text=_('Line item reference'))

    notes = models.CharField(max_length=500, blank=True, verbose_name=_('Notes'), help_text=_('Line item notes'))

    target_date = models.DateField(
        blank=True, null=True,
        verbose_name=_('Target Date'),
        help_text=_('Target shipping date for this line item'),
    )


class OrderExtraLine(OrderLineItem):
    """Abstract Model for a single ExtraLine in a Order.

    Attributes:
        price: The unit sale price for this OrderLineItem
    """

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    context = models.JSONField(
        blank=True, null=True,
        verbose_name=_('Context'),
        help_text=_('Additional context for this line'),
    )

    price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=4,
        null=True, blank=True,
        verbose_name=_('Price'),
        help_text=_('Unit price'),
    )


class PurchaseOrderLineItem(OrderLineItem):
    """Model for a purchase order line item.

    Attributes:
        order: Reference to a PurchaseOrder object
    """

    # Filter for determining if a particular PurchaseOrderLineItem is overdue
    OVERDUE_FILTER = Q(received__lt=F('quantity')) & ~Q(target_date=None) & Q(target_date__lt=datetime.now().date())

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the PurchaseOrderLineItem model"""
        return reverse('api-po-line-list')

    def clean(self):
        """Custom clean method for the PurchaseOrderLineItem model:

        - Ensure the supplier part matches the supplier
        """
        super().clean()

        if self.order.supplier and self.part:
            # Supplier part *must* point to the same supplier!
            if self.part.supplier != self.order.supplier:
                raise ValidationError({
                    'part': _('Supplier part must match supplier')
                })

    def __str__(self):
        """Render a string representation of a PurchaseOrderLineItem instance"""
        return "{n} x {part} from {supplier} (for {po})".format(
            n=decimal2string(self.quantity),
            part=self.part.SKU if self.part else 'unknown part',
            supplier=self.order.supplier.name if self.order.supplier else _('deleted'),
            po=self.order)

    order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('Order'),
        help_text=_('Purchase Order')
    )

    def get_base_part(self):
        """Return the base part.Part object for the line item.

        Note: Returns None if the SupplierPart is not set!
        """
        if self.part is None:
            return None
        else:
            return self.part.part

    part = models.ForeignKey(
        SupplierPart, on_delete=models.SET_NULL,
        blank=False, null=True,
        related_name='purchase_order_line_items',
        verbose_name=_('Part'),
        help_text=_("Supplier part"),
    )

    received = models.DecimalField(
        decimal_places=5,
        max_digits=15,
        default=0,
        verbose_name=_('Received'),
        help_text=_('Number of items received')
    )

    purchase_price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=4,
        null=True, blank=True,
        verbose_name=_('Purchase Price'),
        help_text=_('Unit purchase price'),
    )

    destination = TreeForeignKey(
        'stock.StockLocation', on_delete=models.SET_NULL,
        verbose_name=_('Destination'),
        related_name='po_lines',
        blank=True, null=True,
        help_text=_('Where does the Purchaser want this item to be stored?')
    )

    def get_destination(self):
        """Show where the line item is or should be placed.

        NOTE: If a line item gets split when recieved, only an arbitrary
              stock items location will be reported as the location for the
              entire line.
        """
        for stock in stock_models.StockItem.objects.filter(supplier_part=self.part, purchase_order=self.order):
            if stock.location:
                return stock.location
        if self.destination:
            return self.destination
        if self.part and self.part.part and self.part.part.default_location:
            return self.part.part.default_location

    def remaining(self):
        """Calculate the number of items remaining to be received."""
        r = self.quantity - self.received
        return max(r, 0)


class PurchaseOrderExtraLine(OrderExtraLine):
    """Model for a single ExtraLine in a PurchaseOrder.

    Attributes:
        order: Link to the PurchaseOrder that this line belongs to
        title: title of line
        price: The unit price for this OrderLine
    """
    @staticmethod
    def get_api_url():
        """Return the API URL associated with the PurchaseOrderExtraLine model"""
        return reverse('api-po-extra-line-list')

    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='extra_lines', verbose_name=_('Order'), help_text=_('Purchase Order'))


class SalesOrderLineItem(OrderLineItem):
    """Model for a single LineItem in a SalesOrder.

    Attributes:
        order: Link to the SalesOrder that this line item belongs to
        part: Link to a Part object (may be null)
        sale_price: The unit sale price for this OrderLineItem
        shipped: The number of items which have actually shipped against this line item
    """

    # Filter for determining if a particular SalesOrderLineItem is overdue
    OVERDUE_FILTER = Q(shipped__lt=F('quantity')) & ~Q(target_date=None) & Q(target_date__lt=datetime.now().date())

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderLineItem model"""
        return reverse('api-so-line-list')

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('Order'),
        help_text=_('Sales Order')
    )

    part = models.ForeignKey('part.Part', on_delete=models.SET_NULL, related_name='sales_order_line_items', null=True, verbose_name=_('Part'), help_text=_('Part'), limit_choices_to={'salable': True})

    sale_price = InvenTreeModelMoneyField(
        max_digits=19,
        decimal_places=4,
        null=True, blank=True,
        verbose_name=_('Sale Price'),
        help_text=_('Unit sale price'),
    )

    shipped = RoundingDecimalField(
        verbose_name=_('Shipped'),
        help_text=_('Shipped quantity'),
        default=0,
        max_digits=15, decimal_places=5,
        validators=[MinValueValidator(0)]
    )

    def fulfilled_quantity(self):
        """Return the total stock quantity fulfilled against this line item."""
        query = self.order.stock_items.filter(part=self.part).aggregate(fulfilled=Coalesce(Sum('quantity'), Decimal(0)))

        return query['fulfilled']

    def allocated_quantity(self):
        """Return the total stock quantity allocated to this LineItem.

        This is a summation of the quantity of each attached StockItem
        """
        query = self.allocations.aggregate(allocated=Coalesce(Sum('quantity'), Decimal(0)))

        return query['allocated']

    def is_fully_allocated(self):
        """Return True if this line item is fully allocated."""
        if self.order.status == SalesOrderStatus.SHIPPED:
            return self.fulfilled_quantity() >= self.quantity

        return self.allocated_quantity() >= self.quantity

    def is_over_allocated(self):
        """Return True if this line item is over allocated."""
        return self.allocated_quantity() > self.quantity

    def is_completed(self):
        """Return True if this line item is completed (has been fully shipped)."""
        return self.shipped >= self.quantity


class SalesOrderShipment(models.Model):
    """The SalesOrderShipment model represents a physical shipment made against a SalesOrder.

    - Points to a single SalesOrder object
    - Multiple SalesOrderAllocation objects point to a particular SalesOrderShipment
    - When a given SalesOrderShipment is "shipped", stock items are removed from stock

    Attributes:
        order: SalesOrder reference
        shipment_date: Date this shipment was "shipped" (or null)
        checked_by: User reference field indicating who checked this order
        reference: Custom reference text for this shipment (e.g. consignment number?)
        notes: Custom notes field for this shipment
    """

    class Meta:
        """Metaclass defines extra model options"""
        # Shipment reference must be unique for a given sales order
        unique_together = [
            'order', 'reference',
        ]

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderShipment model"""
        return reverse('api-so-shipment-list')

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        blank=False, null=False,
        related_name='shipments',
        verbose_name=_('Order'),
        help_text=_('Sales Order'),
    )

    shipment_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Shipment Date'),
        help_text=_('Date of shipment'),
    )

    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Checked By'),
        help_text=_('User who checked this shipment'),
        related_name='+',
    )

    reference = models.CharField(
        max_length=100,
        blank=False,
        verbose_name=('Shipment'),
        help_text=_('Shipment number'),
        default='1',
    )

    notes = MarkdownxField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Shipment notes'),
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

    link = models.URLField(
        blank=True,
        verbose_name=_('Link'),
        help_text=_('Link to external page')
    )

    def is_complete(self):
        """Return True if this shipment has already been completed"""
        return self.shipment_date is not None

    def check_can_complete(self, raise_error=True):
        """Check if this shipment is able to be completed"""
        try:
            if self.shipment_date:
                # Shipment has already been sent!
                raise ValidationError(_("Shipment has already been sent"))

            if self.allocations.count() == 0:
                raise ValidationError(_("Shipment has no allocated stock items"))

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
        # Check if the shipment can be completed (throw error if not)
        self.check_can_complete()

        allocations = self.allocations.all()

        # Iterate through each stock item assigned to this shipment
        for allocation in allocations:
            # Mark the allocation as "complete"
            allocation.complete_allocation(user)

        # Update the "shipment" date
        self.shipment_date = kwargs.get('shipment_date', datetime.now())
        self.shipped_by = user

        # Was a tracking number provided?
        tracking_number = kwargs.get('tracking_number', None)

        if tracking_number is not None:
            self.tracking_number = tracking_number

        # Was an invoice number provided?
        invoice_number = kwargs.get('invoice_number', None)

        if invoice_number is not None:
            self.invoice_number = invoice_number

        # Was a link provided?
        link = kwargs.get('link', None)

        if link is not None:
            self.link = link

        self.save()

        trigger_event('salesordershipment.completed', id=self.pk)


class SalesOrderExtraLine(OrderExtraLine):
    """Model for a single ExtraLine in a SalesOrder.

    Attributes:
        order: Link to the SalesOrder that this line belongs to
        title: title of line
        price: The unit price for this OrderLine
    """
    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderExtraLine model"""
        return reverse('api-so-extra-line-list')

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='extra_lines', verbose_name=_('Order'), help_text=_('Sales Order'))


class SalesOrderAllocation(models.Model):
    """This model is used to 'allocate' stock items to a SalesOrder. Items that are "allocated" to a SalesOrder are not yet "attached" to the order, but they will be once the order is fulfilled.

    Attributes:
        line: SalesOrderLineItem reference
        shipment: SalesOrderShipment reference
        item: StockItem reference
        quantity: Quantity to take from the StockItem
    """

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the SalesOrderAllocation model"""
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
        except stock_models.StockItem.DoesNotExist:
            raise ValidationError({'item': _('Stock item has not been assigned')})

        try:
            if self.line.part != self.item.part:
                errors['item'] = _('Cannot allocate stock item to a line with a different part')
        except PartModels.Part.DoesNotExist:
            errors['line'] = _('Cannot allocate stock to a line without a part')

        if self.quantity > self.item.quantity:
            errors['quantity'] = _('Allocation quantity cannot exceed stock quantity')

        # TODO: The logic here needs improving. Do we need to subtract our own amount, or something?
        if self.item.quantity - self.item.allocation_count() + self.quantity < self.quantity:
            errors['quantity'] = _('StockItem is over-allocated')

        if self.quantity <= 0:
            errors['quantity'] = _('Allocation quantity must be greater than zero')

        if self.item.serial and self.quantity != 1:
            errors['quantity'] = _('Quantity must be 1 for serialized stock item')

        if self.line.order != self.shipment.order:
            errors['line'] = _('Sales order does not match shipment')
            errors['shipment'] = _('Shipment does not match sales order')

        if len(errors) > 0:
            raise ValidationError(errors)

    line = models.ForeignKey(
        SalesOrderLineItem,
        on_delete=models.CASCADE,
        verbose_name=_('Line'),
        related_name='allocations'
    )

    shipment = models.ForeignKey(
        SalesOrderShipment,
        on_delete=models.CASCADE,
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
            'belongs_to': None,
            'sales_order': None,
        },
        verbose_name=_('Item'),
        help_text=_('Select stock item to allocate')
    )

    quantity = RoundingDecimalField(max_digits=15, decimal_places=5, validators=[MinValueValidator(0)], default=1, verbose_name=_('Quantity'), help_text=_('Enter stock allocation quantity'))

    def get_location(self):
        """Return the <pk> value of the location associated with this allocation"""
        return self.item.location.id if self.item.location else None

    def get_po(self):
        """Return the PurchaseOrder associated with this allocation"""
        return self.item.purchase_order

    def complete_allocation(self, user):
        """Complete this allocation (called when the parent SalesOrder is marked as "shipped").

        Executes:
        - Determine if the referenced StockItem needs to be "split" (if allocated quantity != stock quantity)
        - Mark the StockItem as belonging to the Customer (this will remove it from stock)
        """
        order = self.line.order

        item = self.item.allocateToCustomer(
            order.customer,
            quantity=self.quantity,
            order=order,
            user=user
        )

        # Update the 'shipped' quantity
        self.line.shipped += self.quantity
        self.line.save()

        # Update our own reference to the StockItem
        # (It may have changed if the stock was split)
        self.item = item
        self.save()
