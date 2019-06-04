from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

from django.utils.translation import ugettext as _

from part.models import Part
from company.models import Company
from stock.models import StockItem


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

    # Order status codes
    PENDING = 10  # Order is pending (not yet placed)
    PLACED = 20  # Order has been placed
    RECEIVED = 30  # Order has been received
    CANCELLED = 40  # Order was cancelled
    LOST = 50  # Order was lost
    RETURNED = 60 # Order was returned

    class Meta:
        abstract = True

    reference = models.CharField(unique=True, max_length=64, blank=False, help_text=_('Order reference'))

    description = models.CharField(max_length=250, blank=True, help_text=_('Order description'))

    URL = models.URLField(blank=True, help_text=_('Link to external page'))

    creation_date = models.DateField(auto_now=True, editable=False)

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

    supplier = models.ForeignKey(Company, on_delete=models.CASCADE,
                                limit_choices_to={
                                    'is_supplier': True,
                                },
                                related_name=_('Orders'),
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

    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE,
                              related_name='lines',
                              help_text=_('Purchase Order')
                              )

    # TODO - foreign key references to part and stockitem objects

    received = models.PositiveIntegerField(default=0, help_text=_('Number of items received'))
