# -*- coding: utf-8 -*-
# from __future__ import unicode_literals
from django.contrib import admin

from users.models import Role, RuleSet
from users.models import RULESET_TYPE_CHOICES, RULESET_OPTIONS

class RuleSetInline(admin.TabularInline):
    model = RuleSet
    can_delete = False
    verbose_name = 'Ruleset'
    verbose_name_plural = 'Rulesets'
    fields = ['name'] + [option for option in RULESET_OPTIONS]
    readonly_fields = ['name']
    max_num = len(RULESET_TYPE_CHOICES)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	inlines = [RuleSetInline]
	verbose_name_plural = 'Roles'

