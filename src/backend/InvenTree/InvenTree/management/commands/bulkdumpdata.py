"""Custom management command to export fixtures faster, by caching natural-key lookups."""

from contextlib import contextmanager

from django.core.management.commands.dumpdata import Command as DumpDataCommand
from django.core.serializers import python as serializers_python


class Command(DumpDataCommand):
    """Dump fixtures using a natural-key cache for improved performance.

    Behaves identically to the built-in 'dumpdata' command, with one difference:

    - When --natural-foreign is used, Django's serializer resolves each natural-key
      FK by fetching the full related row (getattr(obj, field.name)) with no caching
      of its own - see cached_handle_fk_field(). A large export can have many rows
      referencing the same handful of natural-keyed objects (e.g. thousands of
      stock.StockItem rows all pointing at a few part.Part records), which otherwise
      costs one query per *row* instead of one query per distinct related object.
      This mirrors the caching bulkloaddata.py already does on the import side.
    """

    def handle(self, *app_labels, **options):
        """Wrap the base dumpdata command with a natural-key FK resolution cache."""
        with self._cached_natural_keys():
            super().handle(*app_labels, **options)

    @contextmanager
    def _cached_natural_keys(self):
        """Cache natural-key foreign key resolutions for the duration of this block.

        Keyed by (related model, raw FK id) rather than the natural key tuple
        itself, so a cache hit never needs to touch the FK descriptor (and
        therefore never issues a query) - only the raw id column already present
        on the serialized object.
        """
        cache = {}
        original = serializers_python.Serializer.handle_fk_field

        def cached_handle_fk_field(serializer_self, obj, field):
            if not (
                serializer_self.use_natural_foreign_keys
                and hasattr(field.remote_field.model, 'natural_key')
            ):
                return original(serializer_self, obj, field)

            fk_id = getattr(obj, field.attname)

            if fk_id is None:
                serializer_self._current[field.name] = None
                return

            cache_key = (field.remote_field.model, fk_id)

            if cache_key in cache:
                serializer_self._current[field.name] = cache[cache_key]
                return

            original(serializer_self, obj, field)
            cache[cache_key] = serializer_self._current[field.name]

        serializers_python.Serializer.handle_fk_field = cached_handle_fk_field
        try:
            yield
        finally:
            serializers_python.Serializer.handle_fk_field = original
