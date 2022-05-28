from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

import common.models


class SettingsAdmin(ImportExportModelAdmin):

    list_display = ('key', 'value')

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        else:
            return []


class UserSettingsAdmin(ImportExportModelAdmin):

    list_display = ('key', 'value', 'user', )

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        else:
            return []


class WebhookAdmin(ImportExportModelAdmin):

    list_display = ('endpoint_id', 'name', 'active', 'user')


class NotificationEntryAdmin(admin.ModelAdmin):

    list_display = ('key', 'uid', 'updated', )


class NotificationMessageAdmin(admin.ModelAdmin):

    list_display = ('age_human', 'user', 'category', 'name', 'read', 'target_object', 'source_object', )

    list_filter = ('category', 'read', 'user', )

    search_fields = ('name', 'category', 'message', )


admin.site.register(common.models.InvenTreeSetting, SettingsAdmin)
admin.site.register(common.models.InvenTreeUserSetting, UserSettingsAdmin)
admin.site.register(common.models.WebhookEndpoint, WebhookAdmin)
admin.site.register(common.models.WebhookMessage, ImportExportModelAdmin)
admin.site.register(common.models.NotificationEntry, NotificationEntryAdmin)
admin.site.register(common.models.NotificationMessage, NotificationMessageAdmin)
