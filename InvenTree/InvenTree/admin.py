"""Admin classes."""

from django.contrib import admin
from django.http.request import HttpRequest

from djmoney.contrib.exchange.admin import RateAdmin
from djmoney.contrib.exchange.models import Rate
from import_export.exceptions import ImportExportError
from import_export.resources import ModelResource


class InvenTreeResource(ModelResource):
    """Custom subclass of the ModelResource class provided by django-import-export".

    Ensures that exported data are escaped to prevent malicious formula injection.
    Ref: https://owasp.org/www-community/attacks/CSV_Injection
    """

    MAX_IMPORT_ROWS = 1000
    MAX_IMPORT_COLS = 100

    def import_data_inner(
        self,
        dataset,
        dry_run,
        raise_errors,
        using_transactions,
        collect_failed_rows,
        rollback_on_validation_errors=None,
        **kwargs,
    ):
        """Override the default import_data_inner function to provide better error handling."""
        if len(dataset) > self.MAX_IMPORT_ROWS:
            raise ImportExportError(
                f'Dataset contains too many rows (max {self.MAX_IMPORT_ROWS})'
            )

        if len(dataset.headers) > self.MAX_IMPORT_COLS:
            raise ImportExportError(
                f'Dataset contains too many columns (max {self.MAX_IMPORT_COLS})'
            )

        return super().import_data_inner(
            dataset,
            dry_run,
            raise_errors,
            using_transactions,
            collect_failed_rows,
            rollback_on_validation_errors=rollback_on_validation_errors,
            **kwargs,
        )

    def export_resource(self, obj):
        """Custom function to override default row export behavior.

        Specifically, strip illegal leading characters to prevent formula injection
        """
        row = super().export_resource(obj)

        illegal_start_vals = ['@', '=', '+', '-', '@', '\t', '\r', '\n']

        for idx, val in enumerate(row):
            if type(val) is str:
                val = val.strip()

                # If the value starts with certain 'suspicious' values, remove it!
                while len(val) > 0 and val[0] in illegal_start_vals:
                    # Remove the first character
                    val = val[1:]

                row[idx] = val

        return row

    def get_fields(self, **kwargs):
        """Return fields, with some common exclusions."""
        fields = super().get_fields(**kwargs)

        fields_to_exclude = ['metadata', 'lft', 'rght', 'tree_id', 'level']

        return [f for f in fields if f.column_name not in fields_to_exclude]


class CustomRateAdmin(RateAdmin):
    """Admin interface for the Rate class."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable the 'add' permission for Rate objects."""
        return False


admin.site.unregister(Rate)
admin.site.register(Rate, CustomRateAdmin)
