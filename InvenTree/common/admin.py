# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from .models import InvenTreeSetting, ExtensionSetting


class SettingsAdmin(ImportExportModelAdmin):

    list_display = ('key', 'value')


class ExtensionSettingsAdmin(ImportExportModelAdmin):

    list_display = ('extension', 'setting', 'type', 'value', 'label',
                    'description')


admin.site.register(InvenTreeSetting, SettingsAdmin)
admin.site.register(ExtensionSetting, ExtensionSettingsAdmin)
