"""Queryset filtering helper functions for the Build app."""

from django.db.models import DecimalField, ExpressionWrapper, F, Max, Sum
from django.db.models.functions import Coalesce, Greatest


def annotate_required_quantity():
    """Annotate the 'required' quantity for each build item in the queryset."""
    # Note: The use of Max() here is intentional, to avoid aggregation issues in MySQL
    # Ref: https://github.com/inventree/InvenTree/pull/10398
    return Greatest(
        ExpressionWrapper(
            Max(F('quantity')) - Max(F('consumed')), output_field=DecimalField()
        ),
        0,
        output_field=DecimalField(),
    )


def annotate_allocated_quantity():
    """Annotate the 'allocated' quantity for each build item in the queryset."""
    return Coalesce(Sum('allocations__quantity'), 0, output_field=DecimalField())
