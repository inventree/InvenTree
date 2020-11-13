"""
Django views for interacting with common models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.forms import CheckboxInput, Select

from InvenTree.views import AjaxUpdateView
from InvenTree.helpers import str2bool

from . import models
from . import forms


class SettingEdit(AjaxUpdateView):
    """
    View for editing an InvenTree key:value settings object,
    (or creating it if the key does not already exist)
    """

    model = models.InvenTreeSetting
    ajax_form_title = _('Change Setting')
    form_class = forms.SettingEditForm
    ajax_template_name = "common/edit_setting.html"

    def get_context_data(self, **kwargs):
        """
        Add extra context information about the particular setting object.
        """

        ctx = super().get_context_data(**kwargs)

        setting = self.get_object()

        ctx['key'] = setting.key
        ctx['value'] = setting.value
        ctx['name'] = models.InvenTreeSetting.get_setting_name(setting.key)
        ctx['description'] = models.InvenTreeSetting.get_setting_description(setting.key)

        return ctx

    def get_form(self):
        """
        Override default get_form behaviour
        """

        form = super().get_form()
        
        setting = self.get_object()

        choices = setting.choices()

        if choices is not None:
            form.fields['value'].widget = Select(choices=choices)
        elif setting.is_bool():
            form.fields['value'].widget = CheckboxInput()

            self.object.value = str2bool(setting.value)
            form.fields['value'].value = str2bool(setting.value)

        name = models.InvenTreeSetting.get_setting_name(setting.key)

        if name:
            form.fields['value'].label = name

        description = models.InvenTreeSetting.get_setting_description(setting.key)

        if description:
            form.fields['value'].help_text = description

        return form

    def validate(self, setting, form):
        """
        Perform custom validation checks on the form data.
        """

        data = form.cleaned_data

        value = data.get('value', None)

        if setting.choices():
            """
            If a set of choices are provided for a given setting,
            the provided value must be one of those choices.
            """

            choices = [choice[0] for choice in setting.choices()]

            if value not in choices:
                form.add_error('value', _('Supplied value is not allowed'))

        if setting.is_bool():
            """
            If a setting is defined as a boolean setting,
            the provided value must look somewhat like a boolean value!
            """

            if not str2bool(value, test=True) and not str2bool(value, test=False):
                form.add_error('value', _('Supplied value must be a boolean'))
