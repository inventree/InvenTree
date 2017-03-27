from django.contrib import admin

from .models import ProjectCategory, Project, ProjectPart

admin.site.register(ProjectCategory)
admin.site.register(Project)
admin.site.register(ProjectPart)