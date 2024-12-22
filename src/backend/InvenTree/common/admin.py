"""Admin for the common app."""

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

import common.models
import common.validators


@admin.register(common.models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """Admin interface for Attachment objects."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Provide custom choices for 'model_type' field."""
        if db_field.name == 'model_type':
            db_field.choices = common.validators.attachment_model_options()

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    list_display = (
        'model_type',
        'model_id',
        'attachment',
        'link',
        'upload_user',
        'upload_date',
    )

    list_filter = ['model_type', 'upload_user']

    readonly_fields = ['file_size', 'upload_date', 'upload_user']

    search_fields = ('content_type', 'comment')


@admin.register(common.models.BarcodeScanResult)
class BarcodeScanResultAdmin(admin.ModelAdmin):
    """Admin interface for BarcodeScanResult objects."""

    list_display = ('data', 'timestamp', 'user', 'endpoint', 'result')

    list_filter = ('user', 'endpoint', 'result')


@admin.register(common.models.ProjectCode)
class ProjectCodeAdmin(ImportExportModelAdmin):
    """Admin settings for ProjectCode."""

    list_display = ('code', 'description')

    search_fields = ('code', 'description')


@admin.register(common.models.InvenTreeSetting)
class SettingsAdmin(ImportExportModelAdmin):
    """Admin settings for InvenTreeSetting."""

    list_display = ('key', 'value')

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        return []


@admin.register(common.models.InvenTreeUserSetting)
class UserSettingsAdmin(ImportExportModelAdmin):
    """Admin settings for InvenTreeUserSetting."""

    list_display = ('key', 'value', 'user')

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        return []


@admin.register(common.models.WebhookEndpoint)
class WebhookAdmin(ImportExportModelAdmin):
    """Admin settings for Webhook."""

    list_display = ('endpoint_id', 'name', 'active', 'user')


@admin.register(common.models.NotificationEntry)
class NotificationEntryAdmin(admin.ModelAdmin):
    """Admin settings for NotificationEntry."""

    list_display = ('key', 'uid', 'updated')


@admin.register(common.models.NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    """Admin settings for NotificationMessage."""

    list_display = (
        'age_human',
        'user',
        'category',
        'name',
        'read',
        'target_object',
        'source_object',
    )

    list_filter = ('category', 'read', 'user')

    search_fields = ('name', 'category', 'message')


@admin.register(common.models.NewsFeedEntry)
class NewsFeedEntryAdmin(admin.ModelAdmin):
    """Admin settings for NewsFeedEntry."""

    list_display = ('title', 'author', 'published', 'summary')


admin.site.register(common.models.WebhookMessage, ImportExportModelAdmin)
