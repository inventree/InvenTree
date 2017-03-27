from django.contrib import admin

from .models import PartCategory, Part

admin.site.register(Part)

# Custom form for PartCategory
class PartCategoryAdmin(admin.ModelAdmin):
    # TODO - Only let valid parents be displayed
    pass

    
admin.site.register(PartCategory, PartCategoryAdmin)