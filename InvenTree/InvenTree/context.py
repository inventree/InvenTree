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

    roles = {}

    for group in user.groups.all():
        for rule in group.rule_sets.all():
            roles[rule.name] = {
                'view': rule.can_view or user.is_superuser,
                'add': rule.can_add or user.is_superuser,
                'change': rule.can_change or user.is_superuser,
                'delete': rule.can_delete or user.is_superuser,
            }

    print("Roles:")
    print(roles)

    return {'roles': roles}
