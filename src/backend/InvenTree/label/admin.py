"""Admin functionality for the 'label' app."""

from django.contrib import admin

import label.models


class LabelAdmin(admin.ModelAdmin):
    """Admin class for the various label models."""

    list_display = ('name', 'description', 'label', 'filters', 'enabled')


admin.site.register(label.models.StockItemLabel, LabelAdmin)
admin.site.register(label.models.StockLocationLabel, LabelAdmin)
admin.site.register(label.models.PartLabel, LabelAdmin)
admin.site.register(label.models.BuildLineLabel, LabelAdmin)
