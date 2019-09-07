"""
Django views for interacting with common models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.views import AjaxCreateView, AjaxUpdateView

from . import models
from . import forms


class CurrencyCreate(AjaxCreateView):
    """ View for creating a new Currency object """

    model = models.Currency
    form_class = forms.CurrencyEditForm
    ajax_form_title = 'Create new Currency'


class CurrencyEdit(AjaxUpdateView):
    """ View for editing an existing Currency object """

    model = models.Currency
    form_class = forms.CurrencyEditForm
    ajax_form_title = 'Edit Currency'
