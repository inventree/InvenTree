from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

from django.utils.translation import ugettext as _

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

    """

    ORDER_PREFIX = ""

    def __str__(self):
        el = []

        if self.ORDER_PREFIX:
            el.append(self.ORDER_PREFIX)

        el.append(self.reference)

        return " ".join(el)

    class Meta:
        abstract = True

    reference = models.CharField(unique=True, max_length=64, blank=False, help_text=_('Order reference'))

    description = models.CharField(max_length=250, help_text=_('Order description'))

    URL = models.URLField(blank=True, help_text=_('Link to external page'))

    creation_date = models.DateField(auto_now=True, editable=False)

    status = models.PositiveIntegerField(default=OrderStatus.PENDING, choices=OrderStatus.items(),
                                         help_text='Order status')

    created_by = models.ForeignKey(User,
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='+'
                                   )

    issue_date = models.DateField(blank=True, null=True)

    notes = models.TextField(blank=True, help_text=_('Order notes'))


class PurchaseOrder(Order):
    """ A PurchaseOrder represents goods shipped inwards from an external supplier.

    Attributes:
        supplier: Reference to the company supplying the goods in the order

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


class PurchaseOrderLineItem(OrderLineItem):
    """ Model for a purchase order line item.
    
    Attributes:
        order: Reference to a PurchaseOrder object

    """

    class Meta:
        unique_together = (
            ('order', 'part')
        )

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
