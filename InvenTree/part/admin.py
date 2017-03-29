from django.contrib import admin

from .models import PartCategory, Part, PartParameter, PartParameterTemplate


class PartAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'IPN', 'stock', 'category')


class PartCategoryAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'path', 'description')
    

class ParameterTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'units', 'category')


class ParameterAdmin(admin.ModelAdmin):
    list_display = ('part', 'template', 'value')

    
admin.site.register(Part, PartAdmin)
admin.site.register(PartCategory, PartCategoryAdmin)

admin.site.register(PartParameter, ParameterAdmin)
admin.site.register(PartParameterTemplate, ParameterTemplateAdmin)