"""
Order model definitions
"""

# -*- coding: utf-8 -*-

from django.db import models, transaction
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.translation import ugettext as _

from markdownx.models import MarkdownxField

import os
from datetime import datetime
from decimal import Decimal

from part import models as PartModels
from stock import models as stock_models
from company.models import Company, SupplierPart

from InvenTree.fields import RoundingDecimalField
from InvenTree.helpers import decimal2string, increment
from InvenTree.status_codes import PurchaseOrderStatus, SalesOrderStatus, StockStatus
from InvenTree.models import InvenTreeAttachment


class Order(models.Model):
    """ Abstract model for an order.

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

    """

    ORDER_PREFIX = ""

    @classmethod
    def getNextOrderNumber(cls):
        """
        Try to predict the next order-number
        """

        if cls.objects.count() == 0:
            return None

        # We will assume that the latest pk has the highest PO number
        order = cls.objects.last()
        ref = order.reference

        if not ref:
            return None

        tries = set()

        tries.add(ref)

        while 1:
            new_ref = increment(ref)

            if new_ref in tries:
                # We are in a looping situation - simply return the original one
                return ref

            # Check that the new ref does not exist in the database
            if cls.objects.filter(reference=new_ref).exists():
                tries.add(new_ref)
                new_ref = increment(new_ref)

            else:
                break

        return new_ref

    def __str__(self):
        el = []

        if self.ORDER_PREFIX:
            el.append(self.ORDER_PREFIX)

        el.append(self.reference)

        return " ".join(el)

    def save(self, *args, **kwargs):
        if not self.creation_date:
            self.creation_date = datetime.now().date()

        super().save(*args, **kwargs)

    class Meta:
        abstract = True

    reference = models.CharField(unique=True, max_length=64, blank=False, help_text=_('Order reference'))

    description = models.CharField(max_length=250, help_text=_('Order description'))

    link = models.URLField(blank=True, help_text=_('Link to external page'))

    creation_date = models.DateField(blank=True, null=True)

    created_by = models.ForeignKey(User,
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='+'
                                   )

    notes = MarkdownxField(blank=True, help_text=_('Order notes'))


class PurchaseOrder(Order):
    """ A PurchaseOrder represents goods shipped inwards from an external supplier.

    Attributes:
        supplier: Reference to the company supplying the goods in the order
        supplier_reference: Optional field for supplier order reference code
        received_by: User that received the goods
    """
    
    ORDER_PREFIX = "PO"

    def __str__(self):
        return "PO {ref} - {company}".format(ref=self.reference, company=self.supplier.name)

    status = models.PositiveIntegerField(default=PurchaseOrderStatus.PENDING, choices=PurchaseOrderStatus.items(),
                                         help_text=_('Purchase order status'))

    supplier = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        limit_choices_to={
            'is_supplier': True,
        },
        related_name='purchase_orders',
        help_text=_('Company from which the items are being ordered')
    )

    supplier_reference = models.CharField(max_length=64, blank=True, help_text=_("Supplier order reference code"))

    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='+'
    )

    issue_date = models.DateField(blank=True, null=True, help_text=_('Date order was issued'))

    complete_date = models.DateField(blank=True, null=True, help_text=_('Date order was completed'))

    def get_absolute_url(self):
        return reverse('po-detail', kwargs={'pk': self.id})

    @transaction.atomic
    def add_line_item(self, supplier_part, quantity, group=True, reference=''):
        """ Add a new line item to this purchase order.
        This function will check that:

        * The supplier part matches the supplier specified for this purchase order
        * The quantity is greater than zero

        Args:
            supplier_part - The supplier_part to add
            quantity - The number of items to add
            group - If True, this new quantity will be added to an existing line item for the same supplier_part (if it exists)
        """

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValidationError({
                    'quantity': _("Quantity must be greater than zero")})
        except ValueError:
            raise ValidationError({'quantity': _("Invalid quantity provided")})

        if not supplier_part.supplier == self.supplier:
            raise ValidationError({'supplier': _("Part supplier must match PO supplier")})

        if group:
            # Check if there is already a matching line item (for this PO)
            matches = self.lines.filter(part=supplier_part)

            if matches.count() > 0:
                line = matches.first()

                line.quantity += quantity
                line.save()

                return

        line = PurchaseOrderLineItem(
            order=self,
            part=supplier_part,
            quantity=quantity,
            reference=reference)

        line.save()

    def place_order(self):
        """ Marks the PurchaseOrder as PLACED. Order must be currently PENDING. """

        if self.status == PurchaseOrderStatus.PENDING:
            self.status = PurchaseOrderStatus.PLACED
            self.issue_date = datetime.now().date()
            self.save()

    def complete_order(self):
        """ Marks the PurchaseOrder as COMPLETE. Order must be currently PLACED. """

        if self.status == PurchaseOrderStatus.PLACED:
            self.status = PurchaseOrderStatus.COMPLETE
            self.complete_date = datetime.now().date()
            self.save()

    def cancel_order(self):
        """ Marks the PurchaseOrder as CANCELLED. """

        if self.status in [PurchaseOrderStatus.PLACED, PurchaseOrderStatus.PENDING]:
            self.status = PurchaseOrderStatus.CANCELLED
            self.save()

    def pending_line_items(self):
        """ Return a list of pending line items for this order.
        Any line item where 'received' < 'quantity' will be returned.
        """

        return self.lines.filter(quantity__gt=F('received'))

    @property
    def is_complete(self):
        """ Return True if all line items have been received """

        return self.pending_line_items().count() == 0

    @transaction.atomic
    def receive_line_item(self, line, location, quantity, user, status=StockStatus.OK):
        """ Receive a line item (or partial line item) against this PO
        """

        if not self.status == PurchaseOrderStatus.PLACED:
            raise ValidationError({"status": _("Lines can only be received against an order marked as 'Placed'")})

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValidationError({"quantity": _("Quantity must be greater than zero")})
        except ValueError:
            raise ValidationError({"quantity": _("Invalid quantity provided")})

        # Create a new stock item
        if line.part:
            stock = stock_models.StockItem(
                part=line.part.part,
                supplier_part=line.part,
                location=location,
                quantity=quantity,
                purchase_order=self,
                status=status
            )

            stock.save()

            # Add a new transaction note to the newly created stock item
            stock.addTransactionNote("Received items", user, "Received {q} items against order '{po}'".format(
                q=quantity,
                po=str(self))
            )

        # Update the number of parts received against the particular line item
        line.received += quantity
        line.save()

        # Has this order been completed?
        if len(self.pending_line_items()) == 0:
            
            self.received_by = user
            self.complete_order()  # This will save the model


class SalesOrder(Order):
    """
    A SalesOrder represents a list of goods shipped outwards to a customer.

    Attributes:
        customer: Reference to the company receiving the goods in the order
        customer_reference: Optional field for customer order reference code
    """

    def __str__(self):
        return "SO {ref} - {company}".format(ref=self.reference, company=self.customer.name)

    def get_absolute_url(self):
        return reverse('so-detail', kwargs={'pk': self.id})

    customer = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_customer': True},
        related_name='sales_orders',
        help_text=_("Company to which the items are being sold"),
    )

    status = models.PositiveIntegerField(default=SalesOrderStatus.PENDING, choices=SalesOrderStatus.items(),
                                         help_text=_('Purchase order status'))

    customer_reference = models.CharField(max_length=64, blank=True, help_text=_("Customer order reference code"))

    shipment_date = models.DateField(blank=True, null=True)

    shipped_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='+'
    )

    @property
    def is_pending(self):
        return self.status == SalesOrderStatus.PENDING

    def is_fully_allocated(self):
        """ Return True if all line items are fully allocated """

        for line in self.lines.all():
            if not line.is_fully_allocated():
                return False
            
        return True

    def is_over_allocated(self):
        """ Return true if any lines in the order are over-allocated """

        for line in self.lines.all():
            if line.is_over_allocated():
                return True

        return False

    @transaction.atomic
    def ship_order(self, user):
        """ Mark this order as 'shipped' """

        # The order can only be 'shipped' if the current status is PENDING
        if not self.status == SalesOrderStatus.PENDING:
            raise ValidationError({'status': _("SalesOrder cannot be shipped as it is not currently pending")})

        # Complete the allocation for each allocated StockItem
        for line in self.lines.all():
            for allocation in line.allocations.all():
                allocation.complete_allocation(user)

                # Remove the allocation from the database once it has been 'fulfilled'
                if allocation.item.sales_order == self:
                    allocation.delete()
                else:
                    raise ValidationError("Could not complete order - allocation item not fulfilled")

        # Ensure the order status is marked as "Shipped"
        self.status = SalesOrderStatus.SHIPPED
        self.shipment_date = datetime.now().date()
        self.shipped_by = user
        self.save()

        return True

    @transaction.atomic
    def cancel_order(self):
        """
        Cancel this order (only if it is "pending")

        - Mark the order as 'cancelled'
        - Delete any StockItems which have been allocated
        """

        if not self.status == SalesOrderStatus.PENDING:
            return False

        self.status = SalesOrderStatus.CANCELLED
        self.save()

        for line in self.lines.all():
            for allocation in line.allocations.all():
                allocation.delete()

        return True


class PurchaseOrderAttachment(InvenTreeAttachment):
    """
    Model for storing file attachments against a PurchaseOrder object
    """

    def getSubdir(self):
        return os.path.join("po_files", str(self.order.id))

    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="attachments")


class SalesOrderAttachment(InvenTreeAttachment):
    """
    Model for storing file attachments against a SalesOrder object
    """

    def getSubdir(self):
        return os.path.join("so_files", str(self.order.id))

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='attachments')


class OrderLineItem(models.Model):
    """ Abstract model for an order line item
    
    Attributes:
        quantity: Number of items
        note: Annotation for the item
        
    """

    class Meta:
        abstract = True

    quantity = RoundingDecimalField(max_digits=15, decimal_places=5, validators=[MinValueValidator(0)], default=1, help_text=_('Item quantity'))

    reference = models.CharField(max_length=100, blank=True, help_text=_('Line item reference'))
    
    notes = models.CharField(max_length=500, blank=True, help_text=_('Line item notes'))


class PurchaseOrderLineItem(OrderLineItem):
    """ Model for a purchase order line item.
    
    Attributes:
        order: Reference to a PurchaseOrder object

    """

    class Meta:
        unique_together = (
            ('order', 'part')
        )

    def __str__(self):
        return "{n} x {part} from {supplier} (for {po})".format(
            n=decimal2string(self.quantity),
            part=self.part.SKU if self.part else 'unknown part',
            supplier=self.order.supplier.name,
            po=self.order)

    order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE,
        related_name='lines',
        help_text=_('Purchase Order')
    )

    def get_base_part(self):
        """ Return the base-part for the line item """
        return self.part.part
    
    # TODO - Function callback for when the SupplierPart is deleted?

    part = models.ForeignKey(
        SupplierPart, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='purchase_order_line_items',
        help_text=_("Supplier part"),
    )

    received = models.DecimalField(decimal_places=5, max_digits=15, default=0, help_text=_('Number of items received'))

    def remaining(self):
        """ Calculate the number of items remaining to be received """
        r = self.quantity - self.received
        return max(r, 0)


class SalesOrderLineItem(OrderLineItem):
    """
    Model for a single LineItem in a SalesOrder

    Attributes:
        order: Link to the SalesOrder that this line item belongs to
        part: Link to a Part object (may be null)
    """

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines', help_text=_('Sales Order'))

    part = models.ForeignKey('part.Part', on_delete=models.SET_NULL, related_name='sales_order_line_items', null=True, help_text=_('Part'), limit_choices_to={'salable': True})

    class Meta:
        unique_together = [
            ('order', 'part'),
        ]

    def fulfilled_quantity(self):
        """
        Return the total stock quantity fulfilled against this line item.
        """

        query = self.order.stock_items.filter(part=self.part).aggregate(fulfilled=Coalesce(Sum('quantity'), Decimal(0)))

        return query['fulfilled']

    def allocated_quantity(self):
        """ Return the total stock quantity allocated to this LineItem.

        This is a summation of the quantity of each attached StockItem
        """

        query = self.allocations.aggregate(allocated=Coalesce(Sum('quantity'), Decimal(0)))

        return query['allocated']

    def is_fully_allocated(self):
        """ Return True if this line item is fully allocated """

        if self.order.status == SalesOrderStatus.SHIPPED:
            return self.fulfilled_quantity() >= self.quantity

        return self.allocated_quantity() >= self.quantity

    def is_over_allocated(self):
        """ Return True if this line item is over allocated """
        return self.allocated_quantity() > self.quantity


class SalesOrderAllocation(models.Model):
    """
    This model is used to 'allocate' stock items to a SalesOrder.
    Items that are "allocated" to a SalesOrder are not yet "attached" to the order,
    but they will be once the order is fulfilled.

    Attributes:
        line: SalesOrderLineItem reference
        item: StockItem reference
        quantity: Quantity to take from the StockItem

    """

    class Meta:
        unique_together = [
            # Cannot allocate any given StockItem to the same line more than once
            ('line', 'item'),
        ]

    def clean(self):
        """
        Validate the SalesOrderAllocation object:

        - Cannot allocate stock to a line item without a part reference
        - The referenced part must match the part associated with the line item
        - Allocated quantity cannot exceed the quantity of the stock item
        - Allocation quantity must be "1" if the StockItem is serialized
        - Allocation quantity cannot be zero
        """

        super().clean()

        errors = {}

        try:
            if not self.line.part == self.item.part:
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

        if self.item.serial and not self.quantity == 1:
            errors['quantity'] = _('Quantity must be 1 for serialized stock item')

        if len(errors) > 0:
            raise ValidationError(errors)

    line = models.ForeignKey(SalesOrderLineItem, on_delete=models.CASCADE, related_name='allocations')

    item = models.ForeignKey(
        'stock.StockItem',
        on_delete=models.CASCADE,
        related_name='sales_order_allocations',
        limit_choices_to={
            'part__salable': True,
            'belongs_to': None,
            'sales_order': None,
            'build_order': None,
        },
        help_text=_('Select stock item to allocate')
    )

    quantity = RoundingDecimalField(max_digits=15, decimal_places=5, validators=[MinValueValidator(0)], default=1, help_text=_('Enter stock allocation quantity'))

    def get_serial(self):
        return self.item.serial

    def get_location(self):
        return self.item.location.id if self.item.location else None

    def get_location_path(self):
        if self.item.location:
            return self.item.location.pathstring
        else:
            return ""

    def complete_allocation(self, user):
        """
        Complete this allocation (called when the parent SalesOrder is marked as "shipped"):

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

        # Update our own reference to the StockItem
        # (It may have changed if the stock was split)
        self.item = item
        self.save()
