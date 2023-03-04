"""Admin functionality for the 'report' app"""

from django.contrib import admin

from .models import (BillOfMaterialsReport, BuildReport, PurchaseOrderReport,
                     ReportAsset, ReportSnippet, SalesOrderReport, TestReport)


class ReportTemplateAdmin(admin.ModelAdmin):
    """Admin class for the various reporting models"""
    list_display = ('name', 'description', 'template', 'filters', 'enabled', 'revision')


class ReportSnippetAdmin(admin.ModelAdmin):
    """Admin class for the ReportSnippet model"""
    list_display = ('id', 'snippet', 'description')


class ReportAssetAdmin(admin.ModelAdmin):
    """Admin class for the ReportAsset model"""
    list_display = ('id', 'asset', 'description')


admin.site.register(ReportSnippet, ReportSnippetAdmin)
admin.site.register(ReportAsset, ReportAssetAdmin)

admin.site.register(TestReport, ReportTemplateAdmin)
admin.site.register(BuildReport, ReportTemplateAdmin)
admin.site.register(BillOfMaterialsReport, ReportTemplateAdmin)
admin.site.register(PurchaseOrderReport, ReportTemplateAdmin)
admin.site.register(SalesOrderReport, ReportTemplateAdmin)
