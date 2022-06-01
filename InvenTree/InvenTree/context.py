# -*- coding: utf-8 -*-

"""Provides extra global data to all templates."""

import InvenTree.status
from InvenTree.status_codes import (BuildStatus, PurchaseOrderStatus,
                                    SalesOrderStatus, StockHistoryCode,
                                    StockStatus)
from users.models import RuleSet


def health_status(request):
    """Provide system health status information to the global context.

    - Not required for AJAX requests
    - Do not provide if it is already provided to the context
    """
    if request.path.endswith('.js'):
        # Do not provide to script requests
        return {}  # pragma: no cover

    if hasattr(request, '_inventree_health_status'):
        # Do not duplicate efforts
        return {}

    request._inventree_health_status = True

    status = {
        'django_q_running': InvenTree.status.is_worker_running(),
        'email_configured': InvenTree.status.is_email_configured(),
    }

    # The following keys are required to denote system health
    health_keys = [
        'django_q_running',
    ]

    all_healthy = True

    for k in health_keys:
        if status[k] is not True:
            all_healthy = False

    status['system_healthy'] = all_healthy

    status['up_to_date'] = InvenTree.version.isInvenTreeUpToDate()

    return status


def status_codes(request):
    """Provide status code enumerations."""
    if hasattr(request, '_inventree_status_codes'):
        # Do not duplicate efforts
        return {}

    request._inventree_status_codes = True

    return {
        # Expose the StatusCode classes to the templates
        'SalesOrderStatus': SalesOrderStatus,
        'PurchaseOrderStatus': PurchaseOrderStatus,
        'BuildStatus': BuildStatus,
        'StockStatus': StockStatus,
        'StockHistoryCode': StockHistoryCode,
    }


def user_roles(request):
    """Return a map of the current roles assigned to the user.

    Roles are denoted by their simple names, and then the permission type.

    Permissions can be access as follows:

    - roles.part.view
    - roles.build.delete

    Each value will return a boolean True / False
    """
    user = request.user

    roles = {
    }

    if user.is_superuser:
        for ruleset in RuleSet.RULESET_MODELS.keys():  # pragma: no cover
            roles[ruleset] = {
                'view': True,
                'add': True,
                'change': True,
                'delete': True,
            }
    else:
        for group in user.groups.all():
            for rule in group.rule_sets.all():

                # Ensure the role name is in the dict
                if rule.name not in roles:
                    roles[rule.name] = {
                        'view': user.is_superuser,
                        'add': user.is_superuser,
                        'change': user.is_superuser,
                        'delete': user.is_superuser
                    }

                # Roles are additive across groups
                roles[rule.name]['view'] |= rule.can_view
                roles[rule.name]['add'] |= rule.can_add
                roles[rule.name]['change'] |= rule.can_change
                roles[rule.name]['delete'] |= rule.can_delete

    return {'roles': roles}
