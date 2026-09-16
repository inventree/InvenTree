"""Database helper functions for InvenTree."""

import uuid
from typing import Optional

from django.db import transaction
from django.db.models import QuerySet


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
        A QuerySet containing the created items.

    This helper method is required because the Django bulk_create() method
    does not guarantee that the ID values of the created items will be populated in the returned objects.
    In particular, MySQL does not support returning the ID values of bulk created items.

    So, we provide temporary metadata to the created items,
    which can be used to fetch the created items from the database.

    Assumptions:
        - The provided model type has a "metadata" attribute which can be overloaded for this purpose
        - No "metadata" is provided in the input items, as this will be overwritten by the method
        - The model type has an incrementing ID field (default: "pk")

    """
    bulk_create_id = uuid.uuid4().hex

    # Generate temporary metadata for bulk fetching
    metadata = {'bulk_create_id': bulk_create_id}

    lookup_filters = dict(filters) if filters else {}

    lookup_filters['metadata__bulk_create_id'] = bulk_create_id

    if id_field:
        # Find the "most recent" item in the database, to set a search floor
        if instance := model.objects.order_by(f'-{id_field}').first():
            lookup_filters[f'{id_field}__gt'] = getattr(instance, id_field)

    # Overwrite the metadata values
    for item in items:
        item.metadata = metadata

    model.objects.bulk_create(items, batch_size=500)

    instances = model.objects.filter(**lookup_filters)

    id_field = id_field or 'pk'

    pks = list(instances.order_by(id_field).values_list(id_field, flat=True))

    # Override the metadata values to remove the temporary bulk_create_id
    instances.update(metadata=None)

    # Fetch the newly created items (by primary key, as the metadata filter no longer matches)
    # Ordered by id_field: auto-increment values are assigned in insertion order on every
    # backend, so this restores correspondence with the input 'items' list for callers that
    # zip the result against it positionally. Without this, some backends (e.g. MySQL) may
    # return 'pk__in' rows in a different order than they were inserted.
    return model.objects.filter(**{f'{id_field}__in': pks}).order_by(id_field)
