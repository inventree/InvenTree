"""Django system checks for the InvenTree API."""

import inspect
from pathlib import Path

from django.conf import settings
from django.core import checks
from django.urls import URLPattern, URLResolver, get_resolver

from rest_framework.mixins import ListModelMixin

# System check IDs for a list view which silently ignores 'OptionalField.prefetch_fields'
# - Error: core InvenTree view (blocks runserver / migrate / test / check)
# - Warning: view provided by an external plugin (must not prevent the server from starting)
MISSING_OUTPUT_OPTIONS_MIXIN = 'InvenTree.E001'
MISSING_OUTPUT_OPTIONS_MIXIN_PLUGIN = 'InvenTree.W001'


def is_core_view(view_cls) -> bool:
    """Return True if the view class is defined within the InvenTree source tree."""
    try:
        source = Path(inspect.getfile(view_cls)).resolve()
    except (TypeError, OSError):
        return False

    return source.is_relative_to(Path(settings.BASE_DIR).resolve())


def iter_view_classes(patterns=None):
    """Yield every (DRF) view class registered in the URL configuration."""
    if patterns is None:
        patterns = get_resolver().url_patterns

    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from iter_view_classes(pattern.url_patterns)
        elif isinstance(pattern, URLPattern):
            if view_cls := getattr(pattern.callback, 'cls', None):
                yield view_cls


def serializer_prefetch_fields(serializer_class) -> list[str]:
    """Return the names of OptionalFields (on the serializer) which define prefetch_fields."""
    from InvenTree.serializers import FilterableSerializerMixin, OptionalField

    if not isinstance(serializer_class, type) or not issubclass(
        serializer_class, FilterableSerializerMixin
    ):
        return []

    names = set()

    for base in serializer_class.__mro__:
        for name, field in vars(base).items():
            if isinstance(field, OptionalField) and field.prefetch_fields:
                names.add(name)

    return sorted(names)


def check_optional_field_prefetch(app_configs=None, **kwargs):
    """Warn about list views which would silently ignore 'OptionalField.prefetch_fields'.

    The prefetch_fields declared against an OptionalField are only applied to the
    queryset by the OutputOptionsMixin. A list view without this mixin
    will instead perform (at least) one extra query per row for each included field.

    This is reported as an error for core views, so that it is caught before release.
    External plugin views are reported as a warning only.
    """
    from InvenTree.mixins import OutputOptionsMixin

    errors = []
    seen = set()

    for view_cls in iter_view_classes():
        if view_cls in seen:
            continue

        seen.add(view_cls)

        # Only list views are affected (a detail view returns a single object)
        if not issubclass(view_cls, ListModelMixin):
            continue

        if issubclass(view_cls, OutputOptionsMixin):
            continue

        serializer_class = getattr(view_cls, 'serializer_class', None)

        if fields := serializer_prefetch_fields(serializer_class):
            if is_core_view(view_cls):
                level, check_id = checks.Error, MISSING_OUTPUT_OPTIONS_MIXIN
            else:
                level, check_id = checks.Warning, MISSING_OUTPUT_OPTIONS_MIXIN_PLUGIN

            errors.append(
                level(
                    f'{view_cls.__module__}.{view_cls.__qualname__} ignores prefetch_fields '
                    f'declared on {serializer_class.__name__} ({", ".join(fields)})',
                    hint='Add OutputOptionsMixin to the view, so that the prefetch_fields are applied',
                    obj=view_cls,
                    id=check_id,
                )
            )

    return errors
