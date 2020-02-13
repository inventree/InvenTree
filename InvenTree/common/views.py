"""
Django views for interacting with common models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from InvenTree.views import AjaxCreateView, AjaxUpdateView, AjaxDeleteView
from guardian.mixins import PermissionRequiredMixin, PermissionListMixin

from . import models
from . import forms


class CurrencyCreate(PermissionRequiredMixin, AjaxCreateView):
    """ View for creating a new Currency object """

    model = models.Currency
    form_class = forms.CurrencyEditForm
    ajax_form_title = _('Create new Currency')
    permission_required = ('common.add_currency')
    permission_object = None


class CurrencyEdit(PermissionRequiredMixin, AjaxUpdateView):
    """ View for editing an existing Currency object """

    model = models.Currency
    form_class = forms.CurrencyEditForm
    ajax_form_title = _('Edit Currency')
    permission_required = ('common.change_currency')


class CurrencyDelete(PermissionRequiredMixin, AjaxDeleteView):
    """ View for deleting an existing Currency object """

    model = models.Currency
    ajax_form_title = _('Delete Currency')
    ajax_template_name = "common/delete_currency.html"
    permission_required = ('common.delete_currency')
