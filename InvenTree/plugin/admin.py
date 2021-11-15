# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.apps import apps

import plugin.models as models


def plugin_update(queryset, new_status: bool):
    """general function for bulk changing plugins"""
    for model in queryset:
        model.active = new_status
        model.save(no_reload=True)

    app = apps.get_app_config('plugin')
    app.reload_plugins()


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
    list_display = ['key', 'name', 'active', ]
    actions = [plugin_activate, plugin_deactivate, ]


admin.site.register(models.PluginConfig, PluginConfigAdmin)
