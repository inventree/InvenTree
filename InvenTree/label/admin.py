# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import StockItemLabel


class StockItemLabelAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'label', 'filters', 'enabled')


admin.site.register(StockItemLabel, StockItemLabelAdmin)
