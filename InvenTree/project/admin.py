from django.contrib import admin

from .models import ProjectCategory, Project, ProjectPart

class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name','path')
    
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'category')
    
class ProjectPartAdmin(admin.ModelAdmin):
    list_display = ('part', 'project', 'quantity')

admin.site.register(ProjectCategory, ProjectCategoryAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectPart, ProjectPartAdmin)