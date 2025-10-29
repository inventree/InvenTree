"""Admin classes for the 'web' app."""

from django.contrib import admin

from web.models import GuideDefinition, GuideExecution


class GuideExecutionInline(admin.TabularInline):
    """Inline for guide executions."""

    model = GuideExecution
    extra = 1


@admin.register(GuideDefinition)
class GuideDefinitionAdmin(admin.ModelAdmin):
    """Admin class for the GuideDefinition model."""

    list_display = ('guide_type', 'name', 'slug')
    list_filter = ('guide_type',)
    inlines = [GuideExecutionInline]
    fields = ('guide_type', 'name', 'slug', 'description', 'data', 'metadata')
    prepopulated_fields = {'slug': ('name',)}
