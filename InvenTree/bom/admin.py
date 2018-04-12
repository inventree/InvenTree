from django.contrib import admin

from .models import BomItem

class BomItemAdmin(admin.ModelAdmin):
    list_display=('part', 'sub_part', 'quantity')

admin.site.register(BomItem, BomItemAdmin)