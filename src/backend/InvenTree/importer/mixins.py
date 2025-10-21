"""Mixin classes for data import/export functionality."""

from rest_framework import fields, serializers
from taggit.serializers import TagListSerializerField


class DataImportSerializerMixin:
    """Mixin class for adding data import functionality to a DRF serializer."""

    import_only_fields = []
    import_exclude_fields = []

    def get_import_only_fields(self, **kwargs) -> list:
        """Return the list of field names which are only used during data import."""
        return self.import_only_fields

    def get_import_exclude_fields(self, **kwargs) -> list:
        """Return the list of field names which are excluded during data import."""
        return self.import_exclude_fields

    def __init__(self, *args, **kwargs):
        """Initialise the DataImportSerializerMixin.

        Determine if the serializer is being used for data import,
        and if so, adjust the serializer fields accordingly.
        """
        importing = kwargs.pop('importing', False)

        super().__init__(*args, **kwargs)

        if importing:
            # Exclude any fields which are not able to be imported
            importable_field_names = list(self.get_importable_fields().keys())
            field_names = list(self.fields.keys())

            for field in field_names:
                if field not in importable_field_names:
                    self.fields.pop(field, None)

            # Exclude fields which are excluded for data import
            for field in self.get_import_exclude_fields(**kwargs):
                self.fields.pop(field, None)

        else:
            # Exclude fields which are only used for data import
            for field in self.get_import_only_fields(**kwargs):
                self.fields.pop(field, None)

    def get_importable_fields(self) -> dict:
        """Return a dict of fields which can be imported against this serializer instance.

        Returns:
            dict: A dictionary of field names and field objects
        """
        importable_fields = {}

        if meta := getattr(self, 'Meta', None):
            read_only_fields = getattr(meta, 'read_only_fields', [])
        else:
            read_only_fields = []

        for name, field in self.fields.items():
            # Skip read-only fields
            if getattr(field, 'read_only', False):
                continue

            if name in read_only_fields:
                continue

            # Skip fields which are themselves serializers
            if issubclass(field.__class__, serializers.Serializer):
                continue

            # Skip file fields
            if issubclass(field.__class__, fields.FileField):
                continue

            # Skip tags fields
            # TODO: Implement tag field import support
            if issubclass(field.__class__, TagListSerializerField):
                continue

            importable_fields[name] = field

        return importable_fields
