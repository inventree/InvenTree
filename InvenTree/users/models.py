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

class Role(models.Model):
	""" Role model """

	name = models.CharField(max_length=100, unique=True)

	group = models.OneToOneField(Group, unique=True, blank=True, on_delete=models.CASCADE)

	def __str__(self):
		""" Name for admin interface """
		return self.name

	def save(self, *args, **kwargs):
		""" Custom save method """

		try:
			if self.group.name != self.name:
				# Rename group
				self.group.name = self.name
				self.group.save()
		except:
			self.group = Group.objects.create(name=self.name)

		super(Role, self).save(*args, **kwargs)

		for ruleset_type in RULESET_TYPE_CHOICES:
			try:
				ruleset = self.get_ruleset(name=ruleset_type[0])
			except:
				ruleset = RuleSet.objects.create(name=ruleset_type[0], role=self)

			# Should already be saved when form is saved but does not hurt (much)
			ruleset.save()

		# Set permissions
		self.set_permissions()

	def delete(self, *args, **kwargs):
		""" Custom delete method """

		self.group.delete()

		super(Role, self).delete(*args, **kwargs)

	@classmethod
	def create(cls, name):
		""" Create role, group and default rulesets"""

		role = cls(name=name)

		role.save()

	def assign_to_user(self, user):
		""" Assign role (eg. group) to user """

		if self.group:
			self.group.user_set.add(user)			
			return True

		return False

	def get_ruleset(self, name):
		""" Return a specific ruleset """

		query = RuleSet.objects.filter(role=self.pk).get(name=name)

		return query

	def get_rulesets(self):
		""" Return a queryset for all rulesets under this role """

		query = RuleSet.objects.filter(role=self.pk).all()
		
		return query

	def set_permissions(self):
		""" Set role permissions for all rulesets """

		for ruleset in self.get_rulesets():
			for rule_option in RULESET_OPTIONS:
				# Get ruleset option value
				is_rule_option_enabled = getattr(ruleset, rule_option)
				# Get all ruleset permissions for option
				rule_option_permissions = ruleset.get_permissions_option(rule_option)

				for permission in rule_option_permissions:
					if is_rule_option_enabled:
						self.group.permissions.add(permission)
					else:
						self.group.permissions.remove(permission)


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
		# TODO: Find a way to hide inside admin interface
		return self.name.title()

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
