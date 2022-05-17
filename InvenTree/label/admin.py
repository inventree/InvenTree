from django.contrib import admin

from .models import StockItemLabel, StockLocationLabel, PartLabel


class LabelAdmin(admin.ModelAdmin):

    list_display = ('name', 'description', 'label', 'filters', 'enabled')


admin.site.register(StockItemLabel, LabelAdmin)
admin.site.register(StockLocationLabel, LabelAdmin)
admin.site.register(PartLabel, LabelAdmin)
