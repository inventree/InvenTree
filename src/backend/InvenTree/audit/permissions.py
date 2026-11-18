"""Permission checks for the audit app.

Rules:
- An audit entry is visible if the user may view the *audited* model
- Querying the history of a parent object (which includes child entries) requires
  permission to view the parent model
- The parent reference of an entry is only exposed if the user may view the parent model
- For models with AUDIT_REQUIRE_PARENT_PERMISSION (e.g. attachments), entries are only
  visible if the user may view the parent model
"""

from typing import Optional

from audit.registry import get_view_restriction


def user_can_view_audit_model(user, model, groups=None) -> bool:
    """Determine if the user may view audit history for the given model class."""
    from users.permissions import check_user_permission

    if user is None or model is None:
        return False

    restriction = get_view_restriction(model)

    if restriction == 'superuser' and not user.is_superuser:
        return False

    if restriction == 'staff' and not user.is_staff:
        return False

    return check_user_permission(user, model, 'view', groups=groups)


def get_viewable_audit_content_types(user) -> Optional[list[int]]:
    """Return the ContentType IDs for which the user may view audit history.

    Returns None if the user may view everything.
    """
    from InvenTree.cache import get_cached_content_types
    from users.permissions import prefetch_rule_sets

    if user.is_superuser:
        return None

    groups = prefetch_rule_sets(user)

    allowed = []

    for ct in get_cached_content_types():
        model = ct.model_class()

        # Stale content types (model no longer installed) are never visible
        if model is None:
            continue

        if user_can_view_audit_model(user, model, groups=groups):
            allowed.append(ct.pk)

    return allowed


def parent_permission_content_types() -> list[int]:
    """Return the ContentType IDs of audited models which require parent permission."""
    from django.contrib.contenttypes.models import ContentType

    from audit.registry import audited_models

    return [
        ContentType.objects.get_for_model(model).pk
        for model in audited_models()
        if getattr(model, 'AUDIT_REQUIRE_PARENT_PERMISSION', False)
    ]
