# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group
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
        ('general', _('General')),
        ('admin', _('Admin')),
        ('part', _('Parts')),
        ('stock', _('Stock')),
        ('build', _('Build Orders')),
        ('supplier', _('Suppliers')),
        ('purchase_order', _('Purchase Orders')),
        ('customer', _('Customers')),
        ('sales_order', _('Sales Orders')),
    ]

    RULESET_NAMES = [
        choice[0] for choice in RULESET_CHOICES
    ]

    RULESET_MODELS = {
        'general': [
            'part.partstar',
        ],
        'admin': [
            'auth.group',
            'auth.user',
            'auth.permission',
            'authtoken.token',
        ],
        'part': [
            'part.part',
            'part.bomitem',
            'part.partcategory',
            'part.partattachment',
            'part.partsellpricebreak',
            'part.parttesttemplate',
            'part.partparametertemplate',
            'part.partparameter',
        ],
        'stock': [
            'stock.stockitem',
            'stock.stocklocation',
            'stock.stockitemattachment',
            'stock.stockitemtracking',
            'stock.stockitemtestresult',
        ],
        'build': [
            'part.part',
            'part.partcategory',
            'part.bomitem',
            'build.build',
            'build.builditem',
            'stock.stockitem',
            'stock.stocklocation',   
        ]
    }

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

    can_add = models.BooleanField(verbose_name=_('Create'), default=False, help_text=_('Permission to add items'))

    can_change = models.BooleanField(verbose_name=_('Update'), default=False, help_text=_('Permissions to edit items'))

    can_delete = models.BooleanField(verbose_name=_('Delete'), default=False, help_text=_('Permission to delete items'))
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_models(self):

        models = {
            ''
        }

def update_group_roles(group):
    """
    Update group roles:
    
    a) Ensure default roles are assigned to each group.
    b) Ensure group permissions are correctly updated and assigned
    """

    # List of permissions which must be added to the group
    permissions_to_add = []

    # List of permissions which must be removed from the group
    permissions_to_delete = []

    # Get all the rulesets associated with this group
    for r in RuleSet.RULESET_CHOICES:

        rulename = r[0]

        try:
            ruleset = RuleSet.objects.get(group=group, name=rulename)
        except RuleSet.DoesNotExist:
            # Create the ruleset with default values (if it does not exist)
            ruleset = RuleSet.objects.create(group=group, name=rulename)

        # TODO - Update permissions here

    # TODO - Update group permissions


@receiver(post_save, sender=Group)
def create_missing_rule_sets(sender, instance, **kwargs):

    update_group_roles(instance)