"""Queryset filtering helper functions for the Build app."""

from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce


def annotate_allocated_quantity(queryset: Q) -> Q:
    """Annotate the 'allocated' quantity for each build item in the queryset.

    Arguments:
        queryset: The BuildLine queryset to annotate

    """
    queryset = queryset.prefetch_related('allocations')

    return queryset.annotate(
        allocated=Coalesce(
            Sum('allocations__quantity'), 0, output_field=models.DecimalField()
        )
    )
