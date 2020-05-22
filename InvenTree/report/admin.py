# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import ReportTemplate, ReportAsset
from .models import TestReport


class ReportTemplateAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'template')


class ReportAssetAdmin(admin.ModelAdmin):

    list_display = ('asset', 'description')


admin.site.register(ReportTemplate, ReportTemplateAdmin)
admin.site.register(TestReport, ReportTemplateAdmin)
admin.site.register(ReportAsset, ReportAssetAdmin)
