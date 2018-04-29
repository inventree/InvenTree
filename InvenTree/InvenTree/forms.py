# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from crispy_forms.helper import FormHelper


class HelperForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False