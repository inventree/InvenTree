from django.contrib import admin

from .models import PartCategory, Part

class PartAdmin(admin.ModelAdmin):

    list_display = ('name', 'IPN', 'description', 'stock', 'category')


class PartCategoryAdmin(admin.ModelAdmin):

    list_display = ('name', 'pathstring', 'description')

"""
class ParameterTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'units', 'format')


class ParameterAdmin(admin.ModelAdmin):
    list_display = ('part', 'template', 'value')
"""

admin.site.register(Part, PartAdmin)
admin.site.register(PartCategory, PartCategoryAdmin)

#admin.site.register(PartParameter, ParameterAdmin)
#admin.site.register(PartParameterTemplate, ParameterTemplateAdmin)
#admin.site.register(CategoryParameterLink)
