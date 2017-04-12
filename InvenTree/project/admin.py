from django.contrib import admin

from .models import ProjectCategory, Project, ProjectPart, ProjectRun


class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'description')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'category')


class ProjectPartAdmin(admin.ModelAdmin):
    list_display = ('part', 'project', 'quantity', 'output')


class ProjectRunAdmin(admin.ModelAdmin):
    list_display = ('project', 'quantity', 'run_date')


admin.site.register(ProjectCategory, ProjectCategoryAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectPart, ProjectPartAdmin)
admin.site.register(ProjectRun, ProjectRunAdmin)
