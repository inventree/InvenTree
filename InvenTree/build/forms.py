"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django import forms

from InvenTree.forms import HelperForm

from .models import Build


class CancelBuildForm(HelperForm):
    """ Form for cancelling a build """

    confirm_cancel = forms.BooleanField(required=False, label=_('Confirm cancel'), help_text=_('Confirm build cancellation'))

    class Meta:
        model = Build
        fields = [
            'confirm_cancel'
        ]
