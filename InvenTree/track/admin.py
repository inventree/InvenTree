from django.contrib import admin

from .models import UniquePart, PartTrackingInfo


class UniquePartAdmin(admin.ModelAdmin):
    list_display = ('part', 'serial', 'status', 'creation_date')


class PartTrackingAdmin(admin.ModelAdmin):
    list_display = ('part', 'date', 'title')


admin.site.register(UniquePart, UniquePartAdmin)
admin.site.register(PartTrackingInfo, PartTrackingAdmin)
