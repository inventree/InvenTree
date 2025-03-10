"""Admin site specification for the 'importer' app."""

from django.contrib import admin

import importer.models
import importer.registry


class DataImportColumnMapAdmin(admin.TabularInline):
    """Inline admin for DataImportColumnMap model."""

    model = importer.models.DataImportColumnMap
    can_delete = False
    max_num = 0

    def get_readonly_fields(self, request, obj=None):
        """Return the readonly fields for the admin interface."""
        return ['field']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Override the choices for the column field."""
        if db_field.name == 'column':
            # TODO: Implement this!
            queryset = self.get_queryset(request)

            if queryset.count() > 0:
                session = queryset.first().session
                db_field.choices = [(col, col) for col in session.columns]

        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(importer.models.DataImportSession)
class DataImportSessionAdmin(admin.ModelAdmin):
    """Admin interface for the DataImportSession model."""

    list_display = ['id', 'data_file', 'status', 'user']

    list_filter = ['status']

    inlines = [DataImportColumnMapAdmin]

    def get_readonly_fields(self, request, obj=None):
        """Update the readonly fields for the admin interface."""
        fields = ['columns', 'status', 'timestamp']

        # Prevent data file from being edited after upload!
        if obj:
            fields += ['data_file']
        else:
            fields += ['field_mapping']

        return fields

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Override the choices for the model_type field."""
        if db_field.name == 'model_type':
            db_field.choices = importer.registry.supported_model_options()

        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(importer.models.DataImportRow)
class DataImportRowAdmin(admin.ModelAdmin):
    """Admin interface for the DataImportRow model."""

    list_display = ['id', 'session', 'row_index']

    def get_readonly_fields(self, request, obj=None):
        """Return the readonly fields for the admin interface."""
        return ['session', 'row_index', 'row_data', 'errors', 'valid']
