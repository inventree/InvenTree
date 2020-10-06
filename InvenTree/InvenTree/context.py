# -*- coding: utf-8 -*-

"""
Provides extra global data to all templates.
"""

from InvenTree.status_codes import SalesOrderStatus, PurchaseOrderStatus
from InvenTree.status_codes import BuildStatus, StockStatus


def status_codes(request):

    return {
        # Expose the StatusCode classes to the templates
        'SalesOrderStatus': SalesOrderStatus,
        'PurchaseOrderStatus': PurchaseOrderStatus,
        'BuildStatus': BuildStatus,
        'StockStatus': StockStatus,
    }


def user_roles(request):
    """
    Return a map of the current roles assigned to the user.
    
    Roles are denoted by their simple names, and then the permission type.

    Permissions can be access as follows:

    - roles.part.view
    - roles.build.delete

    Each value will return a boolean True / False
    """

    user = request.user

    roles = {
    }

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
