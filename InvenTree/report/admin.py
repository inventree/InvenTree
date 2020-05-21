# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import ReportTemplate


class ReportTemplateAdmin(admin.ModelAdmin):

    list_display = ('template', 'description')


admin.site.register(ReportTemplate, ReportTemplateAdmin)
