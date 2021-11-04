# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

import common.models


class SettingsAdmin(ImportExportModelAdmin):

    list_display = ('key', 'value')


class UserSettingsAdmin(ImportExportModelAdmin):

    list_display = ('key', 'value', 'user', )


class NotificationEntryAdmin(admin.ModelAdmin):

    list_display = ('key', 'uid', 'updated', )


admin.site.register(common.models.InvenTreeSetting, SettingsAdmin)
admin.site.register(common.models.InvenTreeUserSetting, UserSettingsAdmin)
admin.site.register(common.models.NotificationEntry, NotificationEntryAdmin)
