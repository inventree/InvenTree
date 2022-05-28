import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from InvenTree.ready import canAppAccessDatabase

logger = logging.getLogger("inventree")


class RuleSet(models.Model):
    """A RuleSet is somewhat like a superset of the django permission  class, in that in encapsulates a bunch of permissions.

    There are *many* apps models used within InvenTree,
    so it makes sense to group them into "roles".

    These roles translate (roughly) to the menu options available.

    Each role controls permissions for a number of database tables,
    which are then handled using the normal django permissions approach.
    """

    RULESET_CHOICES = [
        ('admin', _('Admin')),
        ('part_category', _('Part Categories')),
        ('part', _('Parts')),
        ('stock_location', _('Stock Locations')),
        ('stock', _('Stock Items')),
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
            'authtoken_tokenproxy',
            'users_ruleset',
            'report_reportasset',
            'report_reportsnippet',
            'report_billofmaterialsreport',
            'report_purchaseorderreport',
            'report_salesorderreport',
            'account_emailaddress',
            'account_emailconfirmation',
            'sites_site',
            'socialaccount_socialaccount',
            'socialaccount_socialapp',
            'socialaccount_socialtoken',
            'otp_totp_totpdevice',
            'otp_static_statictoken',
            'otp_static_staticdevice',
            'plugin_pluginconfig',
            'plugin_pluginsetting',
            'plugin_notificationusersetting',
        ],
        'part_category': [
            'part_partcategory',
            'part_partcategoryparametertemplate',
            'part_partcategorystar',
        ],
        'part': [
            'part_part',
            'part_bomitem',
            'part_bomitemsubstitute',
            'part_partattachment',
            'part_partsellpricebreak',
            'part_partinternalpricebreak',
            'part_parttesttemplate',
            'part_partparametertemplate',
            'part_partparameter',
            'part_partrelated',
            'part_partstar',
            'part_partcategorystar',
            'company_supplierpart',
            'company_manufacturerpart',
            'company_manufacturerpartparameter',
            'company_manufacturerpartattachment',
            'label_partlabel',
        ],
        'stock_location': [
            'stock_stocklocation',
            'label_stocklocationlabel',
        ],
        'stock': [
            'stock_stockitem',
            'stock_stockitemattachment',
            'stock_stockitemtracking',
            'stock_stockitemtestresult',
            'report_testreport',
            'label_stockitemlabel',
        ],
        'build': [
            'part_part',
            'part_partcategory',
            'part_bomitem',
            'part_bomitemsubstitute',
            'build_build',
            'build_builditem',
            'build_buildorderattachment',
            'stock_stockitem',
            'stock_stocklocation',
            'report_buildreport',
        ],
        'purchase_order': [
            'company_company',
            'company_supplierpricebreak',
            'order_purchaseorder',
            'order_purchaseorderattachment',
            'order_purchaseorderlineitem',
            'order_purchaseorderextraline',
            'company_supplierpart',
            'company_manufacturerpart',
            'company_manufacturerpartparameter',
        ],
        'sales_order': [
            'company_company',
            'order_salesorder',
            'order_salesorderallocation',
            'order_salesorderattachment',
            'order_salesorderlineitem',
            'order_salesorderextraline',
            'order_salesordershipment',
        ]
    }

    # Database models we ignore permission sets for
    RULESET_IGNORE = [
        # Core django models (not user configurable)
        'admin_logentry',
        'contenttypes_contenttype',

        # Models which currently do not require permissions
        'common_colortheme',
        'common_inventreesetting',
        'common_inventreeusersetting',
        'common_webhookendpoint',
        'common_webhookmessage',
        'common_notificationentry',
        'common_notificationmessage',
        'company_contact',
        'users_owner',

        # Third-party tables
        'error_report_error',
        'exchange_rate',
        'exchange_exchangebackend',
        'user_sessions_session',

        # Django-q
        'django_q_ormq',
        'django_q_failure',
        'django_q_task',
        'django_q_schedule',
        'django_q_success',
    ]

    RULESET_CHANGE_INHERIT = [
        ('part', 'partparameter'),
        ('part', 'bomitem'),
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

    @classmethod
    def check_table_permission(cls, user, table, permission):
        """Check if the provided user has the specified permission against the table."""
        # If the table does *not* require permissions
        if table in cls.RULESET_IGNORE:
            return True

        # Work out which roles touch the given table
        for role in cls.RULESET_NAMES:
            if table in cls.RULESET_MODELS[role]:

                if check_user_role(user, role, permission):
                    return True

        # Check for children models which inherits from parent role
        for (parent, child) in cls.RULESET_CHANGE_INHERIT:
            # Get child model name
            parent_child_string = f'{parent}_{child}'

            if parent_child_string == table:
                # Check if parent role has change permission
                if check_user_role(user, parent, 'change'):
                    return True

        # Print message instead of throwing an error
        name = getattr(user, 'name', user.pk)

        logger.info(f"User '{name}' failed permission check for {table}.{permission}")

        return False

    @staticmethod
    def get_model_permission_string(model, permission):
        """Construct the correctly formatted permission string, given the app_model name, and the permission type."""
        model, app = split_model(model)

        return "{app}.{perm}_{model}".format(
            app=app,
            perm=permission,
            model=model
        )

    def __str__(self, debug=False):  # pragma: no cover
        """Ruleset string representation."""
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
        """Return the database tables / models that this ruleset covers."""
        return self.RULESET_MODELS.get(self.name, [])


def split_model(model):
    """Get modelname and app from modelstring."""
    *app, model = model.split('_')

    # handle models that have
    if len(app) > 1:
        app = '_'.join(app)
    else:
        app = app[0]

    return model, app


def split_permission(app, perm):
    """Split permission string into permission and model."""
    permission_name, *model = perm.split('_')
    # handle models that have underscores
    if len(model) > 1:  # pragma: no cover
        app += '_' + '_'.join(model[:-1])
        perm = permission_name + '_' + model[-1:][0]
    model = model[-1:][0]
    return perm, model


def update_group_roles(group, debug=False):
    """Iterates through all of the RuleSets associated with the group, and ensures that the correct permissions are either applied or removed from the group.

    This function is called under the following conditions:

    a) Whenever the InvenTree database is launched
    b) Whenver the group object is updated

    The RuleSet model has complete control over the permissions applied to any group.
    """
    if not canAppAccessDatabase(allow_test=True):
        return  # pragma: no cover

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
        """Add a new model to the pile.

        Args:
            name: The name of the model e.g. part_part
            action: The permission action e.g. view
            allowed: Whether or not the action is allowed
        """
        if action not in ['view', 'add', 'change', 'delete']:  # pragma: no cover
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
        """Find the permission object in the database, from the simplified permission string.

        Args:
            permission_string: a simplified permission_string e.g. 'part.view_partcategory'

        Returns the permission object in the database associated with the permission string
        """
        (app, perm) = permission_string.split('.')

        perm, model = split_permission(app, perm)

        try:
            content_type = ContentType.objects.get(app_label=app, model=model)
            permission = Permission.objects.get(content_type=content_type, codename=perm)
        except ContentType.DoesNotExist:  # pragma: no cover
            logger.warning(f"Error: Could not find permission matching '{permission_string}'")
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

        if debug:  # pragma: no cover
            logger.info(f"Adding permission {perm} to group {group.name}")

    # Remove any extra permissions from the group
    for perm in permissions_to_delete:

        # Ignore if the permission is not already assigned
        if perm not in group_permissions:
            continue

        permission = get_permission_object(perm)

        if permission:
            group.permissions.remove(permission)

        if debug:  # pragma: no cover
            logger.info(f"Removing permission {perm} from group {group.name}")

    # Enable all action permissions for certain children models
    # if parent model has 'change' permission
    for (parent, child) in RuleSet.RULESET_CHANGE_INHERIT:
        parent_change_perm = f'{parent}.change_{parent}'
        parent_child_string = f'{parent}_{child}'

        # Check if parent change permission exists
        if parent_change_perm in group_permissions:
            # Add child model permissions
            for action in ['add', 'change', 'delete']:
                child_perm = f'{parent}.{action}_{child}'

                # Check if child permission not already in group
                if child_perm not in group_permissions:
                    # Create permission object
                    add_model(parent_child_string, action, ruleset.can_delete)
                    # Add to group
                    permission = get_permission_object(child_perm)
                    if permission:
                        group.permissions.add(permission)
                        logger.info(f"Adding permission {child_perm} to group {group.name}")


@receiver(post_save, sender=Group, dispatch_uid='create_missing_rule_sets')
def create_missing_rule_sets(sender, instance, **kwargs):
    """Called *after* a Group object is saved.

    As the linked RuleSet instances are saved *before* the Group, then we can now use these RuleSet values to update the group permissions.
    """
    update_group_roles(instance)


def check_user_role(user, role, permission):
    """Check if a user has a particular role:permission combination.

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


class Owner(models.Model):
    """The Owner class is a proxy for a Group or User instance.

    Owner can be associated to any InvenTree model (part, stock, build, etc.)

    owner_type: Model type (Group or User)
    owner_id: Group or User instance primary key
    owner: Returns the Group or User instance combining the owner_type and owner_id fields
    """

    @classmethod
    def get_owners_matching_user(cls, user):
        """Return all "owner" objects matching the provided user.

        Includes:
        - An exact match for the user
        - Any groups that the user is a part of
        """
        user_type = ContentType.objects.get(app_label='auth', model='user')
        group_type = ContentType.objects.get(app_label='auth', model='group')

        owners = []

        try:
            owners.append(cls.objects.get(owner_id=user.pk, owner_type=user_type))
        except:  # pragma: no cover
            pass

        for group in user.groups.all():
            try:
                owner = cls.objects.get(owner_id=group.pk, owner_type=group_type)
                owners.append(owner)
            except:  # pragma: no cover
                pass

        return owners

    @staticmethod
    def get_api_url():  # pragma: no cover
        return reverse('api-owner-list')

    class Meta:
        # Ensure all owners are unique
        constraints = [
            UniqueConstraint(fields=['owner_type', 'owner_id'],
                             name='unique_owner')
        ]

    owner_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)

    owner_id = models.PositiveIntegerField(null=True, blank=True)

    owner = GenericForeignKey('owner_type', 'owner_id')

    def __str__(self):
        """Defines the owner string representation."""
        return f'{self.owner} ({self.owner_type.name})'

    def name(self):
        """Return the 'name' of this owner."""
        return str(self.owner)

    def label(self):
        """Return the 'type' label of this owner i.e. 'user' or 'group'."""
        return str(self.owner_type.name)

    @classmethod
    def create(cls, obj):
        """Check if owner exist then create new owner entry."""
        # Check for existing owner
        existing_owner = cls.get_owner(obj)

        if not existing_owner:
            # Create new owner
            try:
                return cls.objects.create(owner=obj)
            except IntegrityError:  # pragma: no cover
                return None

        return existing_owner

    @classmethod
    def get_owner(cls, user_or_group):
        """Get owner instance for a group or user."""
        user_model = get_user_model()
        owner = None
        content_type_id = 0
        content_type_id_list = [ContentType.objects.get_for_model(Group).id,
                                ContentType.objects.get_for_model(user_model).id]

        # If instance type is obvious: set content type
        if type(user_or_group) is Group:
            content_type_id = content_type_id_list[0]
        elif type(user_or_group) is get_user_model():
            content_type_id = content_type_id_list[1]

        if content_type_id:
            try:
                owner = Owner.objects.get(owner_id=user_or_group.id,
                                          owner_type=content_type_id)
            except Owner.DoesNotExist:
                pass

        return owner

    def get_related_owners(self, include_group=False):
        """Get all owners "related" to an owner.

        This method is useful to retrieve all "user-type" owners linked to a "group-type" owner
        """
        user_model = get_user_model()
        related_owners = None

        if type(self.owner) is Group:
            users = user_model.objects.filter(groups__name=self.owner.name)

            if include_group:
                # Include "group-type" owner in the query
                query = Q(owner_id__in=users, owner_type=ContentType.objects.get_for_model(user_model).id) | \
                    Q(owner_id=self.owner.id, owner_type=ContentType.objects.get_for_model(Group).id)
            else:
                query = Q(owner_id__in=users, owner_type=ContentType.objects.get_for_model(user_model).id)

            related_owners = Owner.objects.filter(query)

        elif type(self.owner) is user_model:
            related_owners = [self]

        return related_owners


@receiver(post_save, sender=Group, dispatch_uid='create_owner')
@receiver(post_save, sender=get_user_model(), dispatch_uid='create_owner')
def create_owner(sender, instance, **kwargs):
    """Callback function to create a new owner instance after either a new group or user instance is saved."""
    Owner.create(obj=instance)


@receiver(post_delete, sender=Group, dispatch_uid='delete_owner')
@receiver(post_delete, sender=get_user_model(), dispatch_uid='delete_owner')
def delete_owner(sender, instance, **kwargs):
    """Callback function to delete an owner instance after either a new group or user instance is deleted."""
    owner = Owner.get_owner(instance)
    owner.delete()
