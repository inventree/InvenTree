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

from stock.models import StockItem
from company.models import Company, SupplierPart
from part.models import Part

from InvenTree.fields import RoundingDecimalField
from InvenTree.helpers import decimal2string
from InvenTree.status_codes import OrderStatus
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

    status = models.PositiveIntegerField(default=OrderStatus.PENDING, choices=OrderStatus.items(),
                                         help_text='Order status')

    created_by = models.ForeignKey(User,
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='+'
                                   )

    issue_date = models.DateField(blank=True, null=True)

    complete_date = models.DateField(blank=True, null=True)

    notes = MarkdownxField(blank=True, help_text=_('Order notes'))

    def place_order(self):
        """ Marks the order as PLACED. Order must be currently PENDING. """

        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.PLACED
            self.issue_date = datetime.now().date()
            self.save()

    def complete_order(self):
        """ Marks the order as COMPLETE. Order must be currently PLACED. """

        if self.status == OrderStatus.PLACED:
            self.status = OrderStatus.COMPLETE
            self.complete_date = datetime.now().date()
            self.save()

    def cancel_order(self):
        """ Marks the order as CANCELLED. """

        if self.status in [OrderStatus.PLACED, OrderStatus.PENDING]:
            self.status = OrderStatus.CANCELLED
            self.save()


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

    supplier = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        limit_choices_to={
            'is_supplier': True,
        },
        related_name='purchase_orders',
        help_text=_('Supplier')
    )

    supplier_reference = models.CharField(max_length=64, blank=True, help_text=_("Supplier order reference code"))

    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='+'
    )

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
    def receive_line_item(self, line, location, quantity, user):
        """ Receive a line item (or partial line item) against this PO
        """

        if not self.status == OrderStatus.PLACED:
            raise ValidationError({"status": _("Lines can only be received against an order marked as 'Placed'")})

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValidationError({"quantity": _("Quantity must be greater than zero")})
        except ValueError:
            raise ValidationError({"quantity": _("Invalid quantity provided")})

        # Create a new stock item
        if line.part:
            stock = StockItem(
                part=line.part.part,
                supplier_part=line.part,
                location=location,
                quantity=quantity,
                purchase_order=self)

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

    customer = models.ForeignKey(Company,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'is_customer': True},
        related_name='sales_orders',
        help_text=_("Customer"),
    )

    customer_reference = models.CharField(max_length=64, blank=True, help_text=_("Customer order reference code"))


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

    part = models.ForeignKey(Part, on_delete=models.SET_NULL, related_name='sales_order_line_items', null=True, help_text=_('Part'), limit_choices_to={'salable': True})

    def allocated_quantity(self):
        """ Return the total stock quantity allocated to this LineItem.

        This is a summation of the quantity of each attached StockItem
        """

        query = self.stock_items.aggregate(allocated=Coalesce(Sum('stock_item__quantity'), Decimal(0)))

        return query['allocated']
