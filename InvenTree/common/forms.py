"""
Django forms for interacting with common objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

from InvenTree.forms import HelperForm

from .models import InvenTreeSetting


class SettingEditForm(HelperForm):
    """
    Form for creating / editing a settings object
    """

    class Meta:
        model = InvenTreeSetting

        fields = [
            'value'
        ]


class UploadFile(forms.Form):
    ''' Step 1 '''
    first_name = forms.CharField(max_length=100)


class MatchField(forms.Form):
    ''' Step 2 '''
    last_name = forms.CharField(max_length=100)


class MatchPart(forms.Form):
    ''' Step 3 '''
    age = forms.IntegerField()
