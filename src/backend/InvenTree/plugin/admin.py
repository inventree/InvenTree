"""Admin for plugin app."""

from django.contrib import admin

from plugin import models
from plugin.registry import registry as pl_registry


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

    read_only_fields = ['key']

    def has_add_permission(self, request, obj):
        """The plugin settings should not be meddled with manually."""
        return False


class PluginUserSettingInline(admin.TabularInline):
    """Inline admin class for PluginUserSetting."""

    model = models.PluginUserSetting

    read_only_fields = ['key']

    def has_add_permission(self, request, obj):
        """The plugin user settings should not be meddled with manually."""
        return False


class PluginConfigAdmin(admin.ModelAdmin):
    """Custom admin with restricted id fields."""

    readonly_fields = ['key', 'name', 'package_name']
    list_display = [
        'name',
        'key',
        'active',
        'is_builtin',
        'is_sample',
        'is_installed',
        'is_package',
    ]
    list_filter = ['active']
    actions = [plugin_activate, plugin_deactivate]
    inlines = [PluginSettingInline, PluginUserSettingInline]
    exclude = ['metadata']
    search_fields = ['name', 'key']


admin.site.register(models.PluginConfig, PluginConfigAdmin)
