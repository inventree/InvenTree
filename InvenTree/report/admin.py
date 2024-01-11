"""Admin functionality for the 'report' app"""

from django.contrib import admin

from .models import (
    BillOfMaterialsReport,
    BuildReport,
    PurchaseOrderReport,
    ReportAsset,
    ReportSnippet,
    ReturnOrderReport,
    SalesOrderReport,
    StockLocationReport,
    TestReport,
)


@admin.register(
    BillOfMaterialsReport,
    BuildReport,
    PurchaseOrderReport,
    ReturnOrderReport,
    SalesOrderReport,
    StockLocationReport,
    TestReport,
)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Admin class for the various reporting models"""

    list_display = ('name', 'description', 'template', 'filters', 'enabled', 'revision')


@admin.register(ReportSnippet)
class ReportSnippetAdmin(admin.ModelAdmin):
    """Admin class for the ReportSnippet model"""

    list_display = ('id', 'snippet', 'description')


@admin.register(ReportAsset)
class ReportAssetAdmin(admin.ModelAdmin):
    """Admin class for the ReportAsset model"""

    list_display = ('id', 'asset', 'description')
