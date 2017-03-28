from django.contrib import admin

from .models import PartCategory, Part

class PartAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'IPN', 'category')

# Custom form for PartCategory
class PartCategoryAdmin(admin.ModelAdmin):

    list_display = ('name', 'path')

    
admin.site.register(Part, PartAdmin)
admin.site.register(PartCategory, PartCategoryAdmin)