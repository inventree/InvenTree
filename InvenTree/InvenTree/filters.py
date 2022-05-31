"""General filters for InvenTree."""

from rest_framework.filters import OrderingFilter


class InvenTreeOrderingFilter(OrderingFilter):
    """Custom OrderingFilter class which allows aliased filtering of related fields.

    To use, simply specify this filter in the "filter_backends" section.

    filter_backends = [
        InvenTreeOrderingFilter,
    ]

    Then, specify a ordering_field_aliases attribute:

    ordering_field_alises = {
        'name': 'part__part__name',
        'SKU': 'part__SKU',
    }
    """

    def get_ordering(self, request, queryset, view):
        """Override ordering for supporting aliases."""
        ordering = super().get_ordering(request, queryset, view)

        aliases = getattr(view, 'ordering_field_aliases', None)

        # Attempt to map ordering fields based on provided aliases
        if ordering is not None and aliases is not None:
            """Ordering fields should be mapped to separate fields."""

            ordering_initial = ordering
            ordering = []

            for field in ordering_initial:

                reverse = field.startswith('-')

                if reverse:
                    field = field[1:]

                # Are aliases defined for this field?
                if field in aliases:
                    alias = aliases[field]
                else:
                    alias = field

                """
                Potentially, a single field could be "aliased" to multiple field,

                (For example to enforce a particular ordering sequence)

                e.g. to filter first by the integer value...

                ordering_field_aliases = {
                    "reference": ["integer_ref", "reference"]
                }

                """

                if type(alias) is str:
                    alias = [alias]
                elif type(alias) in [list, tuple]:
                    pass
                else:
                    # Unsupported alias type
                    continue

                for a in alias:
                    if reverse:
                        a = '-' + a

                    ordering.append(a)

        return ordering
