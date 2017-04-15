from django.contrib import admin

from .models import UniquePart


class UniquePartAdmin(admin.ModelAdmin):
    list_display = ('part', 'serial', 'status', 'creation_date')


admin.site.register(UniquePart, UniquePartAdmin)
