# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import StockItemLabel, StockLocationLabel


class LabelAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'label', 'filters', 'enabled')


admin.site.register(StockItemLabel, LabelAdmin)
admin.site.register(StockLocationLabel, LabelAdmin)
