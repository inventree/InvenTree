"""Queryset filtering helper functions for the Build app."""

from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce, Greatest


def annotate_required_quantity(queryset: Q) -> Q:
    """Annotate the 'required' quantity for each build item in the queryset.

    Arguments:
        queryset: The BuildLine queryset to annotate

    """
    return queryset.annotate(
        required=Greatest(
            ExpressionWrapper(
                F('quantity') - F('consumed'), output_field=DecimalField()
            ),
            0,
            output_field=DecimalField(),
        )
    )


def annotate_allocated_quantity(queryset: Q) -> Q:
    """Annotate the 'allocated' quantity for each build item in the queryset.

    Arguments:
        queryset: The BuildLine queryset to annotate

    """
    queryset = queryset.prefetch_related('allocations')

    return queryset.annotate(
        allocated=Coalesce(Sum('allocations__quantity'), 0, output_field=DecimalField())
    )
