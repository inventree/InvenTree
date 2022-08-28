"""Admin for plugin app."""

from django.contrib import admin

import plugin.models as models
import plugin.registry as pl_registry
from common.models import WebConnection


def plugin_update(queryset, new_status: bool):
    """General function for bulk changing plugins."""
    apps_changed = False

    # Run through all plugins in the queryset as the save method needs to be overridden
    for plugin in queryset:
        if plugin.active is not new_status:
            plugin.active = new_status
            plugin.save(no_reload=True)
            apps_changed = True

    # Reload plugins if they changed
    if apps_changed:
        pl_registry.reload_plugins()


@admin.action(description='Activate plugin(s)')
def plugin_activate(modeladmin, request, queryset):
    """Activate a set of plugins."""
    plugin_update(queryset, True)


@admin.action(description='Deactivate plugin(s)')
def plugin_deactivate(modeladmin, request, queryset):
    """Deactivate a set of plugins."""
    plugin_update(queryset, False)


class PluginSettingInline(admin.TabularInline):
    """Inline admin class for PluginSetting."""

    model = models.PluginSetting

    read_only_fields = [
        'key',
    ]

    def has_add_permission(self, request, obj):
        """The plugin settings should not be meddled with manually."""
        return False


class WebConnectionInline(admin.TabularInline):
    """Inline admin class for WebConnection."""

    model = WebConnection
    inlines = [PluginSettingInline, ]

    read_only_fields = [
        'plugin',
        'connection_key',
        'creator',
        'creation',
    ]

    def has_add_permission(self, request, obj):
        """The plugin settings should not be meddled with manually."""
        return False


class PluginConfigAdmin(admin.ModelAdmin):
    """Custom admin with restricted id fields."""

    readonly_fields = ["key", "name", ]
    list_display = ['name', 'key', '__str__', 'active', 'is_sample']
    list_filter = ['active']
    actions = [plugin_activate, plugin_deactivate, ]
    inlines = [PluginSettingInline, WebConnectionInline]


class NotificationUserSettingAdmin(admin.ModelAdmin):
    """Admin class for NotificationUserSetting."""

    model = models.NotificationUserSetting

    read_only_fields = [
        'key',
    ]

    def has_add_permission(self, request):
        """Notifications should not be changed."""
        return False


admin.site.register(models.PluginConfig, PluginConfigAdmin)
admin.site.register(models.NotificationUserSetting, NotificationUserSettingAdmin)
