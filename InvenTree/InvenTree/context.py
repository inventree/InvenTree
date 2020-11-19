# -*- coding: utf-8 -*-

"""
Provides extra global data to all templates.
"""

from InvenTree.status_codes import SalesOrderStatus, PurchaseOrderStatus
from InvenTree.status_codes import BuildStatus, StockStatus

import InvenTree.status

from users.models import RuleSet
from InvenTree.navigation import get_global_navigation

from django.contrib import messages
from InvenTree.celery import celery_app


def celery_check(request):
    celery_worker_message_displayed = False
    if not hasattr(request, '_celery_checked'):
        request._celery_checked = True
        status = celery_app.control.inspect().active()
        if status is None:
            storage = messages.get_messages(request)
            for message in storage:
                if str(message) == 'Celery worker not running!':
                    celery_worker_message_displayed = True

            storage.used = False

            if not celery_worker_message_displayed:
                messages.error(request, 'Celery worker not running!')
                celery_worker_message_displayed = True

    return []

def health_status(request):

    return {
        "system_healthy": InvenTree.status.check_system_health(),
    }


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

    if user.is_superuser:
        for ruleset in RuleSet.RULESET_MODELS.keys():
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

    request._roles = roles
    return {'roles': roles}

def extension_globals(request):
    ctx = {}

    ctx['nav_items'] = get_global_navigation(request)


    return ctx
