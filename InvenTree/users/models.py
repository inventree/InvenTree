# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from django.dispatch import receiver
from django.db.models.signals import post_save


class RuleSet(models.Model):
    """
    A RuleSet is somewhat like a superset of the django permission  class,
    in that in encapsulates a bunch of permissions.

    There are *many* apps models used within InvenTree,
    so it makes sense to group them into "roles".

    These roles translate (roughly) to the menu options available.

    Each role controls permissions for a number of database tables,
    which are then handled using the normal django permissions approach.
    """

    RULESET_CHOICES = [
        ('admin', _('Admin')),
        ('part', _('Parts')),
        ('stock', _('Stock')),
        ('build', _('Build Orders')),
        ('purchase_order', _('Purchase Orders')),
        ('sales_order', _('Sales Orders')),
    ]

    RULESET_NAMES = [
        choice[0] for choice in RULESET_CHOICES
    ]

    RULESET_PERMISSIONS = [
        'view', 'add', 'change', 'delete',
    ]

    RULESET_MODELS = {
        'admin': [
            'auth_group',
            'auth_user',
            'auth_permission',
            'authtoken_token',
            'users_ruleset',
        ],
        'part': [
            'part_part',
            'part_bomitem',
            'part_partcategory',
            'part_partattachment',
            'part_partsellpricebreak',
            'part_parttesttemplate',
            'part_partparametertemplate',
            'part_partparameter',
            'part_partrelated',
            'part_partcategoryparametertemplate',
        ],
        'stock': [
            'stock_stockitem',
            'stock_stocklocation',
            'stock_stockitemattachment',
            'stock_stockitemtracking',
            'stock_stockitemtestresult',
        ],
        'build': [
            'part_part',
            'part_partcategory',
            'part_bomitem',
            'build_build',
            'build_builditem',
            'build_buildorderattachment',
            'stock_stockitem',
            'stock_stocklocation',
        ],
        'purchase_order': [
            'company_company',
            'company_supplierpart',
            'company_supplierpricebreak',
            'order_purchaseorder',
            'order_purchaseorderattachment',
            'order_purchaseorderlineitem',
        ],
        'sales_order': [
            'company_company',
            'order_salesorder',
            'order_salesorderattachment',
            'order_salesorderlineitem',
            'order_salesorderallocation',
        ]
    }

    # Database models we ignore permission sets for
    RULESET_IGNORE = [
        # Core django models (not user configurable)
        'admin_logentry',
        'contenttypes_contenttype',
        'sessions_session',

        # Models which currently do not require permissions
        'common_colortheme',
        'common_inventreesetting',
        'company_contact',
        'label_stockitemlabel',
        'report_reportasset',
        'report_testreport',
        'part_partstar',

        # Third-party tables
        'error_report_error',
        'exchange_rate',
        'exchange_exchangebackend',
    ]

    RULE_OPTIONS = [
        'can_view',
        'can_add',
        'can_change',
        'can_delete',
    ]

    class Meta:
        unique_together = (
            ('name', 'group'),
        )

    name = models.CharField(
        max_length=50,
        choices=RULESET_CHOICES,
        blank=False,
        help_text=_('Permission set')
    )

    group = models.ForeignKey(
        Group,
        related_name='rule_sets',
        blank=False, null=False,
        on_delete=models.CASCADE,
        help_text=_('Group'),
    )

    can_view = models.BooleanField(verbose_name=_('View'), default=True, help_text=_('Permission to view items'))

    can_add = models.BooleanField(verbose_name=_('Add'), default=False, help_text=_('Permission to add items'))

    can_change = models.BooleanField(verbose_name=_('Change'), default=False, help_text=_('Permissions to edit items'))

    can_delete = models.BooleanField(verbose_name=_('Delete'), default=False, help_text=_('Permission to delete items'))
    
    @staticmethod
    def get_model_permission_string(model, permission):
        """
        Construct the correctly formatted permission string,
        given the app_model name, and the permission type.
        """

        app, model = model.split('_')

        return "{app}.{perm}_{model}".format(
            app=app,
            perm=permission,
            model=model
        )

    def __str__(self, debug=False):
        """ Ruleset string representation """
        if debug:
            # Makes debugging easier
            return f'{str(self.group).ljust(15)}: {self.name.title().ljust(15)} | ' \
                   f'v: {str(self.can_view).ljust(5)} | a: {str(self.can_add).ljust(5)} | ' \
                   f'c: {str(self.can_change).ljust(5)} | d: {str(self.can_delete).ljust(5)}'
        else:
            return self.name

    def save(self, *args, **kwargs):

        # It does not make sense to be able to change / create something,
        # but not be able to view it!

        if self.can_add or self.can_change or self.can_delete:
            self.can_view = True

        if self.can_add or self.can_delete:
            self.can_change = True

        super().save(*args, **kwargs)

        if self.group:
            # Update the group too!
            self.group.save()

    def get_models(self):
        """
        Return the database tables / models that this ruleset covers.
        """

        return self.RULESET_MODELS.get(self.name, [])


def update_group_roles(group, debug=False):
    """

    Iterates through all of the RuleSets associated with the group,
    and ensures that the correct permissions are either applied or removed from the group.

    This function is called under the following conditions:

    a) Whenever the InvenTree database is launched
    b) Whenver the group object is updated

    The RuleSet model has complete control over the permissions applied to any group.

    """

    # List of permissions already associated with this group
    group_permissions = set()

    # Iterate through each permission already assigned to this group,
    # and create a simplified permission key string
    for p in group.permissions.all():
        (permission, app, model) = p.natural_key()

        permission_string = '{app}.{perm}'.format(
            app=app,
            perm=permission
        )

        group_permissions.add(permission_string)

    # List of permissions which must be added to the group
    permissions_to_add = set()

    # List of permissions which must be removed from the group
    permissions_to_delete = set()

    def add_model(name, action, allowed):
        """
        Add a new model to the pile:

        args:
            name - The name of the model e.g. part_part
            action - The permission action e.g. view
            allowed - Whether or not the action is allowed
        """

        if action not in ['view', 'add', 'change', 'delete']:
            raise ValueError("Action {a} is invalid".format(a=action))

        permission_string = RuleSet.get_model_permission_string(model, action)

        if allowed:

            # An 'allowed' action is always preferenced over a 'forbidden' action
            if permission_string in permissions_to_delete:
                permissions_to_delete.remove(permission_string)

            permissions_to_add.add(permission_string)

        else:

            # A forbidden action will be ignored if we have already allowed it
            if permission_string not in permissions_to_add:
                permissions_to_delete.add(permission_string)

    # Get all the rulesets associated with this group
    for r in RuleSet.RULESET_CHOICES:

        rulename = r[0]

        try:
            ruleset = RuleSet.objects.get(group=group, name=rulename)
        except RuleSet.DoesNotExist:
            # Create the ruleset with default values (if it does not exist)
            ruleset = RuleSet.objects.create(group=group, name=rulename)

        # Which database tables does this RuleSet touch?
        models = ruleset.get_models()

        for model in models:
            # Keep track of the available permissions for each model

            add_model(model, 'view', ruleset.can_view)
            add_model(model, 'add', ruleset.can_add)
            add_model(model, 'change', ruleset.can_change)
            add_model(model, 'delete', ruleset.can_delete)

    def get_permission_object(permission_string):
        """
        Find the permission object in the database,
        from the simplified permission string

        Args:
            permission_string - a simplified permission_string e.g. 'part.view_partcategory'

        Returns the permission object in the database associated with the permission string
        """

        (app, perm) = permission_string.split('.')

        (permission_name, model) = perm.split('_')

        try:
            content_type = ContentType.objects.get(app_label=app, model=model)
            permission = Permission.objects.get(content_type=content_type, codename=perm)
        except ContentType.DoesNotExist:
            print(f"Error: Could not find permission matching '{permission_string}'")
            permission = None

        return permission

    # Add any required permissions to the group
    for perm in permissions_to_add:
        
        # Ignore if permission is already in the group
        if perm in group_permissions:
            continue

        permission = get_permission_object(perm)

        if permission:
            group.permissions.add(permission)

        if debug:
            print(f"Adding permission {perm} to group {group.name}")

    # Remove any extra permissions from the group
    for perm in permissions_to_delete:

        # Ignore if the permission is not already assigned
        if perm not in group_permissions:
            continue

        permission = get_permission_object(perm)

        if permission:
            group.permissions.remove(permission)

        if debug:
            print(f"Removing permission {perm} from group {group.name}")


@receiver(post_save, sender=Group)
def create_missing_rule_sets(sender, instance, **kwargs):
    """
    Called *after* a Group object is saved.
    As the linked RuleSet instances are saved *before* the Group,
    then we can now use these RuleSet values to update the
    group permissions.
    """

    update_group_roles(instance)


def check_user_role(user, role, permission):
    """
    Check if a user has a particular role:permission combination.

    If the user is a superuser, this will return True
    """

    if user.is_superuser:
        return True

    for group in user.groups.all():

        for rule in group.rule_sets.all():

            if rule.name == role:

                if permission == 'add' and rule.can_add:
                    return True

                if permission == 'change' and rule.can_change:
                    return True

                if permission == 'view' and rule.can_view:
                    return True

                if permission == 'delete' and rule.can_delete:
                    return True

    # No matching permissions found
    return False
