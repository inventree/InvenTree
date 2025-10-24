"""Custom query filters for the Common app."""

from typing import Optional

from django.db.models import Prefetch
from django.db.models.query import QuerySet

from common.models import InvenTreeImage


def prefetch_related_images(
    queryset: QuerySet, reference: str = '', images_queryset: Optional[QuerySet] = None
) -> QuerySet:
    """Prefetch all InvenTreeImage instances related via the provided reference.

    Args:
        queryset: The base QuerySet of parent model instances.
        reference: The relationship name from the parent model to the target objects that have an 'images' relation.
        images_queryset: Optional QuerySet for InvenTreeImage instances. Defaults to InvenTreeImage.objects.all().

    """
    if images_queryset is None:
        images_queryset = InvenTreeImage.objects.all()

    return queryset.prefetch_related(
        Prefetch(f'{reference}images', queryset=images_queryset, to_attr='all_images')
    )
