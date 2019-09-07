"""
Django views for interacting with common models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.views import AjaxCreateView

from .models import Currency
from .forms import CurrencyEditForm


class CurrencyCreate(AjaxCreateView):
    """ View for creating a new Currency object """

    model = Currency
    form_class = CurrencyEditForm
    ajax_form_title = 'Create new Currency'
