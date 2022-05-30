"""Admin for the common app."""

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

import common.models


@admin.site.register(common.models.InvenTreeSetting)
class SettingsAdmin(ImportExportModelAdmin):
    """Admin settings for InvenTreeSetting."""

    list_display = ('key', 'value')

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        else:
            return []


@admin.site.register(common.models.InvenTreeUserSetting)
class UserSettingsAdmin(ImportExportModelAdmin):
    """Admin settings for InvenTreeUserSetting."""

    list_display = ('key', 'value', 'user', )

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        else:
            return []


@admin.site.register(common.models.WebhookEndpoint)
class WebhookAdmin(ImportExportModelAdmin):
    """Admin settings for Webhook."""

    list_display = ('endpoint_id', 'name', 'active', 'user')


@admin.site.register(common.models.NotificationEntry)
class NotificationEntryAdmin(admin.ModelAdmin):
    """Admin settings for NotificationEntry."""

    list_display = ('key', 'uid', 'updated', )


@admin.site.register(common.models.NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    """Admin settings for NotificationMessage."""

    list_display = ('age_human', 'user', 'category', 'name', 'read', 'target_object', 'source_object', )

    list_filter = ('category', 'read', 'user', )

    search_fields = ('name', 'category', 'message', )


# Register Models to admin
admin.site.register(common.models.WebhookMessage, ImportExportModelAdmin)
