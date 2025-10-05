"""Admin functionality for the 'order' app."""

from django.contrib import admin

from order import models


class GeneralExtraLineAdmin:
    """Admin class template for the 'ExtraLineItem' models."""

    list_display = ('order', 'quantity', 'reference')

    search_fields = ['order__reference', 'order__customer__name', 'reference']

    autocomplete_fields = ('order',)


class GeneralExtraLineMeta:
    """Metaclass template for the 'ExtraLineItem' models."""

    skip_unchanged = True
    report_skipped = False
    clean_model_instances = True


class PurchaseOrderLineItemInlineAdmin(admin.StackedInline):
    """Inline admin class for the PurchaseOrderLineItem model."""

    autocomplete_fields = ['part', 'destination', 'build_order']

    model = models.PurchaseOrderLineItem
    extra = 0


@admin.register(models.PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin class for the PurchaseOrder model."""

    exclude = ['reference_int']

    list_display = ('reference', 'supplier', 'status', 'description', 'creation_date')

    search_fields = ['reference', 'supplier__name', 'description']

    inlines = [PurchaseOrderLineItemInlineAdmin]

    autocomplete_fields = [
        'address',
        'contact',
        'created_by',
        'destination',
        'supplier',
        'project_code',
        'received_by',
        'responsible',
    ]


class SalesOrderLineItemInlineAdmin(admin.StackedInline):
    """Inline admin class for the SalesOrderLineItem model."""

    model = models.SalesOrderLineItem
    extra = 0

    autocomplete_fields = ['part']


@admin.register(models.SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    """Admin class for the SalesOrder model."""

    exclude = ['reference_int']

    list_display = (
        'reference',
        'customer',
        'status',
        'description',
        'creation_date',
        'tax_configuration',
        'tax_rate',
        'tax_amount',
        'total_with_tax',
    )

    search_fields = ['reference', 'customer__name', 'description']

    inlines = [SalesOrderLineItemInlineAdmin]

    autocomplete_fields = [
        'address',
        'contact',
        'created_by',
        'customer',
        'project_code',
        'responsible',
        'shipped_by',
        'tax_configuration',
    ]

    readonly_fields = ['creation_date', 'tax_amount', 'total_with_tax']

    def get_readonly_fields(self, request, obj=None):
        """Make tax fields readonly for completed orders."""
        readonly_fields = list(super().get_readonly_fields(request, obj))

        if obj and obj.status in [20, 30, 40]:  # PENDING, SHIPPED, CANCELLED
            readonly_fields.extend([
                'tax_configuration_reference',
                'tax_rate',
                'tax_inclusive',
            ])

        return readonly_fields


@admin.register(models.PurchaseOrderLineItem)
class PurchaseOrderLineItemAdmin(admin.ModelAdmin):
    """Admin class for the PurchaseOrderLine model."""

    list_display = ('order', 'part', 'quantity', 'reference')

    search_fields = ('reference',)

    autocomplete_fields = ('order', 'part', 'destination')


@admin.register(models.PurchaseOrderExtraLine)
class PurchaseOrderExtraLineAdmin(GeneralExtraLineAdmin, admin.ModelAdmin):
    """Admin class for the PurchaseOrderExtraLine model."""


@admin.register(models.SalesOrderLineItem)
class SalesOrderLineItemAdmin(admin.ModelAdmin):
    """Admin class for the SalesOrderLine model."""

    list_display = (
        'order',
        'part',
        'quantity',
        'sale_price',
        'tax_rate',
        'tax_amount',
        'price_with_tax',
        'reference',
    )

    search_fields = [
        'part__name',
        'order__reference',
        'order__customer__name',
        'reference',
    ]

    autocomplete_fields = ('order', 'part')

    readonly_fields = ['tax_amount', 'price_with_tax']


@admin.register(models.SalesOrderExtraLine)
class SalesOrderExtraLineAdmin(GeneralExtraLineAdmin, admin.ModelAdmin):
    """Admin class for the SalesOrderExtraLine model."""


@admin.register(models.SalesOrderShipment)
class SalesOrderShipmentAdmin(admin.ModelAdmin):
    """Admin class for the SalesOrderShipment model."""

    list_display = ['order', 'shipment_date', 'reference']

    search_fields = ['reference', 'order__reference', 'order__customer__name']

    autocomplete_fields = ('order', 'checked_by')


@admin.register(models.SalesOrderAllocation)
class SalesOrderAllocationAdmin(admin.ModelAdmin):
    """Admin class for the SalesOrderAllocation model."""

    list_display = ('line', 'item', 'quantity')

    autocomplete_fields = ('line', 'shipment', 'item')


@admin.register(models.ReturnOrder)
class ReturnOrderAdmin(admin.ModelAdmin):
    """Admin class for the ReturnOrder model."""

    exclude = ['reference_int']

    list_display = ['reference', 'customer', 'status']

    search_fields = ['reference', 'customer__name', 'description']

    autocomplete_fields = ['customer', 'project_code', 'contact', 'address']


@admin.register(models.ReturnOrderLineItem)
class ReturnOrderLineItemAdmin(admin.ModelAdmin):
    """Admin class for ReturnOrderLine model."""

    list_display = ['order', 'item', 'reference']

    autocomplete_fields = ['item', 'order']


@admin.register(models.ReturnOrderExtraLine)
class ReturnOrdeerExtraLineAdmin(GeneralExtraLineAdmin, admin.ModelAdmin):
    """Admin class for the ReturnOrderExtraLine model."""
