# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

from django.apps import apps
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission

RULESET_TYPE_CHOICES = (
		('part', 'Part'),
		('stock', 'Stock'),
		('build', 'Build'),
		('buy', 'Buy'),
		('sell', 'Sell'),
	)

RULESET_OPTIONS = [
	'view',
	'add',
	'change',
	'delete',	
]
# RULESET_OPTIONS = (
# 		('view', 'View'),
# 		('add', 'Add'),
# 		('change', 'Change'),
# 		('delete', 'Delete'),
# 	)

# RULESET_TYPE_MODELS = {
# 	'part': ['part_category', 'part', ]
# }

class Role(models.Model):
	""" Role model """

	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name

	@classmethod
	def create(cls, name):
		""" Create role, group and default rulesets"""
		role = cls(name=name)
		role.save()

		group = Group.objects.create(name=name)

		for ruleset_type in RULESET_TYPE_CHOICES:
			RuleSet.objects.create(name=ruleset_type[0], role=role)

	@property
	def get_role_group(self):
		return Group.objects.get(name=self.name)

	def assign_to_user(self, user):
		""" Assign role (group) to user """

		group = self.get_role_group

		if group:
			group.user_set.add(user)			
			return True

		return False

	def get_rulesets(self):
		""" Return a queryset for all rulesets under this role """

		query = RuleSet.objects.filter(role=self.pk).all()
		
		return query

	def set_permissions(self):
		""" Set role permissions for all rulesets """

		group = self.get_role_group

		for ruleset in self.get_rulesets():
			for rule_option in RULESET_OPTIONS:
				# Get ruleset option value
				is_rule_option_enabled = getattr(ruleset, rule_option)
				# Get all ruleset permissions for option
				rule_option_permissions = ruleset.get_permissions_option(rule_option)

				if is_rule_option_enabled:
					group.permissions.set(rule_option_permissions)
				else:
					for permission in rule_option_permissions:
						group.permissions.remove(permission)


class RuleSet(models.Model):
	""" Generic ruleset model """

	name = models.CharField(max_length=20, choices=RULESET_TYPE_CHOICES, blank=False)

	role = models.ForeignKey(Role, related_name='rule_sets',
                             on_delete=models.CASCADE,
                             help_text=_('Select Role'))

	view = models.BooleanField(default=True)

	add = models.BooleanField(default=False)

	change = models.BooleanField(default=False)

	delete = models.BooleanField(default=False)

	def __str__(self):
		# To hide in admin interface
		return ''

	def get_models(self):
		""" Get models related to ruleset """

		### TODO: Need actual app assignment
		if self.name == 'buy':
			app_models = apps.get_app_config('order').get_models()
		elif self.name == 'sell':
			app_models = apps.get_app_config('company').get_models()
		else:
			app_models = apps.get_app_config(self.name).get_models()

		return app_models

	def get_permissions(self):
		""" Get all permissions related to ruleset """

		ruleset_permissions = []

		models = self.get_models()

		for model in models:
			content_type = ContentType.objects.get_for_model(model)
			model_permissions = Permission.objects.filter(content_type=content_type)
			for permission in model_permissions:
				ruleset_permissions.append(permission)

		return ruleset_permissions

	def get_permissions_option(self, option):
		""" Get all permissions related to an option of the ruleset """
		option_permissions = []

		if option not in RULESET_OPTIONS:
			return None

		for permission in self.get_permissions():
			if permission.codename.startswith(option):
				option_permissions.append(permission)

		return option_permissions
