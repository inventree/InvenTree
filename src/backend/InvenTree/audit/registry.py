"""Registration of audited models with django-auditlog."""

import functools
from typing import Optional

from django.apps import apps

import structlog
from auditlog.registry import auditlog

logger = structlog.get_logger('inventree')

# Fields which are never recorded in the audit log, for any model
BASE_EXCLUDE_FIELDS = (
    'metadata',
    # Derived sorting fields
    'reference_int',
    'line_int',
    # MPTT tree fields
    'lft',
    'rght',
    'tree_id',
    'level',
    # Automatically updated timestamps
    'updated',
    'updated_at',
    'last_updated',
)

# Models (by 'app_label.model' label) whose audit history is restricted,
# regardless of the RuleSet permissions of the requesting user.
# These are models which InvenTree does not define (so cannot carry the mixin attribute),
# or whose history is more sensitive than the current value.
AUDIT_VIEW_RESTRICTIONS = {
    'auth.user': 'staff',
    'auth.group': 'staff',
    'users.ruleset': 'staff',
    'common.inventreesetting': 'staff',
    'plugin.pluginsetting': 'superuser',
}


def audited_models() -> list:
    """Return all installed models which opt in to the audit log.

    Uses the app registry rather than ContentTypes, so that no database access is required.
    """
    from InvenTree.models import InvenTreeAuditMixin

    return sorted(
        (
            model
            for model in apps.get_models()
            if issubclass(model, InvenTreeAuditMixin) and not model._meta.abstract
        ),
        key=lambda model: model._meta.label_lower,
    )


def register_model(model, **kwargs) -> None:
    """Register a single model with django-auditlog, using the model's audit attributes."""
    exclude_fields = {
        *BASE_EXCLUDE_FIELDS,
        *getattr(model, 'AUDIT_EXCLUDE_FIELDS', ()),
        *kwargs.pop('exclude_fields', ()),
    }

    mask_fields = {
        *getattr(model, 'AUDIT_MASK_FIELDS', ()),
        *kwargs.pop('mask_fields', ()),
    }

    m2m_fields = {
        *getattr(model, 'AUDIT_M2M_FIELDS', ()),
        *kwargs.pop('m2m_fields', ()),
    }

    # If specified, *only* these fields are recorded
    include_fields = {
        *getattr(model, 'AUDIT_INCLUDE_FIELDS', ()),
        *kwargs.pop('include_fields', ()),
    }

    auditlog.register(
        model,
        include_fields=sorted(include_fields),
        exclude_fields=sorted(exclude_fields),
        mask_fields=sorted(mask_fields),
        m2m_fields=m2m_fields,
        **kwargs,
    )


def register_audited_models() -> None:
    """Register all models which opt in to the audit log."""
    for model in audited_models():
        if not auditlog.contains(model):
            register_model(model)

    logger.debug('Registered %s models with the audit log', len(auditlog.get_models()))


def get_view_restriction(model):
    """Return the audit view restriction for a model: None, 'staff' or 'superuser'."""
    if restriction := getattr(model, 'AUDIT_VIEW_RESTRICTION', None):
        return restriction

    return AUDIT_VIEW_RESTRICTIONS.get(model._meta.label_lower)


def event_type_choices(model) -> dict[int, str]:
    """Return a mapping of event type value -> label for the given model.

    Event types are defined by the AUDIT_EVENT_TYPES attribute of the model,
    which may be a StatusCode enumeration or a Django Choices class.
    """
    enum = getattr(model, 'AUDIT_EVENT_TYPES', None)

    if enum is None:
        return {}

    return _enum_choices(enum)


@functools.cache
def _enum_choices(enum) -> dict[int, str]:
    """Return a mapping of value -> label for an event type enumeration (cached).

    Note: Labels are returned as (lazy) translatable strings,
    so that they are translated at the point of use.
    """
    # StatusCode enumeration (e.g. StockHistoryCode)
    if callable(getattr(enum, 'items', None)):
        return dict(enum.items(custom=False))

    # Django Choices class
    return {int(key): label for key, label in enum.choices}


def event_type_label(model, event_type: int) -> Optional[str]:
    """Return the label for an event type of the given model (or None if unknown)."""
    if model is None or event_type is None:
        return None

    label = event_type_choices(model).get(int(event_type))

    return None if label is None else str(label)
