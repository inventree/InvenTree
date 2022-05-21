from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

from InvenTree.ready import canAppAccessDatabase


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):

        if canAppAccessDatabase(allow_test=True):

            try:
                self.assign_permissions()
            except (OperationalError, ProgrammingError):
                pass

            try:
                self.update_owners()
            except (OperationalError, ProgrammingError):
                pass

    def assign_permissions(self):

        from django.contrib.auth.models import Group

        from users.models import RuleSet, update_group_roles

        # First, delete any rule_set objects which have become outdated!
        for rule in RuleSet.objects.all():
            if rule.name not in RuleSet.RULESET_NAMES:  # pragma: no cover  # can not change ORM without the app beeing loaded
                print("need to delete:", rule.name)
                rule.delete()

        # Update group permission assignments for all groups
        for group in Group.objects.all():

            update_group_roles(group)

    def update_owners(self):

        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        from users.models import Owner

        # Create group owners
        for group in Group.objects.all():
            Owner.create(group)

        # Create user owners
        for user in get_user_model().objects.all():
            Owner.create(user)
