"""Admin functionality for the 'report' app."""

from django.contrib import admin

from .models import (
    BillOfMaterialsReport,
    BuildReport,
    PurchaseOrderReport,
    ReportAsset,
    ReportSnippet,
    ReportTemplate,
    ReturnOrderReport,
    SalesOrderReport,
    StockLocationReport,
    TestReport,
)


@admin.register(ReportTemplate)
class ReportAdmin(admin.ModelAdmin):
    """Admin class for the ReportTemplate model."""

    list_display = ('name', 'description', 'model_type', 'enabled')


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
    """Admin class for the various reporting models."""

    list_display = ('name', 'description', 'template', 'filters', 'enabled', 'revision')


@admin.register(ReportSnippet)
class ReportSnippetAdmin(admin.ModelAdmin):
    """Admin class for the ReportSnippet model."""

    list_display = ('id', 'snippet', 'description')


@admin.register(ReportAsset)
class ReportAssetAdmin(admin.ModelAdmin):
    """Admin class for the ReportAsset model."""

    list_display = ('id', 'asset', 'description')
