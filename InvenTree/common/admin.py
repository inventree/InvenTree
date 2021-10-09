# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from .models import InvenTreeSetting, InvenTreeUserSetting


class SettingsAdmin(ImportExportModelAdmin):

    list_display = ('key', 'value')


class UserSettingsAdmin(ImportExportModelAdmin):

    list_display = ('key', 'value', 'user', )


admin.site.register(InvenTreeSetting, SettingsAdmin)
admin.site.register(InvenTreeUserSetting, UserSettingsAdmin)
