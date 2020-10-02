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
    exclude = ['group']

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # Hide RuleSetInline in the 'Add role' view
            if not isinstance(inline, RuleSetInline) or obj is not None:
                yield inline.get_formset(request, obj), inline

    # Save inlines before model
    # https://stackoverflow.com/a/14860703/12794913
    def save_model(self, request, obj, form, change):
        if obj is not None:
            # Save model immediately only if in 'Add role' view
            super(RoleAdmin, self).save_model(request, obj, form, change)
        else:
            pass  # don't actually save the parent instance

    def save_formset(self, request, form, formset, change):
        formset.save()  # this will save the children
        form.instance.save()  # form.instance is the parent
