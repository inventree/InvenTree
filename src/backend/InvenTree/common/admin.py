"""Admin for the common app."""

from django.contrib import admin

import common.models
import common.validators


@admin.register(common.models.ParameterTemplate)
class ParameterTemplateAdmin(admin.ModelAdmin):
    """Admin interface for ParameterTemplate objects."""

    list_display = ('name', 'description', 'model_type', 'units', 'unique')
    search_fields = ('name', 'description')


@admin.register(common.models.Parameter)
class ParameterAdmin(admin.ModelAdmin):
    """Admin interface for Parameter objects."""

    list_display = (
        'template',
        'model_type',
        'model_id',
        'data',
        'updated',
        'updated_by',
    )

    autocomplete_fields = ('template', 'updated_by')
    list_filter = ('template', 'model_type', 'updated_by')
    search_fields = ('template__name', 'data', 'note')


class SelectionListEntryInlineAdmin(admin.StackedInline):
    """Inline admin class for the SelectionListEntry model."""

    model = common.models.SelectionListEntry
    extra = 0


@admin.register(common.models.SelectionList)
class SelectionListAdmin(admin.ModelAdmin):
    """Admin interface for SelectionList objects."""

    list_display = ('name', 'description', 'active', 'locked')
    search_fields = ('name', 'description')
    list_filter = ('active', 'locked')

    inlines = [SelectionListEntryInlineAdmin]


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


@admin.register(common.models.DataOutput)
class DataOutputAdmin(admin.ModelAdmin):
    """Admin interface for DataOutput objects - view and delete only."""

    list_display = ('user', 'created', 'output_type', 'output')

    list_filter = ('user', 'output_type')

    def has_add_permission(self, request):
        """Prevent addition of new DataOutput objects via the admin interface."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of DataOutput objects via the admin interface."""
        return False


@admin.register(common.models.BarcodeScanResult)
class BarcodeScanResultAdmin(admin.ModelAdmin):
    """Admin interface for BarcodeScanResult objects - read-only audit log."""

    list_display = ('data', 'timestamp', 'user', 'endpoint', 'result')

    list_filter = ('user', 'endpoint', 'result')

    def has_add_permission(self, request):
        """Prevent addition of new BarcodeScanResult objects via the admin interface."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of BarcodeScanResult objects via the admin interface."""
        return False


@admin.register(common.models.ProjectCode)
class ProjectCodeAdmin(admin.ModelAdmin):
    """Admin settings for ProjectCode."""

    list_display = ('code', 'description', 'active')
    list_filter = ('active',)

    search_fields = ('code', 'description')


@admin.register(common.models.InvenTreeSetting)
class SettingsAdmin(admin.ModelAdmin):
    """Admin settings for InvenTreeSetting."""

    list_display = ('key', 'value')

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        return []


@admin.register(common.models.InvenTreeUserSetting)
class UserSettingsAdmin(admin.ModelAdmin):
    """Admin settings for InvenTreeUserSetting."""

    list_display = ('key', 'value', 'user')

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover
        """Prevent the 'key' field being edited once the setting is created."""
        if obj:
            return ['key']
        return []


@admin.register(common.models.WebhookEndpoint)
class WebhookAdmin(admin.ModelAdmin):
    """Admin settings for Webhook."""

    list_display = ('endpoint_id', 'name', 'active', 'user')


@admin.register(common.models.NotificationEntry)
class NotificationEntryAdmin(admin.ModelAdmin):
    """Admin settings for NotificationEntry - view and delete only."""

    list_display = ('key', 'uid', 'updated')

    def has_add_permission(self, request):
        """Prevent addition of new NotificationEntry objects via the admin interface."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of NotificationEntry objects via the admin interface."""
        return False


@admin.register(common.models.NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    """Admin settings for NotificationMessage - view and delete only."""

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

    def has_add_permission(self, request):
        """Prevent addition of new NotificationMessage objects via the admin interface."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of NotificationMessage objects via the admin interface."""
        return False


@admin.register(common.models.NewsFeedEntry)
class NewsFeedEntryAdmin(admin.ModelAdmin):
    """Admin settings for NewsFeedEntry - view and delete only."""

    list_display = ('title', 'author', 'published', 'summary')

    def has_add_permission(self, request):
        """Prevent addition of new NewsFeedEntry objects via the admin interface."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of NewsFeedEntry objects via the admin interface."""
        return False


class ReadOnlyAdmin(admin.ModelAdmin):
    """Base admin class that prevents all modifications."""

    def has_add_permission(self, request):
        """Prevent addition of new objects via the admin interface."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent modification of objects via the admin interface."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of objects via the admin interface."""
        return False


admin.site.register(common.models.WebhookMessage, ReadOnlyAdmin)
admin.site.register(common.models.EmailMessage, ReadOnlyAdmin)
admin.site.register(common.models.EmailThread, ReadOnlyAdmin)
