from django.contrib import admin

from .models import PartCategory, Part

admin.site.register(Part)
admin.site.register(PartCategory)
