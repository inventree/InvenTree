"""Admin site specification for the 'importer' app."""

from django.contrib import admin

import importer.models


@admin.register(importer.models.DataImportSession)
class DataImportSessionAdmin(admin.ModelAdmin):
    """Admin interface for the DataImportSession model."""

    list_display = ['id', 'data_file', 'status', 'user']

    list_filter = ['status']

    def get_readonly_fields(self, request, obj=None):
        """Update the readonly fields for the admin interface."""
        fields = ['columns', 'status']

        # Prevent data file from being edited after upload!
        if obj:
            fields += ['data_file']
        else:
            fields += ['field_mapping']

        return fields


@admin.register(importer.models.DataImportRow)
class DataImportRowAdmin(admin.ModelAdmin):
    """Admin interface for the DataImportRow model."""

    list_display = ['id', 'session', 'row_index']
