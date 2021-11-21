# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

import plugin.models as models
from plugin import plugin_reg


def plugin_update(queryset, new_status: bool):
    """general function for bulk changing plugins"""
    apps_changed = False

    # run through all plugins in the queryset as the save method needs to be overridden
    for plugin in queryset:
        if plugin.active is not new_status:
            plugin.active = new_status
            plugin.save(no_reload=True)
            apps_changed = True

    # reload plugins if they changed
    if apps_changed:
        plugin_reg.reload_plugins()


@admin.action(description='Activate plugin(s)')
def plugin_activate(modeladmin, request, queryset):
    """activate a set of plugins"""
    plugin_update(queryset, True)


@admin.action(description='Deactivate plugin(s)')
def plugin_deactivate(modeladmin, request, queryset):
    """deactivate a set of plugins"""
    plugin_update(queryset, False)


class PluginConfigAdmin(admin.ModelAdmin):
    """Custom admin with restricted id fields"""
    readonly_fields = ["key", "name", ]
    list_display = ['active', '__str__', 'key', 'name', ]
    list_filter = ['active']
    actions = [plugin_activate, plugin_deactivate, ]


admin.site.register(models.PluginConfig, PluginConfigAdmin)
