from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Company


class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('name', 'website', 'contact')


admin.site.register(Company, CompanyAdmin)
