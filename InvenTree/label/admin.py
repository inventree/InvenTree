"""Admin functionality for the 'label' app"""

from django.contrib import admin

from .models import PartLabel, StockItemLabel, StockLocationLabel


class LabelAdmin(admin.ModelAdmin):
    """Admin class for the various label models"""
    list_display = ('name', 'description', 'label', 'filters', 'enabled')


admin.site.register(StockItemLabel, LabelAdmin)
admin.site.register(StockLocationLabel, LabelAdmin)
admin.site.register(PartLabel, LabelAdmin)
