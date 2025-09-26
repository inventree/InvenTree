"""Queryset filtering helper functions for the Build app."""

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce, Greatest


def annotate_required_quantity():
    """Annotate the 'required' quantity for each build item in the queryset."""
    return Greatest(
        ExpressionWrapper(F('quantity') - F('consumed'), output_field=DecimalField()),
        0,
        output_field=DecimalField(),
    )


def annotate_allocated_quantity():
    """Annotate the 'allocated' quantity for each build item in the queryset."""
    return Coalesce(Sum('allocations__quantity'), 0, output_field=DecimalField())
