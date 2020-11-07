"""
Django views for interacting with common models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.forms import CheckboxInput
from django.http import JsonResponse

from InvenTree.views import AjaxCreateView, AjaxUpdateView, AjaxDeleteView
from InvenTree.helpers import str2bool
from InvenTree.celery import celery_app
from celery.result import AsyncResult


from . import models
from . import forms


class CurrencyCreate(AjaxCreateView):
    """ View for creating a new Currency object """

    model = models.Currency
    form_class = forms.CurrencyEditForm
    ajax_form_title = _('Create new Currency')


class CurrencyEdit(AjaxUpdateView):
    """ View for editing an existing Currency object """

    model = models.Currency
    form_class = forms.CurrencyEditForm
    ajax_form_title = _('Edit Currency')


class CurrencyDelete(AjaxDeleteView):
    """ View for deleting an existing Currency object """

    model = models.Currency
    ajax_form_title = _('Delete Currency')
    ajax_template_name = "common/delete_currency.html"


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

        if setting.is_bool():
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


def run_task(request):
    if request.POST:
        task_name = request.POST.get("name")
        task = celery_app.send_task(task_name)
        return JsonResponse({"task_id": task.id}, status=202)
    return JsonResponse({"message": "Bad Request"})


def get_task(request, pk):
    task_result = AsyncResult(pk)
    result = {
        "task_id": pk,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JsonResponse(result, status=200)
