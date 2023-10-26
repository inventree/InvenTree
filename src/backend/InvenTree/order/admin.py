"""Admin functionality for the 'order' app"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from import_export import widgets
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

from InvenTree.admin import InvenTreeResource
from order import models


class ProjectCodeResourceMixin:
    """Mixin for exporting project code data"""

    project_code = Field(attribute='project_code', column_name=_('Project Code'))

    def dehydrate_project_code(self, order):
        """Return the project code value, not the pk"""
        if order.project_code:
            return order.project_code.code
        return ''


class TotalPriceResourceMixin:
    """Mixin for exporting total price data"""

    total_price = Field(attribute='total_price', column_name=_('Total Price'))

    def dehydrate_total_price(self, order):
        """Return the total price amount, not the object itself"""
        if order.total_price:
            return order.total_price.amount
        return ''


class PriceResourceMixin:
    """Mixin for 'price' field"""

    price = Field(attribute='price', column_name=_('Price'))

    def dehydrate_price(self, line):
        """Return the price amount, not the object itself"""
        if line.price:
            return line.price.amount
        return ''


# region general classes
class GeneralExtraLineAdmin:
    """Admin class template for the 'ExtraLineItem' models"""
    list_display = (
        'order',
        'quantity',
        'reference'
    )

    search_fields = [
        'order__reference',
        'order__customer__name',
        'reference',
    ]

    autocomplete_fields = ('order', )


class GeneralExtraLineMeta:
    """Metaclass template for the 'ExtraLineItem' models"""
    skip_unchanged = True
    report_skipped = False
    clean_model_instances = True
# endregion


class PurchaseOrderLineItemInlineAdmin(admin.StackedInline):
    """Inline admin class for the PurchaseOrderLineItem model"""
    model = models.PurchaseOrderLineItem
    extra = 0


class PurchaseOrderAdmin(ImportExportModelAdmin):
    """Admin class for the PurchaseOrder model"""

    exclude = [
        'reference_int',
    ]

    list_display = (
        'reference',
        'supplier',
        'status',
        'description',
        'creation_date'
    )

    search_fields = [
        'reference',
        'supplier__name',
        'description',
    ]

    inlines = [
        PurchaseOrderLineItemInlineAdmin
    ]

    autocomplete_fields = ('supplier',)


class SalesOrderAdmin(ImportExportModelAdmin):
    """Admin class for the SalesOrder model"""

    exclude = [
        'reference_int',
    ]

    list_display = (
        'reference',
        'customer',
        'status',
        'description',
        'creation_date',
    )

    search_fields = [
        'reference',
        'customer__name',
        'description',
    ]

    autocomplete_fields = ('customer',)


class PurchaseOrderResource(ProjectCodeResourceMixin, TotalPriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of PurchaseOrder data."""

    class Meta:
        """Metaclass"""
        model = models.PurchaseOrder
        skip_unchanged = True
        clean_model_instances = True
        exclude = [
            'metadata',
        ]

    # Add number of line items
    line_items = Field(attribute='line_count', widget=widgets.IntegerWidget(), readonly=True)

    # Is this order overdue?
    overdue = Field(attribute='is_overdue', widget=widgets.BooleanWidget(), readonly=True)


class PurchaseOrderLineItemResource(PriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of PurchaseOrderLineItem data."""

    class Meta:
        """Metaclass"""
        model = models.PurchaseOrderLineItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

    part_name = Field(attribute='part__part__name', readonly=True)

    manufacturer = Field(attribute='part__manufacturer', readonly=True)

    MPN = Field(attribute='part__MPN', readonly=True)

    SKU = Field(attribute='part__SKU', readonly=True)

    def dehydrate_purchase_price(self, line):
        """Return a string value of the 'purchase_price' field, rather than the 'Money' object"""
        if line.purchase_price:
            return line.purchase_price.amount
        return ''


class PurchaseOrderExtraLineResource(PriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of PurchaseOrderExtraLine data."""

    class Meta(GeneralExtraLineMeta):
        """Metaclass options."""

        model = models.PurchaseOrderExtraLine


class SalesOrderResource(ProjectCodeResourceMixin, TotalPriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of SalesOrder data."""

    class Meta:
        """Metaclass options"""
        model = models.SalesOrder
        skip_unchanged = True
        clean_model_instances = True
        exclude = [
            'metadata',
        ]

    # Add number of line items
    line_items = Field(attribute='line_count', widget=widgets.IntegerWidget(), readonly=True)

    # Is this order overdue?
    overdue = Field(attribute='is_overdue', widget=widgets.BooleanWidget(), readonly=True)


class SalesOrderLineItemResource(PriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of SalesOrderLineItem data."""

    class Meta:
        """Metaclass options"""
        model = models.SalesOrderLineItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

    part_name = Field(attribute='part__name', readonly=True)

    IPN = Field(attribute='part__IPN', readonly=True)

    description = Field(attribute='part__description', readonly=True)

    fulfilled = Field(attribute='fulfilled_quantity', readonly=True)

    def dehydrate_sale_price(self, item):
        """Return a string value of the 'sale_price' field, rather than the 'Money' object.

        Ref: https://github.com/inventree/InvenTree/issues/2207
        """
        if item.sale_price:
            return str(item.sale_price)
        return ''


class SalesOrderExtraLineResource(PriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of SalesOrderExtraLine data."""

    class Meta(GeneralExtraLineMeta):
        """Metaclass options."""
        model = models.SalesOrderExtraLine


class PurchaseOrderLineItemAdmin(ImportExportModelAdmin):
    """Admin class for the PurchaseOrderLine model"""

    resource_class = PurchaseOrderLineItemResource

    list_display = (
        'order',
        'part',
        'quantity',
        'reference'
    )

    search_fields = ('reference',)

    autocomplete_fields = ('order', 'part', 'destination',)


class PurchaseOrderExtraLineAdmin(GeneralExtraLineAdmin, ImportExportModelAdmin):
    """Admin class for the PurchaseOrderExtraLine model"""
    resource_class = PurchaseOrderExtraLineResource


class SalesOrderLineItemAdmin(ImportExportModelAdmin):
    """Admin class for the SalesOrderLine model"""

    resource_class = SalesOrderLineItemResource

    list_display = (
        'order',
        'part',
        'quantity',
        'reference'
    )

    search_fields = [
        'part__name',
        'order__reference',
        'order__customer__name',
        'reference',
    ]

    autocomplete_fields = ('order', 'part',)


class SalesOrderExtraLineAdmin(GeneralExtraLineAdmin, ImportExportModelAdmin):
    """Admin class for the SalesOrderExtraLine model"""
    resource_class = SalesOrderExtraLineResource


class SalesOrderShipmentAdmin(ImportExportModelAdmin):
    """Admin class for the SalesOrderShipment model"""

    list_display = [
        'order',
        'shipment_date',
        'reference',
    ]

    search_fields = [
        'reference',
        'order__reference',
        'order__customer__name',
    ]

    autocomplete_fields = ('order',)


class SalesOrderAllocationAdmin(ImportExportModelAdmin):
    """Admin class for the SalesOrderAllocation model"""

    list_display = (
        'line',
        'item',
        'quantity'
    )

    autocomplete_fields = ('line', 'shipment', 'item',)


class ReturnOrderResource(ProjectCodeResourceMixin, TotalPriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of ReturnOrder data"""

    class Meta:
        """Metaclass options"""
        model = models.ReturnOrder
        skip_unchanged = True
        clean_model_instances = True
        exclude = [
            'metadata',
        ]


class ReturnOrderAdmin(ImportExportModelAdmin):
    """Admin class for the ReturnOrder model"""

    exclude = [
        'reference_int',
    ]

    list_display = [
        'reference',
        'customer',
        'status',
    ]

    search_fields = [
        'reference',
        'customer__name',
        'description',
    ]

    autocomplete_fields = [
        'customer',
    ]


class ReturnOrderLineItemResource(PriceResourceMixin, InvenTreeResource):
    """Class for managing import / export of ReturnOrderLineItem data"""

    class Meta:
        """Metaclass options"""
        model = models.ReturnOrderLineItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True


class ReturnOrderLineItemAdmin(ImportExportModelAdmin):
    """Admin class for ReturnOrderLine model"""

    resource_class = ReturnOrderLineItemResource

    list_display = [
        'order',
        'item',
        'reference',
    ]


class ReturnOrderExtraLineClass(PriceResourceMixin, InvenTreeResource):
    """Class for managing import/export of ReturnOrderExtraLine data"""

    class Meta(GeneralExtraLineMeta):
        """Metaclass options"""
        model = models.ReturnOrderExtraLine


class ReturnOrdeerExtraLineAdmin(GeneralExtraLineAdmin, ImportExportModelAdmin):
    """Admin class for the ReturnOrderExtraLine model"""
    resource_class = ReturnOrderExtraLineClass


# Purchase Order models
admin.site.register(models.PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(models.PurchaseOrderLineItem, PurchaseOrderLineItemAdmin)
admin.site.register(models.PurchaseOrderExtraLine, PurchaseOrderExtraLineAdmin)

# Sales Order models
admin.site.register(models.SalesOrder, SalesOrderAdmin)
admin.site.register(models.SalesOrderLineItem, SalesOrderLineItemAdmin)
admin.site.register(models.SalesOrderExtraLine, SalesOrderExtraLineAdmin)
admin.site.register(models.SalesOrderShipment, SalesOrderShipmentAdmin)
admin.site.register(models.SalesOrderAllocation, SalesOrderAllocationAdmin)

# Return Order models
admin.site.register(models.ReturnOrder, ReturnOrderAdmin)
admin.site.register(models.ReturnOrderLineItem, ReturnOrderLineItemAdmin)
admin.site.register(models.ReturnOrderExtraLine, ReturnOrdeerExtraLineAdmin)
