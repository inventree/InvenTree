# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.utils import OperationalError, ProgrammingError

from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):

        try:
            self.assign_permissions()
        except (OperationalError, ProgrammingError):
            pass

    def assign_permissions(self):

        from django.contrib.auth.models import Group
        from users.models import RuleSet, update_group_roles

        # First, delete any rule_set objects which have become outdated!
        for rule in RuleSet.objects.all():
            if rule.name not in RuleSet.RULESET_NAMES:
                print("need to delete:", rule.name)
                rule.delete()

        # Update group permission assignments for all groups
        for group in Group.objects.all():

            update_group_roles(group)
