# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from .models import InvenTreeSetting


class SettingsAdmin(ImportExportModelAdmin):
    
    list_display = ('key', 'value')


admin.site.register(InvenTreeSetting, SettingsAdmin)
