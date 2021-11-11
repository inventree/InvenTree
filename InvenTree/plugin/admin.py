# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

import plugin.models as models


admin.site.register(models.PluginConfig, admin.ModelAdmin)
