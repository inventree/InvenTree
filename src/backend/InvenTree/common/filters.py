"""Custom query filters for the Common app."""

from django.db.models import Prefetch
from django.db.models.query import QuerySet

from common.models import InvenTreeImage


def prefetch_related_images(queryset: QuerySet, reference: str) -> QuerySet:
    """Prefetch all InvenTreeImage instances related via the provided reference.

    Args:
        queryset: The base QuerySet of parent model instances.
        reference: The relationship name from the parent model to the target objects that have an 'images' relation.

    """
    return queryset.prefetch_related(
        Prefetch(
            f'{reference}__images',
            queryset=InvenTreeImage.objects.all(),
            to_attr='all_images',
        )
    )
