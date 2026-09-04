"""Custom management command to load fixtures faster using bulk_create()."""

from django.core.management.base import CommandError
from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.db import DatabaseError, IntegrityError, router

import structlog

logger = structlog.get_logger('inventree')

DEFAULT_BATCH_SIZE = 500


class Command(LoadDataCommand):
    """Load fixtures using bulk_create() for improved performance.

    Behaves like the built-in 'loaddata' command, with two differences to be
    aware of:

    - pre_save / post_save signals are not sent, and Model.save() / full_clean()
      are bypassed entirely (this is a Django bulk_create() limitation).
    - Natural-key-based foreign key / many-to-many resolution and multi-table
      inheritance are not supported. Neither is currently used by any InvenTree
      fixture/model, but a fixture or model that requires either will fail
      loudly with a bulk_create() error rather than being silently mishandled.

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
        super().handle(*fixture_labels, **options)

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
        self.pending_objs.setdefault(obj.object.__class__, []).append(obj)

        if obj.deferred_fields:
            self.objs_with_deferred_fields.append(obj)

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
