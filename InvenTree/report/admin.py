from django.contrib import admin

from .models import ReportSnippet, ReportAsset
from .models import TestReport
from .models import BuildReport
from .models import BillOfMaterialsReport
from .models import PurchaseOrderReport
from .models import SalesOrderReport


class ReportTemplateAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'template', 'filters', 'enabled', 'revision')


class ReportSnippetAdmin(admin.ModelAdmin):

    list_display = ('id', 'snippet', 'description')


class ReportAssetAdmin(admin.ModelAdmin):

    list_display = ('id', 'asset', 'description')


admin.site.register(ReportSnippet, ReportSnippetAdmin)
admin.site.register(ReportAsset, ReportAssetAdmin)

admin.site.register(TestReport, ReportTemplateAdmin)
admin.site.register(BuildReport, ReportTemplateAdmin)
admin.site.register(BillOfMaterialsReport, ReportTemplateAdmin)
admin.site.register(PurchaseOrderReport, ReportTemplateAdmin)
admin.site.register(SalesOrderReport, ReportTemplateAdmin)
