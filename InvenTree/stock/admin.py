"""Admin for stock app."""

from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from import_export import widgets
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

from build.models import Build
from company.models import Company, SupplierPart
from InvenTree.admin import InvenTreeResource
from order.models import PurchaseOrder, SalesOrder
from part.models import Part

from .models import (StockItem, StockItemAttachment, StockItemTestResult,
                     StockItemTracking, StockLocation, StockLocationType)


class LocationResource(InvenTreeResource):
    """Class for managing StockLocation data import/export."""

    class Meta:
        """Metaclass options."""

        model = StockLocation
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

        exclude = [
            # Exclude MPTT internal model fields
            'lft', 'rght', 'tree_id', 'level',
            'metadata',
            'barcode_data', 'barcode_hash',
            'owner', 'icon',
        ]

    id = Field(attribute='id', column_name=_('Location ID'), widget=widgets.IntegerWidget())
    name = Field(attribute='name', column_name=_('Location Name'))
    description = Field(attribute='description', column_name=_('Description'))
    parent = Field(attribute='parent', column_name=_('Parent ID'), widget=widgets.ForeignKeyWidget(StockLocation))
    parent_name = Field(attribute='parent__name', column_name=_('Parent Name'), readonly=True)
    pathstring = Field(attribute='pathstring', column_name=_('Location Path'))

    # Calculated fields
    items = Field(attribute='item_count', column_name=_('Stock Items'), widget=widgets.IntegerWidget(), readonly=True)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """Rebuild after import to keep tree intact."""
        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the StockLocation tree(s)
        StockLocation.objects.rebuild()


class LocationInline(admin.TabularInline):
    """Inline for sub-locations."""
    model = StockLocation


@admin.register(StockLocation)
class LocationAdmin(ImportExportModelAdmin):
    """Admin class for Location."""

    resource_class = LocationResource

    list_display = ('name', 'pathstring', 'description')

    search_fields = ('name', 'description')

    inlines = [
        LocationInline,
    ]

    autocomplete_fields = [
        'parent',
    ]


@admin.register(StockLocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    """Admin class for StockLocationType."""

    list_display = ('name', 'description', 'icon', 'location_count')
    readonly_fields = ('location_count', )

    def get_queryset(self, request):
        """Annotate queryset to fetch location count."""
        return super().get_queryset(request).annotate(
            location_count=Count("stock_locations"),
        )

    def location_count(self, obj):
        """Returns the number of locations this location type is assigned to."""
        return obj.location_count


class StockItemResource(InvenTreeResource):
    """Class for managing StockItem data import/export."""

    class Meta:
        """Metaclass options."""

        model = StockItem
        skip_unchanged = True
        report_skipped = False
        clean_model_instance = True

        exclude = [
            # Exclude MPTT internal model fields
            'lft', 'rght', 'tree_id', 'level',
            # Exclude internal fields
            'serial_int', 'metadata',
            'barcode_hash', 'barcode_data',
            'owner',
        ]

    id = Field(attribute='pk', column_name=_('Stock Item ID'), widget=widgets.IntegerWidget())
    part = Field(attribute='part', column_name=_('Part ID'), widget=widgets.ForeignKeyWidget(Part))
    part_name = Field(attribute='part__full_name', column_name=_('Part Name'), readonly=True)
    quantity = Field(attribute='quantity', column_name=_('Quantity'), widget=widgets.DecimalWidget())
    serial = Field(attribute='serial', column_name=_('Serial'))
    batch = Field(attribute='batch', column_name=_('Batch'))
    status_label = Field(attribute='status_label', column_name=_('Status'), readonly=True)
    status = Field(attribute='status', column_name=_('Status Code'), widget=widgets.IntegerWidget())
    location = Field(attribute='location', column_name=_('Location ID'), widget=widgets.ForeignKeyWidget(StockLocation))
    location_name = Field(attribute='location__name', column_name=_('Location Name'), readonly=True)
    supplier_part = Field(attribute='supplier_part', column_name=_('Supplier Part ID'), widget=widgets.ForeignKeyWidget(SupplierPart))
    supplier = Field(attribute='supplier_part__supplier__id', column_name=_('Supplier ID'), readonly=True, widget=widgets.IntegerWidget())
    supplier_name = Field(attribute='supplier_part__supplier__name', column_name=_('Supplier Name'), readonly=True)
    customer = Field(attribute='customer', column_name=_('Customer ID'), widget=widgets.ForeignKeyWidget(Company))
    belongs_to = Field(attribute='belongs_to', column_name=_('Installed In'), widget=widgets.ForeignKeyWidget(StockItem))
    build = Field(attribute='build', column_name=_('Build ID'), widget=widgets.ForeignKeyWidget(Build))
    parent = Field(attribute='parent', column_name=_('Parent ID'), widget=widgets.ForeignKeyWidget(StockItem))
    sales_order = Field(attribute='sales_order', column_name=_('Sales Order ID'), widget=widgets.ForeignKeyWidget(SalesOrder))
    purchase_order = Field(attribute='purchase_order', column_name=_('Purchase Order ID'), widget=widgets.ForeignKeyWidget(PurchaseOrder))
    packaging = Field(attribute='packaging', column_name=_('Packaging'))
    link = Field(attribute='link', column_name=_('Link'))
    notes = Field(attribute='notes', column_name=_('Notes'))

    # Status fields (note that IntegerWidget exports better to excel than BooleanWidget)
    is_building = Field(attribute='is_building', column_name=_('Building'), widget=widgets.IntegerWidget())
    review_needed = Field(attribute='review_needed', column_name=_('Review Needed'), widget=widgets.IntegerWidget())
    delete_on_deplete = Field(attribute='delete_on_deplete', column_name=_('Delete on Deplete'), widget=widgets.IntegerWidget())

    # Date management
    updated = Field(attribute='updated', column_name=_('Last Updated'), widget=widgets.DateWidget())
    stocktake_date = Field(attribute='stocktake_date', column_name=_('Stocktake'), widget=widgets.DateWidget())
    expiry_date = Field(attribute='expiry_date', column_name=_('Expiry Date'), widget=widgets.DateWidget())

    def dehydrate_purchase_price(self, item):
        """Render purchase pric as float"""
        if item.purchase_price is not None:
            return float(item.purchase_price.amount)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """Rebuild after import to keep tree intact."""
        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # Rebuild the StockItem tree(s)
        StockItem.objects.rebuild()


@admin.register(StockItem)
class StockItemAdmin(ImportExportModelAdmin):
    """Admin class for StockItem."""

    resource_class = StockItemResource

    list_display = ('part', 'quantity', 'location', 'status', 'updated')

    # A list of search fields which can be used for lookup on matching 'autocomplete' fields
    search_fields = [
        'part__name',
        'part__description',
        'serial',
        'batch',
    ]

    autocomplete_fields = [
        'belongs_to',
        'build',
        'customer',
        'location',
        'parent',
        'part',
        'purchase_order',
        'sales_order',
        'stocktake_user',
        'supplier_part',
    ]


@admin.register(StockItemAttachment)
class StockAttachmentAdmin(admin.ModelAdmin):
    """Admin class for StockAttachment."""

    list_display = ('stock_item', 'attachment', 'comment')

    autocomplete_fields = [
        'stock_item',
    ]


@admin.register(StockItemTracking)
class StockTrackingAdmin(ImportExportModelAdmin):
    """Admin class for StockTracking."""

    list_display = ('item', 'date', 'label')

    autocomplete_fields = [
        'item',
    ]


@admin.register(StockItemTestResult)
class StockItemTestResultAdmin(admin.ModelAdmin):
    """Admin class for StockItemTestResult."""

    list_display = ('stock_item', 'test', 'result', 'value')

    autocomplete_fields = [
        'stock_item',
    ]
