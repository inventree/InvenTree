"""Admin site specification for the 'importer' app."""

from django.contrib import admin

import importer.models


@admin.register(importer.models.DataImportSession)
class DataImportSessionAdmin(admin.ModelAdmin):
    """Admin interface for the DataImportSession model."""

    list_display = ['id', 'data_file', 'status', 'progress', 'user']

    list_filter = ['status']


@admin.register(importer.models.DataImportRow)
class DataImportRowAdmin(admin.ModelAdmin):
    """Admin interface for the DataImportRow model."""

    list_display = ['id', 'session', 'row_index']
