"""
Order model definitions
"""

# -*- coding: utf-8 -*-

from django.db import models, transaction
from django.db.models import F
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.translation import ugettext as _

from datetime import datetime

from stock.models import StockItem
from company.models import Company, SupplierPart

from InvenTree.status_codes import OrderStatus


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

    URL = models.URLField(blank=True, help_text=_('Link to external page'))

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

    notes = models.TextField(blank=True, help_text=_('Order notes'))

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
        received_by: User that received the goods
    """

    ORDER_PREFIX = "PO"

    supplier = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        limit_choices_to={
            'is_supplier': True,
        },
        related_name='purchase_orders',
        help_text=_('Company')
    )

    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='+'
    )

    def get_absolute_url(self):
        return reverse('purchase-order-detail', kwargs={'pk': self.id})

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


class OrderLineItem(models.Model):
    """ Abstract model for an order line item
    
    Attributes:
        quantity: Number of items
        note: Annotation for the item
        
    """

    class Meta:
        abstract = True

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=1, help_text=_('Item quantity'))

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
            n=self.quantity,
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

    received = models.PositiveIntegerField(default=0, help_text=_('Number of items received'))

    def remaining(self):
        """ Calculate the number of items remaining to be received """
        r = self.quantity - self.received
        return max(r, 0)
