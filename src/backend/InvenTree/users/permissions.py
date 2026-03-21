"""Helper functions for user permission checks."""

from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import Prefetch, QuerySet

import InvenTree.cache
from users.ruleset import RULESET_CHANGE_INHERIT, get_ruleset_ignore, get_ruleset_models


def split_model(model_label: str) -> tuple[str, str]:
    """Split a model string into its component parts.

    Arguments:
        model_label: The model class to check (e.g. 'part_partcategory')

    Returns:
        A tuple of the model and app names (e.g. ('partcategory', 'part'))
    """
    *app, model = model_label.split('_')
    app = '_'.join(app) if len(app) > 1 else app[0]
    return model, app


def get_model_permission_string(model: models.Model, permission: str) -> str:
    """Generate a permission string for a given model and permission type.

    Arguments:
        model: The model class to check
        permission: The permission to check (e.g. 'view' / 'delete')

    Returns:
        str: The permission string (e.g. 'part.view_part')
    """
    _model, _app = split_model(model)
    return f'{_app}.{permission}_{_model}'


def split_permission(app: str, perm: str) -> tuple[str, str]:
    """Split the permission string into its component parts.

    Arguments:
        app: The application name (e.g. 'part')
        perm: The permission string (e.g. 'view_part' / 'delete_partcategory')

    Returns:
        A tuple of the permission and model names
    """
    permission_name, *model = perm.split('_')

    # Handle models that have underscores
    if len(model) > 1:  # pragma: no cover
        app += '_' + '_'.join(model[:-1])
        perm = permission_name + '_' + model[-1:][0]
    model = model[-1:][0]
    return perm, model


def prefetch_rule_sets(user) -> QuerySet:
    """Return a queryset of groups with prefetched rule sets for the given user.

    Arguments:
        user: The user object

    Returns:
        QuerySet: The queryset of groups with prefetched rule sets
    """
    return user.groups.all().prefetch_related(
        Prefetch('rule_sets', to_attr='prefetched_rule_sets')
    )


def check_user_role(
    user: User,
    role: str,
    permission: str,
    allow_inactive: bool = False,
    groups: Optional[QuerySet] = None,
) -> bool:
    """Check if a user has a particular role:permission combination.

    Arguments:
        user: The user object to check
        role: The role to check (e.g. 'part' / 'stock')
        permission: The permission to check (e.g. 'view' / 'delete')
        allow_inactive: If False, disallow inactive users from having permissions
        groups: Optional cached queryset of groups to check (defaults to user's groups)

    Returns:
        bool: True if the user has the specified role:permission combination

    Note: As this check may be called frequently, we cache the result in the session cache.
    """
    if not user:
        return False

    if not user.is_active and not allow_inactive:
        return False

    if user.is_superuser:
        return True

    # First, check the session cache
    cache_key = f'role_{user.pk}_{role}_{permission}'
    result = InvenTree.cache.get_session_cache(cache_key)

    if result is not None:
        return result

    # Default for no match
    result = False

    groups = groups or prefetch_rule_sets(user)

    for group in groups:
        for rule in group.prefetched_rule_sets:
            if rule.name == role:
                # Check if the rule has the specified permission
                # e.g. "view" role maps to "can_view" attribute
                if getattr(rule, f'can_{permission}', False):
                    result = True
                    break

    # Save result to session-cache
    InvenTree.cache.set_session_cache(cache_key, result)

    return result


def check_user_permission(
    user: User,
    model: models.Model,
    permission: str,
    allow_inactive: bool = False,
    groups: Optional[QuerySet] = None,
) -> bool:
    """Check if the user has a particular permission against a given model type.

    Arguments:
        user: The user object to check
        model: The model class to check (e.g. 'part')
        permission: The permission to check (e.g. 'view' / 'delete')
        allow_inactive: If False, disallow inactive users from having permissions
        groups: Optional cached queryset of groups to check (defaults to user's groups)

    Returns:
        bool: True if the user has the specified permission

    Note: As this check may be called frequently, we cache the result in the session cache.
    """
    if not user:
        return False

    if not user.is_active and not allow_inactive:
        return False

    if user.is_superuser:
        return True

    table_name = f'{model._meta.app_label}_{model._meta.model_name}'

    # Particular table does not require specific permissions
    if table_name in get_ruleset_ignore():
        return True

    groups = groups or prefetch_rule_sets(user)

    for role, table_names in get_ruleset_models().items():
        if table_name in table_names:
            if check_user_role(user, role, permission, groups=groups):
                return True

    # Check for children models which inherits from parent role
    for parent, child in RULESET_CHANGE_INHERIT:
        # Get child model name
        parent_child_string = f'{parent}_{child}'

        if parent_child_string == table_name:
            # Check if parent role has change permission
            if check_user_role(user, parent, 'change', groups=groups):
                return True

    # Generate the permission name based on the model and permission
    # e.g. 'part.view_part'
    permission_name = f'{model._meta.app_label}.{permission}_{model._meta.model_name}'

    # First, check the session cache
    cache_key = f'permission_{user.pk}_{permission_name}'
    result = InvenTree.cache.get_session_cache(cache_key)

    if result is not None:
        return result

    result = user.has_perm(permission_name)

    # Save result to session-cache
    InvenTree.cache.set_session_cache(cache_key, result)

    return result
