"""Admin functionality for the 'report' app."""

from django.contrib import admin

from .helpers import report_model_options
from .models import (
    LabelOutput,
    LabelTemplate,
    ReportAsset,
    ReportOutput,
    ReportSnippet,
    ReportTemplate,
)


@admin.register(LabelTemplate)
@admin.register(ReportTemplate)
class ReportAdmin(admin.ModelAdmin):
    """Admin class for the LabelTemplate and ReportTemplate models."""

    list_display = ('name', 'description', 'model_type', 'enabled')

    list_filter = ('model_type', 'enabled')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Provide custom choices for 'model_type' field."""
        if db_field.name == 'model_type':
            db_field.choices = report_model_options()

        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(ReportSnippet)
class ReportSnippetAdmin(admin.ModelAdmin):
    """Admin class for the ReportSnippet model."""

    list_display = ('id', 'snippet', 'description')


@admin.register(ReportAsset)
class ReportAssetAdmin(admin.ModelAdmin):
    """Admin class for the ReportAsset model."""

    list_display = ('id', 'asset', 'description')


@admin.register(LabelOutput)
@admin.register(ReportOutput)
class TemplateOutputAdmin(admin.ModelAdmin):
    """Admin class for the TemplateOutput model."""

    list_display = ('id', 'output', 'progress', 'complete')
