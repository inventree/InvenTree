"""Admin site specification for the 'importer' app."""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

import importer.models


class DataImportColumnMapAdmin(admin.TabularInline):
    """Inline admin for DataImportColumnMap model."""

    model = importer.models.DataImportColumnMap
    can_delete = False
    max_num = 0

    def get_readonly_fields(self, request, obj=None):
        """Return the readonly fields for the admin interface."""
        return ['column']


@admin.register(importer.models.DataImportSession)
class DataImportSessionAdmin(admin.ModelAdmin):
    """Admin interface for the DataImportSession model."""

    list_display = ['id', 'data_file', 'status', 'user']

    list_filter = ['status']

    inlines = [DataImportColumnMapAdmin]

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

    def get_readonly_fields(self, request, obj=None):
        """Return the readonly fields for the admin interface."""
        return ['session', 'row_index', 'row_data', 'errors', 'valid']
