"""
Django views for interacting with common models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from InvenTree.views import AjaxCreateView, AjaxUpdateView, AjaxDeleteView

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
