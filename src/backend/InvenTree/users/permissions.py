"""User permission checks."""

from django.contrib.auth.models import User
from django.db import models

import InvenTree.cache


def check_user_role(user: User, role: str, permission: str) -> bool:
    """Check if a user has a particular role:permission combination.

    Arguments:
        user: The user object to check
        role: The role to check (e.g. 'part' / 'stock')
        permission: The permission to check (e.g. 'view' / 'delete')

    Returns:
        bool: True if the user has the specified role:permission combination

    Note: As this check may be called frequently, we cache the result in the session cache.
    """
    if not user:
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

    for group in user.groups.all():
        for rule in group.rule_sets.all():
            if rule.name == role:
                # Check if the rule has the specified permission
                # e.g. "view" role maps to "can_view" attribute
                if getattr(rule, f'can_{permission}', False):
                    result = True
                    break

    # Save result to session-cache
    InvenTree.cache.set_session_cache(cache_key, result)

    return result


def check_user_permission(user: User, model: models.Model, permission: str) -> bool:
    """Check if the user has a particular permission against a given model type.

    Arguments:
        user: The user object to check
        model: The model class to check (e.g. 'part')
        permission: The permission to check (e.g. 'view' / 'delete')

    Returns:
        bool: True if the user has the specified permission

    Note: As this check may be called frequently, we cache the result in the session cache.
    """
    if not user:
        return False

    if user.is_superuser:
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
