"""Database helper functions for InvenTree."""

import uuid
from typing import Optional

from django.db import connections, router, transaction
from django.db.models import QuerySet


def bulk_insert_returns_pks(model) -> bool:
    """Return True if the database backend returns primary keys from bulk_create() for this model.

    e.g. PostgreSQL, SQLite 3.35+ and MariaDB 10.5+ do, MySQL does not.
    """
    db = router.db_for_write(model)
    return connections[db].features.can_return_rows_from_bulk_insert


@transaction.atomic
def bulk_create_and_fetch(
    model, items, id_field: str = 'pk', filters: Optional[dict] = None
) -> QuerySet:
    """Bulk create items in the database, and return a list of the created items.

    Arguments:
        model: The Django model class to create instances of.
        items: A list of dictionaries containing the data for each item to be created.
        id_field: The name of the field to use as the unique identifier for the created items.
        filters: Optional dictionary of filters to apply when fetching the created items.

    Returns:
        A QuerySet containing the created items, ordered by id_field (i.e. insertion order).

    This helper method is required because the Django bulk_create() method
    does not guarantee that the ID values of the created items will be populated in the returned objects.
    In particular, MySQL does not support returning the ID values of bulk created items.

    If the database backend returns primary keys from bulk_create() (e.g. PostgreSQL),
    these are used directly. Otherwise, we provide temporary metadata to the created items,
    which can be used to fetch the created items from the database.

    Assumptions (for backends which do not return primary keys):
        - The provided model type has a "metadata" attribute which can be overloaded for this purpose
        - The model type has an incrementing ID field (default: "pk")

    Any "metadata" provided on the input items is retained (on both code paths).
    """
    id_field = id_field or 'pk'

    if not items:
        return model.objects.none()

    if bulk_insert_returns_pks(model):
        created = model.objects.bulk_create(items, batch_size=500)
        pks = [item.pk for item in created]

        return model.objects.filter(pk__in=pks, **(filters or {})).order_by(id_field)

    return _bulk_create_and_fetch_by_metadata(model, items, id_field, filters)


def _bulk_create_and_fetch_by_metadata(
    model, items, id_field: str, filters: Optional[dict]
) -> QuerySet:
    """Fallback for bulk_create_and_fetch(), for backends which do not return primary keys.

    The created items are tagged with temporary metadata, which is used to fetch them back.
    """
    bulk_create_id = uuid.uuid4().hex

    # Generate temporary metadata for bulk fetching
    metadata = {'bulk_create_id': bulk_create_id}

    # Note: caller-provided filters are only applied to the returned queryset,
    # so that *every* created item is found (and its temporary metadata cleared)
    lookup_filters = {'metadata__bulk_create_id': bulk_create_id}

    # Find the "most recent" item in the database, to set a search floor
    if instance := model.objects.order_by(f'-{id_field}').first():
        lookup_filters[f'{id_field}__gt'] = getattr(instance, id_field)

    # Retain any metadata provided with the input items, so that it can be restored
    original_metadata = [item.metadata for item in items]

    # Overwrite the metadata values
    for item in items:
        item.metadata = metadata

    model.objects.bulk_create(items, batch_size=500)

    instances = model.objects.filter(**lookup_filters)

    pks = list(instances.order_by(id_field).values_list(id_field, flat=True))

    # Override the metadata values to remove the temporary bulk_create_id
    instances.update(metadata=None)

    # Restore the original metadata on the input items
    for item, original in zip(items, original_metadata, strict=True):
        item.metadata = original

    # ...and in the database, for any items which provided their own metadata.
    # Note: pks are in insertion order, so correspond positionally with the input items
    restored = [
        model(pk=pk, metadata=original)
        for pk, original in zip(pks, original_metadata, strict=True)
        if original is not None
    ]

    if restored:
        model.objects.bulk_update(restored, ['metadata'], batch_size=500)

    # Fetch the newly created items (by primary key, as the metadata filter no longer matches)
    # Ordered by id_field: auto-increment values are assigned in insertion order on every
    # backend, so this restores correspondence with the input 'items' list for callers that
    # zip the result against it positionally. Without this, some backends (e.g. MySQL) may
    # return 'pk__in' rows in a different order than they were inserted.
    return model.objects.filter(**{f'{id_field}__in': pks}, **(filters or {})).order_by(
        id_field
    )
