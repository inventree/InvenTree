from django.contrib import admin

from .models import PartCategory, Part


class PartAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'IPN', 'stock', 'category')


class PartCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'path', 'description')
    
admin.site.register(Part, PartAdmin)
admin.site.register(PartCategory, PartCategoryAdmin)
