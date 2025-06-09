"""Background tasks for the users app."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

import structlog

from InvenTree.ready import canAppAccessDatabase
from users.models import RuleSet
from users.permissions import get_model_permission_string, split_permission
from users.ruleset import RULESET_CHANGE_INHERIT, RULESET_CHOICES, RULESET_NAMES

logger = structlog.get_logger('inventree')


def rebuild_all_permissions() -> None:
    """Rebuild all user permissions.

    This function is called when a user is created or when a group is modified.
    It rebuilds the permissions for all users in the system.
    """
    logger.info('Rebuilding permissions')

    # Rebuild permissions for each group
    for group in Group.objects.all():
        update_group_roles(group)


def update_group_roles(group: Group, debug: bool = False) -> None:
    """Update the roles for a particular group.

    Arguments:
        group: The group object to update roles for.
        debug: Whether to enable debug logging

    This function performs the following tasks:
    - Remove any RuleSet objects which have become outdated
    - Ensure that the group has a mapped RuleSet for each role
    - Rebuild the permissions for the group, based on the assigned RuleSet objects
    """
    if not canAppAccessDatabase(allow_test=True):
        return  # pragma: no cover

    logger.info('Updating group roles for %s', group)

    # Remove any outdated RuleSet objects
    outdated_rules = group.rule_sets.exclude(name__in=RULESET_NAMES)

    if outdated_rules.exists():
        logger.info(
            'Deleting %s outdated rulesets from group %s', outdated_rules.count(), group
        )
        outdated_rules.delete()

    # Add any missing RuleSet objects
    for rule in RULESET_NAMES:
        if not group.rule_sets.filter(name=rule).exists():
            logger.info('Adding ruleset %s to group %s', rule, group)
            RuleSet.objects.create(group=group, name=rule)

    # Update the permissions for the group
    # List of permissions already associated with this group
    group_permissions = set()

    # Iterate through each permission already assigned to this group,
    # and create a simplified permission key string
    for p in group.permissions.all().prefetch_related('content_type'):
        (permission, app, model) = p.natural_key()
        permission_string = f'{app}.{permission}'
        group_permissions.add(permission_string)

    # List of permissions which must be added to the group
    permissions_to_add = set()

    # List of permissions which must be removed from the group
    permissions_to_delete = set()

    def add_model(name, action, allowed):
        """Add a new model to the pile.

        Args:
            name: The name of the model e.g. part_part
            action: The permission action e.g. view
            allowed: Whether or not the action is allowed
        """
        if action not in ['view', 'add', 'change', 'delete']:  # pragma: no cover
            raise ValueError(f'Action {action} is invalid')

        permission_string = get_model_permission_string(model, action)

        if allowed:
            # An 'allowed' action is always preferenced over a 'forbidden' action
            if permission_string in permissions_to_delete:
                permissions_to_delete.remove(permission_string)

            permissions_to_add.add(permission_string)

        elif permission_string not in permissions_to_add:
            permissions_to_delete.add(permission_string)

    # Pre-fetch all the RuleSet objects
    rulesets = {
        r.name: r for r in RuleSet.objects.filter(group=group).prefetch_related('group')
    }

    # Get all the rulesets associated with this group
    for rule_name, _rule_label in RULESET_CHOICES:
        if rule_name in rulesets:
            ruleset = rulesets[rule_name]
        else:
            try:
                ruleset = RuleSet.objects.get(group=group, name=rule_name)
            except RuleSet.DoesNotExist:
                ruleset = RuleSet.objects.create(group=group, name=rule_name)

        # Which database tables does this RuleSet touch?
        models = ruleset.get_models()

        for model in models:
            # Keep track of the available permissions for each model
            add_model(model, 'view', ruleset.can_view)
            add_model(model, 'add', ruleset.can_add)
            add_model(model, 'change', ruleset.can_change)
            add_model(model, 'delete', ruleset.can_delete)

    def get_permission_object(permission_string):
        """Find the permission object in the database, from the simplified permission string.

        Args:
            permission_string: a simplified permission_string e.g. 'part.view_partcategory'

        Returns the permission object in the database associated with the permission string
        """
        (app, perm) = permission_string.split('.')

        perm, model = split_permission(app, perm)
        permission = None

        try:
            content_type = ContentType.objects.get(app_label=app, model=model)
            permission = Permission.objects.get(
                content_type=content_type, codename=perm
            )
        except ContentType.DoesNotExist:  # pragma: no cover
            logger.warning("No ContentType found matching '%s' and '%s'", app, model)
        except Permission.DoesNotExist:
            logger.warning("No Permission found matching '%s' and '%s'", app, perm)

        return permission

    # Add any required permissions to the group
    for perm in permissions_to_add:
        # Ignore if permission is already in the group
        if perm in group_permissions:
            continue

        if permission := get_permission_object(perm):
            group.permissions.add(permission)
            if debug:  # pragma: no cover
                logger.debug('Adding permission %s to group %s', perm, group.name)

    # Remove any extra permissions from the group
    for perm in permissions_to_delete:
        # Ignore if the permission is not already assigned
        if perm not in group_permissions:
            continue

        if permission := get_permission_object(perm):
            group.permissions.remove(permission)
            if debug:  # pragma: no cover
                logger.debug('Removing permission %s from group %s', perm, group.name)

    # Enable all action permissions for certain children models
    # if parent model has 'change' permission
    for parent, child in RULESET_CHANGE_INHERIT:
        parent_child_string = f'{parent}_{child}'

        # Check each type of permission
        for action in ['view', 'change', 'add', 'delete']:
            parent_perm = f'{parent}.{action}_{parent}'

            if parent_perm in group_permissions:
                child_perm = f'{parent}.{action}_{child}'

                # Check if child permission not already in group
                if child_perm not in group_permissions:
                    # Create permission object
                    add_model(parent_child_string, action, ruleset.can_delete)
                    # Add to group
                    permission = get_permission_object(child_perm)
                    if permission:
                        group.permissions.add(permission)
                        logger.debug(
                            'Adding permission %s to group %s', child_perm, group.name
                        )
