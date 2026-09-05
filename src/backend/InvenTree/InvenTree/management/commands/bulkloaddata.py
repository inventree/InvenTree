"""Custom management command to load fixtures faster using bulk_create()."""

import time
from contextlib import contextmanager

from django.core.management.base import CommandError
from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.core.serializers import base as serializers_base
from django.db import DatabaseError, IntegrityError, connections, router

import structlog

logger = structlog.get_logger('inventree')

DEFAULT_BATCH_SIZE = 500


class Command(LoadDataCommand):
    """Load fixtures using bulk_create() for improved performance.

    Behaves like the built-in 'loaddata' command, with two differences to be
    aware of:

    - pre_save / post_save signals are not sent, and Model.save() / full_clean()
      are bypassed entirely (this is a Django bulk_create() limitation).
    - Multi-table inheritance is not supported by bulk_create() and will fail
      loudly rather than being silently mishandled. Natural-key foreign key /
      many-to-many resolution *is* supported (falling back to an individual,
      non-bulk save for any row that needs it - see save_obj()) and is further
      sped up by caching each resolved natural key for the life of the command
      (see _cached_natural_keys()), since 'export_records' uses
      --natural-foreign and a large fixture can have many rows referencing the
      same handful of natural-keyed objects (e.g. stock.StockItemTracking.user
      -> auth.User) - without caching, each one costs a separate DB query.

    Based on the django forum thread:
    - https://forum.djangoproject.com/t/feature-proposal-faster-fixture-loading-via-loaddata-command/36972/21
    """

    def add_arguments(self, parser):
        """Add bulkloaddata-specific arguments, on top of loaddata's own."""
        super().add_arguments(parser)
        parser.add_argument(
            '--batch-size',
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help=f'Number of records per bulk_create() batch (default: {DEFAULT_BATCH_SIZE})',
        )
        parser.add_argument(
            '--ignore-conflicts',
            action='store_true',
            help='Skip records that violate a unique constraint, instead of raising an error',
        )

    def handle(self, *fixture_labels, **options):
        """Store bulk-loading options before delegating to the base command."""
        self.batch_size = options['batch_size']
        self.ignore_conflicts = options['ignore_conflicts']
        self.pending_objs = {}

        connection = connections[options['database']]
        self.query_count = 0

        def count_queries(execute, sql, params, many, context):
            """Count every query executed against this connection, without the overhead of recording each query's SQL text (unlike e.g. CaptureQueriesContext)."""
            self.query_count += 1
            return execute(sql, params, many, context)

        start_time = time.monotonic()

        with connection.execute_wrapper(count_queries), self._cached_natural_keys():
            super().handle(*fixture_labels, **options)

        elapsed = time.monotonic() - start_time

        if self.verbosity >= 1:
            self.stdout.write(
                f'Executed {self.query_count} database queries in {elapsed:.2f}s'
            )

    @contextmanager
    def _cached_natural_keys(self):
        """Cache natural-key foreign key resolutions for the duration of this block.

        Django's deserializer (deserialize_fk_value) issues a fresh DB query
        every time it resolves a natural-key FK reference, with no caching of
        its own. A fixture with many rows referencing the same handful of
        natural-keyed objects (e.g. thousands of stock.StockItemTracking rows
        all pointing at a few auth.User accounts) would otherwise cost one
        query per row instead of one query per distinct value.
        """
        cache = {}
        original = serializers_base.deserialize_fk_value

        def cached_deserialize_fk_value(
            field, field_value, using, handle_forward_references
        ):
            default_manager = field.remote_field.model._default_manager

            is_natural_key = (
                field_value is not None
                and hasattr(default_manager, 'get_by_natural_key')
                and hasattr(field_value, '__iter__')
                and not isinstance(field_value, str)
            )

            if not is_natural_key:
                # Plain (non natural-key) FK values never reach a DB query in
                # the first place - nothing to cache, delegate as normal
                return original(field, field_value, using, handle_forward_references)

            cache_key = (field.remote_field.model, using, tuple(field_value))

            if cache_key in cache:
                return cache[cache_key]

            value = original(field, field_value, using, handle_forward_references)

            # Only cache a fully-resolved value - a deferred lookup (the
            # referenced object doesn't exist yet) may well succeed on a later
            # call, once that object has actually been saved.
            if value is not serializers_base.DEFER_FIELD:
                cache[cache_key] = value

            return value

        serializers_base.deserialize_fk_value = cached_deserialize_fk_value
        try:
            yield
        finally:
            serializers_base.deserialize_fk_value = original

    def save_obj(self, obj):
        """Buffer an object for bulk insertion, instead of saving it immediately."""
        if (
            obj.object._meta.app_config in self.excluded_apps
            or type(obj.object) in self.excluded_models
        ):
            return False

        if not router.allow_migrate_model(self.using, obj.object.__class__):
            return False

        self.models.add(obj.object.__class__)

        if obj.deferred_fields:
            # This object has an unresolved forward reference (e.g. a natural-key
            # FK to an object that has not been saved yet - 'export_records' uses
            # --natural-foreign, and e.g. auth.User defines a natural_key(), so
            # this does occur in practice). It cannot be bulk_create()'d as-is, since
            # the deferred field would be written as blank/null. The base loaddata()
            # command already resolves and saves objects like this individually,
            # via save_deferred_fields(), once every fixture file has been buffered
            # (see 'handle' -> 'loaddata') - so just hand it off for that, rather
            # than also bulk-inserting it here with the field left unresolved.
            self.objs_with_deferred_fields.append(obj)
        else:
            self.pending_objs.setdefault(obj.object.__class__, []).append(obj)

        return True

    def flush_pending(self):
        """Bulk-create every object buffered so far, grouped by model."""
        for model, objs in self.pending_objs.items():
            try:
                model._default_manager.db_manager(self.using).bulk_create(
                    [obj.object for obj in objs],
                    batch_size=self.batch_size,
                    ignore_conflicts=self.ignore_conflicts,
                )
            except (DatabaseError, IntegrityError, ValueError) as e:
                e.args = (
                    f'Could not bulk-create {len(objs)} object(s) of {model._meta.label}: {e}',
                )
                raise

            # bulk_create() cannot populate many-to-many relations - apply them here,
            # same as DeserializedObject.save() does for the non-bulk path.
            for obj in objs:
                if obj.m2m_data:
                    for accessor_name, values in obj.m2m_data.items():
                        getattr(obj.object, accessor_name).set(values)
                    obj.m2m_data = None

        self.pending_objs = {}

    def load_label(self, fixture_label):
        """Load one fixture label, then flush the records it buffered."""
        super().load_label(fixture_label)
        try:
            self.flush_pending()
        except Exception as e:
            if not isinstance(e, CommandError):
                e.args = (f"Problem installing fixture '{fixture_label}': {e}",)
            raise
