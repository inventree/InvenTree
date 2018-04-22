class SupplierOrder(models.Model):
    """
    An order of parts from a supplier, made up of multiple line items
    """

    def get_absolute_url(self):
        return "/supplier/order/{id}/".format(id=self.id)

    # Interal reference for this order
    internal_ref = models.CharField(max_length=25, unique=True)

    supplier = models.ForeignKey(Company, on_delete=models.CASCADE,
                                 related_name='orders')

    created_date = models.DateField(auto_now_add=True, editable=False)

    issued_date = models.DateField(blank=True, null=True, help_text="Date the purchase order was issued")

    notes = models.TextField(blank=True, help_text="Order notes")

    def __str__(self):
        return "PO {ref} ({status})".format(ref=self.internal_ref,
                                            status=self.get_status_display)

    PENDING = 10  # Order is pending (not yet placed)
    PLACED = 20  # Order has been placed
    RECEIVED = 30  # Order has been received
    CANCELLED = 40  # Order was cancelled
    LOST = 50  # Order was lost

    ORDER_STATUS_CODES = {PENDING: _("Pending"),
                          PLACED: _("Placed"),
                          CANCELLED: _("Cancelled"),
                          RECEIVED: _("Received"),
                          LOST: _("Lost")
                         }

    status = models.PositiveIntegerField(default=PENDING,
                                         choices=ORDER_STATUS_CODES.items())

    delivery_date = models.DateField(blank=True, null=True)



class SupplierOrderLineItem(models.Model):
    """
    A line item in a supplier order, corresponding to some quantity of part
    """

    class Meta:
        unique_together = [
            ('order', 'line_number'),
            ('order', 'supplier_part'),
            ('order', 'internal_part'),
        ]

    order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE)

    line_number = models.PositiveIntegerField(default=1)

    internal_part = models.ForeignKey(Part, null=True, blank=True, on_delete=models.SET_NULL)

    supplier_part = models.ForeignKey(SupplierPart, null=True, blank=True, on_delete=models.SET_NULL)

    quantity = models.PositiveIntegerField(default=1)

    notes = models.TextField(blank=True)

    received = models.BooleanField(default=False)
