"""Registration of audited models with django-auditlog."""

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
