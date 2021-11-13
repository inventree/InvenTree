# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

import plugin.models as models


class PluginConfigAdmin(admin.ModelAdmin):
    """Custom admin with restricted id fields"""
    readonly_fields = ["key", "name", ]


admin.site.register(models.PluginConfig, PluginConfigAdmin)
