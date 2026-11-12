"""Fast-path serializer output for large API list queries.

DRF's Serializer.to_representation() handles every field generically:

    attribute = field.get_attribute(instance)   # nested getattr, callable checks, error handling
    value = field.to_representation(attribute)  # type coercion

For a 1,000 row list with ~70 fields per row, that machinery is a large fraction of the request
time, even though for most fields it reduces to a plain getattr() of a value which is already the
correct output type.

This module builds (once per serializer instance) a "representation plan", which classifies each
readable field as either:

- VALUE:    simple field with single attribute source, whose to_representation() is an identity
            for values of known exact types (e.g. CharField and str). Read directly via getattr.
- PK:       PrimaryKeyRelatedField for a forward relation - read the FK column (<name>_id) directly,
            exactly as DRF's 'pk only' optimization does via Model.serializable_value().
- DATETIME: DateTimeField using the default output format and timezone, with the
            current timezone resolved once per row rather than once per value.
- GENERIC:  anything else - handled exactly as DRF does.

Any value which does not match the expected type (or raises an exception) falls back to the
standard DRF code path for that field, so output is identical to DRF's.
"""

import datetime
from typing import Any

from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from rest_framework.settings import api_settings

# Field plan modes
GENERIC = 0
VALUE = 1
PK = 2
DATETIME = 3

# Serializer field classes (exact type) for which to_representation(value) == value,
# when type(value) is one of the listed (exact) types
IDENTITY_TYPES: dict[type, tuple[type, ...]] = {
    serializers.CharField: (str,),
    serializers.IntegerField: (int,),
    serializers.FloatField: (float,),
    serializers.BooleanField: (bool,),
    serializers.ReadOnlyField: (str, int, float, bool),
}

# Cache of whether a serializer class may use the fast path (see check_serializer_class)
_class_check_cache: dict[type, bool] = {}


def check_serializer_class(cls: type, base: type) -> bool:
    """Determine whether the provided serializer class can use the fast path.

    The fast path replaces Serializer.to_representation() - so it is only valid if the
    next to_representation() implementation in the MRO after 'base' is DRF's own.
    """
    if cls in _class_check_cache:
        return _class_check_cache[cls]

    mro = cls.__mro__
    result = True

    for klass in mro[mro.index(base) + 1 :]:
        if 'to_representation' in klass.__dict__:
            result = klass is serializers.Serializer
            break

    _class_check_cache[cls] = result
    return result


def classify_field(field, model_class: type) -> tuple:
    """Return the plan entry (mode, attribute, extra) for a single serializer field."""
    source_attrs = getattr(field, 'source_attrs', None)

    # Only fields which read a single attribute directly from the instance
    if not source_attrs or len(source_attrs) != 1:
        return (GENERIC, None, None)

    attr = source_attrs[0]
    field_type = type(field)

    if field_type in IDENTITY_TYPES:
        return (VALUE, attr, IDENTITY_TYPES[field_type])

    if field_type is serializers.PrimaryKeyRelatedField and field.pk_field is None:
        try:
            model_field = model_class._meta.get_field(attr)
        except Exception:
            return (GENERIC, None, None)

        if (
            model_field.concrete
            and model_field.is_relation
            and (model_field.many_to_one or model_field.one_to_one)
        ):
            return (PK, model_field.attname, None)

    if field_type is serializers.DateTimeField:
        # Only the default format + timezone behavior is supported
        if not hasattr(field, 'format') and not hasattr(field, 'timezone'):
            return (DATETIME, attr, api_settings.DATETIME_FORMAT)

    return (GENERIC, None, None)


def build_plan(serializer, model_class: type) -> list[tuple]:
    """Construct the representation plan for the provided serializer."""
    return [
        (field.field_name, field, *classify_field(field, model_class))
        for field in serializer._readable_fields
    ]


def represent_generic(field, instance, ret: dict) -> None:
    """Represent a single field exactly as DRF Serializer.to_representation() does."""
    try:
        attribute = field.get_attribute(instance)
    except SkipField:
        return

    check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute

    if check_for_none is None:
        ret[field.field_name] = None
    else:
        ret[field.field_name] = field.to_representation(attribute)


class _FallbackError(Exception):
    """Internal signal to use the generic code path."""


def represent_datetime(value: datetime.datetime, tz, output_format):
    """Equivalent to DRF DateTimeField.to_representation(), with a pre-resolved timezone.

    Raises _FallbackError for edge cases (naive datetime with USE_TZ, overflow, etc).
    """
    # Note: DRF returns the value *without* timezone conversion if no format is specified
    if output_format is None:
        return value

    aware = value.utcoffset() is not None

    if tz is not None:
        if not aware:
            raise _FallbackError
        try:
            value = value.astimezone(tz)
        except OverflowError:
            raise _FallbackError
    elif aware:
        raise _FallbackError

    if output_format.lower() == 'iso-8601':
        value = value.isoformat()
        if value.endswith('+00:00'):
            value = value[:-6] + 'Z'
        return value

    return value.strftime(output_format)


def fast_to_representation(serializer, instance) -> dict[str, Any]:
    """Return the serialized representation of 'instance', using the fast path where possible.

    The output is identical to DRF Serializer.to_representation()
    """
    model_class = type(instance)

    plan_cache = getattr(serializer, '_fast_repr_plan', None)

    if plan_cache is None or plan_cache[0] is not model_class:
        plan_cache = (model_class, build_plan(serializer, model_class))
        serializer._fast_repr_plan = plan_cache

    plan = plan_cache[1]

    ret = {}
    tz = None
    tz_resolved = False

    for name, field, mode, attr, extra in plan:
        if mode == VALUE:
            try:
                value = getattr(instance, attr)
            except Exception:
                # Let DRF handle defaults / missing attributes / related object lookups
                represent_generic(field, instance, ret)
                continue

            if value is None:
                ret[name] = None
            elif type(value) in extra:
                ret[name] = value
            elif callable(value):
                represent_generic(field, instance, ret)
            else:
                ret[name] = field.to_representation(value)

        elif mode == PK:
            ret[name] = getattr(instance, attr)

        elif mode == DATETIME:
            try:
                value = getattr(instance, attr)
            except Exception:
                represent_generic(field, instance, ret)
                continue

            if value is None:
                ret[name] = None
                continue

            if type(value) is not datetime.datetime:
                represent_generic(field, instance, ret)
                continue

            if not tz_resolved:
                # Matches DRF DateTimeField.default_timezone()
                tz = timezone.get_current_timezone() if settings.USE_TZ else None
                tz_resolved = True

            try:
                ret[name] = represent_datetime(value, tz, extra)
            except _FallbackError:
                ret[name] = field.to_representation(value)

        else:
            represent_generic(field, instance, ret)

    return ret
