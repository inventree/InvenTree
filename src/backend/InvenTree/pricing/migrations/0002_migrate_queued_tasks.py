"""Migrate queued background tasks which reference the moved pricing models.

The PartPricing, PartSellPriceBreak and PartInternalPriceBreak models were moved from the
'part' app to the 'pricing' app (see 0001_initial).

Background tasks which were queued before this change (e.g. part pricing updates)
contain pickled model instances which reference the old ('part', <model>) identity.
These can no longer be unpickled, which causes the background worker to fail when
it attempts to process the queued task.

This migration rewrites any such queued tasks to reference the new ('pricing', <model>) identity.
"""

import pickle

from django.db import migrations
from django.db.models.base import model_unpickle

import structlog

logger = structlog.get_logger('inventree')

# Mapping of legacy model identities to their new identities
LEGACY_MODELS = {
    ('part', 'PartPricing'): ('pricing', 'PartPricing'),
    ('part', 'PartSellPriceBreak'): ('pricing', 'PartSellPriceBreak'),
    ('part', 'PartInternalPriceBreak'): ('pricing', 'PartInternalPriceBreak'),
}


def remapped_model_unpickle(model_id):
    """Unpickle a model instance, mapping any legacy model identity to its new identity."""
    if isinstance(model_id, tuple):
        model_id = LEGACY_MODELS.get(model_id, model_id)

    return model_unpickle(model_id)


class RemappingUnpickler(pickle.Unpickler):
    """Unpickler which maps legacy model identities to their new identities.

    Django pickles model instances as a call to 'model_unpickle(app_label, object_name)',
    so the remapping is performed by substituting that function.
    """

    def find_class(self, module, name):
        """Substitute the model unpickling function."""
        if module == 'django.db.models.base' and name == 'model_unpickle':
            return remapped_model_unpickle

        return super().find_class(module, name)


class RemappingPickleSerializer:
    """Serializer for django-q signed payloads, which remaps legacy model identities."""

    @staticmethod
    def loads(data):
        """Unpickle the provided data, remapping legacy model identities."""
        import io

        return RemappingUnpickler(io.BytesIO(data)).load()


def migrate_queued_tasks(apps, schema_editor):
    """Rewrite queued task payloads which reference legacy model identities."""
    from django_q import core_signing
    from django_q.conf import Conf
    from django_q.signing import SignedPackage

    OrmQ = apps.get_model('django_q', 'OrmQ')

    migrated = 0

    for task in OrmQ.objects.all():
        try:
            SignedPackage.loads(task.payload)
            # Payload can be loaded - nothing to do
            continue
        except LookupError:
            # Payload references a model which does not exist (e.g. a legacy model identity)
            pass
        except Exception:
            # Payload cannot be loaded for some other reason - leave it untouched
            continue

        try:
            data = core_signing.loads(
                task.payload,
                key=Conf.SECRET_KEY,
                salt=Conf.PREFIX,
                serializer=RemappingPickleSerializer,
            )
        except Exception:
            logger.warning('Could not migrate queued task %s', task.pk)
            continue

        # Re-pickle the payload, which now references the new model identity
        task.payload = SignedPackage.dumps(data)
        task.save()
        migrated += 1

    if migrated:
        logger.info('pricing.0002: Migrated %s queued background tasks', migrated)


class Migration(migrations.Migration):
    dependencies = [
        ('pricing', '0001_initial'),
        ('django_q', '0019_alter_task_options_alter_ormq_key_alter_ormq_lock_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_queued_tasks, reverse_code=migrations.RunPython.noop)
    ]
